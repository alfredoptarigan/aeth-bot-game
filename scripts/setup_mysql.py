"""
Script untuk membuat database dan tabel di MySQL
Jalankan ini PERTAMA sebelum migrasi data
"""
import os
import sys

from dotenv import load_dotenv
import mysql.connector

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def create_database():
    """Buat database jika belum ada"""
    print("🔧 Membuat database...")
    
    conn = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        port=int(os.getenv('MYSQL_PORT', 3306)),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', '')
    )
    cursor = conn.cursor()
    
    db_name = os.getenv('MYSQL_DATABASE', 'aethbotgame')
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    
    print(f"✅ Database '{db_name}' berhasil dibuat/sudah ada")
    
    conn.close()

def create_tables():
    """Buat semua tabel"""
    print("🔧 Membuat tabel...")
    
    conn = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        port=int(os.getenv('MYSQL_PORT', 3306)),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
        database=os.getenv('MYSQL_DATABASE', 'aethbotgame')
    )
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            exp INT DEFAULT 0,
            level INT DEFAULT 1,
            Money INT DEFAULT 0,
            last_daily_claim VARCHAR(20) DEFAULT '2000-01-01',
            ATK INT DEFAULT 5,
            SPD INT DEFAULT 5,
            DEF INT DEFAULT 5,
            DEX INT DEFAULT 5,
            CRIT INT DEFAULT 5,
            MDMG INT DEFAULT 5,
            HP INT DEFAULT 100,
            MP INT DEFAULT 50,
            inventory_slots INT DEFAULT 10,
            equipped_weapon VARCHAR(100) DEFAULT NULL,
            equipped_armor VARCHAR(100) DEFAULT NULL,
            dice_rolls_today INT DEFAULT 0,
            last_dice_reset VARCHAR(20) DEFAULT '2000-01-01',
            last_fight_time DOUBLE DEFAULT 0.0,
            hunt_count_today INT DEFAULT 0,
            last_hunt_reset VARCHAR(20) DEFAULT '2000-01-01'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')
    print("  ✅ Tabel 'users' dibuat")
    
    # Inventory table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            item_name VARCHAR(100) NOT NULL,
            quantity INT DEFAULT 0,
            INDEX idx_user_id (user_id),
            UNIQUE KEY unique_user_item (user_id, item_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')
    print("  ✅ Tabel 'inventory' dibuat")
    
    # Items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            item_id INT PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            type VARCHAR(50) NOT NULL,
            price INT DEFAULT 0,
            bonus_atk INT DEFAULT 0,
            bonus_def INT DEFAULT 0,
            bonus_spd INT DEFAULT 0,
            bonus_dex INT DEFAULT 0,
            bonus_crit INT DEFAULT 0,
            bonus_mdmg INT DEFAULT 0,
            bonus_hp INT DEFAULT 0,
            bonus_mp INT DEFAULT 0
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')
    print("  ✅ Tabel 'items' dibuat")
    
    # Roles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            role_id BIGINT PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            price INT DEFAULT 0
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')
    print("  ✅ Tabel 'roles' dibuat")
    
    # Shift config table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shift_config (
            guild_id BIGINT PRIMARY KEY,
            duration_minutes INT DEFAULT 60,
            required_role_ids TEXT,
            reward_money INT DEFAULT 1000,
            reward_exp INT DEFAULT 100,
            shift_detail TEXT,
            max_participants INT DEFAULT 0
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')
    print("  ✅ Tabel 'shift_config' dibuat")
    
    # Active shifts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_shifts (
            user_id BIGINT PRIMARY KEY,
            start_time DOUBLE NOT NULL,
            end_time DOUBLE NOT NULL,
            reward_money INT NOT NULL,
            reward_exp INT NOT NULL,
            shift_detail TEXT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')
    print("  ✅ Tabel 'active_shifts' dibuat")
    
    conn.commit()
    conn.close()

def insert_default_items():
    """Insert default items"""
    print("🔧 Menambahkan default items...")
    
    conn = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        port=int(os.getenv('MYSQL_PORT', 3306)),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
        database=os.getenv('MYSQL_DATABASE', 'aethbotgame')
    )
    cursor = conn.cursor()
    
    default_items = [
        (1, 'Iron_Sword', 'weapon', 500, 5, 0, 0, 0, 0, 0, 0, 0),
        (2, 'Leather_Armor', 'armor', 300, 0, 3, 0, 0, 0, 0, 20, 0),
        (3, 'Great_Axe', 'weapon', 1500, 15, 0, -2, 0, 0, 0, 0, 0),
        (4, 'Dagger_of_Thief', 'weapon', 800, 2, 0, 3, 5, 0, 0, 0, 0),
    ]
    
    for item in default_items:
        cursor.execute('''
            INSERT INTO items (item_id, name, type, price, bonus_atk, bonus_def, bonus_spd, 
                bonus_dex, bonus_crit, bonus_mdmg, bonus_hp, bonus_mp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE name=VALUES(name)
        ''', item)
    
    # Default role
    cursor.execute('''
        INSERT INTO roles (role_id, name, price)
        VALUES (1448172828192145520, 'Knight', 1000)
        ON DUPLICATE KEY UPDATE name=VALUES(name)
    ''')
    
    conn.commit()
    print("  ✅ Default items dan roles ditambahkan")
    conn.close()

def run_setup():
    print("=" * 50)
    print("🚀 SETUP DATABASE MYSQL")
    print("=" * 50)
    
    create_database()
    create_tables()
    insert_default_items()
    
    print("=" * 50)
    print("✅ SETUP SELESAI!")
    print("=" * 50)
    print("\nLangkah selanjutnya:")
    print("1. Jalankan: python3 migrate_sqlite_to_mysql.py")
    print("2. Update maingame.py untuk menggunakan MySQL")

if __name__ == "__main__":
    run_setup()
