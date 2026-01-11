"""
Discord embed templates and utilities
"""
import discord
import logging

logger = logging.getLogger(__name__)

def create_error_embed(message):
    """Create error embed"""
    return discord.Embed(
        description=f"❌ {message}",
        color=discord.Color.red()
    )

def create_success_embed(message):
    """Create success embed"""
    return discord.Embed(
        description=f"✅ {message}",
        color=discord.Color.green()
    )

def create_info_embed(title, description, color=discord.Color.blue()):
    """Create info embed"""
    return discord.Embed(
        title=title,
        description=description,
        color=color
    )

def create_level_up_embed(user, new_level, reward, stat_boosted):
    """Create level up embed"""
    embed = discord.Embed(
        title=f"🎉 Level Up! (Level {new_level})", 
        description=f"{user.mention} naik ke **Level {new_level}**!", 
        color=discord.Color.blue()
    )
    embed.add_field(
        name="Reward", 
        value=f"💵 {reward:,} ACR | +5 {stat_boosted.upper()}", 
        inline=False
    )

    embed.set_thumbnail(url=user.display_avatar.url)
    return embed

def create_stats_embed(user, user_data, total_stats, role=None):
    """Create character stats embed"""
    current_exp, current_level, current_currency, _, base_atk, base_spd, base_def, base_dex, base_crit, base_mdmg, base_hp, base_mp, max_slots, equipped_weapon, equipped_armor, *_ = user_data
    total_atk, total_spd, total_def, total_dex, total_crit, total_mdmg, total_hp, total_mp = total_stats

    from game.leveling import required_exp_for_level
    required_exp = required_exp_for_level(current_level)
    
    # Progress bar
    progress_bar_length = 10
    exp_in_level = current_exp
    exp_needed = required_exp
    ratio = exp_in_level / exp_needed if exp_needed > 0 else 1.0 
    filled = int(ratio * progress_bar_length)
    unfilled = progress_bar_length - filled
    progress_bar = f"[{'█' * filled}{'░' * unfilled}]"

    embed = discord.Embed(
        title=f"📊 Stats {user.display_name} 📊", 
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

    # Derive role from the Discord Member object (not from DB).
    # Prefer the member's top role but ignore the guild default/@everyone role.
    role_text = "Player"
    try:
        guild = getattr(user, 'guild', None)
        top_role = getattr(user, 'top_role', None)
        default_role = getattr(guild, 'default_role', None) if guild is not None else None

        if top_role and default_role and top_role != default_role:
            role_text = top_role.mention
        else:
            # fallback: pick the highest non-default role from member.roles
            roles = [r for r in getattr(user, 'roles', []) if r != default_role]
            if roles:
                role_text = roles[-1].mention
            else:
                role_text = "Player"
    except Exception as e:
        logger.debug(f"Failed getting Discord role for user {getattr(user, 'id', None)}: {e}")
        role_text = "Player"
    embed.add_field(name="Title", value=role_text, inline=False)

    embed.add_field(name="Arrived on", value=f"{user.joined_at.strftime('%Y-%b-%d')}", inline=False)
    embed.add_field(name="Progress", value=f"{progress_bar} ({ratio*100:.2f}%)", inline=False)
    
    embed.set_thumbnail(url=user.display_avatar.url)
    return embed