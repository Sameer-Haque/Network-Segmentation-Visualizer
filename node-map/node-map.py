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
# SNMP Devices
snmp_devices = [
    ["192.168.10.1","161","public"],
    ["192.168.20.1","161","public"]
]

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
    
def conversion_gafana(arptable,edges):
    data = []
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
        data.append([index, devicename, info[0], info[1], "", color, icon])
    filename_node_backup = datetime.now().strftime("node_data_%Y-%m-%d_%H-%M-%S.csv")
    filename_nodes = "nodes.csv"
    filename_edge_backup = datetime.now().strftime("edge_data_%Y-%m-%d_%H-%M-%S.csv")
    filename_edge = "edges.csv"
    output_dir_backup = Path("/node-map/NodeGraphCSV/Backup/")
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
        writer.writerow(["id","title","subtitle","mainstat","secondarystat","color","icon"])
        writer.writerows(data)
    with open(file_path(output_dir_Current,filename_edge_backup), "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["id","title","subtitle","mainstat","secondarystat","color","icon"])
        writer.writerows(data)

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
    #Node CSV
    conversion_gafana(nodes,edge)
    time.sleep(300)