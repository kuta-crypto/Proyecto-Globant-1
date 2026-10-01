"""Offline Monte Carlo audit of the fixed 6x6 scatter mathematics.

Counts are sufficient here: every copy of a winning symbol is removed, and
all refill cells are IID. This is distribution-equivalent to gravity on the
full grid, and is checked against the real resolver with identical RNG streams.
No player state, live tuning, bankroll feedback or save files are involved.
"""

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from game.rng_system import SYMBOL_ORDER, DEFAULT_PROBABILITIES
from game.scatter import MAX_CASCADES_PER_SPIN, SCATTER_THRESHOLD, SCATTER_PAYOUTS, SCATTER_PAYOUT_SCALE, RTP_TARGET, scatter_tier


def sample_spin(rng):
    weights = [DEFAULT_PROBABILITIES[key] for key in SYMBOL_ORDER]
    counts = Counter(rng.choices(SYMBOL_ORDER, weights=weights, k=36))
    payout = 0.0
    depth = 0
    for _ in range(MAX_CASCADES_PER_SPIN):
        winners = [key for key in SYMBOL_ORDER if counts[key] >= SCATTER_THRESHOLD]
        if not winners:
            break
        payout += sum(SCATTER_PAYOUTS[key][scatter_tier(counts[key])] for key in winners)
        refill = sum(counts[key] for key in winners)
        for key in winners:
            counts[key] = 0
        counts.update(rng.choices(SYMBOL_ORDER, weights=weights, k=refill))
        depth += 1
    capped = depth == MAX_CASCADES_PER_SPIN and max(counts.values()) >= SCATTER_THRESHOLD
    return payout, depth, capped


def audit(spins, seed, wager=10):
    rng = random.Random(seed)
    total = squares = 0.0
    hit = profit = depths = caps = settled = 0
    highest = 0.0
    for _ in range(spins):
        raw, depth, capped = sample_spin(rng)
        payout = raw * SCATTER_PAYOUT_SCALE
        total += payout
        squares += payout * payout
        hit += payout > 0
        profit += payout > 1
        depths += depth
        caps += capped
        highest = max(highest, payout)
        settled += int(wager * payout)
    mean = total / spins
    variance = max(0, (squares - total * total / spins) / (spins-1))
    margin = 1.96 * math.sqrt(variance / spins)
    return dict(
        spins=spins, seed=seed, target_rtp=RTP_TARGET, payout_scale=SCATTER_PAYOUT_SCALE,
        measured_rtp=mean, rtp_95_percent_interval=[mean-margin, mean+margin],
        hit_rate=hit/spins, net_win_rate=profit/spins, no_award_rate=1-hit/spins,
        mean_cascades=depths/spins, capped_spins=caps, highest_sampled_multiplier=highest,
        rounding_example=dict(wager=wager, rtp_after_integer_floor=settled/(spins*wager)),
        suggested_offline_scale=RTP_TARGET / (mean/SCATTER_PAYOUT_SCALE),
        exclusions=["character and pet effects", "luck modifiers", "travel gold", "equipment", "free spins", "rounding except in rounding_example"],
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--spins", type=int, default=1_000_000)
    parser.add_argument("--seed", type=int, default=20260930)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.spins < 2:
        parser.error("--spins must be at least 2")
    report = json.dumps(audit(args.spins, args.seed), indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report+"\n", encoding="utf-8")
    print(report)
