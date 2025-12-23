"""
Leveling and Experience System
"""

def required_exp_for_level(level):
    """Calculate required experience for a given level"""
    return 5 * (level ** 2) + 50 * level + 100