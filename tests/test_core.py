import json

from game.abilities import AbilityManager
from game.characters import get_all_characters, get_character_by_id
from game.grid import find_lines
from game.progression import PlayerProgress, world_multiplier
from game.rng_system import DEFAULT_PROBABILITIES, check_bonus, generate_grid
from game.save_system import load_game, save_game
from game.scoring import evaluate_lines, line_gold_reward, line_xp_reward
from game.upgrades import upgrade_cost, max_upgrade_level


def test_generate_grid_6x6():
    grid = generate_grid(seed=42)
    assert len(grid) == 6
    assert all(len(row) == 6 for row in grid)
    assert set(cell for row in grid for cell in row).issubset(set(DEFAULT_PROBABILITIES))


def test_rng_generation_and_bonus_logic():
    grid = [
        ["joker", "joker", "joker", "joker", "joker", "joker"],
        ["joker", "joker", "joker", "joker", "joker", "joker"],
        ["joker", "joker", "joker", "joker", "joker", "joker"],
        ["joker", "joker", "joker", "joker", "joker", "joker"],
        ["joker", "joker", "joker", "joker", "joker", "joker"],
        ["coin", "coin", "coin", "coin", "coin", "coin"],
    ]
    assert check_bonus(grid) is True


def test_detect_horizontal_vertical_and_diagonal_lines():
    grid = [
        ["coin", "coin", "coin", "seven", "coin", "coin"],
        ["seven", "coin", "coin", "coin", "coin", "coin"],
        ["coin", "seven", "coin", "coin", "coin", "coin"],
        ["coin", "coin", "seven", "coin", "coin", "coin"],
        ["coin", "coin", "coin", "coin", "coin", "coin"],
        ["coin", "coin", "coin", "coin", "coin", "coin"],
    ]
    lines = find_lines(grid)
    assert any(line["orientation"] == "horizontal" and line["length"] >= 3 for line in lines)
    assert any(line["orientation"] == "vertical" and line["length"] >= 3 for line in lines)
    assert any(line["orientation"] == "diagonal" and line["length"] >= 3 for line in lines)


def test_score_and_rewards():
    lines = [{"symbol": "coin", "length": 3, "orientation": "horizontal"}]
    result = evaluate_lines(lines)
    assert result["points"] == 10
    assert result["gold"] == 5
    assert result["xp"] >= 10
    assert line_gold_reward(4) == 10
    assert line_xp_reward(5) >= 30


def test_player_level_and_world_unlock():
    player = PlayerProgress()
    player.apply_xp(300)
    assert player.level >= 2
    assert 2 not in player.unlocked_worlds

    player = PlayerProgress(level=40)
    assert 2 in player.unlocked_worlds
    assert player.current_world == 1


def test_upgrade_cost_and_max_level():
    cost = upgrade_cost("spin_speed", 0)
    assert cost > 0
    assert upgrade_cost("spin_speed", 7) > upgrade_cost("spin_speed", 0)
    player = PlayerProgress(gold=1000, upgrade_levels={"spin_speed": max_upgrade_level("spin_speed")})
    assert player.buy_upgrade("spin_speed") == (False, 0)
    assert player.gold == 1000


def test_skill_cooldown():
    manager = AbilityManager()
    manager.buy_ability("bonus_auto")
    manager.equip_ability("bonus_auto")
    manager.activate_ability("bonus_auto")
    assert manager.get_cooldown_remaining("bonus_auto") > 0
    assert manager.is_ability_ready("bonus_auto") is False


def test_save_and_load_game():
    player = PlayerProgress(level=40, xp=120, gold=250, points=900, current_world=2, unlocked_worlds=[1, 2])
    path = "test_save.json"
    save_game(player, path)
    loaded = load_game(path)
    assert loaded["level"] == 40
    assert loaded["gold"] == 250
    assert loaded["current_world"] == 2


def test_character_unlocks():
    characters = get_all_characters()
    assert len(characters) == 8
    assert get_character_by_id(1)["name"]
    assert get_character_by_id(2)["unlock_level"] == 4


def test_world_multiplier_is_progressive():
    assert world_multiplier(1) == 1.0
    assert world_multiplier(2) > world_multiplier(1)
    assert world_multiplier(6) > world_multiplier(5)
