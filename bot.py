import discord
import os
import logging
from dotenv import load_dotenv
from discord.ext import commands

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

# Run the bot
bot.run(token)



