"""
Expansion inventory
"""

import discord
from commands.base import BaseCommand
from database.queries.user_queries import get_user_data, update_full_user_data
from database.queries.expan_inven import calculate_inventory_upgrade_cost, upgrade_inventory
from config.constants import PREFIX

class ExpansionInventoryCommands(BaseCommand):
    """Handles expansion inventory commands"""

    async def handle_expand_inventory(self, message, msg_lower_parts):
        """Handle the expand inventory command"""
        user_id = message.author.id
        user_data = get_user_data(user_id)

        exp, level, money, last_daily, atk, spd, def_stat, dex, crit, mdmg, hp, mp, \
        inventory_slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, \
        last_fight_time, hunt_count, hunt_reset, max_inventory = user_data

        upgrade_cost = calculate_inventory_upgrade_cost(inventory_slots)

        if money < upgrade_cost:
            await message.channel.send(f"❌ You don't have enough money to upgrade your inventory! You need {upgrade_cost} coins.")
            return

        new_slots, cost = upgrade_inventory(user_id, inventory_slots, max_inventory)

        if new_slots is None:
            await message.channel.send(f"❌ Your inventory is already at maximum capacity ({max_inventory} slots)!")
            return

        new_money = money - cost
        next_upgrade_cost = calculate_inventory_upgrade_cost(new_slots)

        update_full_user_data(user_id, exp, level, new_money, last_daily, atk, spd, def_stat, dex,
                              crit, mdmg, hp, mp, new_slots, equipped_weapon, equipped_armor,
                              dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset, max_inventory)

        await message.channel.send(f"✅ Successfully upgraded your inventory to {new_slots} slots! Next upgrade will cost {next_upgrade_cost} coins.")
