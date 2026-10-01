"""Six equipment slots, each with a meaningful alternative."""

GEAR_DEFS = {
    "lucky_charm": {"name": "Amuleto del zorro", "slot": "Amuleto", "cost": 55, "level": 1, "description": "+3 suerte.", "luck": 3, "icon": "clover"},
    "golden_boots": {"name": "Botas del metro", "slot": "Botas", "cost": 45, "level": 1, "description": "Giros 18% mas rapidos.", "speed": .18, "icon": "bolt"},
    "coin_pendant": {"name": "Moneda antigua", "slot": "Reliquia", "cost": 80, "level": 4, "description": "+8% premios y +1 oro de viaje.", "payout": .08, "travel_gold": 1, "icon": "coin"},
    "payout_ring": {"name": "Anillo de cobre", "slot": "Anillo", "cost": 95, "level": 4, "description": "+12% a los premios.", "payout": .12, "icon": "ring"},
    "bonus_badge": {"name": "Pase nocturno", "slot": "Insignia", "cost": 140, "level": 8, "description": "+1 giro cuando se activa un bonus.", "bonus_spins": 1, "icon": "ticket"},
    "jackpot_crown": {"name": "Corona obsidiana", "slot": "Corona", "cost": 220, "level": 12, "description": "+40% jackpot.", "jackpot": .4, "icon": "crown"},
    "scholar_charm": {"name": "Talisman del buho", "slot": "Amuleto", "cost": 65, "level": 1, "description": "+20% XP.", "xp": .2, "icon": "book"},
    "wanderer_boots": {"name": "Botas de viajero", "slot": "Botas", "cost": 90, "level": 4, "description": "+2 oro de viaje por giro pago.", "travel_gold": 2, "icon": "compass"},
    "jade_relic": {"name": "Hoja de jade", "slot": "Reliquia", "cost": 130, "level": 8, "description": "+5 suerte y +10% puntos.", "luck": 5, "points": .1, "icon": "leaf"},
    "ward_ring": {"name": "Anillo guardia", "slot": "Anillo", "cost": 115, "level": 4, "description": "Devuelve 10% de la apuesta pagada.", "refund": .1, "icon": "shield"},
    "collector_badge": {"name": "Pin del coleccionista", "slot": "Insignia", "cost": 120, "level": 8, "description": "+25% puntos para mascotas y maestria.", "points": .25, "icon": "star"},
    "sage_crown": {"name": "Corona astral", "slot": "Corona", "cost": 190, "level": 12, "description": "+20% XP y +15% puntos.", "xp": .2, "points": .15, "icon": "moon"},
}


def equipment_effects(equipped):
    effects = {}
    for slot, item_id in equipped.items():
        item = GEAR_DEFS.get(item_id, {})
        if item.get("slot") != slot:
            continue
        for key in ("luck", "speed", "payout", "travel_gold", "xp", "points", "refund", "bonus_spins", "jackpot"):
            effects[key] = effects.get(key, 0) + item.get(key, 0)
    return effects
