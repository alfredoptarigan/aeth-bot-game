"""
Character Stats and Equipment System
"""
from database.queries.user_queries import get_user_data, get_user_role
from database.queries.shop_queries import get_item_details
from config.constants import (
    STAT_TIER_1_MAX, STAT_TIER_2_MAX, STAT_TIER_3_MAX, STAT_TIER_4_MAX,
    STAT_TIER_1_COST, STAT_TIER_2_COST, STAT_TIER_3_COST, STAT_TIER_4_COST
)

def get_total_stats(user_id):
    """Calculate total stats including equipment bonuses"""
    user_data = get_user_data(user_id)
    base_stats = list(user_data[4:12])  # ATK, SPD, DEF, DEX, CRIT, MDMG, HP, MP
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

def get_stats_and_role(user_id):
    stats = get_total_stats(user_id)
    role = get_user_role(user_id)
    return stats, role

def calculate_upgrade_cost(base_stat_value, amount_to_add, stat_name):
    """Calculate cost for upgrading stats"""
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