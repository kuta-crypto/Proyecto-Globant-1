WORLD_DEFS = {
    1: {"id": 1, "name": "Timba Central", "theme": "Neon y suerte", "unlock_level": 1, "payout": 1.0, "xp": 1.0, "luck": 0, "bonus": 0, "color": (126, 92, 228), "description": "El salon clasico para aprender los rodillos."},
    2: {"id": 2, "name": "Metro Neon", "theme": "Premios rapidos", "unlock_level": 40, "payout": 1.08, "xp": 1.05, "luck": 0, "bonus": 0, "color": (44, 193, 224), "description": "Luces veloces y pagos ligeramente mayores."},
    3: {"id": 3, "name": "Bosque Jade", "theme": "Simbolos raros", "unlock_level": 80, "payout": 1.05, "xp": 1.10, "luck": 2, "bonus": 1, "color": (75, 200, 123), "description": "La suerte acompana a quien explora."},
    4: {"id": 4, "name": "Casino Obsidiana", "theme": "Jackpot", "unlock_level": 120, "payout": 1.14, "xp": 1.08, "luck": 1, "bonus": 1, "color": (234, 112, 75), "description": "Un mundo de apuestas altas y grandes premios."},
    5: {"id": 5, "name": "Galaxia Dorada", "theme": "Ronda final", "unlock_level": 160, "payout": 1.18, "xp": 1.15, "luck": 2, "bonus": 1, "color": (246, 194, 70), "description": "La frontera final, con bonus y experiencia mejorados."},
}

for world, level in zip(WORLD_DEFS.values(), (1, 8, 18, 30, 45)):
    world["unlock_level"] = level
    world["travel_gold"] = 4 + world["id"] * 2
    world["background"] = f"world_{world['id']}.png"
