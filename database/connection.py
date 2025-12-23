"""
MySQL Database Connection Module
Pengganti sqlite3 untuk maingame.py
"""
import os
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv

load_dotenv()

# Connection pool untuk performa lebih baik
db_config = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'aethbotgame'),
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

# Create connection pool
try:
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="aethbot_pool",
        pool_size=5,
        pool_reset_session=True,
        **db_config
    )
except Exception as e:
    print(f"⚠️ Warning: Could not create connection pool: {e}")
    connection_pool = None

def get_connection():
    """Get a connection from pool or create new one"""
    if connection_pool:
        return connection_pool.get_connection()
    return mysql.connector.connect(**db_config)

def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    """Execute a query and return results"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(query, params or ())
        
        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        else:
            conn.commit()
            result = cursor.lastrowid
        
        return result
    finally:
        cursor.close()
        conn.close()

def execute_many(query, params_list):
    """Execute many queries"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.executemany(query, params_list)
        conn.commit()
    finally:
        cursor.close()
        conn.close()
