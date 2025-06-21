import requests
import os
from dotenv import load_dotenv

load_dotenv()  # loads .env file in the same folder

BOT_TOKEN = os.getenv("DISCORD_TOKEN")
APP_ID = os.getenv("APPLICATION_ID")  # or hardcode your app id here if you want


headers = {
    "Authorization": f"Bot {BOT_TOKEN}"
}

# Delete all global commands
url = f"https://discord.com/api/v10/applications/{APP_ID}/commands"
response = requests.get(url, headers=headers)

if response.status_code == 200:
    commands = response.json()
    for cmd in commands:
        cmd_id = cmd['id']
        del_url = f"{url}/{cmd_id}"
        del_response = requests.delete(del_url, headers=headers)
        if del_response.status_code == 204:
            print(f"✅ Deleted command: {cmd['name']}")
        else:
            print(f"❌ Failed to delete {cmd['name']} - Status {del_response.status_code}")
else:
    print("❌ Failed to fetch commands:", response.status_code)
