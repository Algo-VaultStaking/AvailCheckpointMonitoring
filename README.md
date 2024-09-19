## Intro

## Set up The Database
I use a MariaDB database deployed on AWS RDS. A free-tier sized database will work.


### Create the database
``` sql
CREATE DATABASE AvailMonitoring;
```

### Create and seed the MainnetValidatorInfo table
``` sql
CREATE TABLE MainnetValidatorInfo (
    ID INT PRIMARY KEY,
	ValidatorAddress VARCHAR(50) UNIQUE NOT NULL,
    ValidatorID VARCHAR(150) CHARACTER SET UTF8,
    Network VARCHAR(16)
);

INSERT INTO MainnetValidatorInfo VALUES(0, '5D', 'blank', 'none');
```

### Create and seed the TuringValidatorInfo table
``` sql
CREATE TABLE TuringValidatorInfo (
    ID INT PRIMARY KEY,
	ValidatorAddress VARCHAR(50) UNIQUE NOT NULL,
    ValidatorID VARCHAR(150) CHARACTER SET UTF8,
    Network VARCHAR(16)
);

INSERT INTO TuringValidatorInfo VALUES(0, '5D', 'blank', 'none');
```

### Create and seed the ValidatorMainnetMonitoring table
``` sql
CREATE TABLE ValidatorMainnetMonitoring (
	SessionNumber INT NOT NULL,
    BlockNumber INT NOT NULL,
    ChainName INT NOT NULL
);

Insert into ValidatorMainnetMonitoring VALUES(0, 0, 'Mainnet');
```

### Create and seed the ValidatorTuringMonitoring table
``` sql
CREATE TABLE ValidatorTuringMonitoring (
	SessionNumber INT NOT NULL,
    BlockNumber INT NOT NULL,
    ChainName INT NOT NULL
);

Insert into ValidatorTuringMonitoring VALUES(0, 0, 'Turing');
```

### Create and seed the ValidatorMainnetEras table
``` sql
CREATE TABLE ValidatorMainnetEras (
	EraNumber INT NOT NULL,
    BlockNumber INT NOT NULL,
    NumberOfBlocks INT NOT NULL,
    NumberActiveValidators INT NOT NULL,
    ValidatorPayout INT NOT NULL
);

INSERT INTO ValidatorMainnetEras VALUES(0, 4317, 4317, 8, 273897);
```

### Create the ValidatorContacts table
``` sql
CREATE TABLE ValidatorContacts (
    ValidatorAddress VARCHAR(50) NOT NULL,
    Contact VARCHAR(25) NOT NULL,
    Network VARCHAR(16)
);
```



## Download the Code
``` bash
git clone git@github.com:Algo-VaultStaking/AvailCheckpointMonitoring.git
```

## Setup
Copy the config.ini.example to config.ini and fill in the following properties:

```
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
docker run --name avail-monitoring -d avail-monitoring
```

## Logs

Check and follow the docker logs:
``` bash
docker logs avail-monitoring -f
```