"""Scatter-pay evaluation and capped cascading refills for the 6x6 slot."""

import random
from typing import Dict, List, Sequence

from game.rng_system import DEFAULT_PROBABILITIES, SYMBOL_ORDER, weighted_choice

SCATTER_THRESHOLD = 12
MAX_CASCADES_PER_SPIN = 10
RTP_TARGET = 0.96
# Fixed before play, calibrated offline. Never compensate a player's streak.
# RTP here covers base scatter awards only, before RPG effects and rounding.
SCATTER_PAYOUT_SCALE = 1.6364

# Gross wager multipliers by total matching symbols anywhere on the grid.
# The rare symbols keep larger awards to retain a high-variance payout shape.
SCATTER_PAYOUTS = {
    "coin": {"12-14": 0.15, "15-17": 0.40, "18+": 1.0},
    "seven": {"12-14": 0.25, "15-17": 0.60, "18+": 1.5},
    "joker": {"12-14": 0.50, "15-17": 1.50, "18+": 4.0},
    "sixty_nine": {"12-14": 1.0, "15-17": 3.0, "18+": 8.0},
    "sixty_seven": {"12-14": 5.0, "15-17": 15.0, "18+": 50.0},
}


def scatter_tier(count: int) -> str | None:
    if 12 <= count <= 14:
        return "12-14"
    if 15 <= count <= 17:
        return "15-17"
    if count >= 18:
        return "18+"
    return None


def count_symbols(grid: Sequence[Sequence[str]]) -> Dict[str, int]:
    counts = {symbol: 0 for symbol in SYMBOL_ORDER}
    for row in grid:
        for symbol in row:
            if symbol not in counts:
                raise ValueError(f"Unknown symbol in grid: {symbol!r}")
            counts[symbol] += 1
    return counts


def jackpot_near_miss(grid: Sequence[Sequence[str]]) -> int | None:
    """Report an actual board count, never manufacture a near miss."""
    count = count_symbols(grid)["sixty_seven"]
    return count if count in (SCATTER_THRESHOLD - 2, SCATTER_THRESHOLD - 1) else None


def _settle_cascade(
    grid: List[List[str]],
    winning_symbols: set[str],
    weights: Dict[str, float],
    rng: random.Random,
) -> None:
    rows = len(grid)
    cols = len(grid[0])
    for col in range(cols):
        survivors = [grid[row][col] for row in range(rows) if grid[row][col] not in winning_symbols]
        refill_count = rows - len(survivors)
        new_symbols = [weighted_choice(weights, rng) for _ in range(refill_count)]
        # New symbols enter at the top; symbols above each removed cell fall down.
        for row, symbol in enumerate(new_symbols + survivors):
            grid[row][col] = symbol


def resolve_scatter_cascades(
    grid: Sequence[Sequence[str]],
    *,
    weights: Dict[str, float] | None = None,
    payout_table: Dict[str, Dict[str, float]] | None = None,
    rng: random.Random | None = None,
    max_cascades: int = MAX_CASCADES_PER_SPIN,
    capture_frames: bool = False,
) -> Dict[str, object]:
    """Pay 12+ matching symbols, then fall/refill until no win or the cap.

    Non-winning boards are kept as drawn. No rerolls, forced wins, or dependence
    on previous spins. The existing 10-cascade limit is part of the paytable.
    """
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("Grid must be a non-empty rectangle")
    if max_cascades < 1:
        raise ValueError("max_cascades must be at least 1")

    current = [list(row) for row in grid]
    rows, cols = len(current), len(current[0])
    if rows != 6 or cols != 6:
        raise ValueError("Scatter cascade expects a 6x6 grid (36 cells)")
    weights = DEFAULT_PROBABILITIES if weights is None else weights
    payout_table = SCATTER_PAYOUTS if payout_table is None else payout_table
    rng = rng if rng is not None else random.SystemRandom()
    cascades = []

    while len(cascades) < max_cascades:
        counts = count_symbols(current)
        winners = [symbol for symbol in SYMBOL_ORDER if counts[symbol] >= SCATTER_THRESHOLD]
        if not winners:
            break

        cascade_multiplier = 0.0
        payout_by_symbol = {}
        for symbol in winners:
            tier = scatter_tier(counts[symbol])
            symbol_multiplier = payout_table.get(symbol, {}).get(tier, 0.0)
            payout_by_symbol[symbol] = symbol_multiplier
            cascade_multiplier += symbol_multiplier
        cascades.append({
            "counts": counts,
            "winning_symbols": winners,
            "payout_by_symbol": payout_by_symbol,
            "payout_multiplier": cascade_multiplier,
        })
        if capture_frames:
            cascades[-1]["before"] = [row[:] for row in current]
        _settle_cascade(current, set(winners), weights, rng)
        if capture_frames:
            cascades[-1]["after"] = [row[:] for row in current]

    remaining_winners = [
        symbol for symbol, count in count_symbols(current).items()
        if count >= SCATTER_THRESHOLD
    ]
    capped = bool(remaining_winners) and len(cascades) >= max_cascades
    return {
        "grid": current,
        "cascades": cascades,
        "cascade_count": len(cascades),
        "payout_multiplier": sum(item["payout_multiplier"] for item in cascades),
        "remaining_winners": remaining_winners,
        "capped": capped,
    }


def estimate_scatter_rtp(
    spins: int = 10_000,
    *,
    seed: int = 1,
    weights: Dict[str, float] | None = None,
    payout_table: Dict[str, Dict[str, float]] | None = None,
    max_cascades: int = MAX_CASCADES_PER_SPIN,
    payout_multiplier: float = 1.0,
    payout_scale: float = SCATTER_PAYOUT_SCALE,
) -> float:
    """Estimate gross return per wager for the default character; excludes free spins.

    Base symbol weights and paytable only. Character passives, luck, travel
    gold, charged skills, free spins and integer rounding are excluded.
    """
    if spins < 1:
        raise ValueError("spins must be at least 1")
    weights = weights or DEFAULT_PROBABILITIES
    payout_table = payout_table or SCATTER_PAYOUTS
    rng = random.Random(seed)
    total_return = 0.0
    for _ in range(spins):
        grid = [[weighted_choice(weights, rng) for _ in range(6)] for _ in range(6)]
        result = resolve_scatter_cascades(
            grid,
            weights=weights,
            payout_table=payout_table,
            rng=rng,
            max_cascades=max_cascades,
        )
        total_return += float(result["payout_multiplier"]) * payout_scale * payout_multiplier
    return total_return / spins


def calibrate_scatter_payout_scale(
    spins: int = 50_000,
    *,
    target_rtp: float = RTP_TARGET,
    seed: int = 20260929,
    weights: Dict[str, float] | None = None,
    payout_table: Dict[str, Dict[str, float]] | None = None,
    max_cascades: int = MAX_CASCADES_PER_SPIN,
    payout_multiplier: float = 1.0,
) -> float:
    """Return a Monte Carlo scale for the requested baseline gross RTP."""
    if target_rtp <= 0:
        raise ValueError("target_rtp must be positive")
    unscaled_rtp = estimate_scatter_rtp(
        spins,
        seed=seed,
        weights=weights,
        payout_table=payout_table,
        max_cascades=max_cascades,
        payout_multiplier=payout_multiplier,
        payout_scale=1.0,
    )
    if unscaled_rtp <= 0:
        raise ValueError("The configured paytable has no expected payout")
    return target_rtp / unscaled_rtp
