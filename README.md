# Discord Bot

A Python-powered Discord bot using py-cord.  
Features slash commands like `/ping` and `/purge`.

### 📌 Note on Hosting
> The bot runs continuously on the Windows PC as a background service via NSSM, effectively making this PC the host/server.  
>
> It is currently configured to work for a **personal Discord server** with setup, commands, and permissions tailored to that environment. However, the codebase is flexible — you can modify the command structure, token, and configuration to deploy it to **other servers or cloud hosting platforms** if needed.


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

# 21 Switched to NSSM for Background Execution
- We installed NSSM (Non-Sucking Service Manager) to manage the bot as a Windows background service. This lets the bot stay online without needing an open terminal window or user - - interaction after system boot.

# 22 Located the Correct NSSM Path
- Identified the correct installation path for NSSM:
- C:\Users\Dale\Downloads\nssm-2.24\nssm-2.24\win64

# 23 Created a Windows Service Using NSSM
- Used the NSSM GUI to configure a new service:
- Path: C:\Users\Dale\AppData\Local\Programs\Python\Python313\python.exe
- Startup Directory: C:\Users\Dale\DiscordBot
- Arguments: bot.py
- Named the service something identifiable (e.g. DiscordBotNingyo).
- This eliminated the need to keep Git Bash, VSCode, or any other terminal open.

# 24 Verified Bot Runs in Background
- Confirmed that the bot starts automatically and runs silently in the background via Windows Services.

# 25 Retired bot_watcher.py and Task Scheduler
- Since NSSM handles restarts and running in the background, we no longer need:
- bot_watcher.py
- runbot.bat
- Task Scheduler setup

# 26 Organized and Named Multiple README Files
- Created multiple README documents in the repo:
- README.md: General overview of the bot.
- README_NSSM.md: Documentation specific to background service setup using NSSM.
- These won’t conflict in GitHub as long as filenames are unique and referenced properly.

# 27 Bot Mention Support for Track Commands
- Users can now mention bots (e.g. @BotName) instead of manually entering numeric IDs in trackbot and untrackbot commands.
- Applies to both prefix and slash commands
- Internally uses discord.User type and accesses .id for tracking
- Improves usability and minimizes input errors

# 28 Unified Dual Command System (Prefix + Slash)
- All major bot actions now exist as both traditional prefix commands and modern slash commands:
- ping, purge, trackbot, untrackbot, listtracked
- Permissions are enforced consistently
- Slash commands are registered to a test guild (for fast updates)

# 29 Persistent Bot Tracking with JSON Storage
- Tracked bot IDs and their delete delay settings are now saved to a JSON file (tracked_bots.json).
- Survives restarts and service resets
- Automatically loads data on bot startup
- Uses json.load() and json.dump() with conversion for proper ID handling

# 30 Auto-Delete Tracked Bot Messages (After Delay)
- The bot now automatically deletes messages sent by tracked bots after a custom delay.
- Runs via on_message event
- Skips deleting its own messages
- Handles permission errors gracefully
- Uses asyncio.sleep(delay) to time deletions

# 31 Better Error Handling in Purge Command
- purge command now includes a proper error handler:
- Detects and reports missing permissions
- Logs unknown/unexpected errors to the console
- Ensures user feedback is clear and non-crashing

# 32 Added Discord Bot Presence (Listening Status)
- Introduced a presence update on bot startup using bot.change_presence().
- Bot now shows "Listening to Lofi Chill Mix – ChilledCow" as its status, making it feel more alive and interactive.
- Used discord.Activity with ActivityType.listening to simulate a user-like listening experience.
- Presence logic placed inside on_ready() event for automatic activation when the bot connects.

# 33 Prepared Project Environment
- Installed core libraries: discord.py, yt-dlp
- Installed FFmpeg for real-time audio streaming
- Created a basic bot skeleton using discord.ext.commands

# 34 Implemented Voice Channel Support
- Added !join command for joining the user’s current voice channel
- Ensured the bot could move between channels if already connected
- Tested functionality live on Discord server

# 35 Verified FFmpeg Installation and PATH Configuration
- Confirmed FFmpeg was installed via ffmpeg -version
- Added the correct bin directory to Windows User PATH:
- C:\Users\Dale\Downloads\ffmpeg-7.1.1-essentials_build\bin
- Restarted VSCode to ensure the PATH change was recognized in terminal

# 36 Diagnosed and Resolved Playback Errors
- Investigated ClientException: ffmpeg was not found
- Verified that FFmpeg was callable from both PowerShell and VSCode
- Confirmed that FFmpeg was usable via discord.FFmpegOpusAudio.from_probe()

# 37 Integrated yt-dlp for YouTube Playback
- Added yt_dlp to project dependencies
- Configured YoutubeDL with default_search: 'auto' to support links and search queries
- Implemented fallback logic for full stream metadata extraction
- Set noplaylist = True and extract_flat = False to avoid playlist issues

