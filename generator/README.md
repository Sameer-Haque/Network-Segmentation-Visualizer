# Prometheus Configuration Generator

This Python script takes a few arguments from the user, scans the network, and creates a scraping configuration for Prometheus based on that information. This is for the purpose of setting up SNMP only. NetFlow/sFlow setup doesn't require any specific configuration on the visualizer host.

```
usage: generator.py [-h] [--auth AUTH] [--network NETWORK]
                    [--community COMMUNITY] [--version VERSION]
                    [--output-conf OUTPUT_CONF] [--output-hosts OUTPUT_HOSTS]

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

For further details check the README
```  
