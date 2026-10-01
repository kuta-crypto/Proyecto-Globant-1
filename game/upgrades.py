"""Short, affordable upgrade tracks with a predictable gold cost."""

UPGRADE_DEFS = {
    "spin_speed": ("Rodillos ligeros", 12, 8, .10, "s menos por giro"),
    "luck": ("Ojo de halcon", 18, 10, 1, "suerte"),
    "bonus_chance": ("Invitacion VIP", 24, 8, 1, "bonus"),
    "point_gain": ("Coleccionista", 16, 10, .08, "puntos"),
    "xp_gain": ("Aprendiz", 16, 10, .08, "XP"),
    "payout": ("Caja fuerte", 25, 12, .03, "premios"),
    "jackpot": ("Siete dorado", 30, 8, .12, "jackpot"),
    "bet_discount": ("Pase de socio", 28, 5, .02, "descuento"),
    "bonus_spins": ("Tiempo extra", 45, 3, 1, "giro extra de bonus"),
    "safety_net": ("Fondo de reserva", 20, 8, 2, "oro de rescate"),
}
UPGRADE_BASE_COSTS = {key: value[1] for key, value in UPGRADE_DEFS.items()}


def upgrade_cost(name: str, level: int) -> int:
    level = max(0, level)
    return round(UPGRADE_BASE_COSTS.get(name, 20) * (1 + .5 * level + .10 * level * level))


def max_upgrade_level(name=None) -> int:
    return UPGRADE_DEFS[name][2] if name in UPGRADE_DEFS else max(item[2] for item in UPGRADE_DEFS.values())


def upgrade_effect(name, level):
    return min(max(0, level), max_upgrade_level(name)) * UPGRADE_DEFS[name][3]


def effect_label(name, level):
    value = upgrade_effect(name, level)
    unit = UPGRADE_DEFS[name][4]
    if name in ("point_gain", "xp_gain", "payout", "jackpot", "bet_discount"):
        return f"{value:.0%} {unit}"
    return f"{value:g} {unit}"


def bulk_quote(name, level, gold, fraction=.25):
    """A multi-buy spends at most 25% of the balance shown before purchase."""
    budget = int(max(0, gold) * fraction)
    count = spent = 0
    while level + count < max_upgrade_level(name):
        cost = upgrade_cost(name, level + count)
        if spent + cost > budget:
            break
        count += 1
        spent += cost
    return count, spent
