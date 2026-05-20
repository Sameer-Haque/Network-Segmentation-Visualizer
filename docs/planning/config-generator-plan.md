# Network Segmentation Visualizer – Phase 2

## Technical Plan for Configuration Generator

__Group 5__

- Edwin Downton
- Sameer Haque
- Andrew Russel
- Taha Siraj

__Contents__

- Feature Outline
- Feature Components
- References

__GitHub Links__

[Project Repository](github.com/Sameer-Haque/Network-Segmentation-Visualizer "Project Repository")

[Project README](https://github.com/Sameer-Haque/Network-Segmentation-Visualizer/blob/main/README.md "Project README")



## Outline
The generator should be a script which scans the local network and creates an appropriate configuration for Prometheus to use for gathering network data. The goal of this generator is to assist the user in setting up the Network Visualizer. Some user prompting or preconfiguration will be needed to provide required private information, like SNMP community strings and passwords.

### Other considerations

- Should we also use this to provide an initial state for the node map?

No. Config generation and node map generation should be kept separate for modularity.

- Can this be reused for updating the node map?

See previous question.

- Should any other information besides SNMP configurations be provided by the user?

Seeing as the data storage, processing, and Netflow/sFlow collector configurations do not require any network-specific information to function, they can remain static. Miscellaneous options like the Grafana password can be configured in-application. SNMP credentials, community names, and potentially device vendor information are the only essential pieces of information that may have to be specified by the user for the purposes of the Prometheus configuration.



## Components 
Scripting language: [Python 3][0] 
File formats supported: YAML 
YAML library: [PyYAML][1]
Network mapping tool: [nmap][2]
nmap library: [python-nmap][3]

The generator should be a Python script run by the end user as setup for the application. The script can be rerun to regenerate the configuration in the event of changes to the network SNMP configuration. When regenerating, the old configuration files should be backed up, not overwritten. The basic program flow should be something like this:

1. Get required SNMP information from user prompting/arguments/config file
2. Use nmap to scan for SNMP endpoints and determine device vendors if possible
3. Select appropriate vendor SNMP MIB configuration
4. Construct and install Prometheus configuration



## References 

[0]: https://docs.python.org/3/library/index.html "Python Docs"
{0} https://docs.python.org/3/library/index.html "Python Docs"

[1]: https://pypi.org/project/PyYAML/ "PyYAML Project"
{1} https://pypi.org/project/PyYAML/

[2]: https://nmap.readthedocs.io/en/latest/nmap.html "nmap Docs"
{2} https://nmap.readthedocs.io/en/latest/nmap.html

[3]: https://pypi.org/project/python3-nmap/ "python3-nmap Project"
{3} https://pypi.org/project/python3-nmap/
