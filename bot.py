import discord
import os
import logging
import json
from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands
import asyncio
import requests
from discord.ext import tasks
import datetime
from datetime import datetime, timedelta

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Load env
load_dotenv()
token = os.getenv("DISCORD_TOKEN")
if not token:
    raise ValueError("🚨 DISCORD_TOKEN not found in environment variables.")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="n", intents=intents)

GUILD_ID = 1030603151033769994
GUILD_OBJ = discord.Object(id=GUILD_ID)

WELCOME_CHANNEL_ID = 1030723841426722878

# Auto-delete config
TRACKED_BOTS_FILE = "tracked_bots.json"
if os.path.isfile(TRACKED_BOTS_FILE):
    with open(TRACKED_BOTS_FILE, "r") as f:
        tracked_bots = {int(k): v for k, v in json.load(f).items()}
else:
    tracked_bots = {}

def save_tracked_bots():
    with open(TRACKED_BOTS_FILE, "w") as f:
        json.dump(tracked_bots, f)
# --- MEME CONFIG ---
MEME_CHANNEL_ID = 1030749131469242389  # replace with your channel ID

def get_random_meme():
    """Fetch a fresh meme from meme-api."""
    try:
        response = requests.get("https://meme-api.com/gimme")
        if response.status_code == 200:
            data = response.json()
            return data.get("url")
    except Exception as e:
        logging.warning(f"Error fetching meme: {e}")
    return None

@tasks.loop(hours=24)
async def daily_meme():
    """Send a fresh meme once every 24 hours."""
    channel = bot.get_channel(MEME_CHANNEL_ID)
    if channel:
        meme_url = get_random_meme()
        if meme_url:
            await channel.send(f"**Meme of the Day 😎**\n{meme_url}")

async def wait_until(hour, minute=0):
    """Wait until a specific time to start the daily meme loop."""
    now = datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target < now:
        target += timedelta(days=1)
    await asyncio.sleep((target - now).total_seconds())

# Helpers
async def send_response(ctx_or_interaction, message, ephemeral=False):
    if hasattr(ctx_or_interaction, "send"):
        await ctx_or_interaction.send(message)
    else:
        try:
            await ctx_or_interaction.response.send_message(message, ephemeral=ephemeral)
        except discord.InteractionResponded:
            await ctx_or_interaction.followup.send(message, ephemeral=ephemeral)

# Handlers
async def ping_handler(ctx_or_interaction):
    await send_response(ctx_or_interaction, "🏓 Pong!", ephemeral=True)

async def purge_handler(ctx_or_interaction, amount: int):
    if not hasattr(ctx_or_interaction, "guild") or not ctx_or_interaction.guild:
        await send_response(ctx_or_interaction, "This must be used in a server.", ephemeral=True)
        return

    perms = None
    if hasattr(ctx_or_interaction, "author"):
        perms = ctx_or_interaction.author.guild_permissions
    elif hasattr(ctx_or_interaction, "user"):
        perms = ctx_or_interaction.user.guild_permissions

    if not perms or not perms.manage_messages:
        await send_response(ctx_or_interaction, "You don’t have permission.", ephemeral=True)
        return

    if amount < 1 or amount > 100:
        await send_response(ctx_or_interaction, "Choose 1–100.", ephemeral=True)
        return

    if not hasattr(ctx_or_interaction, "send"):
        await ctx_or_interaction.response.defer(ephemeral=True)

    deleted = await ctx_or_interaction.channel.purge(limit=amount + 1)
    await send_response(ctx_or_interaction, f"Deleted {len(deleted)-1} messages.", ephemeral=True)

# Events
@bot.event
async def on_ready():
    logging.info(f"✅ Bot is online as {bot.user}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="RIDE ON SHOOTING STAR"))
    await bot.tree.sync(guild=GUILD_OBJ)

    # Start the daily meme loop at 12:00 PM server time
    async def start_meme_loop():
        await wait_until(12, 0)  # wait until 12:00
        daily_meme.start()

    bot.loop.create_task(start_meme_loop())

    # Post a meme immediately
    meme_url = get_random_meme()
    channel = bot.get_channel(MEME_CHANNEL_ID)
    if channel and meme_url:
        await channel.send(f"**Meme of the Day 😎**\n{meme_url}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    delay = tracked_bots.get(message.author.id)
    if delay is not None:
        await asyncio.sleep(delay)
        try:
            await message.delete()
        except Exception:
            pass
    await bot.process_commands(message)


#greets joining/leaving
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="🎉 Welcome!",
            description=f"Hey {member.mention}, welcome to **{member.guild.name}**!",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text=f"Member #{len(member.guild.members)} • Glad you’re here!")
        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="👋 Goodbye!",
            description=f"{member.name} has left the server.",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        await channel.send(embed=embed)



# Commands
@bot.command()
async def ping(ctx): await ping_handler(ctx)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int): await purge_handler(ctx, amount)

@bot.tree.command(name="ping", description="Ping", guild=GUILD_OBJ)
async def slash_ping(interaction: discord.Interaction): await ping_handler(interaction)

@bot.tree.command(name="purge", description="Delete messages", guild=GUILD_OBJ)
@app_commands.describe(amount="How many (1–100)")
async def slash_purge(interaction: discord.Interaction, amount: int):
    await purge_handler(interaction, amount)

@bot.tree.command(name="autodelete_add", description="Add bot auto-delete", guild=GUILD_OBJ)
async def autodelete_add(interaction: discord.Interaction, bot_id: int, delay: int):
    tracked_bots[bot_id] = delay
    save_tracked_bots()
    await interaction.response.send_message(f"Added bot {bot_id} delay {delay}s", ephemeral=True)

@bot.tree.command(name="autodelete_remove", description="Remove bot auto-delete", guild=GUILD_OBJ)
async def autodelete_remove(interaction: discord.Interaction, bot_id: int):
    tracked_bots.pop(bot_id, None)
    save_tracked_bots()
    await interaction.response.send_message(f"Removed bot {bot_id}", ephemeral=True)

bot.run(token)



























