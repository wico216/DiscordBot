import discord
from discord.ext import commands
from discord import Interaction
import os
from dotenv import load_dotenv

load_dotenv()

channel_id = 1192590547454546043
BOT_TOKEN=os.getenv("BOT_TOKEN")
client = commands.Bot(command_prefix = '.', intents = discord.Intents.all())



@client.event
async def on_ready():
    global channel
    channel = client.get_channel(channel_id)
    await client.tree.sync()
    print('Bot is ready.')
    if channel:
        await channel.send('Bot is ready.')
    else:
        print(f"Channel with ID {channel_id} not found.")

@client.tree.command(name='ping', description='Returns the latency of the bot.')
async def ping(interaction: Interaction):
    await interaction.response.send_message(f"Pong! {round(client.latency * 1000)}ms")
    
client.run(BOT_TOKEN)
    