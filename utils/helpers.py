"""
Helper functions for common operations
"""
import datetime
from database.queries.user_queries import get_user_data, update_full_user_data

def get_dice_status(user_id):
    """Get dice roll status for user"""
    user_data = get_user_data(user_id)
    (current_exp, current_level, current_currency, last_daily_str, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, current_rolls, last_reset_str, last_fight_time, hunt_count, hunt_reset) = user_data
    
    today = datetime.date.today().strftime('%Y-%m-%d')
    if last_reset_str != today:
        current_rolls = 0
        last_reset_str = today
        update_full_user_data(user_id, current_exp, current_level, current_currency, last_daily_str, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, current_rolls, last_reset_str, last_fight_time, hunt_count, hunt_reset)
    return current_rolls, last_reset_str, user_data

def get_hunt_status(user_id):
    """Get hunt status for user"""
    user_data = get_user_data(user_id)
    hunt_count = user_data[18]
    last_hunt_reset = user_data[19]
    
    today = datetime.date.today().strftime('%Y-%m-%d')
    if last_hunt_reset != today:
        hunt_count = 0
        last_hunt_reset = today
    return hunt_count, last_hunt_reset, user_data

def get_display_width(text):
    """Calculate display width for text (handles unicode characters)"""
    width = 0
    for char in text:
        if ord(char) > 127: 
            width += 2
        else:
            width += 1
    return width

def format_item_name(item_name_db):
    """Convert database item name to display format"""
    return item_name_db.replace('_', ' ') if item_name_db else 'None'