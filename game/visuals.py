"""Illustrated world backdrops with lightweight, deterministic ambient loops."""

import math
from pathlib import Path

import pygame

ASSETS = Path(__file__).resolve().parent.parent / "assets"
_ART = {}


def illustration(group, name, size):
    key = (group, name, tuple(size))
    if key not in _ART:
        path = ASSETS / group / f"{name}.png"
        if not path.exists():
            return None
        source = pygame.image.load(str(path)).convert_alpha()
        _ART[key] = pygame.transform.smoothscale(source, size)
    return _ART[key]


def pet_portrait(screen, pet_id, rect, dim=False):
    picture = illustration("pets", pet_id, rect.size)
    if picture is not None:
        screen.blit(picture, rect)
    if dim:
        shade = pygame.Surface(rect.size, pygame.SRCALPHA)
        shade.fill((10, 17, 27, 185))
        screen.blit(shade, rect)


class WorldBackdrop:
    def __init__(self, size):
        self.size = size
        self.layer = pygame.Surface(size, pygame.SRCALPHA)
        self.veil = pygame.Surface(size, pygame.SRCALPHA)

    def draw(self, screen, world, elapsed, dim=20):
        width, height = self.size
        picture = illustration("worlds", f"world_{world}", (width + 32, height + 24))
        if picture:
            screen.blit(picture, (-16 + round(math.sin(elapsed * .12) * 12), -12 + round(math.cos(elapsed * .16) * 8)))
        else:
            screen.fill((14, 22, 32))
        self.layer.fill((0, 0, 0, 0))
        for i in range(42):
            seed_x, seed_y = (i * 317 + world * 47) % width, (i * 173) % height
            if world == 1:
                x = (seed_x + elapsed * (3 + i % 3)) % width
                y = (seed_y - elapsed * 8) % height
                pygame.draw.circle(self.layer, (245, 197, 119, 60 + int(30 * math.sin(elapsed + i))), (int(x), int(y)), 1 + i % 2)
            elif world == 2:
                x, y = (seed_x - elapsed * 80) % width, (seed_y + elapsed * 230) % height
                pygame.draw.line(self.layer, (116, 209, 223, 65), (x, y), (x - 6, y + 18), 1)
            elif world == 3:
                x = (seed_x + elapsed * 15 + 20 * math.sin(elapsed + i)) % width
                y = (seed_y + elapsed * 13) % height
                if i % 3:
                    pygame.draw.ellipse(self.layer, (145, 199, 127, 100), (x, y, 8, 3))
                else:
                    pygame.draw.circle(self.layer, (228, 232, 147, 130 + int(70 * math.sin(elapsed * 2 + i))), (int(x), int(y)), 2)
            elif world == 4:
                x = (seed_x + 12 * math.sin(elapsed + i)) % width
                y = height - (seed_y + elapsed * (18 + i % 6)) % height
                pygame.draw.line(self.layer, (255, 143, 69, 140), (x, y), (x + 2, y - 5), 2)
            else:
                alpha = 100 + int(85 * math.sin(elapsed * .8 + i))
                pygame.draw.circle(self.layer, (249, 222, 153, alpha), (seed_x, seed_y), 1 + i % 2)
        if world == 2:
            x = int((elapsed * 170) % (width + 600)) - 600
            pygame.draw.line(self.layer, (243, 179, 99, 70), (x, int(height * .58)), (x + 350, int(height * .58)), 3)
        elif world == 5:
            phase = elapsed % 12
            if phase < 2:
                x, y = width - phase * 400, 90 + phase * 100
                pygame.draw.line(self.layer, (249, 229, 184, int(160 * (1 - phase / 2))), (x, y), (x + 110, y - 28), 2)
        screen.blit(self.layer, (0, 0))
        self.veil.fill((7, 12, 19, dim))
        screen.blit(self.veil, (0, 0))


def item_icon(screen, icon, rect, color=(226, 188, 115)):
    """A small native icon set; no font glyph or emoji dependencies."""
    cx, cy = rect.center
    r = min(rect.size) * .32
    def polygon(points):
        pygame.draw.polygon(screen, color, [(cx + x*r, cy + y*r) for x, y in points], 2)
    if icon in ("coin", "ring", "compass", "moon"):
        pygame.draw.circle(screen, color, (cx, cy), int(r), 3)
        if icon == "coin":
            pygame.draw.line(screen, color, (cx, cy-r*.6), (cx, cy+r*.6), 3)
        elif icon == "ring":
            polygon([(-.3, -1), (0, -1.4), (.3, -1), (0, -.7)])
        elif icon == "compass":
            polygon([(0, -1), (.4, .5), (0, .2), (-.4, .5)])
        else:
            pygame.draw.circle(screen, (25, 37, 50), (int(cx+r*.5), int(cy-r*.3)), int(r*.8))
    elif icon == "bolt":
        polygon([(.2,-1),(-.7,.2),(-.1,.2),(-.3,1),(.8,-.3),(.1,-.3)])
    elif icon == "shield":
        polygon([(-.8,-.8),(0,-1),(.8,-.8),(.7,.4),(0,1),(-.7,.4)])
    elif icon == "crown":
        polygon([(-1,-.7),(-.5,0),(0,-1),(.5,0),(1,-.7),(.8,.8),(-.8,.8)])
    elif icon == "book":
        polygon([(-1,-.8),(0,-.5),(1,-.8),(1,.8),(0,1),(-1,.8)])
        pygame.draw.line(screen, color, (cx,cy-r*.5),(cx,cy+r),2)
    elif icon == "ticket":
        pygame.draw.rect(screen, color, (cx-r, cy-r*.6, r*2, r*1.2), 2, border_radius=4)
        pygame.draw.line(screen,color,(cx+r*.4,cy-r*.6),(cx+r*.4,cy+r*.6),2)
    elif icon in ("leaf", "clover"):
        for dx, dy in ((-.4,-.3),(.4,-.3),(-.3,.3),(.3,.3)):
            pygame.draw.circle(screen,color,(int(cx+dx*r),int(cy+dy*r)),int(r*.45),2)
        pygame.draw.line(screen,color,(cx,cy),(cx-r*.3,cy+r),2)
    else:
        polygon([(math.cos(i*math.pi/5-math.pi/2)*(1 if i%2==0 else .45), math.sin(i*math.pi/5-math.pi/2)*(1 if i%2==0 else .45)) for i in range(10)])
