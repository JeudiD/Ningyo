import discord
import os
import logging
import json
import yt_dlp
from dotenv import load_dotenv
from discord.ext import commands
import asyncio
from discord import FFmpegPCMAudio, app_commands
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import re
from yt_dlp import YoutubeDL

dll_path = os.path.join(os.path.dirname(__file__), "opus.dll")
if not discord.opus.is_loaded():
    discord.opus.load_opus(dll_path)

print("Opus loaded:", discord.opus.is_loaded())

# Logging setup
logging.getLogger('discord').setLevel(logging.INFO)
logging.getLogger('discord').propagate = False
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Load env variables
load_dotenv()
token = os.getenv("DISCORD_TOKEN")
if not token:
    raise ValueError("🚨 DISCORD_TOKEN not found in environment variables.")

spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID")
spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

print(f"✅ ID loaded: {bool(spotify_client_id)}")
print(f"✅ Secret loaded: {bool(spotify_client_secret)}")
# print(f"ID: {spotify_client_id}")
# print(f"Secret: {spotify_client_secret}")

if not spotify_client_id or not spotify_client_secret:
    raise ValueError("🚨 Spotify credentials missing in environment variables.")

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=spotify_client_id,
    client_secret=spotify_client_secret
))

#print(sp.search(q="Never Gonna Give You Up", limit=1))


ydl_opts = {'format': 'bestaudio/best', 'quiet': True, 'no_warnings': True, 'default_search': 'ytsearch'}

async def search_and_play_youtube(ctx, query):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
        url = info['webpage_url']

    await handle_queue_and_play(ctx, url)

# Bot intents
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="n", intents=intents)

# Guild info for slash commands
GUILD_ID = 1030603151033769994
GUILD_OBJ = discord.Object(id=GUILD_ID)

# Auto-delete tracked bots config
TRACKED_BOTS_FILE = "tracked_bots.json"
if os.path.isfile(TRACKED_BOTS_FILE):
    with open(TRACKED_BOTS_FILE, "r") as f:
        tracked_bots = {int(k): v for k, v in json.load(f).items()}
else:
    tracked_bots = {}

def save_tracked_bots():
    with open(TRACKED_BOTS_FILE, "w") as f:
        json.dump(tracked_bots, f)

# Global Spotify client
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=("SPOTIFY_CLIENT_ID"),
    client_secret=("SPOTIFY_CLIENT_SECRET")
))

# Music state
song_queue = []
is_playing = False
current_voice_client = None
current_player_message = None
progress_task = None
volume = 0.1
repeat_mode = 0

# Auto-disconnect
disconnect_task = None
disconnect_timer = 0

# yt-dlp options
ydl_opts_youtube = {'format': 'bestaudio/best', 'quiet': True, 'no_warnings': True, 'default_search': 'ytsearch'}
ydl_opts_soundcloud = {'format': 'bestaudio/best', 'quiet': True, 'no_warnings': True, 'default_search': 'scsearch'}

# FFmpeg options
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

# Helpers
def repeat_mode_to_str(mode: int) -> str:
    return {0: "Off", 1: "Repeat One", 2: "Repeat All"}.get(mode, "Unknown")

async def send_response(ctx_or_interaction, message, ephemeral=False):
    """
    Sends message depending on context:
    - ctx (prefix command): ctx.send()
    - interaction (slash or button): response.send_message or followup.send_message
    """
    if hasattr(ctx_or_interaction, 'send'):
        await ctx_or_interaction.send(message)
    else:
        try:
            await ctx_or_interaction.response.send_message(message, ephemeral=ephemeral)
        except discord.InteractionResponded:
            await ctx_or_interaction.followup.send(message, ephemeral=ephemeral)

# Unified command handlers

async def ping_handler(ctx_or_interaction):
    await send_response(ctx_or_interaction, "🏓 Pong!", ephemeral=True)

async def pause_handler(ctx_or_interaction):
    global current_voice_client
    if current_voice_client and current_voice_client.is_playing():
        current_voice_client.pause()
        await send_response(ctx_or_interaction, "Paused.", ephemeral=True)
        await update_now_playing_message()
    else:
        await send_response(ctx_or_interaction, "Nothing is playing.", ephemeral=True)

