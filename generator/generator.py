import sys
import argparse
import nmap

def main(argv):
    print(argv)
    target = '127.0.0.1' # PLACEHOLDER
    port = '161' # SNMP port
    nm = nmap.PortScanner()
    # Scan targets on given ports
    nm.scan(target, port)
    print(nm.all_hosts())
    # Print out each scanned host's information
    for host in nm.all_hosts():
        print("==== nmap host scan begin ====")
        print("Host: %s" % (host))
        print("State: %s" % (nm[host].state()))
        # Print info for each scanned protocol (TCP, UDP, etc.)
        for proto in nm[host].all_protocols():
            print("==== %s ====" % proto)
            open_ports = nm[host][proto].keys()
            # Print state of each port
            for port in open_ports:
                print("Port: %s  State: %s" % (port, nm[host][proto][port]['state']))
        print("==== nmap host scan end ====")
    return 0

if __name__ == "__main__":
    main(sys.argv)
