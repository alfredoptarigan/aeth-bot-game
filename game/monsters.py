"""
Monster System for Hunt Feature
"""
import json
import random

def load_monsters():
    """Load monsters from JSON file"""
    try:
        with open('monsters.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('monsters', [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# def get_monster_for_level(player_level):
#     """Get appropriate monster for player level"""
#     monsters = load_monsters()
#     if not monsters:
#         return None
#     suitable_monsters = [m for m in monsters if m['level'] <= min(player_level + 1, 10)]
#     if not suitable_monsters:
#         suitable_monsters = [monsters[0]]
#     return random.choice(suitable_monsters)


def get_monster_for_level(player_level):
    """Get appropriate monster for player level.
    Prefer monsters at or below player level, but allow stronger monsters
    up to +3 levels with decreasing probability.
    """
    monsters = load_monsters()
    if not monsters:
        return None

    max_extra = 3  # allow monsters up to player_level + max_extra
    candidates = []
    weights = []

    for m in monsters:
        m_level = m.get('level', 0)
        # skip monsters that are too far above the player's level
        if m_level > player_level + max_extra:
            continue

        # difference relative to player
        diff = m_level - player_level

        # base weighting:
        # - equal or lower levels get high weight (common encounters)
        # - higher levels get exponentially smaller weight per level above player
        if diff <= 0:
            weight = 10.0
        else:
            weight = 10.0 * (0.5 ** diff)  # +1 -> 5.0, +2 -> 2.5, +3 -> 1.25

        candidates.append(m)
        weights.append(weight)

    if not candidates:
        # fallback to first monster if nothing matched
        return monsters[0]

    chosen = random.choices(candidates, weights=weights, k=1)[0]
    return chosen