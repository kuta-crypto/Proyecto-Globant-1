from typing import Dict, List

POINT_TABLE = {
    "coin": {3: 10, 4: 20, 5: 40, 6: 80},
    "seven": {3: 20, 4: 40, 5: 80, 6: 160},
    "joker": {3: 40, 4: 80, 5: 160, 6: 320},
    "sixty_nine": {3: 80, 4: 160, 5: 320, 6: 640},
    "sixty_seven": {3: 120, 4: 240, 5: 480, 6: 960},
}

GOLD_REWARD = {3: 5, 4: 10, 5: 20, 6: 40}
XP_REWARD = {3: 10, 4: 20, 5: 40, 6: 80}

# Gross bet multipliers for matching paylines. Payouts scale with symbol rarity.
PAYOUT_MULTIPLIERS = {
    "coin": {3: 0.25, 4: 0.6, 5: 1.5, 6: 4},
    "seven": {3: 0.5, 4: 1.2, 5: 3, 6: 8},
    "joker": {3: 1, 4: 3, 5: 8, 6: 20},
    "sixty_nine": {3: 2, 4: 5, 5: 14, 6: 40},
    "sixty_seven": {3: 3, 4: 8, 5: 24, 6: 75},
}


def line_gold_reward(length: int) -> int:
    return GOLD_REWARD.get(length, 0)


def line_xp_reward(length: int) -> int:
    return XP_REWARD.get(length, 0)


def evaluate_lines(lines: List[Dict[str, object]]) -> Dict[str, int]:
    total_points = 0
    total_gold = 0
    total_xp = 0
    for line in lines:
        symbol = str(line["symbol"])
        length = int(line["length"])
        if length not in POINT_TABLE.get(symbol, {}):
            continue
        points = POINT_TABLE[symbol][length]
        total_points += points
        total_gold += line_gold_reward(length)
        total_xp += line_xp_reward(length)
    return {"points": total_points, "gold": total_gold, "xp": total_xp}


def evaluate_payout_multiplier(lines: List[Dict[str, object]]) -> float:
    """Sum the gross wager multipliers for all matching paylines."""
    total = 0.0
    for line in lines:
        symbol = str(line["symbol"])
        length = int(line["length"])
        table = PAYOUT_MULTIPLIERS.get(symbol, {})
        total += table.get(length, table.get(max(table, default=6), 0.0))
    return total
