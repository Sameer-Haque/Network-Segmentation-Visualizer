from easysnmp import Session
from datetime import datetime
from pathlib import Path
import csv
import time
import subprocess
import re

# OIDs
oids = [
    "1.3.6.1.2.1.4.22",         # ArpTable
    "1.3.6.1.2.1.4.20.1.1"      # Router's own IP addresses
]

SNMP_DEVICES_FILE = Path("/node-map/snmp_devices.csv")


def load_snmp_devices(path):
    devices = []
    try:
        with open(path, "r", newline="") as file:
            reader = csv.reader(file)
            for row in reader:
                if not row or row[0].strip().startswith("#"):
                    continue
                row = [col.strip() for col in row]
                if len(row) < 3 or not row[1].isdigit():
                    print(f"[WARN] Skipping malformed row in {path}: {row}")
                    continue
                devices.append(row[:3])
    except FileNotFoundError:
        print(f"[ERROR] {path} not found. No SNMP devices loaded.")
    except Exception as e:
        print(f"[ERROR] Failed to read {path}: {e}")
    return devices


def get_snmp_info(device, oid):
    data = []
    try:
        session = Session(
            hostname=device[0], community=device[2], version=2,
            remote_port=int(device[1]), use_numeric=True,
            use_sprint_value=True, timeout=5, retries=2,
        )
        for row in session.walk(oid):
            data.append(row)
    except Exception as e:
        print(f"[WARN] SNMP walk failed for {device[0]}: {e}")
    return data


def traceroute(ip):
    try:
        result = subprocess.run(
            ["traceroute", "-n", "-q", "1", ip],
            capture_output=True, text=True, timeout=45,
        )
    except Exception as e:
        print(f"[WARN] traceroute failed for {ip}: {e}")
        return []
    data = []
    for line in result.stdout.splitlines():
        match = re.match(r"^\s*(\d+)\s+(\d{1,3}(?:\.\d{1,3}){3})", line)
        if match:
            data.append([int(match.group(1)), match.group(2)])
    return data


def file_path(output_dir, filename):
    return output_dir / filename


def get_node_info(arptable, router_data):
    """
    arptable: list of (source_router_ip, snmp_row) tuples
    router_data: list of (router_ip, walk-result of that router's own IPs)

    Returns:
        nodes: list of [mac, ip]  (end-devices only, routers excluded)
        owner_map: dict {ip: set(router_ip)} -- which router(s) have this
                   ip in their ARP cache. Used to build edges directly,
                   without relying on traceroute.
    """
    excludeip = set()
    for router_ip, addrs in router_data:
        for row in addrs:
            if row.value != router_ip:
                excludeip.add(row.value)

    rows = {}        # key -> [mac, ip]
    owner_map = {}    # ip -> set(router_ip)

    for source_router, info in arptable:
        key = f"{info.oid}{info.oid_index}"[24:]
        row = rows.setdefault(key, ["", ""])
        if info.snmp_type == "OCTETSTR":
            row[0] = info.value
        if info.snmp_type == "IPADDR":
            row[1] = info.value
            # record ownership even for router IPs -- needed for
            # router-to-router edge detection below
            owner_map.setdefault(info.value, set()).add(source_router)
            if info.value in excludeip:
                rows.pop(key, None)

    nodes = [row for row in rows.values() if row[0] and row[1]]
    return nodes, owner_map


