"""
Character-related commands (stat, level, upgrade)
"""
import discord
from commands.base import BaseCommand
from database.queries.user_queries import get_user_data, update_full_user_data
from game.stats import get_stats_and_role, calculate_upgrade_cost
from utils.embeds import create_stats_embed
from config.constants import VALID_STATS, STAT_TIER_1_COST

class CharacterCommands(BaseCommand):
    """Handle character-related commands"""
    
    async def handle_stat_command(self, message, target_user):
        """Handle stat/level command"""
        user_id = target_user.id
        user_data = get_user_data(user_id)
        total_stats, role = get_stats_and_role(user_id)

        embed = create_stats_embed(target_user, user_data, total_stats, role)
        await message.channel.send(embed=embed)
    
    async def handle_upgrade_command(self, message):
        """Handle upgrade command"""
        user_id = message.author.id
        parts = message.content.lower().split()
        
        if len(parts) < 3:
            await message.channel.send(f"❌ Format: `{self.prefix}upgrade <stat> <amount>` (e.g., `{self.prefix}upgrade atk 5`). Biaya: Progresif, dimulai dari {STAT_TIER_1_COST} ACR per poin.")
            return
        
        stat = parts[1]
        
        if stat not in VALID_STATS:
            await message.channel.send(f"❌ Stat tidak valid: `{stat}`. Gunakan: `{'`, `'.join(VALID_STATS)}`.")
            return
        
        try:
            amount = int(parts[2])
            if amount <= 0: raise ValueError
        except ValueError:
            await message.channel.send(f"❌ Jumlah harus angka positif!")
            return

        user_data = get_user_data(user_id)
        exp, level, money, last_daily, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset = user_data

        # Get current base stat
        stat_mapping = {
            'atk': atk, 'spd': spd, 'def': def_stat, 'dex': dex, 
            'crit': crit, 'mdmg': mdmg, 'hp': hp // 10, 'mp': mp // 5
        }
        current_base_stat = stat_mapping.get(stat, 0)

        cost = calculate_upgrade_cost(current_base_stat, amount, stat)

        if money < cost:
            await message.channel.send(f"❌ Uang tidak cukup! Dibutuhkan **💵 {cost:,} ACR**, Anda punya **💵 {money:,} ACR**.")
            return

        # Apply upgrade
        increment = 0
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

        embed = discord.Embed(color=discord.Color.green())
        embed.set_author(name=f"{message.author.display_name} | Status Upgrade!")
        embed.set_thumbnail(url=message.author.display_avatar.url)
        embed.add_field(name="Upgrade Detail", value=f"**{stat.upper()}** +{increment} points", inline=False)
        embed.add_field(name="Total Cost", value=f"💵 {cost:,} ACR", inline=True)
        embed.add_field(name="Remaining Money", value=f"💵 {money:,} ACR", inline=True)

        await message.channel.send(embed=embed)