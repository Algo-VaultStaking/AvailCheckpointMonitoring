## Download
``` bash
git clone git@github.com:Algo-VaultStaking/AvailCheckpointMonitoring.git
```

## Setup
Copy the config.ini.example to config.ini and fill in the following properties:

``` toml 
[GENERAL]
pagerduty_token = [Not required for outside deployments]
mainnet_rpc = [public or private RPC websocket address]
turing_rpc = [public or private RPC websocket address]

[DISCORD]
token = [72 character discord token]
mainnet_monitoring_channel = [channel ID to send mainnet alerts]
turing_monitoring_channel = [channel ID to send turing alerts]

[SLACK]
token = [57 character slack token]
mainnet_monitoring_channel = [slack channel name to send mainnet alerts]
turing_monitoring_channel = [slack channel name to send turing alerts]

[DATABASE]
user = [Database username]
password = [Database password]
host = [Database host; AWS RDS MariaDB instance]
name = [Database name]
```

## Run 
Build the docker image using the included Dockerfile:

``` bash
docker build -t avail-monitoring ~/AvailCheckpointMonitoring/
```

Run the newly created docker image:
``` bash
docker run --name avail-monitoring -d avail-monitoring`
```

## Logs

Check and follow the docker logs:
``` bash
docker logs avail-monitoring -f
```