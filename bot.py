import discord
import os
import logging
from dotenv import load_dotenv
from discord.ext import commands

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load the .env file
load_dotenv()

# Grab the token
token = os.getenv("DISCORD_TOKEN")
if not token:
    raise ValueError("🚨 DISCORD_TOKEN not found in environment variables.")

# Set up bot intents
intents = discord.Intents.default()
intents.message_content = True

# Create bot instance
bot = commands.Bot(intents=intents)

# Bot ready event
@bot.event
async def on_ready():
    logging.info(f"✅ Bot is online as {bot.user}")

# Slash command: ping
@bot.slash_command(name="ping", description="Check if the bot is alive")
async def ping(ctx):
    await ctx.respond("🏓 Pong!")

# Slash command: purge
@bot.slash_command(name="purge", description="Delete a number of messages")
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.respond(f"🧹 Deleted {amount} messages", ephemeral=True)

# Permission error handler for purge
@purge.error
async def purge_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.respond("🚫 You don't have permission to use this command.", ephemeral=True)

# Run the bot
bot.run(token)


