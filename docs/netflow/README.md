# Netflow Setup

Setting up Netflow or IPFIX to work with the visualizer is fairly straightforward. The visualizer accepts flows on UDP port 2055, and no configuration is required on the visualizer side. Any routers that are to provide flows to the visualizer do need to have some sort of Netflow software running and have it pointed at the visualizer.

## OpenWRT

Netflow setup on OpenWRT is simple. First, install softflowd, a Netflow daemon available in OpenWRT's package repository:

```
opkg update
opkg install softflowd
```

You can check the configuration with uci:

```
uci show softflowd
```

At minimum, you will need to enable softflowd and configure it to send flows to the visualizer. Replace '0' with the number of whatever instance of softflowd you are configuring, and '192.168.1.7' with the IP of your visualizer host:

```
uci set softflowd.@softflowd[0].enabled='1'
uci set softflowd.@softflowd[0].host_port='192.168.1.7:2055'
```

You should probably set the sampling rate to 1, in order to sample all packets:

```
uci set softflowd.@softflowd[0].sampling_rate='1'
```

While the visualizer's collector does support Netflow v5, it is strongly recommended to use Netflow v9, so set that version:

```
uci set softflowd.@softflowd[0].export_version='9'
```

Do not forget to commit your changes:

```
uci commit
```

Now restart softflowd to make sure the new configuration is applied:

```
service softflowd restart
```

You can find some additional information in this [guide.](https://m00nie.com/install-and-verify-softflowd-netflow-on-openwrt/ "softflowd guide")

## Cisco

First, get into configuration mode:

```
enable
configure terminal
```

Setup the IOS flow exporter. Swap out the placeholders (all CAPS):

```
flow exporter EXPORTER-NAME
description DESCRIPTION
destination {IP-ADDRESS | HOSTNAME} [vrf VRF-NAME]
dscp DSCP
source interface-type interface-number
output-features
template data timeout seconds
transport udp udp-port
ttl seconds
end 
```

Do not forget to commit your changes:

```
copy running-config startup-config
```

For valid values, consult the [Cisco documentation](https://www.cisco.com/c/en/us/td/docs/routers/ios/config/17-x/ntw-servs/b-network-services/m_fnf-ipfix-export.html "Cisco docs") for more information.