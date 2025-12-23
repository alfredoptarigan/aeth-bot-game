"""
Shift-related commands (shift, setshift, finishshift)
"""
import discord
import time
import random
from commands.base import BaseCommand
from database.queries.user_queries import get_user_data, update_full_user_data
from database.queries.shift_queries import (
    get_shift_config, set_shift_config, get_active_shift, 
    start_new_shift, end_active_shift, count_active_shifts
)
from game.leveling import required_exp_for_level

class ShiftCommands(BaseCommand):
    """Handle shift-related commands"""
    
    async def handle_shift_command(self, message):
        """Handle shift command"""
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
                embed = await self.process_shift_claim(user_id, guild_id, reward_money, reward_exp, config_duration_min, shift_detail, message.author)
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
    
    async def handle_setshift_command(self, message):
        """Handle setshift command"""
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
            await message.channel.send(f"❌ Format: `{self.prefix}setshift <durasi> <money> <exp> <max_peserta> <detail> [roles]`")
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
    
    async def handle_finishshift_command(self, message):
        """Handle finishshift command"""
        if message.guild is None:
            await message.channel.send("❌ Hanya bisa di server.")
            return

        is_owner = message.author == message.guild.owner
        is_cybersurge = any(role.name.lower() == 'cybersurge' for role in message.author.roles)
        if not (is_owner or is_cybersurge):
            await message.channel.send("❌ Tidak punya izin!")
            return

        if not message.mentions:
            await message.channel.send(f"❌ Format: `{self.prefix}finishshift <@user>`")
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
            await message.channel.send(f"⚠️ **Peringatan Admin:** Shift {target_member.mention} masih berjalan (**{minutes}m {seconds}s** tersisa), tetapi Admin memaksa klaim.")

        embed = await self.process_shift_claim(user_id, message.guild.id, reward_money, reward_exp, config_duration_min, shift_detail, target_member)
        await message.channel.send(embed=embed)
    
    async def process_shift_claim(self, user_id, guild_id, reward_money, reward_exp, duration_min, shift_detail, member=None):
        """Process shift claim and rewards"""
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