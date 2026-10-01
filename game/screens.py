"""Shared illustrated UI for companions, progression and the shop."""

import math
import pygame

from game.abilities import ABILITY_DEFS
from game.characters import CHARACTERS, mastery_cost
from game.equipment import GEAR_DEFS, equipment_effects
from game.pets import PET_DEFS, RARITY_ORDER, describe_effects, companion_effects, pet_rank, skill_description
from game.progression import xp_to_next_level
from game.upgrades import UPGRADE_DEFS, upgrade_cost, max_upgrade_level, effect_label, bulk_quote
from game.visuals import illustration, pet_portrait, item_icon
from game.worlds import WORLD_DEFS

INK = (17, 26, 37)
PANEL = (25, 37, 50)
LINE = (62, 77, 88)
PAPER = (237, 229, 211)
MUTED = (158, 174, 183)
GOLD = (232, 190, 113)
JADE = (125, 204, 174)


def text(game, value, pos, color=PAPER, big=False, small=False):
    font = game.big_font if big else game.small_font if small else game.font
    surface = font.render(str(value), True, color)
    game.screen.blit(surface, pos)


def panel(game, rect, selected=False):
    pygame.draw.rect(game.screen, INK, rect, border_radius=10)
    pygame.draw.rect(game.screen, GOLD if selected else LINE, rect, 2 if selected else 1, border_radius=10)


def button(game, key, label, rect, enabled=True, selected=False):
    rect = pygame.Rect(rect)
    fill = (58, 91, 83) if selected else (51, 70, 83) if enabled else (32, 42, 53)
    pygame.draw.rect(game.screen, fill, rect, border_radius=6)
    pygame.draw.rect(game.screen, GOLD if selected else LINE, rect, 1, border_radius=6)
    surface = game.small_font.render(label, True, PAPER if enabled else (116, 132, 142))
    game.screen.blit(surface, surface.get_rect(center=rect.center))
    if enabled:
        game.ui_buttons[key] = rect


def bar(game, rect, value, maximum, color=JADE):
    rect = pygame.Rect(rect)
    pygame.draw.rect(game.screen, (48, 60, 71), rect, border_radius=3)
    fraction = min(1, max(0, value / max(1, maximum)))
    if fraction:
        pygame.draw.rect(game.screen, color, (rect.x, rect.y, int(rect.w * fraction), rect.h), border_radius=3)


def base(game, title, subtitle, world=None):
    game.ui_buttons.clear()
    game.backdrop.draw(game.screen, world or game.player.current_world, game.visual_time, dim=170)
    text(game, title, (45, 28), big=True)
    text(game, subtitle, (48, 84), MUTED, small=True)
    wallet = pygame.Rect(1095, 28, 360, 64)
    panel(game, wallet)
    text(game, f"{game.player.gold:,} ORO", (1112, 34), GOLD)
    text(game, f"{game.player.points:,} PTS   /   NIVEL {game.player.level}", (1112, 66), MUTED, small=True)


def back(game):
    button(game, "back", "VOLVER", (45, 819, 155, 43))


def pager(game, page, count, prefix="page", page_size=6):
    pages = max(1, math.ceil(count / page_size))
    button(game, prefix + ":-1", "< ANTERIOR", (566, 819, 150, 43), page > 0)
    text(game, f"{page + 1} / {pages}", (737, 831), MUTED, small=True)
    button(game, prefix + ":1", "SIGUIENTE >", (805, 819, 150, 43), page + 1 < pages)


def wallet_share(cost, gold):
    return f"{cost / gold:.1%} de tu oro" if gold else "Sin oro disponible"


