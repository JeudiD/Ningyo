import discord

print("Opus loaded:", discord.opus.is_loaded())

if not discord.opus.is_loaded():
    try:
        discord.opus.load_opus("opus.dll")
        print("Opus loaded manually:", discord.opus.is_loaded())
    except Exception as e:
        print("Failed to load opus.dll:", e)
