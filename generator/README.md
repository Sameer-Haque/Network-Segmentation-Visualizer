# Prometheus Configuration Generator

This Python script takes a few arguments from the user, scans the network, and creates a scraping configuration for Prometheus based on that information. This is for the purpose of setting up SNMP only. NetFlow/sFlow setup doesn't require any specific configuration on the visualizer host.

```
python3 ./generator.py --help
usage: generator.py [-h] [--network NETWORK] [--community COMMUNITY] [--version VERSION]
                    [--output OUTPUT]

options:
  -h, --help            show this help message and exit
  --network NETWORK
  --community COMMUNITY
  --version VERSION
  --output OUTPUT
```  