async def resume_handler(ctx_or_interaction):
    global current_voice_client
    if current_voice_client and current_voice_client.is_paused():
        current_voice_client.resume()
        await send_response(ctx_or_interaction, "Resumed.", ephemeral=True)
        await update_now_playing_message()
    else:
        await send_response(ctx_or_interaction, "Nothing is paused.", ephemeral=True)

async def skip_handler(ctx_or_interaction):
    global current_voice_client
    if current_voice_client and current_voice_client.is_playing():
        current_voice_client.stop()
        await send_response(ctx_or_interaction, "Skipped.", ephemeral=True)
    else:
        await send_response(ctx_or_interaction, "Nothing is playing.", ephemeral=True)

async def stop_handler(ctx_or_interaction):
    global song_queue, is_playing, current_voice_client, disconnect_task, disconnect_timer, current_player_message, progress_task

    song_queue.clear()
    is_playing = False

    if current_voice_client:
        current_voice_client.stop()
        await current_voice_client.disconnect()
        current_voice_client = None

    if disconnect_task and not disconnect_task.done():
        disconnect_task.cancel()
    disconnect_timer = 0

    if current_player_message:
        try:
            await current_player_message.delete()
        except:
            pass
        current_player_message = None

    if progress_task:
        progress_task.cancel()
        progress_task = None

    await send_response(ctx_or_interaction, "Stopped and disconnected.", ephemeral=True)

async def join_handler(ctx_or_interaction):
    channel = None
    if hasattr(ctx_or_interaction, 'author'):
        if ctx_or_interaction.author.voice:
            channel = ctx_or_interaction.author.voice.channel
    elif hasattr(ctx_or_interaction, 'user'):
        if ctx_or_interaction.user.voice:
            channel = ctx_or_interaction.user.voice.channel

    if channel:
        global current_voice_client
        current_voice_client = await channel.connect()
        await send_response(ctx_or_interaction, f"Connected to {channel.name}.", ephemeral=True)
    else:
        await send_response(ctx_or_interaction, "You must be in a voice channel.", ephemeral=True)

async def leave_handler(ctx_or_interaction):
    global current_voice_client
    if current_voice_client:
        await current_voice_client.disconnect()
        current_voice_client = None
        await send_response(ctx_or_interaction, "Disconnected.", ephemeral=True)
    else:
        await send_response(ctx_or_interaction, "Not connected.", ephemeral=True)

async def queue_handler(ctx_or_interaction):
    if not song_queue:
        await send_response(ctx_or_interaction, "The queue is empty.", ephemeral=True)
        return

    pages = []
    per_page = 10
    for i in range(0, len(song_queue), per_page):
        page_songs = song_queue[i:i+per_page]
        desc = ""
        for j, song in enumerate(page_songs, start=i+1):
            desc += f"**{j}.** [{song['title']}]({song['webpage_url']}) - requested by {song['requester'].mention if song['requester'] else 'unknown'}\n"
        pages.append(desc)

    embed = discord.Embed(title=f"Queue (Page 1/{len(pages)})", description=pages[0], color=discord.Color.green())
    view = QueuePagination(ctx_or_interaction, pages)

    # Send embed + view differently based on context
    if hasattr(ctx_or_interaction, 'send'):
        await ctx_or_interaction.send(embed=embed, view=view)
    else:
        try:
            await ctx_or_interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        except discord.InteractionResponded:
            await ctx_or_interaction.followup.send(embed=embed, view=view, ephemeral=True)

async def purge_handler(ctx_or_interaction, amount: int):
    if not hasattr(ctx_or_interaction, 'guild') or not ctx_or_interaction.guild:
        await send_response(ctx_or_interaction, "This command must be used in a guild.", ephemeral=True)
        return

    perms = None
    if hasattr(ctx_or_interaction, 'author'):
        perms = ctx_or_interaction.author.guild_permissions
    elif hasattr(ctx_or_interaction, 'user'):
        perms = ctx_or_interaction.user.guild_permissions

    if not perms or not perms.manage_messages:
        await send_response(ctx_or_interaction, "You don't have permission to manage messages.", ephemeral=True)
        return

    if amount < 1 or amount > 100:
        await send_response(ctx_or_interaction, "Please specify an amount between 1 and 100.", ephemeral=True)
        return

    # Defer for interactions
    if not hasattr(ctx_or_interaction, 'send'):
        await ctx_or_interaction.response.defer(ephemeral=True)

    deleted = await ctx_or_interaction.channel.purge(limit=amount + 1)
    await send_response(ctx_or_interaction, f"Deleted {len(deleted)-1} messages.", ephemeral=True)

