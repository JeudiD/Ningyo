# Discord Bot

A Python-powered Discord bot using py-cord.  
Features slash commands like `/ping` and `/purge`.

## How to Run
1. Create a `.env` file with your `DISCORD_TOKEN`.
2. Run `python watchdog_runner.py` to auto-reload on changes.

## Requirements
- py-cord
- python-dotenv
- watchdog

## Commands
- `/ping`: Replies with "Pong!"
- `/purge`: Deletes a specified number of messages (admin-only)



# Steps of Bot Creation

# 1 Project Setup
- Created the project folder and initialized a Python file named bot.py
- Installed required packages: py-cord, python-dotenv, watchdog
- Set up a .env file to store the Discord bot token securely
- Added .env to .gitignore to prevent it from being pushed to GitHub

# 2 Basic Bot Initialization
- Imported necessary modules: discord, os, logging, dotenv, commands from discord.ext
- Used load_dotenv() to pull in the DISCORD_TOKEN from the .env file
- Defined discord.Intents and enabled message_content so the bot can read messages
- Created a bot instance using py-cord with slash command support

# 3 Bot Startup Confirmation
- @bot.event
- async def on_ready():
    - Logs a confirmation message in the terminal when the bot starts successfully

# 4 Ping Slash Command
- @bot.slash_command(name="ping", description="Check if the bot is alive")
- async def ping(ctx):
    - Responds with 🏓 Pong! when the user uses the /ping command
    - Confirms the bot is running and listening


# 5 Purge Slash Command with Permissions
- @bot.slash_command(name="purge", description="Delete a number of messages")
- @commands.has_permissions(manage_messages=True)
- async def purge(ctx, amount: int):
    - Deletes `amount + 1` messages in the channel where the command is used
    - Includes the command message itself in the deletion count
    - Only users with "Manage Messages" permission can use this

- @purge.error
- async def purge_error(ctx, error):
    - Sends a private error message if the user doesn’t have permission

# 6 Running the Bot
- Used bot.run(token) at the bottom of bot.py to start the bot

# 7 Auto-Restart With Watchdog
- Created a second file: watchdog_runner.py
- Uses watchdog to observe any Python file changes in the current directory
- If any file is modified (excluding __pycache__), it restarts the bot process
- This allows live development without manually restarting the bot

# 8 Pushing to GitHub
- Initialized a Git repo in the project folder
- Created and checked .gitignore to make sure .env is excluded
- Committed the code and pushed to GitHub repo using:
- git add .
- git commit -m "Initial bot setup with slash commands and auto-reload"
- git push origin master

# 9 Set up automatic bot restart with file changes
- Created a file originally called watchdog_runner.py, renamed later to bot_watcher.py.
- Used watchdog library to monitor .py files in the project.
- When changes are detected, the bot process is killed and restarted automatically.
- Ensures faster testing without needing to manually stop and relaunch the bot every time.

# 10 Made the watcher cross-platform safe
- Used:
- self.process = subprocess.Popen(["python", "bot.py"], cwd=os.path.dirname(__file__))
- to ensure bot.py runs from the right directory regardless of where it's launched from.

# 11 Logging added
- Added logging to both bot.py and the watcher file.
- Helps debug startup issues and tracks when the bot goes online.

# 12 Renamed runner to something clearer
- Renamed watchdog_runner.py ➜ bot_watcher.py for clarity.
- No other file references needed changing since it’s run directly, not imported.

# 13 Fixed token not loading issue
- Ensured .env was in the correct project root.
- Made sure DISCORD_TOKEN was defined inside .env as:
- DISCORD_TOKEN=your_token_here
- Confirmed that load_dotenv() was called before reading the token.

# 14 Pushed updates to GitHub
- Used git add ., git commit -m, and git push origin master to upload:
- Updated bot.py
- bot_watcher.py
- Enhanced README.md
- .gitignore (to keep .env and __pycache__ private)

# 15 Fixed Token Location Issue
- Realized your bot token was not where the code expected it.
- Moved or fixed the .env file to correctly load DISCORD_TOKEN.

# 16 Added Slash Commands Support  
- Transitioned from prefix-only commands to using Discord’s slash commands.
- Added slash command decorators with @bot.slash_command().
- Implemented ping and purge as slash commands.
- Added guild_ids=[your_guild_id] to slash commands for faster local testing.

# 17 Tested Slash Commands
- Verified commands show up in the specified guild/server.
- Noted global commands take longer to propagate.

# 18 Added Classic Prefix Commands Back
- Introduced command_prefix="!" on commands.Bot() to support prefix commands alongside slash commands.
- Created prefix version of purge command using @bot.command().
- Added ephemeral-like behavior to prefix commands by sending messages with delete_after parameter.

# 19 Added Error Handling to Commands
- Implemented error handlers, especially for permission errors on purge.
- Responded to users without permissions gracefully.
- Logged unexpected errors for debugging.

# 20 Improved Code Style and Logging
- Added proper logging throughout, including bot startup and command errors.
- Used consistent environment variable handling with dotenv.