"""
Aetherion Game Bot - Refactored Version
Entry point for the Discord bot
"""
import random
import time
from bot.client import get_bot, run_bot
from bot.events import setup_events
from commands.character import CharacterCommands
from commands.economy import EconomyCommands
from commands.combat import CombatCommands
from commands.help import HelpCommands
from commands.leaderboard import LeaderboardCommands
from commands.inventory import InventoryCommands
from commands.shop import ShopCommands
# from commands.shift import ShiftCommands  # DISABLED - Shift commands
from config.constants import PREFIX

# Initialize bot and command handlers
bot = get_bot()
character_commands = CharacterCommands()
economy_commands = EconomyCommands()
combat_commands = CombatCommands()
help_commands = HelpCommands()
leaderboard_commands = LeaderboardCommands()
inventory_commands = InventoryCommands()
shop_commands = ShopCommands()
# shift_commands = ShiftCommands()  # DISABLED - Shift commands
shift_commands = None  # Placeholder for disabled shift commands

# Setup events
setup_events(bot, character_commands, economy_commands, combat_commands, help_commands, leaderboard_commands, inventory_commands, shop_commands, shift_commands)

if __name__ == "__main__":
    print("🚀 Starting Aetherion Game Bot (Refactored Version)...")
    run_bot()