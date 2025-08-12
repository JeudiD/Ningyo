import discord
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("No Discord token found in environment. Check your .env file.")

intents = discord.Intents.default()
client = discord.Client(intents=intents)

VOICE_GUILD_ID = 1030603151033769994  # Replace with your guild ID (int)
VOICE_CHANNEL_ID = 1219540473639866369  # Replace with your voice channel ID (int)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

    guild = client.get_guild(VOICE_GUILD_ID)
    if not guild:
        print("Guild not found. Check VOICE_GUILD_ID.")
        await client.close()
        return

    channel = guild.get_channel(VOICE_CHANNEL_ID)
    if not channel:
        print("Voice channel not found. Check VOICE_CHANNEL_ID.")
        await client.close()
        return

    try:
        print(f"Connecting to voice channel: {channel.name}")
        voice_client = await channel.connect()
        print("Connected! Staying connected until you stop the bot.")
        # Stay connected indefinitely
        await asyncio.Event().wait()
    except Exception as e:
        print(f"Failed to connect to voice channel: {e}")
    finally:
        if client.is_connected():
            await client.close()

client.run(TOKEN)

