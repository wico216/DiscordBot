import discord
from discord.ext import commands
import config
import youtube_dl
import asyncio
from discord import FFmpegPCMAudio




# Setup Discord bot with command prefix '!'
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True  # Add this line
client = commands.Bot(command_prefix='!', intents=intents) #Replace with your desired command prefix for the bot answer
channel = client.get_channel(config.CHANNEL_ID) #Get channel ID from config.py
BOT_TOKEN = config.BOT_TOKEN #Get bot token from config.py

# !play <url>: Connects the bot to the voice channel that the command author is in, 
# downloads the audio from the YouTube video at <url>, and starts playing it in the voice channel.

# !queue <url>: Adds the audio from the YouTube video at <url> to the queue. 
# The audio will be played after the current song finishes.

# !pause: Pauses the audio playback.

# !resume: Resumes the audio playback.

# !stop: Stops the audio playback and disconnects the bot from the voice channel.

# !skip: Skips the current song and plays the next song in the queue.

# !viewqueue: Shows the list of songs in the queue.
# Queue to store the music tracks
queue = []


# Setup bot to chat in Discord channel
@client.event
async def on_ready():
    global channel
    channel = client.get_channel(config.CHANNEL_ID)
    print('Bot is ready.')
    if channel:
        await channel.send('Bot is ready.')
    else:
        print(f"Channel with ID {config.CHANNEL_ID} not found.")
    
# Setup bot to listen for messages in Discord channel
'''
# FILEPATH: /c:/Users/wico2/OneDrive/Documents/DiscordBot/bot.py
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    await message.channel.send('Message received')
    
    # Check if message is from a user
    if isinstance(message.author, discord.User):
        print('Message is from user.')
        await channel.send('Message is from user.')
        # Add your desired logic for responding to user messages here
        
    '''

# Assuming queue is a list that contains the URLs of the songs in the queue


@client.command()
async def viewqueue(ctx):
    if not queue:
        await ctx.send("The queue is currently empty.")
    else:
        message = "Songs in the queue:\n"
        for url in queue:
            message += f"{url}\n"
        await ctx.send(message)



# Function to play music
async def play_music(ctx):
    if not queue:
        await ctx.send("Queue is empty.")
        return
    MUSIC_CHANNEL_ID = config.MUSIC_CHANNEL_ID
    voice_channel = discord.utils.get(ctx.guild.voice_channels, id=MUSIC_CHANNEL_ID)
    if voice_channel is None:
        await ctx.send("Music channel not found.")
        return

    voice_client = await voice_channel.connect()
    

    while queue:
        track = queue[0]
        source = await discord.FFmpegOpusAudio.from_probe(track['url'])
        voice_client.play(source)
        await ctx.send(f"Now playing: {track['title']}")

        # Wait for the track to finish playing
        while voice_client.is_playing():
            await asyncio.sleep(1)

        # Remove the track from the queue
        queue.pop(0)

    await voice_client.disconnect()

# Command to add a track to the queue
"""
@client.command()
async def play(ctx, url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info['title']
        url = info['url']

    track = {'title': title, 'url': url}
    queue.append(track)

    await ctx.send(f"Added to queue: {title}")
    
"""

@client.command()
async def play(ctx, url):
    channel = ctx.message.author.voice.channel
    if channel is None:
        await ctx.send("You are not in a voice channel.")
        return

    voice_channel = await channel.connect()

    ydl_opts = {'format': 'bestaudio'}
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if 'formats' not in info:
            await ctx.send("Invalid YouTube URL.")
            return
        url2 = info['formats'][0]['url']
        voice_channel.play(FFmpegPCMAudio(url2))
        await ctx.send('Playing...')

# Command to pause the currently playing track
@client.command()
async def pause(ctx):
    voice_client = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice_client is None or not voice_client.is_playing():
        await ctx.send("No audio is currently playing.")
        return
    voice_client.pause()

# Command to resume the paused track
@client.command()
async def resume(ctx):
    voice_client = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice_client is None or not voice_client.is_paused():
        await ctx.send("No audio is currently paused.")
        return
    voice_client.resume()

# Command to skip the currently playing track
@client.command()
async def skip(ctx):
    voice_client = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice_client is None or not voice_client.is_playing():
        await ctx.send("No audio is currently playing.")
        return
    voice_client.stop()

# Command to stop playing music and clear the queue
@client.command()
async def stop(ctx):
    voice_client = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice_client is None or not voice_client.is_playing():
        await ctx.send("No audio is currently playing.")
        return
    voice_client.stop()
    queue.clear()


# Error handler for play command
@play.error
async def play_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please provide a YouTube URL.")
    elif isinstance(error, commands.CommandInvokeError):
        await ctx.send("An error occurred while playing the audio.")
        await ctx.send(f"An error occurred: {str(error)}")

# Error handler for pause command
@pause.error
async def pause_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        await ctx.send("An error occurred while pausing the audio.")
        await ctx.send(f"An error occurred: {str(error)}")

# Error handler for resume command
@resume.error
async def resume_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        await ctx.send("An error occurred while resuming the audio.")
        await ctx.send(f"An error occurred: {str(error)}")

# Error handler for skip command
@skip.error
async def skip_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        await ctx.send("An error occurred while skipping the audio.")
        await ctx.send(f"An error occurred: {str(error)}")

# Error handler for stop command
@stop.error
async def stop_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        await ctx.send("An error occurred while stopping the audio.")
        await ctx.send(f"An error occurred: {str(error)}")


# Run the bot
client.run(config.BOT_TOKEN)
