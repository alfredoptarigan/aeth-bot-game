"""
Shop-related database queries
"""
from database.connection import execute_query

def get_shop_items(item_type):
    """Get shop items by type"""
    query = 'SELECT name, price, bonus_atk, bonus_def, bonus_spd, bonus_dex, bonus_crit, bonus_mdmg, bonus_hp, bonus_mp FROM items WHERE type = %s ORDER BY price ASC'
    return execute_query(query, (item_type,), fetch_all=True)

def get_item_details(item_name_with_underscore):
    """Get item details by name"""
    query = 'SELECT item_id, name, type, price, bonus_atk, bonus_def, bonus_spd, bonus_dex, bonus_crit, bonus_mdmg, bonus_hp, bonus_mp FROM items WHERE LOWER(name) = LOWER(%s)'
    return execute_query(query, (item_name_with_underscore,), fetch_one=True)

def get_shop_roles():
    """Get available roles for purchase"""
    query = 'SELECT role_id, name, price FROM roles ORDER BY price ASC'
    return execute_query(query, fetch_all=True)

def get_role_details(role_name):
    """Get role details by name"""
    query = 'SELECT role_id, name, price FROM roles WHERE LOWER(name) = LOWER(%s)'
    return execute_query(query, (role_name,), fetch_one=True)