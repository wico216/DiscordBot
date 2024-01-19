import discord
from discord.ext import commands
from discord import Interaction
#import config
import yt_dlp
import asyncio
from discord import FFmpegPCMAudio
import subprocess
import discord
from yt_dlp.utils import ExtractorError
import os
import re
from dotenv import load_dotenv


load_dotenv()

channel_id = 1192590547454546043
app_id = 1192578363806732400
guild_id = 293111337431859201
#ffmpeg_path="ffmpeg"#linux
ffmpeg_path="C:/ffmpeg/bin/ffmpeg.exe"#windows
BOT_TOKEN=os.getenv("BOT_TOKEN")
client = commands.Bot(command_prefix = '!', intents = discord.Intents.all())
queue = []


@client.event
async def on_ready():
    global channel
    channel = client.get_channel(channel_id)
    print('Bot is ready.')
    if channel:
        await channel.send('Bot is ready.')
    else:
        print(f"Channel with ID {channel_id} not found.")
        
        
@client.command()
async def sync(ctx):
    guild = client.get_guild(guild_id)
    synced = await ctx.bot.tree.sync()
    if synced:
        await ctx.send(f"Synced {synced} commands.")
    else:
        await ctx.send('No new commands to sync.')




@client.tree.command(name='ping', description='Returns the latency of the bot.')
async def ping(interaction: Interaction):
    await interaction.response.send_message(f"Pong! {round(client.latency * 1000)}ms")
    
    
@client.tree.command(name='add', description='Adds a song to the queue.')
async def add(interaction: Interaction, url: str):
    # Rest of your code
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
                await interaction.response.send_message(f"{num_songs_added} songs added to the queue from the playlist.")
            else:  # It's a single video
                title = info['title']
                queue.append({'title': title, 'url': playlist_url})
                await interaction.response.send_message(f"Added to queue: {title}")

    except ExtractorError as e:
        await interaction.response.send_message(f"An error occurred: {e}")

# Command to play the music in the queue
@client.tree.command(name='playmusic', description='Plays the music in the queue.')
async def play_music(interaction: Interaction):
    if not queue:
        await interaction.response.send_message("Queue is empty.")
        return

    if interaction.user.voice is None:
        await interaction.response.send_message("You're not connected to a voice channel!")
        return

    # Check if the bot is already connected to a voice channel
    voice_client = discord.utils.get(client.voice_clients, guild=interaction.guild)
    if voice_client is None:
        voice_client = await interaction.user.voice.channel.connect()

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
                    await interaction.response.send_message("No audio formats found for this video.")
                    return
                url = formats[0]['url']

                source = discord.FFmpegPCMAudio(executable=ffmpeg_path, source=url, 
                                before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 
                                options='-vn -bufsize 128k -probesize 32k -analyzeduration 0')

            voice_client.play(source, after=lambda e: print('Player error: %s' % e) if e else print('Playback finished successfully.'))
            await client.change_presence(activity=discord.Game(name=f"Playing: {track['title']}"))
            await interaction.response.send_message(f"Now playing: {track['title']}")

            # Wait for the track to finish playing
            while voice_client.is_playing():
                await asyncio.sleep(1)

        except Exception as e:
            await interaction.response.send_message(f"An error occurred while playing {track['title']}: {e}")
            print(f"An error occurred: {e}")

    # Clear the queue and disconnect after playing all songs
    queue.clear()
    await voice_client.disconnect()


@client.tree.command(name='pause', description='Pause the currently playing track.')
async def pause(interaction: Interaction):
    voice_client = discord.utils.get(client.voice_clients, guild=interaction.guild)
    if voice_client is None or not voice_client.is_playing():
        await interaction.response.send_message("No audio is currently playing.")
        return
    else:
        voice_client.pause()
        await interaction.response.send_message('Audio has been paused')


@client.tree.command(name='resume', description='Resume the paused track.')
async def resume(interaction: Interaction):
    voice_client = discord.utils.get(client.voice_clients, guild=interaction.guild)
    if voice_client is None or not voice_client.is_paused():
        await interaction.response.send_message("No audio is currently paused.")
        return
    else:
        voice_client.resume()
        await interaction.response.send_message('Audio is resuming')


@client.tree.command(name='skip', description='Skip the currently playing track.')
async def skip(interaction: Interaction):
    voice_client = discord.utils.get(client.voice_clients, guild=interaction.guild)
    if voice_client is None or not voice_client.is_playing():
        await interaction.response.send_message("No audio is currently playing.")
        return
    voice_client.stop()
    await interaction.response.send_message("Skipped the currently playing track.")

@client.tree.command(name='stop', description='Stop playing music and clear the queue.')
async def stop(interaction: Interaction):
    voice_client = discord.utils.get(client.voice_clients, guild=interaction.guild)
    if voice_client is None or not voice_client.is_playing():
        await interaction.response.send_message("No audio is currently playing.")
        return
    voice_client.stop()
    await interaction.response.send_message("Stopped playing audio and cleared the queue.")





    
client.run(BOT_TOKEN)
    