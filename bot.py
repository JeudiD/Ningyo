import discord
import os
import logging
import json
from dotenv import load_dotenv
from discord.ext import commands
import asyncio

# Set up logging for info and above
logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
load_dotenv()

# Grab the bot token from environment variables
token = os.getenv("DISCORD_TOKEN")
if not token:
    raise ValueError("🚨 DISCORD_TOKEN not found in environment variables.")

# Set up intents - message_content is required for reading message content in some commands
intents = discord.Intents.default()
intents.message_content = True

# Create bot instance
bot = commands.Bot(command_prefix="n", intents=intents)

# Tracked bots JSON file and dictionary
TRACKED_BOTS_FILE = "tracked_bots.json"

# Load tracked bots from file if it exists
if os.path.isfile(TRACKED_BOTS_FILE):
    with open(TRACKED_BOTS_FILE, "r") as f:
        tracked_bots = json.load(f)
    tracked_bots = {int(k): v for k, v in tracked_bots.items()}
else:
    tracked_bots = {}

def save_tracked_bots():
    with open(TRACKED_BOTS_FILE, "w") as f:
        json.dump(tracked_bots, f)

#tells u in terminal if bot is online and now gives bot status
@bot.event
async def on_ready():
    logging.info(f"✅ Bot is online as {bot.user}")
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.listening, name="RIDE ON SHOOTING STAR"),
        status=discord.Status.online
    )

# Prefix ping
@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

# Slash command: ping
@bot.slash_command(name="ping", description="Check if the bot is alive", guild_ids=[1030603151033769994])
async def ping(ctx):
    await ctx.respond("🏓 Pong!")

# Prefix purge
@bot.command(name="purge")
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    deleted = await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 Deleted {len(deleted) - 1} messages", delete_after=5)

# Slash purge
@bot.slash_command(name="purge", description="Delete a number of messages", guild_ids=[1030603151033769994])
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    deleted = await ctx.channel.purge(limit=amount + 1)
    await ctx.respond(f"🧹 Deleted {len(deleted) - 1} messages", ephemeral=True)

# Handle purge permission errors
@purge.error
async def purge_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.respond("🚫 You don't have permission to use this command.", ephemeral=True)
    else:
        logging.error(f"Error in purge command: {error}")
        await ctx.respond("❌ An unexpected error occurred.", ephemeral=True)

# Prefix command: trackbot with mention support
@bot.command(name="trackbot")
@commands.has_permissions(administrator=True)
async def track_bot(ctx, bot: discord.User, delay: int):
    tracked_bots[bot.id] = delay
    save_tracked_bots()
    await ctx.send(f"✅ Now tracking bot {bot.mention} to delete messages after {delay} seconds.")

# Prefix command: untrackbot with mention support
@bot.command(name="untrackbot")
@commands.has_permissions(administrator=True)
async def untrack_bot(ctx, bot: discord.User):
    if bot.id in tracked_bots:
        tracked_bots.pop(bot.id)
        save_tracked_bots()
        await ctx.send(f"✅ Stopped tracking bot {bot.mention}.")
    else:
        await ctx.send(f"❌ Bot {bot.mention} is not currently tracked.")

# Prefix command: listtracked
@bot.command(name="listtracked")
@commands.has_permissions(administrator=True)
async def list_tracked(ctx):
    if tracked_bots:
        msg = "Tracked bots:\n" + "\n".join(f"<@{bid}> — Delay: {delay}s" for bid, delay in tracked_bots.items())
    else:
        msg = "No bots are currently being tracked."
    await ctx.send(msg)

# Slash command: trackbot with mention support
@bot.slash_command(name="trackbot", description="Start auto-deleting messages from a bot after delay seconds", guild_ids=[1030603151033769994])
@commands.has_permissions(administrator=True)
async def trackbot_slash(ctx, bot: discord.User, delay: int):
    tracked_bots[bot.id] = delay
    save_tracked_bots()
    await ctx.respond(f"✅ Now tracking bot {bot.mention} to delete messages after {delay} seconds.")

# Slash command: untrackbot with mention support
@bot.slash_command(name="untrackbot", description="Stop auto-deleting messages from a tracked bot", guild_ids=[1030603151033769994])
@commands.has_permissions(administrator=True)
async def untrackbot_slash(ctx, bot: discord.User):
    if bot.id in tracked_bots:
        tracked_bots.pop(bot.id)
        save_tracked_bots()
        await ctx.respond(f"✅ Stopped tracking bot {bot.mention}.")
    else:
        await ctx.respond(f"❌ Bot {bot.mention} is not currently tracked.")

# Slash command: listtracked
@bot.slash_command(name="listtracked", description="List all tracked bots and their delays", guild_ids=[1030603151033769994])
@commands.has_permissions(administrator=True)
async def listtracked_slash(ctx):
    if tracked_bots:
        msg = "Tracked bots:\n" + "\n".join(f"<@{bid}> — Delay: {delay}s" for bid, delay in tracked_bots.items())
    else:
        msg = "No bots are currently being tracked."
    await ctx.respond(msg)

# Delete messages from tracked bots after delay
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

# Run the bot
bot.run(token)





