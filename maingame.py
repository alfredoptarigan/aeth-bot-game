import discord
import random
import sqlite3
import datetime
import time
import asyncio
import logging
import os
import json
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

prefix = 'ag!'
DB_NAME = 'aethbotgame.db'
EXP_COOLDOWN = 60
EXP_PER_MESSAGE_MIN = 10
EXP_PER_MESSAGE_MAX = 50

MAX_DAILY_DICE = 5
DICE_COSTS = [0, 200, 400, 600, 800] 
DICE_BASE_REWARD = 300 

FIGHT_COOLDOWN = 10 * 60
FIGHT_COST_MIN = 500
FIGHT_COST_MAX = 500

# Hunt Monster Config
MAX_DAILY_HUNT = 5
HUNT_GOLD_MULTIPLIER_MIN = 5
HUNT_GOLD_MULTIPLIER_MAX = 15

FIGHT_BONUS_EXP_MIN = 50
FIGHT_BONUS_EXP_MAX = 200
FIGHT_BONUS_MONEY_MIN = 500
FIGHT_BONUS_MONEY_MAX = 2500

STAT_UPGRADE_COST = 100

STAT_TIER_1_MAX = 10
STAT_TIER_2_MAX = 20
STAT_TIER_3_MAX = 50
STAT_TIER_4_MAX = 1000

STAT_TIER_1_COST = 100
STAT_TIER_2_COST = 125
STAT_TIER_3_COST = 175
STAT_TIER_4_COST = 250

user_exp_cooldown = {}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = discord.Client(intents=intents)

def create_db_dump():
    backup_dir = 'db_backups'
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = os.path.join(backup_dir, f'backup_{timestamp}.sql')

    try:
        conn = sqlite3.connect(DB_NAME)

        with open(backup_filename, 'w') as f:
            for line in conn.iterdump():
                f.write(f'{line}\n')
                
        conn.close()
        print(f"✅ Backup database berhasil disimpan ke: {backup_filename}")
        return backup_filename
    except Exception as e:
        print(f"❌ Gagal melakukan backup: {e}")
        return None

def db_setup():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                exp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                Money INTEGER DEFAULT 0,
                last_daily_claim TEXT DEFAULT '2000-01-01', 
                ATK INTEGER DEFAULT 5,
                SPD INTEGER DEFAULT 5,
                DEF INTEGER DEFAULT 5,
                DEX INTEGER DEFAULT 5,
                CRIT INTEGER DEFAULT 5,
                MDMG INTEGER DEFAULT 5,
                HP INTEGER DEFAULT 100,
                MP INTEGER DEFAULT 50,
                inventory_slots INTEGER DEFAULT 10,
                equipped_weapon TEXT DEFAULT NULL,
                equipped_armor TEXT DEFAULT NULL,
                dice_rolls_today INTEGER DEFAULT 0, 
                last_dice_reset TEXT DEFAULT '2000-01-01',
                last_fight_time REAL DEFAULT 0.0,
                hunt_count_today INTEGER DEFAULT 0,
                last_hunt_reset TEXT DEFAULT '2000-01-01'
            )''')

    new_user_cols = {'DEX': 5, 'CRIT': 5, 'MDMG': 5, 'HP': 100, 'MP': 50, 'hunt_count_today': 0}
    for col, default in new_user_cols.items():
        try:
            c.execute(f'ALTER TABLE users ADD COLUMN {col} INTEGER DEFAULT {default}')
        except sqlite3.OperationalError:
            pass

    # Add TEXT columns separately
    try:
        c.execute("ALTER TABLE users ADD COLUMN last_hunt_reset TEXT DEFAULT '2000-01-01'")
    except sqlite3.OperationalError:
        pass

    c.execute('''CREATE TABLE IF NOT EXISTS inventory (
                user_id INTEGER NOT NULL,
                item_name TEXT NOT NULL, 
                quantity INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, item_name)
            )''')

    c.execute('''CREATE TABLE IF NOT EXISTS items (
                item_id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                price INTEGER DEFAULT 0,
                bonus_atk INTEGER DEFAULT 0,
                bonus_def INTEGER DEFAULT 0,
                bonus_spd INTEGER DEFAULT 0,
                bonus_dex INTEGER DEFAULT 0,
                bonus_crit INTEGER DEFAULT 0,
                bonus_mdmg INTEGER DEFAULT 0,
                bonus_hp INTEGER DEFAULT 0,
                bonus_mp INTEGER DEFAULT 0
            )''')

    new_item_cols = ['bonus_dex', 'bonus_crit', 'bonus_mdmg', 'bonus_hp', 'bonus_mp']
    for col in new_item_cols:
        try:
            c.execute(f'ALTER TABLE items ADD COLUMN {col} INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass

    c.execute('''CREATE TABLE IF NOT EXISTS roles (
                role_id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                price INTEGER DEFAULT 0
            )''')

    c.execute('''CREATE TABLE IF NOT EXISTS shift_config (
                guild_id INTEGER PRIMARY KEY,
                duration_minutes INTEGER DEFAULT 60,
                required_role_ids TEXT DEFAULT '',
                reward_money INTEGER DEFAULT 1000,
                reward_exp INTEGER DEFAULT 100,
                shift_detail TEXT DEFAULT 'Shift Standar Harian',
                max_participants INTEGER DEFAULT 0
            )''')
    
    new_config_cols = {'shift_detail': 'Shift Standar Harian', 'max_participants': 0}
    for col, default in new_config_cols.items():
        try:
            c.execute(f'ALTER TABLE shift_config ADD COLUMN {col} TEXT DEFAULT "{default}"')
        except sqlite3.OperationalError:
            pass

    c.execute('''CREATE TABLE IF NOT EXISTS active_shifts (
                user_id INTEGER PRIMARY KEY,
                start_time REAL NOT NULL,
                end_time REAL NOT NULL,
                reward_money INTEGER NOT NULL,
                reward_exp INTEGER NOT NULL
            )''')
    
    try:
        c.execute('ALTER TABLE active_shifts ADD COLUMN shift_detail TEXT DEFAULT "Shift Standar"')
        print("✅ Kolom 'shift_detail' berhasil ditambahkan ke active_shifts.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            pass
        else:
            pass

    c.execute("INSERT OR REPLACE INTO items (item_id, name, type, price, bonus_atk, bonus_def, bonus_spd, bonus_dex, bonus_crit, bonus_mdmg, bonus_hp, bonus_mp) VALUES (1, 'Iron_Sword', 'weapon', 500, 5, 0, 0, 0, 0, 0, 0, 0)")
    c.execute("INSERT OR REPLACE INTO items (item_id, name, type, price, bonus_atk, bonus_def, bonus_spd, bonus_dex, bonus_crit, bonus_mdmg, bonus_hp, bonus_mp) VALUES (2, 'Leather_Armor', 'armor', 300, 0, 3, 0, 0, 0, 0, 20, 0)")
    c.execute("INSERT OR REPLACE INTO items (item_id, name, type, price, bonus_atk, bonus_def, bonus_spd, bonus_dex, bonus_crit, bonus_mdmg, bonus_hp, bonus_mp) VALUES (3, 'Great_Axe', 'weapon', 1500, 15, 0, -2, 0, 0, 0, 0, 0)")
    c.execute("INSERT OR REPLACE INTO items (item_id, name, type, price, bonus_atk, bonus_def, bonus_spd, bonus_dex, bonus_crit, bonus_mdmg, bonus_hp, bonus_mp) VALUES (4, 'Dagger_of_Thief', 'weapon', 800, 2, 0, 3, 5, 0, 0, 0, 0)") # Item dengan DEX
    c.execute("INSERT OR IGNORE INTO roles (role_id, name, price) VALUES (1448172828192145520, 'Knight', 1000)") 
    
    conn.commit()
    conn.close()

def get_user_data(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute('SELECT exp, level, Money, last_daily_claim, ATK, SPD, DEF, DEX, CRIT, MDMG, HP, MP, inventory_slots, equipped_weapon, equipped_armor, dice_rolls_today, last_dice_reset, last_fight_time, hunt_count_today, last_hunt_reset FROM users WHERE user_id = ?', (user_id,))
    data = c.fetchone()
    conn.close()

    if data is None:
        return 0, 1, 0, '2000-01-01', 5, 5, 5, 5, 5, 5, 100, 50, 10, None, None, 0, '2000-01-01', 0.0, 0, '2000-01-01'
    return data

def update_full_user_data(user_id, exp, level, Money, last_daily_claim, ATK, SPD, DEF, DEX, CRIT, MDMG, HP, MP, inventory_slots, equipped_weapon=None, equipped_armor=None, dice_rolls_today=0, last_dice_reset='2000-01-01', last_fight_time=0.0, hunt_count_today=0, last_hunt_reset='2000-01-01'):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    weapon_to_store = equipped_weapon if equipped_weapon is not None else None
    armor_to_store = equipped_armor if equipped_armor is not None else None

    c.execute('''INSERT OR REPLACE INTO users 
               (user_id, exp, level, Money, last_daily_claim, ATK, SPD, DEF, DEX, CRIT, MDMG, HP, MP, inventory_slots, equipped_weapon, equipped_armor, dice_rolls_today, last_dice_reset, last_fight_time, hunt_count_today, last_hunt_reset) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
             (user_id, exp, level, Money, last_daily_claim, ATK, SPD, DEF, DEX, CRIT, MDMG, HP, MP, inventory_slots, weapon_to_store, armor_to_store, dice_rolls_today, last_dice_reset, last_fight_time, hunt_count_today, last_hunt_reset))
    conn.commit()
    conn.close()

def required_exp_for_level(level):
    return 5 * (level ** 2) + 50 * level + 100

def get_dice_status(user_id):

    user_data = get_user_data(user_id)

    (current_exp, current_level, current_currency, last_daily_str, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, current_rolls, last_reset_str, last_fight_time, hunt_count, hunt_reset) = user_data
    
    today = datetime.date.today().strftime('%Y-%m-%d')
    if last_reset_str != today:
        current_rolls = 0
        last_reset_str = today

        update_full_user_data(user_id, current_exp, current_level, current_currency, last_daily_str, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, current_rolls, last_reset_str, last_fight_time, hunt_count, hunt_reset)
    return current_rolls, last_reset_str, user_data

def get_leaderboard_data():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT user_id, level, exp, Money FROM users ORDER BY level DESC, exp DESC, Money DESC LIMIT 10')
    data = c.fetchall()
    conn.close()
    return data

