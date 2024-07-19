import configparser
import http.client
import json

import mariadb
from substrateinterface import SubstrateInterface

c = configparser.ConfigParser()
c.read("config.ini", encoding='utf-8')

DB_USER = str(c["DATABASE"]["user"])
DB_PASSWORD = str(c["DATABASE"]["password"])
DB_HOST = str(c["DATABASE"]["host"])
DB_NAME = str(c["DATABASE"]["name"])
PAGERDUTY_TOKEN = str(c["GENERAL"]["pagerduty_token"])

mainnet_rpc = str(c["GENERAL"]["mainnet_rpc"])
turing_rpc = str(c["GENERAL"]["turing_rpc"])


# Connect to MariaDB Platform
def connection():
    try:
        conn = mariadb.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=3306,
            database=DB_NAME
        )

        return conn

    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        exit()


def initial_setup():
    try:
        conn = connection()
        cur = conn.cursor()

        cur.execute("CREATE TABLE validator_info(val_id VARCHAR(10), "
                    "name VARCHAR(50), "
                    "contacts VARCHAR(200), "
                    "missedLatestCheckpointcount INT);")

        cur.close()
        conn.close()
    except mariadb.Error as e:
        print(f"Error: {e}")


def update_active_validators(active_val_list: list, network: str):
    # TODO: Update on-chain identity
    conn = connection()
    cur = conn.cursor()
    if network == 'Turing':
        substrate = SubstrateInterface(url=turing_rpc, use_remote_preset=True,
                                   type_registry_preset='substrate-node-template')
    else:
        substrate = SubstrateInterface(url=mainnet_rpc, use_remote_preset=True,
                                       type_registry_preset='substrate-node-template')

    i=0
    for validator_addr in active_val_list:
        i+=1
        cur.execute(f"SELECT ID "
                    f"FROM {network}ValidatorInfo "
                    f"WHERE ValidatorAddress = '{validator_addr}';")

        val_db_id = cur.fetchone()
        # if this is an unknown validator
        if val_db_id is None:
            # Get the last database ID
            cur.execute(f"SELECT max(ID) "
                        f"FROM {network}ValidatorInfo;")
            next_id = int(cur.fetchone()[0])+1

            # Get the validator's on-chain ID
            identity_info = substrate.query(
                module='Identity',
                storage_function='IdentityOf',
                params=[validator_addr]
            )

            address_id = 'null' if identity_info.value is None else str(identity_info.value[0]["info"]["display"]["Raw"])
            # address_id = re.sub('[^\w\s]+', '', address_id)
            print(address_id)

            # Add validator to ValidatorInfo
            cur.execute(f"INSERT INTO {network}ValidatorInfo "
                        f"VALUES({next_id}, '{validator_addr}', \"{address_id}\", '{network}');")

            # Create a new row with the next incremented ID
            cur.execute(f"ALTER TABLE Validator{network}Monitoring ADD COLUMN val_{next_id} INT;")
            conn.commit()
    conn.close()


def set_validator_offline_data(session_num: int, block_num: int, active_validators: list, offline_validators: list, network: str):
    conn = connection()
    cur = conn.cursor()

    val_dict = {}
    for val in active_validators:
        val_id = get_validator_id_num(val, network)
        val_dict[val_id] = 0
    for val in offline_validators:
        val_id = get_validator_id_num(val, network)
        val_missed_sessions = get_validator_offline_count(val_id, session_num, network) + 1
        val_dict[val_id] = val_missed_sessions

    dict_keys = ", ".join(list(val_dict.keys()))
    dict_values = ", ".join(str(x) for x in list(val_dict.values()))

    command = f"INSERT INTO Validator{network}Monitoring (SessionNumber, BlockNumber, {dict_keys}) VALUES ({session_num}, {block_num}, {dict_values});"


    print(command)
    cur.execute(command)
    conn.commit()
    conn.close()
    return val_dict


def get_validator_offline_count(val_id: str, session_num: int, network: str):
    conn = connection()
    cur = conn.cursor()
    cur.execute(f"SELECT {val_id} FROM Validator{network}Monitoring WHERE SessionNumber = {session_num - 1};")
    val_missed_sessions = cur.fetchone()[0]
    conn.close()
    return val_missed_sessions


