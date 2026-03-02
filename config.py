from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables.")

if not CHAT_ID:
    raise ValueError("CHAT_ID not found in environment variables.")