def get_user_inventory(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT item_name, quantity FROM inventory WHERE user_id = ? AND quantity > 0', (user_id,))
    data = c.fetchall()
    conn.close()
    return data

def get_shop_items(item_type):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT name, price, bonus_atk, bonus_def, bonus_spd, bonus_dex, bonus_crit, bonus_mdmg, bonus_hp, bonus_mp FROM items WHERE type = ? ORDER BY price ASC', (item_type,))
    data = c.fetchall()
    conn.close()
    return data

def get_item_details(item_name_with_underscore):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT item_id, name, type, price, bonus_atk, bonus_def, bonus_spd, bonus_dex, bonus_crit, bonus_mdmg, bonus_hp, bonus_mp FROM items WHERE LOWER(name) = LOWER(?)', (item_name_with_underscore,))
    details = c.fetchone()
    conn.close()
    return details

def update_inventory(user_id, item_name_with_underscore, quantity_change):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT quantity FROM inventory WHERE user_id = ? AND item_name = ?', (user_id, item_name_with_underscore))
    existing_quantity = c.fetchone()
    if existing_quantity:
        new_quantity = existing_quantity[0] + quantity_change
        if new_quantity > 0:
            c.execute('UPDATE inventory SET quantity = ? WHERE user_id = ? AND item_name = ?', (new_quantity, user_id, item_name_with_underscore))
        else:
            c.execute('DELETE FROM inventory WHERE user_id = ? AND item_name = ?', (user_id, item_name_with_underscore))
    elif quantity_change > 0:
        c.execute('INSERT INTO inventory (user_id, item_name, quantity) VALUES (?, ?, ?)', (user_id, item_name_with_underscore, quantity_change))
    conn.commit()
    conn.close()

def get_total_stats(user_id):
    user_data = get_user_data(user_id)
    base_stats = list(user_data[4:12]) 
    equipped_weapon = user_data[13]
    equipped_armor = user_data[14]

    total_stats = base_stats[:]

    def add_item_bonus(item_name):
        if item_name:
            details = get_item_details(item_name)
            if details and len(details) >= 12:

                total_stats[0] += details[4]    # ATK
                total_stats[1] += details[6]    # SPD
                total_stats[2] += details[5]    # DEF
                total_stats[3] += details[7]    # DEX
                total_stats[4] += details[8]    # CRIT
                total_stats[5] += details[9]    # MDMG
                total_stats[6] += details[10]   # HP
                total_stats[7] += details[11]   # MP

    add_item_bonus(equipped_weapon)
    add_item_bonus(equipped_armor)

    return total_stats[0], total_stats[1], total_stats[2], total_stats[3], total_stats[4], total_stats[5], total_stats[6], total_stats[7]

def calculate_upgrade_cost(base_stat_value, amount_to_add, stat_name):

    total_cost = 0
    current_stat = base_stat_value

    for _ in range(amount_to_add):
        current_stat += 1
        
        if current_stat <= STAT_TIER_1_MAX:
            cost_per_point = STAT_TIER_1_COST
        elif current_stat <= STAT_TIER_2_MAX:
            cost_per_point = STAT_TIER_2_COST
        elif current_stat <= STAT_TIER_3_MAX:
            cost_per_point = STAT_TIER_3_COST
        elif current_stat <= STAT_TIER_4_MAX:
            cost_per_point = STAT_TIER_4_COST
        else:
            cost_per_point = STAT_TIER_4_COST 
            
        total_cost += cost_per_point
        
    return total_cost

def get_shop_roles():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT role_id, name, price FROM roles ORDER BY price ASC')
    data = c.fetchall()
    conn.close()
    return data

def get_role_details(role_name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT role_id, name, price FROM roles WHERE LOWER(name) = LOWER(?)', (role_name,))
    details = c.fetchone()
    conn.close()
    return details

def update_user_money(user_id, amount_change):
    
    user_data = get_user_data(user_id)
    (exp, level, current_money, last_daily_str, 
     atk, spd, def_stat, dex, crit, mdmg, hp, mp, 
     inventory_slots, equipped_weapon, equipped_armor, 
     dice_rolls_today, last_dice_reset, last_fight_time, hunt_count, hunt_reset) = user_data
    
    new_money = current_money + amount_change
    
    if new_money < 0:
        new_money = 0
        
    update_full_user_data(user_id, exp, level, new_money, last_daily_str, 
                          atk, spd, def_stat, dex, crit, mdmg, hp, mp, 
                          inventory_slots, equipped_weapon, equipped_armor, 
                          dice_rolls_today, last_dice_reset, last_fight_time, hunt_count, hunt_reset)
    return new_money

def get_shift_config(guild_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT duration_minutes, required_role_ids, reward_money, reward_exp, shift_detail, max_participants FROM shift_config WHERE guild_id = ?', (guild_id,))
    data = c.fetchone()
    conn.close()

    if data is None:
        return 60, '', 1000, 100, 'Shift Standar Harian', 0
    
    if data:
        duration = int(data[0])
        roles_str = data[1]
        money = int(data[2])
        exp = int(data[3])
        detail = data[4]
        max_p = int(data[5])
        return duration, roles_str, money, exp, detail, max_p
        
    return data

def set_shift_config(guild_id, duration, required_roles_str, money, exp, detail, max_p):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO shift_config 
                (guild_id, duration_minutes, required_role_ids, reward_money, reward_exp, shift_detail, max_participants) 
                VALUES (?, ?, ?, ?, ?, ?, ?)''', 
              (guild_id, duration, required_roles_str, money, exp, detail, max_p))
    conn.commit()
    conn.close()

def get_active_shift(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute('SELECT start_time, end_time, reward_money, reward_exp, shift_detail FROM active_shifts WHERE user_id = ?', (user_id,))
    data = c.fetchone()
    conn.close()
    if data:
        return data
    return None

def start_new_shift(user_id, start_time, end_time, money, exp, detail):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM active_shifts WHERE user_id = ?', (user_id,))
    
    c.execute('''INSERT INTO active_shifts 
                (user_id, start_time, end_time, reward_money, reward_exp, shift_detail) 
                VALUES (?, ?, ?, ?, ?, ?)''', 
              (user_id, start_time, end_time, money, exp, detail))
    conn.commit()
    conn.close()

def end_active_shift(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM active_shifts WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def count_active_shifts(guild_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT user_id FROM active_shifts')
    active_user_ids = [row[0] for row in c.fetchall()]
    conn.close()
    return len(active_user_ids)

def load_monsters():
    try:
        with open('monsters.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('monsters', [])
    except FileNotFoundError:
        print("❌ monsters.json tidak ditemukan!")
        return []
    except json.JSONDecodeError:
        print("❌ Format monsters.json tidak valid!")
        return []

def get_monster_for_level(player_level):
    monsters = load_monsters()
    if not monsters:
        return None
    
    # Filter monster yang levelnya <= player level + 2 (bisa ketemu monster sedikit lebih kuat)
    suitable_monsters = [m for m in monsters if m['level'] <= min(player_level + 2, 10)]
    
    if not suitable_monsters:
        suitable_monsters = [monsters[0]]  # Default ke Poring jika tidak ada
    
    return random.choice(suitable_monsters)

def get_hunt_status(user_id):
    user_data = get_user_data(user_id)
    hunt_count = user_data[18]
    last_hunt_reset = user_data[19]
    
    today = datetime.date.today().strftime('%Y-%m-%d')
    if last_hunt_reset != today:
        hunt_count = 0
        last_hunt_reset = today
    
    return hunt_count, last_hunt_reset, user_data

async def handle_equip_command(message):
    user_id = message.author.id
    parts = message.content.lower().split()
    if len(parts) < 2:
        await message.channel.send(f"❌ Format: `{prefix}equip <Item_Name>` (e.g., `{prefix}equip Iron Sword`)")
        return
    
    item_name_raw = " ".join(parts[1:]) 
    item_name_db = item_name_raw.replace(' ', '_')
    inventory = get_user_inventory(user_id)
    item_in_inventory = any(item[0].lower() == item_name_db.lower() and item[1] > 0 for item in inventory)

    if not item_in_inventory:
        await message.channel.send(f"❌ Anda tidak memiliki `{item_name_raw}` di inventaris! Pastikan Anda sudah membelinya.")
        return
    
    details = get_item_details(item_name_db)

    if not details:
        await message.channel.send(f"❌ Item `{item_name_raw}` tidak valid atau tidak ada di database!")
        return

    _, name_db, item_type, _, bonus_atk, bonus_def, bonus_spd, bonus_dex, bonus_crit, bonus_mdmg, bonus_hp, bonus_mp = details

    user_data = get_user_data(user_id)
    exp, level, money, last_daily, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset = user_data

    old_item_name = None
    
    if item_type == 'weapon':
        old_item_name = equipped_weapon
        equipped_weapon = name_db 
        slot_display = "Senjata (Weapon)"
    elif item_type == 'armor':
        old_item_name = equipped_armor
        equipped_armor = name_db
        slot_display = "Baju Zirah (Armor)"
    else:
        await message.channel.send(f"❌ Item `{item_name_raw}` tidak dapat di-equip (tipe: {item_type})!")
        return

    update_full_user_data(user_id, exp, level, money, last_daily, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset)

    item_name_display = name_db.replace('_', ' ')

    description_text = f"Item **{item_name_display}** berhasil dipasang di slot **{slot_display}**."
    if old_item_name:
        description_text += f"\n(Item lama **{old_item_name.replace('_', ' ')}** telah dilepas ke inventaris.)"
    
    embed = discord.Embed(
        title="⚔️ ITEM TERPASANG (EQUIPPED) 🛡️",
        description=description_text,
        color=discord.Color.dark_teal()
    )

    stats_list = []
    if bonus_atk != 0: stats_list.append(f"⚔️ ATK: +{bonus_atk}" if bonus_atk > 0 else f"⚔️ ATK: {bonus_atk}")
    if bonus_def != 0: stats_list.append(f"🛡️ DEF: +{bonus_def}" if bonus_def > 0 else f"🛡️ DEF: {bonus_def}")
    if bonus_spd != 0: stats_list.append(f"👟 SPD: +{bonus_spd}" if bonus_spd > 0 else f"👟 SPD: {bonus_spd}")
    if bonus_dex != 0: stats_list.append(f"🎯 DEX: +{bonus_dex}" if bonus_dex > 0 else f"🎯 DEX: {bonus_dex}")
    if bonus_crit != 0: stats_list.append(f"💥 CRIT: +{bonus_crit}" if bonus_crit > 0 else f"💥 CRIT: {bonus_crit}")
    if bonus_mdmg != 0: stats_list.append(f"⚛️ MDMG: +{bonus_mdmg}" if bonus_mdmg > 0 else f"⚛️ MDMG: {bonus_mdmg}")
    if bonus_hp != 0: stats_list.append(f"❤️ HP: +{bonus_hp}" if bonus_hp > 0 else f"❤️ HP: {bonus_hp}")
    if bonus_mp != 0: stats_list.append(f"🌀 MP: +{bonus_mp}" if bonus_mp > 0 else f"🌀 MP: {bonus_mp}")


    embed.add_field(
        name=f"✨ {item_name_display.upper()} ({item_type.capitalize()})",
        value='\n'.join(stats_list) if stats_list else "Tidak ada bonus statistik.",
        inline=True
    )

    if old_item_name:
          embed.add_field(
            name="Item Sebelumnya Dilepas",
            value=f"{old_item_name.replace('_', ' ')}",
            inline=True
        )

    await message.channel.send(embed=embed)

async def handle_unequip_command(message):
    user_id = message.author.id
    parts = message.content.lower().split()
    
    if len(parts) < 2:
        await message.channel.send(f"❌ Format: `{prefix}unequip <Item_Name>` (e.g., `{prefix}unequip Iron Sword`)")
        return

    item_name_raw = " ".join(parts[1:])
    item_name_db = item_name_raw.replace(' ', '_')

    user_data = get_user_data(user_id)
    exp, level, money, last_daily, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset = user_data

    item_unequipped = None
    slot_affected = None

    if equipped_weapon and equipped_weapon.lower() == item_name_db.lower():
        item_unequipped = equipped_weapon
        equipped_weapon = None
        slot_affected = "Weapon"

    elif equipped_armor and equipped_armor.lower() == item_name_db.lower():
        item_unequipped = equipped_armor
        equipped_armor = None
        slot_affected = "Armor"

    if item_unequipped:
        item_name_display = item_unequipped.replace('_', ' ')

        update_full_user_data(user_id, exp, level, money, last_daily, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset)

        embed = discord.Embed(
            description=f"{message.author.mention} berhasil melepas item **{item_name_display}**.",
            color=discord.Color.gold()
        )
        embed.add_field(
            name="Slot Terpengaruh",
            value=slot_affected,
            inline=True
        )
        embed.add_field(
            name="Status Terbaru",
            value="Item sekarang berada di inventaris Anda.",
            inline=True
        )
        
        await message.channel.send(embed=embed)
    else:
        await message.channel.send(f"❌ Item `{item_name_raw}` tidak terpasang di slot `weapon` maupun `armor`.")

async def handle_upgrade_command(message):
    user_id = message.author.id
    parts = message.content.lower().split()
    
    # 1. Validasi Input
    if len(parts) < 3:
        await message.channel.send(f"❌ Format: `{prefix}upgrade <stat> <amount>` (e.g., `{prefix}upgrade atk 5`). Biaya: Progresif, dimulai dari {STAT_TIER_1_COST} ACR per poin.")
        return
    
    stat = parts[1]
    valid_stats = ['atk', 'spd', 'def', 'dex', 'crit', 'mdmg', 'hp', 'mp']
    
    if stat not in valid_stats:
        await message.channel.send(f"❌ Stat tidak valid: `{stat}`. Gunakan: `{'`, `'.join(valid_stats)}`.")
        return
    
    try:
        amount = int(parts[2])
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.channel.send(f"❌ Jumlah harus angka positif!")
        return

    user_data = get_user_data(user_id)
    exp, level, money, last_daily, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset = user_data

    if stat == 'atk': current_base_stat = atk
    elif stat == 'spd': current_base_stat = spd
    elif stat == 'def': current_base_stat = def_stat
    elif stat == 'dex': current_base_stat = dex
    elif stat == 'crit': current_base_stat = crit
    elif stat == 'mdmg': current_base_stat = mdmg

    elif stat == 'hp': current_base_stat = hp // 10 
    elif stat == 'mp': current_base_stat = mp // 5 
    else: current_base_stat = 0

    cost = calculate_upgrade_cost(current_base_stat, amount, stat)

    if money < cost:
        await message.channel.send(f"❌ Uang tidak cukup! Dibutuhkan **💵 {cost:,} ACR**, Anda punya **💵 {money:,} ACR**.")
        return

    if stat == 'atk': 
        atk += amount
        increment = amount
    elif stat == 'spd': 
        spd += amount
        increment = amount
    elif stat == 'def': 
        def_stat += amount
        increment = amount
    elif stat == 'dex': 
        dex += amount
        increment = amount
    elif stat == 'crit': 
        crit += amount
        increment = amount
    elif stat == 'mdmg': 
        mdmg += amount
        increment = amount
    elif stat == 'hp': 
        hp += amount * 10 
        increment = amount * 10
    elif stat == 'mp': 
        mp += amount * 5 
        increment = amount * 5

    money -= cost

    update_full_user_data(user_id, exp, level, money, last_daily, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset)

    embed = discord.Embed(
        color=discord.Color.green(),
    )

    embed.set_author(
        name=f"{message.author.display_name} | Status Upgrade!",
    )

    embed.set_thumbnail(url=message.author.display_avatar.url)
    
    embed.add_field(
        name = "Upgrade Detail",
        value=f"**{stat.upper()}** +{increment} points",
        inline = False,
    )

    embed.add_field(
        name = "Total Cost",
        value=f"💵 {cost:,} ACR",
        inline= True,
    )

    embed.add_field(
        name = "Remaining Money",
        value=f"💵 {money:,} ACR",
        inline= True,
    )

    await message.channel.send(embed=embed)

async def handle_inventory_command(message):
    user_id = message.author.id

    user_data = get_user_data(user_id)
    max_slots = user_data[12]
    equipped_weapon = user_data[13]
    equipped_armor = user_data[14]
    
    inventory_items = get_user_inventory(user_id)
    total_unique_items = len(inventory_items)
    
    embed = discord.Embed(
        title=f"🎒 Inventory {message.author.display_name}",
        description=f"Slot Terpakai: **{total_unique_items} / {max_slots}** (Item Unik)\nEquipped: Weapon - **{equipped_weapon.replace('_', ' ') if equipped_weapon else 'None'}**, Armor - **{equipped_armor.replace('_', ' ') if equipped_armor else 'None'}**",
        color=discord.Color.dark_green()
    )
    if inventory_items:
        item_list = []
        for name_db, quantity in inventory_items:
            name_display = name_db.replace('_', ' ')
            equipped_status = ""
            if name_db == equipped_weapon:
                equipped_status = " (Equipped - Weapon)"
            elif name_db == equipped_armor:
                equipped_status = " (Equipped - Armor)"
            item_list.append(f"**{name_display}** x{quantity}{equipped_status}")
        embed.add_field(name="Item Anda", value="\n".join(item_list), inline=False)
    else:
        embed.add_field(name="Item Anda", value="Inventaris kosong.", inline=False)
    await message.channel.send(embed=embed)

async def handle_list_command(message, item_type):
    if item_type == 'role':

        shop_roles = get_shop_roles()
        if not shop_roles:
            await message.channel.send(f"❌ Toko saat ini tidak menjual ROLE.")
            return
        max_name_len = max(len(name) for _, name, _ in shop_roles)
        max_price_len = max(len(f"{price:,}") for _, _, price in shop_roles)
        header_name = "ROLE".ljust(max_name_len)
        header_price = "PRICE".rjust(max_price_len + 1)
        header_line = f"{header_name} | {header_price}"
        role_list = []
        for _, name, price in shop_roles:
            name_padded = name.ljust(max_name_len)
            price_padded = f"${price:,} ACR".rjust(max_price_len + 1)
            role_list.append(f"{name_padded} | {price_padded}")
        final_content = (
            f"═{'═'*len(header_line)}\n"
            f"{header_line}\n"
            f"═{'═'*len(header_line)}\n"
            + "\n".join(role_list)
        )
        embed = discord.Embed(
            title=f"🛒 ROLE SHOP",
            description=f"Daftar role yang tersedia. Gunakan `{prefix}buy role <Role_Name>`.\n**Pastikan Anda menyebutkan nama role persis seperti yang tertera.**",
            color=discord.Color.blue()
        )
        embed.add_field(name="Role dan Harga (ACR)", 
                         value=f"```fix\n{final_content}\n```", 
                         inline=False)
        await message.channel.send(embed=embed)
        return

    shop_items = get_shop_items(item_type)
    if not shop_items:
        await message.channel.send(f"❌ Toko saat ini tidak menjual {item_type.upper()}.")
        return
    
    max_name_len = max(len(name.replace('_', ' ')) for name, *_, _ in shop_items)
    max_price_len = max(len(f"{price:,}") for _, price, *_, _ in shop_items)

    STAT_COL_WIDTH = 1

    header_name = "ITEM".ljust(max_name_len)
    header_stats_phys = "ATK|DEF|SPD".replace('|', ' ' * (STAT_COL_WIDTH))
    header_stats_magic = "DEX|CRT|MDMG".replace('|', ' ' * (STAT_COL_WIDTH))
    header_stats_tambah = "HP|MP".replace('|', ' ' * (STAT_COL_WIDTH))
    header_price = "PRICE".rjust(max_price_len)
    
    header_line = f"{header_name} | {header_stats_phys} | {header_stats_magic} | {header_stats_tambah} | {header_price}"

    item_list = []
    for item_data in shop_items:
        name_db, price, atk, def_stat, spd, dex, crit, mdmg, hp, mp = item_data
        
        stats_phys_str = f"{atk:03}|{def_stat:03}|{spd:03}"
        stats_magic_str = f"{dex:03}|{crit:03}|{mdmg:03}"
        stats_tambah = f"{hp:03}|{mp:03}"
        
        name_display = name_db.replace('_', ' ')
        name_padded = name_display.ljust(max_name_len)
        price_padded = f"${price:,}".rjust(max_price_len + 1)
        
        item_list.append(f"{name_padded} | {stats_phys_str} | {stats_magic_str} |{stats_tambah}| {price_padded}")
        
    final_content = (
        f"═{'═'*len(header_line)}\n"
        f"{header_line}\n"
        f"═{'═'*len(header_line)}\n"
        + "\n".join(item_list)
    )

    embed = discord.Embed(
        title=f"🛒 {item_type.upper()} SHOP",
        color=discord.Color.blue()
    )
    embed.add_field(name="Item, Stat, dan Harga", 
                     value=f"```fix\n{final_content}\n```", 
                     inline=False)
    await message.channel.send(embed=embed)

async def handle_buy_role_command(message):
    user_id = message.author.id
    try:
        parts = message.content.lower().split()
        role_name_raw = " ".join(parts[2:])
        role_name = role_name_raw.title()
    except IndexError:
        await message.channel.send(f"❌ Format salah. Gunakan: `{prefix}buy role <Role_Name>`")
        return
    details = get_role_details(role_name) 
    if not details:
        await message.channel.send(f"❌ Role `{role_name}` tidak ditemukan di toko! Cek `{prefix}list role`.")
        return
    role_discord_id, role_db_name, price = details
    # Ambil 20 kolom data user
    user_data = get_user_data(user_id)
    exp, level, current_currency, last_daily_str, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset = user_data

    if current_currency < price:
        await message.channel.send(f"❌ Uang Anda tidak cukup! Anda butuh **💵 {price:,} ACR**, tetapi Anda hanya punya **💵 {current_currency:,} ACR**.")
        return
    try:
        guild = message.guild
        if guild is None:
            await message.channel.send("❌ Perintah ini hanya bisa digunakan di dalam server.")
            return
        role_to_give = guild.get_role(role_discord_id)
        if role_to_give is None:
            await message.channel.send(f"❌ Role Discord dengan ID `{role_discord_id}` tidak ditemukan di server ini.")
            return
        if role_to_give in message.author.roles:
            await message.channel.send(f"❌ Anda sudah memiliki role **{role_db_name}**!")
            return
        new_currency = current_currency - price
        await message.author.add_roles(role_to_give)

        update_full_user_data(user_id, exp, level, new_currency, last_daily_str, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset)
        await message.channel.send(
            f"🎉 **Pembelian Role Berhasil!** {message.author.mention} membeli role **{role_db_name}** "
            f"seharga **💵 {price:,} ACR**.\n"
            f"Sisa uang Anda: **💵 {new_currency:,} ACR**."
        )
    except discord.Forbidden:
        await message.channel.send("❌ Bot tidak memiliki izin untuk memberikan role tersebut. Pastikan role bot berada di atas role yang akan diberikan.")
    except Exception as e:
        logging.error(f"Error giving role: {e}")
        await message.channel.send("❌ Terjadi kesalahan saat mencoba memberikan role.")

async def handle_dice_command(message):
    user_id = message.author.id
    current_rolls, _, user_data = get_dice_status(user_id)
  
    (current_exp, current_level, current_currency, last_daily_str, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset) = user_data
    
    stage_index = current_rolls 
    if stage_index >= MAX_DAILY_DICE:
        await message.channel.send(f"❌ **Jatah Dadu Habis!** Anda sudah menggunakan {MAX_DAILY_DICE} dari {MAX_DAILY_DICE} jatah roll hari ini. Silahkan coba lagi besok.")
        return
    cost = DICE_COSTS[stage_index]
    if current_currency < cost:
        await message.channel.send(f"❌ Uang tidak cukup untuk Roll Tahap {stage_index + 1}! Dibutuhkan **💵 {cost:,} ACR**, Anda punya **💵 {current_currency:,} ACR**.")
        return
    
    current_currency -= cost
    dice_roll = random.randint(1, 6)
    base_reward = DICE_BASE_REWARD + (stage_index * 200) 
    
    if dice_roll == 6:
        reward_multiplier = 2.0
    elif dice_roll >= 4:
        reward_multiplier = 1.0 
    else:
        reward_multiplier = 0.5
        
    reward_gain = int(base_reward * reward_multiplier)
    current_currency += reward_gain
    new_rolls = current_rolls + 1
    today_str = datetime.date.today().strftime('%Y-%m-%d')

    update_full_user_data(user_id, current_exp, current_level, current_currency, last_daily_str, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, new_rolls, today_str, last_fight_time, hunt_count, hunt_reset)
    
    if dice_roll == 6: emoji = "👑"
    elif dice_roll == 5: emoji = "⚄"
    elif dice_roll == 4: emoji = "⚃"
    elif dice_roll == 3: emoji = "⚂"
    elif dice_roll == 2: emoji = "⚁"
    elif dice_roll == 1: emoji = "⚀"
    
    response = (
        f"{message.author.mention} melempar dadu (Roll Tahap {stage_index + 1}): **{dice_roll}** {emoji}\n"
        f"Biaya Roll: **💵 {cost:,} ACR**.\n"
    )
    if reward_multiplier > 0:
        response += f"🎉 Anda mendapatkan **💵 {reward_gain:,} ACR**! (Multiplier: x{reward_multiplier:.1f})\n"
    response += f"Sisa jatah hari ini: **{MAX_DAILY_DICE - new_rolls}** kali. Total uang: **💵 {current_currency:,} ACR**."
    await message.channel.send(response)

async def handle_fight_command(message):
    user_id = message.author.id
    current_time = time.time()

    if not message.mentions or message.mentions[0].id == user_id:
        await message.channel.send(f"❌ Format: `{prefix}fight <@user>`! Anda tidak bisa bertarung dengan diri sendiri!")
        return
    
    attacker = message.author
    target_member = message.mentions[0]
    target_id = target_member.id

    if target_member.bot:
        await message.channel.send("❌ Anda tidak bisa bertarung melawan bot!")
        return

    player_data = get_user_data(user_id)
    (p_exp, p_lvl, p_money, p_daily, p_atk, p_spd, p_def, p_dex, p_crit, p_mdmg, p_hp, p_mp, p_slots, p_w, p_a, p_dice, p_dice_reset, p_last_fight, p_hunt, p_hunt_reset) = player_data

    time_remaining = FIGHT_COOLDOWN - (current_time - p_last_fight)

    if time_remaining > 0:
        minutes = int(time_remaining // 60)
        seconds = int(time_remaining % 60)
        await message.channel.send(f"⏳ **Cooldown!** Anda harus menunggu {minutes} menit {seconds} detik lagi sebelum pertarungan berikutnya.")
        return
        
    fight_cost = random.randint(FIGHT_COST_MIN, FIGHT_COST_MAX)

    if p_money < fight_cost:
        await message.channel.send(f"❌ **Uang Tidak Cukup!** Anda butuh setidaknya **💵 {fight_cost:,} ACR** untuk memulai pertarungan.")
        return
    
    challenge_embed = discord.Embed(
        title="⚔️ TANTANGAN PERTARUNGAN PVP ⚔️",
        description=f"{target_member.mention}, Anda ditantang oleh **{attacker.display_name}**!\n"
                    f"Biaya Pertarungan: **💵 {fight_cost:,} ACR** (Dibebankan ke penantang).\n"
                    f"Anda punya 30 detik untuk menerima.\n\n"
                    f"Tekan ✅ untuk Menerima, ❌ untuk Menolak.",
        color=discord.Color.orange()
    )
    challenge_msg = await message.channel.send(embed=challenge_embed)

    await challenge_msg.add_reaction('✅')
    await challenge_msg.add_reaction('❌')

    def check(reaction, user):
        return user.id == target_id and str(reaction.emoji) in ['✅', '❌'] and reaction.message.id == challenge_msg.id

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)
    
    except asyncio.TimeoutError:
        await message.channel.send(f"⏳ {target_member.mention} tidak merespon tepat waktu. Tantangan pertarungan dibatalkan.")
        return
        
    if str(reaction.emoji) == '❌':
        await message.channel.send(f"🛡️ {target_member.mention} menolak tantangan dari {attacker.mention}. Pertarungan dibatalkan.")
        return

    target_data = get_user_data(target_id)
    (t_exp, t_lvl, t_money, t_daily, t_atk, t_spd, t_def, t_dex, t_crit, t_mdmg, t_hp, t_mp, t_slots, t_w, t_a, t_dice, t_dice_reset, t_last_fight, t_hunt, t_hunt_reset) = target_data

    if t_money < fight_cost / 2:

        await message.channel.send(f"❌ **Target Miskin!** {target_member.display_name} terlalu miskin untuk menerima pertarungan (dibutuhkan min **💵 {int(fight_cost/2):,} ACR**). Pertarungan dibatalkan.")
        return

    p_total_atk, p_total_spd, p_total_def, p_total_dex, p_total_crit, p_total_mdmg, p_total_hp, p_total_mp = get_total_stats(user_id)
    t_total_atk, t_total_spd, t_total_def, t_total_dex, t_total_crit, t_total_mdmg, t_total_hp, t_total_mp = get_total_stats(target_id)
    
    p_power_base = (p_total_atk * 0.4) + (p_total_mdmg * 0.2) + (p_total_def * 0.1) + (p_total_spd * 0.1) + (p_total_dex * 0.1)
    t_power_base = (t_total_atk * 0.4) + (t_total_mdmg * 0.2) + (t_total_def * 0.1) + (t_total_spd * 0.1) + (t_total_dex * 0.1)
    
    p_crit_mod = 1 + (p_total_crit / 100) * 0.5 
    t_crit_mod = 1 + (t_total_crit / 100) * 0.5
    
    p_power = (p_power_base * p_crit_mod) + (p_lvl * 10)
    t_power = (t_power_base * t_crit_mod) + (t_lvl * 10)
    
    p_power *= random.uniform(0.9, 1.1)
    t_power *= random.uniform(0.9, 1.1)
    
    winner = attacker if p_power > t_power else target_member
    loser = target_member if p_power > t_power else attacker

    bonus_exp = random.randint(FIGHT_BONUS_EXP_MIN, FIGHT_BONUS_EXP_MAX)
    bonus_money = random.randint(FIGHT_BONUS_MONEY_MIN, FIGHT_BONUS_MONEY_MAX)

    max_steal = int(t_money * 0.5) 
    stolen_amount = random.randint(int(t_money * 0.1), max_steal)

    if winner.id == user_id:
        p_money -= fight_cost 
        p_money += stolen_amount 
        t_money -= stolen_amount 
        p_exp += bonus_exp
        p_money += bonus_money

        update_full_user_data(user_id, p_exp, p_lvl, p_money, p_daily, p_atk, p_spd, p_def, p_dex, p_crit, p_mdmg, p_hp, p_mp, p_slots, p_w, p_a, p_dice, p_dice_reset, current_time, p_hunt, p_hunt_reset)

        update_full_user_data(target_id, t_exp, t_lvl, t_money, t_daily, t_atk, t_spd, t_def, t_dex, t_crit, t_mdmg, t_hp, t_mp, t_slots, t_w, t_a, t_dice, t_dice_reset, t_last_fight, t_hunt, t_hunt_reset)

    else:
        p_money -= fight_cost 
        p_money -= stolen_amount 
        t_money += stolen_amount
        t_exp += bonus_exp
        t_money += bonus_money

        update_full_user_data(target_id, t_exp, t_lvl, t_money, t_daily, t_atk, t_spd, t_def, t_dex, t_crit, t_mdmg, t_hp, t_mp, t_slots, t_w, t_a, t_dice, t_dice_reset, current_time, t_hunt, t_hunt_reset)

        update_full_user_data(user_id, p_exp, p_lvl, p_money, p_daily, p_atk, p_spd, p_def, p_dex, p_crit, p_mdmg, p_hp, p_mp, p_slots, p_w, p_a, p_dice, p_dice_reset, current_time, p_hunt, p_hunt_reset)

    embed = discord.Embed(
        title="⚔️ Hasil Pertarungan PVP ⚔️",
        description=f"Pertarungan sengit antara {attacker.mention} dan {target_member.mention} telah usai!",
        color=discord.Color.green() if winner.id == user_id else discord.Color.red()
    )
    embed.add_field(name="Pemenang", value=f"👑 **{winner.display_name}**", inline=False)
    embed.add_field(name="Kalah", value=f"💀 {loser.display_name}", inline=True)
    embed.add_field(name="Uang Diambil", value=f"💵 **{stolen_amount:,} ACR**", inline=True)
    embed.add_field(name="Bonus Pemenang", value=f"🎁 **+ {bonus_exp:,} EXP, + {bonus_money:,} ACR**", inline=False)
   
    await message.channel.send(embed=embed)

async def handle_buy_menu(message):
    prefix = 'ag!'
    menu_text = f"""

    Selamat datang di Toko Aetherion Game!
    Silakan pilih kategori pembelian:
    1. **{prefix}buy weapon <Nama_Senjata>**: Beli Senjata (Lihat daftar: `{prefix}shop weapon`)
    2. **{prefix}buy armor <Nama_Armor>**: Beli Baju Zirah (Lihat daftar: `{prefix}shop armor`)
    3. **{prefix}buy role <Nama_Role>**: Beli Role Discord (Lihat daftar: `{prefix}shop role`)

    **Lainnya:**

    * **{prefix}sell <Item_Name> <Jumlah>**: Jual item (50% harga beli).
    * **{prefix}inventory**: Lihat semua item yang Anda miliki.
    Contoh: `{prefix}buy role Knight`
    """
    embed = discord.Embed(
        title="🛒 KATEGORI TOKO (SHOP)",
        description=menu_text,
        color=discord.Color.gold()
    )
    await message.channel.send(embed=embed)

async def handle_buy_item_command(message, item_type):
    user_id = message.author.id
    try:
        parts = message.content.lower().split()
        item_name_raw = " ".join(parts[2:]) 
        item_name_db = item_name_raw.replace(' ', '_') 
    except IndexError:
        await message.channel.send(f"❌ Format salah. Gunakan: `{prefix}buy {item_type} <Item_Name>`")
        return
        
    details = get_item_details(item_name_db) 
    if not details:
        await message.channel.send(f"❌ Item `{item_name_raw}` tidak ditemukan di toko!")
        return
        
    item_id, name_db, item_db_type, price, *_, _ = details
    
    if item_db_type != item_type:
        await message.channel.send(f"❌ `{name_db.replace('_', ' ')}` adalah {item_db_type.upper()}, bukan {item_type.upper()}.")
        return

    user_data = get_user_data(user_id)
    exp, level, current_currency, last_daily_str, atk, spd, def_stat, dex, crit, mdmg, hp, mp, max_slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset = user_data
    
    if current_currency < price:
        await message.channel.send(f"❌ Uang Anda tidak cukup! Anda butuh **💵 {price:,} ACR**, tetapi Anda hanya punya **💵 {current_currency:,} ACR**.")
        return
        
    inventory_items = get_user_inventory(user_id)
    total_unique_items = len(inventory_items)
    is_new_item = name_db not in [item[0] for item in inventory_items]
    
    if total_unique_items >= max_slots and is_new_item:
        await message.channel.send(f"❌ **Inventaris penuh!** Anda hanya punya {max_slots} slot unik. Kosongkan ruang untuk item baru, atau beli item yang sudah ada.")
        return
        
    new_currency = current_currency - price
    update_inventory(user_id, name_db, 1)

    update_full_user_data(user_id, exp, level, new_currency, last_daily_str, atk, spd, def_stat, dex, crit, mdmg, hp, mp, max_slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset)
    
    await message.channel.send(
        f"✅ **Pembelian Berhasil!** {message.author.mention} membeli **{name_db.replace('_', ' ')}** "
        f"seharga **💵 {price:,} ACR**.\n"
        f"Sisa uang Anda: **💵 {new_currency:,} ACR**."
    )

async def handle_sell_command(message):
    user_id = message.author.id
    parts = message.content.lower().split()
    if len(parts) < 3:
        await message.channel.send(f"❌ Format: `{prefix}sell <Item_Name> <Jumlah>` (e.g., `{prefix}sell Iron Sword 1`).")
        return
        
    try:
        amount = int(parts[-1])
        if amount <= 0:
            raise ValueError
        item_name_raw = " ".join(parts[1:-1]) 
        item_name_db = item_name_raw.replace(' ', '_')
    except ValueError:
        await message.channel.send(f"❌ Jumlah harus angka positif!")
        return
        
    details = get_item_details(item_name_db)
    if not details:
        await message.channel.send(f"❌ Item `{item_name_raw}` tidak valid!")
        return
        
    name_db, price = details[1], details[3]
    sell_price = int(price * 0.5) 
    
    inventory = get_user_inventory(user_id)
    item_in_inventory = next((item for item in inventory if item[0].lower() == item_name_db.lower()), None)
    
    if not item_in_inventory or item_in_inventory[1] < amount:
        current_quantity = item_in_inventory[1] if item_in_inventory else 0
        await message.channel.send(f"❌ Anda tidak punya **{amount}**x `{item_name_raw}`. Anda hanya punya **{current_quantity}**.")
        return

    user_data = get_user_data(user_id)
    exp, level, money, last_daily, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset = user_data
    
    if (name_db == equipped_weapon and item_in_inventory[1] == amount) or \
       (name_db == equipped_armor and item_in_inventory[1] == amount):
        await message.channel.send(f"❌ Anda harus melepaskan (`{prefix}unequip`) `{item_name_raw}` terlebih dahulu sebelum menjualnya (jika Anda menjual semua stok yang Anda miliki).")
        return
        
    total_revenue = amount * sell_price
    new_currency = money + total_revenue
    
    update_inventory(user_id, name_db, -amount)

    update_full_user_data(user_id, exp, level, new_currency, last_daily, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset)
    
    await message.channel.send(
        f"✅ **Jual Berhasil!** {message.author.mention} menjual **{amount}x {name_db.replace('_', ' ')}** "
        f"sebesar **💵 {total_revenue:,} ACR**.\n"
        f"Total Uang Anda sekarang: **💵 {new_currency:,} ACR**."
    )

async def handle_givemoney_command(message):
    user_id = message.author.id
    parts = message.content.lower().split()

    if len(parts) < 3 or not message.mentions or message.mentions[0].id == user_id:
        await message.channel.send(f"❌ Format: `{prefix}givemoney <@user> <amount>`. Anda harus menyebutkan pengguna lain dan jumlah yang valid.")
        return

    target_user = message.mentions[0]
    target_id = target_user.id
    
    try:
        amount_to_give = int(parts[-1])
        if amount_to_give <= 0:
            raise ValueError
    except ValueError:
        await message.channel.send("❌ Jumlah uang yang diberikan harus berupa angka positif!")
        return

    total_cost = amount_to_give

    sender_data = get_user_data(user_id)
    (s_exp, s_level, s_money, s_daily, s_atk, s_spd, s_def, s_dex, s_crit, s_mdmg, s_hp, s_mp, s_slots, s_w, s_a, s_dice, s_dice_reset, s_fight_time, s_hunt, s_hunt_reset) = sender_data
    
    if s_money < total_cost:
        await message.channel.send(f"❌ Uang tidak cukup! Anda hanya punya **💵 {s_money:,} ACR**, tetapi Anda perlu **💵 {total_cost:,} ACR**.")
        return

    s_money -= total_cost
    update_full_user_data(user_id, s_exp, s_level, s_money, s_daily, s_atk, s_spd, s_def, s_dex, s_crit, s_mdmg, s_hp, s_mp, s_slots, s_w, s_a, s_dice, s_dice_reset, s_fight_time, s_hunt, s_hunt_reset)
    target_data = get_user_data(target_id)
    (t_exp, t_level, t_money, t_daily, t_atk, t_spd, t_def, t_dex, t_crit, t_mdmg, t_hp, t_mp, t_slots, t_w, t_a, t_dice, t_dice_reset, t_fight_time, t_hunt, t_hunt_reset) = target_data
    
    t_money += amount_to_give
    
    update_full_user_data(target_id, t_exp, t_level, t_money, t_daily, t_atk, t_spd, t_def, t_dex, t_crit, t_mdmg, t_hp, t_mp, t_slots, t_w, t_a, t_dice, t_dice_reset, t_fight_time, t_hunt, t_hunt_reset)

    embed = discord.Embed(
        title="💸 TRANSFER UANG ACR 💸",
        color=discord.Color.green()
    )

    embed.add_field(name="Penerima:", value=f"**{target_user.mention}**", inline=False)
    embed.add_field(name="Pengirim:", value=f"**{message.author.mention}**", inline=False)
    embed.add_field(name="Jumlah Ditransfer", value=f"**💵 {amount_to_give:,} ACR**", inline=False)
    embed.add_field(name="Sisa Uang Anda", value=f"**💵 {s_money:,} ACR**", inline=True)
    embed.add_field(name="Total Uang Penerima", value=f"**💵 {t_money:,} ACR**", inline=True)

    await message.channel.send(embed=embed)

async def handle_hunt_command(message):
    user_id = message.author.id
    
    # Check hunt limit
    hunt_count, last_hunt_reset, user_data = get_hunt_status(user_id)
    
    if hunt_count >= MAX_DAILY_HUNT:
        await message.channel.send(f"❌ **Jatah Hunt Habis!** Anda sudah berburu {MAX_DAILY_HUNT}x hari ini. Coba lagi besok!")
        return
    
    (exp, level, money, last_daily, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, dice_reset, fight_time, _, _) = user_data
    
    # Get monster
    monster = get_monster_for_level(level)
    if not monster:
        await message.channel.send("❌ Tidak ada monster yang tersedia!")
        return
    
    # Get total stats with equipment
    total_atk, total_spd, total_def, total_dex, total_crit, total_mdmg, total_hp, total_mp = get_total_stats(user_id)
    
    # Battle calculation
    player_damage = (total_atk * 2) + (total_mdmg * 1.5) + (level * 3)
    crit_chance = total_crit / 100
    
    # Check for critical hit
    is_crit = random.random() < crit_chance
    if is_crit:
        player_damage *= 1.5
    
    # Add randomness
    player_damage *= random.uniform(0.85, 1.15)
    player_damage = int(player_damage)
    
    monster_hp = monster['hp']
    monster_atk = monster['level'] * 8
    
    # Simple battle: compare damage vs monster HP
    turns_to_kill = max(1, monster_hp // max(1, player_damage))
    player_hp_loss = turns_to_kill * monster_atk
    
    # Win condition: player can kill monster before losing all HP
    win = player_hp_loss < total_hp or player_damage >= monster_hp
    
    # Update hunt count
    today = datetime.date.today().strftime('%Y-%m-%d')
    new_hunt_count = hunt_count + 1
    
    if win:
        # Calculate rewards
        exp_reward = monster['exp']
        gold_reward = monster['level'] * random.randint(HUNT_GOLD_MULTIPLIER_MIN, HUNT_GOLD_MULTIPLIER_MAX)
        
        # Bonus for higher level monsters
        if monster['level'] >= level:
            exp_reward = int(exp_reward * 1.5)
            gold_reward = int(gold_reward * 1.3)
        
        new_exp = exp + exp_reward
        new_money = money + gold_reward
        
        # Check level up
        lvl_up_message = ""
        required_exp = required_exp_for_level(level)
        
        while new_exp >= required_exp:
            level += 1
            new_exp -= required_exp
            required_exp = required_exp_for_level(level)
            
            stat_to_boost = random.choice(['atk', 'spd', 'def', 'dex', 'crit', 'mdmg'])
            
            if stat_to_boost == 'atk': atk += 5
            elif stat_to_boost == 'spd': spd += 5
            elif stat_to_boost == 'def': def_stat += 5
            elif stat_to_boost == 'dex': dex += 5
            elif stat_to_boost == 'crit': crit += 5
            elif stat_to_boost == 'mdmg': mdmg += 5
            
            lvl_up_message += f"🎉 **LEVEL UP** ke **Level {level}**! (+5 {stat_to_boost.upper()})\n"
        
        update_full_user_data(user_id, new_exp, level, new_money, last_daily, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, dice_reset, fight_time, new_hunt_count, today)
        
        # Create victory embed
        embed = discord.Embed(
            title=f"⚔️ HUNT VICTORY! ⚔️",
            description=f"{message.author.mention} berhasil mengalahkan **{monster['name']}**!",
            color=discord.Color.green()
        )
        # Set monster image if available
        if monster.get('image'):
            embed.set_thumbnail(url=monster['image'])
        embed.add_field(name="🎯 Monster", value=f"**{monster['name']}** (Lv.{monster['level']})\n{monster['description']}", inline=False)
        embed.add_field(name="💥 Damage Dealt", value=f"**{player_damage:,}** {'🔥 CRIT!' if is_crit else ''}", inline=True)
        embed.add_field(name="❤️ Monster HP", value=f"**{monster_hp}**", inline=True)
        embed.add_field(name="🌟 Element", value=f"**{monster['element'].capitalize()}**", inline=True)
        embed.add_field(name="🎁 Rewards", value=f"✨ **+{exp_reward} EXP**\n💵 **+{gold_reward:,} ACR**", inline=False)
        
        if lvl_up_message:
            embed.add_field(name="🆙 Level Up!", value=lvl_up_message, inline=False)
        
        embed.add_field(name="📊 Hunt Hari Ini", value=f"**{new_hunt_count}/{MAX_DAILY_HUNT}**", inline=True)
        embed.add_field(name="💰 Total Money", value=f"**{new_money:,} ACR**", inline=True)
        
    else:
        # Lose - no rewards, still count hunt
        update_full_user_data(user_id, exp, level, money, last_daily, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, dice_reset, fight_time, new_hunt_count, today)
        
        embed = discord.Embed(
            title=f"💀 HUNT FAILED! 💀",
            description=f"{message.author.mention} kalah melawan **{monster['name']}**!",
            color=discord.Color.red()
        )
        # Set monster image if available
        if monster.get('image'):
            embed.set_thumbnail(url=monster['image'])
        embed.add_field(name="🎯 Monster", value=f"**{monster['name']}** (Lv.{monster['level']})\n{monster['description']}", inline=False)
        embed.add_field(name="�  Your Damage", value=f"**{player_damage:,}**", inline=True)
        embed.add_field(name="❤️ Monster HP", value=f"**{monster_hp}**", inline=True)
        embed.add_field(name="� HuP Loss", value=f"**{player_hp_loss}** (Your HP: {total_hp})", inline=False)
        embed.add_field(name="💡 Tips", value="Tingkatkan stat ATK, MDMG, atau HP untuk memenangkan pertarungan!", inline=False)
        embed.add_field(name="📊 Hunt Hari Ini", value=f"**{new_hunt_count}/{MAX_DAILY_HUNT}**", inline=True)
    
    await message.channel.send(embed=embed)

async def handle_setshift_command(message):
    if message.guild is None:
        await message.channel.send("❌ Perintah ini hanya bisa digunakan di server.")
        return

    is_owner = message.author == message.guild.owner
    is_cybersurge = any(role.name.lower() == 'cybersurge' for role in message.author.roles)

    if not (is_owner or is_cybersurge):
        await message.channel.send("❌ Anda tidak memiliki izin (`cybersurge` atau Owner) untuk mengatur shift.")
        return

    parts = message.content.split() # Gunakan split biasa

    if len(parts) < 6:
        await message.channel.send(f"❌ Format: `{prefix}setshift <durasi_menit> <money_reward> <exp_reward> <max_peserta> <Detail_Shift_SATU_KATA_atau_dikutip> [role_1,role_2,...]`")
        await message.channel.send(f"Contoh: \n`{prefix}setshift 120 5000 500 10 Shift_Malam admin,vip`\n`{prefix}setshift 60 1000 100 0 'Shift Standar Harian'`")
        return

    try:
        duration = int(parts[1])
        money_reward = int(parts[2])
        exp_reward = int(parts[3])
        max_participants = int(parts[4])
        if duration <= 0 or money_reward <= 0 or exp_reward <= 0 or max_participants < 0:
             raise ValueError
    except ValueError:
        await message.channel.send("❌ Durasi, Reward Uang, Reward EXP harus positif. Maksimal Peserta harus angka (0 atau lebih).")
        return

    full_command = message.content[len(prefix) + len('setshift'):].strip()

    numeric_parts_len = len(parts[1]) + len(parts[2]) + len(parts[3]) + len(parts[4]) + 4 
    content_start_index = message.content.find(parts[4]) + len(parts[4])
    content_after_numbers = full_command[numeric_parts_len:].strip()

    role_names_input = ""
    shift_detail = "Shift Standar Harian"

    if ',' in content_after_numbers or '@' in content_after_numbers:

        last_arg = parts[-1]

        if ',' in last_arg or '@' in last_arg:
            role_names_input = last_arg.replace('@', '').strip() # Hapus @ jika role mention
            shift_detail = " ".join(parts[5:-1]) # Sisa bagian menjadi detail shift
        else:
             shift_detail = content_after_numbers
             role_names_input = "" 

        last_comma_index = content_after_numbers.rfind(',')
        role_start_index = content_after_numbers.rfind(' ', 0, last_comma_index) 
        
        if role_start_index != -1:
            role_names_input = content_after_numbers[role_start_index + 1:].strip()
            shift_detail = content_after_numbers[:role_start_index].strip()
        else: 
            role_names_input = content_after_numbers.split()[-1]
            shift_detail = " ".join(content_after_numbers.split()[:-1]).strip()

    else:

        shift_detail = content_after_numbers
    
    if shift_detail.startswith(('"', "'")) and shift_detail.endswith(('"', "'")):
        shift_detail = shift_detail[1:-1]
        
    if not shift_detail:
         shift_detail = "Shift Standar Harian"

    required_role_ids = []

    if role_names_input:
            role_names = [name.strip() for name in role_names_input.split(',') if name.strip()]
    for name in role_names:
           role = discord.utils.get(message.guild.roles, check=lambda r: r.name.lower() == name.lower())  # Perbaikan di sini
           
           if role:
               required_role_ids.append(str(role.id))
           else:
               await message.channel.send(f"⚠️ Peringatan: Role Discord `{name}` tidak ditemukan di server ini. Role ini akan diabaikan.")
   
    required_roles_str = ",".join(required_role_ids)
    set_shift_config(message.guild.id, duration, required_roles_str, money_reward, exp_reward, shift_detail, max_participants)

    role_mentions = [message.guild.get_role(int(rid)).mention for rid in required_role_ids if message.guild.get_role(int(rid))]
    roles_display = ", ".join(role_mentions) if role_mentions else "**Semua Role**"

    embed = discord.Embed(
        title="✅ Konfigurasi Shift Diperbarui!",
        description=f"**{shift_detail}**",
        color=discord.Color.blue()
    )
    embed.add_field(name="Durasi", value=f"⏰ **{duration} Menit**", inline=True)
    embed.add_field(name="Reward Total", value=f"💵 **{money_reward:,} ACR** / ✨ **{exp_reward:,} EXP**", inline=True)
    embed.add_field(name="Max Peserta", value=f"👥 **{max_participants}** (0 = Tak Terbatas)", inline=True)
    embed.add_field(name="Role yang Diperlukan", value=roles_display, inline=False)

    await message.channel.send(embed=embed)

async def handle_shift_command(message):
    user_id = message.author.id
    current_time = time.time()
    
    if message.guild is None:
        await message.channel.send("❌ Perintah ini hanya bisa digunakan di server.")
        return

    guild_id = message.guild.id

    config_duration_min, config_roles_str, config_money, config_exp, shift_detail, max_participants = get_shift_config(guild_id)
    active_shift_data = get_active_shift(user_id)

    if active_shift_data:
        start_time, end_time, reward_money, reward_exp = active_shift_data

        if current_time >= end_time:
            # Claim rewards and end shift
            embed = await process_shift_claim(user_id, guild_id, reward_money, reward_exp, config_duration_min, shift_detail, message.author)
            await message.channel.send(embed=embed)
        else:
            # Show remaining time
            time_remaining = end_time - current_time
            minutes = int(time_remaining // 60)
            seconds = int(time_remaining % 60)
            
            embed = discord.Embed(
                title=f"⏳ Shift Sedang Berjalan: {shift_detail}",
                description=f"{message.author.mention}, Shift Anda akan berakhir dalam **{minutes} menit {seconds} detik**.",
                color=discord.Color.orange()
            )
            embed.add_field(name="Durasi", value=f"**{config_duration_min} Menit**", inline=True)
            embed.add_field(name="Waktu Selesai", value=f"⏱️ <t:{int(end_time)}:R>", inline=True)
            embed.add_field(name="Hadiah Target", value=f"💵 **{reward_money:,} ACR**, ✨ **{reward_exp:,} EXP**", inline=False)
            
            await message.channel.send(embed=embed)
    else:
        # Attempt to start a new shift
        if max_participants > 0:
            current_participants = count_active_shifts(guild_id)
            if current_participants >= max_participants:
                 await message.channel.send(f"❌ **Batas Maksimal Shift Terpenuhi!** Shift **{shift_detail}** saat ini memiliki {current_participants}/{max_participants} peserta. Coba lagi nanti.")
                 return

        required_role_ids = [int(rid) for rid in config_roles_str.split(',') if rid]
        can_start = True
        missing_roles_display = ""
        
        if required_role_ids:
            author_role_ids = [role.id for role in message.author.roles]
            if not any(rid in author_role_ids for rid in required_role_ids):
                 role_mentions = [message.guild.get_role(rid).mention for rid in required_role_ids if message.guild.get_role(rid)]
                 missing_roles_display = ", ".join(role_mentions)
                 can_start = False
        
        if not can_start:
            await message.channel.send(f"❌ Anda tidak dapat memulai shift ini! Diperlukan salah satu dari role berikut: {missing_roles_display}.")
            return

        start_time = current_time
        end_time = current_time + (config_duration_min * 60)
        
        start_new_shift(user_id, start_time, end_time, config_money, config_exp, shift_detail)
        
        roles_display = ", ".join([message.guild.get_role(rid).mention for rid in required_role_ids if message.guild.get_role(rid)]) if required_role_ids else "**Semua Role**"

        embed = discord.Embed(
            title=f"▶️ Shift Dimulai: {shift_detail}!",
            description=f"{message.author.mention}, Anda memulai Shift selama **{config_duration_min} menit**.",
            color=discord.Color.green()
        )
        embed.add_field(name="Durasi Shift", value=f"⏰ **{config_duration_min} Menit**", inline=True)
        embed.add_field(name="Waktu Selesai", value=f"⏱️ <t:{int(end_time)}:F> (<t:{int(end_time)}:R>)", inline=True)
        embed.add_field(name="Target Hadiah", value=f"💵 **{config_money:,} ACR**, ✨ **{config_exp:,} EXP**", inline=False)
        
        if max_participants > 0:
            current_participants = count_active_shifts(guild_id)
            embed.add_field(name="Peserta Saat Ini", value=f"👥 **{current_participants}/{max_participants}**", inline=True)
            
        embed.add_field(name="Role Persyaratan", value=roles_display, inline=False)

        await message.channel.send(embed=embed)
    
async def process_shift_claim(user_id, guild_id, reward_money, reward_exp, duration_min, shift_detail, member=None):
    
    end_active_shift(user_id)
    
    user_data = get_user_data(user_id)
    (exp, level, money, last_daily_str, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset) = user_data
    
    new_exp = exp + reward_exp
    new_money = money + reward_money

    lvl_up_message = ""
    required_exp = required_exp_for_level(level)

    while new_exp >= required_exp:
        level += 1
        new_exp -= required_exp
        required_exp = required_exp_for_level(level)
        
        stat_to_boost = random.choice(['atk', 'spd', 'def', 'dex', 'crit', 'mdmg'])
        
        if stat_to_boost == 'atk': atk += 5
        elif stat_to_boost == 'spd': spd += 5
        elif stat_to_boost == 'def': def_stat += 5
        elif stat_to_boost == 'dex': dex += 5
        elif stat_to_boost == 'crit': crit += 5
        elif stat_to_boost == 'mdmg': mdmg += 5
        
        stat_upper = stat_to_boost.upper()
        
        if stat_upper == 'ATK': stat_value_string = f"⚔️ **{stat_upper}**: 5↑"
        elif stat_upper == 'SPD': stat_value_string = f"👟 **{stat_upper}**: 5↑"
        elif stat_upper == 'DEF': stat_value_string = f"🛡️ **{stat_upper}**: 5↑"
        elif stat_upper == 'DEX': stat_value_string = f"🎯 **{stat_upper}**: 5↑"
        elif stat_upper == 'CRIT': stat_value_string = f"💥 **{stat_upper}**: 5↑"
        elif stat_upper == 'MDMG': stat_value_string = f"⚛️ **{stat_upper}**: 5↑"
        else: stat_value_string = f"**{stat_upper}**: 5↑" 
        
        lvl_up_message += f"🎉 **LEVEL UP** ke **Level {level}** (Bonus: {stat_value_string})!\n"
        
    update_full_user_data(user_id, new_exp, level, new_money, last_daily_str, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset)

    user_mention = member.mention if member else f"<@{user_id}>"

    embed = discord.Embed(
        title=f"✅ Shift Selesai! (Reward Klaim) - {shift_detail}",
        description=f"{user_mention}, Anda telah menyelesaikan shift **{shift_detail}** selama **{duration_min} menit**!",
        color=discord.Color.green()
    )
    embed.add_field(name="Hadiah Diterima", value=f"💵 **{reward_money:,} ACR**, ✨ **{reward_exp:,} EXP**", inline=False)
    if lvl_up_message:
        embed.add_field(name="Level Up!", value=lvl_up_message, inline=False)
    embed.add_field(name="Total Uang Terbaru", value=f"💵 **{new_money:,} ACR**", inline=True)

    return embed

async def handle_finishshift_admin(message):
    if message.guild is None:
        await message.channel.send("❌ Perintah ini hanya bisa digunakan di server.")
        return

    is_owner = message.author == message.guild.owner
    is_cybersurge = any(role.name.lower() == 'cybersurge' for role in message.author.roles)

    if not (is_owner or is_cybersurge):
        await message.channel.send("❌ Anda tidak memiliki izin (`cybersurge` atau Owner) untuk menggunakan perintah ini.")
    return

    if not message.mentions:
        await message.channel.send(f"❌ Format: `{prefix}finishshift <@user>`. Anda harus menyebutkan pengguna yang ingin diklaimkan rewardnya.")
    return

    target_member = message.mentions[0]
    user_id = target_member.id
    current_time = time.time()

    active_shift_data = get_active_shift(user_id)

    if not active_shift_data:
        await message.channel.send(f"❌ {target_member.mention} tidak sedang dalam shift aktif!")
        return


    start_time, end_time, reward_money, reward_exp, shift_detail = active_shift_data

    config_duration_min, _, _, _, config_shift_detail, _ = get_shift_config(message.guild.id)

    if current_time < end_time:
        time_remaining = end_time - current_time
        minutes = int(time_remaining // 60)
        seconds = int(time_remaining % 60)
        await message.channel.send(f"⚠️ **Peringatan Admin:** Shift {target_member.mention} masih berjalan (**{minutes}m {seconds}d** tersisa), tetapi Admin memaksa klaim.")

    embed = await process_shift_claim(user_id, message.guild.id, reward_money, reward_exp, config_duration_min, shift_detail, target_member)
    await message.channel.send(embed=embed)

async def handle_help_command(message):
    prefix = 'ag!' 
    help_text = f"""
    **{prefix}stat** atau **{prefix}level** [opsional: @user]
    > Melihat semua statistik (termasuk DEX, CRIT, MDMG, HP, MP).
    
    **{prefix}daily**
    > Klaim hadiah uang harian.

    **{prefix}roll** atau **{prefix}dice**
    > Melempar dadu untuk hadiah uang. Jatah: {MAX_DAILY_DICE}x per hari.
    
    **{prefix}hunt**
    > Berburu monster untuk mendapatkan EXP dan Gold. Jatah: {MAX_DAILY_HUNT}x per hari.
    
    **{prefix}fight <@user>**
    > Bertarung melawan pemain lain. Cooldown: {int(FIGHT_COOLDOWN/60)} menit.
    
    **{prefix}leaderboard**
    > Menampilkan 10 pemain teratas.
    
    **{prefix}buy** [kategori] [item/role] & **{prefix}shop** [weapon/armor/role]
    > Menu dan daftar item/role di toko.
    
    **{prefix}inventory**
    > Melihat item yang Anda miliki (Slot: 10 item unik).
    
    **{prefix}equip <Item_Name>**
    > Equip item dari inventaris (cth:, `{prefix}equip Iron Sword`).

    **{prefix}unequip <Item_Name>**
    > Lepas item yang di-equip (cth:, `{prefix}unequip Iron Sword`).

    **{prefix}upgrade <stat> <amount>**
    > Tingkatkan stat dengan uang ({STAT_UPGRADE_COST} ACR per poin).
    > Stat yang dapat di-upgrade: `atk`, `spd`, `def`, `dex`, `crit`, `mdmg`, `hp`, `mp`.
    
    **{prefix}sell <Item_Name> <Jumlah>**
    > Jual item Anda (50% harga beli).

    **{prefix}givemoney <@user> <amount>**
    > Kirim sejumlah uang (ACR) kepada pengguna lain

    **{prefix}shift**
    > Memulai Shift, melihat progres, dan klaim hadiah Shift.
    
    **KHUSUS CYBERHELPER DAN OWNER**
    **{prefix}setshift <durasi> <money> <exp> <max_peserta> <Detail_Shift> [role_1,role_2,...]**
    > Mengatur konfigurasi shift

    **{prefix}finishshift <@user>**
    > **[NEW]** Memaksa klaim reward shift untuk pengguna yang ditandai, *terlepas apakah waktu shift mereka sudah berakhir atau belum*
    
    **{prefix}help**
    > Menampilkan daftar perintah ini.
"""
    embed = discord.Embed(
        title="📚 Bantuan Komando Aetherion Game",
        description=help_text,
        color=discord.Color.red()
    )
    await message.channel.send(embed=embed)

async def handle_stat_command(message, target_user):
    user_id = target_user.id

    user_data = get_user_data(user_id)

    current_exp, current_level, current_currency, _, base_atk, base_spd, base_def, base_dex, base_crit, base_mdmg, base_hp, base_mp, max_slots, equipped_weapon, equipped_armor, *_, _ = user_data

    total_atk, total_spd, total_def, total_dex, total_crit, total_mdmg, total_hp, total_mp = get_total_stats(user_id)

    required_exp = required_exp_for_level(current_level)
    progress_bar_length = 10
    
    exp_in_level = current_exp
    exp_needed = required_exp
    ratio = exp_in_level / exp_needed if exp_needed > 0 else 1.0 
    filled = int(ratio * progress_bar_length)
    unfilled = progress_bar_length - filled
    progress_bar = f"[{'█' * filled}{'░' * unfilled}]"

    embed = discord.Embed(
        title=f"📊 Stats {target_user.display_name} 📊", 
        color=discord.Color.blurple()
    )
    
    embed.add_field(name="Level", value=f"**{current_level}**", inline=True)
    embed.add_field(name="Money", value=f"💵 **{current_currency:,} ACR**", inline=True)
    embed.add_field(name="EXP", value=f"{current_exp} / {required_exp}", inline=False)
    
    embed.add_field(name="HP", value=f"❤️ {base_hp} ({total_hp - base_hp}) = **{total_hp}**", inline=True)
    embed.add_field(name="MP", value=f"🌀 {base_mp} ({total_mp - base_mp}) = **{total_mp}**", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)

    embed.add_field(name="ATK", value=f"⚔️ {base_atk} ({total_atk - base_atk}) = **{total_atk}**", inline=True)
    embed.add_field(name="DEF", value=f"🛡️ {base_def} ({total_def - base_def}) = **{total_def}**", inline=True)
    embed.add_field(name="SPD", value=f"👟 {base_spd} ({total_spd - base_spd}) = **{total_spd}**", inline=True)
    
    embed.add_field(name="DEX", value=f"🎯 {base_dex} ({total_dex - base_dex}) = **{total_dex}**", inline=True)
    embed.add_field(name="CRIT", value=f"💥 {base_crit} ({total_crit - base_crit}) = **{total_crit}%**", inline=True)
    embed.add_field(name="MDMG", value=f"⚛️ {base_mdmg} ({total_mdmg - base_mdmg}) = **{total_mdmg}**", inline=True)

    embed.add_field(name="Title", value=f"{target_user.top_role.mention}", inline=False)
    embed.add_field(name="Arrived on", value=f"{target_user.joined_at.strftime('%Y-%b-%d')}", inline=False)

    embed.add_field(name="Progress", value=f"{progress_bar} ({ratio*100:.2f}%)", inline=False)
    
    embed.set_thumbnail(url=target_user.display_avatar.url)
    await message.channel.send(embed=embed)

async def handle_leaderboard_command(message):
    leaderboard_data = get_leaderboard_data()
    if not leaderboard_data:
        await message.channel.send("❌ Leaderboard kosong. Kirim pesan untuk mulai mendapatkan EXP!")
        return
    user_map = {}
    for user_id, _, _, _ in leaderboard_data:
        try:
            user = await bot.fetch_user(user_id) 
            user_map[user_id] = user.name
        except discord.NotFound:
            user_map[user_id] = f"User Dihapus" 
        except Exception:
            user_map[user_id] = f"Error Nama"
    def get_display_width(text):
        width = 0
        for char in text:
            if ord(char) > 127: 
                width += 2
            else:
                width += 1
        return width
    max_name_len = max(get_display_width(name) for name in user_map.values())
    NAME_WIDTH = max(max_name_len + 1, 6) 
    RANK_WIDTH = 4 
    LVL_WIDTH = 3 
    EXP_WIDTH = 4 
    max_money_len = max(len(f"{money:,}") for _, _, _, money in leaderboard_data)
    MONEY_WIDTH = max(max_money_len, 5) 
    header_rank = "RANK".center(RANK_WIDTH)
    header_name = "NAMA".ljust(NAME_WIDTH)
    header_lvl = "LVL".center(LVL_WIDTH)
    header_exp = "EXP".center(EXP_WIDTH)
    header_money = "MONEY".center(MONEY_WIDTH) 
    header_line_1 = f"{header_rank}│{header_name}│{header_lvl}│{header_exp}│{header_money}"
    line_rank = "═" * RANK_WIDTH
    line_name = "═" * NAME_WIDTH
    line_lvl = "═" * LVL_WIDTH
    line_exp = "═" * EXP_WIDTH
    line_money = "═" * MONEY_WIDTH
    header_line_2 = f"{line_rank}╪{line_name}╪{line_lvl}╪{line_exp}╪{line_money}"
    combined_list = [header_line_1, header_line_2]
    for index, (user_id, level, exp, money) in enumerate(leaderboard_data):
        username = user_map.get(user_id, "User Dihapus")
        rank = index + 1
        name_padding_needed = NAME_WIDTH - get_display_width(username)
        name_str = username + (" " * name_padding_needed)
        rank_str = f"{rank}.".ljust(RANK_WIDTH) 
        lvl_str = f"{level:02}".rjust(LVL_WIDTH)
        exp_str = f"{exp:03}".rjust(EXP_WIDTH)
        money_str = f"{money:,}".rjust(MONEY_WIDTH)
        combined_line = (
            f"{rank_str}│{name_str}│{lvl_str}│{exp_str}│{money_str}"
        )
        combined_list.append(combined_line)
    final_content = "\n".join(combined_list)
    embed = discord.Embed(
        title="🏆 TOP 10 LEADERBOARD! 🏆",
        color=discord.Color.purple()
    )
    embed.add_field(name="TOP 10 Berdasarkan Level, EXP, dan ACR", 
                     value=f"```fix\n{final_content}\n```",
                     inline=False)
    await message.channel.send(embed=embed)

async def handle_daily_command(message):
    user_id = message.author.id
    user_data = get_user_data(user_id)
    current_exp, current_level, current_currency, last_daily_str, atk, spd, def_stat, dex, crit, mdmg, hp, mp, inventory_slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset = user_data
    
    today = datetime.date.today()
    last_daily = datetime.datetime.strptime(last_daily_str, '%Y-%m-%d').date()
    
    if today > last_daily:
        DAILY_REWARD_AMOUNT = random.randint(500, 2000)
        current_currency += DAILY_REWARD_AMOUNT
        new_last_daily_str = today.strftime('%Y-%m-%d')
        update_full_user_data(user_id, current_exp, current_level, current_currency, new_last_daily_str, atk, spd, def_stat, dex, crit, mdmg, hp, mp, inventory_slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset)
        
        await message.channel.send(
            f"✅ **Claimmed!** {message.author.mention}, Anda mendapatkan ** 💵 {DAILY_REWARD_AMOUNT:,} ACR** harian! "
            f"Total Uang Anda sekarang: **{current_currency:,}**."
        )
    else:
        tomorrow = today + datetime.timedelta(days=1)
        waktu_sekarang = datetime.datetime.now()
        tengah_malam = datetime.datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0)
        sisa_waktu = tengah_malam - waktu_sekarang
        jam = int(sisa_waktu.total_seconds() // 3600)
        menit = int((sisa_waktu.total_seconds() % 3600) // 60)
        await message.channel.send(
            f"⊹ ࣪ ﹏𓊝﹏𓂁﹏⊹ ࣪ ˖**Tunggu Sebentar {message.author.mention}~ ⊹ ࣪ ﹏𓊝﹏𓂁﹏⊹ ࣪ ˖** \n, Anda sudah mengklaim hadiah harian hari ini\n"
            f" ⊹ ࣪ ﹏𓊝﹏𓂁﹏⊹ Silahkan klaim lagi dalam **{jam} jam {menit} menit**. ⊹ ࣪ ﹏𓊝﹏𓂁﹏⊹ ࣪ ˖"
        )

db_setup()

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id
    current_time = time.time()
    last_exp_time = user_exp_cooldown.get(user_id, 0)
    
    if current_time - last_exp_time >= EXP_COOLDOWN:

        user_data = get_user_data(user_id)
        current_exp, current_level, current_currency, last_daily_str, atk, spd, def_stat, dex, crit, mdmg, hp, mp, inventory_slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset = user_data
        
        exp_gain = random.randint(EXP_PER_MESSAGE_MIN, EXP_PER_MESSAGE_MAX)
        current_exp += exp_gain
        
        user_exp_cooldown[user_id] = current_time

        required_exp = required_exp_for_level(current_level)
        
        while current_exp >= required_exp:
            current_level += 1
            current_exp -= required_exp 
            required_exp = required_exp_for_level(current_level) 
            
            reward = current_level * 200 
            current_currency += reward
            
            stat_to_boost = random.choice(['atk', 'spd', 'def', 'dex', 'crit', 'mdmg'])
            
            if stat_to_boost == 'atk': atk += 5
            elif stat_to_boost == 'spd': spd += 5
            elif stat_to_boost == 'def': def_stat += 5
            elif stat_to_boost == 'dex': dex += 5
            elif stat_to_boost == 'crit': crit += 5
            elif stat_to_boost == 'mdmg': mdmg += 5
            
            stat_upper = stat_to_boost.upper()

            if stat_upper == 'ATK': stat_value_string = f"⚔️ **{stat_upper}**: 5↑"
            elif stat_upper == 'SPD': stat_value_string = f"👟 **{stat_upper}**: 5↑"
            elif stat_upper == 'DEF': stat_value_string = f"🛡️ **{stat_upper}**: 5↑"
            elif stat_upper == 'DEX': stat_value_string = f"🎯 **{stat_upper}**: 5↑"
            elif stat_upper == 'CRIT': stat_value_string = f"💥 **{stat_upper}**: 5↑"
            elif stat_upper == 'MDMG': stat_value_string = f"⚛️ **{stat_upper}**: 5↑"
            else: stat_value_string = f"**{stat_upper}**: 5↑" 

            embed = discord.Embed(
                title=f"Level Up Berhasil! (Level {current_level})",
                description=f"🎉 **{message.author.mention}** telah mencapai **Level {current_level}**",
                color=discord.Color.blue()
            )

            embed.set_author(name=f"{message.author.display_name} | Naik Level!")
            embed.set_thumbnail(url=message.author.display_avatar.url)
            embed.add_field(name="Reward", value=f"**💵 {reward:,} ACR**", inline=False)
            embed.add_field(name="Stat up!", value=stat_value_string, inline=False)
            
            await message.channel.send(embed=embed)

        update_full_user_data(user_id, current_exp, current_level, current_currency, last_daily_str, atk, spd, def_stat, dex, crit, mdmg, hp, mp, inventory_slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset) 
        
    msg_lower_parts = message.content.lower().split()
    if not msg_lower_parts:
        return
        
    command = msg_lower_parts[0]
    
    if command == f'{prefix}buy':
        if len(msg_lower_parts) == 1:
            await handle_buy_menu(message)
        elif len(msg_lower_parts) >= 2:
            item_type = msg_lower_parts[1]
            if item_type in ['weapon', 'armor']:
                if len(msg_lower_parts) == 2:
                    await handle_list_command(message, item_type) 
                else: 
                    await handle_buy_item_command(message, item_type)
            elif item_type == 'role':
                if len(msg_lower_parts) == 2:
                    await handle_list_command(message, item_type)
                else:
                    await handle_buy_role_command(message)
            else:
                await message.channel.send(f"❌ Kategori pembelian tidak valid: `{item_type}`. Gunakan `weapon`, `armor`, atau `role`.")

    elif command == f'{prefix}shop' or command == f'{prefix}list':
        if len(msg_lower_parts) < 2:
            await handle_buy_menu(message)
            return
        
        item_type = msg_lower_parts[1]
        if item_type in ['weapon', 'armor', 'role']: 
            await handle_list_command(message, item_type)
        else:
            await message.channel.send(f"❌ Tipe item/kategori tidak valid: `{item_type}`. Gunakan `weapon`, `armor`, atau `role`.")
    
    elif command in [f'{prefix}level', f'{prefix}stat']:
        target = message.author
        if message.mentions:
            target = message.mentions[0]
        await handle_stat_command(message, target)
        
    elif command == f'{prefix}daily':
        await handle_daily_command(message)
    elif command == f'{prefix}leaderboard':
        await handle_leaderboard_command(message)
    elif command == f'{prefix}help':
        await handle_help_command(message) 
    elif command == f'{prefix}inventory':
        await handle_inventory_command(message)
    elif command == f'{prefix}equip':
        await handle_equip_command(message)
    elif command == f'{prefix}unequip':
        await handle_unequip_command(message)
    elif command == f'{prefix}upgrade':
        await handle_upgrade_command(message)
    elif command == f'{prefix}sell': 
        await handle_sell_command(message)
    elif command == f'{prefix}roll' or command == f'{prefix}dice': 
        await handle_dice_command(message)
    elif command == f'{prefix}fight': 
        await handle_fight_command(message)
    elif command == f'{prefix}givemoney':
        await handle_givemoney_command(message)
    elif command == f'{prefix}hunt':
        await handle_hunt_command(message)
    elif command == f'{prefix}setshift':
        await handle_setshift_command(message)
    elif command == f'{prefix}shift':
        await handle_shift_command(message)
    elif command == f'{prefix}finishshift':
        await handle_finishshift_admin(message)

bot.run(token)