# 38 Implemented Working Audio Queue and Playback System
- Built song_queue per guild to manage music tracks
- Added play_next() coroutine to continue playback automatically
- Used FFmpegOpusAudio.from_probe() for streaming without file downloads
- Enabled both !play (prefix) and /play (slash) command support

# 39 Improved Error Handling and Logging
- Wrapped yt-dlp and playback calls in try/except blocks
- Configured logging to INFO level for Discord events and bot actions
- Handled voice join failures, queue underruns, and yt-dlp extraction issues

# 40 Fixed yt-dlp Extraction Options
- Removed extract_flat: 'in_playlist' and replaced with extract_flat: False
- Ensured extracted info includes url needed for FFmpeg streaming

# 41 Confirmed Working Music Playback Flow
- Final test verified that bot can:
- Join VC
- Play by name or link
- Queue multiple songs
- Stream YouTube audio seamlessly
- Example: !play 20 mins by Uzi now works using yt-dlp's search, no direct link required

# 42 Added Pause and Resume Commands
- Implemented basic pause/resume for the music player
- Allows users to control playback flow during songs

# 43 Added Skip and Stop Commands
- Skip stops current song and moves to next
- Stop clears queue, disconnects bot, and cancels disconnect timer

# 44 Added Auto-Disconnect Logic
- Bot auto-disconnects if alone in voice channel for 5 minutes.
- Checks every 60 seconds.
- Prevents bot staying in empty VC forever.

# 45 Implemented Wipe Script for Global Slash Commands
- Created separate script to delete all global slash commands quickly.
- Used Discord REST API with requests.
- Environment variables for token and app ID.
- Ensured wipe worked by testing commands disappeared on Discord client.

# 46 Added Queue Command (Prefix and Slash)
- Show current queue of songs with titles listed.
- Useful to check what’s next in line.

# 47 Added Robust Music Playback Logic
- Used yt-dlp to search YouTube and SoundCloud.
- Queue management with async playback.
- FFmpeg audio streaming with reconnect options.
- After playback ends, automatically plays next song in queue.
- Supports URL or search query input.

# 48 Added Detailed Logging and Error Handling
- Logging level set to INFO for important events.
- Catches exceptions in YouTube/SoundCloud info extraction.
- Logs warnings when failures occur.

# 49 Persistent UI for Music Controls and Queue Pagination
- Added MusicControls view with buttons for Pause, Resume, Skip, Stop, Repeat Mode, and Volume adjustments, providing ephemeral user feedback.
- QueuePagination view allows paginated display of the song queue with navigation restricted to the requester. Both views support interactive control without needing to resend.

# 50 Playback Enhancements with Repeat and Volume Control
- Now Playing message dynamically updates with song info, requester, repeat mode, and volume.
- Repeat modes (Off, Repeat One, Repeat All) controlled via UI button.
- Volume adjustable between 0.0 and 1.0 through UI, integrated into playback and reflected in embeds.

# 51 Improved Playback Management
- play_next handles queue management respecting repeat mode, includes error handling, and uses FFmpeg reconnect options for stability.

# 52 Slash Commands Aligned with Prefix Commands, Emphasizing Ephemeral Responses
- Slash commands replicate prefix functionality but emphasize ephemeral responses to reduce channel clutter, improving user experience.

# 53 Miscellaneous Improvements
- Startup logging, error handling, and clean code structure throughout.

# 54 Opus Library Setup & Voice Channel Join Fix
- Problem:
Bot was able to join voice channels initially but started joining and immediately leaving afterward. This was due to missing or improperly loaded Opus codec, required by Discord voice to encode/decode audio.

- Cause:
The bot did not have the Opus dynamic library (e.g., libopus.dll) available or properly loaded.
Without Opus, voice connections become unstable and drop.

- Solution Steps:
Download the prebuilt Opus DLL for Windows 64-bit from a trusted source:
Example trusted link:
https://dsharpplus.emzi0767.com/natives/vnext_natives_win32_x64.zip
(Inside this archive, libopus.dll is included)

- Extract libopus.dll and place it in your bot’s root directory (or the directory where your bot script runs).
- Rename libopus.dll to opus.dll (optional but recommended for direct loading).
- In your Python bot code (bot.py), add the following at the top (before voice connection attempts):
python
Copy
Edit
import discord
if not discord.opus.is_loaded():
    discord.opus.load_opus("opus.dll")

- Confirm the bot loads Opus correctly by checking the log for:
- Opus loaded: True
- Run your bot. It should now join voice channels without immediately leaving.

- Additional Resources:
For more info on installing libopus, see:
https://github.com/shardlab/discordrb/wiki/Installing-libopus?utm_source=chatgpt.com

- Additional Notes:
Make sure your system architecture matches the DLL (64-bit Windows).
Placing opus.dll in the same folder as your bot script is the simplest way to ensure it loads properly.
This fix prevents voice connection issues related to missing Opus codec.

- (PS: Opus is a prebuilt native library, in my experience it was very hard to find an official/trusted (usually because the all the links were broken or gone) one so I hope this helps someone.)