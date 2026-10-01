CHARACTERS = {
    "oliva": {
        "id": "oliva", "name": "Oliva", "unlock_level": 1, "color": (134, 111, 255),
        "description": "El punto de partida. Equilibrado y confiable.",
        "skill": "Sinergia: obtiene +2% de premio.",
        "luck": 0, "payout": 0.02, "xp": 0.0, "bonus": 0,
    },
    "labu": {
        "id": "labu", "name": "Labu", "unlock_level": 20, "color": (66, 202, 158),
        "description": "Siempre encuentra una oportunidad para crecer.",
        "skill": "Aprendizaje: gana 12% más de experiencia.",
        "luck": 0, "payout": 0.0, "xp": 0.12, "bonus": 0,
    },
    "lauta": {
        "id": "lauta", "name": "Lauta", "unlock_level": 40, "color": (65, 163, 241),
        "description": "Lee los rodillos y anticipa los símbolos raros.",
        "skill": "Intuición: suma 3 niveles de suerte.",
        "luck": 3, "payout": 0.0, "xp": 0.0, "bonus": 0,
    },
    "jere": {
        "id": "jere", "name": "Jere", "unlock_level": 60, "color": (247, 170, 63),
        "description": "Especialista en activar rondas especiales.",
        "skill": "Racha: facilita el bonus y suma 4% a los premios.",
        "luck": 0, "payout": 0.04, "xp": 0.0, "bonus": 1,
    },
    "franco": {
        "id": "franco", "name": "Franco", "unlock_level": 80, "color": (244, 91, 130),
        "description": "Apuesta fuerte y convierte premios en progreso.",
        "skill": "Gran premio: +10% de pago y +8% de experiencia.",
        "luck": 0, "payout": 0.10, "xp": 0.08, "bonus": 0,
    },
    "alejo": {
        "id": "alejo", "name": "Alejo", "unlock_level": 100, "color": (97, 183, 232),
        "description": "Observa cada giro antes de tomar riesgos.",
        "skill": "Lectura precisa: +2 de suerte y +3% de premio.",
        "luck": 2, "payout": 0.03, "xp": 0.0, "bonus": 0,
    },
    "alba": {
        "id": "alba", "name": "Alba", "unlock_level": 120, "color": (239, 142, 198),
        "description": "Encuentra oportunidades para mantener la racha.",
        "skill": "Buena estrella: +1 de bonus y +10% de experiencia.",
        "luck": 0, "payout": 0.0, "xp": 0.10, "bonus": 1,
    },
    "berta": {
        "id": "berta", "name": "Berta", "unlock_level": 140, "color": (239, 183, 91),
        "description": "Una apuesta firme puede convertirse en un gran premio.",
        "skill": "Apuesta firme: +1 de suerte y +8% de premio.",
        "luck": 1, "payout": 0.08, "xp": 0.0, "bonus": 0,
    },
}


_CHARACTER_SKILLS = {
    "oliva": (1, "Reserva", "Bolsillo secreto", 4, {"payout": .04}, {"gold": 8}),
    "labu": (4, "Estudio", "Clase magistral", 4, {"xp": .18}, {"xp": .80}),
    "lauta": (8, "Fortuna", "Lectura perfecta", 5, {"luck": 4}, {"luck": 12}),
    "jere": (12, "Impulso", "Hora extra", 7, {"payout": .06}, {"free_spins": 1}),
    "franco": (18, "Impulso", "Golpe fuerte", 5, {"payout": .12}, {"payout": .65}),
    "alejo": (24, "Reserva", "Plan B", 4, {"refund": .08}, {"refund": .50}),
    "alba": (32, "Estudio", "Nueva estrella", 5, {"xp": .15, "points": .10}, {"xp": .50, "points": .70}),
    "berta": (40, "Coleccion", "Botin completo", 5, {"points": .20}, {"points": 1.0, "gold": 10}),
}

from game.pets import describe_effects

for key, (level, role, name, charge, passive, burst) in _CHARACTER_SKILLS.items():
    CHARACTERS[key].update(unlock_level=level, role=role, skill_name=name, charge=charge, passive=passive, burst=burst)
    CHARACTERS[key]["skill"] = f"{name}: {describe_effects(burst)} cada {charge} giros."
    CHARACTERS[key].update(luck=passive.get("luck", 0), payout=passive.get("payout", 0), xp=passive.get("xp", 0), bonus=0)


def mastery_cost(rank):
    return 300 * max(1, rank) ** 2


def get_all_characters():
    return list(CHARACTERS.values())


def get_character_by_id(character_id):
    if character_id == "negro":
        character_id = "oliva"
    if character_id in CHARACTERS:
        return CHARACTERS[character_id]
    if isinstance(character_id, int) and 1 <= character_id <= len(CHARACTERS):
        return list(CHARACTERS.values())[character_id - 1]
    return None
