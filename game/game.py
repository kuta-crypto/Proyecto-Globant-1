import sys
import random
import math
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pygame
try:
    import cv2
except ImportError:
    cv2 = None

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from game.abilities import ABILITY_DEFS, AbilityManager
from game.characters import CHARACTERS, get_all_characters, get_character_by_id, mastery_cost
from game.builds import spin_build, advance_charges
from game.equipment import GEAR_DEFS, equipment_effects
from game.progression import PlayerProgress, xp_to_next_level
from game.pets import PET_DEFS, RARITY_CONFIG, RARITY_ORDER, roll_pet
from game.rng_system import DEFAULT_PROBABILITIES, calculate_lucky_probability, check_bonus, generate_grid
from game.scatter import (
    MAX_CASCADES_PER_SPIN,
    SCATTER_THRESHOLD,
    SCATTER_PAYOUT_SCALE,
    jackpot_near_miss,
    resolve_scatter_cascades,
)
from game.save_system import DEFAULT_SAVE_PATH, load_game, save_game
from game.settings import GameSettings
from game.slot_animation import build_reels, cascade_paths, reel_offset
from game.upgrades import UPGRADE_BASE_COSTS, upgrade_cost, upgrade_effect, bulk_quote
from game.worlds import WORLD_DEFS
from game.visuals import WorldBackdrop
from game import screens

WIDTH, HEIGHT = 1500, 900
GRID_SIZE = 6
SYMBOL_TYPES = ["coin", "seven", "joker", "sixty_nine", "sixty_seven"]
SYMBOL_LABELS = {
    "coin": "🪙",
    "seven": "7️⃣",
    "joker": "🃏",
    "sixty_nine": "6️⃣9️⃣",
    "sixty_seven": "6️⃣7️⃣",
}
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
WORLD_ONE_BACKGROUND = ASSETS_DIR / "Soul Eater - fondo.mp4"
CHARACTER_IMAGES_DIR = ASSETS_DIR / "characters"
SYMBOL_IMAGES = {
    "coin": ASSETS_DIR / "coin.png",
    "seven": ASSETS_DIR / "seven-transparent.png",
    "joker": ASSETS_DIR / "joker.png",
    "sixty_nine": ASSETS_DIR / "69.png",
    "sixty_seven": ASSETS_DIR / "sixty_seven.png",
}
_SYMBOL_IMAGE_CACHE = {}
_CHARACTER_IMAGE_CACHE = {}


def load_character_portrait(character_id: str, size: Tuple[int, int]):
    cache_key = (character_id, size)
    if cache_key not in _CHARACTER_IMAGE_CACHE:
        image_path = CHARACTER_IMAGES_DIR / f"{character_id}.png"
        image = None
        if image_path.exists():
            try:
                source = pygame.image.load(str(image_path)).convert_alpha()
                scale = min(size[0] / source.get_width(), size[1] / source.get_height())
                scaled_size = (max(1, round(source.get_width() * scale)), max(1, round(source.get_height() * scale)))
                image = pygame.transform.smoothscale(source, scaled_size)
            except pygame.error:
                image = None
        _CHARACTER_IMAGE_CACHE[cache_key] = image
    return _CHARACTER_IMAGE_CACHE[cache_key]


