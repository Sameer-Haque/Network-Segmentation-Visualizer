#!/usr/bin/env python3
import argparse
import ipaddress
import os
import socket
import csv

# needs python-nmap
import nmap
# needs snimpy
from snimpy.manager import Manager as M
from snimpy.manager import load
import snimpy
# needs PyYAML
import yaml

# IF-MIB, IP-MIB, IP-FORWARD-MIB, SNMPv2-MIB, HOST-RESOURCES-MIB
BASE_MODULES = ["if_mib", "ip_mib", "ip_forward_mib", "system", "hrSystem", "hrDevice", "hrStorage"]

# Currently supported vendors:
# - OpenWRT
# - Cisco
# - D-Link (untested)
# - TODO: Support Mikrotik
# Profile format:
# - label = vendor name
# - extra_modules = additional SNMP MIB modules supported by vendor
# - keywords = used for detection based on presence in sysDescr
VENDOR_PROFILES = {
    "openwrt": {
        "label": "openwrt",
        "extra_modules": ["ucd_system_stats", "ucd_memory"],
        "keywords": ["openwrt", "lede"],
    },
    "cisco": {
        "label": "cisco",
        "extra_modules": ["bridge_mib", "cisco_cpu", "cisco_memory", "cisco_if_extension", "cisco_envmon", "entity_mib", "cisco_cdp", "cisco_vtp"],
        "keywords": ["cisco", "ios", "catalyst", "nexus", "asr", "isr"],
    },
    "dlink": {
        "label": "dlink",
		"extra_modules": ["bridge_mib", "q_bridge_mib", "p_bridge_mib"],
		"keywords": ["dlink", "d-link", "des", "dgs"],
    },
    "mikrotik": {
        "label": "mikrotik",
        "extra_modules": ["mikrotik_mib"],
        "keywords": ["mikrotik", "routeros"]
    },
}

# Cisco, Mikrotik, and D-Link are identified by the presence of the MIB trees
# associated with them
# OpenWRT is identified by Net-SNMP's MIB tree, which shouldn't lead to
# false positives so long as sysDescr detection is functioning
SYSOID_VENDOR_MAP = {
    ".1.3.6.1.4.1.9.":     "cisco",
    ".1.3.6.1.4.1.8072.":  "openwrt",
    ".1.3.6.1.4.1.171.":   "dlink",
    ".1.3.6.1.4.1.14988":  "mikrotik",
}

# This gets the default IPv4 address and guesses a /24 network based on that
# If users want something else they can use --network
def get_local_network():
    print("Warning: No network provided, guessing based on default IPv4 address")
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Reserved TEST-NET-1 address used so we do not actually get a connection
    # We just want to know the address assigned on our end
    s.connect(("192.0.2.1", 1))
    ip = s.getsockname()[0]
    s.close()
    prefix = "/24"
    network = str(ipaddress.IPv4Network(f"{ip}{prefix}", strict=False))
    print(f"Guessed {network}")
    return network

# System vendors are identified via the presence of certain OIDs
# and by keywords in SNMPv2-MIB sysDescr
# nmap OS detection is used as a supplement to sysDescr
def detect_vendor(sys_oid, sys_descr, nmap_hints):
    for prefix, vendor_key in SYSOID_VENDOR_MAP.items():
        if sys_oid.startswith(prefix):
            return VENDOR_PROFILES[vendor_key]

    for text in (sys_descr, nmap_hints):
        text = text.lower()
        for profile in VENDOR_PROFILES.values():
            if any(kw in text for kw in profile["keywords"]):
                return profile

    return None

# nmap scan and snimpy data gathering
def scan(network, community, version):
    nm = nmap.PortScanner()
    # Run nmap with our args to scan for SNMP devices
    try:
        nm.scan(hosts=network, arguments="-sU -p161 --open -T4 -O --host-timeout 30s")
    except Exception as e:
        print("nmap scan failed, remember to run this script as root")
        print(f"nmap error message: {e}")
        exit(1)

    print(f"SNMP hosts: {nm.all_hosts()}")

    # Grab some device information using SNMPv2-MIB for identification
    hosts = []
    load("SNMPv2-MIB")
    for ip in nm.all_hosts():
        agent = M(host=ip, community=community, version=version)
        sys_oid   = str(agent.sysObjectID or "")
        sys_descr = str(agent.sysDescr or "")
        sys_name  = str(agent.sysName or "")

        host_data = nm[ip]
        nmap_hints = " ".join([
            host_data.get("osmatch", [{}])[0].get("name", "") if host_data.get("osmatch") else "",
            host_data.hostname(),
        ])

        profile = detect_vendor(sys_oid, sys_descr, nmap_hints)
        hosts.append({
            "ip":       ip,
            "hostname": sys_name or host_data.hostname() or ip,
            "sys_oid":  sys_oid,
            "profile":  profile,
            "label":    profile["label"] if profile else "unknown",
        })

    return hosts

