"""Symbol paths for downward reels and gravity cascades (in cell units)."""

import random

from game.rng_system import weighted_choice


def build_reels(before, after, weights, rng=None):
    rng = rng or random.Random()
    rows, cols = len(before), len(before[0])
    reels = []
    for col in range(cols):
        distance = rows * 3 + col * 2
        strip = []
        for source in range(-distance, rows):
            if source >= 0:
                symbol = before[source][col]
            elif source < -distance + rows:
                symbol = after[source + distance][col]
            else:
                symbol = weighted_choice(weights, rng)
            strip.append((symbol, source))
        reels.append((distance, strip))
    return reels


def reel_offset(progress, distance):
    # Continuous downward travel with a soft stop exactly on the result.
    progress = max(0.0, min(1.0, progress))
    return distance * (1.0 - (1.0 - progress) ** 3)


def cascade_paths(before, after, winners):
    paths = []
    rows, cols = len(before), len(before[0])
    for col in range(cols):
        survivors = [row for row in range(rows) if before[row][col] not in winners]
        refill = rows - len(survivors)
        for row in range(refill):
            paths.append((after[row][col], col, row - refill, row))
        for destination, source in enumerate(survivors, start=refill):
            paths.append((before[source][col], col, source, destination))
    return paths
