import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram Bot token from BotFather
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set in environment")

# Bot username (for generating invite link)
BOT_USERNAME = os.getenv("BOT_USERNAME", "PavelDumbrao_bot")

# Admin user IDs (comma-separated in .env, e.g. "12345,67890")
admins = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x) for x in admins.split(",") if x.isdigit()]

# Channel and Group IDs for subscription checks (should be integers, possibly negative for channels/groups)
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
GROUP_ID = int(os.getenv("GROUP_ID", "0"))
if CHANNEL_ID == 0 or GROUP_ID == 0:
    raise RuntimeError("CHANNEL_ID or GROUP_ID not set in environment")

# YooMoney API token and wallet
YOOMONEY_TOKEN = os.getenv("YOOMONEY_TOKEN")
YOOMONEY_WALLET = os.getenv("YOOMONEY_WALLET")
if not YOOMONEY_TOKEN or not YOOMONEY_WALLET:
    raise RuntimeError("YooMoney credentials not set in environment")

# Premium access pricing
PREMIUM_COST_RUB = 2  # cost in rubles
PREMIUM_COST_POINTS = 500  # cost in points

# (Optional) invite link or username for closed premium group/channel
CLOSED_COMMUNITY_LINK = os.getenv("CLOSED_COMMUNITY_LINK", "")
CLOSED_CHAT_ID = os.getenv("CLOSED_CHAT_ID", "")
