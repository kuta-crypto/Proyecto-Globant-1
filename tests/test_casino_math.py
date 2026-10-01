import random

import pytest

from game.rng_system import DEFAULT_PROBABILITIES, SYMBOL_ORDER, generate_grid, weighted_choice
from game.scatter import SCATTER_THRESHOLD, SCATTER_PAYOUTS, MAX_CASCADES_PER_SPIN, jackpot_near_miss, resolve_scatter_cascades, scatter_tier
from tools.casino_math import sample_spin


def losing_board():
    return [[SYMBOL_ORDER[(row*6+col)%5] for col in range(6)] for row in range(6)]


def test_losing_board_is_never_rerolled_or_awarded():
    class NoDraws:
        def random(self):
            raise AssertionError("A losing board must not consume refill RNG")
    board = losing_board()
    result = resolve_scatter_cascades(board, rng=NoDraws(), capture_frames=True)
    assert result["grid"] == board
    assert result["payout_multiplier"] == 0
    assert result["cascades"] == []
    assert not result["capped"]


@pytest.mark.parametrize("count,tier", [(0,None),(8,None),(11,None),(12,"12-14"),(14,"12-14"),(15,"15-17"),(17,"15-17"),(18,"18+"),(36,"18+")])
def test_paytable_boundaries(count, tier):
    assert scatter_tier(count) == tier


def test_awarded_groups_use_actual_counts_and_input_is_not_modified():
    board = [["coin"]*6 for _ in range(2)] + [[SYMBOL_ORDER[1+(i//6*6+i%6)%4] for i in range(row*6,(row+1)*6)] for row in range(4)]
    before = [row[:] for row in board]
    result = resolve_scatter_cascades(board, rng=random.Random(41), max_cascades=1, capture_frames=True)
    frame = result["cascades"][0]
    assert frame["counts"]["coin"] == 12
    assert frame["winning_symbols"] == ["coin"]
    assert frame["payout_multiplier"] == SCATTER_PAYOUTS["coin"]["12-14"]
    assert frame["before"] == board == before
    assert frame["before"] is not board


def test_cascade_limit_is_explicit_and_payments_are_bounded():
    board = [["coin"]*6 for _ in range(6)]
    result = resolve_scatter_cascades(board, weights={"coin":1}, rng=random.Random(2))
    assert result["cascade_count"] == MAX_CASCADES_PER_SPIN
    assert result["capped"]
    assert result["payout_multiplier"] == MAX_CASCADES_PER_SPIN * SCATTER_PAYOUTS["coin"]["18+"]


def test_fast_audit_matches_the_real_gravity_resolver():
    fast, real = random.Random(8173), random.Random(8173)
    for _ in range(1000):
        raw, depth, capped = sample_spin(fast)
        board = [[weighted_choice(DEFAULT_PROBABILITIES, real) for _ in range(6)] for _ in range(6)]
        result = resolve_scatter_cascades(board, rng=real)
        assert raw == pytest.approx(result["payout_multiplier"])
        assert depth == result["cascade_count"]
        assert capped == result["capped"]


def test_live_grid_and_cascades_use_os_randomness(monkeypatch):
    calls = []
    def system_rng():
        calls.append(True)
        return random.Random(42)
    monkeypatch.setattr(random, "SystemRandom", system_rng)
    generate_grid()
    assert len(calls) == 1
    resolve_scatter_cascades(losing_board())
    assert len(calls) == 2
    generate_grid(seed=5)
    assert len(calls) == 2


@pytest.mark.parametrize("weights", [{}, {"coin":0}, {"coin":-1}, {"coin":float("nan")}, {"coin":float("inf")}])
def test_invalid_random_weights_fail_explicitly(weights):
    with pytest.raises(ValueError):
        weighted_choice(weights, random.Random(2))


def test_zero_weight_symbols_cannot_be_selected_at_zero_random_input():
    class Zero:
        def random(self):
            return 0.0
    assert weighted_choice({"coin":0,"seven":1}, Zero()) == "seven"


def test_near_miss_only_reports_real_counts_close_to_new_threshold():
    for count in (6,7,9,10,11,12):
        cells=["sixty_seven"]*count+["coin"]*(36-count)
        board=[cells[i:i+6] for i in range(0,36,6)]
        assert jackpot_near_miss(board) == (count if count in (SCATTER_THRESHOLD-2,SCATTER_THRESHOLD-1) else None)


@pytest.mark.parametrize("animations_enabled", [True, False])
def test_losing_spin_finishes_normally_without_changing_rpg_rewards(monkeypatch, animations_enabled):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    import pygame
    from game import game as module
    monkeypatch.setattr(module.TimbaRNGGame, "load_save", lambda self: None)
    monkeypatch.setattr(module.TimbaRNGGame, "save", lambda self: None)
    monkeypatch.setattr(module, "generate_grid", lambda *args, **kwargs: losing_board())
    game = module.TimbaRNGGame()
    try:
        game.state = "game"
        game.settings.animations_enabled = animations_enabled
        game.perform_spin()
        game.update(game.spin_duration)
        game.draw_game()
        assert not game.animating
        assert game.animation_phase == "idle"
        assert game.current_scatter_cascades == []
        assert game.last_reward["prize"] == 0
        assert game.last_reward["travel"] == 6
        assert game.last_reward["net"] == -4
        assert game.player.gold == 96
        assert game.stats["total_spins"] == 1
        game.update(100)
        assert game.player.gold == 96
    finally:
        pygame.quit()
