"""
Aetherion Game Bot - MySQL Version
Migrasi dari SQLite ke MySQL
"""
import discord
import random
import datetime
import time
import asyncio
import logging
import os
import json
from dotenv import load_dotenv
from database.connection import get_connection, execute_query

load_dotenv()
logging.basicConfig(level=logging.INFO)

token = os.getenv('DISCORD_TOKEN')
prefix = 'ag!'

EXP_COOLDOWN = 60
EXP_PER_MESSAGE_MIN = 10
EXP_PER_MESSAGE_MAX = 50

MAX_DAILY_DICE = 5
DICE_COSTS = [0, 200, 400, 600, 800] 
DICE_BASE_REWARD = 300 

FIGHT_COOLDOWN = 10 * 60
FIGHT_COST_MIN = 500
FIGHT_COST_MAX = 500

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

# ============== DATABASE FUNCTIONS (MySQL) ==============

def get_user_data(user_id):
    query = '''SELECT exp, level, Money, last_daily_claim, ATK, SPD, DEF, DEX, CRIT, MDMG, HP, MP, 
               inventory_slots, equipped_weapon, equipped_armor, dice_rolls_today, last_dice_reset, 
               last_fight_time, hunt_count_today, last_hunt_reset 
               FROM users WHERE user_id = %s'''
    data = execute_query(query, (user_id,), fetch_one=True)
    
    if data is None:
        return 0, 1, 0, '2000-01-01', 5, 5, 5, 5, 5, 5, 100, 50, 10, None, None, 0, '2000-01-01', 0.0, 0, '2000-01-01'
    return data

def update_full_user_data(user_id, exp, level, Money, last_daily_claim, ATK, SPD, DEF, DEX, CRIT, MDMG, HP, MP, inventory_slots, equipped_weapon=None, equipped_armor=None, dice_rolls_today=0, last_dice_reset='2000-01-01', last_fight_time=0.0, hunt_count_today=0, last_hunt_reset='2000-01-01'):
    query = '''INSERT INTO users 
               (user_id, exp, level, Money, last_daily_claim, ATK, SPD, DEF, DEX, CRIT, MDMG, HP, MP, 
                inventory_slots, equipped_weapon, equipped_armor, dice_rolls_today, last_dice_reset, 
                last_fight_time, hunt_count_today, last_hunt_reset) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON DUPLICATE KEY UPDATE
               exp=%s, level=%s, Money=%s, last_daily_claim=%s, ATK=%s, SPD=%s, DEF=%s, DEX=%s, 
               CRIT=%s, MDMG=%s, HP=%s, MP=%s, inventory_slots=%s, equipped_weapon=%s, equipped_armor=%s,
               dice_rolls_today=%s, last_dice_reset=%s, last_fight_time=%s, hunt_count_today=%s, last_hunt_reset=%s'''
    
    params = (user_id, exp, level, Money, last_daily_claim, ATK, SPD, DEF, DEX, CRIT, MDMG, HP, MP,
              inventory_slots, equipped_weapon, equipped_armor, dice_rolls_today, last_dice_reset,
              last_fight_time, hunt_count_today, last_hunt_reset,
              exp, level, Money, last_daily_claim, ATK, SPD, DEF, DEX, CRIT, MDMG, HP, MP,
              inventory_slots, equipped_weapon, equipped_armor, dice_rolls_today, last_dice_reset,
              last_fight_time, hunt_count_today, last_hunt_reset)
    
    execute_query(query, params)

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
    query = 'SELECT user_id, level, exp, Money FROM users ORDER BY level DESC, exp DESC, Money DESC LIMIT 10'
    return execute_query(query, fetch_all=True)

def get_user_inventory(user_id):
    query = 'SELECT item_name, quantity FROM inventory WHERE user_id = %s AND quantity > 0'
    return execute_query(query, (user_id,), fetch_all=True)

def get_shop_items(item_type):
    query = 'SELECT name, price, bonus_atk, bonus_def, bonus_spd, bonus_dex, bonus_crit, bonus_mdmg, bonus_hp, bonus_mp FROM items WHERE type = %s ORDER BY price ASC'
    return execute_query(query, (item_type,), fetch_all=True)

