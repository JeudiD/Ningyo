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

# Configure logging for bot events and errors
logging.getLogger('discord').setLevel(logging.INFO)
logging.getLogger('discord').propagate = False
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Load secrets like bot token from .env file
load_dotenv()

# Music player state management
song_queue = []
is_playing = False
current_voice_client = None

# Auto-disconnect state
disconnect_task = None
disconnect_timer = 0

# yt-dlp options for YouTube and SoundCloud
ydl_opts_youtube = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'extract_flat': False
}

ydl_opts_soundcloud = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'scsearch',
    'extract_flat': False
}

# FFmpeg options for reconnect support
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# Load Discord bot token
token = os.getenv("DISCORD_TOKEN")
if not token:
    raise ValueError("🚨 DISCORD_TOKEN not found in environment variables.")

# Setup required bot intents
intents = discord.Intents.default()
intents.message_content = True

# Initialize bot instance
bot = commands.Bot(command_prefix="n", intents=intents)

# Track which bots to auto-delete messages from
TRACKED_BOTS_FILE = "tracked_bots.json"
if os.path.isfile(TRACKED_BOTS_FILE):
    with open(TRACKED_BOTS_FILE, "r") as f:
        tracked_bots = json.load(f)
    tracked_bots = {int(k): v for k, v in tracked_bots.items()}
else:
    tracked_bots = {}

def save_tracked_bots():
    with open(TRACKED_BOTS_FILE, "w") as f:
        json.dump(tracked_bots, f)

# Define guild ID for syncing slash commands
GUILD_ID = 1030603151033769994
GUILD_OBJ = discord.Object(id=GUILD_ID)

