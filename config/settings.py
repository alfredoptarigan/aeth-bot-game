"""
Bot Settings and Configuration
"""
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging configuration
logging.basicConfig(level=logging.INFO)

# Discord Bot Token
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Database Configuration (if needed in the future)
DATABASE_URL = os.getenv('DATABASE_URL', '')

def validate_config():
    """Validate that all required configuration is present"""
    if not DISCORD_TOKEN:
        raise ValueError("❌ DISCORD_TOKEN tidak ditemukan di .env!")
    return True