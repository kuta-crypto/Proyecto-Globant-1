import random
from pathlib import Path

import pytest

from game.abilities import ABILITY_DEFS, AbilityManager
from game.builds import spin_build, advance_charges
from game.characters import CHARACTERS, mastery_cost
from game.equipment import GEAR_DEFS, equipment_effects
from game.pets import PET_DEFS, pet_rank, companion_effects, roll_pet
from game.progression import PlayerProgress
from game.upgrades import UPGRADE_DEFS, max_upgrade_level, bulk_quote, upgrade_cost
from game.worlds import WORLD_DEFS


def test_every_world_and_pet_has_its_own_artwork():
    assets = Path(__file__).resolve().parents[1] / "assets"
    assert len(list((assets / "pets").glob("*.png"))) == len(PET_DEFS) == 25
    for key in PET_DEFS:
        assert (assets / "pets" / f"{key}.png").stat().st_size > 1000
    for key in WORLD_DEFS:
        assert (assets / "worlds" / f"world_{key}.png").stat().st_size > 1000


def test_legacy_upgrade_migration_refunds_retired_ranks_once():
    payload = dict(level=40, gold=350, points=120, upgrade_levels={"spin_speed": 12}, character_unlocks=["oliva", "labu"])
    migrated = PlayerProgress.from_dict(payload)
    assert migrated.gold == 350 + sum(int(30 * 1.08 ** rank) for rank in range(8,12))
    assert migrated.upgrade_levels["spin_speed"] == 8
    assert migrated.character_unlocks[:2] == ["oliva", "labu"]
    assert PlayerProgress.from_dict(migrated.to_dict()).to_dict() == migrated.to_dict()


@pytest.mark.parametrize("key", UPGRADE_DEFS)
def test_bulk_purchase_preserves_three_quarters_of_wallet(key):
    for gold in (0, 15, 100, 450, 5000):
        count, spent = bulk_quote(key, 0, gold)
        assert spent <= gold * .25
        assert count <= max_upgrade_level(key)
        assert spent == sum(upgrade_cost(key, rank) for rank in range(count))
        if count < max_upgrade_level(key):
            assert spent + upgrade_cost(key, count) > int(gold * .25)


def test_cooldowns_use_paid_spins_and_armed_skills_survive_save():
    manager = AbilityManager()
    for key in list(ABILITY_DEFS)[:4]:
        manager.buy_ability(key)
    assert all(manager.equip_ability(key) for key in list(ABILITY_DEFS)[:3])
    assert not manager.equip_ability("fortune")
    assert manager.activate_ability("luck_x2")
    assert not manager.activate_ability("luck_x2")
    restored = AbilityManager.from_dict(manager.to_dict())
    assert restored.armed == ["luck_x2"]
    restored.finish_spin(paid=True)
    assert restored.get_cooldown_remaining("luck_x2") == 4
    restored.finish_spin(paid=False)
    assert restored.get_cooldown_remaining("luck_x2") == 4
    for _ in range(4):
        restored.finish_spin(paid=True)
    assert restored.is_ability_ready("luck_x2")


@pytest.mark.parametrize("pet_id", PET_DEFS)
def test_pet_charge_fires_once_and_free_spins_do_not_charge(pet_id):
    pet = PET_DEFS[pet_id]
    key = "pet:" + pet_id
    charges = {key: pet["charge"]-1}
    args = ("oliva", pet_id, {}, {pet_id: 3}, charges, {})
    passive, _, _ = spin_build(*args, False, [])
    active, names, resets = spin_build(*args, True, [])
    assert pet["skill_name"] in names
    assert key in resets
    for effect in pet["burst"]:
        assert active.get(effect, 0) > passive.get(effect, 0)
    advance_charges("oliva", pet_id, charges, resets, True)
    assert charges[key] == 0
    advance_charges("oliva", pet_id, charges, [], False)
    assert charges[key] == 0
    _, names, _ = spin_build(*args, True, [])
    assert pet["skill_name"] not in names


def test_character_mastery_and_pet_bond_have_bounded_effects():
    assert [pet_rank(copies) for copies in (1,2,3,7,9,100)] == [1,1,2,4,5,5]
    assert mastery_cost(2) > mastery_cost(1)
    for definition in [*CHARACTERS.values(), *PET_DEFS.values()]:
        first = companion_effects(definition, 1, True)
        maximum = companion_effects(definition, 5, True)
        assert all(first[key] <= maximum[key] for key in first)
        if "free_spins" in first:
            assert first["free_spins"] == maximum["free_spins"] == 1


def test_gear_replacement_removes_the_previous_passive():
    assert equipment_effects({"Amuleto": "lucky_charm"})["luck"] == 3
    effects = equipment_effects({"Amuleto": "scholar_charm"})
    assert effects["luck"] == 0
    assert effects["xp"] == .2
    assert equipment_effects({"Anillo": "lucky_charm"}) == {}


def test_pet_guarantee_resets_only_the_corresponding_rarity_counters():
    pity = {"epic": 9, "legendary": 79, "mythic": 139}
    key = roll_pet(pity, random.Random(3))
    assert PET_DEFS[key]["rarity"] == "Mitica"
    assert pity == {"epic": 0, "legendary": 0, "mythic": 0}


