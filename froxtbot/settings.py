import logging
import sys
from datetime import datetime
from typing import Dict, Any

# Enhanced logging configuration
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Bot Configuration
BOT_TOKEN = "8374407374:AAG420w3D7vl-kpzboXkDVjqrEFZbs0hjfU"
BOT_NAME = "🔍FroxtXOSINT Bot"
ADMIN_IDS = [6792765047,7846896084]
FORCE_JOIN_CHANNELS = ["@yufqxwuyGEN","TeamXcodex"]

# Broadcast Channel Configuration
# IMPORTANT: Replace with the actual numeric ID of your updates channel (e.g., -1001234567890)
# You can get the channel ID by forwarding a message from the channel to @RawDataBot
UPDATES_CHANNEL_ID = -1001978901234 # Placeholder ID for @UpdatesXBots/3 - User needs to replace with actual ID
BROADCAST_INTERVAL_SECONDS = 60 # Check for new messages every 60 seconds

# Default API Configuration - Moved from database to code
DEFAULT_API_CONFIG: Dict[str, Any] = {
    "API_BASE_URL": "https://presents-specialties-mention-simpson.trycloudflare.com",
    "API_KEY": "sultan123",
    "REQUEST_TIMEOUT": 30,
    "MAX_RETRIES": 2,
    "RETRY_DELAY": 1,
    "MAX_MESSAGE_LENGTH": 4096,
    "MAX_PRETTY_PRINT_LENGTH": 2000,
    "PAGINATION_SIZE": 10
}

DATABASE_FILE = "enhanced_users.json"
BACKUP_FILE = "enhanced_users_backup.json"
