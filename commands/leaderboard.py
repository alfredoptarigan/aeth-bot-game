"""
Leaderboard command handler
"""
import discord
from commands.base import BaseCommand
from database.queries.user_queries import get_leaderboard_data
from utils.helpers import get_display_width

class LeaderboardCommands(BaseCommand):
    """Handle leaderboard command"""
    
    async def handle_leaderboard_command(self, message):
        """Handle leaderboard command"""
        from bot.client import get_bot
        bot = get_bot()
        
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