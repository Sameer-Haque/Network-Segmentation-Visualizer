# Network Visualizer Testing Setup (Virtualbox-based)

## Requirements:
- Oracle Virtualbox 7
- Debian 13 AMD64 netinstall ISO ( See [0] )
- OpenWRT 24.10.5 x86-64 generic ext4 combined IMG ( See [1] )

## Central router setup:
![Image](https://raw.githubusercontent.com/Sameer-Haque/Network-Segmentation-Visualizer/refs/heads/main/docs/vbox-test-setup/vbox-testing-openwrt-vbox-settings.png "VBox Screenshot")
- Create a new VM for Other Linux
- defaults are mostly fine, do NOT create a hard drive
- Follow the OpenWRT Virtualbox guide to install OpenWRT ( See [2] )
- Setup network interfaces, details below

## Metrics machine setup:
![Image](https://raw.githubusercontent.com/Sameer-Haque/Network-Segmentation-Visualizer/refs/heads/main/docs/vbox-test-setup/vbox-testing-debian-visualizer-vbox-settings.png "VBox Screenshot")
- Create a new VM for Debian
- Default settings are mostly fine. Make sure you have at least 2048MB of RAM. 1 CPU is fine.
- Set the network interface to one of the internal networks

## Client/server machines
![Image](https://raw.githubusercontent.com/Sameer-Haque/Network-Segmentation-Visualizer/refs/heads/main/docs/vbox-test-setup/vbox-testing-debian-client-vbox-settings.png "VBox Screenshot")
- Just spin up some more Debian VMs, default settings should be fine
- Just remember to set the network interface to one of the internal networks

## Network setup
In the "Interfaces" menu in LuCI:
![Image](https://raw.githubusercontent.com/Sameer-Haque/Network-Segmentation-Visualizer/refs/heads/main/docs/vbox-test-setup/vbox-testing-openwrt-interfaces.png "VBox Screenshot")
In the "Firewall" menu in LuCI:
![Image](https://raw.githubusercontent.com/Sameer-Haque/Network-Segmentation-Visualizer/refs/heads/main/docs/vbox-test-setup/vbox-testing-openwrt-firewall.png "VBox Screenshot")
The OpenWRT VM should have 4 interfaces:
- Adapter 1 should be a host-only adapter setup as management interface as in the guide [2]
- Adapter 2 should be set to "NAT" and setup as WAN in OpenWRT
- Adapter 3 should be set to "Internal Network"
- Adapter 4 should be set to "Internal Network"

The networks for adapters 3 and 4 should be different.

## Notes

### Missing Netflow template error

If you experience errors due to a missing Netflow template, this is likely because you restarted the application and OpenWRT's softflowd has not re-sent it. You can SSH into OpenWRT and use the following command to tell softflowd to send the template again:

```softflowctl send-template```

### References:

[0] - https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/

[1] - https://downloads.openwrt.org/releases/24.10.5/targets/x86/64/

[2] - https://openwrt.org/docs/guide-user/virtualization/virtualbox-vm
