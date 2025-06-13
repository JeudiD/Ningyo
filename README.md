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





