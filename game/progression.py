from typing import Dict, List

from game.characters import CHARACTERS
from game.upgrades import UPGRADE_BASE_COSTS, max_upgrade_level, upgrade_cost
from game.worlds import WORLD_DEFS

MAX_UPGRADE_LEVEL = max_upgrade_level()
CHARACTER_IDS = list(CHARACTERS)
LEGACY_CHARACTER_IDS = {"negro": "oliva"}


def canonical_character_id(character_id: str) -> str:
    return LEGACY_CHARACTER_IDS.get(character_id, character_id)


def world_multiplier(world_number: int) -> float:
    if world_number <= 1:
        return 1.0
    return 1.67 ** (world_number - 1)


def xp_to_next_level(level: int) -> int:
    return max(1, int(80 + 35 * level ** 1.15))


class PlayerProgress:
    def __init__(self, level: int = 1, xp: int = 0, gold: int = 100, points: int = 0,
                 current_world: int = 1, unlocked_worlds: List[int] | None = None,
                 upgrade_levels: Dict[str, int] | None = None,
                 character_unlocks: List[str] | None = None,
                 current_character: str = "oliva"):
        self.level = max(1, int(level))
        self.xp = max(0, int(xp))
        self.gold = max(0, int(gold))
        self.points = max(0, int(points))
        self.current_world = max(1, min(5, int(current_world)))
        self.unlocked_worlds = sorted(set(int(w) for w in (unlocked_worlds or [1]) if 1 <= int(w) <= 5))
        self.max_upgrade_level = MAX_UPGRADE_LEVEL
        raw_character_unlocks = character_unlocks or ["oliva"]
        self.character_unlocks = []
        for character_id in raw_character_unlocks:
            character_id = canonical_character_id(character_id)
            if character_id in CHARACTER_IDS and character_id not in self.character_unlocks:
                self.character_unlocks.append(character_id)
        current_character = canonical_character_id(current_character)
        self.current_character = current_character if current_character in CHARACTER_IDS else "oliva"
        self.upgrade_levels = {
            name: max(0, min(max_upgrade_level(name), int((upgrade_levels or {}).get(name, 0))))
            for name in UPGRADE_BASE_COSTS
        }
        self.refresh_unlocks()
        if self.current_world not in self.unlocked_worlds:
            self.current_world = max(self.unlocked_worlds, default=1)
        if self.current_character not in self.character_unlocks:
            self.current_character = "oliva"

    def refresh_unlocks(self) -> None:
        for world_number in range(2, 6):
            if self.level >= WORLD_DEFS[world_number]["unlock_level"] and world_number not in self.unlocked_worlds:
                self.unlocked_worlds.append(world_number)
        self.unlocked_worlds.sort()
        for character_id, character in CHARACTERS.items():
            required_level = character["unlock_level"]
            if self.level >= required_level and character_id not in self.character_unlocks:
                self.character_unlocks.append(character_id)

    def buy_upgrade(self, name: str) -> tuple[bool, int]:
        if name not in self.upgrade_levels:
            return False, 0
        level = self.upgrade_levels[name]
        if level >= max_upgrade_level(name):
            return False, 0
        cost = upgrade_cost(name, level)
        if self.gold < cost:
            return False, cost
        self.gold -= cost
        self.upgrade_levels[name] += 1
        return True, cost

    def apply_xp(self, amount: int) -> bool:
        self.xp += max(0, int(amount))
        leveled = False
        while self.xp >= xp_to_next_level(self.level):
            self.xp -= xp_to_next_level(self.level)
            self.level += 1
            leveled = True
        self.refresh_unlocks()
        return leveled

    def unlock_world(self, world_number: int) -> bool:
        if not self.can_unlock_world(world_number):
            return False
        if world_number not in self.unlocked_worlds:
            self.unlocked_worlds.append(world_number)
            self.unlocked_worlds.sort()
            return True
        return False

    def can_unlock_world(self, world_number: int) -> bool:
        if world_number == 1:
            return True
        return world_number in WORLD_DEFS and self.level >= WORLD_DEFS[world_number]["unlock_level"]

    def to_dict(self) -> Dict[str, object]:
        return {
            "economy_version": 2,
            "level": self.level, "xp": self.xp, "gold": self.gold, "points": self.points,
            "current_world": self.current_world, "unlocked_worlds": self.unlocked_worlds,
            "character_unlocks": self.character_unlocks, "current_character": self.current_character,
            "upgrade_levels": self.upgrade_levels,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, object]) -> "PlayerProgress":
        level = int(payload.get("level", 1))
        raw_characters = payload.get("character_unlocks", ["oliva"])
        migrated = []
        for value in raw_characters if isinstance(raw_characters, list) else ["oliva"]:
            if isinstance(value, int) and 1 <= value <= len(CHARACTER_IDS):
                value = CHARACTER_IDS[value - 1]
            if isinstance(value, str):
                value = canonical_character_id(value)
            if value in CHARACTER_IDS and value not in migrated:
                migrated.append(value)
        if not migrated:
            migrated = ["oliva"]
        upgrades = dict(payload.get("upgrade_levels", {}))
        gold = int(payload.get("gold", 100))
        if payload.get("economy_version", 1) < 2:
            # Keep existing ranks up to each new cap. Refund retired ranks at
            # their historical purchase price, once, without losing investment.
            old_bases = dict(zip(UPGRADE_BASE_COSTS, (30, 35, 40, 45, 50, 65, 85, 100, 120, 80)))
            for name, value in upgrades.items():
                if name in old_bases:
                    old_level = max(0, min(200, int(value)))
                    gold += sum(int(old_bases[name] * 1.08 ** rank) for rank in range(max_upgrade_level(name), old_level))
        return cls(
            level=level, xp=int(payload.get("xp", 0)), gold=gold,
            points=int(payload.get("points", 0)), current_world=int(payload.get("current_world", 1)),
            unlocked_worlds=list(payload.get("unlocked_worlds", [1])),
            upgrade_levels=upgrades,
            character_unlocks=migrated,
            current_character=canonical_character_id(str(payload.get("current_character", "oliva"))),
        )
