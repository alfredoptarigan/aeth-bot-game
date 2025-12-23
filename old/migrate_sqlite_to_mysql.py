"""
Script untuk migrasi data dari SQLite ke MySQL
Jalankan setelah MySQL database dan tabel sudah dibuat
"""
import sqlite3
import os
from dotenv import load_dotenv
import mysql.connector

load_dotenv()

SQLITE_DB = 'aethbotgame.db'

def get_mysql_connection():
    return mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        port=int(os.getenv('MYSQL_PORT', 3306)),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
        database=os.getenv('MYSQL_DATABASE', 'aethbotgame')
    )

def migrate_users():
    print("📦 Migrasi tabel users...")
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_cursor = sqlite_conn.cursor()
    
    mysql_conn = get_mysql_connection()
    mysql_cursor = mysql_conn.cursor()
    
    sqlite_cursor.execute('''
        SELECT user_id, exp, level, Money, last_daily_claim, 
               ATK, SPD, DEF, DEX, CRIT, MDMG, HP, MP,
               inventory_slots, equipped_weapon, equipped_armor,
               dice_rolls_today, last_dice_reset, last_fight_time,
               hunt_count_today, last_hunt_reset
        FROM users
    ''')
    
    users = sqlite_cursor.fetchall()
    
    for user in users:
        try:
            mysql_cursor.execute('''
                INSERT INTO users (user_id, exp, level, Money, last_daily_claim,
                    ATK, SPD, DEF, DEX, CRIT, MDMG, HP, MP,
                    inventory_slots, equipped_weapon, equipped_armor,
                    dice_rolls_today, last_dice_reset, last_fight_time,
                    hunt_count_today, last_hunt_reset)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    exp=VALUES(exp), level=VALUES(level), Money=VALUES(Money)
            ''', user)
        except Exception as e:
            print(f"  ⚠️ Error user {user[0]}: {e}")
    
    mysql_conn.commit()
    print(f"  ✅ {len(users)} users berhasil dimigrasi")
    
    sqlite_conn.close()
    mysql_conn.close()

def migrate_inventory():
    print("📦 Migrasi tabel inventory...")
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_cursor = sqlite_conn.cursor()
    
    mysql_conn = get_mysql_connection()
    mysql_cursor = mysql_conn.cursor()
    
    sqlite_cursor.execute('SELECT user_id, item_name, quantity FROM inventory')
    items = sqlite_cursor.fetchall()
    
    for item in items:
        try:
            mysql_cursor.execute('''
                INSERT INTO inventory (user_id, item_name, quantity)
                VALUES (%s, %s, %s)
            ''', item)
        except Exception as e:
            print(f"  ⚠️ Error inventory: {e}")
    
    mysql_conn.commit()
    print(f"  ✅ {len(items)} inventory items berhasil dimigrasi")
    
    sqlite_conn.close()
    mysql_conn.close()


def migrate_items():
    print("📦 Migrasi tabel items...")
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_cursor = sqlite_conn.cursor()
    
    mysql_conn = get_mysql_connection()
    mysql_cursor = mysql_conn.cursor()
    
    sqlite_cursor.execute('''
        SELECT item_id, name, type, price, bonus_atk, bonus_def, bonus_spd,
               bonus_dex, bonus_crit, bonus_mdmg, bonus_hp, bonus_mp
        FROM items
    ''')
    items = sqlite_cursor.fetchall()
    
    for item in items:
        try:
            mysql_cursor.execute('''
                INSERT INTO items (item_id, name, type, price, bonus_atk, bonus_def, bonus_spd,
                    bonus_dex, bonus_crit, bonus_mdmg, bonus_hp, bonus_mp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    name=VALUES(name), type=VALUES(type), price=VALUES(price)
            ''', item)
        except Exception as e:
            print(f"  ⚠️ Error item: {e}")
    
    mysql_conn.commit()
    print(f"  ✅ {len(items)} items berhasil dimigrasi")
    
    sqlite_conn.close()
    mysql_conn.close()

def migrate_roles():
    print("📦 Migrasi tabel roles...")
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_cursor = sqlite_conn.cursor()
    
    mysql_conn = get_mysql_connection()
    mysql_cursor = mysql_conn.cursor()
    
    sqlite_cursor.execute('SELECT role_id, name, price FROM roles')
    roles = sqlite_cursor.fetchall()
    
    for role in roles:
        try:
            mysql_cursor.execute('''
                INSERT INTO roles (role_id, name, price)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE name=VALUES(name), price=VALUES(price)
            ''', role)
        except Exception as e:
            print(f"  ⚠️ Error role: {e}")
    
    mysql_conn.commit()
    print(f"  ✅ {len(roles)} roles berhasil dimigrasi")
    
    sqlite_conn.close()
    mysql_conn.close()

def migrate_shift_config():
    print("📦 Migrasi tabel shift_config...")
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_cursor = sqlite_conn.cursor()
    
    mysql_conn = get_mysql_connection()
    mysql_cursor = mysql_conn.cursor()
    
    sqlite_cursor.execute('''
        SELECT guild_id, duration_minutes, required_role_ids, reward_money, 
               reward_exp, shift_detail, max_participants
        FROM shift_config
    ''')
    configs = sqlite_cursor.fetchall()
    
    for config in configs:
        try:
            mysql_cursor.execute('''
                INSERT INTO shift_config (guild_id, duration_minutes, required_role_ids, 
                    reward_money, reward_exp, shift_detail, max_participants)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    duration_minutes=VALUES(duration_minutes)
            ''', config)
        except Exception as e:
            print(f"  ⚠️ Error shift_config: {e}")
    
    mysql_conn.commit()
    print(f"  ✅ {len(configs)} shift configs berhasil dimigrasi")
    
    sqlite_conn.close()
    mysql_conn.close()

def migrate_active_shifts():
    print("📦 Migrasi tabel active_shifts...")
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_cursor = sqlite_conn.cursor()
    
    mysql_conn = get_mysql_connection()
    mysql_cursor = mysql_conn.cursor()
    
    sqlite_cursor.execute('''
        SELECT user_id, start_time, end_time, reward_money, reward_exp, shift_detail
        FROM active_shifts
    ''')
    shifts = sqlite_cursor.fetchall()
    
    for shift in shifts:
        try:
            mysql_cursor.execute('''
                INSERT INTO active_shifts (user_id, start_time, end_time, 
                    reward_money, reward_exp, shift_detail)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    start_time=VALUES(start_time)
            ''', shift)
        except Exception as e:
            print(f"  ⚠️ Error active_shift: {e}")
    
    mysql_conn.commit()
    print(f"  ✅ {len(shifts)} active shifts berhasil dimigrasi")
    
    sqlite_conn.close()
    mysql_conn.close()

def run_migration():
    print("=" * 50)
    print("🚀 MIGRASI DATA SQLITE KE MYSQL")
    print("=" * 50)
    
    if not os.path.exists(SQLITE_DB):
        print(f"❌ File {SQLITE_DB} tidak ditemukan!")
        return
    
    try:
        # Test MySQL connection
        conn = get_mysql_connection()
        conn.close()
        print("✅ Koneksi MySQL berhasil!")
    except Exception as e:
        print(f"❌ Gagal koneksi ke MySQL: {e}")
        return
    
    migrate_users()
    migrate_inventory()
    migrate_items()
    migrate_roles()
    migrate_shift_config()
    migrate_active_shifts()
    
    print("=" * 50)
    print("✅ MIGRASI SELESAI!")
    print("=" * 50)

if __name__ == "__main__":
    run_migration()