def draw_catalog(game, category=None):
    category = category or game.shop_category
    base(game, "EL MERCADO" if game.state == "shop" else "TUS HABILIDADES" if category == "skills" else "TU EQUIPO",
         "Arma tu estilo de juego. Tres habilidades activas y una pieza por ranura.")
    if game.state == "shop":
        for i, (key, name) in enumerate((("skills", "HABILIDADES"), ("gear", "EQUIPAMIENTO"))):
            button(game, "shop_tab:" + key, name, (45 + i * 208, 124, 195, 44), selected=category == key)
    else:
        text(game, f"{len(game.abilities.equipped)}/3 habilidades equipadas" if category == "skills" else f"{len(game.gear_equipped)}/6 ranuras ocupadas", (48, 138), JADE, small=True)
    catalog = ABILITY_DEFS if category == "skills" else GEAR_DEFS
    entries = list(catalog.items())
    game.catalog_page = min(game.catalog_page, (len(entries)-1)//6)
    for i, (key, item) in enumerate(entries[game.catalog_page*6:game.catalog_page*6+6]):
        x, y = 45 + (i % 3) * 475, 193 + (i // 3) * 292
        rect = pygame.Rect(x, y, 460, 274)
        owned = key in (game.abilities.purchased if category == "skills" else game.gear_owned)
        equipped = key in game.abilities.equipped if category == "skills" else game.gear_equipped.get(item["slot"]) == key
        unlocked = owned or game.player.level >= item["level"]
        panel(game, rect, equipped)
        pygame.draw.rect(game.screen, PANEL, (x+15, y+16, 66, 66), border_radius=9)
        item_icon(game.screen, item["icon"], pygame.Rect(x+15, y+16, 66, 66), JADE if equipped else GOLD)
        text(game, item["name"], (x+95, y+18))
        kind = f"Recarga: {item['cooldown']} giros pagos" if category == "skills" else item["slot"]
        text(game, kind, (x+96, y+51), JADE, small=True)
        game.draw_wrapped_text(item["description"], x+19, y+99, 418, PAPER, 20)
        if not unlocked:
            info = f"Se desbloquea en nivel {item['level']}"
        elif not owned:
            info = f"{item['cost']} oro  /  {wallet_share(item['cost'], game.player.gold)}"
        elif category == "gear" and not equipped:
            current = GEAR_DEFS.get(game.gear_equipped.get(item["slot"]), {})
            info = "Reemplaza: " + current.get("name", "ranura vacia")
        else:
            info = "EQUIPADO" if equipped else "EN TU COLECCION"
        text(game, info, (x+19, y+167), GOLD if unlocked else MUTED, small=True)
        if category == "skills":
            armed = key in game.abilities.armed
            label = "PREPARADA" if armed else "RETIRAR" if equipped else "EQUIPAR" if owned else "COMPRAR"
            can_equip = equipped or len(game.abilities.equipped) < 3
            enabled = unlocked and not armed and (can_equip if owned else game.player.gold >= item["cost"])
            button(game, ("toggle:" if owned else "ability:") + key, label, (x+19,y+214,195,40), enabled)
            if equipped:
                cooldown = int(game.abilities.get_cooldown_remaining(key))
                ready = game.abilities.is_ability_ready(key)
                label = "LISTA PARA GIRAR" if armed else f"RECARGA: {cooldown}" if cooldown else "PREPARAR"
                button(game, "activate:" + key, label, (x+226,y+214,215,40), ready, armed)
        else:
            button(game, "gear:" + key, "EQUIPADO" if equipped else "EQUIPAR" if owned else "COMPRAR Y EQUIPAR", (x+19,y+214,422,40), unlocked and not equipped and (owned or game.player.gold >= item["cost"]), equipped)
    back(game)
    pager(game, game.catalog_page, len(entries))


def draw_upgrades(game):
    base(game, "EL TALLER", "Mejoras permanentes. Comprar varios usa como maximo el 25% del oro que tenes ahora.")
    for i, (key, item) in enumerate(UPGRADE_DEFS.items()):
        x, y = 45 + (i % 2) * 715, 130 + (i // 2) * 132
        panel(game, pygame.Rect(x, y, 695, 121))
        level = game.player.upgrade_levels[key]
        cap = max_upgrade_level(key)
        cost = upgrade_cost(key, level)
        maxed = level >= cap
        text(game, item[0], (x+16,y+10))
        text(game, f"RANGO {level}/{cap}", (x+537,y+16), JADE, small=True)
        detail = effect_label(key, level)
        if not maxed:
            detail += "  >  " + effect_label(key, level+1)
        text(game, detail, (x+16,y+40), MUTED, small=True)
        bar(game, (x+16,y+65,660,4), level, cap)
        button(game, "upgrade:"+key, "COMPLETADO" if maxed else f"+1  /  {cost} ORO", (x+16,y+80,177,30), not maxed and game.player.gold >= cost)
        count, spent = bulk_quote(key, level, game.player.gold)
        button(game, "upgrade_max:"+key, f"+{count} RANGOS  /  {spent} ORO", (x+204,y+80,230,30), count > 0)
        text(game, "Al maximo" if maxed else wallet_share(cost, game.player.gold), (x+451,y+87), GOLD, small=True)
    back(game)


def draw_pet_collection(game):
    base(game, "COMPANEROS", "Cada mascota tiene una habilidad propia. Cada dos repetidas: +1 vinculo, hasta rango 5.")
    for i, rarity in enumerate(["Todas"] + RARITY_ORDER):
        button(game, "pet_filter:"+rarity, rarity.upper(), (45+i*190,119,175,39), selected=game.pet_filter == rarity)
    entries = [(key, pet) for key, pet in PET_DEFS.items() if game.pet_filter in ("Todas", pet["rarity"])]
    game.pet_page = min(game.pet_page, (len(entries)-1)//8)
    for i, (key, pet) in enumerate(entries[game.pet_page*8:game.pet_page*8+8]):
        x, y = 45+(i%4)*357, 181+(i//4)*306
        owned, active = key in game.pet_collection, key == game.active_pet
        panel(game, pygame.Rect(x,y,343,293), active)
        text(game, pet["name"], (x+12,y+10), PAPER if owned else MUTED)
        pet_portrait(game.screen, key, pygame.Rect(x+12,y+49,126,126), dim=not owned)
        color = pet["color"]
        text(game, pet["rarity"].upper(), (x+151,y+50), color, small=True)
        text(game, pet["role"], (x+151,y+74), JADE, small=True)
        rank = pet_rank(game.pet_copies.get(key, 1))
        passive = companion_effects(pet, rank, False)
        game.draw_wrapped_text(describe_effects(passive), x+151,y+99,179,MUTED,19)
        text(game, f"Vinculo {rank}/5" if owned else "Por descubrir", (x+151,y+157), GOLD, small=True)
        game.draw_wrapped_text(skill_description(pet, rank), x+12,y+188,319,PAPER,19)
        if owned:
            button(game, "pet_equip:"+key, "TE ACOMPANA" if active else "ELEGIR COMPANERO", (x+12,y+250,319,31), not active, active)
        else:
            text(game, "Aparece en las invocaciones", (x+12,y+259), MUTED, small=True)
    back(game)
    pager(game, game.pet_page, len(entries), "pet_page", 8)


def draw_pets(game):
    base(game, "EL REFUGIO", "Conoce a tu proximo companero. Las repetidas mejoran el vinculo y devuelven 100 puntos.", world=3)
    panel(game, pygame.Rect(45,125,1410,205))
    pet_id = game.active_pet or "comun_01"
    pet_portrait(game.screen, pet_id, pygame.Rect(65,145,165,165))
    text(game, "Un viaje mejor, en compania", (257,150))
    text(game, "1 invocacion: 500 puntos  /  10 invocaciones: 4500 puntos", (258,190), GOLD, small=True)
    text(game, f"Garantias: epica {game.pet_pity['epic']}/10  /  legendaria {game.pet_pity['legendary']}/80  /  mitica {game.pet_pity['mythic']}/140", (258,220), MUTED, small=True)
    text(game, "Probabilidades: 68% comun / 20% rara / 9% epica / 2.5% legendaria / 0.5% mitica", (258,248), MUTED, small=True)
    text(game, f"Coleccion: {len(game.pet_collection)}/{len(PET_DEFS)}", (258,279), JADE, small=True)
    button(game, "pet_pull:single", "INVOCAR / 500 PTS", (1065,164,365,48), not game.pet_animation_active and game.player.points >= 500)
    button(game, "pet_pull:ten", "INVOCAR 10 / 4500 PTS", (1065,229,365,48), not game.pet_animation_active and game.player.points >= 4500)
    if game.pet_animation_active:
        cx, cy = 750, 540
        phase = game.pet_animation_progress
        for i in range(5):
            radius = 55+i*15+int(6*math.sin(phase*3+i))
            pygame.draw.circle(game.screen, GOLD if i%2 else JADE, (cx,cy), radius, 1)
        item_icon(game.screen, "star", pygame.Rect(cx-45,cy-45,90,90))
        text(game, "Alguien se acerca...", (653,684), PAPER)
        bar(game, (530,736,440,7), phase, 2.4)
    else:
        text(game, "ULTIMOS EN LLEGAR", (48,350), JADE, small=True)
        ids = game.revealed_pets or list(PET_DEFS)[:5]
        for i, key in enumerate(ids[:10]):
            x, y = 45+(i%5)*284, 386+(i//5)*202
            pet = PET_DEFS[key]
            panel(game, pygame.Rect(x,y,268,188))
            pet_portrait(game.screen, key, pygame.Rect(x+10,y+10,112,112), dim=not game.revealed_pets)
            game.draw_wrapped_text(pet["name"],x+134,y+21,120,PAPER,22)
            text(game, pet["rarity"], (x+134,y+83),pet["color"],small=True)
            text(game, pet["role"], (x+12,y+134),JADE,small=True)
            label = "VINCULO +1 COPIA / +100 PTS" if i in game.duplicate_pet_indices and game.revealed_pets else "NUEVO COMPANERO" if game.revealed_pets else "Por descubrir"
            text(game,label,(x+12,y+161),GOLD,small=True)
        button(game,"pet_collection","VER COLECCION",(1125,819,330,43))
    back(game)


def draw_run_select(game):
    base(game, "ELIGE TU RUMBO", "Mundos para explorar y personajes con habilidades propias.", world=game.selected_world)
    worlds = [1] if game.pending_new_game else game.player.unlocked_worlds
    characters = ["oliva"] if game.pending_new_game else game.player.character_unlocks
    for world_id, world in WORLD_DEFS.items():
        x, y = 45+(world_id-1)*285, 127
        rect = pygame.Rect(x,y,270,210)
        unlocked, chosen = world_id in worlds, world_id == game.selected_world
        panel(game,rect,chosen)
        picture = illustration("worlds", f"world_{world_id}",(246,119))
        if picture:
            game.screen.blit(picture,(x+12,y+12))
        text(game,world["name"],(x+12,y+138),PAPER if unlocked else MUTED)
        text(game,f"+{world['travel_gold']} oro de viaje" if unlocked else f"NIVEL {world['unlock_level']}",(x+12,y+178),GOLD,small=True)
        if unlocked:
            game.ui_buttons[f"select_world:{world_id}"] = rect
    for i,(key,char) in enumerate(CHARACTERS.items()):
        x,y = 45+(i%4)*357,365+(i//4)*204
        rect=pygame.Rect(x,y,343,190)
        unlocked,chosen = key in characters, key == game.selected_character
        panel(game,rect,chosen)
        game.draw_character_portrait(key,pygame.Rect(x+10,y+14,84,135))
        text(game,char["name"].upper(),(x+107,y+12),PAPER if unlocked else MUTED)
        text(game,char["role"],(x+107,y+45),JADE,small=True)
        game.draw_wrapped_text(char["skill"],x+107,y+72,220,MUTED,18)
        text(game,"SELECCIONADO" if chosen else "ELEGIR" if unlocked else f"NIVEL {char['unlock_level']}",(x+14,y+164),GOLD,small=True)
        if unlocked:
            game.ui_buttons["select_character:"+key]=rect
    back(game)
    button(game,"start_selected","EMPEZAR EL VIAJE" if game.pending_new_game else "ENTRAR",(1110,819,345,43),selected=True)


def draw_roster(game):
    base(game,"MAESTRIA","Cada rango potencia un 15% los bonos de tu personaje; maximo 5. Los giros gratis no se multiplican.")
    for i,(key,char) in enumerate(CHARACTERS.items()):
        x,y = 45+(i%4)*357,130+(i//4)*322
        panel(game,pygame.Rect(x,y,343,302),key==game.player.current_character)
        game.draw_character_portrait(key,pygame.Rect(x+12,y+14,85,147))
        text(game,char["name"].upper(),(x+111,y+14))
        text(game,char["role"],(x+111,y+49),JADE,small=True)
        rank=game.character_mastery.get(key,1)
        unlocked=key in game.player.character_unlocks
        game.draw_wrapped_text(describe_effects(companion_effects(char,rank,False)),x+111,y+78,215,MUTED,20)
        text(game,f"Maestria {rank}/5" if unlocked else f"Nivel {char['unlock_level']}",(x+111,y+134),GOLD,small=True)
        game.draw_wrapped_text(skill_description(char, rank),x+14,y+179,313,PAPER,20)
        cost=mastery_cost(rank)
        label="MAESTRIA COMPLETA" if rank==5 else f"ENTRENAR / {cost} PTS" if unlocked else "BLOQUEADO"
        button(game,"mastery:"+key,label,(x+14,y+253,315,36),unlocked and rank<5 and game.player.points>=cost)
    back(game)


def draw_inventory(game):
    base(game,"TU EXPEDICION","Combina roles para activar afinidad: +5% premios y +10% XP.")
    char=CHARACTERS[game.player.current_character]
    pet=PET_DEFS.get(game.active_pet)
    panel(game,pygame.Rect(45,130,695,295))
    game.draw_character_portrait(char["id"],pygame.Rect(65,150,150,245))
    text(game,char["name"].upper(),(235,153))
    text(game,char["role"],(235,191),JADE,small=True)
    rank=game.character_mastery.get(char["id"],1)
    game.draw_wrapped_text(describe_effects(companion_effects(char,rank,False)),235,226,470,PAPER,20)
    game.draw_wrapped_text(skill_description(char, rank),235,276,470,MUTED,20)
    button(game,"roster",f"MAESTRIA {rank}/5 / ENTRENAR",(235,363,475,40))
    panel(game,pygame.Rect(760,130,695,295))
    if pet:
        pet_portrait(game.screen,pet["id"],pygame.Rect(780,151,210,210))
        text(game,pet["name"],(1008,153))
        text(game,pet["role"],(1008,191),JADE,small=True)
        game.draw_wrapped_text(skill_description(pet, pet_rank(game.pet_copies.get(pet['id'],1))),1008,230,421,PAPER,20)
        text(game,"AFINIDAD ACTIVA" if pet["role"]==char["role"] else "Sin afinidad de rol",(1008,319),GOLD,small=True)
    else:
        text(game,"Todavia viajas solo",(790,170))
        text(game,"Visita el refugio para invocar un companero.",(790,220),MUTED,small=True)
    button(game,"pet_collection","ELEGIR COMPANERO",(1008,363,418,40))
    text(game,"EQUIPO",(48,451),JADE,small=True)
    for i,slot in enumerate(dict.fromkeys(item["slot"] for item in GEAR_DEFS.values())):
        x,y=45+(i%3)*475,487+(i//3)*137
        panel(game,pygame.Rect(x,y,460,120))
        item=GEAR_DEFS.get(game.gear_equipped.get(slot))
        item_icon(game.screen,item["icon"] if item else "ring",pygame.Rect(x+13,y+26,62,62))
        text(game,slot.upper(),(x+90,y+13),JADE,small=True)
        text(game,item["name"] if item else "Ranura vacia",(x+90,y+40))
        game.draw_wrapped_text(item["description"] if item else "Busca una pieza en el mercado.",x+90,y+79,350,MUTED,17)
    back(game)
    button(game,"equipment","CAMBIAR EQUIPO",(1110,819,345,43))


def draw_game_companions(game):
    char=CHARACTERS[game.player.current_character]
    pet=PET_DEFS.get(game.active_pet)
    world=WORLD_DEFS[game.player.current_world]
    panel(game,pygame.Rect(45,143,340,445))
    text(game,world["name"].upper(),(65,159),GOLD,small=True)
    game.draw_character_portrait(char["id"],pygame.Rect(62,198,105,180))
    text(game,char["name"].upper(),(182,216))
    text(game,char["role"],(182,254),JADE,small=True)
    text(game,f"Maestria {game.character_mastery.get(char['id'],1)}/5",(182,281),MUTED,small=True)
    text(game,char["skill_name"],(65,399),GOLD)
    charge=game.companion_charges.get("character:"+char["id"],0)
    text(game,f"Carga {charge}/{char['charge']} / giros pagos",(65,439),MUTED,small=True)
    bar(game,(65,472,300,7),charge,char["charge"])
    game.draw_wrapped_text(skill_description(char, game.character_mastery.get(char['id'],1)),65,502,300,PAPER,20)
    panel(game,pygame.Rect(1115,143,340,445))
    if pet:
        text(game,pet["name"],(1135,157))
        pet_portrait(game.screen,pet["id"],pygame.Rect(1188,197,194,194))
        text(game,pet["skill_name"],(1135,408),GOLD)
        charge=game.companion_charges.get("pet:"+pet["id"],0)
        text(game,f"{pet['role']} / carga {charge}/{pet['charge']}",(1135,446),JADE,small=True)
        bar(game,(1135,477,300,7),charge,pet["charge"])
        game.draw_wrapped_text(skill_description(pet, pet_rank(game.pet_copies.get(pet['id'],1))),1135,502,300,PAPER,19)
    else:
        pet_portrait(game.screen,"comun_01",pygame.Rect(1188,190,194,194),dim=True)
        text(game,"UN LUGAR A TU LADO",(1135,412),GOLD,small=True)
        game.draw_wrapped_text("Invoca una mascota en el refugio. Su habilidad se cargara mientras juegas.",1135,450,296,MUTED,22)
    if pet and pet["role"]==char["role"]:
        text(game,"AFINIDAD: +5% PREMIO / +10% XP",(1119,603),JADE,small=True)
    for i in range(3):
        y=611+i*40
        if i<len(game.abilities.equipped):
            key=game.abilities.equipped[i]
            item=ABILITY_DEFS[key]
            armed=key in game.abilities.armed
            cooldown=int(game.abilities.get_cooldown_remaining(key))
            status="PREPARADA" if armed else f"{cooldown} GIROS" if cooldown else "LISTA"
            button(game,"activate:"+key,f"[{i+1}] {item['name']} / {status}",(45,y,340,33),not game.animating and game.abilities.is_ability_ready(key),armed)
        else:
            button(game,f"equip_slot:{i}",f"[{i+1}] EQUIPAR HABILIDAD",(45,y,340,33),not game.animating)
    if game.last_reward:
        reward=game.last_reward
        panel(game,pygame.Rect(1115,630,340,102))
        text(game,f"BALANCE DEL GIRO: {reward['net']:+} ORO",(1129,640),GOLD,small=True)
        text(game,f"Premio {reward['prize']} / Viaje {reward['travel']}",(1129,665),MUTED,small=True)
        text(game,f"Reembolso {reward['refund']} / Habilidad {reward['skill']}",(1129,687),MUTED,small=True)
        if reward["activations"]:
            game.draw_wrapped_text(" + ".join(reward["activations"]),1118,744,333,JADE,19)


def draw_menu(game):
    game.ui_buttons.clear()
    game.backdrop.draw(game.screen,game.player.current_world,game.visual_time,dim=60)
    panel(game,pygame.Rect(495,107,510,675))
    text(game,"TIMBA RNG",(632,143),GOLD,big=True)
    text(game,"Cinco mundos. Tu propia suerte.",(626,203),MUTED,small=True)
    text(game,f"NIVEL {game.player.level} / {game.player.gold:,} ORO",(639,253),JADE,small=True)
    for i,(key,label) in enumerate((("continue","CONTINUAR VIAJE"),("new_game","NUEVA PARTIDA"),("roster","PERSONAJES Y MAESTRIA"),("settings","AJUSTES"),("quit","SALIR"))):
        button(game,key,label,(540,312+i*79,420,56),selected=i==0)


def draw_game(game):
    game.ui_buttons.clear()
    game.backdrop.draw(game.screen,game.player.current_world,game.visual_time,dim=35)
    draw_game_companions(game)
    panel(game,pygame.Rect(14,10,1472,58))
    for x,label,value,color in ((30,"MUNDO",game.player.current_world,MUTED),(170,"NIVEL",game.player.level,JADE),(330,"ORO",f"{game.player.gold:,}",GOLD),(650,"PUNTOS",f"{game.player.points:,}",PAPER)):
        text(game,label,(x,19),MUTED,small=True)
        text(game,value,(x+75,17),color)
    bar(game,(30,53,1295,4),game.player.xp,xp_to_next_level(game.player.level))
    button(game,"paytable","PAGOS",(1364,20,105,34))
    grid_rect=pygame.Rect(487,143,526,526)
    panel(game,grid_rect)
    game.draw_slot_board(grid_rect)
    panel(game,pygame.Rect(490,684,520,56))
    button(game,"bet_down","-10",(500,694,42,36),not game.animating)
    button(game,"bet_up","+10",(692,694,42,36),not game.animating)
    button(game,"bet_custom","NUMERO",(743,694,110,36),not game.animating)
    button(game,"bet_all","TODO EL ORO",(862,694,135,36),not game.animating)
    bet=game.spin_wager if game.animating else game.last_bet if game.bonus_spins_remaining else game.bet_amount
    bet_text=game.font.render(f"{bet:,}",True,GOLD)
    game.screen.blit(bet_text,bet_text.get_rect(center=(606,711)))
    if game.animating:
        result="Rodillos en movimiento" if game.animation_phase=="spin" else "Combinaciones ganadoras"
    elif game.bonus_spins_remaining:
        result=f"BONUS / {game.bonus_spins_remaining} giros gratis x{game.bonus_multiplier:.2f}"
    elif game.last_reward:
        result=f"Premio {game.last_reward['prize']} oro / Viaje {game.last_reward['travel']} / Balance {game.last_reward['net']:+}"
    else:
        result=""
    result_surface=game.small_font.render(result,True,PAPER)
    game.screen.blit(result_surface,result_surface.get_rect(center=(750,91)))
    for i,(key,label) in enumerate((("shop","MERCADO"),("upgrades","TALLER"),("inventory","INVENTARIO"))):
        button(game,key,label,(45+i*140,801,132,44),not game.animating)
    for i,(key,label) in enumerate((("skills","HABILIDADES"),("equipment","EQUIPO"),("pets","REFUGIO"))):
        button(game,key,label,(1043+i*140,801,132,44),not game.animating)
    button(game,"spin","GIRO GRATIS" if game.bonus_spins_remaining else "GIRAR",(632,792,236,56),not game.animating,True)
    hint=game.small_font.render("ESPACIO / CLICK",True,GOLD)
    game.screen.blit(hint,hint.get_rect(center=(750,773)))
    if game.animating:
        label=f"Girando {min(100,int(100*game.animation_progress/game.spin_duration))}%" if game.animation_phase=="spin" else f"Cascada {game.cascade_index+1}/{len(game.current_scatter_cascades)}"
        status=game.small_font.render(label,True,JADE)
        game.screen.blit(status,status.get_rect(center=(750,872)))
