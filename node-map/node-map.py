from easysnmp import Session
from datetime import datetime
from pathlib import Path
import asyncio
import csv
import time
# OIDs
cisco_ooids = [
    "1.3.6.1.2.1.2.2.1.2",
    "1.3.6.1.2.1.2.2.1.6",
    "1.3.6.1.2.1.4.20.1.2"   
]
# SNMP Devices
snmp_devices = [
    ["172.16.0.50","161","cisco-c1900"],
    ["172.16.0.50","161","cisco-c1900"]
]
def get_snmp_info(device,ooid):
    data = []
    session = Session(hostname=device[0], community=device[2], version=2, remote_port=int(device[1]), use_numeric=True, use_sprint_value=True)
    for row in session.walk(ooid):
        data.append(row)
    return data
def get_node_info(arptable):
    data = []
    duplicate = False
    for info in arptable:
        key = f"{info.oid}{info.oid_index}"[24:]
        for row in data:
            if key == row[0]:
                if info.snmp_type == "OCTETSTR":
                    row[1] = info.value 
                if info.snmp_type == "IPADDR":
                    row[2] = info.value
                duplicate = True
                break 
        if duplicate == False:
            data.append([key,"",""])
        duplicate = False
    for row in data:
        del row[0]
    return data
def conversion_gafana(arptable):
    data = []
    for index, info in enumerate(arptable):
        for device in snmp_devices:
            devicename = "End Device"
            color = "blue"
            icon = "monitor"
            if info[1] == device [0]:
                devicename = "Router"
                color = "green"
                icon = "sitemap"
        data.append([index, devicename, info[0], info[1], "", color, icon])
    filename = datetime.now().strftime("node_data_%Y-%m-%d_%H-%M-%S.csv")
    output_dir = Path("/")
    file_path = output_dir / filename
    with open(file_path, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["id","title","subtitle","mainstat","secondarystat","color","icon"])
        writer.writerows(data)
    return str(file_path)
#Main Loop
while True:
    #Arp Collection
    arptable = []
    seen = set()
    i = 0
    for device in snmp_devices:
        arptable.extend(get_snmp_info(device, "Arpooid"))
    nodes = get_node_info(arptable)
    while i < len(nodes):
        row_key = tuple(nodes[i])
        if row_key in seen:
            nodes.pop(i)
        else:
            seen.add(row_key)
            i += 1
    #Node CSV
    conversion_gafana(nodes)
    time.sleep(300)