"""
Combat System Logic
"""
import random
from game.stats import get_total_stats

def calculate_combat_power(user_id, level):
    """Calculate combat power for PvP"""
    total_stats = get_total_stats(user_id)
    # ATK * 0.4 + MDMG * 0.2 + DEF * 0.1 + SPD * 0.1 + level bonus
    power = (total_stats[0] * 0.4) + (total_stats[5] * 0.2) + (total_stats[2] * 0.1) + (total_stats[1] * 0.1) + level * 10
    # Add randomness
    power *= random.uniform(0.9, 1.1)
    return power

def calculate_hunt_damage(user_id, level):
    """Calculate damage for hunting monsters.

    Returns a tuple (damage, is_crit).
    The formula uses ATK and MDMG as primary damage sources and includes
    a small contribution from level. The crit chance uses the player's
    CRIT stat (as percentage).
    """
    total_atk, total_spd, total_def, total_dex, total_crit, total_mdmg, total_hp, total_mp = get_total_stats(user_id)
    # Base damage scales with ATK and MDMG. Give ATK higher weight for normal hits
    base_damage = (total_atk * 2.0) + (total_mdmg * 1.2) + (level * 2.5)

    # Small contribution from DEX to reward investing in accuracy/speed
    base_damage += total_dex * 0.3

    # Critical check
    is_crit = random.random() < (total_crit / 100.0)
    if is_crit:
        base_damage *= 1.6  # stronger crit multiplier

    # Apply per-hit randomness
    damage = int(max(1, base_damage * random.uniform(0.9, 1.12)))
    return damage, is_crit


def simulate_hunt_battle(user_id, player_damage, monster_hp, monster_level):
    """Simulate battle between player and monster using full player stats.

    Args:
      user_id: player's discord id (used to fetch total stats)
      player_damage: snapshot damage value (from calculate_hunt_damage)
      monster_hp: monster total hp
      monster_level: monster level

    Returns True if player wins, False otherwise.
    """
    total_atk, total_spd, total_def, total_dex, total_crit, total_mdmg, total_hp, total_mp = get_total_stats(user_id)

    # Monster attack scales with level and HP
    base_monster_atk = monster_level * 8 + int(monster_hp * 0.03)

    cur_player_hp = total_hp
    cur_monster_hp = monster_hp
    turns = 0
    max_turns = 12

    # chance to dodge per hit based on SPD/Dex (capped)
    dodge_chance = min(0.35, (total_spd * 0.01) + (total_dex * 0.005))

    while cur_player_hp > 0 and cur_monster_hp > 0 and turns < max_turns:
        turns += 1

        # Player attack: use snapshot damage with small variance, and small bonus from atk/level
        hit_damage = int(max(1, player_damage * random.uniform(0.92, 1.08) + (total_atk * 0.05)))
        cur_monster_hp -= hit_damage
        if cur_monster_hp <= 0:
            return True

        # Monster attack: may miss if player dodges
        if random.random() < dodge_chance:
            # dodged
            continue

        monster_raw = base_monster_atk + random.randint(-3, 6)

        # Reduce incoming damage by DEF (each DEF point reduces a bit) and by a small portion of player's HP
        def_reduction = int(total_def * 1.2)
        hp_shield = int(total_hp * 0.02)  # 2% of total HP acts like damage soak
        damage_to_player = max(1, monster_raw - def_reduction - hp_shield)

        cur_player_hp -= damage_to_player
        if cur_player_hp <= 0:
            return False

    # fallback: compare remaining hp to determine winner
    return cur_player_hp > cur_monster_hp
