"""Deterministic companion charges and additive build effects."""

from game.characters import CHARACTERS
from game.equipment import equipment_effects
from game.pets import PET_DEFS, companion_effects, pet_rank


def spin_build(character_id, pet_id, mastery, copies, charges, equipped, paid, armed):
    character = CHARACTERS[character_id]
    char_key = "character:" + character_id
    char_charged = paid and charges.get(char_key, 0) + 1 >= character["charge"]
    effects = equipment_effects(equipped)
    activated = []
    resets = []

    def merge(values):
        for key, value in values.items():
            effects[key] = effects.get(key, 0) + value

    merge(companion_effects(character, mastery.get(character_id, 1), char_charged))
    if char_charged:
        activated.append(character["skill_name"])
        resets.append(char_key)
    if pet_id in PET_DEFS:
        pet = PET_DEFS[pet_id]
        pet_key = "pet:" + pet_id
        pet_charged = (paid and charges.get(pet_key, 0) + 1 >= pet["charge"]) or "resonance" in armed
        merge(companion_effects(pet, pet_rank(copies.get(pet_id, 1)), pet_charged))
        if pet_charged:
            activated.append(pet["skill_name"])
            resets.append(pet_key)
        if pet["role"] == character["role"]:
            merge({"payout": .05, "xp": .10})
    active_effects = {
        "luck_x2": {"luck": 10}, "turbo": {"speed": .25, "points": .15},
        "fortune": {"payout": .50}, "cashback": {"refund": .40},
        "jackpot_boost": {"jackpot": 1.0}, "bonus_round": {"free_spins": 1},
        "study": {"xp": .75}, "collector": {"points": .60},
    }
    for key in armed:
        merge(active_effects.get(key, {}))
    return effects, activated, resets


def advance_charges(character_id, pet_id, charges, resets, paid):
    if paid:
        for key in ("character:" + character_id, "pet:" + str(pet_id)):
            if key.endswith(":None"):
                continue
            charges[key] = charges.get(key, 0) + 1
    for key in resets:
        charges[key] = 0
