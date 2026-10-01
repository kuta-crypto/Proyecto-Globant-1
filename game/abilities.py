from typing import Dict, List

ABILITY_DEFS = {
    "bonus_auto": {"name": "Bonus automatico", "cost": 250, "purchase": True, "cooldown": 45},
    "luck_x2": {"name": "2x Suerte", "cost": 180, "purchase": True, "cooldown": 35},
    "turbo": {"name": "Turbo", "cost": 150, "purchase": True, "cooldown": 30},
    "fortune": {"name": "Fortuna", "cost": 220, "purchase": True, "cooldown": 45},
    "cashback": {"name": "Reembolso", "cost": 320, "purchase": True, "cooldown": 50},
    "jackpot_boost": {"name": "Caza jackpot", "cost": 500, "purchase": True, "cooldown": 70},
    "bonus_round": {"name": "Ronda extra", "cost": 650, "purchase": True, "cooldown": 90},
}

_CATALOG = {
    "bonus_auto": ("Llamada VIP", 180, 12, 8, "Activa un bonus de tres giros.", "ticket"),
    "luck_x2": ("Sexto sentido", 55, 4, 1, "+10 suerte en el siguiente giro.", "clover"),
    "turbo": ("Sobre marcha", 35, 3, 1, "Giro mas rapido y +15% puntos.", "bolt"),
    "fortune": ("Fortuna", 100, 7, 4, "+50% al premio del siguiente giro.", "coin"),
    "cashback": ("Plan de vuelta", 75, 5, 1, "Recupera 40% de la apuesta pagada.", "shield"),
    "jackpot_boost": ("Caza jackpot", 150, 8, 8, "+100% al premio de jackpot.", "crown"),
    "bonus_round": ("Ultima ronda", 130, 8, 8, "Otorga un giro gratis al terminar.", "moon"),
    "study": ("Concentracion", 45, 4, 1, "+75% XP en el siguiente giro.", "book"),
    "collector": ("Manos rapidas", 60, 4, 4, "+60% puntos en el siguiente giro.", "star"),
    "shield": ("Apuesta cubierta", 95, 6, 4, "Premio minimo: 80% de la apuesta pagada.", "shield"),
    "resonance": ("Resonancia", 160, 7, 12, "Activa la habilidad cargada de tu mascota.", "leaf"),
    "cascade_power": ("Efecto domino", 120, 6, 8, "+4% premio por cascada, hasta +40%.", "compass"),
}
for key, (name, cost, cooldown, level, description, icon) in _CATALOG.items():
    ABILITY_DEFS[key] = dict(name=name, cost=cost, cooldown=cooldown, level=level, description=description, icon=icon, purchase=True)

MAX_EQUIPPED_ABILITIES = 3


class AbilityManager:
    def __init__(self):
        self.purchased = []
        self.equipped = []
        self.armed = []
        self.cooldowns = {name: 0.0 for name in ABILITY_DEFS}

    def buy_ability(self, ability_id: str) -> bool:
        if ability_id not in ABILITY_DEFS or ability_id in self.purchased:
            return False
        self.purchased.append(ability_id)
        return True

    def equip_ability(self, ability_id: str) -> bool:
        if ability_id not in self.purchased:
            return False
        if ability_id not in self.equipped:
            if len(self.equipped) >= MAX_EQUIPPED_ABILITIES:
                return False
            self.equipped.append(ability_id)
        return True

    def activate_ability(self, ability_id: str) -> bool:
        if ability_id not in ABILITY_DEFS or ability_id not in self.purchased or ability_id not in self.equipped:
            return False
        if not self.is_ability_ready(ability_id):
            return False
        self.cooldowns[ability_id] = ABILITY_DEFS[ability_id]["cooldown"]
        self.armed.append(ability_id)
        return True

    def get_cooldown_remaining(self, ability_id: str) -> float:
        return max(0.0, self.cooldowns.get(ability_id, 0.0))

    def is_ability_ready(self, ability_id: str) -> bool:
        return ability_id not in self.armed and self.get_cooldown_remaining(ability_id) <= 0

    def tick(self, delta: float) -> None:
        """Advance cooldowns in completed paid spins, never wall-clock seconds."""
        for name in self.cooldowns:
            if self.cooldowns[name] > 0:
                self.cooldowns[name] = max(0.0, self.cooldowns[name] - delta)

    def finish_spin(self, paid=True):
        if paid:
            # Newly used skills start their full cooldown after this spin.
            for name in self.cooldowns:
                if name not in self.armed:
                    self.cooldowns[name] = max(0, self.cooldowns[name] - 1)
        self.armed.clear()

    def to_dict(self) -> Dict[str, object]:
        return {"version": 2, "purchased": self.purchased, "equipped": self.equipped, "cooldowns": self.cooldowns, "armed": self.armed}

    @classmethod
    def from_dict(cls, payload: Dict[str, object]) -> "AbilityManager":
        manager = cls()
        manager.purchased = [name for name in payload.get("purchased", []) if name in ABILITY_DEFS]
        manager.equipped = list(dict.fromkeys(name for name in payload.get("equipped", []) if name in manager.purchased))[:MAX_EQUIPPED_ABILITIES]
        if payload.get("version", 1) >= 2:
            manager.cooldowns.update({k: max(0, min(ABILITY_DEFS[k]["cooldown"], int(v))) for k, v in payload.get("cooldowns", {}).items() if k in ABILITY_DEFS})
            manager.armed = list(dict.fromkeys(name for name in payload.get("armed", []) if name in manager.equipped))
        return manager
