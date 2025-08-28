import os
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Google Sheets configuration
SHEETS_SPREADSHEET_ID = os.getenv("SHEETS_SPREADSHEET_ID")
SHEETS_RANGE = os.getenv("SHEETS_RANGE", "Sheet1!A2:C")

# Intro text for /start command
INTRO_TEXT = (
    "Welcome to the PYQ Bot!\n\n"
    "This bot helps you find previous year question papers for your subjects.\n"
    "Use /start to select your year and branch.\n\n"
    "You can also directly send a subject code to get its link.\n"
    "Example: 23BS1001"
)