def conversion_gafana(nodes, edges, routerips, snmp_devices):
    data = []
    data1 = []
    for index, info in enumerate(nodes):
        devicename = "End Device"
        color = "blue"
        icon = "monitor"
        for device in snmp_devices:
            if info[1] == device[0]:
                devicename = "Router"
                color = "green"
                icon = "sitemap"
                break
        data.append([index, devicename, info[1], info[0], "", color, icon])

    for index, info in enumerate(edges):
        node1 = ""
        node2 = ""
        for node in data:
            if node[2] == info[0]:
                node1 = node[0]
            if node[2] == info[1]:
                node2 = node[0]
            if node1 != "" and node2 != "":
                break
        if node1 == "" or node2 == "":
            for router in routerips:
                for routerip in router[1]:
                    if routerip.value == info[0]:
                        for node in data:
                            if node[2] == router[0]:
                                node1 = node[0]
                    if routerip.value == info[1]:
                        for node in data:
                            if node[2] == router[0]:
                                node2 = node[0]
        data1.append([index, node1, node2, "", "", 1, "", "orange"])

    filename_node_backup = datetime.now().strftime("node_data_%Y-%m-%d_%H-%M-%S.csv")
    filename_nodes = "nodes.csv"
    filename_edge_backup = datetime.now().strftime("edge_data_%Y-%m-%d_%H-%M-%S.csv")
    filename_edge = "edges.csv"
    output_dir_backup = Path("/node-map/NodeGraphCSV/Backups/")
    output_dir_Current = Path("/node-map/NodeGraphCSV/Current/")
    output_dir_backup.mkdir(parents=True, exist_ok=True)
    output_dir_Current.mkdir(parents=True, exist_ok=True)

    with open(file_path(output_dir_Current, filename_nodes), "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["id", "title", "subtitle", "mainstat", "secondarystat", "color", "icon"])
        writer.writerows(data)
    with open(file_path(output_dir_backup, filename_node_backup), "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["id", "title", "subtitle", "mainstat", "secondarystat", "color", "icon"])
        writer.writerows(data)
    with open(file_path(output_dir_Current, filename_edge), "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["id", "source", "target", "mainstat", "secondarystat", "thickness", "highlighted", "color"])
        writer.writerows(data1)
    with open(file_path(output_dir_backup, filename_edge_backup), "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["id", "source", "target", "mainstat", "secondarystat", "thickness", "highlighted", "color"])
        writer.writerows(data1)


def get_edge_info(nodes, owner_map, snmp_devices):
    """
    Build edges primarily from ARP ownership: if exactly one router's ARP
    cache contains a host's IP, that router is its directly-connected
    gateway -- no traceroute needed. Traceroute is only used as a
    fallback when ownership is ambiguous or unknown.

    Also adds router-to-router edges when one router's own IP shows up
    in another router's ARP cache (i.e. they share a transit link).
    """
    router_ips = [d[0] for d in snmp_devices]
    data = []

    for mac, ip in nodes:
        owners = owner_map.get(ip, set())
        if len(owners) == 1:
            data.append([next(iter(owners)), ip])
        elif len(owners) > 1:
            # seen in more than one router's ARP cache -- disambiguate
            # with a traceroute hop
            results = traceroute(ip)
            hop1 = results[0][1] if results else None
            data.append([hop1 if hop1 in owners else sorted(owners)[0], ip])
        else:
            # not present in any known router's ARP cache -- fall back
            # to traceroute to at least get *a* link
            results = traceroute(ip)
            if len(results) >= 2:
                data.append([results[-2][1], results[-1][1]])

    seen_pairs = set()
    for router_a in router_ips:
        for router_b in owner_map.get(router_a, set()):
            if router_b == router_a:
                continue
            pair = tuple(sorted([router_a, router_b]))
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                data.append([router_b, router_a])

    return data


# Main Loop
while True:
    snmp_devices = load_snmp_devices(SNMP_DEVICES_FILE)
    if not snmp_devices:
        print(f"[WARN] No valid SNMP devices loaded from {SNMP_DEVICES_FILE}. Skipping this cycle.")
        time.sleep(300)
        continue

    # Arp Collection -- tag every ARP row with which router it came from
    arptable = []
    routerips = []
    for device in snmp_devices:
        routerips.append((device[0], get_snmp_info(device, oids[1])))
        for row in get_snmp_info(device, oids[0]):
            arptable.append((device[0], row))

    nodes, owner_map = get_node_info(arptable, routerips)

    # de-dupe identical [mac, ip] pairs
    seen = set()
    unique_nodes = []
    for n in nodes:
        key = tuple(n)
        if key not in seen:
            seen.add(key)
            unique_nodes.append(n)
    nodes = unique_nodes

    # edge mapping (ARP-ownership based, traceroute only as fallback)
    edges = get_edge_info(nodes, owner_map, snmp_devices)

    # Node and Edges CSV
    conversion_gafana(nodes, edges, routerips, snmp_devices)
    time.sleep(300)