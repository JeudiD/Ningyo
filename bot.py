import discord
import os
import logging
import json
import yt_dlp
from dotenv import load_dotenv
from discord.ext import commands
from yt_dlp import YoutubeDL
import asyncio
from discord import FFmpegPCMAudio

# Set up logging for info and above
logging.getLogger('discord').setLevel(logging.INFO)
logging.getLogger('discord').propagate = False
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Load environment variables from .env file
load_dotenv()

# Music bot state variables
song_queue = []  # Queue of songs to be played
is_playing = False  # Whether a song is currently playing
current_voice_client = None  # Current voice client connection

# yt-dlp and ffmpeg configuration
ydl_opts = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'extract_flat': False
}
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}
ydl = YoutubeDL(ydl_opts)

# Grab the bot token from environment variables
token = os.getenv("DISCORD_TOKEN")
if not token:
    raise ValueError("🚨 DISCORD_TOKEN not found in environment variables.")

# Set up bot intents
intents = discord.Intents.default()
intents.message_content = True

# Create bot instance
bot = commands.Bot(command_prefix="n", intents=intents)

# Tracked bots JSON file path and in-memory dict
TRACKED_BOTS_FILE = "tracked_bots.json"

# Load tracked bots from disk if available
if os.path.isfile(TRACKED_BOTS_FILE):
    with open(TRACKED_BOTS_FILE, "r") as f:
        tracked_bots = json.load(f)
    tracked_bots = {int(k): v for k, v in tracked_bots.items()}
else:
    tracked_bots = {}

def save_tracked_bots():
    with open(TRACKED_BOTS_FILE, "w") as f:
        json.dump(tracked_bots, f)

# Bot ready event
@bot.event
async def on_ready():
    logging.info(f"✅ Bot is online as {bot.user}")
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.listening, name="RIDE ON SHOOTING STAR"),
        status=discord.Status.online
    )
    await bot.tree.sync()  # Sync slash commands to Discord

# EVENT: Automatically delete tracked bot messages
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    delay = tracked_bots.get(message.author.id)
    if delay is not None:
        await asyncio.sleep(delay)
        try:
            await message.delete()
        except discord.NotFound:
            pass
        except discord.Forbidden:
            logging.warning("No permission to delete messages.")
        except Exception as e:
            logging.error(f"Failed to delete message: {e}")
    await bot.process_commands(message)

# BASIC COMMANDS: ping, purge, track/untrack bots
@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

@bot.command(name="purge")
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    deleted = await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 Deleted {len(deleted) - 1} messages", delete_after=5)

@bot.command(name="trackbot")
@commands.has_permissions(administrator=True)
async def track_bot(ctx, bot_user: discord.User, delay: int):
    tracked_bots[bot_user.id] = delay
    save_tracked_bots()
    await ctx.send(f"✅ Now tracking bot {bot_user.mention} to delete messages after {delay} seconds.")

@bot.command(name="untrackbot")
@commands.has_permissions(administrator=True)
async def untrack_bot(ctx, bot_user: discord.User):
    if tracked_bots.pop(bot_user.id, None):
        save_tracked_bots()
        await ctx.send(f"✅ Stopped tracking bot {bot_user.mention}.")
    else:
        await ctx.send(f"❌ Bot {bot_user.mention} is not currently tracked.")

@bot.command(name="listtracked")
@commands.has_permissions(administrator=True)
async def list_tracked(ctx):
    if tracked_bots:
        msg = "Tracked bots:\n" + "\n".join(f"<@{bid}> — Delay: {delay}s" for bid, delay in tracked_bots.items())
    else:
        msg = "No bots are currently being tracked."
    await ctx.send(msg)

# MUSIC COMMANDS — JOIN AND CONTROL AUDIO
@bot.command(name="join")
async def join(ctx):
    global current_voice_client
    if ctx.author.voice is None:
        await ctx.send("You're not in a voice channel.")
        return
    channel = ctx.author.voice.channel
    if not current_voice_client or not current_voice_client.is_connected():
        current_voice_client = await channel.connect()
    else:
        await current_voice_client.move_to(channel)
    await ctx.send(f"Joined {channel.name}")

@bot.command(name="search")  # renamed from play
async def search(ctx, *, search: str):
    await handle_queue_and_play(ctx, search)

@bot.command(name="pause")
async def pause(ctx):
    if current_voice_client and current_voice_client.is_playing():
        current_voice_client.pause()
        await ctx.send("Paused.")
    else:
        await ctx.send("Nothing is playing.")

@bot.command(name="resume")
async def resume(ctx):
    if current_voice_client and current_voice_client.is_paused():
        current_voice_client.resume()
        await ctx.send("Resumed.")
    else:
        await ctx.send("Nothing is paused.")