@bot.event
async def on_ready():
    logging.info(f"✅ Bot is online as {bot.user}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="RIDE ON SHOOTING STAR"))
    await bot.tree.sync(guild=GUILD_OBJ)
    logging.info(f"✅ Slash commands synced for guild {GUILD_ID}")

# Message delete delay handler
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

# Disconnects the bot if alone in voice channel for 5 minutes
async def auto_disconnect_check():
    global disconnect_timer, current_voice_client, disconnect_task
    while current_voice_client and current_voice_client.is_connected():
        voice_channel = current_voice_client.channel
        non_bot_members = [m for m in voice_channel.members if not m.bot]

        if len(non_bot_members) == 0:
            disconnect_timer += 60
            if disconnect_timer >= 300:
                await current_voice_client.disconnect()
                current_voice_client = None
                disconnect_timer = 0
                disconnect_task = None
                break
        else:
            disconnect_timer = 0

        await asyncio.sleep(60)

# ----- Prefix Commands -----

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

@bot.command()
async def join(ctx):
    global current_voice_client, disconnect_task, disconnect_timer
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("You're not in a voice channel.")
        return
    channel = ctx.author.voice.channel
    if not current_voice_client or not current_voice_client.is_connected():
        current_voice_client = await channel.connect()
    else:
        await current_voice_client.move_to(channel)
    await ctx.send(f"Joined {channel.name}")

    if disconnect_task and not disconnect_task.done():
        disconnect_task.cancel()
    disconnect_timer = 0
    disconnect_task = bot.loop.create_task(auto_disconnect_check())

@bot.command()
async def play(ctx, *, query):
    await handle_queue_and_play(ctx, query)

@bot.command()
async def queue(ctx):
    if not song_queue:
        await ctx.send("The queue is empty.")
    else:
        msg = "**Current Queue:**\n" + "\n".join(f"{i+1}. {s['title']}" for i, s in enumerate(song_queue))
        await ctx.send(msg)

@bot.command()
async def pause(ctx):
    if current_voice_client and current_voice_client.is_playing():
        current_voice_client.pause()
        await ctx.send("Paused.")
    else:
        await ctx.send("Nothing is playing.")

@bot.command()
async def resume(ctx):
    if current_voice_client and current_voice_client.is_paused():
        current_voice_client.resume()
        await ctx.send("Resumed.")
    else:
        await ctx.send("Nothing is paused.")

@bot.command()
async def skip(ctx):
    if current_voice_client and current_voice_client.is_playing():
        current_voice_client.stop()
        await ctx.send("Skipped.")
    else:
        await ctx.send("Nothing is playing.")

@bot.command()
async def stop(ctx):
    global song_queue, is_playing, current_voice_client, disconnect_task, disconnect_timer
    song_queue.clear()
    is_playing = False
    if current_voice_client:
        current_voice_client.stop()
        await current_voice_client.disconnect()
        current_voice_client = None
    if disconnect_task and not disconnect_task.done():
        disconnect_task.cancel()
    disconnect_timer = 0
    await ctx.send("Stopped and disconnected.")

# Admin-only purge command to delete multiple messages quickly
@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🪩 Purged {amount} messages.", delete_after=5)

# ----- Admin Bot Tracking Commands -----

@bot.command()
@commands.has_permissions(administrator=True)
async def trackbot(ctx, bot_user: discord.User, delay: int):
    tracked_bots[bot_user.id] = delay
    save_tracked_bots()
    await ctx.send(f"✅ Tracking bot {bot_user.mention} with {delay}s delay.")

@bot.command()
@commands.has_permissions(administrator=True)
async def untrackbot(ctx, bot_user: discord.User):
    if tracked_bots.pop(bot_user.id, None):
        save_tracked_bots()
        await ctx.send(f"✅ Untracked bot {bot_user.mention}.")
    else:
        await ctx.send(f"❌ Bot {bot_user.mention} not found.")

@bot.command()
@commands.has_permissions(administrator=True)
async def listtracked(ctx):
    if tracked_bots:
        entries = [f"<@{uid}> — Delay: {delay}s" for uid, delay in tracked_bots.items()]
        await ctx.send("Tracked bots:\n" + "\n".join(entries))
    else:
        await ctx.send("No bots are being tracked.")

# ----- Slash Commands: Mirroring Prefix Commands -----

@bot.tree.command(name="join", description="Join your voice channel", guild=GUILD_OBJ)
async def join_slash(interaction: discord.Interaction):
    await join(interaction)

@bot.tree.command(name="play", description="Search and play a song", guild=GUILD_OBJ)
async def play_slash(interaction: discord.Interaction, query: str):
    await interaction.response.defer()
    await handle_queue_and_play(interaction, query)

@bot.tree.command(name="queue", description="Show current music queue", guild=GUILD_OBJ)
async def queue_slash(interaction: discord.Interaction):
    if not song_queue:
        await interaction.response.send_message("The queue is empty.")
    else:
        msg = "**Current Queue:**\n" + "\n".join(f"{i+1}. {s['title']}" for i, s in enumerate(song_queue))
        await interaction.response.send_message(msg)

@bot.tree.command(name="pause", description="Pause current song", guild=GUILD_OBJ)
async def pause_slash(interaction: discord.Interaction):
    await pause(interaction)

@bot.tree.command(name="resume", description="Resume paused song", guild=GUILD_OBJ)
async def resume_slash(interaction: discord.Interaction):
    await resume(interaction)

@bot.tree.command(name="skip", description="Skip current song", guild=GUILD_OBJ)
async def skip_slash(interaction: discord.Interaction):
    await skip(interaction)

@bot.tree.command(name="stop", description="Stop and disconnect", guild=GUILD_OBJ)
async def stop_slash(interaction: discord.Interaction):
    await stop(interaction)

@bot.tree.command(name="ping", description="Responds with Pong!", guild=GUILD_OBJ)
async def ping_slash(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!")

@bot.tree.command(name="purge", description="Delete a number of messages", guild=GUILD_OBJ)
@discord.app_commands.checks.has_permissions(manage_messages=True)
async def purge_slash(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount + 1)
    await interaction.followup.send(f"🪩 Purged {len(deleted) - 1} messages.", ephemeral=True)

# ----- Music Playback Logic -----

async def handle_queue_and_play(ctx_or_interaction, search):
    global current_voice_client, song_queue, is_playing
    info = None
    try:
        with YoutubeDL(ydl_opts_youtube) as ydl:
            info = ydl.extract_info(search, download=False)
            if 'entries' in info:
                info = info['entries'][0]
    except Exception as e:
        logging.warning(f"YouTube search failed: {e}")
    if not info:
        try:
            with YoutubeDL(ydl_opts_soundcloud) as ydl:
                info = ydl.extract_info(search, download=False)
                if 'entries' in info:
                    info = info['entries'][0]
        except Exception as e:
            logging.warning(f"SoundCloud search failed: {e}")
    if not info:
        msg = "❌ No results."
        if hasattr(ctx_or_interaction, 'send'):
            await ctx_or_interaction.send(msg)
        else:
            await ctx_or_interaction.followup.send(msg)
        return
    url = info.get('url') or info.get('webpage_url')
    title = info.get('title', 'Unknown Title')
    song_queue.append({'url': url, 'title': title})
    if hasattr(ctx_or_interaction, 'send'):
        await ctx_or_interaction.send(f"Queued: {title}")
    else:
        await ctx_or_interaction.followup.send(f"Queued: {title}")
    if not current_voice_client or not current_voice_client.is_connected():
        if hasattr(ctx_or_interaction, 'author'):
            current_voice_client = await ctx_or_interaction.author.voice.channel.connect()
        else:
            current_voice_client = await ctx_or_interaction.user.voice.channel.connect()

        global disconnect_task, disconnect_timer
        if disconnect_task and not disconnect_task.done():
            disconnect_task.cancel()
        disconnect_timer = 0
        disconnect_task = bot.loop.create_task(auto_disconnect_check())

    if not is_playing:
        await play_next(ctx_or_interaction)

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















