import random

RARITY_ORDER = ["Comun", "Rara", "Epica", "Legendaria", "Mitica"]
RARITY_CONFIG = {
    "Comun": {"luck": 1, "payout": 0.01, "xp": 0.01, "bonus": 0, "free_spin_chance": 0.005, "color": (157, 164, 174), "skill": "Apoyo: +1 suerte, +1% premios y 0.5% de giro gratis."},
    "Rara": {"luck": 2, "payout": 0.03, "xp": 0.03, "bonus": 0, "free_spin_chance": 0.01, "color": (74, 172, 112), "skill": "Instinto: +2 suerte, +3% premios, +3% XP y 1% de giro gratis."},
    "Epica": {"luck": 3, "payout": 0.06, "xp": 0.05, "bonus": 1, "free_spin_chance": 0.02, "color": (151, 85, 224), "skill": "Aura: +3 suerte, +6% premios, +5% XP y 2% de giro gratis."},
    "Legendaria": {"luck": 5, "payout": 0.10, "xp": 0.08, "bonus": 1, "free_spin_chance": 0.03, "color": (237, 163, 54), "skill": "Fortuna: +5 suerte, +10% premios, +8% XP y 3% de giro gratis."},
    "Mitica": {"luck": 7, "payout": 0.14, "xp": 0.12, "bonus": 2, "free_spin_chance": 0.04, "color": (239, 87, 155), "skill": "Destino: +7 suerte, +14% premios, +12% XP y 4% de giro gratis."},
}

_PET_NAMES = {
    "Comun": ["Chispa", "Dado", "Miga", "Nube", "Pipo", "Tuerca", "Bombo", "Tiki", "Monedita", "Trueno"],
    "Rara": ["Zorrito", "Lunita", "Rayo", "Cactus", "Cometa", "Golem", "Acuarela"],
    "Epica": ["Dragoncito", "Fenix", "Oraculo", "Kitsune", "Nebulon"],
    "Legendaria": ["Leon Solar", "Serpiente Celeste"],
    "Mitica": ["Guardian del Jackpot"],
}
_PET_WEIGHTS = {"Comun": 0.68, "Rara": 0.20, "Epica": 0.09, "Legendaria": 0.025, "Mitica": 0.005}
_PET_RANK = {rarity: i for i, rarity in enumerate(RARITY_ORDER)}
PET_DEFS = {}
for rarity, names in _PET_NAMES.items():
    for i, name in enumerate(names, 1):
        pet_id = f"{rarity.lower()}_{i:02d}"
        config = RARITY_CONFIG[rarity]
        PET_DEFS[pet_id] = {"id": pet_id, "name": name, "rarity": rarity, **config}


def roll_pet(pity: dict, rng=None) -> str:
    """Roll a pet and advance independent 10/80/140-pull rarity guarantees."""
    rng = rng or random.Random()
    next_counts = {tier: int(pity.get(tier, 0)) + 1 for tier in ("epic", "legendary", "mythic")}
    if next_counts["mythic"] >= 140:
        rarity = "Mitica"
    elif next_counts["legendary"] >= 80:
        rarity = "Legendaria"
    elif next_counts["epic"] >= 10:
        rarity = "Epica"
    else:
        rarity = rng.choices(list(_PET_WEIGHTS), weights=list(_PET_WEIGHTS.values()), k=1)[0]
    for tier, minimum_rarity in (("epic", "Epica"), ("legendary", "Legendaria"), ("mythic", "Mitica")):
        pity[tier] = 0 if _PET_RANK[rarity] >= _PET_RANK[minimum_rarity] else next_counts[tier]
    choices = [pet_id for pet_id, pet in PET_DEFS.items() if pet["rarity"] == rarity]
    return rng.choice(choices)


def rarity_color(rarity: str):
    return RARITY_CONFIG[rarity]["color"]


