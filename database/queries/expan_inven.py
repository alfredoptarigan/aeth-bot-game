"""
Expansion inventory database queries
"""

from database.connection import execute_query
from config.constants import INVENTORY_BASE_UPGRADE_COST, INVENTORY_COST_MULTIPLIER, INVENTORY_SLOTS_INCREASE

def calculate_inventory_upgrade_cost(current_slots):
    """Calculate the cost to upgrade inventory based on current slots"""
    upgrade_level = (current_slots - 10) // INVENTORY_SLOTS_INCREASE
    if upgrade_level < 0:
        upgrade_level = 0
    next_cost = int(INVENTORY_BASE_UPGRADE_COST * (INVENTORY_COST_MULTIPLIER ** upgrade_level))
    return next_cost

def get_next_inventory_slots(current_slots):
    """Calculate the next inventory slots after upgrade"""
    return current_slots + INVENTORY_SLOTS_INCREASE

def upgrade_inventory(user_id, current_slots, current_max_inventory):
    """Upgrade the inventory slots for a user and return new slots and cost"""
    new_slots = current_slots + INVENTORY_SLOTS_INCREASE

    if new_slots > current_max_inventory:
        return None, current_max_inventory

    upgrade_cost = calculate_inventory_upgrade_cost(current_slots)
    return new_slots, upgrade_cost
