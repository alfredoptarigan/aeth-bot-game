"""
Expansion inventory database queries
"""

from database.connection import execute_query

def get_inventory_upgrade_cost(user_id):
    """Get the cost to upgrade inventory for a user"""
    query = """
    SELECT upgrade_cost FROM inventory_upgrades
    WHERE user_id = %s
    ORDER BY upgrade_level DESC
    LIMIT 1
    """
    result = execute_query(query, (user_id,))
    if result:
        return result[0][0]
    return None

def set_inventory_upgrade_cost(user_id, new_cost):
    """Set a new cost for inventory upgrade for a user"""
    query = """
    INSERT INTO inventory_upgrades (user_id, upgrade_cost)
    VALUES (%s, %s)
    """
    execute_query(query, (user_id, new_cost))

def get_next_inventory_upgrade_cost(current_level):
    """Calculate the next inventory upgrade cost based on current level"""
    base_cost = 500  
    cost_multiplier = 1.5 
    next_cost = int(base_cost * (cost_multiplier ** current_level))
    return next_cost

def upgrade_inventory(user_id, new_cost):
    """Upgrade the inventory for a user and set new cost"""
    set_inventory_upgrade_cost(user_id, new_cost)
    return True