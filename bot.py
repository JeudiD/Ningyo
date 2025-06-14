import discord
import os
import logging
import json                      # <<< ADDED
from dotenv import load_dotenv
from discord.ext import commands
import asyncio                   # <<< ADDED

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

# Create bot instance, no command prefix because we use slash commands only
#bot = commands.Bot(intents=intents) <----we dont need this with the other to support both commands
bot = commands.Bot(command_prefix="n", intents=intents)

# <<< ADDED: Tracked bots JSON file and dictionary
TRACKED_BOTS_FILE = "tracked_bots.json"

# Load tracked bots from file if it exists
if os.path.isfile(TRACKED_BOTS_FILE):
    with open(TRACKED_BOTS_FILE, "r") as f:
        tracked_bots = json.load(f)
    # json keys are strings, convert to int keys
    tracked_bots = {int(k): v for k, v in tracked_bots.items()}
else:
    tracked_bots = {}

def save_tracked_bots():
    with open(TRACKED_BOTS_FILE, "w") as f:
        json.dump(tracked_bots, f)

@bot.event
async def on_ready():
    logging.info(f"✅ Bot is online as {bot.user}")

#prefix ping
@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

# Slash command: ping
@bot.slash_command(name="ping", description="Check if the bot is alive", guild_ids=[1030603151033769994])
async def ping(ctx):
    await ctx.respond("🏓 Pong!")

#prefix purge
@bot.command(name = "purge")
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to include the command message
    await ctx.send(f"🧹 Deleted {len(deleted) - 1} messages", delete_after=5)

# Slash command: purge - deletes specified number of messages + the command message itself
@bot.slash_command(name="purge", description="Delete a number of messages", guild_ids=[1030603151033769994])
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to include the command message
    await ctx.respond(f"🧹 Deleted {len(deleted) - 1} messages", ephemeral=True)

# Handle missing permissions error for purge command
@purge.error
async def purge_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.respond("🚫 You don't have permission to use this command.", ephemeral=True)
    else:
        # Log unexpected errors
        logging.error(f"Error in purge command: {error}")
        await ctx.respond("❌ An unexpected error occurred.", ephemeral=True)

# <<< ADDED: Commands to track/untrack/list tracked bots, with admin permission

@bot.command(name="trackbot")
@commands.has_permissions(administrator=True)
async def track_bot(ctx, bot_id: int, delay: int):
    """Start deleting messages from a bot after delay seconds."""
    tracked_bots[bot_id] = delay
    save_tracked_bots()
    await ctx.send(f"✅ Now tracking bot ID `{bot_id}` to delete messages after {delay} seconds.")

@bot.command(name="untrackbot")
@commands.has_permissions(administrator=True)
async def untrack_bot(ctx, bot_id: int):
    """Stop deleting messages from a tracked bot."""
    if bot_id in tracked_bots:
        tracked_bots.pop(bot_id)
        save_tracked_bots()
        await ctx.send(f"✅ Stopped tracking bot ID `{bot_id}`.")
    else:
        await ctx.send(f"❌ Bot ID `{bot_id}` is not currently tracked.")

@bot.command(name="listtracked")
@commands.has_permissions(administrator=True)
async def list_tracked(ctx):
    """List all tracked bots and their delays."""
    if tracked_bots:
        msg = "Tracked bots:\n" + "\n".join(f"ID: {bid} — Delay: {delay}s" for bid, delay in tracked_bots.items())
    else:
        msg = "No bots are currently being tracked."
    await ctx.send(msg)

# <<< ADDED: Slash commands for tracking bots

@bot.slash_command(name="trackbot", description="Start auto-deleting messages from a bot after delay seconds", guild_ids=[1030603151033769994])
@commands.has_permissions(administrator=True)
async def trackbot_slash(ctx, bot_id: int, delay: int):
    tracked_bots[bot_id] = delay
    save_tracked_bots()
    await ctx.respond(f"✅ Now tracking bot ID `{bot_id}` to delete messages after {delay} seconds.")

@bot.slash_command(name="untrackbot", description="Stop auto-deleting messages from a tracked bot", guild_ids=[1030603151033769994])
@commands.has_permissions(administrator=True)
async def untrackbot_slash(ctx, bot_id: int):
    if bot_id in tracked_bots:
        tracked_bots.pop(bot_id)
        save_tracked_bots()
        await ctx.respond(f"✅ Stopped tracking bot ID `{bot_id}`.")
    else:
        await ctx.respond(f"❌ Bot ID `{bot_id}` is not currently tracked.")

@bot.slash_command(name="listtracked", description="List all tracked bots and their delays", guild_ids=[1030603151033769994])
@commands.has_permissions(administrator=True)
async def listtracked_slash(ctx):
    if tracked_bots:
        msg = "Tracked bots:\n" + "\n".join(f"ID: {bid} — Delay: {delay}s" for bid, delay in tracked_bots.items())
    else:
        msg = "No bots are currently being tracked."
    await ctx.respond(msg)

# <<< ADDED: on_message event to delete messages from tracked bots

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




