"""
Bot Event Handlers
"""
import random
import time
from database.queries.user_queries import get_user_data, update_full_user_data
from game.leveling import required_exp_for_level
from utils.embeds import create_level_up_embed
from config.constants import EXP_COOLDOWN, EXP_PER_MESSAGE_MIN, EXP_PER_MESSAGE_MAX, PREFIX

# Store user experience cooldowns
user_exp_cooldown = {}

def setup_events(bot, character_commands, economy_commands, combat_commands, help_commands, leaderboard_commands, inventory_commands, shop_commands, shift_commands):
    """Setup all bot events"""
    
    @bot.event
    async def on_ready():
        print(f"✅ Bot {bot.user} is ready! (Refactored Version)")

    @bot.event
    async def on_message(message):
        if message.author.bot:
            return

        user_id = message.author.id
        current_time = time.time()
        last_exp_time = user_exp_cooldown.get(user_id, 0)
        
        # Handle experience gain
        if current_time - last_exp_time >= EXP_COOLDOWN:
            await handle_experience_gain(message, user_id, current_time)
            
        # Handle commands
        await handle_commands(message, character_commands, economy_commands, combat_commands, help_commands, leaderboard_commands, inventory_commands, shop_commands, shift_commands)

async def handle_experience_gain(message, user_id, current_time):
    """Handle experience gain from messages"""
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

        embed = create_level_up_embed(message.author, user_data[1], reward, stat_to_boost)
        await message.channel.send(embed=embed)

    update_full_user_data(user_id, *user_data)

async def handle_commands(message, character_commands, economy_commands, combat_commands, help_commands, leaderboard_commands, inventory_commands, shop_commands, shift_commands):
    """Handle command routing"""
    msg_lower_parts = message.content.lower().split()
    if not msg_lower_parts:
        return
        
    command = msg_lower_parts[0]
    
    # Character commands
    if command in [f'{PREFIX}level', f'{PREFIX}stat']:
        target = message.mentions[0] if message.mentions else message.author
        await character_commands.handle_stat_command(message, target)
    elif command == f'{PREFIX}upgrade':
        await character_commands.handle_upgrade_command(message)
    
    # Economy commands
    elif command == f'{PREFIX}daily':
        await economy_commands.handle_daily_command(message)
    elif command in [f'{PREFIX}roll', f'{PREFIX}dice']:
        await economy_commands.handle_dice_command(message)
    elif command == f'{PREFIX}givemoney':
        await economy_commands.handle_givemoney_command(message)
    
    # Combat commands
    elif command == f'{PREFIX}hunt':
        await combat_commands.handle_hunt_command(message)
    elif command == f'{PREFIX}fight':
        await combat_commands.handle_fight_command(message)
    elif command == f'{PREFIX}reset_hunt_time':
        await combat_commands.handle_reset_hunt_time(message)
    elif command == f'{PREFIX}loophunt':
        await combat_commands.handle_loop_hunt(message)
    
    # Inventory commands
    elif command == f'{PREFIX}inventory':
        await inventory_commands.handle_inventory_command(message)
    elif command == f'{PREFIX}equip':
        await inventory_commands.handle_equip_command(message)
    elif command == f'{PREFIX}unequip':
        await inventory_commands.handle_unequip_command(message)
    
    # Shop commands
    elif command == f'{PREFIX}buy':
        if len(msg_lower_parts) == 1:
            await shop_commands.handle_buy_menu(message)
        elif len(msg_lower_parts) >= 2:
            item_type = msg_lower_parts[1]
            if item_type in ['weapon', 'armor']:
                if len(msg_lower_parts) == 2:
                    await shop_commands.handle_shop_list(message, item_type)
                else:
                    await shop_commands.handle_buy_item(message, item_type)
            elif item_type == 'role':
                if len(msg_lower_parts) == 2:
                    await shop_commands.handle_shop_list(message, item_type)
                else:
                    await shop_commands.handle_buy_role(message)
    elif command in [f'{PREFIX}shop', f'{PREFIX}list']:
        if len(msg_lower_parts) < 2:
            await shop_commands.handle_buy_menu(message)
        else:
            item_type = msg_lower_parts[1]
            if item_type in ['weapon', 'armor', 'role']:
                await shop_commands.handle_shop_list(message, item_type)
    elif command == f'{PREFIX}sell':
        await shop_commands.handle_sell_command(message)
    
    # Shift commands - DISABLED
    # elif command == f'{PREFIX}shift':
    #     await shift_commands.handle_shift_command(message)
    # elif command == f'{PREFIX}setshift':
    #     await shift_commands.handle_setshift_command(message)
    # elif command == f'{PREFIX}finishshift':
    #     await shift_commands.handle_finishshift_command(message)
    
    # Help command
    elif command == f'{PREFIX}help':
        await help_commands.handle_help_command(message)
    
    # Leaderboard command
    elif command == f'{PREFIX}leaderboard':
        await leaderboard_commands.handle_leaderboard_command(message)