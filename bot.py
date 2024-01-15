import discord
from discord.ext import commands
import config
import yt_dlp
import asyncio
from discord import FFmpegPCMAudio
import subprocess
import discord
from discord.ext import commands
from yt_dlp.utils import ExtractorError
import re

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
    
# Assuming queue is a list that contains the URLs of the songs in the queue
@client.command()
async def viewqueue(ctx):
    # Count the number of songs in the queue
    num_songs = len(queue)

    # Check if the queue is empty
    if num_songs == 0:
        await ctx.send("The queue is currently empty.")
    else:
        # Send a message with the count of songs
        await ctx.send(f"There are {num_songs} songs in the queue.")



# Function to play music

@client.command()
async def play_music(ctx):
    if not queue:
        await ctx.send("Queue is empty.")
        return

    if ctx.author.voice is None:
        await ctx.send("You're not connected to a voice channel!")
        return

    # Check if the bot is already connected to a voice channel
    voice_client = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice_client is None:
        voice_client = await ctx.author.voice.channel.connect()

    for track in queue:
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'downloads/%(title)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'webm',
                    'preferredquality': '192',
                }],
                'prefer_ffmpeg': True,
                'keepvideo': False
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ytdl:
                info = ytdl.extract_info(track['url'], download=False)
                formats = [f for f in info['formats'] if 'acodec' in f and f['acodec'] != 'none']
                if not formats:
                     await ctx.send("No audio formats found for this video.")
                     return
                url = formats[0]['url']

                source = discord.FFmpegPCMAudio(executable=config.FFMPEG_EXECUTABLE_PATH, source=url, 
                                before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 
                                options='-vn -bufsize 64k -probesize 32k -analyzeduration 0')

            voice_client.play(source, after=lambda e: print('Player error: %s' % e) if e else print('Playback finished successfully.'))
            await client.change_presence(activity=discord.Game(name=f"Playing: {track['title']}"))
            await ctx.send(f"Now playing: {track['title']}")

            # Wait for the track to finish playing
            while voice_client.is_playing():
                await asyncio.sleep(1)

        except Exception as e:
            await ctx.send(f"An error occurred while playing {track['title']}: {e}")
            print(f"An error occurred: {e}")

    # Clear the queue and disconnect after playing all songs
    queue.clear()
    await voice_client.disconnect()

# Command to add a track to the queue
@client.command()
async def add(ctx, url):
    try:
        # Check if the URL contains a playlist ID and extract it
        playlist_id_match = re.search(r'list=([a-zA-Z0-9_-]+)', url)
        if playlist_id_match:
            playlist_url = f"https://www.youtube.com/playlist?list={playlist_id_match.group(1)}"
        else:
            playlist_url = url

        ydl_opts = {
            'extract_flat': True,  # Extract information without downloading
            'format': 'bestaudio/best'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)
            if 'entries' in info:  # It's a playlist
                num_songs_added = 0
                for entry in info['entries']:
                    queue.append({'title': entry['title'], 'url': entry['url']})
                    num_songs_added += 1
                await ctx.send(f"{num_songs_added} songs added to the queue from the playlist.")
            else:  # It's a single video
                title = info['title']
                queue.append({'title': title, 'url': playlist_url})
                await ctx.send(f"Added to queue: {title}")

    except ExtractorError as e:
        await ctx.send(f"An error occurred: {e}")
    
@client.command()
async def play(ctx, url):
    if ctx.author.voice is None:
        await ctx.send("You're not connected to a voice channel!")
        return

    voice_client = await ctx.author.voice.channel.connect()

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'webm',
            'preferredquality': '192',
        }],
        'prefer_ffmpeg': True,
        'keepvideo': False
    }

    ytdl = yt_dlp.YoutubeDL(ydl_opts)
    info = ytdl.extract_info(url, download=False)

    # Filter the formats to find one that contains audio
    formats = [f for f in info['formats'] if 'acodec' in f and f['acodec'] != 'none']
    if not formats:
        await ctx.send("No audio formats found for this video.")
        return

    # Use the URL of the first audio format
    url = formats[0]['url']

    # Create the audio source without the FFmpeg options    
    source = discord.FFmpegPCMAudio(executable=config.FFMPEG_EXECUTABLE_PATH, source=url, 
                                before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 
                                options='-vn -bufsize 64k -probesize 32k -analyzeduration 0')



    voice_client.play(source, after=lambda e: print('Player error: %s' % e) if e else print('Playback finished successfully.'))
        
    while voice_client.is_playing():
        await asyncio.sleep(1)

    # Disconnect from the voice channel
    await voice_client.disconnect()


# Command to pause the currently playing track
@client.command()
async def pause(ctx):
    voice_client = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice_client is None or not voice_client.is_playing():
        await ctx.send("No audio is currently playing.")
        return
    else:
        voice_client.pause()
        await ctx.send('Audio has been paused')

# Command to resume the paused track
@client.command()
async def resume(ctx):
    voice_client = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice_client is None or not voice_client.is_paused():
        await ctx.send("No audio is currently paused.")
        return
    else:
        voice_client.resume()
        await ctx.send('Audio is resuming')

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
