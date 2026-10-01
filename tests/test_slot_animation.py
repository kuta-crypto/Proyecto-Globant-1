import random

import pytest

from game.rng_system import DEFAULT_PROBABILITIES, generate_grid
from game.scatter import resolve_scatter_cascades
from game.slot_animation import build_reels, cascade_paths, reel_offset


def test_reels_move_down_and_land_on_exact_result():
    before, after = generate_grid(seed=1), generate_grid(seed=2)
    reels = build_reels(before, after, DEFAULT_PROBABILITIES, random.Random(3))
    for col, (distance, strip) in enumerate(reels):
        offsets = [reel_offset(i / 100, distance) for i in range(101)]
        assert offsets[0] == 0
        assert offsets[-1] == distance
        assert all(a <= b for a, b in zip(offsets, offsets[1:]))
        assert [symbol for symbol, row in strip if 0 <= row < 6] == [row[col] for row in before]
        assert [symbol for symbol, row in strip if 0 <= row + distance < 6] == [row[col] for row in after]


def test_cascade_frames_preserve_payout_and_falling_survivors():
    initial = generate_grid(seed=4)
    plain = resolve_scatter_cascades(initial, rng=random.Random(5))
    animated = resolve_scatter_cascades(initial, rng=random.Random(5), capture_frames=True)
    assert animated["grid"] == plain["grid"]
    assert animated["payout_multiplier"] == plain["payout_multiplier"]
    previous = initial
    for frame in animated["cascades"]:
        assert frame["before"] == previous
        landed = [[None] * 6 for _ in range(6)]
        paths = cascade_paths(frame["before"], frame["after"], frame["winning_symbols"])
        assert len(paths) == 36
        for symbol, col, source, destination in paths:
            assert source <= destination
            if source >= 0:
                assert symbol == frame["before"][source][col]
                assert symbol not in frame["winning_symbols"]
            landed[destination][col] = symbol
        assert landed == frame["after"]
        previous = frame["after"]
    assert previous == animated["grid"]
    assert initial == generate_grid(seed=4)


@pytest.mark.parametrize("animations_enabled", [True, False])
def test_spin_playback_pays_once_and_respects_pause(monkeypatch, animations_enabled):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    import pygame
    from game import game as game_module

    monkeypatch.setattr(game_module, "cv2", None)
    monkeypatch.setattr(game_module.TimbaRNGGame, "load_save", lambda self: None)
    monkeypatch.setattr(game_module.TimbaRNGGame, "save", lambda self: None)
    # A winning board is explicit now; an arbitrary spin can genuinely lose.
    monkeypatch.setattr(game_module, "generate_grid", lambda *args, **kwargs: [["coin"] * 6 for _ in range(6)])
    game = game_module.TimbaRNGGame()
    try:
        game.state = "game"
        game.settings.animations_enabled = animations_enabled
        game.perform_spin()
        game.update(game.spin_duration / 2)
        game.draw_game()
        assert game.stats["total_spins"] == 0
        game.update(game.spin_duration)
        assert game.animation_phase == "wins"
        game.draw_game()
        assert game.grid == game.current_scatter_cascades[0]["before"]
        assert game.stats["total_spins"] == 1
        paid_gold = game.player.gold
        game.perform_spin()
        assert game.player.gold == paid_gold
        game.paused_game = True
        game.update(20)
        assert game.cascade_index == 0
        assert game.cascade_timer == 0
        game.paused_game = False
        hold, fall = game.cascade_durations()
        game.update(hold + fall / 2)
        game.draw_game()
        game.update(100)
        game.draw_game()
        assert not game.animating
        assert game.animation_phase == "idle"
        assert game.grid == game.final_grid
        assert game.grid == game.current_scatter_cascades[-1]["after"]
        assert game.stats["total_spins"] == 1
        assert game.player.gold == paid_gold
    finally:
        pygame.quit()