# Build Prometheus config for PyYAML dump
def build_prometheus_config(hosts, auth):
	# Metrics from other applications in the visualizer stack
    static_jobs = [
        {"job_name": "prometheus",    "static_configs": [{"targets": ["prometheus:9090"]}]},
        {"job_name": "grafana",       "static_configs": [{"targets": ["grafana:3000"]}]},
        {"job_name": "goflow2",       "static_configs": [{"targets": ["goflow2:8080"]}]},
        {"job_name": "snmp_exporter", "static_configs": [{"targets": ["snmp-exporter:9116"]}]},
    ]

    # Scrape jobs for snmp-exporter, one per SNMP device, with modules set based on vendor detection
    snmp_jobs = []
    for h in hosts:
        modules = BASE_MODULES + (h["profile"]["extra_modules"] if h["profile"] else [])
        snmp_jobs.append({
            "job_name": f"snmp_{h['label']}_{h['ip'].replace('.', '_')}",
            "static_configs": [{"targets": [h["ip"]], "labels": {"vendor": h["label"], "hostname": h["hostname"]}}],
            "metrics_path": "/snmp",
            "params": {"auth": [auth], "module": modules},
            "relabel_configs": [
                {"source_labels": ["__address__"],    "target_label": "__param_target"},
                {"source_labels": ["__param_target"], "target_label": "instance"},
                {"target_label": "__address__",       "replacement": "snmp-exporter:9116"},
            ],
        })

    # Global configuration options
    # Set metrics update interval at 15 seconds
    return {
        "global": {"scrape_interval": "15s", "evaluation_interval": "15s"},
        "alerting": {"alertmanagers": [{"static_configs": [{"targets": []}]}]},
        "rule_files": None,
        "scrape_configs": static_jobs + snmp_jobs,
    }


def main():
	# Setup args and help
    parser = argparse.ArgumentParser(
                      description='Generates Prometheus configuration for Network Segmentation Visualizer',
                      epilog='For further details check the README')

    parser.add_argument("--auth", default="public_v2", help="snmp-exporter auth module to use for Prometheus (default: public_v2)")
    parser.add_argument("--network", default=None, help='Network to scan in CIDR notation')
    parser.add_argument("--community", default="public", help='SNMP community to scan (default: public)')
    parser.add_argument("--version", type=int, default=2, help='SNMP version to use for scan (default: 2)')
    parser.add_argument("--output-conf", default="../config/prometheus/prometheus.yml", help='Output file for Prometheus configuration (default: ../config/prometheus/prometheus.yml)')
    parser.add_argument("--output-hosts", default="../config/node-map/snmp_devices.csv", help='Output file for node-map SNMP info (default: ../config/node-map/snmp_devices.csv)')
    parser.add_argument("--mibdir", default=(os.getcwd() + "/mibs"), help='Directory to find SNMPv2-MIB in (default: ./mibs)')

    args = parser.parse_args()

    # Set SNMP MIB directory
    snimpy.mib.path(args.mibdir + ":" + snimpy.mib.path())
    print(f"MIBDIRS = {snimpy.mib.path()}")

    network = args.network or get_local_network()
    hosts   = scan(network, args.community, args.version)
    cfg     = build_prometheus_config(hosts, args.auth)
    
    # Warn if the script doesn't find any SNMP hosts at all
    if len(hosts) == 0:
        print("Warning: No SNMP hosts found")

    print(f"{len(hosts)} SNMP host(s)")

    try:
		# Write out prometheus configuration file
        conf_out = os.path.join(args.output_conf)
        os.makedirs(os.path.dirname(conf_out), exist_ok=True)
        with open(conf_out, "w") as f:
            yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)        
        print(f"Wrote {conf_out}")

        # Write out SNMP device information for node map
        nodemap_out = os.path.join(args.output_hosts)
        os.makedirs(os.path.dirname(nodemap_out), exist_ok=True)
        with open(nodemap_out, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["ip", "port", "community"])
            for h in hosts:
                writer.writerow([h["ip"], "161", args.community])
        print(f"Wrote {nodemap_out}")

    # Fail nicely if writing does not work
    except Exception as e:
        print("ERROR: File output failed")
        print(e)
        exit(1)

# Entry point
if __name__ == "__main__":
    main()