# async def play_handler(ctx_or_interaction, search: str):
#     await handle_queue_and_play(ctx_or_interaction, search)
async def play_handler(ctx_or_interaction, search: str):
    if "open.spotify.com/track" in search:
        await handle_spotify_track(ctx_or_interaction, search)
        return

    await handle_queue_and_play(ctx_or_interaction, search)


async def handle_spotify_track(ctx, url):
    # Extract track ID
    match = re.search(r"track/([a-zA-Z0-9]+)", url)
    if not match:
        if hasattr(ctx, "response"):
            await ctx.response.send_message("❌ Could not extract track ID.", ephemeral=True)
        else:
            await ctx.send("❌ Could not extract track ID.")
        return

    track_id = match.group(1)

    try:
        track = sp.track(track_id)
        title = track["name"]
        artist = track["artists"][0]["name"]
        query = f"{title} {artist}"
    except Exception as e:
        print(e)
        if hasattr(ctx, "response"):
            await ctx.response.send_message("⚠️ Failed to retrieve track info.", ephemeral=True)
        else:
            await ctx.send("⚠️ Failed to retrieve track info.")
        return

    # # Notify user what you're searching for
    # if hasattr(ctx, "response"):
    #     # Interaction: first response or followup?
    #     # If already responded, use followup, else response.send_message
    #     try:
    #         await ctx.response.send_message(f"🔍 Searching YouTube for: `{query}`")
    #     except discord.errors.InteractionResponded:
    #         await ctx.followup.send(f"🔍 Searching YouTube for: `{query}`")
    # else:
    #     await ctx.send(f"🔍 Searching YouTube for: `{query}`")

    # await search_and_play_youtube(ctx, query)




# Your existing handle_queue_and_play function here unchanged
# (Add your pasted function below or import it)

# Repeat button cycle handler
async def repeat_mode_handler(ctx_or_interaction):
    global repeat_mode
    repeat_mode = (repeat_mode + 1) % 3
    await send_response(ctx_or_interaction, f"Repeat mode set to: {repeat_mode_to_str(repeat_mode)}", ephemeral=True)
    await update_now_playing_message()

# Volume up/down handlers
async def volume_up_handler(ctx_or_interaction):
    global volume
    volume = min(volume + 0.1, 1.0)
    if current_voice_client and current_voice_client.source:
        current_voice_client.source.volume = volume
    await send_response(ctx_or_interaction, f"Volume: {int(volume * 100)}%", ephemeral=True)
    await update_now_playing_message()

async def volume_down_handler(ctx_or_interaction):
    global volume
    volume = max(volume - 0.1, 0.0)
    if current_voice_client and current_voice_client.source:
        current_voice_client.source.volume = volume
    await send_response(ctx_or_interaction, f"Volume: {int(volume * 100)}%", ephemeral=True)
    await update_now_playing_message()

# Views with persistent buttons (custom_id set for persistence)
class MusicControls(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="⏸️ Pause", style=discord.ButtonStyle.primary, custom_id="pause_button")
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await pause_handler(interaction)

    @discord.ui.button(label="▶️ Resume", style=discord.ButtonStyle.success, custom_id="resume_button")
    async def resume_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await resume_handler(interaction)

    @discord.ui.button(label="⏭️ Skip", style=discord.ButtonStyle.secondary, custom_id="skip_button")
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await skip_handler(interaction)

    @discord.ui.button(label="⏹️ Stop", style=discord.ButtonStyle.danger, custom_id="stop_button")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await stop_handler(interaction)

    @discord.ui.button(label="🔁 Repeat Mode", style=discord.ButtonStyle.primary, custom_id="repeat_button")
    async def repeat_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await repeat_mode_handler(interaction)

    @discord.ui.button(label="🔊 Vol +", style=discord.ButtonStyle.secondary, custom_id="vol_up_button")
    async def volume_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        await volume_up_handler(interaction)

    @discord.ui.button(label="🔉 Vol -", style=discord.ButtonStyle.secondary, custom_id="vol_down_button")
    async def volume_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        await volume_down_handler(interaction)