def get_validator_id_num(val_stash: str, network: str):
    conn = connection()
    cur = conn.cursor()
    cur.execute(f"SELECT ID FROM {network}ValidatorInfo WHERE ValidatorAddress = '{val_stash}'")
    val_id = f"val_{str(cur.fetchone()[0])}"
    conn.close()
    return val_id


def get_validator_identity(val_stash: str, network: str):
    conn = connection()
    cur = conn.cursor()
    cur.execute(f"SELECT ValidatorID FROM {network}ValidatorInfo WHERE ValidatorAddress = '{val_stash}'")
    val_identity = str(cur.fetchone()[0])
    conn.close()
    return val_identity


def get_validator_address(val_id: str, network: str):
    conn = connection()
    cur = conn.cursor()
    cur.execute(f"SELECT ValidatorAddress FROM {network}ValidatorInfo WHERE ID = '{val_id[4:]}'")
    val_identity = str(cur.fetchone()[0])
    conn.close()
    return val_identity


def get_last_saved_block(network: str):
    conn = connection()
    cur = conn.cursor()
    cur.execute(f"SELECT MAX(BlockNumber) FROM Validator{network}Monitoring;")
    last_saved_block = int(cur.fetchone()[0])
    return last_saved_block


def get_validators_removed_from_active_set(latest_session: int, network: str):
    # https://chatgpt.com/share/0d712ea0-4e30-48c2-8bdd-859bd3cb8b18
    conn = connection()
    cursor = conn.cursor()

    # Fetch column names
    cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Validator{network}Monitoring'")
    columns = [col[0] for col in cursor.fetchall()]

    # Fetch the rows with ID 1 and ID 2
    cursor.execute(f"SELECT * FROM Validator{network}Monitoring WHERE SessionNumber = {latest_session-1}")
    row_id1 = cursor.fetchone()

    cursor.execute(f"SELECT * FROM Validator{network}Monitoring WHERE SessionNumber = {latest_session}")
    row_id2 = cursor.fetchone()

    # Close the connection
    cursor.close()
    conn.close()

    # Find columns with NULL in row with ID 2 and non-NULL in row with ID 1
    columns_with_null_id2_non_null_id1 = []
    for i, col in enumerate(columns):
        if row_id2[i] is None and row_id1[i] is not None:
            columns_with_null_id2_non_null_id1.append(col)

    return columns_with_null_id2_non_null_id1


def create_pagerduty_alert(validator: int, num_missed: int):
    json_payload = {
      "payload": {
        "summary": f"Polygon validator {validator} has missed {num_missed} checkpoints.",
        "source": "Polygon Checkpoints",
        "severity": "critical"
      },
      "routing_key": "64737e7a4bbf490ad09f45d7aeffc3ce",
      "dedup_key": "polygon_checkpoints",
      "event_action": "trigger",
      "client": "Polygon"
    }

    headers = {
        'Content-Type': "application/json",
        'Accept': "application/vnd.pagerduty+json;version=2",
        'From': "Polygon",
        'Authorization': f"Token token={PAGERDUTY_TOKEN}"
    }
    conn = http.client.HTTPSConnection("events.pagerduty.com")
    conn.request("POST", "/v2/enqueue", json.dumps(json_payload), headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))


def resolve_pagerduty_alert():
    json_payload = {
      "payload": {
        "summary": "Polygon validator signed the latest checkpoint.",
        "source": "Polygon Checkpoints",
        "severity": "critical"
      },
      "routing_key": "64737e7a4bbf490ad09f45d7aeffc3ce",
      "dedup_key": "polygon_checkpoints",
      "event_action": "resolve",
      "client": "Polygon"
    }

    headers = {
        'Content-Type': "application/json",
        'Accept': "application/vnd.pagerduty+json;version=2",
        'From': "Polygon",
        'Authorization': f"Token token={PAGERDUTY_TOKEN}"
    }
    conn = http.client.HTTPSConnection("events.pagerduty.com")
    conn.request("POST", "/v2/enqueue", json.dumps(json_payload), headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))


