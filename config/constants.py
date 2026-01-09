"""
Game Constants - All game configuration values
"""

# Bot Configuration
PREFIX = 'ag!'

# Experience System
EXP_COOLDOWN = 60
EXP_PER_MESSAGE_MIN = 10
EXP_PER_MESSAGE_MAX = 50

# Dice System
MAX_DAILY_DICE = 5
DICE_COSTS = [0, 200, 400, 600, 800] 
DICE_BASE_REWARD = 300 

# Combat System
FIGHT_COOLDOWN = 10 * 60  # 10 minutes
FIGHT_COST_MIN = 500
FIGHT_COST_MAX = 500

# Hunt System
MAX_DAILY_HUNT = 5
HUNT_GOLD_MULTIPLIER_MIN = 5
HUNT_GOLD_MULTIPLIER_MAX = 15

# Fight Rewards
FIGHT_BONUS_EXP_MIN = 50
FIGHT_BONUS_EXP_MAX = 200
FIGHT_BONUS_MONEY_MIN = 500
FIGHT_BONUS_MONEY_MAX = 2500

# Stat Upgrade System
STAT_UPGRADE_COST = 100

# Stat Tiers
STAT_TIER_1_MAX = 10
STAT_TIER_2_MAX = 20
STAT_TIER_3_MAX = 50
STAT_TIER_4_MAX = 1000

STAT_TIER_1_COST = 100
STAT_TIER_2_COST = 125
STAT_TIER_3_COST = 175
STAT_TIER_4_COST = 250

#expansion inventory
INVENTORY_BASE_UPGRADE_COST = 500
INVENTORY_COST_MULTIPLIER = 1.5
INVENTORY_SLOTS_INCREASE = 5

# Valid Stats for Upgrade
VALID_STATS = ['atk', 'spd', 'def', 'dex', 'crit', 'mdmg', 'hp', 'mp']

# Default User Stats
DEFAULT_USER_DATA = (0, 1, 0, '2000-01-01', 5, 5, 5, 5, 5, 5, 100, 50, 10, None, None, 0, '2000-01-01', 0.0, 0, '2000-01-01')


UPPER_LEVEL_ACCESS = [
    "Honorable",
    "SAO",
    "Cyber Helper",
    "Cybersurge",
    "Aetherians"
]