import configparser

import discord
from discord.ext import tasks, commands
from slack_sdk import WebClient
from substrateinterface import SubstrateInterface

import contact_db
import db

c = configparser.ConfigParser()
c.read("config.ini", encoding='utf-8')
discord_token = str(c["DISCORD"]["token"])
slack_token = str(c["SLACK"]["token"])
discord_mainnet_monitoring_channel = int(c["DISCORD"]["mainnet_monitoring_channel"])
slack_monitoring_channel = str(c["SLACK"]["mainnet_monitoring_channel"])
mainnet_rpc = str(c["GENERAL"]["mainnet_rpc"])
network = "Mainnet"
intents = discord.Intents.all()
intents.messages = True

prefix = 'avail'
bot = commands.Bot(command_prefix=prefix, intents=intents)
slack_client = WebClient(token=slack_token)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('-----------------')
    print("ready")
    await stream_blocks.start()

@tasks.loop(minutes=5)
async def stream_blocks():
    substrate = SubstrateInterface(url=mainnet_rpc, use_remote_preset=True,
                                   type_registry_preset='substrate-node-template')
    notification_channel = bot.get_channel(discord_mainnet_monitoring_channel)

    chain_head_hash = substrate.get_chain_finalised_head()
    chain_head_num = substrate.get_block_number(block_hash=chain_head_hash)
    block_num = db.get_last_saved_block(network)
    while (block_num+730) < chain_head_num:
        for i in range(700, 731):
            block_num = db.get_last_saved_block(network)
            block_num += i

            if block_num % 100 == 0:
                print(f"Fetched block #{block_num}")
            try:
                block = substrate.get_block(block_number=block_num)
                block_hash = block['header']['hash']

                # Fetch block events
                events = substrate.get_events(block_hash=block_hash)
            except Exception as e:
                # print(block_num, e)
                events = []
                block_hash = ""

            for event in events:
                try:
                    # Decode the event
                    event_data = event['event'].value
                    module_id = event_data['module_id']
                    event_id = event_data['event_id']
                    if module_id == 'staking':
                        print(f"Staking block #{block_num}")

                    # If we just started a new session
                    if module_id == 'Session' and event_id == 'NewSession':
                        print(f"Session block #{block_num}")

                        # Get the set of validators in the active set
                        active_validators_temp = list(substrate.query(
                            module='Session',
                            storage_function='Validators',
                            block_hash=block_hash
                        ))
                        active_validators = [str(v) for v in active_validators_temp]
                        #TODO: This part
                        db.update_active_validators(active_validators, network)

                        # Get the session number and offline validators. This will require looping through the events again
                        session_num = 0
                        offline_validators = []
                        for e in events:
                            e_data = e['event'].value
                            m_id = e_data['module_id']
                            e_id = e_data['event_id']
                            if m_id == 'Session' and e_id == 'NewSession':
                                session_num = int(e_data["attributes"]["session_index"])

                        for e in events:
                            e_data = e['event'].value
                            m_id = e_data['module_id']
                            e_id = e_data['event_id']
                            if m_id == 'ImOnline' and e_id == 'AllGood':
                                notification_text=f"No downtime reported in session {session_num-1}."
                                await notification_channel.send(notification_text)
                                slack_client.chat_postMessage(channel=slack_monitoring_channel, text=notification_text)
                                for val_stash in active_validators:
                                    val_id = db.get_validator_id_num(val_stash, network)
                                    validator_offline_count = db.get_validator_offline_count(val_id, session_num, network)
                                    if validator_offline_count is None:
                                        address_id = db.get_validator_identity(val_stash, network)
                                        await send_socials_message(address_id, val_stash, contact_db.get_val_contacts_from_address(val_stash), "active")
                                    elif validator_offline_count > 0:
                                        address_id = db.get_validator_identity(val_stash, network)
                                        await send_socials_message(address_id, val_stash, contact_db.get_val_contacts_from_address(val_stash), "online")
                            # We are looking for when validators are noted as offline
                            if m_id == 'ImOnline' and e_id == 'SomeOffline':
                                notification_text = f"**Session Complete**: {session_num-1}"
                                await notification_channel.send(notification_text)
                                slack_client.chat_postMessage(channel=slack_monitoring_channel, text=notification_text)
                                for offline_val in e_data['attributes']['offline']:
                                    val_stash = offline_val[0]
                                    address_id = db.get_validator_identity(val_stash, network)
                                    print(db.get_validator_id_num(val_stash, network))
                                    if val_stash in active_validators:
                                        offline_validators.append(val_stash)
                                        active_validators.remove(val_stash)
                                        val_id = db.get_validator_id_num(val_stash, network)
                                        validator_offline_count = db.get_validator_offline_count(val_id, session_num, network)
                                        await send_socials_message(address_id, val_stash,
                                                                   contact_db.get_val_contacts_from_address(val_stash),
                                                                   "offline", validator_offline_count + 1)

                                for val_stash in active_validators:
                                    val_id = db.get_validator_id_num(val_stash, network)
                                    validator_offline_count = db.get_validator_offline_count(val_id, session_num, network)
                                    if validator_offline_count is None:
                                        address_id = db.get_validator_identity(val_stash, network)
                                        await send_socials_message(address_id, val_stash, contact_db.get_val_contacts_from_address(val_stash), "active")
                                    elif validator_offline_count > 0:
                                        address_id = db.get_validator_identity(val_stash, network)
                                        await send_socials_message(address_id, val_stash, contact_db.get_val_contacts_from_address(val_stash), "online")

                        db.set_validator_offline_data(session_num, block_num, active_validators, offline_validators, network)

                        inactive_validators = db.get_validators_removed_from_active_set(session_num, network)
                        for val_id in inactive_validators:
                            val_stash = db.get_validator_address(val_id, network)
                            address_id = db.get_validator_identity(val_stash, network)
                            await send_socials_message(address_id, val_stash, contact_db.get_val_contacts_from_address(val_stash), "not active")
                        break

                except Exception as e:
                    print(f"Error processing event: {e}")


async def send_socials_message(identity: str, address: str, contacts: list, message, offline_count=0):
    notification_channel = bot.get_channel(discord_mainnet_monitoring_channel)
    match message:
        case "active":
            if identity == 'null':
                notification_text = f"**{address}** is in the active set."
            else:
                notification_text = f"**{identity}** ({address[:6]}...{address[-6:]}) is in the active set."

        case "not active":
            if identity == 'null':
                notification_text = f"**{address}** is not in the active set."
            else:
                notification_text = f"**{identity}** ({address[:6]}...{address[-6:]}) is not in the active set."
        case "online":
            if identity == 'null':
                notification_text = f"{address} is back online."
            else:
                notification_text = f"{identity} ({address[:6]}...{address[-6:]}) is back online."
        case "offline":
            if identity == 'null':
                notification_text = f"**{address}** has been offline for {offline_count} sessions."
            else:
                notification_text = f"**{identity}** ({address[:6]}...{address[-6:]}) has been offline for {offline_count} sessions."
        case _:
            return

    slack_client.chat_postMessage(channel=slack_monitoring_channel, text=notification_text)

    if len(contacts) != 0:
        notification_text += f" - " + ", ".join(contacts)

    await notification_channel.send(notification_text)

bot.run(discord_token)