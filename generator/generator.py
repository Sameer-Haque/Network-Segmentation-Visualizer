#!/usr/bin/env python3
import argparse
import ipaddress
import os
import socket

import nmap
from snimpy.manager import Manager as M
from snimpy.manager import load
import yaml

BASE_MODULES = ["if_mib", "system", "hrSystem", "hrDevice", "hrStorage"]

VENDOR_PROFILES = {
    "openwrt": {
        "label": "openwrt",
        "extra_modules": ["ip_mib", "ucd_system_stats", "ucd_memory"],
        "keywords": ["openwrt", "lede"],
    },
    "cisco": {
        "label": "cisco",
        "extra_modules": ["cisco_device"],
        "keywords": ["cisco", "ios", "catalyst", "nexus", "asr", "isr"],
    },
    "tplink": {
        "label": "tplink",
        "extra_modules": ["ip_mib"],
        "keywords": ["tp-link", "tplink", "archer", "tl-"],
    },
}

SYSOID_VENDOR_MAP = {
    ".1.3.6.1.4.1.9.":     "cisco",
    ".1.3.6.1.4.1.8072.":  "openwrt",
    ".1.3.6.1.4.1.11863.": "tplink",
}


def get_local_network():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return str(ipaddress.IPv4Network(f"{ip}/24", strict=False))


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


def scan(network, community, version):
    nm = nmap.PortScanner()
    nm.scan(hosts=network, arguments="-sU -p161 --open -T4 -O --host-timeout 30s")

    print(nm.all_hosts())

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


def build_prometheus_config(hosts, community, version):
    auth_name = f"public_v{version}"

    static_jobs = [
        {"job_name": "prometheus",    "static_configs": [{"targets": ["prometheus:9090"]}]},
        {"job_name": "grafana",       "static_configs": [{"targets": ["grafana:3000"]}]},
        {"job_name": "goflow2",       "static_configs": [{"targets": ["goflow2:8080"]}]},
        {"job_name": "snmp_exporter", "static_configs": [{"targets": ["snmp-exporter:9116"]}]},
    ]

    snmp_jobs = []
    for h in hosts:
        modules = BASE_MODULES + (h["profile"]["extra_modules"] if h["profile"] else [])
        snmp_jobs.append({
            "job_name": f"snmp_{h['label']}_{h['ip'].replace('.', '_')}",
            "static_configs": [{"targets": [h["ip"]], "labels": {"vendor": h["label"], "hostname": h["hostname"]}}],
            "metrics_path": "/snmp",
            "params": {"auth": [auth_name], "module": modules},
            "relabel_configs": [
                {"source_labels": ["__address__"],    "target_label": "__param_target"},
                {"source_labels": ["__param_target"], "target_label": "instance"},
                {"target_label": "__address__",       "replacement": "snmp-exporter:9116"},
            ],
        })

    return {
        "global": {"scrape_interval": "15s", "evaluation_interval": "15s"},
        "alerting": {"alertmanagers": [{"static_configs": [{"targets": []}]}]},
        "rule_files": None,
        "scrape_configs": static_jobs + snmp_jobs,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--network",   default=None)
    parser.add_argument("--community", default="public")
    parser.add_argument("--version",   type=int, default=2)
    parser.add_argument("--output",    default="./config")
    args = parser.parse_args()

    network = args.network or get_local_network()
    hosts   = scan(network, args.community, args.version)
    cfg     = build_prometheus_config(hosts, args.community, args.version)

    out = os.path.join(args.output, "prometheus", "prometheus.yml")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)

    print(f"Wrote {out} ({len(hosts)} host(s))")


if __name__ == "__main__":
    main()
