# SNMP Exporter Config Generation

This README explains the process for generating the snmp-exporter config for OpenWRT. These instructions can be modified to produce configs for other vendors. The testing setup under "docs/vbox-test-setup" was used for the example.

## Requirements

- Internet access
- Debian system or similar
- Recent version of snmp-exporter (https://github.com/prometheus/snmp_exporter)
- snmp-exporter config generator dependencies (see README linked below)
- Visualizer testing setup with desired vendor devices

## Process

1. Obtain vendor MIBs
2. Compile snmp-exporter config generator
3. Create config (generator.yml) for generator
4. Run generator against obtained vendor MIBs
5. Debug errors
6. Test generated snmp.yml

## Example (OpenWRT)

### Obtaining vendor MIBs

You can copy the MIBs from an OpenWRT router with them installed. Another option is to just download the package from OpenWRT's download site and extract the MIBs. Both options are outlined here.

#### Install MIBs on OpenWRT and copy them

You can install the snmp-mibs package on OpenWRT through the HTTP GUI (LuCI) or CLI (opkg/apk via SSH).

**HTTP GUI (LuCI)**

![Image](https://raw.githubusercontent.com/Sameer-Haque/Network-Segmentation-Visualizer/refs/heads/main/docs/snmp/openwrt-install-snmp-mibs-luci.png "OpenWRT LuCI")

Login via HTTP, then go to "Software" under the "System" menu. Hit "Update lists..." and then search for and install the "snmp-mibs" package.

**CLI (opkg via SSH)**

![Image](https://raw.githubusercontent.com/Sameer-Haque/Network-Segmentation-Visualizer/refs/heads/main/docs/snmp/openwrt-install-snmp-mibs-opkg.png "OpenWRT LuCI")

SSH and login as root on the OpenWRT device, then:

```
opkg update
opkg install snmp-mibs
```

Then copy the installed files from the router.

![Image](https://raw.githubusercontent.com/Sameer-Haque/Network-Segmentation-Visualizer/refs/heads/main/docs/snmp/openwrt-scp-snmp-mibs.png "OpenWRT LuCI")

```
scp -Or root@<ip addr>:/usr/share/snmp/mibs ./
```

#### Download package and extract MIBs

![Image](https://raw.githubusercontent.com/Sameer-Haque/Network-Segmentation-Visualizer/refs/heads/main/docs/snmp/openwrt-snmp-mibs-web-download.png "OpenWRT LuCI")

You can grab the package from https://downloads.openwrt.org/releases/packages-24.10/x86_64/packages/.

Then extract the package contents.

```
tar zxf snmp-mibs_*.ipk
```

The MIBs are located in the 'data.tar.gz' file.

### Obtaining snmp-exporter and compiling the generator

First, install dependencies.

```
apt-get install unzip build-essential libsnmp-dev curl golang-go git
```

Clone the repository and enter it.

```
git clone https://github.com/prometheus/snmp_exporter
cd snmp_exporter
```

Switch to the "generator" subdirectory and compile the generator.

```
cd generator
make generator
```

### Creating the generator config (generator.yml)

Go read the README for the snmp_exporter generator, which is linked below. Then backup the default generator.yml and write your own replacement generator.yml with the OIDs you need to walk.

The config used for this example is located [here](https://raw.githubusercontent.com/Sameer-Haque/Network-Segmentation-Visualizer/refs/heads/main/docs/snmp/generator-openwrt-example.yml "generator.yml OpenWRT example").

### Run generator

![Image](https://raw.githubusercontent.com/Sameer-Haque/Network-Segmentation-Visualizer/refs/heads/main/docs/snmp/snmp-exporter-generator-openwrt.png "OpenWRT LuCI")

Make sure your generator.yml is in place and then run the generator against your MIBs.

```
MIBDIRS='<insert dir with vendor MIBs>' ./generator --fail-on-parse-errors generate --output-path='<insert path to write config to>'
```

### Debug errors

If you get errors you can run the generator in a more verbose mode.

```
MIBDIRS='<insert dir with vendor MIBs>' ./generator --fail-on-parse-errors parse_errors --output-path='<insert path to write config to>'
```

### Test generated snmp.yml

Backup your visualizer snmp.yml, place your newly generated snmp.yml, restart the visualizer, and see if it works.

## Useful Resources

Cloning the GitHub links just in case GitHub goes down again might be a good idea.

- [snmp-exporter config generator code and README (GitHub)](https://github.com/prometheus/snmp_exporter/tree/main/generator "snmp-exporter generator")
- [Observium SNMP MIB Database](https://mibs.observium.org/ "Observium MIB Browser")
- [MIB Explorer](https://mib-explorer.com/en/ "MIB Explorer")
- [librenms MIB collection (GitHub)](https://github.com/librenms/librenms/tree/master/mibs "librenms/mibs")
- [Observium MIB collection (GitHub)](https://github.com/pgmillon/observium/tree/master/mibs "observium/mibs")
- [Ferroin's MIB collection (GitHub)](https://github.com/Ferroin/snmp-mibs-collection "Ferroin/snmp-mibs-collection")
- [SNMP-MIB-Compiler MIB collection (GitHub)](https://github.com/jimbobhickville/SNMP-MIB-Compiler/tree/master/mibs "SNMP-MIB-Compiler/mibs")