@pytest.fixture
def game(monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    import pygame
    from game import game as module
    monkeypatch.setattr(module.TimbaRNGGame, "load_save", lambda self: None)
    monkeypatch.setattr(module.TimbaRNGGame, "save", lambda self: None)
    instance = module.TimbaRNGGame()
    instance.player = PlayerProgress(level=45, gold=10000, points=10000)
    yield instance
    pygame.quit()


def test_purchases_charge_once_and_respect_equipment_slots(game):
    game.handle_button("gear:lucky_charm")
    game.handle_button("gear:lucky_charm")
    assert game.player.gold == 10000-GEAR_DEFS["lucky_charm"]["cost"]
    game.handle_button("gear:scholar_charm")
    assert game.gear_equipped == {"Amuleto": "scholar_charm"}
    game.handle_button("ability:study")
    gold = game.player.gold
    game.handle_button("ability:study")
    assert game.player.gold == gold
    game.handle_button("activate:study")
    game.handle_button("toggle:study")
    assert "study" in game.abilities.equipped
    assert game.abilities.armed == ["study"]


def test_duplicate_pet_progress_and_mastery_purchase(game):
    game.pet_collection = ["comun_01"]
    game.pending_pets = ["comun_01", "comun_01"]
    game.finish_pet_pull()
    assert game.pet_collection == ["comun_01"]
    assert game.pet_copies["comun_01"] == 3
    assert game.player.points == 10200
    game.handle_button("mastery:oliva")
    assert game.character_mastery["oliva"] == 2
    assert game.player.points == 9900


@pytest.mark.parametrize("state", ["menu", "run_select", "roster", "shop", "equipment", "skills", "upgrades", "pets", "pet_collection", "inventory", "game"])
def test_screens_render_and_click_targets_stay_inside_window(game, state):
    game.state = state
    game.pet_collection = list(PET_DEFS)
    game.active_pet = "mitica_01"
    game.catalog_page = 1
    game.pet_page = 3
    game.render()
    assert game.ui_buttons
    for key, rect in game.ui_buttons.items():
        assert game.screen.get_rect().contains(rect), (state, key)


def test_animation_toggle_and_pause_freeze_background(game):
    game.update(.5)
    assert game.visual_time == .5
    game.settings.animations_enabled = False
    game.update(.5)
    assert game.visual_time == .5
    game.settings.animations_enabled = True
    game.paused_game = True
    game.update(.5)
    assert game.visual_time == .5


@pytest.mark.parametrize("ability,expected", [
    ("study", {"xp": 28}),
    ("collector", {"points": 57}),
    ("fortune", {"prize": 5}),
    ("cashback", {"refund": 4}),
    ("shield", {"prize": 8}),
    ("bonus_auto", {"free_spins": 3}),
    ("bonus_round", {"free_spins": 1}),
    ("jackpot_boost", {"prize": 7}),
    ("cascade_power", {"prize": 5}),
    ("resonance", {"skill": 5}),
    ("turbo", {"points": 41}),
    ("luck_x2", {"luck": 10}),
])
def test_each_ability_affects_the_resolved_spin(game, monkeypatch, ability, expected):
    from game import game as module
    from game.rng_system import DEFAULT_PROBABILITIES
    # Keep this test about skill effects, independent of paytable calibration.
    monkeypatch.setattr(module, "SCATTER_PAYOUT_SCALE", .37)
    game.active_pet = "comun_03" if ability == "resonance" else None
    grid = [["coin"]*6 for _ in range(6)]
    # A controlled award isolates skill effects from RNG and bonus triggers.
    def award(*args, **kwargs):
        frame = dict(before=grid, after=grid, counts={"coin":36}, winning_symbols=["coin"], payout_by_symbol={"sixty_seven":1.0} if ability=="jackpot_boost" else {"coin":1.0})
        return dict(grid=grid, cascades=[frame] * (10 if ability=="cascade_power" else 1), payout_multiplier=1.0, capped=False)
    monkeypatch.setattr(module, "resolve_scatter_cascades", award)
    game.abilities.buy_ability(ability)
    game.abilities.equip_ability(ability)
    game.handle_button("activate:"+ability)
    game.perform_spin()
    game.last_spin_result = grid
    if ability=="turbo":
        assert game.spin_duration < 2.6
    if ability=="luck_x2":
        assert game.spin_effects["luck"] == 10
        assert game.spin_probabilities["sixty_seven"] > DEFAULT_PROBABILITIES["sixty_seven"]
    game.update(game.spin_duration)
    for key, value in expected.items():
        actual = game.stats["xp_earned"] if key=="xp" else game.stats["points_earned"] if key=="points" else game.bonus_spins_remaining if key=="free_spins" else game.spin_effects["luck"] if key=="luck" else game.last_reward[key]
        assert actual == value
    assert not game.abilities.armed
    assert game.stats["total_spins"] == 1


def test_full_profile_save_load_preserves_companions_and_prepared_skill(monkeypatch, tmp_path):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    monkeypatch.chdir(tmp_path)
    import pygame
    from game.game import TimbaRNGGame
    game = TimbaRNGGame()
    game.pet_collection = ["rara_01"]
    game.pet_copies = {"rara_01": 5}
    game.active_pet = "rara_01"
    game.character_mastery = {"oliva": 3}
    game.companion_charges = {"character:oliva": 2, "pet:rara_01": 4}
    game.abilities.buy_ability("study")
    game.abilities.equip_ability("study")
    game.abilities.activate_ability("study")
    game.save()
    restored = TimbaRNGGame()
    assert restored.active_pet == "rara_01"
    assert restored.pet_copies == game.pet_copies
    assert restored.character_mastery == game.character_mastery
    assert restored.companion_charges == game.companion_charges
    assert restored.active_ability_effects == ["study"]
    assert restored.active_ability_effects is restored.abilities.armed
    pygame.quit()