@bot.command(name="skip")
async def skip(ctx):
    if current_voice_client and current_voice_client.is_playing():
        current_voice_client.stop()
        await ctx.send("Skipped.")
    else:
        await ctx.send("Nothing is playing.")

@bot.command(name="stop")
async def stop(ctx):
    global song_queue, is_playing, current_voice_client
    song_queue.clear()
    is_playing = False
    if current_voice_client:
        current_voice_client.stop()
        await current_voice_client.disconnect()
        current_voice_client = None
    await ctx.send("Stopped and disconnected.")

# SLASH COMMANDS MIRRORING PREFIX COMMANDS
@bot.tree.command(name="join", description="Join your voice channel")
async def join_slash(interaction: discord.Interaction):
    global current_voice_client
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.response.send_message("You're not in a voice channel.", ephemeral=True)
        return
    channel = interaction.user.voice.channel
    if not current_voice_client or not current_voice_client.is_connected():
        current_voice_client = await channel.connect()
    else:
        await current_voice_client.move_to(channel)
    await interaction.response.send_message(f"Joined {channel.name}")

@bot.tree.command(name="search", description="Search and play a song")
async def search_slash(interaction: discord.Interaction, query: str):
    await interaction.response.defer()
    await handle_queue_and_play(interaction, query)

@bot.tree.command(name="pause", description="Pause current song")
async def pause_slash(interaction: discord.Interaction):
    if current_voice_client and current_voice_client.is_playing():
        current_voice_client.pause()
        await interaction.response.send_message("Paused.")
    else:
        await interaction.response.send_message("Nothing is playing.")

@bot.tree.command(name="resume", description="Resume paused song")
async def resume_slash(interaction: discord.Interaction):
    if current_voice_client and current_voice_client.is_paused():
        current_voice_client.resume()
        await interaction.response.send_message("Resumed.")
    else:
        await interaction.response.send_message("Nothing is paused.")

@bot.tree.command(name="skip", description="Skip current song")
async def skip_slash(interaction: discord.Interaction):
    if current_voice_client and current_voice_client.is_playing():
        current_voice_client.stop()
        await interaction.response.send_message("Skipped.")
    else:
        await interaction.response.send_message("Nothing is playing.")

@bot.tree.command(name="stop", description="Stop and disconnect")
async def stop_slash(interaction: discord.Interaction):
    global song_queue, is_playing, current_voice_client
    song_queue.clear()
    is_playing = False
    if current_voice_client:
        current_voice_client.stop()
        await current_voice_client.disconnect()
        current_voice_client = None
    await interaction.response.send_message("Stopped and disconnected.")

# Centralized function to handle music queue and playback
async def handle_queue_and_play(ctx_or_interaction, search):
    global current_voice_client, song_queue, is_playing

    try:
        info = ydl.extract_info(search, download=False)
        if 'entries' in info:
            info = info['entries'][0]
        url = info.get('url') or info.get('webpage_url')
        title = info.get('title', 'Unknown Title')
        song_queue.append({'url': url, 'title': title})
        if hasattr(ctx_or_interaction, 'send'):
            await ctx_or_interaction.send(f"Queued: {title}")
        else:
            await ctx_or_interaction.followup.send(f"Queued: {title}")
    except Exception as e:
        msg = f"Error: {e}"
        if hasattr(ctx_or_interaction, 'send'):
            await ctx_or_interaction.send(msg)
        else:
            await ctx_or_interaction.followup.send(msg)
        return

    if not current_voice_client or not current_voice_client.is_connected():
        if hasattr(ctx_or_interaction, 'author'):
            current_voice_client = await ctx_or_interaction.author.voice.channel.connect()
        else:
            current_voice_client = await ctx_or_interaction.user.voice.channel.connect()

    if not is_playing:
        await play_next(ctx_or_interaction)

# Core function to handle actual audio playback and queue chaining
async def play_next(ctx_or_interaction):
    global is_playing, song_queue, current_voice_client

    if not song_queue:
        is_playing = False
        return

    is_playing = True
    song = song_queue.pop(0)
    url = song['url']
    title = song['title']

    source = FFmpegPCMAudio(url, **FFMPEG_OPTIONS)

    if hasattr(ctx_or_interaction, 'send'):
        await ctx_or_interaction.send(f"Now playing: {title}")
    else:
        await ctx_or_interaction.followup.send(f"Now playing: {title}")

    def after_playing(error):
        fut = asyncio.run_coroutine_threadsafe(play_next(ctx_or_interaction), bot.loop)
        try:
            fut.result()
        except Exception as e:
            print(f"Error in after_playing: {e}")

    current_voice_client.play(source, after=after_playing)

# Run the bot
bot.run(token)








