"""
Role and User Role Query Functions
"""
from database.connection import execute_query, execute_many
from datetime import datetime

def get_all_roles():
    """Get all available roles"""
    query = """
    SELECT role_id, name, price, description, color, created_at, is_buy 
    FROM roles 
    ORDER BY price ASC
    """
    return execute_query(query, fetch_all=True)

def get_role_by_id(role_id):
    """Get role by ID"""
    query = "SELECT role_id, name, price, description, color, is_buy FROM roles WHERE role_id = %s"
    return execute_query(query, (role_id,), fetch_one=True)

def get_role_by_name(role_name):
    """Get role by name"""
    query = "SELECT role_id, name, price, description, color, is_buy FROM roles WHERE name = %s"
    return execute_query(query, (role_name,), fetch_one=True)

def get_buyable_roles():
    """Get only buyable roles (is_buy = 1)"""
    query = """
    SELECT role_id, name, price, description, color, created_at, is_buy 
    FROM roles 
    WHERE is_buy = 1
    ORDER BY price ASC
    """
    return execute_query(query, fetch_all=True)

def create_role(name, price, description=None, color='#000000', is_buy=1):
    """Create a new role"""
    query = """
    INSERT INTO roles (name, price, description, color, created_at, is_buy) 
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    return execute_query(query, (name, price, description, color, datetime.utcnow(), is_buy))

def update_role(role_id, name=None, price=None, description=None, color=None, is_buy=None):
    """Update role information"""
    updates = []
    params = []
    
    if name is not None:
        updates.append("name = %s")
        params.append(name)
    if price is not None:
        updates.append("price = %s")
        params.append(price)
    if description is not None:
        updates.append("description = %s")
        params.append(description)
    if color is not None:
        updates.append("color = %s")
        params.append(color)
    if is_buy is not None:
        updates.append("is_buy = %s")
        params.append(is_buy)
    
    if not updates:
        return False
    
    params.append(role_id)
    query = f"UPDATE roles SET {', '.join(updates)} WHERE role_id = %s"
    execute_query(query, params)
    return True

def delete_role(role_id):
    """Delete a role (also removes all user_roles associations)"""
    # First delete user_roles associations
    execute_query("DELETE FROM user_roles WHERE role_id = %s", (role_id,))
    # Then delete the role
    execute_query("DELETE FROM roles WHERE role_id = %s", (role_id,))

# User Role Functions
def get_user_roles(user_id, active_only=True):
    """Get all roles for a user"""
    if active_only:
        query = """
        SELECT ur.id, ur.user_id, ur.role_id, ur.purchased_at, ur.is_active,
               r.name, r.price, r.description, r.color
        FROM user_roles ur
        JOIN roles r ON ur.role_id = r.role_id
        WHERE ur.user_id = %s AND ur.is_active = 1
        ORDER BY ur.purchased_at DESC
        """
    else:
        query = """
        SELECT ur.id, ur.user_id, ur.role_id, ur.purchased_at, ur.is_active,
               r.name, r.price, r.description, r.color
        FROM user_roles ur
        JOIN roles r ON ur.role_id = r.role_id
        WHERE ur.user_id = %s
        ORDER BY ur.purchased_at DESC
        """
    return execute_query(query, (user_id,), fetch_all=True)

def user_has_role(user_id, role_id):
    """Check if user has a specific role"""
    query = """
    SELECT COUNT(*) FROM user_roles 
    WHERE user_id = %s AND role_id = %s AND is_active = 1
    """
    result = execute_query(query, (user_id, role_id), fetch_one=True)
    return result[0] > 0 if result else False

def user_has_role_by_name(user_id, role_name):
    """Check if user has a specific role by name"""
    query = """
    SELECT COUNT(*) FROM user_roles ur
    JOIN roles r ON ur.role_id = r.role_id
    WHERE ur.user_id = %s AND r.name = %s AND ur.is_active = 1
    """
    result = execute_query(query, (user_id, role_name), fetch_one=True)
    return result[0] > 0 if result else False

def purchase_role(user_id, role_id):
    """Purchase a role for user"""
    # Check if user already has this role
    if user_has_role(user_id, role_id):
        return False, "User already has this role"
    
    query = """
    INSERT INTO user_roles (user_id, role_id, purchased_at, is_active) 
    VALUES (%s, %s, %s, 1)
    """
    execute_query(query, (user_id, role_id, datetime.utcnow()))
    return True, "Role purchased successfully"

def activate_user_role(user_id, role_id):
    """Activate a user's role"""
    query = """
    UPDATE user_roles 
    SET is_active = 1 
    WHERE user_id = %s AND role_id = %s
    """
    execute_query(query, (user_id, role_id))

def deactivate_user_role(user_id, role_id):
    """Deactivate a user's role"""
    query = """
    UPDATE user_roles 
    SET is_active = 0 
    WHERE user_id = %s AND role_id = %s
    """
    execute_query(query, (user_id, role_id))

def remove_user_role(user_id, role_id):
    """Completely remove a role from user"""
    query = "DELETE FROM user_roles WHERE user_id = %s AND role_id = %s"
    execute_query(query, (user_id, role_id))

def get_role_owners(role_id, active_only=True):
    """Get all users who have a specific role"""
    if active_only:
        query = """
        SELECT ur.user_id, ur.purchased_at, ur.is_active
        FROM user_roles ur
        WHERE ur.role_id = %s AND ur.is_active = 1
        ORDER BY ur.purchased_at ASC
        """
    else:
        query = """
        SELECT ur.user_id, ur.purchased_at, ur.is_active
        FROM user_roles ur
        WHERE ur.role_id = %s
        ORDER BY ur.purchased_at ASC
        """
    return execute_query(query, (role_id,), fetch_all=True)

def count_role_owners(role_id, active_only=True):
    """Count how many users have a specific role"""
    if active_only:
        query = "SELECT COUNT(*) FROM user_roles WHERE role_id = %s AND is_active = 1"
    else:
        query = "SELECT COUNT(*) FROM user_roles WHERE role_id = %s"
    
    result = execute_query(query, (role_id,), fetch_one=True)
    return result[0] if result else 0

def get_buyable_roles():
    """Get only buyable roles (is_buy = 1)"""
    query = """
    SELECT role_id, name, price, description, color, created_at
    FROM roles
    WHERE is_buy = 1
    ORDER BY price ASC
    """
    return execute_query(query, fetch_all=True)