def get_item_details(item_name_with_underscore):
    query = 'SELECT item_id, name, type, price, bonus_atk, bonus_def, bonus_spd, bonus_dex, bonus_crit, bonus_mdmg, bonus_hp, bonus_mp FROM items WHERE LOWER(name) = LOWER(%s)'
    return execute_query(query, (item_name_with_underscore,), fetch_one=True)


def update_inventory(user_id, item_name_with_underscore, quantity_change):
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
    return tuple(total_stats)

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
        else:
            cost_per_point = STAT_TIER_4_COST
        total_cost += cost_per_point
    return total_cost

def get_shop_roles():
    query = 'SELECT role_id, name, price FROM roles ORDER BY price ASC'
    return execute_query(query, fetch_all=True)

def get_role_details(role_name):
    query = 'SELECT role_id, name, price FROM roles WHERE LOWER(name) = LOWER(%s)'
    return execute_query(query, (role_name,), fetch_one=True)

def update_user_money(user_id, amount_change):
    user_data = get_user_data(user_id)
    (exp, level, current_money, last_daily_str, atk, spd, def_stat, dex, crit, mdmg, hp, mp, 
     inventory_slots, equipped_weapon, equipped_armor, dice_rolls_today, last_dice_reset, 
     last_fight_time, hunt_count, hunt_reset) = user_data
    
    new_money = max(0, current_money + amount_change)
    update_full_user_data(user_id, exp, level, new_money, last_daily_str, atk, spd, def_stat, 
                          dex, crit, mdmg, hp, mp, inventory_slots, equipped_weapon, equipped_armor, 
                          dice_rolls_today, last_dice_reset, last_fight_time, hunt_count, hunt_reset)
    return new_money

def get_shift_config(guild_id):
    query = 'SELECT duration_minutes, required_role_ids, reward_money, reward_exp, shift_detail, max_participants FROM shift_config WHERE guild_id = %s'
    data = execute_query(query, (guild_id,), fetch_one=True)
    
    if data is None:
        return 60, '', 1000, 100, 'Shift Standar Harian', 0
    return int(data[0]), data[1] or '', int(data[2]), int(data[3]), data[4] or 'Shift Standar Harian', int(data[5])

def set_shift_config(guild_id, duration, required_roles_str, money, exp, detail, max_p):
    query = '''INSERT INTO shift_config (guild_id, duration_minutes, required_role_ids, reward_money, reward_exp, shift_detail, max_participants) 
               VALUES (%s, %s, %s, %s, %s, %s, %s)
               ON DUPLICATE KEY UPDATE
               duration_minutes=%s, required_role_ids=%s, reward_money=%s, reward_exp=%s, shift_detail=%s, max_participants=%s'''
    execute_query(query, (guild_id, duration, required_roles_str, money, exp, detail, max_p,
                          duration, required_roles_str, money, exp, detail, max_p))

def get_active_shift(user_id):
    query = 'SELECT start_time, end_time, reward_money, reward_exp, shift_detail FROM active_shifts WHERE user_id = %s'
    return execute_query(query, (user_id,), fetch_one=True)

def start_new_shift(user_id, start_time, end_time, money, exp, detail):
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
    execute_query('DELETE FROM active_shifts WHERE user_id = %s', (user_id,))

def count_active_shifts(guild_id):
    result = execute_query('SELECT COUNT(*) FROM active_shifts', fetch_one=True)
    return result[0] if result else 0

