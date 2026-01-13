"""
Inventory-related database queries
"""
from database.connection import get_connection, execute_query

def get_user_inventory(user_id):
    """Get user inventory items"""
    query = 'SELECT item_name, quantity FROM inventory WHERE user_id = %s AND quantity > 0'
    return execute_query(query, (user_id,), fetch_all=True)

def get_inventory_count(user_id):
    """Get count of unique items in user inventory"""
    query = 'SELECT COUNT(*) FROM inventory WHERE user_id = %s AND quantity > 0'
    result = execute_query(query, (user_id,), fetch_one=True)
    return result[0] if result else 0

def update_inventory(user_id, item_name_with_underscore, quantity_change):
    """Update inventory item quantity"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT quantity FROM inventory WHERE user_id = %s AND item_name = %s', (user_id, item_name_with_underscore))
        existing = cursor.fetchone()
        
        if existing:
            new_quantity = existing[0] + quantity_change
            if new_quantity > 0:
                cursor.execute('UPDATE inventory SET quantity = %s WHERE user_id = %s AND item_name = %s', (new_quantity, user_id, item_name_with_underscore))
            else:
                cursor.execute('DELETE FROM inventory WHERE user_id = %s AND item_name = %s', (user_id, item_name_with_underscore))
        elif quantity_change > 0:
            cursor.execute('INSERT INTO inventory (user_id, item_name, quantity) VALUES (%s, %s, %s)', (user_id, item_name_with_underscore, quantity_change))
        
        conn.commit()
    finally:
        cursor.close()
        conn.close()