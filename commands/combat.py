"""
Combat-related commands (fight, hunt)
"""
import discord
import random
import datetime
import time
import asyncio
from commands.base import BaseCommand
from database.queries.user_queries import get_user_data, update_full_user_data, reset_last_hunt_reset, reset_all_last_hunt_reset
from game.stats import get_total_stats
from game.monsters import get_monster_for_level
from game.combat import calculate_combat_power, calculate_hunt_damage, simulate_hunt_battle
from game.leveling import required_exp_for_level
from utils.helpers import get_hunt_status
from config.constants import (
    MAX_DAILY_HUNT, HUNT_GOLD_MULTIPLIER_MIN, HUNT_GOLD_MULTIPLIER_MAX,
    FIGHT_COOLDOWN, FIGHT_COST_MIN, FIGHT_COST_MAX,
    FIGHT_BONUS_EXP_MIN, FIGHT_BONUS_EXP_MAX,
    FIGHT_BONUS_MONEY_MIN, FIGHT_BONUS_MONEY_MAX,
    UPPER_LEVEL_ACCESS
)

# In-memory guard to prevent the same user from running multiple loophunt sessions concurrently.
# We create the lock lazily inside the async handler to avoid creating an asyncio.Lock at import time
_LOOPING_USERS = set()
_LOOPING_LOCK = None

