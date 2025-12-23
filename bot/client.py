"""
Discord Bot Client Setup
"""
import discord
from config.settings import DISCORD_TOKEN

# Bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Create bot client
bot = discord.Client(intents=intents)

def get_bot():
    """Get bot instance"""
    return bot

def run_bot():
    """Run the bot"""
    from config.settings import validate_config
    validate_config()
    bot.run(DISCORD_TOKEN)