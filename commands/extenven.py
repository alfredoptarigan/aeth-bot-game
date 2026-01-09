"""
Expansion inventory
"""

import discord
from commands.base import BaseCommand
from database.queries.user_queries import get_user_data, update_full_user_data
from database.queries.expan_inven import get_inventory_upgrade_cost, set_inventory_upgrade_cost, get_next_inventory_upgrade_cost, upgrade_inventory
from config.constants import PREFIX

class ExpansionInventoryCommands(BaseCommand):
    """Handles expansion inventory commands"""

    async def handle_expand_inventory(self, message, msg_lower_parts):
        """Handle the expand inventory command"""
        user_id = message.author.id
        user_data = list(get_user_data(user_id))
        
        current_level = user_data[10] 
        current_cost = get_inventory_upgrade_cost(user_id)
        
        if current_cost is None:
            current_cost = 500 
        
        if user_data[3] < current_cost:
            await message.channel.send(f"❌ You don't have enough money to upgrade your inventory! You need {current_cost} coins.")
            return
        
        # Deduct money and upgrade inventory
        user_data[3] -= current_cost
        user_data[10] += 1 
        
        # Calculate next upgrade cost
        next_cost = get_next_inventory_upgrade_cost(current_level + 1)
        set_inventory_upgrade_cost(user_id, next_cost)
        
        update_full_user_data(user_id, *user_data)
        
        await message.channel.send(f"✅ Successfully upgraded your inventory to level {user_data[10]}! Next upgrade will cost {next_cost} coins.")