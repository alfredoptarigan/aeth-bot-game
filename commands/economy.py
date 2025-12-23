"""
Economy-related commands (daily, givemoney, dice)
"""
import discord
import random
import datetime
from commands.base import BaseCommand
from database.queries.user_queries import get_user_data, update_full_user_data
from utils.helpers import get_dice_status
from config.constants import (
    MAX_DAILY_DICE, DICE_COSTS, DICE_BASE_REWARD
)

class EconomyCommands(BaseCommand):
    """Handle economy-related commands"""
    
    async def handle_daily_command(self, message):
        """Handle daily reward command"""
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
                f"✅ **Claimed!** {message.author.mention}, Anda mendapatkan **💵 {DAILY_REWARD_AMOUNT:,} ACR** harian! "
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
    
    async def handle_dice_command(self, message):
        """Handle dice roll command"""
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
        
        # Dice emoji mapping
        dice_emojis = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "👑"}
        emoji = dice_emojis.get(dice_roll, "⚀")
        
        response = (
            f"{message.author.mention} melempar dadu (Roll Tahap {stage_index + 1}): **{dice_roll}** {emoji}\n"
            f"Biaya Roll: **💵 {cost:,} ACR**.\n"
        )
        if reward_multiplier > 0:
            response += f"🎉 Anda mendapatkan **💵 {reward_gain:,} ACR**! (Multiplier: x{reward_multiplier:.1f})\n"
        response += f"Sisa jatah hari ini: **{MAX_DAILY_DICE - new_rolls}** kali. Total uang: **💵 {current_currency:,} ACR**."
        await message.channel.send(response)
    
    async def handle_givemoney_command(self, message):
        """Handle give money command"""
        user_id = message.author.id
        parts = message.content.lower().split()

        if len(parts) < 3 or not message.mentions or message.mentions[0].id == user_id:
            await message.channel.send(f"❌ Format: `{self.prefix}givemoney <@user> <amount>`")
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