class SymbolArt:
    def __init__(self, symbol: str, x: int, y: int, size: int):
        self.symbol = symbol
        self.x = x
        self.y = y
        self.size = size
        self.color_map = {
            "coin": (255, 204, 51),
            "seven": (61, 176, 255),
            "joker": (255, 98, 201),
            "sixty_nine": (112, 255, 128),
            "sixty_seven": (255, 112, 67),
        }
        cache_key = (self.symbol, size)
        if cache_key in _SYMBOL_IMAGE_CACHE:
            self.image = _SYMBOL_IMAGE_CACHE[cache_key]
        else:
            self.image = None
            image_path = SYMBOL_IMAGES.get(self.symbol)
            if image_path is not None and image_path.exists():
                try:
                    image = pygame.image.load(str(image_path)).convert_alpha()
                    max_image_size = size - 16
                    scale = min(max_image_size / image.get_width(), max_image_size / image.get_height())
                    image_size = (
                        max(1, round(image.get_width() * scale)),
                        max(1, round(image.get_height() * scale)),
                    )
                    self.image = pygame.transform.smoothscale(image, image_size)
                except pygame.error:
                    self.image = None
            _SYMBOL_IMAGE_CACHE[cache_key] = self.image

    def draw(self, surface: pygame.Surface, active: bool = False) -> None:
        color = self.color_map.get(self.symbol, (255, 255, 255))
        rect = pygame.Rect(self.x, self.y, self.size, self.size)
        pygame.draw.rect(surface, (26, 32, 46), rect, border_radius=16)
        if self.image is not None:
            pygame.draw.rect(surface, color, rect.inflate(-8, -8), 2, border_radius=12)
            surface.blit(self.image, self.image.get_rect(center=rect.center))
            if active:
                pygame.draw.rect(surface, (255, 255, 255), rect.inflate(6, 6), 3, border_radius=16)
            return
        pygame.draw.rect(surface, color, rect.inflate(-8, -8), border_radius=12)
        if active:
            pygame.draw.rect(surface, (255, 255, 255), rect.inflate(6, 6), 3, border_radius=16)
        label = SYMBOL_LABELS.get(self.symbol, self.symbol)
        emoji_font = pygame.font.match_font("segoe ui emoji") or pygame.font.match_font("arial")
        font = pygame.font.Font(emoji_font, max(18, self.size // 2))
        text = font.render(label, True, (20, 20, 30))
        surface.blit(text, text.get_rect(center=rect.center))


class TimbaRNGGame:
    def __init__(self):
        pygame.init()

        try:
            pygame.mixer.init()
        except pygame.error:
            print("Aviso: no se pudo inicializar el audio. El juego continuará sin sonido.")

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.world_one_video = None
        self.world_one_video_fps = 30.0
        self.world_one_video_next_frame = 0.0
        self.world_one_video_surface = None
        pygame.display.set_caption("TimbaRNG")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = "menu"
        self.navigation_history = []
        self.pause_return_state = "game"
        self.paused_game = False
        self.settings = GameSettings()
        self.player = PlayerProgress()
        self.abilities = AbilityManager()
        self.gear_owned = []
        self.gear_equipped = {}
        self.shop_category = "skills"
        self.pending_new_game = False
        self.selected_world = 1
        self.selected_character = "oliva"
        self.bet_entry_text = "10"
        self.active_pet = None
        self.pet_collection = []
        self.pet_copies = {}
        self.character_mastery = {}
        self.companion_charges = {}
        self.spin_effects = {}
        self.spin_activations = []
        self.spin_charge_resets = []
        self.last_reward = {}
        self.catalog_page = 0
        self.pet_page = 0
        self.pet_filter = "Todas"
        self.visual_time = 0.0
        self.backdrop = WorldBackdrop((WIDTH, HEIGHT))
        self.pet_pity = {"epic": 0, "legendary": 0, "mythic": 0}
        self.pet_animation_active = False
        self.pet_animation_progress = 0.0
        self.pending_pets = []
        self.revealed_pets = []
        self.duplicate_pet_ids = []
        self.duplicate_pet_indices = []
        self.bet_amount = 10
        self.last_bet = 10
        self.spin_wager = 0
        self.spin_is_free = False
        self.spin_bonus_multiplier = 1.0
        self.bonus_spins_remaining = 0
        self.bonus_multiplier = 2.0
        self.spin_probabilities = DEFAULT_PROBABILITIES
        self.reel_stop_times = [0.0] * GRID_SIZE
        self.jackpot_triggered = False
        self.spin_result_text = ""
        self.save_path = DEFAULT_SAVE_PATH
        self.stats = {
            "total_spins": 0,
            "lines": 0,
            "bonuses": 0,
            "gold_earned": 0,
            "points_earned": 0,
            "xp_earned": 0,
            "best_line": 0,
            "best_bonus": 0,
            "most_common_symbol": "coin",
        }
        self.load_save()
        self.font = pygame.font.SysFont("arial", 24)
        self.small_font = pygame.font.SysFont("arial", 15)
        self.big_font = pygame.font.SysFont("arial", 42, bold=True)
        self.grid = generate_grid(6, 6)
        self.final_grid = [row[:] for row in self.grid]
        self.animating = False
        self.animation_phase = "idle"
        self.cascade_index = 0
        self.cascade_timer = 0.0
        self.reels = []
        self.animation_progress = 0.0
        self.spin_duration = 3.2
        self.grid_cells = []
        self.last_spin_result = []
        self.current_lines = []
        self.current_scatter_cascades = []
        self.current_near_miss = None
        self.current_bonus = False
        self.ui_buttons = {}
        self.active_ability_effects = self.abilities.armed
        self.toast_message = ""
        self.toast_color = (255, 255, 255)
        self.toast_timer = 0.0

    def load_save(self):
        data = load_game(self.save_path)
        if data:
            if data.get("economy_version", 1) < 2:
                backup = Path(self.save_path).with_suffix(".before-v2.json")
                if not backup.exists():
                    import shutil
                    shutil.copy2(self.save_path, backup)
            self.player = PlayerProgress.from_dict(data)
            self.settings = GameSettings.from_dict(data.get("settings"))
            self.abilities = AbilityManager.from_dict(data.get("abilities", {}))
            self.gear_owned = [item for item in data.get("gear_owned", []) if item in GEAR_DEFS]
            self.gear_equipped = {slot: item for slot, item in data.get("gear_equipped", {}).items() if item in self.gear_owned and slot == GEAR_DEFS[item]["slot"]}
            run_state = data.get("run_state", {})
            self.bet_amount = max(1, int(run_state.get("bet_amount", 10)))
            self.last_bet = max(1, int(run_state.get("last_bet", self.bet_amount)))
            self.bonus_spins_remaining = max(0, int(run_state.get("bonus_spins_remaining", 0)))
            self.bonus_multiplier = max(1.0, float(run_state.get("bonus_multiplier", 2.0)))
            self.stats = data.get("stats", self.stats)
            profile = data.get("profile_state", {})
            self.pet_copies = {key: max(1, int(value)) for key, value in profile.get("pet_copies", {}).items() if key in PET_DEFS}
            self.character_mastery = {key: max(1, min(5, int(value))) for key, value in profile.get("character_mastery", {}).items() if key in CHARACTERS}
            self.companion_charges = {key: max(0, int(value)) for key, value in profile.get("companion_charges", {}).items()}
            self.pet_collection = [pet for pet in profile.get("pet_collection", []) if pet in PET_DEFS]
            active_pet = profile.get("active_pet")
            self.active_pet = active_pet if active_pet in self.pet_collection else None
            self.pet_pity = {
                "epic": max(0, int(profile.get("pet_pity", {}).get("epic", 0))),
                "legendary": max(0, int(profile.get("pet_pity", {}).get("legendary", 0))),
                "mythic": max(0, int(profile.get("pet_pity", {}).get("mythic", 0))),
            }
            self.pending_pets = [pet for pet in profile.get("pending_pets", []) if pet in PET_DEFS]
            self.pet_animation_progress = max(0.0, min(2.4, float(profile.get("pet_animation_progress", 0.0))))
            self.pet_animation_active = bool(self.pending_pets)
            self.revealed_pets = [pet for pet in profile.get("revealed_pets", []) if pet in PET_DEFS]
            self.duplicate_pet_indices = [int(i) for i in profile.get("duplicate_pet_indices", []) if 0 <= int(i) < 10]
            self.selected_world = self.player.current_world
            self.selected_character = self.player.current_character

    def save(self):
        payload = self.player.to_dict()
        payload["settings"] = self.settings.to_dict()
        payload["abilities"] = self.abilities.to_dict()
        payload["gear_owned"] = self.gear_owned
        payload["gear_equipped"] = self.gear_equipped
        payload["run_state"] = {
            "bet_amount": self.bet_amount,
            "last_bet": self.last_bet,
            "bonus_spins_remaining": self.bonus_spins_remaining,
            "bonus_multiplier": self.bonus_multiplier,
        }
        payload["profile_state"] = {
            "pet_copies": self.pet_copies,
            "character_mastery": self.character_mastery,
            "companion_charges": self.companion_charges,
            "pet_collection": self.pet_collection,
            "active_pet": self.active_pet,
            "pet_pity": self.pet_pity,
            "pending_pets": self.pending_pets,
            "pet_animation_progress": self.pet_animation_progress,
            "revealed_pets": self.revealed_pets,
            "duplicate_pet_indices": self.duplicate_pet_indices,
        }
        payload["stats"] = self.stats
        save_game(payload, self.save_path)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.state == "bet_entry":
                    if event.key == pygame.K_ESCAPE:
                        self.go_back()
                    elif event.key == pygame.K_RETURN:
                        self.handle_button("bet_confirm")
                    elif event.key == pygame.K_BACKSPACE:
                        self.bet_entry_text = self.bet_entry_text[:-1]
                    elif event.unicode.isdigit() and len(self.bet_entry_text) < 9:
                        self.bet_entry_text += event.unicode
                elif event.key == pygame.K_ESCAPE:
                    if self.state == "game":
                        self.pause_return_state = "game"
                        self.paused_game = True
                        self.state = "pause"
                    elif self.state == "pause":
                        self.paused_game = False
                        self.state = self.pause_return_state
                    elif self.state != "menu":
                        self.go_back()
                elif event.key == pygame.K_SPACE and self.state == "game":
                    self.perform_spin()
                elif self.state == "game" and not self.animating and event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    index = event.key - pygame.K_1
                    if index < len(self.abilities.equipped):
                        self.handle_button("activate:" + self.abilities.equipped[index])
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = pygame.mouse.get_pos()
                for name, rect in self.ui_buttons.items():
                    if rect.collidepoint(pos):
                        if self.animating and self.state == "game" and name != "spin":
                            break
                        self.handle_button(name)
                        self.bet_amount = min(max(1, self.bet_amount), max(1, self.player.gold))

    def handle_button(self, name: str):
        if self.animating and name.startswith(("activate:", "toggle:", "gear:", "pet_equip:", "mastery:")):
            return
        if name.startswith("page:"):
            self.catalog_page = max(0, self.catalog_page + int(name.split(":")[1]))
            return
        if name.startswith("equip_slot:"):
            self.go_to("skills")
            return
        if name.startswith("pet_page:"):
            self.pet_page = max(0, self.pet_page + int(name.split(":")[1]))
            return
        if name.startswith("pet_filter:"):
            self.pet_filter = name.split(":")[1]
            self.pet_page = 0
            return
        if name.startswith("mastery:"):
            key = name.split(":")[1]
            rank = self.character_mastery.get(key, 1)
            if key in self.player.character_unlocks and rank < 5 and self.player.points >= mastery_cost(rank):
                self.player.points -= mastery_cost(rank)
                self.character_mastery[key] = rank + 1
                self.show_toast("Maestria mejorada: +15% a la habilidad", (112, 210, 180))
                self.save()
            return
        if name == "new_game":
            self.pending_new_game = True
            self.selected_world = 1
            self.selected_character = "oliva"
            self.go_to("run_select")
        elif name == "continue":
            self.pending_new_game = False
            self.selected_world = self.player.current_world if self.player.current_world in self.player.unlocked_worlds else 1
            self.selected_character = self.player.current_character if self.player.current_character in self.player.character_unlocks else "oliva"
            self.go_to("run_select")
        elif name == "start_selected":
            allowed_worlds = [1] if self.pending_new_game else self.player.unlocked_worlds
            allowed_characters = ["oliva"] if self.pending_new_game else self.player.character_unlocks
            if self.selected_world not in allowed_worlds or self.selected_character not in allowed_characters:
                self.show_toast("Selecciona contenido desbloqueado", (255, 130, 110))
                return
            if self.pending_new_game:
                self.player = PlayerProgress()
                self.abilities = AbilityManager()
                self.active_ability_effects = self.abilities.armed
                self.pet_copies = {}
                self.character_mastery = {}
                self.companion_charges = {}
                self.last_reward = {}
                self.gear_owned = []
                self.gear_equipped = {}
                self.bet_amount = self.last_bet = 10
                self.bonus_spins_remaining = 0
                self.bonus_multiplier = 2.0
                self.active_ability_effects.clear()
                self.pet_collection = []
                self.active_pet = None
                self.pet_pity = {"epic": 0, "legendary": 0, "mythic": 0}
                self.pending_pets = []
                self.revealed_pets = []
                self.duplicate_pet_ids = []
                self.duplicate_pet_indices = []
                self.pet_animation_progress = 0.0
                self.pet_animation_active = False
                self.stats = {"total_spins": 0, "lines": 0, "bonuses": 0, "gold_earned": 0, "points_earned": 0, "xp_earned": 0, "best_line": 0, "best_bonus": 0, "most_common_symbol": "coin"}
            self.player.current_world = self.selected_world
            self.player.current_character = self.selected_character
            self.paused_game = False
            self.pending_new_game = False
            self.state = "game"
            self.navigation_history.clear()
            self.save()
        elif name == "settings":
            self.go_to("settings")
        elif name.startswith("setting_toggle:"):
            key = name.split(":", 1)[1]
            if key in ("music_enabled", "sound_enabled", "animations_enabled", "fullscreen"):
                setattr(self.settings, key, not getattr(self.settings, key))
                if key == "fullscreen":
                    flags = pygame.FULLSCREEN if self.settings.fullscreen else 0
                    self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
                self.save()
        elif name.startswith("setting_adjust:"):
            _, key, raw_delta = name.split(":", 2)
            delta = int(raw_delta)
            if key == "master_volume":
                self.settings.master_volume = min(1.0, max(0.0, round(self.settings.master_volume + delta * 0.1, 2)))
            elif key == "animation_speed":
                self.settings.animation_speed = min(2.0, max(0.5, round(self.settings.animation_speed + delta * 0.25, 2)))
            self.save()
        elif name == "resume":
            self.paused_game = False
            self.state = self.pause_return_state
        elif name == "roster":
            self.go_to("roster")
        elif name == "quit":
            self.running = False
        elif name == "spin":
            self.perform_spin()
        elif name == "bet_down":
            if not self.animating:
                self.bet_amount = max(1, min(self.player.gold, self.bet_amount - 10))
        elif name == "bet_up":
            if not self.animating:
                self.bet_amount = min(self.player.gold, self.bet_amount + 10)
        elif name == "bet_all":
            if not self.animating:
                self.bet_amount = max(1, self.player.gold)
        elif name == "paytable":
            self.go_to("paytable")
        elif name == "upgrades":
            self.go_to("upgrades")
        elif name == "shop":
            self.go_to("shop")
        elif name == "inventory":
            self.go_to("inventory")
        elif name == "pets":
            self.go_to("pets")
        elif name == "pet_collection":
            self.go_to("pet_collection")
        elif name == "bet_custom":
            if not self.animating:
                self.bet_entry_text = ""
                self.go_to("bet_entry")
        elif name == "bet_confirm":
            try:
                entered = int(self.bet_entry_text)
            except (ValueError, AttributeError):
                entered = 1
            self.bet_amount = max(1, min(entered, max(1, self.player.gold)))
            self.go_back()
        elif name == "bet_cancel":
            self.go_back()
        elif name.startswith("select_world:"):
            world_id = int(name.split(":", 1)[1])
            available = [1] if self.pending_new_game else self.player.unlocked_worlds
            if world_id in available:
                self.selected_world = world_id
        elif name.startswith("select_character:"):
            character_id = name.split(":", 1)[1]
            available = ["oliva"] if self.pending_new_game else self.player.character_unlocks
            if character_id in available:
                self.selected_character = character_id
        elif name.startswith("pet_pull:"):
            self.start_pet_pull(name.split(":", 1)[1])
        elif name.startswith("pet_equip:"):
            pet_id = name.split(":", 1)[1]
            if pet_id in self.pet_collection:
                self.active_pet = pet_id
                self.show_toast(f"{PET_DEFS[pet_id]['name']} es tu mascota activa", (112, 210, 255))
                self.save()
        elif name == "skills":
            self.go_to("skills")
        elif name == "equipment":
            self.go_to("equipment")
        elif name.startswith("shop_tab:"):
            self.shop_category = name.split(":", 1)[1]
            self.catalog_page = 0
        elif name == "back":
            self.go_back()
        elif name == "menu":
            self.paused_game = False
            self.state = "menu"
            self.navigation_history.clear()
            self.save()
        elif name.startswith("upgrade:"):
            upgrade_id = name.split(":", 1)[1]
            purchased, cost = self.player.buy_upgrade(upgrade_id)
            if purchased:
                self.show_toast(f"Mejora adquirida por {cost} oro", (112, 255, 128))
                self.save()
            else:
                self.show_toast("No hay suficiente oro o alcanzaste el nivel máximo", (255, 130, 110))
        elif name.startswith("upgrade_max:"):
            upgrade_id = name.split(":", 1)[1]
            bought, spent = bulk_quote(upgrade_id, self.player.upgrade_levels[upgrade_id], self.player.gold)
            self.player.gold -= spent
            self.player.upgrade_levels[upgrade_id] += bought
            if bought:
                self.show_toast(f"{bought} niveles comprados · {spent} oro", (112, 255, 128))
                self.save()
            else:
                self.show_toast("Te falta oro o la mejora llegó al máximo", (255, 130, 110))
        elif name.startswith("ability:"):
            ability_id = name.split(":", 1)[1]
            if ability_id not in ABILITY_DEFS:
                return
            if ability_id not in self.abilities.purchased and self.player.level < ABILITY_DEFS[ability_id]["level"]:
                return
            if ability_id in self.abilities.purchased:
                equipped = self.abilities.equip_ability(ability_id)
                self.show_toast(f"{ABILITY_DEFS[ability_id]['name']} equipada" if equipped else "Libera una de las 3 ranuras", (112, 210, 255))
                self.save()
            elif ability_id in ABILITY_DEFS and self.player.gold >= ABILITY_DEFS[ability_id]["cost"]:
                self.player.gold -= ABILITY_DEFS[ability_id]["cost"]
                self.abilities.buy_ability(ability_id)
                equipped = self.abilities.equip_ability(ability_id)
                self.show_toast("Habilidad comprada" + (" y equipada" if equipped else "; libera una ranura para equiparla"), (112, 255, 128))
                self.save()
            else:
                self.show_toast("No hay suficiente oro", (255, 130, 110))
        elif name.startswith("toggle:"):
            ability_id = name.split(":", 1)[1]
            if ability_id in self.abilities.equipped:
                if ability_id in self.abilities.armed:
                    self.show_toast("Usa la habilidad preparada antes de retirarla", (255, 210, 110))
                    return
                self.abilities.equipped.remove(ability_id)
                self.show_toast("Habilidad retirada", (255, 210, 110))
            else:
                equipped = self.abilities.equip_ability(ability_id)
                self.show_toast("Habilidad equipada" if equipped else "Tenes 3 ranuras: retira otra habilidad", (112, 210, 255))
            self.save()
        elif name.startswith("activate:"):
            ability_id = name.split(":", 1)[1]
            if ability_id == "resonance" and self.active_pet is None:
                self.show_toast("Equipa una mascota para usar Resonancia", (255, 210, 110))
                return
            if self.abilities.activate_ability(ability_id):
                self.show_toast("Habilidad activada", (255, 220, 100))
                self.save()
            elif ability_id not in self.abilities.equipped:
                self.show_toast("Primero equipa la habilidad", (255, 130, 110))
            else:
                self.show_toast("Habilidad en enfriamiento", (255, 130, 110))
        elif name.startswith("gear:"):
            gear_id = name.split(":", 1)[1]
            definition = GEAR_DEFS[gear_id]
            if gear_id not in self.gear_owned and self.player.level < definition["level"]:
                return
            if gear_id in self.gear_owned:
                self.gear_equipped[definition["slot"]] = gear_id
                self.show_toast(f"{definition['name']} equipado", (112, 210, 255))
            elif self.player.gold >= definition["cost"]:
                self.player.gold -= definition["cost"]
                self.gear_owned.append(gear_id)
                self.gear_equipped[definition["slot"]] = gear_id
                self.show_toast("Equipamiento comprado y equipado", (112, 255, 128))
            else:
                self.show_toast("No hay suficiente oro", (255, 130, 110))
            self.save()

    def go_to(self, state: str) -> None:
        """Opens a screen while keeping the current screen for its Back button."""
        if state != self.state:
            self.catalog_page = 0
            self.navigation_history.append(self.state)
            self.state = state

    def go_back(self) -> None:
        if self.navigation_history:
            self.state = self.navigation_history.pop()
        else:
            self.state = "menu"

    def show_toast(self, message: str, color: tuple[int, int, int]) -> None:
        self.toast_message = message
        self.toast_color = color
        self.toast_timer = 2.2

    def _grant_bailout(self):
        gift = 15 + int(upgrade_effect("safety_net", self.player.upgrade_levels.get("safety_net", 0)))
        self.player.gold += gift
        self.bet_amount = min(max(1, self.bet_amount), self.player.gold)
        self.show_toast(f"Bono de emergencia: +{gift} de oro", (112, 210, 255))

    def perform_spin(self):
        if self.animating:
            return
        if self.player.gold <= 0 and self.bonus_spins_remaining <= 0:
            self._grant_bailout()
        self.spin_is_free = self.bonus_spins_remaining > 0
        if self.spin_is_free:
            self.spin_wager = max(1, self.last_bet)
            self.spin_bonus_multiplier = self.bonus_multiplier
        else:
            wanted = max(1, min(self.bet_amount, self.player.gold))
            discount = upgrade_effect("bet_discount", self.player.upgrade_levels.get("bet_discount", 0))
            self.spin_wager = wanted
            self.spin_paid = max(1, math.ceil(wanted * (1.0 - discount)))
            self.player.gold -= self.spin_paid
            self.last_bet = self.spin_wager
            self.bet_amount = min(max(1, self.bet_amount), max(1, self.player.gold))
            self.spin_bonus_multiplier = 1.0
        character = get_character_by_id(self.player.current_character) or CHARACTERS["oliva"]
        world = WORLD_DEFS.get(self.player.current_world, WORLD_DEFS[1])
        pet = PET_DEFS.get(self.active_pet) if self.active_pet else None
        if self.spin_is_free:
            self.spin_paid = 0
        self.spin_effects, self.spin_activations, self.spin_charge_resets = spin_build(
            character["id"], self.active_pet, self.character_mastery, self.pet_copies,
            self.companion_charges, self.gear_equipped, not self.spin_is_free, self.active_ability_effects,
        )
        luck_level = self.player.upgrade_levels.get("luck", 0) + world["luck"] + self.spin_effects.get("luck", 0)
        self.spin_probabilities = calculate_lucky_probability(DEFAULT_PROBABILITIES, luck_level)
        self.final_grid = generate_grid(GRID_SIZE, GRID_SIZE, probabilities=self.spin_probabilities)
        self.last_spin_result = [row[:] for row in self.final_grid]
        self.current_lines = []
        self.current_scatter_cascades = []
        self.current_near_miss = None
        self.current_bonus = False
        self.jackpot_triggered = False
        self.spin_result_text = ""
        self.animation_progress = 0.0
        speed_level = self.player.upgrade_levels.get("spin_speed", 0)
        base_duration = (2.6 - upgrade_effect("spin_speed", speed_level)) * (1 - min(.5, self.spin_effects.get("speed", 0)))
        if self.settings.animations_enabled:
            self.spin_duration = max(0.75, min(4.0, base_duration / max(0.5, self.settings.animation_speed)))
        else:
            self.spin_duration = 0.18
        self.reel_stop_times = [self.spin_duration * (0.72 + col * 0.056) for col in range(GRID_SIZE)]
        self.reels = build_reels(self.grid, self.final_grid, self.spin_probabilities)
        self.animation_phase = "spin"
        self.animating = True
        self.save()

    def update(self, dt: float):
        if self.animating and not self.paused_game:
            if self.animation_phase == "spin":
                self.animation_progress += dt
                if self.animation_progress >= self.spin_duration:
                    self.resolve_spin_results()
                    self.cascade_index = 0
                    self.cascade_timer = 0.0
                    self.animation_phase = "wins"
                    if self.current_scatter_cascades:
                        self.grid = [row[:] for row in self.current_scatter_cascades[0]["before"]]
                    else:
                        self.animation_phase = "idle"
                        self.animating = False
            else:
                self.update_cascade_animation(dt)
        if not self.paused_game and self.settings.animations_enabled:
            self.visual_time += dt
        if self.pet_animation_active and not self.paused_game:
            self.pet_animation_progress = min(2.4, self.pet_animation_progress + dt)
            if self.pet_animation_progress >= 2.4:
                self.finish_pet_pull()
        if self.toast_timer > 0:
            self.toast_timer = max(0.0, self.toast_timer - dt)

    def cascade_durations(self):
        if not self.settings.animations_enabled:
            return 0.35, 0.0
        speed = max(0.5, self.settings.animation_speed)
        return max(0.25, 0.45 / speed), 0.26 / speed

    def update_cascade_animation(self, dt):
        self.cascade_timer += dt
        hold, fall = self.cascade_durations()
        while self.animating:
            duration = hold if self.animation_phase == "wins" else fall
            if self.cascade_timer < duration:
                break
            self.cascade_timer -= duration
            if self.animation_phase == "wins":
                self.animation_phase = "fall"
            else:
                frame = self.current_scatter_cascades[self.cascade_index]
                self.grid = [row[:] for row in frame["after"]]
                self.cascade_index += 1
                if self.cascade_index == len(self.current_scatter_cascades):
                    self.animation_phase = "idle"
                    self.animating = False
                else:
                    self.animation_phase = "wins"

    def start_pet_pull(self, count: str):
        if self.pet_animation_active:
            return
        pull_count = 10 if count == "ten" else 1
        cost = 4500 if pull_count == 10 else 500
        if self.player.points < cost:
            self.show_toast(f"Necesitas {cost} puntos para esta tirada", (255, 130, 110))
            return
        self.player.points -= cost
        self.pending_pets = [roll_pet(self.pet_pity) for _ in range(pull_count)]
        self.revealed_pets = []
        self.duplicate_pet_ids = []
        self.duplicate_pet_indices = []
        self.pet_animation_progress = 0.0
        self.pet_animation_active = True
        if not self.settings.animations_enabled:
            self.finish_pet_pull()
        self.save()

    def finish_pet_pull(self):
        self.pet_animation_active = False
        owned = set(self.pet_collection)
        for index, pet_id in enumerate(self.pending_pets):
            self.pet_copies[pet_id] = self.pet_copies.get(pet_id, 1 if pet_id in owned else 0) + 1
            if pet_id in owned:
                self.duplicate_pet_ids.append(pet_id)
                self.duplicate_pet_indices.append(index)
                self.player.points += 100
            else:
                self.pet_collection.append(pet_id)
                owned.add(pet_id)
                if self.active_pet is None:
                    self.active_pet = pet_id
        self.revealed_pets = list(self.pending_pets)
        count = len(self.pending_pets)
        duplicate_count = len(self.duplicate_pet_ids)
        self.pending_pets = []
        message = f"Revelacion completa: {count} mascota(s)"
        if duplicate_count:
            message += f"; {duplicate_count} repetida(s): vinculo + puntos"
        self.show_toast(message, (220, 180, 255))
        self.save()

    def resolve_spin_results(self):
        initial_grid = [row[:] for row in self.last_spin_result]
        self.current_near_miss = jackpot_near_miss(initial_grid)
        scatter_result = resolve_scatter_cascades(
            initial_grid,
            weights=self.spin_probabilities,
            rng=random.SystemRandom(),
            max_cascades=MAX_CASCADES_PER_SPIN,
            capture_frames=True,
        )
        self.grid = [row[:] for row in scatter_result["grid"]]
        self.final_grid = [row[:] for row in self.grid]
        self.current_scatter_cascades = scatter_result["cascades"]
        self.current_lines = []
        raw_points_earned = sum(
            cascade["counts"][symbol]
            for cascade in self.current_scatter_cascades
            for symbol in cascade["winning_symbols"]
        )
        character = get_character_by_id(self.player.current_character) or CHARACTERS["oliva"]
        world = WORLD_DEFS.get(self.player.current_world, WORLD_DEFS[1])
        pet = PET_DEFS.get(self.active_pet) if self.active_pet else None
        effects = self.spin_effects
        point_multiplier = 1 + upgrade_effect("point_gain", self.player.upgrade_levels.get("point_gain", 0)) + effects.get("points", 0)
        points_earned = int(raw_points_earned * point_multiplier)
        xp_multiplier = (1 + upgrade_effect("xp_gain", self.player.upgrade_levels.get("xp_gain", 0)) + effects.get("xp", 0)) * world["xp"]
        payout_multiplier = (1 + upgrade_effect("payout", self.player.upgrade_levels.get("payout", 0)) + effects.get("payout", 0)) * world["payout"]
        if "cascade_power" in self.active_ability_effects:
            payout_multiplier += min(.4, len(self.current_scatter_cascades) * .04)
        payout_multiplier *= self.spin_bonus_multiplier
        self.current_bonus = False
        flat = [symbol for row in initial_grid for symbol in row]
        jackpot_level = self.player.upgrade_levels.get("jackpot", 0)
        raw_scatter_multiplier = float(scatter_result["payout_multiplier"])
        jackpot_scatter_multiplier = sum(
            cascade["payout_by_symbol"].get("sixty_seven", 0.0)
            for cascade in self.current_scatter_cascades
        )
        jackpot_enhancer = 1 + upgrade_effect("jackpot", jackpot_level) + effects.get("jackpot", 0)
        raw_scatter_multiplier += jackpot_scatter_multiplier * (jackpot_enhancer - 1.0)
        self.jackpot_triggered = jackpot_scatter_multiplier > 0
        scatter_multiplier = raw_scatter_multiplier * SCATTER_PAYOUT_SCALE
        gross_payout = int(self.spin_wager * scatter_multiplier * payout_multiplier)
        if "shield" in self.active_ability_effects:
            gross_payout = max(gross_payout, math.ceil(self.spin_paid * .8))
        refund = int(self.spin_paid * min(.8, effects.get("refund", 0)))
        travel_gold = int(world["travel_gold"] + effects.get("travel_gold", 0)) if not self.spin_is_free else 0
        skill_gold = int(effects.get("gold", 0))
        reward_gold = gross_payout + refund + travel_gold + skill_gold
        self.player.gold += reward_gold
        self.player.points += points_earned
        earned_xp = int((12 + raw_points_earned * .12) * xp_multiplier)
        self.player.apply_xp(earned_xp)

        bonus_level = self.player.upgrade_levels.get("bonus_chance", 0) + character["bonus"] + world["bonus"] + (pet["bonus"] if pet else 0)
        joker_threshold = max(10, 12 - bonus_level // 4)
        rare_threshold = max(22, 25 - bonus_level // 3)
        scatter_count = flat.count("sixty_nine")
        bonus_triggered = (
            check_bonus(initial_grid, joker_threshold=joker_threshold, high_value_threshold=rare_threshold)
            or scatter_count >= SCATTER_THRESHOLD
            or "bonus_auto" in self.active_ability_effects
        )
        earned_free_spins = int(effects.get("free_spins", 0))
        pet_free_spin = earned_free_spins > 0
        if self.spin_is_free and self.bonus_spins_remaining > 0:
            self.bonus_spins_remaining -= 1
        if bonus_triggered:
            self.current_bonus = True
            extra = int(upgrade_effect("bonus_spins", self.player.upgrade_levels.get("bonus_spins", 0)))
            extra += int(effects.get("bonus_spins", 0))
            self.bonus_spins_remaining += 1 if self.spin_is_free and "bonus_auto" not in self.active_ability_effects else 3 + extra
            self.bonus_multiplier = min(2.0, 1.25 + bonus_level * .03)
            self.stats["bonuses"] += 1
            self.stats["best_bonus"] = max(self.stats["best_bonus"], self.bonus_spins_remaining)
        if pet_free_spin:
            self.current_bonus = True
            self.bonus_spins_remaining += earned_free_spins
            self.bonus_multiplier = max(self.bonus_multiplier, 1.25)
            self.stats["bonuses"] += 1
            self.stats["best_bonus"] = max(self.stats["best_bonus"], self.bonus_spins_remaining)
        self.stats["total_spins"] += 1
        self.stats["lines"] += sum(len(cascade["winning_symbols"]) for cascade in self.current_scatter_cascades)
        self.stats["gold_earned"] += reward_gold
        self.stats["points_earned"] += points_earned
        self.stats["xp_earned"] += earned_xp
        self.stats["best_line"] = max(
            self.stats["best_line"],
            max(
                (cascade["counts"][symbol] for cascade in self.current_scatter_cascades for symbol in cascade["winning_symbols"]),
                default=0,
            ),
        )
        if self.jackpot_triggered:
            self.spin_result_text = f"JACKPOT SCATTER - premio {gross_payout} oro"
        elif gross_payout:
            self.spin_result_text = f"Premio: {gross_payout} oro | {len(self.current_scatter_cascades)} cascadas"
        else:
            self.spin_result_text = "Sin premio de simbolos"
        if scatter_result["capped"]:
            self.spin_result_text += " | limite de cascadas alcanzado"
        if bonus_triggered:
            self.spin_result_text = f"{self.spin_result_text} | BONUS: giros gratis"
        elif pet_free_spin:
            self.spin_result_text = f"{self.spin_result_text} | HABILIDAD: giro gratis"
        if self.spin_is_free and not self.current_bonus:
            self.spin_result_text = f"Giro gratis x{self.spin_bonus_multiplier:.1f} - premio {gross_payout} oro"
        self.last_reward = dict(prize=gross_payout, travel=travel_gold, refund=refund, skill=skill_gold, total=reward_gold, net=reward_gold-self.spin_paid, activations=list(self.spin_activations))
        advance_charges(character["id"], self.active_pet, self.companion_charges, self.spin_charge_resets, not self.spin_is_free)
        self.abilities.finish_spin(paid=not self.spin_is_free)
        if self.player.gold <= 0 and self.bonus_spins_remaining <= 0:
            self._grant_bailout()
        else:
            self.bet_amount = min(max(1, self.bet_amount), max(1, self.player.gold))
        if self.current_near_miss is not None:
            self.show_toast(f"Cerca del umbral: {self.current_near_miss}/{SCATTER_THRESHOLD} Jackpot en el giro inicial", (255, 190, 90))
        self.active_ability_effects.clear()
        self.save()

    def draw_wrapped_text(self, text, x, y, width, color, line_gap=18):
        words = str(text).split()
        lines = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if current and self.small_font.size(candidate)[0] > width:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        for index, line in enumerate(lines):
            self.screen.blit(self.small_font.render(line, True, color), (x, y+index*line_gap))
        return len(lines)*line_gap

    def draw_character_portrait(self, character_id, rect):
        portrait = load_character_portrait(character_id, rect.size)
        if portrait is not None:
            self.screen.blit(portrait, portrait.get_rect(center=rect.center))

    def draw_menu(self):
        screens.draw_menu(self)

    def draw_run_select(self):
        screens.draw_run_select(self)

    def draw_roster(self):
        screens.draw_roster(self)

    def draw_pause(self):
        self.draw_game()
        self.ui_buttons.clear()
        shade=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
        shade.fill((3,3,10,205))
        self.screen.blit(shade,(0,0))
        panel=pygame.Rect(490,220,520,455)
        pygame.draw.rect(self.screen,(20,19,38),panel,border_radius=20)
        pygame.draw.rect(self.screen,(99,76,155),panel,2,border_radius=20)
        title=self.big_font.render("PAUSA",True,(247,240,255))
        self.screen.blit(title,title.get_rect(center=(WIDTH//2,292)))
        for i,(name,label,color) in enumerate((("resume","REANUDAR",(69,112,104)),("menu","MENU PRINCIPAL",(83,59,128)),("settings","AJUSTES",(57,54,83)))):
            rect=pygame.Rect(560,365+i*78,380,56)
            pygame.draw.rect(self.screen,color,rect,border_radius=11)
            text=self.font.render(label,True,(255,255,255))
            self.screen.blit(text,text.get_rect(center=rect.center))
            self.ui_buttons[name]=rect

    def draw_settings(self):
        self.ui_buttons.clear()
        self.screen.fill((11, 11, 21))
        title = self.big_font.render("AJUSTES", True, (246, 240, 255))
        self.screen.blit(title, (72, 45))
        subtitle = self.small_font.render("Personaliza la presentacion y los controles de la partida.", True, (151, 146, 177))
        self.screen.blit(subtitle, (80, 103))
        rows = [
            ("Volumen general", "master_volume", False),
            ("Musica", "music_enabled", True),
            ("Efectos de sonido", "sound_enabled", True),
            ("Animaciones", "animations_enabled", True),
            ("Pantalla completa", "fullscreen", True),
            ("Velocidad de animacion", "animation_speed", False),
        ]
        for i, (label, key, is_toggle) in enumerate(rows):
            y = 150 + i * 88
            row = pygame.Rect(170, y, 1160, 68)
            pygame.draw.rect(self.screen, (21, 20, 39), row, border_radius=12)
            pygame.draw.rect(self.screen, (57, 49, 84), row, 1, border_radius=12)
            self.screen.blit(self.font.render(label, True, (239, 235, 249)), (row.x + 24, row.y + 20))
            if is_toggle:
                value = getattr(self.settings, key)
                button = pygame.Rect(row.right - 240, row.y + 14, 210, 40)
                color = (40, 115, 91) if value else (72, 65, 84)
                pygame.draw.rect(self.screen, color, button, border_radius=9)
                text = self.small_font.render("ACTIVADO" if value else "DESACTIVADO", True, (255, 255, 255))
                self.screen.blit(text, text.get_rect(center=button.center))
                self.ui_buttons[f"setting_toggle:{key}"] = button
            else:
                value = self.settings.master_volume if key == "master_volume" else self.settings.animation_speed
                display = f"{int(value * 100)}%" if key == "master_volume" else f"x{value:.2f}"
                minus = pygame.Rect(row.right - 300, row.y + 14, 46, 40)
                plus = pygame.Rect(row.right - 78, row.y + 14, 46, 40)
                for button, symbol, delta in ((minus, "-", -1), (plus, "+", 1)):
                    pygame.draw.rect(self.screen, (62, 52, 102), button, border_radius=8)
                    symbol_surface = self.font.render(symbol, True, (255, 255, 255))
                    self.screen.blit(symbol_surface, symbol_surface.get_rect(center=button.center))
                    self.ui_buttons[f"setting_adjust:{key}:{delta}"] = button
                value_surface = self.font.render(display, True, (255, 216, 111))
                self.screen.blit(value_surface, value_surface.get_rect(center=(row.right - 180, row.centery)))
        back = pygame.Rect(60, 800, 170, 48)
        pygame.draw.rect(self.screen, (54, 48, 85), back, border_radius=10)
        self.screen.blit(self.small_font.render("VOLVER", True, (255, 255, 255)), back.move(53, 16))
        self.ui_buttons["back"] = back

    def draw_game(self):
        screens.draw_game(self)

    def draw_slot_board(self, grid_rect):
        origin_x, origin_y = grid_rect.x + 11, grid_rect.y + 10
        pitch, size = 86, 80
        self.grid_cells = [
            (row, col, pygame.Rect(origin_x + col * pitch, origin_y + row * pitch, size, size))
            for row in range(GRID_SIZE) for col in range(GRID_SIZE)
        ]
        previous_clip = self.screen.get_clip()
        self.screen.set_clip(pygame.Rect(origin_x - 4, origin_y - 4, 518, 518))

        def draw_symbol(symbol, col, row, active=False):
            if -1 < row < GRID_SIZE:
                SymbolArt(symbol, origin_x + col * pitch, round(origin_y + row * pitch), size).draw(self.screen, active)

        if self.animating and self.animation_phase == "spin" and self.settings.animations_enabled:
            for col, (distance, strip) in enumerate(self.reels):
                offset = reel_offset(self.animation_progress / self.reel_stop_times[col], distance)
                for symbol, source in strip:
                    draw_symbol(symbol, col, source + offset)
        elif self.animating and self.animation_phase == "fall":
            frame = self.current_scatter_cascades[self.cascade_index]
            _, duration = self.cascade_durations()
            progress = min(1.0, self.cascade_timer / max(0.001, duration))
            for symbol, col, source, destination in cascade_paths(frame["before"], frame["after"], frame["winning_symbols"]):
                draw_symbol(symbol, col, source + (destination - source) * progress ** 2)
        else:
            winners = []
            if self.animating and self.animation_phase == "wins":
                winners = self.current_scatter_cascades[self.cascade_index]["winning_symbols"]
            for row, col, rect in self.grid_cells:
                draw_symbol(self.grid[row][col], col, row, self.grid[row][col] in winners)
            if winners:
                self.draw_scatter_wins(winners, origin_x, origin_y)
        self.screen.set_clip(previous_clip)
        if self.animating and self.animation_phase == "wins":
            frame = self.current_scatter_cascades[self.cascade_index]
            names = {"coin": "Monedas", "seven": "Sietes", "joker": "Jokers", "sixty_nine": "69", "sixty_seven": "Jackpot"}
            label = "  +  ".join(f"{names[symbol]} x{frame['counts'][symbol]}" for symbol in frame["winning_symbols"])
        else:
            label = f"{SCATTER_THRESHOLD} o mas simbolos iguales en cualquier posicion"
        text = self.small_font.render(label, True, (255, 223, 130))
        self.screen.blit(text, text.get_rect(center=(grid_rect.centerx, grid_rect.y - 22)))

    def draw_scatter_wins(self, winners, origin_x, origin_y):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for symbol in winners:
            color = SymbolArt(symbol, 0, 0, 80).color_map[symbol]
            points = []
            # A single trace joins every paid scatter, including isolated cells.
            for row in range(GRID_SIZE):
                columns = range(GRID_SIZE) if row % 2 == 0 else reversed(range(GRID_SIZE))
                for col in columns:
                    if self.grid[row][col] == symbol:
                        points.append((origin_x + col * 86 + 40, origin_y + row * 86 + 40))
            if len(points) > 1:
                pygame.draw.lines(overlay, (*color, 150), False, points, 3)
            for x, y in points:
                rect = pygame.Rect(x - 41, y - 41, 82, 82)
                pygame.draw.rect(overlay, (*color, 240), rect, 3, border_radius=14)
                pygame.draw.circle(overlay, (*color, 255), (x, y + 32), 4)
        self.screen.blit(overlay, (0, 0))

    def draw_bet_entry(self):
        self.draw_game()
        shade=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
        shade.fill((3,3,10,190))
        self.screen.blit(shade,(0,0))
        self.ui_buttons.clear()
        panel=pygame.Rect(520,315,460,255)
        pygame.draw.rect(self.screen,(24,22,43),panel,border_radius=20)
        pygame.draw.rect(self.screen,(105,75,164),panel,2,border_radius=20)
        title=self.font.render("APUESTA PERSONALIZADA",True,(245,239,255))
        self.screen.blit(title,title.get_rect(center=(WIDTH//2,355)))
        field=pygame.Rect(580,390,340,58)
        pygame.draw.rect(self.screen,(12,12,26),field,border_radius=10)
        pygame.draw.rect(self.screen,(102,80,151),field,1,border_radius=10)
        value=self.bet_entry_text or ""
        rendered=self.font.render(value+("|" if pygame.time.get_ticks()%900<450 else ""),True,(255,216,111))
        self.screen.blit(rendered,rendered.get_rect(center=field.center))
        hint=self.small_font.render(f"Disponible: {self.player.gold} oro | escribe el monto y pulsa Enter",True,(159,151,188))
        self.screen.blit(hint,hint.get_rect(center=(WIDTH//2,465)))
        for key,rect,label,color in (("bet_confirm",pygame.Rect(585,495,145,45),"CONFIRMAR",(84,53,144)),
                                     ("bet_cancel",pygame.Rect(770,495,145,45),"CANCELAR",(57,48,81))):
            pygame.draw.rect(self.screen,color,rect,border_radius=9)
            text=self.small_font.render(label,True,(255,255,255))
            self.screen.blit(text,text.get_rect(center=rect.center))
            self.ui_buttons[key]=rect

    def draw_paytable(self):
        self.ui_buttons.clear()
        self.screen.fill((11,11,21))
        self.screen.blit(self.big_font.render("TABLA DE PREMIOS",True,(246,240,255)),(75,45))
        self.screen.blit(self.small_font.render("Scatter pays por cantidad total en la matriz; se escala por la apuesta.",True,(151,146,177)),(80,105))
        headers=["SIMBOLO / PROBABILIDAD BASE","12-14","15-17","18+"]
        xs=[100,730,910,1090]
        for label,x in zip(headers,xs):
            self.screen.blit(self.small_font.render(label,True,(181,155,230)),(x,160))
        names={"coin":"Moneda","seven":"7","joker":"Joker","sixty_nine":"69","sixty_seven":"67 - JACKPOT"}
        from game.rng_system import DEFAULT_PROBABILITIES
        from game.scatter import SCATTER_PAYOUTS, SCATTER_PAYOUT_SCALE
        for i,symbol in enumerate(("coin","seven","joker","sixty_nine","sixty_seven")):
            y=205+i*78
            rect=pygame.Rect(80,y,1320,60)
            pygame.draw.rect(self.screen,(21,20,39),rect,border_radius=10)
            prob=DEFAULT_PROBABILITIES[symbol]*100
            self.screen.blit(self.font.render(f"{names[symbol]} - {prob:.1f}% por casilla",True,(244,240,255)),(100,y+17))
            for col,tier in enumerate(("12-14","15-17","18+")):
                amount=SCATTER_PAYOUTS[symbol][tier]*SCATTER_PAYOUT_SCALE
                text=self.font.render(f"x{amount:.6g}",True,(255,210,79) if symbol=="sixty_seven" else (181,215,255))
                self.screen.blit(text,text.get_rect(center=(770+180*col,y+30)))
        note1=self.font.render("Cada cascada retira los simbolos premiados, aplica gravedad y rellena desde arriba.",True,(229,177,255))
        note2=self.font.render(f"Sin {SCATTER_THRESHOLD} iguales no hay premio de simbolos. Maximo: {MAX_CASCADES_PER_SPIN} cascadas.",True,(255,213,112))
        self.screen.blit(note1,(100,630))
        self.screen.blit(note2,(100,674))
        self.screen.blit(self.small_font.render("RTP base objetivo: 96% antes del redondeo. Suerte, bonus, mascotas y oro de viaje se calculan aparte.",True,(151,146,177)),(100,719))
        self._draw_back_button()

    def draw_upgrades(self):
        screens.draw_upgrades(self)

    def draw_shop(self):
        screens.draw_catalog(self)

    def draw_inventory(self):
        screens.draw_inventory(self)

    def draw_pets(self):
        screens.draw_pets(self)


    def draw_pet_collection(self):
        screens.draw_pet_collection(self)

    def draw_skills(self):
        screens.draw_catalog(self, "skills")

    def draw_equipment(self):
        screens.draw_catalog(self, "gear")

    def _draw_back_button(self):
        back = pygame.Rect(WIDTH-180, HEIGHT-72, 150, 46)
        pygame.draw.rect(self.screen, (54,48,85), back, border_radius=10)
        self.screen.blit(self.small_font.render("Volver", True, (255,255,255)), back.move(50,15))
        self.ui_buttons["back"] = back

    def draw_toast(self):
        if self.toast_timer <= 0:
            return
        alpha = min(255, int(self.toast_timer * 180))
        panel = pygame.Surface((620, 54), pygame.SRCALPHA)
        panel.fill((*self.toast_color, alpha))
        rect = panel.get_rect(center=(WIDTH // 2, HEIGHT - 42))
        self.screen.blit(panel, rect)
        text = self.font.render(self.toast_message, True, (18, 24, 32))
        self.screen.blit(text, text.get_rect(center=rect.center))

    def render(self):
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "settings":
            self.draw_settings()
        elif self.state == "game":
            self.draw_game()
        elif self.state == "pause":
            self.draw_pause()
        elif self.state == "run_select":
            self.draw_run_select()
        elif self.state == "roster":
            self.draw_roster()
        elif self.state == "bet_entry":
            self.draw_bet_entry()
        elif self.state == "paytable":
            self.draw_paytable()
        elif self.state == "upgrades":
            self.draw_upgrades()
        elif self.state == "shop":
            self.draw_shop()
        elif self.state == "inventory":
            self.draw_inventory()
        elif self.state == "skills":
            self.draw_skills()
        elif self.state == "equipment":
            self.draw_equipment()
        elif self.state == "pets":
            self.draw_pets()
        elif self.state == "pet_collection":
            self.draw_pet_collection()
        self.draw_toast()
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self.handle_events()
            self.update(dt)
            self.render()
        if self.world_one_video is not None:
            self.world_one_video.release()


def main():
    game = TimbaRNGGame()
    game.run()


if __name__ == "__main__":
    main()
