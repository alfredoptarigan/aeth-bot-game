"""
Shift-related database queries
"""
from database.connection import get_connection, execute_query

def get_shift_config(guild_id):
    """Get shift configuration for guild"""
    query = 'SELECT duration_minutes, required_role_ids, reward_money, reward_exp, shift_detail, max_participants FROM shift_config WHERE guild_id = %s'
    data = execute_query(query, (guild_id,), fetch_one=True)
    
    if data is None:
        return 60, '', 1000, 100, 'Shift Standar Harian', 0
    return int(data[0]), data[1] or '', int(data[2]), int(data[3]), data[4] or 'Shift Standar Harian', int(data[5])

def set_shift_config(guild_id, duration, required_roles_str, money, exp, detail, max_p):
    """Set shift configuration for guild"""
    query = '''INSERT INTO shift_config (guild_id, duration_minutes, required_role_ids, reward_money, reward_exp, shift_detail, max_participants) 
               VALUES (%s, %s, %s, %s, %s, %s, %s)
               ON DUPLICATE KEY UPDATE
               duration_minutes=%s, required_role_ids=%s, reward_money=%s, reward_exp=%s, shift_detail=%s, max_participants=%s'''
    execute_query(query, (guild_id, duration, required_roles_str, money, exp, detail, max_p,
                          duration, required_roles_str, money, exp, detail, max_p))

def get_active_shift(user_id):
    """Get active shift for user"""
    query = 'SELECT start_time, end_time, reward_money, reward_exp, shift_detail FROM active_shifts WHERE user_id = %s'
    return execute_query(query, (user_id,), fetch_one=True)

def start_new_shift(user_id, start_time, end_time, money, exp, detail):
    """Start new shift for user"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM active_shifts WHERE user_id = %s', (user_id,))
        cursor.execute('INSERT INTO active_shifts (user_id, start_time, end_time, reward_money, reward_exp, shift_detail) VALUES (%s, %s, %s, %s, %s, %s)',
                      (user_id, start_time, end_time, money, exp, detail))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def end_active_shift(user_id):
    """End active shift for user"""
    execute_query('DELETE FROM active_shifts WHERE user_id = %s', (user_id,))

def count_active_shifts(guild_id):
    """Count active shifts in guild"""
    result = execute_query('SELECT COUNT(*) FROM active_shifts', fetch_one=True)
    return result[0] if result else 0