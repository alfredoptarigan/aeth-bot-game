"""
User-related database queries
"""
from database.connection import execute_query
from config.constants import DEFAULT_USER_DATA

def get_user_data(user_id):
    """Get user data from database"""
    query = '''SELECT exp, level, Money, last_daily_claim, ATK, SPD, DEF, DEX, CRIT, MDMG, HP, MP,
               inventory_slots, equipped_weapon, equipped_armor, dice_rolls_today, last_dice_reset,
               last_fight_time, hunt_count_today, last_hunt_reset, max_inventory
               FROM users WHERE user_id = %s'''
    data = execute_query(query, (user_id,), fetch_one=True)

    if data is None:
        return DEFAULT_USER_DATA
    return data

def get_user_role(user_id):
    query = 'SELECT roles.name FROM user_roles JOIN roles ON user_roles.role_id = roles.role_id WHERE user_roles.user_id = %s'
    data = execute_query(query, (user_id,), fetch_one=True)
    if not data:
        return 'Player'
    return data[0]

def reset_last_hunt_reset(user_id, date_str='2000-01-01'):
    """Reset last_hunt_reset for a specific user to `date_str` (default '2000-01-01').

    Returns True on success.
    """
    query = 'UPDATE users SET last_hunt_reset = %s WHERE user_id = %s'
    execute_query(query, (date_str, user_id))
    return True

def reset_all_last_hunt_reset(date_str='2000-01-01'):
    """Reset last_hunt_reset for all users to `date_str` (default '2000-01-01').

    Returns number of affected rows if available (may be connector-specific) or True.
    """
    query = 'UPDATE users SET last_hunt_reset = %s'
    execute_query(query, (date_str,))
    return True

def update_full_user_data(user_id, exp, level, Money, last_daily_claim, ATK, SPD, DEF, DEX, CRIT, MDMG, HP, MP, inventory_slots, equipped_weapon=None, equipped_armor=None, dice_rolls_today=0, last_dice_reset='2000-01-01', last_fight_time=0.0, hunt_count_today=0, last_hunt_reset='2000-01-01', max_inventory=50):
    """Update complete user data"""
    query = '''INSERT INTO users
               (user_id, exp, level, Money, last_daily_claim, ATK, SPD, DEF, DEX, CRIT, MDMG, HP, MP,
                inventory_slots, equipped_weapon, equipped_armor, dice_rolls_today, last_dice_reset,
                last_fight_time, hunt_count_today, last_hunt_reset, max_inventory)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON DUPLICATE KEY UPDATE
               exp=%s, level=%s, Money=%s, last_daily_claim=%s, ATK=%s, SPD=%s, DEF=%s, DEX=%s,
               CRIT=%s, MDMG=%s, HP=%s, MP=%s, inventory_slots=%s, equipped_weapon=%s, equipped_armor=%s,
               dice_rolls_today=%s, last_dice_reset=%s, last_fight_time=%s, hunt_count_today=%s, last_hunt_reset=%s, max_inventory=%s'''

    params = (user_id, exp, level, Money, last_daily_claim, ATK, SPD, DEF, DEX, CRIT, MDMG, HP, MP,
              inventory_slots, equipped_weapon, equipped_armor, dice_rolls_today, last_dice_reset,
              last_fight_time, hunt_count_today, last_hunt_reset, max_inventory,
              exp, level, Money, last_daily_claim, ATK, SPD, DEF, DEX, CRIT, MDMG, HP, MP,
              inventory_slots, equipped_weapon, equipped_armor, dice_rolls_today, last_dice_reset,
              last_fight_time, hunt_count_today, last_hunt_reset, max_inventory)

    execute_query(query, params)

def get_leaderboard_data():
    """Get leaderboard data"""
    query = 'SELECT user_id, level, exp, Money FROM users ORDER BY level DESC, exp DESC, Money DESC LIMIT 10'
    return execute_query(query, fetch_all=True)

def update_user_money(user_id, amount_change):
    """Update user money by amount"""
    user_data = get_user_data(user_id)
    (exp, level, current_money, last_daily_str, atk, spd, def_stat, dex, crit, mdmg, hp, mp,
     inventory_slots, equipped_weapon, equipped_armor, dice_rolls_today, last_dice_reset,
     last_fight_time, hunt_count, hunt_reset, max_inventory) = user_data

    new_money = max(0, current_money + amount_change)
    update_full_user_data(user_id, exp, level, new_money, last_daily_str, atk, spd, def_stat,
                          dex, crit, mdmg, hp, mp, inventory_slots, equipped_weapon, equipped_armor,
                          dice_rolls_today, last_dice_reset, last_fight_time, hunt_count, hunt_reset, max_inventory)
    return new_money