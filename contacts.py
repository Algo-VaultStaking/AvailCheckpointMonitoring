
import configparser
import re

import discord
from discord import app_commands
from discord.ext import commands, tasks
from substrateinterface import SubstrateInterface

import contact_db
import db

c = configparser.ConfigParser()
c.read("config.ini", encoding='utf-8')
token = str(c["DISCORD"]["token"])
MISSED_CHECKPOINTS_CHANNEL = int(c["DISCORD"]["monitoring_channel"])
intents = discord.Intents.all()
intents.messages = True

prefix = 'avail'
bot = commands.Bot(command_prefix=prefix, intents=intents)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('-----------------')
    print("ready")
    # synced = await bot.tree.sync()
    # print(f"Synced {len(synced)} commands")


@bot.command(name='version', help='')
@commands.has_any_role("Mod", "team", "admin")
async def version(ctx):
    await ctx.send("v0.1.1")


@bot.tree.command(name="show-contacts", description="Show contacts for a specific validator.")
@app_commands.describe(validator_address="The validator address.")
async def contacts(interaction: discord.Interaction, validator_address: str):
    db_connection = db.connection()
    validator_name = db.get_validator_identity(validator_address)
    contacts = contact_db.get_val_contacts_from_address(db_connection, validator_address)
    # TODO: Make sure this isn't validator_name != ""
    if validator_name is not None:
        message = f"{validator_name} has the following contacts: {', '.join(contacts)}"
    else:
        message = f"{validator_address} has the following contacts: {', '.join(contacts)}"
    await interaction.response.send_message(message)
    db_connection.close()


@bot.tree.command(name="add-contact", description="Add a contact to a validator.")
@app_commands.describe(validator_address="The validator address", user="The user to be alerted")
async def contacts_add(interaction: discord.Interaction, validator_address: str, user: str):
    db_connection = db.connection()
    # TODO: verify the user is a discord user
    if user == re.compile("^<@[0-9]*>$"):
        await interaction.response.send_message("User is not in a correct format. Please tag a discord user.")
        return

    contact_db.add_val_contact_for_address(db_connection, validator_address, user)

    validator_name = db.get_validator_identity(validator_address)
    contacts = contact_db.get_val_contacts_from_address(db_connection, validator_address)
    # TODO: Make sure this isn't validator_name != ""
    if validator_name is not None:
        message = f"{validator_name} has the following contacts: {', '.join(contacts)}"
    else:
        message = f"{validator_address} has the following contacts: {', '.join(contacts)}"

    await interaction.response.send_message(message)
    db_connection.close()
    return


@bot.tree.command(name="remove-contact", description="Remove a contract from a validator.")
@app_commands.describe(validator_address="The validator address.", user="The user to be removed.")
async def contacts_remove(interaction: discord.Interaction, validator_address: str, user: str):
    db_connection = db.connection()
    # TODO: verify the user is a discord user
    if user == re.compile("^<@[0-9]*>$"):
        await interaction.response.send_message("User is not in a correct format. Please tag a discord user.")
        return

    contact_db.remove_val_contact_for_address(db_connection, validator_address, user)

    validator_name = db.get_validator_identity(validator_address)
    contacts = contact_db.get_val_contacts_from_address(db_connection, validator_address)
    # TODO: Make sure this isn't validator_name != ""
    if validator_name is not None:
        message = f"{validator_name} has the following contacts: {contacts}"
    else:
        message = f"{validator_address} has the following contacts: {contacts}"

    await interaction.response.send_message(message)
    db_connection.close()
    return

def get_on_chain_identity(val_stash: str):
    substrate = SubstrateInterface(url="wss://turing-rpc.avail.so/ws", use_remote_preset=True,
                                   type_registry_preset='substrate-node-template')

    identity_info = substrate.query(
        module='Identity',
        storage_function='IdentityOf',
        params=[val_stash]
    )
    try:
        return identity_info.value[0]["info"]["display"]["Raw"]
    except:
        return ""


bot.run(token)
