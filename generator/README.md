# Prometheus Configuration Generator

This Python script takes a few arguments from the user, scans the network, and creates a scraping configuration for Prometheus based on that information. This is for the purpose of setting up SNMP and the node map. NetFlow/sFlow setup doesn't require any specific configuration on the visualizer host.

This script is intended to be run from within the generator directory only. It depends on the MIBs located there in the mibs subfolder. If the operating system has SNMPv2-MIB installed natively (e.g. through snmp-mibs-downloader on Debian) then the script can be run anywhere.

```
usage: generator.py [-h] [--auth AUTH] [--network NETWORK]
                    [--community COMMUNITY] [--version VERSION]
                    [--output-conf OUTPUT_CONF] [--output-hosts OUTPUT_HOSTS]
                    [--mibdir MIBDIR]

Generates Prometheus configuration for Network Segmentation Visualizer

options:
  -h, --help            show this help message and exit
  --auth AUTH           snmp-exporter auth module to use for Prometheus
                        (default: public_v2)
  --network NETWORK     Network to scan in CIDR notation
  --community COMMUNITY
                        SNMP community to scan (default: public)
  --version VERSION     SNMP version to use for scan (default: 2)
  --output-conf OUTPUT_CONF
                        Output file for Prometheus configuration (default:
                        ./config/prometheus/prometheus.yml)
  --output-hosts OUTPUT_HOSTS
                        Output file for node-map SNMP info (default:
                        ./config/node-map/snmp_devices.csv)
  --mibdir MIBDIR       Directory to find SNMPv2-MIB in (default: ./mibs)

For further details check the README
```  