class CombatCommands(BaseCommand):
    """Handle combat-related commands"""
    
    def _perform_single_hunt(self, user_id):
        """Perform one hunt cycle for user_id: update DB and return a result dict.

        This is synchronous and returns a dict with keys:
          - status: 'win'|'lose'|'no_quota'|'no_monster'
          - hunt_count: previous hunt_count
          - new_hunt_count
          - exp_reward, gold_reward (0 if none)
          - level_ups: list of level-up messages (may be empty)
          - monster: monster dict or None
          - new_level, new_exp, new_money
        """
        user_id = int(user_id)
        hunt_count, last_hunt_reset, user_data = get_hunt_status(user_id)

        if hunt_count >= MAX_DAILY_HUNT:
            return {'status': 'no_quota', 'hunt_count': hunt_count}

        (exp, level, money, last_daily, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, dice_reset, fight_time, _, _) = user_data

        monster = get_monster_for_level(level)
        if not monster:
            return {'status': 'no_monster', 'hunt_count': hunt_count}

        player_damage, is_crit = calculate_hunt_damage(user_id, level)
        # Use new simulate signature which takes user_id to access full stats
        win = simulate_hunt_battle(user_id, player_damage, monster['hp'], monster['level'])

        today = datetime.date.today().strftime('%Y-%m-%d')
        new_hunt_count = hunt_count + 1

        result = {
            'status': 'lose',
            'hunt_count': hunt_count,
            'new_hunt_count': new_hunt_count,
            'exp_reward': 0,
            'gold_reward': 0,
            'level_ups': [],
            'monster': monster,
            'new_level': level,
            'new_exp': exp,
            'new_money': money,
        }

        if win:
            exp_reward = monster['exp']
            gold_reward = monster['level'] * random.randint(HUNT_GOLD_MULTIPLIER_MIN, HUNT_GOLD_MULTIPLIER_MAX)

            if monster['level'] >= level:
                exp_reward = int(exp_reward * 1.5)
                gold_reward = int(gold_reward * 1.3)

            new_exp = exp + exp_reward
            new_money = money + gold_reward

            level_ups = []
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
                level_ups.append(f"LEVEL UP ke Level {level}")

            # persist updated data
            update_full_user_data(user_id, new_exp, level, new_money, last_daily, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, dice_reset, fight_time, new_hunt_count, today)

            result.update({
                'status': 'win',
                'exp_reward': exp_reward,
                'gold_reward': gold_reward,
                'level_ups': level_ups,
                'new_level': level,
                'new_exp': new_exp,
                'new_money': new_money,
            })
        else:
            # persist hunt failure (still consumes hunt slot)
            update_full_user_data(user_id, exp, level, money, last_daily, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, dice_reset, fight_time, new_hunt_count, today)

            result.update({'status': 'lose'})

        return result

    async def handle_hunt_command(self, message):
        """Handle hunt command - uses helper to perform one hunt and sends a single embed result."""
        user_id = message.author.id
        res = self._perform_single_hunt(user_id)

        if res.get('status') == 'no_quota':
            await message.channel.send(f"❌ Jatah hunt habis! ({MAX_DAILY_HUNT}/{MAX_DAILY_HUNT})")
            return

        if res.get('status') == 'no_monster':
            await message.channel.send("❌ Tidak ada monster!")
            return

        monster = res.get('monster')
        if res.get('status') == 'win':
            exp_reward = res.get('exp_reward', 0)
            gold_reward = res.get('gold_reward', 0)
            lvl_up_messages = res.get('level_ups', [])

            embed = discord.Embed(title=f"⚔️ HUNT VICTORY! ⚔️", description=f"{message.author.mention} mengalahkan **{monster['name']}**!", color=discord.Color.green())
            if monster.get('image'): embed.set_thumbnail(url=monster['image'])
            embed.add_field(name="🎁 Rewards", value=f"✨ **+{exp_reward} EXP** | 💵 **+{gold_reward:,} ACR**", inline=False)
            if lvl_up_messages:
                embed.add_field(name="🆙", value="\n".join(lvl_up_messages), inline=False)
            embed.add_field(name="Hunt", value=f"**{res.get('new_hunt_count')}/{MAX_DAILY_HUNT}**", inline=True)
        else:
            embed = discord.Embed(title=f"💀 HUNT FAILED! 💀", description=f"{message.author.mention} kalah melawan **{monster['name']}**!", color=discord.Color.red())
            if monster.get('image'): embed.set_thumbnail(url=monster['image'])
            embed.add_field(name="Hunt", value=f"**{res.get('new_hunt_count')}/{MAX_DAILY_HUNT}**", inline=True)

        await message.channel.send(embed=embed)

    async def handle_fight_command(self, message):
        """Handle fight command"""
        user_id = message.author.id
        current_time = time.time()

        if not message.mentions or message.mentions[0].id == user_id:
            await message.channel.send(f"❌ Format: `{self.prefix}fight <@user>`")
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
            from bot.client import get_bot
            bot = get_bot()
            reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await message.channel.send(f"⏳ {target_member.mention} tidak merespon.")
            return
            
        if str(reaction.emoji) == '❌':
            await message.channel.send(f"🛡️ {target_member.mention} menolak tantangan.")
            return

        # Battle calculation
        p_power = calculate_combat_power(user_id, player_data[1])
        t_power = calculate_combat_power(target_id, get_user_data(target_id)[1])
        
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

    async def handle_reset_hunt_time(self, message):
        """Reset last_hunt_reset for a specific user or all users.


        Usage:
          ag!reset_hunt_time @user  -> resets that user's last_hunt_reset
          ag!reset_hunt_time all    -> resets all users' last_hunt_reset

        Only usable by server admin (role id ROLE_ID_ADMIN) or users with Manage Guild permission.
        """

        # permission check: either has manage_guild or has the special admin role
        author = message.author
        guild = message.guild

        # permission check: either has Manage Guild permission or has the admin role on Discord
        user_id = author.id

        # Check Manage Guild permission (guild-level permission)
        has_manage_guild = False
        try:
            has_manage_guild = bool(getattr(author, 'guild_permissions', None) and author.guild_permissions.manage_guild)
        except Exception:
            has_manage_guild = False

        # Check by configured role names (UPPER_LEVEL_ACCESS)
        has_admin_role = False
        try:
            if guild is not None:
                member_role_names = {(r.name or '').strip().lower() for r in getattr(author, 'roles', [])}
                allowed_names = {n.strip().lower() for n in UPPER_LEVEL_ACCESS}
                if member_role_names & allowed_names:
                    has_admin_role = True
        except Exception:
            has_admin_role = False

        if not (has_manage_guild or has_admin_role):
            embed = discord.Embed(title="❌ Error!", description="Anda tidak memiliki hak untuk melakukan ini!", color=discord.Color.red())
            await message.channel.send(embed=embed)
            return False

        parts = message.content.strip().split()
        if len(parts) < 2:
            await message.channel.send("❌ Usage: `ag!reset_hunt_time <@user|all>`")
            return False

        target = parts[1].lower()

        try:
            if target == 'all':
                reset_all_last_hunt_reset()
                embed = discord.Embed(title="✅ Reset Sukses", description="Waktu hunting untuk semua user telah di-reset.", color=discord.Color.green())
                await message.channel.send(embed=embed)
                return True

            # try mention first
            if message.mentions:
                target_member = message.mentions[0]
                reset_last_hunt_reset(target_member.id)
                embed = discord.Embed(title="✅ Reset Sukses", description=f"Waktu hunting untuk {target_member.mention} telah di-reset.", color=discord.Color.green())
                await message.channel.send(embed=embed)
                return True

            # try numeric id
            try:
                uid = int(target)
                reset_last_hunt_reset(uid)
                embed = discord.Embed(title="✅ Reset Sukses", description=f"Waktu hunting untuk user id `{uid}` telah di-reset.", color=discord.Color.green())
                await message.channel.send(embed=embed)
                return True
            except ValueError:
                await message.channel.send("❌ Target tidak valid. Berikan mention user, user ID, atau `all`.")
                return False

        except Exception as e:
            # unexpected DB or other error
            embed = discord.Embed(title="❌ Terjadi Kesalahan", description=f"Gagal mereset: {e}", color=discord.Color.red())
            await message.channel.send(embed=embed)
            return False

        # end of handler

    async def handle_loop_hunt_command(self, message):
        """Perform multiple hunts in sequence until the user's daily hunt quota is exhausted.

        Usage: ag!loophunt
        This will run the same logic as `ag!hunt` repeatedly for the remaining hunt slots (max = MAX_DAILY_HUNT).
        """

        user_id = message.author.id
        hunt_count, _, _ = get_hunt_status(user_id)
        remaining = MAX_DAILY_HUNT - hunt_count

        if remaining <= 0:
            await message.channel.send(f"❌ Jatah hunt habis! ({MAX_DAILY_HUNT}/{MAX_DAILY_HUNT})")
            return

        # prevent concurrent loophunt executions by the same user
        global _LOOPING_USERS, _LOOPING_LOCK
        if _LOOPING_LOCK is None:
            _LOOPING_LOCK = asyncio.Lock()

        async with _LOOPING_LOCK:
            if user_id in _LOOPING_USERS:
                await message.channel.send("❌ Sedang dalam sesi loophunt lain. Tunggu sampai selesai.")
                return
            _LOOPING_USERS.add(user_id)

        total_performed = 0
        total_exp = 0
        total_gold = 0
        total_wins = 0
        total_losses = 0
        level_up_messages = []
        monsters_defeated = []

        try:
            for _ in range(remaining):
                before, _, _ = get_hunt_status(user_id)
                res = self._perform_single_hunt(user_id)
                # small delay to avoid hitting rate limits
                await asyncio.sleep(0.6)

                if res.get('status') in ('no_quota', 'no_monster'):
                    # stop looping if quota unexpectedly exhausted or no monster
                    break

                total_performed += 1
                total_exp += res.get('exp_reward', 0)
                total_gold += res.get('gold_reward', 0)
                if res.get('status') == 'win':
                    total_wins += 1
                    monsters_defeated.append(res.get('monster', {}).get('name'))
                else:
                    total_losses += 1

                if res.get('level_ups'):
                    level_up_messages.extend(res.get('level_ups'))

                after, _, _ = get_hunt_status(user_id)
                if after <= before:
                    break

            # Build a single summary embed
            summary = discord.Embed(title="🏹 Loop Hunt Summary", color=discord.Color.blue())
            summary.add_field(name="Performed", value=f"{total_performed} hunt(s)", inline=True)
            summary.add_field(name="Wins", value=str(total_wins), inline=True)
            summary.add_field(name="Losses", value=str(total_losses), inline=True)
            summary.add_field(name="EXP Gained", value=f"✨ **+{total_exp} EXP**", inline=False)
            summary.add_field(name="Gold Gained", value=f"💵 **+{total_gold:,} ACR**", inline=False)

            if monsters_defeated:
                summary.add_field(name="Monsters Defeated", value=", ".join(monsters_defeated), inline=False)
            if level_up_messages:
                summary.add_field(name="Level Ups", value="\n".join(level_up_messages), inline=False)

            # final hunt count for readability
            final_count, _, _ = get_hunt_status(user_id)
            summary.set_footer(text=f"Hunt slots: {final_count}/{MAX_DAILY_HUNT}")

            await message.channel.send(embed=summary)
        finally:
            # ensure removal from the guard set
            _LOOPING_USERS.discard(user_id)

    # Backwards-compatible alias: some event code calls `handle_loop_hunt` (without _command)
    async def handle_loop_hunt(self, message):
        return await self.handle_loop_hunt_command(message)
