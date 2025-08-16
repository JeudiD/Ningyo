# Ningyo Bot (Non-Music)

A Python-powered Discord bot using py-cord, focusing on moderation, auto-delete, and utility commands.

### 📌 Hosting Notes
Runs continuously on Windows via NSSM (Non-Sucking Service Manager), keeping the bot online without an open terminal.

Configured for a personal Discord server, but flexible for deployment elsewhere.

## How to Run
1. Create a .env file with your DISCORD_TOKEN.
2. Run the bot:
- python bot.py

## Requirements
- Python 3.10 or higher
- discord.py / py-cord
- python-dotenv
- Python's built-in logging module

## Commands
- /ping or !ping – Check if the bot is online. Responds with 🏓 Pong!
- /purge [amount] or !purge [amount] – Deletes a specified number of messages (admin-only).
- /auto-delete add [bot/user] or !auto-delete add [bot/user] – Add a user/bot to the auto-delete list.
- /auto-delete remove [bot/user] or !auto-delete remove [bot/user] – Remove a user/bot from the auto-delete list.
- /listtracked or !listtracked – Show users/bots currently tracked for auto-delete.

## Attribution

If you use or modify this bot, a simple shout-out or mention would be appreciated but is not required. Thanks for supporting my work!

## Steps of Bot Creation    

# 1. Project Setup
- Created project folder and bot.py.
- Installed required packages: py-cord, python-dotenv.
- Added .env for DISCORD_TOKEN and added it to .gitignore.

# 2. Basic Bot Initialization
- Loaded DISCORD_TOKEN via dotenv.
- Enabled message_content intent for reading messages.
- Created bot instance supporting both prefix and slash commands.

# 3. Bot Startup Confirmation
- on_ready() logs a message when the bot starts successfully.

# 4. Ping Command
- Implemented /ping and !ping.
- Confirms bot is running.

# 5. Purge Command
- /purge [amount] and !purge [amount] delete messages.
- Checks user permissions (manage_messages).
- Error handling for missing permissions.

# 6. Auto-Delete Tracking
- /auto-delete add/remove and /listtracked commands implemented.
- Tracked users/bots stored in tracked_bots.json for persistence.

# 7. Dual Command System
- Both slash and prefix commands supported for main actions.
- Permissions enforced consistently.

# 8. Error Handling
- Logs unexpected errors.
- Graceful user feedback for permission issues.

# 9. Logging
- Added logging for startup, command usage, and errors.
- Consistent handling of environment variables.

# 10. GitHub Push Setup
- Initialized Git repo and added .gitignore.
- Committed and pushed code while keeping .env private.

# 11. Background Hosting via NSSM
- Configured Windows service for bot:
    - Python executable path
    - Bot script path
    - Service name (e.g., DiscordBotNingyo)
- Eliminates need to keep terminals open or use Task Scheduler.

# 12. Persistent Bot Tracking
- JSON file keeps track of bots/users to auto-delete messages.
- Data survives restarts and service resets.

# 13. Improved Command Usability
- Bot now accepts mentions instead of raw IDs for tracking commands.
- Consistent behavior between prefix and slash commands.

# 14. Daily Meme Feature
- Bot automatically posts a fresh meme every day in a designated channel.
- Uses Meme API to fetch random memes; no static images.
- Posts labeled “Meme of the Day”.
- Optionally posts a meme immediately when the bot starts.
- Configuration is hard-coded:
- Channel ID must be set directly in the code (MEME_CHANNEL_ID).
- Posting time/interval is fixed in the code and cannot be changed via commands.