def load_monsters():
    try:
        with open('monsters.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('monsters', [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def get_monster_for_level(player_level):
    monsters = load_monsters()
    if not monsters:
        return None
    suitable_monsters = [m for m in monsters if m['level'] <= min(player_level + 2, 10)]
    if not suitable_monsters:
        suitable_monsters = [monsters[0]]
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


# ============== COMMAND HANDLERS ==============
# (Sama dengan versi SQLite, hanya database functions yang berbeda)

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
        if amount <= 0: raise ValueError
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

async def handle_buy_menu(message):
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
    parts = message.content.lower().split()
    if len(parts) < 3:
        await message.channel.send(f"❌ Format: `{prefix}buy {item_type} <Item_Name>`")
        return
        
    item_name_raw = " ".join(parts[2:])
    item_name_db = item_name_raw.replace(' ', '_')
    details = get_item_details(item_name_db)
    
    if not details:
        await message.channel.send(f"❌ Item `{item_name_raw}` tidak ditemukan!")
        return
        
    item_id, name_db, item_db_type, price, *_ = details
    if item_db_type != item_type:
        await message.channel.send(f"❌ `{name_db.replace('_', ' ')}` adalah {item_db_type.upper()}, bukan {item_type.upper()}.")
        return

    user_data = get_user_data(user_id)
    exp, level, current_currency, last_daily_str, atk, spd, def_stat, dex, crit, mdmg, hp, mp, max_slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset = user_data
    
    if current_currency < price:
        await message.channel.send(f"❌ Uang tidak cukup! Butuh **💵 {price:,} ACR**.")
        return
        
    inventory_items = get_user_inventory(user_id)
    total_unique_items = len(inventory_items)
    is_new_item = name_db not in [item[0] for item in inventory_items]
    
    if total_unique_items >= max_slots and is_new_item:
        await message.channel.send(f"❌ Inventaris penuh!")
        return
        
    new_currency = current_currency - price
    update_inventory(user_id, name_db, 1)
    update_full_user_data(user_id, exp, level, new_currency, last_daily_str, atk, spd, def_stat, dex, crit, mdmg, hp, mp, max_slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset)
    
    await message.channel.send(f"✅ {message.author.mention} membeli **{name_db.replace('_', ' ')}** seharga **💵 {price:,} ACR**. Sisa: **💵 {new_currency:,} ACR**.")

async def handle_buy_role_command(message):
    user_id = message.author.id
    parts = message.content.lower().split()
    if len(parts) < 3:
        await message.channel.send(f"❌ Format: `{prefix}buy role <Role_Name>`")
        return
        
    role_name_raw = " ".join(parts[2:])
    role_name = role_name_raw.title()
    details = get_role_details(role_name)
    
    if not details:
        await message.channel.send(f"❌ Role `{role_name}` tidak ditemukan!")
        return
        
    role_discord_id, role_db_name, price = details
    user_data = get_user_data(user_id)
    exp, level, current_currency, last_daily_str, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset = user_data

    if current_currency < price:
        await message.channel.send(f"❌ Uang tidak cukup! Butuh **💵 {price:,} ACR**.")
        return
        
    try:
        guild = message.guild
        if guild is None:
            await message.channel.send("❌ Hanya bisa di server.")
            return
            
        role_to_give = guild.get_role(role_discord_id)
        if role_to_give is None:
            await message.channel.send(f"❌ Role tidak ditemukan di server.")
            return
            
        if role_to_give in message.author.roles:
            await message.channel.send(f"❌ Anda sudah memiliki role **{role_db_name}**!")
            return
            
        new_currency = current_currency - price
        await message.author.add_roles(role_to_give)
        update_full_user_data(user_id, exp, level, new_currency, last_daily_str, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset)
        await message.channel.send(f"🎉 {message.author.mention} membeli role **{role_db_name}** seharga **💵 {price:,} ACR**!")
    except discord.Forbidden:
        await message.channel.send("❌ Bot tidak punya izin memberikan role.")

async def handle_sell_command(message):
    user_id = message.author.id
    parts = message.content.lower().split()
    if len(parts) < 3:
        await message.channel.send(f"❌ Format: `{prefix}sell <Item_Name> <Jumlah>`")
        return
        
    try:
        amount = int(parts[-1])
        if amount <= 0: raise ValueError
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
        await message.channel.send(f"❌ Anda tidak punya cukup `{item_name_raw}`.")
        return

    user_data = get_user_data(user_id)
    exp, level, money, last_daily, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset = user_data
    
    total_revenue = amount * sell_price
    new_currency = money + total_revenue
    
    update_inventory(user_id, name_db, -amount)
    update_full_user_data(user_id, exp, level, new_currency, last_daily, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset)
    
    await message.channel.send(f"✅ {message.author.mention} menjual **{amount}x {name_db.replace('_', ' ')}** seharga **💵 {total_revenue:,} ACR**.")


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
        await message.channel.send(f"❌ Format: `{prefix}fight <@user>`")
        return
    
    attacker = message.author
    target_member = message.mentions[0]
    target_id = target_member.id

    if target_member.bot:
        await message.channel.send("❌ Tidak bisa melawan bot!")
        return

    player_data = get_user_data(user_id)
    p_last_fight = player_data[17]
    time_remaining = FIGHT_COOLDOWN - (current_time - p_last_fight)

    if time_remaining > 0:
        minutes = int(time_remaining // 60)
        seconds = int(time_remaining % 60)
        await message.channel.send(f"⏳ Cooldown! Tunggu {minutes}m {seconds}s.")
        return
        
    fight_cost = random.randint(FIGHT_COST_MIN, FIGHT_COST_MAX)
    if player_data[2] < fight_cost:
        await message.channel.send(f"❌ Butuh **💵 {fight_cost:,} ACR** untuk bertarung.")
        return
    
    # Challenge embed
    embed = discord.Embed(title="⚔️ TANTANGAN PVP ⚔️", description=f"{target_member.mention}, Anda ditantang oleh **{attacker.display_name}**!\nBiaya: **💵 {fight_cost:,} ACR**\n✅ Terima | ❌ Tolak", color=discord.Color.orange())
    challenge_msg = await message.channel.send(embed=embed)
    await challenge_msg.add_reaction('✅')
    await challenge_msg.add_reaction('❌')

    def check(reaction, user):
        return user.id == target_id and str(reaction.emoji) in ['✅', '❌'] and reaction.message.id == challenge_msg.id

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)
    except asyncio.TimeoutError:
        await message.channel.send(f"⏳ {target_member.mention} tidak merespon.")
        return
        
    if str(reaction.emoji) == '❌':
        await message.channel.send(f"🛡️ {target_member.mention} menolak tantangan.")
        return

    # Battle calculation
    p_total = get_total_stats(user_id)
    t_total = get_total_stats(target_id)
    
    p_power = (p_total[0] * 0.4) + (p_total[5] * 0.2) + (p_total[2] * 0.1) + (p_total[1] * 0.1) + player_data[1] * 10
    t_power = (t_total[0] * 0.4) + (t_total[5] * 0.2) + (t_total[2] * 0.1) + (t_total[1] * 0.1)
    
    p_power *= random.uniform(0.9, 1.1)
    t_power *= random.uniform(0.9, 1.1)
    
    winner = attacker if p_power > t_power else target_member
    loser = target_member if p_power > t_power else attacker

    bonus_exp = random.randint(FIGHT_BONUS_EXP_MIN, FIGHT_BONUS_EXP_MAX)
    bonus_money = random.randint(FIGHT_BONUS_MONEY_MIN, FIGHT_BONUS_MONEY_MAX)

    # Update winner/loser data
    target_data = get_user_data(target_id)
    stolen_amount = random.randint(int(target_data[2] * 0.1), int(target_data[2] * 0.5))

    if winner.id == user_id:
        # Attacker wins
        p_data = list(get_user_data(user_id))
        p_data[2] = p_data[2] - fight_cost + stolen_amount + bonus_money
        p_data[0] += bonus_exp
        p_data[17] = current_time
        update_full_user_data(user_id, *p_data)
        
        t_data = list(get_user_data(target_id))
        t_data[2] -= stolen_amount
        update_full_user_data(target_id, *t_data)
    else:
        # Target wins
        t_data = list(get_user_data(target_id))
        t_data[2] += stolen_amount + bonus_money
        t_data[0] += bonus_exp
        t_data[17] = current_time
        update_full_user_data(target_id, *t_data)
        
        p_data = list(get_user_data(user_id))
        p_data[2] = p_data[2] - fight_cost - stolen_amount
        p_data[17] = current_time
        update_full_user_data(user_id, *p_data)

    embed = discord.Embed(title="⚔️ Hasil PVP ⚔️", color=discord.Color.green() if winner.id == user_id else discord.Color.red())
    embed.add_field(name="Pemenang", value=f"👑 **{winner.display_name}**", inline=True)
    embed.add_field(name="Kalah", value=f"💀 {loser.display_name}", inline=True)
    embed.add_field(name="Uang Diambil", value=f"💵 **{stolen_amount:,} ACR**", inline=False)
    await message.channel.send(embed=embed)

async def handle_givemoney_command(message):
    user_id = message.author.id
    parts = message.content.lower().split()

    if len(parts) < 3 or not message.mentions or message.mentions[0].id == user_id:
        await message.channel.send(f"❌ Format: `{prefix}givemoney <@user> <amount>`")
        return

    target_user = message.mentions[0]
    target_id = target_user.id
    
    try:
        amount = int(parts[-1])
        if amount <= 0: raise ValueError
    except ValueError:
        await message.channel.send("❌ Jumlah harus angka positif!")
        return

    sender_data = list(get_user_data(user_id))
    if sender_data[2] < amount:
        await message.channel.send(f"❌ Uang tidak cukup!")
        return

    sender_data[2] -= amount
    update_full_user_data(user_id, *sender_data)
    
    target_data = list(get_user_data(target_id))
    target_data[2] += amount
    update_full_user_data(target_id, *target_data)

    await message.channel.send(f"💸 {message.author.mention} mengirim **💵 {amount:,} ACR** ke {target_user.mention}!")


async def handle_hunt_command(message):
    user_id = message.author.id
    hunt_count, last_hunt_reset, user_data = get_hunt_status(user_id)
    
    if hunt_count >= MAX_DAILY_HUNT:
        await message.channel.send(f"❌ Jatah hunt habis! ({MAX_DAILY_HUNT}/{MAX_DAILY_HUNT})")
        return
    
    (exp, level, money, last_daily, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, dice_reset, fight_time, _, _) = user_data
    
    monster = get_monster_for_level(level)
    if not monster:
        await message.channel.send("❌ Tidak ada monster!")
        return
    
    total_atk, total_spd, total_def, total_dex, total_crit, total_mdmg, total_hp, total_mp = get_total_stats(user_id)
    
    player_damage = (total_atk * 2) + (total_mdmg * 1.5) + (level * 3)
    is_crit = random.random() < (total_crit / 100)
    if is_crit: player_damage *= 1.5
    player_damage = int(player_damage * random.uniform(0.85, 1.15))
    
    monster_hp = monster['hp']
    monster_atk = monster['level'] * 8
    turns_to_kill = max(1, monster_hp // max(1, player_damage))
    player_hp_loss = turns_to_kill * monster_atk
    
    win = player_hp_loss < total_hp or player_damage >= monster_hp
    today = datetime.date.today().strftime('%Y-%m-%d')
    new_hunt_count = hunt_count + 1
    
    if win:
        exp_reward = monster['exp']
        gold_reward = monster['level'] * random.randint(HUNT_GOLD_MULTIPLIER_MIN, HUNT_GOLD_MULTIPLIER_MAX)
        
        if monster['level'] >= level:
            exp_reward = int(exp_reward * 1.5)
            gold_reward = int(gold_reward * 1.3)
        
        new_exp = exp + exp_reward
        new_money = money + gold_reward
        
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
            lvl_up_message += f"🎉 **LEVEL UP** ke **Level {level}**!\n"
        
        update_full_user_data(user_id, new_exp, level, new_money, last_daily, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, dice_reset, fight_time, new_hunt_count, today)
        
        embed = discord.Embed(title=f"⚔️ HUNT VICTORY! ⚔️", description=f"{message.author.mention} mengalahkan **{monster['name']}**!", color=discord.Color.green())
        if monster.get('image'): embed.set_thumbnail(url=monster['image'])
        embed.add_field(name="🎁 Rewards", value=f"✨ **+{exp_reward} EXP** | 💵 **+{gold_reward:,} ACR**", inline=False)
        if lvl_up_message: embed.add_field(name="🆙", value=lvl_up_message, inline=False)
        embed.add_field(name="Hunt", value=f"**{new_hunt_count}/{MAX_DAILY_HUNT}**", inline=True)
    else:
        update_full_user_data(user_id, exp, level, money, last_daily, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, dice_reset, fight_time, new_hunt_count, today)
        embed = discord.Embed(title=f"💀 HUNT FAILED! 💀", description=f"{message.author.mention} kalah melawan **{monster['name']}**!", color=discord.Color.red())
        if monster.get('image'): embed.set_thumbnail(url=monster['image'])
        embed.add_field(name="Hunt", value=f"**{new_hunt_count}/{MAX_DAILY_HUNT}**", inline=True)
    
    await message.channel.send(embed=embed)

async def handle_shift_command(message):
    user_id = message.author.id
    current_time = time.time()
    
    if message.guild is None:
        await message.channel.send("❌ Hanya bisa di server.")
        return

    guild_id = message.guild.id
    config_duration_min, config_roles_str, config_money, config_exp, shift_detail, max_participants = get_shift_config(guild_id)
    active_shift_data = get_active_shift(user_id)

    if active_shift_data:
        start_time, end_time, reward_money, reward_exp, shift_detail = active_shift_data
        if current_time >= end_time:
            embed = await process_shift_claim(user_id, guild_id, reward_money, reward_exp, config_duration_min, shift_detail, message.author)
            await message.channel.send(embed=embed)
        else:
            time_remaining = end_time - current_time
            minutes = int(time_remaining // 60)
            seconds = int(time_remaining % 60)
            embed = discord.Embed(title=f"⏳ Shift Berjalan: {shift_detail}", description=f"Selesai dalam **{minutes}m {seconds}s**", color=discord.Color.orange())
            await message.channel.send(embed=embed)
    else:
        if max_participants > 0 and count_active_shifts(guild_id) >= max_participants:
            await message.channel.send(f"❌ Shift penuh!")
            return

        required_role_ids = [int(rid) for rid in config_roles_str.split(',') if rid]
        if required_role_ids:
            author_role_ids = [role.id for role in message.author.roles]
            if not any(rid in author_role_ids for rid in required_role_ids):
                await message.channel.send(f"❌ Anda tidak memiliki role yang diperlukan!")
                return

        start_time = current_time
        end_time = current_time + (config_duration_min * 60)
        start_new_shift(user_id, start_time, end_time, config_money, config_exp, shift_detail)
        
        embed = discord.Embed(title=f"▶️ Shift Dimulai: {shift_detail}!", description=f"Durasi: **{config_duration_min} menit**\nReward: **💵 {config_money:,} ACR**, **✨ {config_exp:,} EXP**", color=discord.Color.green())
        await message.channel.send(embed=embed)

async def process_shift_claim(user_id, guild_id, reward_money, reward_exp, duration_min, shift_detail, member=None):
    end_active_shift(user_id)
    user_data = list(get_user_data(user_id))
    
    user_data[0] += reward_exp  # exp
    user_data[2] += reward_money  # money
    
    lvl_up_message = ""
    required_exp = required_exp_for_level(user_data[1])
    
    while user_data[0] >= required_exp:
        user_data[1] += 1  # level
        user_data[0] -= required_exp
        required_exp = required_exp_for_level(user_data[1])
        stat_to_boost = random.choice(['atk', 'spd', 'def', 'dex', 'crit', 'mdmg'])
        stat_idx = {'atk': 4, 'spd': 5, 'def': 6, 'dex': 7, 'crit': 8, 'mdmg': 9}
        user_data[stat_idx[stat_to_boost]] += 5
        lvl_up_message += f"🎉 **LEVEL UP** ke **Level {user_data[1]}**!\n"
    
    update_full_user_data(user_id, *user_data)
    
    embed = discord.Embed(title=f"✅ Shift Selesai! - {shift_detail}", description=f"Reward: **💵 {reward_money:,} ACR**, **✨ {reward_exp:,} EXP**", color=discord.Color.green())
    if lvl_up_message: embed.add_field(name="Level Up!", value=lvl_up_message, inline=False)
    return embed

async def handle_setshift_command(message):
    if message.guild is None:
        await message.channel.send("❌ Hanya bisa di server.")
        return

    is_owner = message.author == message.guild.owner
    is_cybersurge = any(role.name.lower() == 'cybersurge' for role in message.author.roles)
    if not (is_owner or is_cybersurge):
        await message.channel.send("❌ Tidak punya izin!")
        return

    parts = message.content.split()
    if len(parts) < 6:
        await message.channel.send(f"❌ Format: `{prefix}setshift <durasi> <money> <exp> <max_peserta> <detail> [roles]`")
        return

    try:
        duration = int(parts[1])
        money_reward = int(parts[2])
        exp_reward = int(parts[3])
        max_participants = int(parts[4])
        shift_detail = " ".join(parts[5:])
    except ValueError:
        await message.channel.send("❌ Parameter tidak valid!")
        return

    set_shift_config(message.guild.id, duration, '', money_reward, exp_reward, shift_detail, max_participants)
    embed = discord.Embed(title="✅ Shift Config Updated!", description=f"**{shift_detail}**\nDurasi: {duration}m | Reward: 💵{money_reward:,} / ✨{exp_reward}", color=discord.Color.blue())
    await message.channel.send(embed=embed)


async def handle_stat_command(message, target_user):
    user_id = target_user.id
    user_data = get_user_data(user_id)
    current_exp, current_level, current_currency, _, base_atk, base_spd, base_def, base_dex, base_crit, base_mdmg, base_hp, base_mp, max_slots, equipped_weapon, equipped_armor, *_ = user_data
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
    
    embed.add_field(name="HP", value=f"❤️ {base_hp} ({total_hp - base_hp:+d}) = **{total_hp}**", inline=True)
    embed.add_field(name="MP", value=f"🌀 {base_mp} ({total_mp - base_mp:+d}) = **{total_mp}**", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)

    embed.add_field(name="ATK", value=f"⚔️ {base_atk} ({total_atk - base_atk:+d}) = **{total_atk}**", inline=True)
    embed.add_field(name="DEF", value=f"🛡️ {base_def} ({total_def - base_def:+d}) = **{total_def}**", inline=True)
    embed.add_field(name="SPD", value=f"👟 {base_spd} ({total_spd - base_spd:+d}) = **{total_spd}**", inline=True)
    
    embed.add_field(name="DEX", value=f"🎯 {base_dex} ({total_dex - base_dex:+d}) = **{total_dex}**", inline=True)
    embed.add_field(name="CRIT", value=f"💥 {base_crit} ({total_crit - base_crit:+d}) = **{total_crit}%**", inline=True)
    embed.add_field(name="MDMG", value=f"⚛️ {base_mdmg} ({total_mdmg - base_mdmg:+d}) = **{total_mdmg}**", inline=True)

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
    user_data = list(get_user_data(user_id))
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

async def handle_help_command(message):
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

# ============== BOT EVENTS ==============

@bot.event
async def on_ready():
    print(f"✅ Bot {bot.user} is ready! (MySQL Version)")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id
    current_time = time.time()
    last_exp_time = user_exp_cooldown.get(user_id, 0)
    
    if current_time - last_exp_time >= EXP_COOLDOWN:
        user_data = list(get_user_data(user_id))
        exp_gain = random.randint(EXP_PER_MESSAGE_MIN, EXP_PER_MESSAGE_MAX)
        user_data[0] += exp_gain
        user_exp_cooldown[user_id] = current_time

        required_exp = required_exp_for_level(user_data[1])
        
        while user_data[0] >= required_exp:
            user_data[1] += 1  # level
            user_data[0] -= required_exp
            required_exp = required_exp_for_level(user_data[1])
            
            reward = user_data[1] * 200
            user_data[2] += reward
            
            stat_to_boost = random.choice(['atk', 'spd', 'def', 'dex', 'crit', 'mdmg'])
            stat_idx = {'atk': 4, 'spd': 5, 'def': 6, 'dex': 7, 'crit': 8, 'mdmg': 9}
            user_data[stat_idx[stat_to_boost]] += 5

            embed = discord.Embed(title=f"🎉 Level Up! (Level {user_data[1]})", description=f"{message.author.mention} naik ke **Level {user_data[1]}**!", color=discord.Color.blue())
            embed.add_field(name="Reward", value=f"💵 {reward:,} ACR | +5 {stat_to_boost.upper()}", inline=False)
            await message.channel.send(embed=embed)

        update_full_user_data(user_id, *user_data)
        
    # Command handling
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
    elif command in [f'{prefix}shop', f'{prefix}list']:
        if len(msg_lower_parts) < 2:
            await handle_buy_menu(message)
        else:
            item_type = msg_lower_parts[1]
            if item_type in ['weapon', 'armor', 'role']:
                await handle_list_command(message, item_type)
    elif command in [f'{prefix}level', f'{prefix}stat']:
        target = message.mentions[0] if message.mentions else message.author
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
    elif command in [f'{prefix}roll', f'{prefix}dice']:
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

# Run bot
if __name__ == "__main__":
    if not token:
        print("❌ DISCORD_TOKEN tidak ditemukan di .env!")
    else:
        bot.run(token)
