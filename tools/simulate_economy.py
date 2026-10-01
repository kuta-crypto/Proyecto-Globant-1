"""Reproducible gameplay sample. Never loads or writes the player's save."""

import argparse
import json
import os
from pathlib import Path
import random
import statistics
import sys
from unittest.mock import patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame
from game import game as module
from game.rng_system import generate_grid
from game.scatter import resolve_scatter_cascades


def sample(paid_spins=1000, seed=20260929):
    rng = random.Random(seed)

    def grid(rows, cols, **kwargs):
        return generate_grid(rows, cols, seed=rng.randrange(2**32), **kwargs)

    def cascades(board, **kwargs):
        kwargs["rng"] = rng
        return resolve_scatter_cascades(board, **kwargs)

    with patch.object(module.TimbaRNGGame, "load_save", lambda self: None), patch.object(module.TimbaRNGGame, "save", lambda self: None), patch.object(module, "generate_grid", grid), patch.object(module, "resolve_scatter_cascades", cascades):
        game = module.TimbaRNGGame()
        game.settings.animations_enabled = False
        paid = free = 0
        net = []
        prizes = []
        while paid < paid_spins or game.bonus_spins_remaining:
            if len(net) > paid_spins * 30:
                raise RuntimeError("Unexpectedly long bonus chain")
            game.bet_amount = 10
            game.perform_spin()
            game.update(100)
            game.update(100)
            paid += int(not game.spin_is_free)
            free += int(game.spin_is_free)
            net.append(game.last_reward["net"])
            prizes.append(game.last_reward["prize"])
        result = dict(seed=seed, paid_spins=paid, free_spins=free, wager=10, world=1, character="oliva", upgrades=False, starting_gold=100, ending_gold=game.player.gold, net_gold_per_paid_spin=round((game.player.gold-100)/paid,3), median_prize=statistics.median(prizes), mean_prize=round(statistics.mean(prizes),3), zero_prize_spins=prizes.count(0), ending_level=game.player.level, earned_points=game.player.points)
        pygame.quit()
        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--spins", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260929)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.spins < 1:
        parser.error("--spins must be positive")
    result = sample(args.spins, args.seed)
    report = json.dumps(result, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report + "\n", encoding="utf-8")
    print(report)