# Each companion has its own passive and charged skill. Charge advances only
# while that companion participates in a paid spin; changing pets keeps it.
_SKILLS = [
    ("Impulso", "Ascuas", 4, {"payout": .04}, {"payout": .25}),
    ("Fortuna", "Doble dado", 5, {"luck": 1}, {"luck": 8}),
    ("Reserva", "Migas de oro", 4, {"travel_gold": 1}, {"gold": 5}),
    ("Reserva", "Colchon de nube", 5, {"refund": .03}, {"refund": .35}),
    ("Estudio", "Primer vuelo", 4, {"xp": .08}, {"xp": .50}),
    ("Impulso", "Resorte", 4, {"speed": .05}, {"payout": .20, "points": .15}),
    ("Coleccion", "Redoble", 5, {"points": .08}, {"points": .60}),
    ("Estudio", "Memoria del bosque", 5, {"xp": .06}, {"xp": .40, "gold": 3}),
    ("Reserva", "Alcancia", 6, {"travel_gold": 1}, {"gold": 9}),
    ("Impulso", "Descarga", 5, {"payout": .03}, {"payout": .35}),
    ("Fortuna", "Astucia", 5, {"luck": 3}, {"luck": 10}),
    ("Estudio", "Luz de luna", 4, {"xp": .12}, {"xp": .70}),
    ("Impulso", "Carrera electrica", 4, {"speed": .10}, {"payout": .35}),
    ("Reserva", "Espinas", 5, {"refund": .06}, {"refund": .45}),
    ("Coleccion", "Estela", 5, {"points": .15}, {"points": .80}),
    ("Reserva", "Guardia de piedra", 6, {"travel_gold": 2}, {"refund": .65}),
    ("Coleccion", "Lluvia de color", 4, {"points": .10}, {"points": .50, "xp": .30}),
    ("Impulso", "Aliento jade", 5, {"payout": .08}, {"payout": .60}),
    ("Reserva", "Renacer", 7, {"refund": .08}, {"free_spins": 1}),
    ("Estudio", "Vision", 5, {"xp": .18}, {"xp": 1.0}),
    ("Fortuna", "Tres colas", 6, {"luck": 4}, {"luck": 14, "payout": .20}),
    ("Coleccion", "Polvo estelar", 5, {"points": .20}, {"points": 1.0}),
    ("Impulso", "Amanecer", 6, {"payout": .12}, {"payout": .90}),
    ("Fortuna", "Marea celeste", 6, {"luck": 5}, {"luck": 16, "points": .40}),
    ("Fortuna", "Destino dorado", 8, {"luck": 5, "payout": .10}, {"free_spins": 1, "payout": .80}),
]

EFFECT_NAMES = {"payout": "premios", "xp": "XP", "points": "puntos", "refund": "reembolso", "luck": "suerte", "speed": "velocidad", "gold": "oro", "travel_gold": "oro de viaje", "free_spins": "giro gratis"}


def describe_effects(effects):
    return ", ".join(
        f"+{value:.0%} {EFFECT_NAMES[key]}" if key in ("payout", "xp", "points", "refund", "speed")
        else f"+{value:g} {EFFECT_NAMES[key]}"
        for key, value in effects.items()
    )


for pet, (role, name, charge, passive, burst) in zip(PET_DEFS.values(), _SKILLS):
    pet.update(role=role, skill_name=name, charge=charge, passive=passive, burst=burst)
    pet["skill"] = f"{name}: {describe_effects(burst)} cada {charge} giros pagos."
    # Retain old fields for save compatibility; the new effect resolver owns math.
    pet.update(luck=0, payout=0.0, xp=0.0, bonus=0, free_spin_chance=0.0)


def pet_rank(copies):
    return min(5, 1 + max(0, copies - 1) // 2)


def companion_effects(definition, rank, charged):
    scale = 1 + .15 * (max(1, min(5, rank)) - 1)
    effects = {key: value * scale for key, value in definition["passive"].items()}
    if charged:
        for key, value in definition["burst"].items():
            effects[key] = effects.get(key, 0) + (value if key == "free_spins" else value * scale)
    return effects


def skill_description(definition, rank=1):
    passive = companion_effects(definition, rank, False)
    total = companion_effects(definition, rank, True)
    burst = {key: total[key] - passive.get(key, 0) for key in definition["burst"]}
    return f"{definition['skill_name']}: {describe_effects(burst)} cada {definition['charge']} giros pagos."
