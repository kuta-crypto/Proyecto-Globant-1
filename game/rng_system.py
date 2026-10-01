import random
import math
from typing import Dict, List

SYMBOL_ORDER = ["coin", "seven", "joker", "sixty_nine", "sixty_seven"]

# Fixed base-game weights. Only explicit, existing luck effects can modify
# these; bankroll, previous wins and losing streaks never enter the draw.
SYMBOL_WEIGHTS = {
    "coin": 27,
    "seven": 24,
    "joker": 21,
    "sixty_nine": 17,
    "sixty_seven": 11,
}
WEIGHT_TOTAL = sum(SYMBOL_WEIGHTS.values())
DEFAULT_PROBABILITIES = {
    symbol: weight / WEIGHT_TOTAL
    for symbol, weight in SYMBOL_WEIGHTS.items()
}


def weighted_choice(symbols: Dict[str, float], rng: random.Random | None = None) -> str:
    rng = rng if rng is not None else random.SystemRandom()
    items = list(symbols.items())
    if not items or any(not math.isfinite(weight) or weight < 0 for _, weight in items):
        raise ValueError("Weights must be non-negative and include at least one symbol")
    total = sum(weight for _, weight in items)
    if not math.isfinite(total) or total <= 0:
        raise ValueError("Weights must sum to a positive number")
    value = rng.random() * total
    accumulator = 0.0
    for symbol, weight in items:
        accumulator += weight
        if value < accumulator:
            return symbol
    return items[-1][0]


def generate_grid(rows: int = 6, cols: int = 6, seed: int | None = None, probabilities: Dict[str, float] | None = None) -> List[List[str]]:
    # Deterministic seeds are an explicit test/simulation feature only.
    rng = random.SystemRandom() if seed is None else random.Random(seed)
    probs = SYMBOL_WEIGHTS if probabilities is None else probabilities
    return [[weighted_choice(probs, rng) for _ in range(cols)] for _ in range(rows)]


def calculate_lucky_probability(base_probs: Dict[str, float], luck_level: int = 0) -> Dict[str, float]:
    """Suerte biases higher-value symbols progressively, but with diminishing returns.

    Each level weights rarer symbols more strongly than common ones.
    """
    if luck_level <= 0:
        return dict(base_probs)

    adjusted = {}
    for symbol, probability in base_probs.items():
        rank = SYMBOL_ORDER.index(symbol)
        rarity_weight = (rank + 1) / len(SYMBOL_ORDER)
        boost = 1.0 + luck_level * 0.08 * rarity_weight
        adjusted[symbol] = max(probability * boost, 0.01)

    total = sum(adjusted.values())
    if total <= 0:
        return dict(base_probs)
    scale = 1.0 / total
    scaled = {symbol: value * scale for symbol, value in adjusted.items()}
    return scaled


def check_bonus(grid: List[List[str]], joker_threshold: int = 12, high_value_threshold: int = 25) -> bool:
    """Activates bonus when either threshold is reached.

    Requirements: 12+ Joker symbols, or 25+ high-value symbols combining Joker, 69, and 67.
    """
    flat = [cell for row in grid for cell in row]
    joker_count = flat.count("joker")
    high_value_count = sum(1 for symbol in flat if symbol in {"joker", "sixty_nine", "sixty_seven"})
    return joker_count >= joker_threshold or high_value_count >= high_value_threshold


def simulate_spin(seed: int | None = None, probabilities: Dict[str, float] | None = None):
    return generate_grid(seed=seed, probabilities=probabilities)
