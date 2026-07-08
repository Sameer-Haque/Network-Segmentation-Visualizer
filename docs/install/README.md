# Network Visualizer Installation Guide

This project should be functional on any platform with Docker Compose and Python 3 available.

## Example setup (Debian 13)

First, install Debian. You can use a minimal install or a full desktop install.

You should setup Docker's apt repository according to the instructions on their [website.](https://docs.docker.com/engine/install/debian/ "Docker Docs")

Once Docker's apt repository and signing key are setup, you can install Docker Compose as root:

```
su root
apt-get update
apt-get install docker-compose
```

Then install the required Python dependencies for the Prometheus configuration generator. This is not technically required for the visualizer itself to run, but the automatic configuration generator needs these modules:

```
su root
apt-get update
apt-get install python3-nmap python3-yaml python3-snimpy python3-zombie-imp
```

Make sure you have Git:

```
su root
apt-get update
apt-get install git
```

Now you can clone the project, make sure some permissions are set correctly, and generate some required configuration files. It is strongly recommended to first read the generator script [README:](https://github.com/Sameer-Haque/Network-Segmentation-Visualizer/blob/main/generator/README.md "generator.py README")

```
git clone https://github.com/Sameer-Haque/Network-Segmentation-Visualizer
cd Network-Segmentation-Visualizer
chmod -Rv a+w config/grafana/lib
su root
cd generator
python3 ./generator.py
cd ../
```

Then you can start up the visualizer:

```
su root
docker compose up -d --force-recreate
```

The Grafana interface for dashboards and alerting should be available over HTTP on port 3000. This should be accessible using any recent web browser, and has been tested on Mozilla Firefox ESR 140.
