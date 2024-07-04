network = "turing"
def get_val_contacts_from_address(db_connection, val_addr: str):
    conn = db_connection
    cur = conn.cursor()
    command = f"SELECT Contact FROM ValidatorContacts WHERE ValidatorAddress = '{val_addr}';"
    try:
        cur.execute(command)
        result = cur.fetchall()
        contact_list = []
        # TODO Verify this works
        for contact in result:
            contact_list.append(contact[0])
    except Exception as e:
        contact_list = None
    return contact_list


def add_val_contact_for_address(db_connection, val_addr: str, contact: str):
    cur = db_connection.cursor()
    command = f"INSERT INTO ValidatorContacts (ValidatorAddress, Contact, Network) VALUES ('{val_addr}', '{contact}', '{network}');"
    cur.execute(command)
    db_connection.commit()


def remove_val_contact_for_address(db_connection, val_addr: str, contact: str):
    cur = db_connection.cursor()
    command = f"DELETE FROM ValidatorContacts WHERE ValidatorAddress='{val_addr}' AND Contact='{contact}';"
    cur.execute(command)
    db_connection.commit()

    return None