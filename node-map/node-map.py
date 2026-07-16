from easysnmp import Session
from datetime import datetime
from pathlib import Path
import asyncio
import csv
import time
import subprocess
import re
# OIDs
cisco_ooids = [
    "1.3.6.1.2.1.4.22",         #ArpTable
    "1.3.6.1.2.1.4.20.1.1"      #Router IP
]

SNMP_DEVICES_FILE = Path("/node-map/snmp_devices.csv")
snmp_devices = []

with open(SNMP_DEVICES_FILE, "r", newline="") as f:
    reader = csv.reader(f)
    for row in reader:
        snmp_devices.append(row)
        print(snmp_devices)

def get_snmp_info(device,ooid):
    data = []
    session = Session(hostname=device[0], community=device[2], version=2, remote_port=int(device[1]), use_numeric=True, use_sprint_value=True)
    for row in session.walk(ooid):
        data.append(row)
    return data

def traceroute(ip):
    result = subprocess.run(
        ["traceroute", "-n", "-q", "1", ip],
        capture_output=True,
        text=True,
        timeout=45
    )
    data = []
    for line in result.stdout.splitlines():
        match = re.match(
            r"^\s*(\d+)\s+(\d{1,3}(?:\.\d{1,3}){3})",
            line
        )
        if match:
            data.append([
                int(match.group(1)),
                match.group(2)
            ])
    return data

def file_path(output_dir, filename):
    return output_dir / filename

def get_node_info(arptable, router_data):
    data = []
    excludeip = set()
    for ip in router_data:
        for row in ip[1]:
            if row.value != ip[0]:
                excludeip.add(row.value)
    duplicate = False
    for info in arptable:
        todelete = False
        key = f"{info.oid}{info.oid_index}"[24:]
        for row in data:
            if key == row[0]:
                if info.snmp_type == "OCTETSTR":
                    row[1] = info.value 
                if info.snmp_type == "IPADDR":
                    if info.value in excludeip:
                        todelete = True
                    row[2] = info.value
                duplicate = True
                break 
        if duplicate == False:
            data.append([key,"",""])
        duplicate = False
        if todelete == True:
            data[:] = [row for row in data if row[0] != key]
    for row in data:
        del row[0]
    return data
    
def conversion_gafana(arptable,edges,routerips):
    data = []
    data1 = []
    for index, info in enumerate(arptable):
        for device in snmp_devices:
            devicename = "End Device"
            color = "blue"
            icon = "monitor"
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
        data1.append([index, node1, node2,"","", 1 , "", "orange"])

    filename_node_backup = datetime.now().strftime("node_data_%Y-%m-%d_%H-%M-%S.csv")
    filename_nodes = "nodes.csv"
    filename_edge_backup = datetime.now().strftime("edge_data_%Y-%m-%d_%H-%M-%S.csv")
    filename_edge = "edges.csv"
    output_dir_backup = Path("/node-map/NodeGraphCSV/Backups/")
    output_dir_Current = Path("/node-map/NodeGraphCSV/Current/")

    with open(file_path(output_dir_Current,filename_nodes), "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["id","title","subtitle","mainstat","secondarystat","color","icon"])
        writer.writerows(data)
    with open(file_path(output_dir_backup,filename_node_backup), "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["id","title","subtitle","mainstat","secondarystat","color","icon"])
        writer.writerows(data)
    with open(file_path(output_dir_Current,filename_edge), "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["id","source","target","mainstat","secondarystat","thickness","highlighted", "color"])
        writer.writerows(data1)
    with open(file_path(output_dir_backup,filename_edge_backup), "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["id","source","target","mainstat","secondarystat","thickness","highlighted", "color"])
        writer.writerows(data1)

def get_edge_info(arptable):
    data = []
    closest_router = ""
    for ip in snmp_devices:
        results = traceroute(ip[0])
        count = len(results)
        if count == 1:
            closest_router = ip[0]
            break
    for ip in arptable:
        results = traceroute(ip[1])
        count = len(results)
        if count == 0:
            continue
        if count == 1:
            data.append([closest_router, ip[1]])
        else:
           data.append([results[count-2][1], results[count-1][1]]) 
    if closest_router == "":
        with open("no_closest_router.txt", "w") as file:
            file.write("no closest router")
    return data

#Main Loop
while True:
    #Arp Collection
    arptable = []
    routerips = []
    seen = set()
    i = 0
    for device in snmp_devices:
        routerips.append((device[0], get_snmp_info(device,cisco_ooids[1])))
        arptable.extend(get_snmp_info(device, cisco_ooids[0]))
    nodes = get_node_info(arptable,routerips)
    while i < len(nodes):
        nodes[i][0] = nodes[i][0].strip('"')
        nodes[i][1] = nodes[i][1].strip('"')
        if nodes[i][0] == "" or nodes[i][1] == "":
            nodes.pop(i)
            continue
        row_key = tuple(nodes[i])
        if row_key in seen:
            nodes.pop(i)
        else:
            seen.add(row_key)
            i += 1
    #trace route mapping
    edges = get_edge_info(nodes)
    #Node and Edges CSV
    conversion_gafana(nodes,edges,routerips)
    time.sleep(300)
