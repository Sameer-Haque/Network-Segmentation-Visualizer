from easysnmp import Session
import asyncio

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

def get_snmp_info(device):
    data = []
    session = Session(hostname=device[0], community=device[2], version=2, remote_port=int(device[1]), use_numeric=True, use_sprint_value=True)
    for ooid in cisco_ooids:
        ooid_info = {}
        for row in session.walk(ooid):
            ooid_info[row.oid_index] = row.value
        data.append(ooid_info)
    return data

async def gather():
    results = await asyncio.gather(*[
        asyncio.to_thread(get_snmp_info, device)
        for device in snmp_devices
    ])
    return results


results = asyncio.run(gather())
print(results)