class QueuePagination(discord.ui.View):
    def __init__(self, ctx_or_interaction, pages):
        super().__init__(timeout=60)
        self.ctx_or_interaction = ctx_or_interaction
        self.pages = pages
        self.page = 0

    async def update_page(self, interaction):
        embed = discord.Embed(title=f"Queue (Page {self.page+1}/{len(self.pages)})", description=self.pages[self.page], color=discord.Color.green())
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary, custom_id="queue_prev")
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != (self.ctx_or_interaction.author if hasattr(self.ctx_or_interaction, 'author') else self.ctx_or_interaction.user):
            await interaction.response.send_message("This is not your queue to control.", ephemeral=True)
            return
        if self.page > 0:
            self.page -= 1
            await self.update_page(interaction)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary, custom_id="queue_next")
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != (self.ctx_or_interaction.author if hasattr(self.ctx_or_interaction, 'author') else self.ctx_or_interaction.user):
            await interaction.response.send_message("This is not your queue to control.", ephemeral=True)
            return
        if self.page < len(self.pages) - 1:
            self.page += 1
            await self.update_page(interaction)
        else:
            await interaction.response.defer()

# on_ready event
@bot.event
async def on_ready():
    logging.info(f"✅ Bot is online as {bot.user}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="RIDE ON SHOOTING STAR"))
    await bot.tree.sync(guild=GUILD_OBJ)
    logging.info(f"✅ Slash commands synced for guild {GUILD_ID}")
    bot.add_view(MusicControls())

# Auto-delete tracked bot messages
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

# Update Now Playing message embed
async def update_now_playing_message():
    global current_player_message, is_playing, current_voice_client

    if not current_player_message or current_player_message.channel is None:
        return

    if not is_playing or not current_voice_client or not current_voice_client.is_playing():
        try:
            await current_player_message.delete()
        except:
            pass
        current_player_message = None
        return

    current_song = getattr(bot, "current_song", None)
    if not current_song:
        return

    embed = discord.Embed(
        title="🎶 Now Playing",
        description=f"[{current_song['title']}]({current_song['webpage_url']})",
        color=discord.Color.blurple()
    )
    embed.set_thumbnail(url=current_song.get('thumbnail', None))
    embed.add_field(name="Requested by", value=current_song['requester'].mention if current_song['requester'] else "Unknown", inline=True)
    embed.add_field(name="Repeat Mode", value=repeat_mode_to_str(repeat_mode), inline=True)
    embed.add_field(name="Volume", value=f"{int(volume * 100)}%", inline=True)

    await current_player_message.edit(embed=embed, view=MusicControls())

# Auto disconnect if alone in VC for 5 minutes
async def auto_disconnect_check():
    global disconnect_timer, current_voice_client, disconnect_task, progress_task
    while current_voice_client and current_voice_client.is_connected():
        voice_channel = current_voice_client.channel
        non_bot_members = [m for m in voice_channel.members if not m.bot]

        if len(non_bot_members) == 0:
            disconnect_timer += 60
            if disconnect_timer >= 300:
                if progress_task:
                    progress_task.cancel()
                    progress_task = None
                await current_voice_client.disconnect()
                current_voice_client = None
                disconnect_timer = 0
                disconnect_task = None
                break
        else:
            disconnect_timer = 0

        await asyncio.sleep(60)

# Progress updater (optional, updates now playing embed every 5s)
async def progress_updater():
    global is_playing, current_voice_client, current_player_message

    while is_playing and current_voice_client and current_voice_client.is_playing():
        await update_now_playing_message()
        await asyncio.sleep(5)

# Play next song from queue
async def play_next(ctx_or_interaction):
    global is_playing, song_queue, current_voice_client, current_player_message, progress_task, volume, repeat_mode

    if not song_queue:
        is_playing = False
        if current_player_message:
            try:
                await current_player_message.delete()
            except:
                pass
            current_player_message = None
        return

    is_playing = True

    if repeat_mode == 1 and hasattr(bot, "current_song"):
        song = bot.current_song
    else:
        song = song_queue.pop(0)
        bot.current_song = song
        if repeat_mode == 2:
            song_queue.append(song)

    url = song['url']

    source = FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
    source = discord.PCMVolumeTransformer(source, volume=volume)

    def after_playing(error):
        if error:
            logging.error(f"Error in after_playing: {error}")

    # Schedule play_next without blocking
        asyncio.run_coroutine_threadsafe(play_next(ctx_or_interaction), bot.loop)



    if not current_voice_client or not current_voice_client.is_connected():
        # Connect voice client if not connected
        channel = None
        if hasattr(ctx_or_interaction, 'author'):
            if ctx_or_interaction.author.voice:
                channel = ctx_or_interaction.author.voice.channel
        elif hasattr(ctx_or_interaction, 'user'):
            if ctx_or_interaction.user.voice:
                channel = ctx_or_interaction.user.voice.channel

        if not channel:
            await send_response(ctx_or_interaction, "❌ You must be in a voice channel.", ephemeral=True)
            return

        global disconnect_task, disconnect_timer
        current_voice_client = await channel.connect()
        if disconnect_task and not disconnect_task.done():
            disconnect_task.cancel()
        disconnect_timer = 0
        disconnect_task = bot.loop.create_task(auto_disconnect_check())

    current_voice_client.play(source, after=after_playing)

    # Send or update now playing message
    if not current_player_message:
        channel = None
        if hasattr(ctx_or_interaction, 'channel'):
            channel = ctx_or_interaction.channel
        elif hasattr(ctx_or_interaction, 'guild') and hasattr(ctx_or_interaction.guild, 'text_channels'):
            channel = ctx_or_interaction.guild.text_channels[0]

        if channel:
            embed = discord.Embed(
                title="🎶 Now Playing",
                description=f"[{song['title']}]({song['webpage_url']})",
                color=discord.Color.blurple()
            )
            embed.set_thumbnail(url=song.get('thumbnail', None))
            embed.add_field(name="Requested by", value=song['requester'].mention if song['requester'] else "Unknown", inline=True)
            embed.add_field(name="Repeat Mode", value=repeat_mode_to_str(repeat_mode), inline=True)
            embed.add_field(name="Volume", value=f"{int(volume * 100)}%", inline=True)

            #global current_player_message - this was casuing errors because it was said somewhere else
            current_player_message = await channel.send(embed=embed, view=MusicControls())

    # Start progress updater
    global progress_task
    if not progress_task or progress_task.done():
        progress_task = bot.loop.create_task(progress_updater())

# Queue and play handler (your existing function, simplified for example)
async def handle_queue_and_play(ctx_or_interaction, search):
    ydl_opts = ydl_opts_youtube

    def blocking_extract():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(search, download=False)

    try:
        info = await asyncio.to_thread(blocking_extract)
    except Exception as e:
        await send_response(ctx_or_interaction, f"Error finding media: {e}", ephemeral=True)
        return

    if not info:
        await send_response(ctx_or_interaction, "❌ No results.", ephemeral=True)
        return

    # If multiple entries (playlist or search), take first
    if 'entries' in info:
        info = info['entries'][0]

    url = info.get('url') or info.get('webpage_url')
    title = info.get('title', 'Unknown Title')
    webpage_url = info.get('webpage_url', url)
    duration = info.get('duration', 0)
    thumbnail = info.get('thumbnail', None)

    requester = None
    if hasattr(ctx_or_interaction, 'author'):
        requester = ctx_or_interaction.author
    elif hasattr(ctx_or_interaction, 'user'):
        requester = ctx_or_interaction.user

    was_queue_empty = len(song_queue) == 0

    song_queue.append({
        'url': url,
        'title': title,
        'webpage_url': webpage_url,
        'duration': duration,
        'thumbnail': thumbnail,
        'requester': requester,
    })

    global is_playing, current_voice_client, disconnect_task, disconnect_timer

    if was_queue_empty and (not current_voice_client or not current_voice_client.is_playing()):
        await send_response(ctx_or_interaction, f"▶️ Now playing: **{title}** (requested by {requester.mention if requester else 'unknown'})")
        await play_next(ctx_or_interaction)
    else:
        await send_response(ctx_or_interaction, f"✅ Queued: **{title}** (requested by {requester.mention if requester else 'unknown'})")

    # Connect voice client if not connected
    if not current_voice_client or not current_voice_client.is_connected():
        channel = None
        if hasattr(ctx_or_interaction, 'author'):
            if ctx_or_interaction.author.voice:
                channel = ctx_or_interaction.author.voice.channel
        elif hasattr(ctx_or_interaction, 'user'):
            if ctx_or_interaction.user.voice:
                channel = ctx_or_interaction.user.voice.channel

        if not channel:
            await send_response(ctx_or_interaction, "❌ You must be in a voice channel.", ephemeral=True)
            return

        current_voice_client = await channel.connect()

        if disconnect_task and not disconnect_task.done():
            disconnect_task.cancel()
        disconnect_timer = 0
        disconnect_task = bot.loop.create_task(auto_disconnect_check())

    if not is_playing:
        await play_next(ctx_or_interaction)


# Prefix commands wrapping unified handlers
@bot.command()
async def ping(ctx):
    await ping_handler(ctx)

@bot.command()
async def pause(ctx):
    await pause_handler(ctx)

@bot.command()
async def resume(ctx):
    await resume_handler(ctx)

@bot.command()
async def skip(ctx):
    await skip_handler(ctx)

@bot.command()
async def stop(ctx):
    await stop_handler(ctx)

@bot.command()
async def join(ctx):
    await join_handler(ctx)

@bot.command()
async def leave(ctx):
    await leave_handler(ctx)

@bot.command()
async def queue(ctx):
    await queue_handler(ctx)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    await purge_handler(ctx, amount)

@bot.command()
async def play(ctx, *, search: str):
    await play_handler(ctx, search)

# Slash commands wrapping unified handlers
@bot.tree.command(name="ping", description="Ping the bot", guild=GUILD_OBJ)
async def slash_ping(interaction: discord.Interaction):
    await ping_handler(interaction)

@bot.tree.command(name="pause", description="Pause the current song", guild=GUILD_OBJ)
async def slash_pause(interaction: discord.Interaction):
    await pause_handler(interaction)

@bot.tree.command(name="resume", description="Resume the current song", guild=GUILD_OBJ)
async def slash_resume(interaction: discord.Interaction):
    await resume_handler(interaction)

@bot.tree.command(name="skip", description="Skip the current song", guild=GUILD_OBJ)
async def slash_skip(interaction: discord.Interaction):
    await skip_handler(interaction)

@bot.tree.command(name="stop", description="Stop playback and disconnect", guild=GUILD_OBJ)
async def slash_stop(interaction: discord.Interaction):
    await stop_handler(interaction)

@bot.tree.command(name="join", description="Join your voice channel", guild=GUILD_OBJ)
async def slash_join(interaction: discord.Interaction):
    await join_handler(interaction)

@bot.tree.command(name="leave", description="Leave the voice channel", guild=GUILD_OBJ)
async def slash_leave(interaction: discord.Interaction):
    await leave_handler(interaction)

@bot.tree.command(name="queue", description="Show the music queue", guild=GUILD_OBJ)
async def slash_queue(interaction: discord.Interaction):
    await queue_handler(interaction)

@bot.tree.command(name="purge", description="Delete multiple messages", guild=GUILD_OBJ)
@app_commands.describe(amount="Number of messages to delete (1-100)")
async def slash_purge(interaction: discord.Interaction, amount: int):
    await purge_handler(interaction, amount)

@bot.tree.command(name="play", description="Play a song from URL or search", guild=GUILD_OBJ)
@app_commands.describe(search="YouTube/SoundCloud URL or search term")
async def slash_play(interaction: discord.Interaction, search: str):
    await interaction.response.defer()
    await play_handler(interaction, search)

# Auto-delete bot commands
@bot.tree.command(name="autodelete_add", description="Add a bot for auto-delete of its messages", guild=GUILD_OBJ)
@app_commands.describe(bot_id="The bot's user ID", delay="Delay in seconds before deleting messages")
async def autodelete_add(interaction: discord.Interaction, bot_id: int, delay: int):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission to manage messages.", ephemeral=True)
        return
    if delay < 1 or delay > 300:
        await interaction.response.send_message("Delay must be between 1 and 300 seconds.", ephemeral=True)
        return
    tracked_bots[bot_id] = delay
    save_tracked_bots()
    await interaction.response.send_message(f"Added bot ID {bot_id} with auto-delete delay {delay}s.", ephemeral=True)

@bot.tree.command(name="autodelete_remove", description="Remove a bot from auto-delete tracking", guild=GUILD_OBJ)
@app_commands.describe(bot_id="The bot's user ID")
async def autodelete_remove(interaction: discord.Interaction, bot_id: int):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission to manage messages.", ephemeral=True)
        return
    if bot_id in tracked_bots:
        tracked_bots.pop(bot_id)
        save_tracked_bots()
        await interaction.response.send_message(f"Removed bot ID {bot_id} from auto-delete tracking.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Bot ID {bot_id} not found in auto-delete tracking.", ephemeral=True)



# Run bot
bot.run(token)


























