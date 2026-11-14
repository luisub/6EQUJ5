"""
# PURPOSE: High-performance bounded visual particle and combat effect engine (muzzle flashes, sparks, dust, mortar smoke).
# CALLED BY: FieldOpsScene, BossScene, weapons, and enemies.
# HOW TO MODIFY: Tune particle lifetimes, physics velocities, or maximum pool caps.
"""

import math
import random
import hashlib
import io
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pygame
from PIL import Image

from video_game.engine import config
from video_game.engine.world import Camera, Room

MAX_PARTICLES = 128
MAX_BURSTS = 16
MASER_FAMILY = Path('effects/maser_discharge')
MASER_NAME = 'flash_64x32.png'
MASER_SHA256 = '244482ae198b1aaa23f4bb225085d5e29e3a0123dec289fa3bc9d439d32db3bc'
MASER_MANIFEST = {'schema_version': 1, 'file': MASER_NAME, 'sha256': MASER_SHA256,
                  'dimensions': [64, 32], 'pivot_right': [12, 16], 'pivot_left': [51, 16]}


def validate_maser_bytes(data):
    """Accept only the registered, transparent authored export."""
    if hashlib.sha256(data).hexdigest() != MASER_SHA256:
        raise ValueError('Maser discharge does not match the reviewed export')
    with Image.open(io.BytesIO(data)) as image:
        image.load()
        if image.format != 'PNG' or image.mode != 'RGBA' or image.size != (64, 32):
            raise ValueError('Maser discharge must be a 64x32 RGBA PNG')
        low, high = image.getchannel('A').getextrema()
        if low != 0 or high == 0:
            raise ValueError('Maser discharge requires transparent and visible pixels')


def load_maser_presentation(asset_root):
    """Validate and decode once on scene entry; incomplete transactions fall back."""
    if asset_root is None:
        return None
    root = Path(asset_root).resolve()
    family = root / MASER_FAMILY
    manifest, image = family / 'manifest.json', family / MASER_NAME
    journal = root.parent / f'.{root.name}-asset-build-pending.json'
    try:
        if journal.exists() or journal.is_symlink():
            return None
        if not manifest.exists() and not manifest.is_symlink():
            return None
        if any(path.is_symlink() for path in (root / 'effects', family, manifest, image)):
            raise ValueError('Symlinked maser discharge family')
        data = json.loads(manifest.read_text(encoding='utf-8'))
        if json.dumps(data, sort_keys=True) != json.dumps(MASER_MANIFEST, sort_keys=True):
            raise ValueError('Invalid maser discharge manifest')
        data = image.read_bytes()
        validate_maser_bytes(data)
        return MaserPresentation(pygame.image.load(io.BytesIO(data), MASER_NAME).convert_alpha())
    except (OSError, ValueError, TypeError, pygame.error) as exc:
        logging.getLogger(__name__).warning('Maser discharge unavailable: %s', exc)
        return None


class MaserPresentation:
    """Bounded native-density shot artwork and local, alpha-preserving light."""

    LEVELS = 8
    LIGHT_SIZE = (96, 72)

    def __init__(self, burst):
        if burst.get_size() != (64, 32) or not burst.get_flags() & pygame.SRCALPHA:
            raise ValueError('Expected a 64x32 alpha burst')
        charged = burst.copy()
        # Recolor once, keeping the authored alpha and cluster shape intact.
        for y in range(charged.get_height()):
            for x in range(charged.get_width()):
                r, g, b, a = burst.get_at((x, y))
                if a:
                    strength = max(r, g, b) / 255.0
                    charged.set_at((x, y), (round(255 * strength), round(175 * strength),
                                            round(72 * strength), a))
        self.sources = (burst, charged)
        self.bursts = {}  # At most 24 directions x 8 levels x 2 charge states.
        self.glows = tuple(tuple(self._glow(charged, level) for level in range(self.LEVELS + 1))
                           for charged in (False, True))

    @classmethod
    def _glow(cls, charged, level):
        surface = pygame.Surface(cls.LIGHT_SIZE).convert()
        surface.fill((0, 0, 0))
        color = (58, 31, 10) if charged else (17, 43, 51)
        for step in range(18, 0, -1):
            fraction = step / 18
            strength = (1 - fraction) ** 1.5 * level / cls.LEVELS
            width, height = (max(1, round(v * fraction)) for v in cls.LIGHT_SIZE)
            pygame.draw.ellipse(surface, tuple(round(c * strength) for c in color),
                                ((cls.LIGHT_SIZE[0] - width) // 2,
                                 (cls.LIGHT_SIZE[1] - height) // 2, width, height))
        return surface

    @staticmethod
    def active_flashes(flashes):
        return [f for f in flashes if f.get('maser_presentation') and f.get('life', 0) > 0]

    def _level(self, flash):
        return min(self.LEVELS, max(1, round(self.LEVELS * flash['life'] / flash['max_life'])))

    @staticmethod
    def _position(flash, camera):
        x, y = camera.world_to_screen(flash['x'], flash['y'])
        return 2 * x, 2 * y

    def light_actor(self, sprite, dest, camera, flashes):
        result = None
        rect = pygame.Rect(dest, sprite.get_size())
        for flash in flashes:
            x, y = self._position(flash, camera)
            light_rect = pygame.Rect(x - 48, y - 36, *self.LIGHT_SIZE)
            if rect.colliderect(light_rect):
                if result is None:
                    result = sprite.copy()
                glow = self.glows[bool(flash['is_charged'])][self._level(flash)]
                result.blit(glow, (light_rect.x - rect.x, light_rect.y - rect.y), special_flags=pygame.BLEND_RGB_ADD)
        return result if result is not None else sprite

    def render_bursts(self, crt, camera, flashes):
        layers = []
        for flash in flashes:
            if flash.get('lighting_only'):
                continue
            x, y = self._position(flash, camera)
            if not (-96 <= x < 1056 and -96 <= y < 636):
                continue
            dx, dy = flash.get('aim_vector', (1, 0))
            angle = round(math.degrees(math.atan2(dy, dx)) / 15) * 15 % 360
            charged, level = bool(flash['is_charged']), self._level(flash)
            key = (charged, angle, level)
            if key not in self.bursts:
                source = self.sources[charged]
                image = pygame.transform.rotate(source, -angle)
                image.set_alpha(round(255 * level / self.LEVELS))
                radians = math.radians(angle)
                # Rotate the pixel-center registration, including the half-pixel
                # offset of the even-sized canvas, around the same center as SDL.
                pivot = (round((image.get_width() - 1) / 2 - 19.5 * math.cos(radians) - .5 * math.sin(radians)),
                         round((image.get_height() - 1) / 2 - 19.5 * math.sin(radians) + .5 * math.cos(radians)))
                self.bursts[key] = image, pivot
            image, pivot = self.bursts[key]
            layers.append((self.glows[charged][level], (x - 48, y - 36), pygame.BLEND_RGB_ADD))
            layers.append((image, (x - pivot[0], y - pivot[1]), 0))
        if layers:
            crt.composite_native_effects(layers)


class EffectManager:
    """
    Manages bounded visual particle effects, muzzle flashes, ricochet sparks,
    dust puffs, and mortar smoke with viewport culling and pause freeze safety.
    """

    def __init__(self):
        self.sparks: List[Dict[str, Any]] = []
        self.dust: List[Dict[str, Any]] = []
        self.flashes: List[Dict[str, Any]] = []
        self.smoke: List[Dict[str, Any]] = []

    def clear(self):
        """Immediately purge all active particles and effects."""
        self.sparks.clear()
        self.dust.clear()
        self.flashes.clear()
        self.smoke.clear()

    def discard_maser_flashes(self):
        """Do not carry an old room or life into a new local light context."""
        self.flashes = [f for f in self.flashes if not (f.get('maser_presentation') or f.get('lighting_only'))]

    @property
    def total_count(self) -> int:
        """Total number of active particle instances."""
        return len(self.sparks) + len(self.dust) + len(self.flashes) + len(self.smoke)

    def add_muzzle_flash(self, x: float, y: float, direction: str = "right", is_charged: bool = False, lighting_token=None, maser_presentation=False, *, lighting_only=False, input_generation=None):
        """Trigger an instant muzzle flash burst."""
        if len(self.flashes) >= MAX_BURSTS:
            self.flashes.pop(0)

        color = (210, 255, 235) if not is_charged else (255, 224, 128)
        glow_color = (51, 255, 102) if not is_charged else (255, 158, 44)
        radius = 16.0 if not is_charged else 26.0

        self.flashes.append({
            "x": x,
            "y": y,
            "radius": radius,
            "life": 0.08,
            "max_life": 0.08,
            "color": color,
            "glow_color": glow_color,
            "direction": direction,
            "is_charged": is_charged,
            "lighting_token": lighting_token,
            "maser_presentation": maser_presentation,
            "lighting_only": lighting_only,
            "input_generation": input_generation,
        })

    def current_lighting_flashes(self, input_generation):
        """Discard stale compact light after pause, focus loss or control reset."""
        return [flash for flash in self.flashes
                if not flash.get('lighting_only') or flash.get('input_generation') == input_generation]

    def add_impact_sparks(
        self,
        x: float,
        y: float,
        count: int = 6,
        is_charged: bool = False,
        dir_x: float = 0.0,
        dir_y: float = 0.0,
    ):
        """Spawn energetic ricochet sparks."""
        color = (255, 220, 100) if is_charged else (100, 230, 255)
        for i in range(count):
            if len(self.sparks) >= MAX_PARTICLES:
                self.sparks.pop(0)

            # Cone directed opposite to incoming trajectory or omnidirectional
            if dir_x != 0.0 or dir_y != 0.0:
                base_angle = math.atan2(-dir_y, -dir_x)
                angle = base_angle + (random.random() - 0.5) * 1.6
            else:
                angle = random.random() * 2.0 * math.pi

            speed = random.uniform(40.0, 140.0) if not is_charged else random.uniform(60.0, 220.0)
            life = random.uniform(0.12, 0.28)

            self.sparks.append({
                "x": x,
                "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": life,
                "max_life": life,
                "color": color,
                "gravity": 220.0,
            })

    def add_dust_puff(self, x: float, y: float, count: int = 3, spread: float = 8.0):
        """Spawn low ground friction dust puffs for jumps, landings, and slides."""
        for _ in range(count):
            if len(self.dust) >= MAX_PARTICLES:
                self.dust.pop(0)

            life = random.uniform(0.18, 0.35)
            self.dust.append({
                "x": x + random.uniform(-spread, spread),
                "y": y + random.uniform(-2.0, 2.0),
                "vx": random.uniform(-20.0, 20.0),
                "vy": random.uniform(-15.0, -5.0),
                "radius": 2.0,
                "max_radius": random.uniform(5.0, 8.0),
                "life": life,
                "max_life": life,
                "color": (94, 112, 118),
            })

    def add_mortar_smoke(self, x: float, y: float, count: int = 4):
        """Spawn billowing explosive smoke puffs for boss artillery and explosions."""
        for _ in range(count):
            if len(self.smoke) >= MAX_PARTICLES:
                self.smoke.pop(0)

            life = random.uniform(0.30, 0.60)
            angle = random.random() * 2.0 * math.pi
            speed = random.uniform(20.0, 60.0)

            self.smoke.append({
                "x": x,
                "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed - 15.0,
                "radius": 4.0,
                "max_radius": random.uniform(12.0, 20.0),
                "life": life,
                "max_life": life,
                "color": (58, 72, 78),
            })

    def update(self, dt: float, room: Optional[Room] = None, is_paused: bool = False):
        """
        Step simulation across all particle pools.
        Pause safety: zero movement and zero decay when is_paused is True.
        """
        if is_paused or dt <= 0.0:
            return

        # 1. Update flashes
        surviving_flashes = []
        for f in self.flashes:
            f["life"] -= dt
            if f["life"] > 0.0:
                surviving_flashes.append(f)
        self.flashes = surviving_flashes

        # 2. Update sparks (velocity + gravity)
        surviving_sparks = []
        for s in self.sparks:
            s["x"] += s["vx"] * dt
            s["y"] += s["vy"] * dt
            s["vy"] += s["gravity"] * dt
            s["life"] -= dt
            if s["life"] > 0.0:
                surviving_sparks.append(s)
        self.sparks = surviving_sparks

        # 3. Update dust (expanding radius)
        surviving_dust = []
        for d in self.dust:
            d["x"] += d["vx"] * dt
            d["y"] += d["vy"] * dt
            d["life"] -= dt
            growth_ratio = 1.0 - max(0.0, d["life"] / d["max_life"])
            d["radius"] = 2.0 + growth_ratio * (d["max_radius"] - 2.0)
            if d["life"] > 0.0:
                surviving_dust.append(d)
        self.dust = surviving_dust

        # 4. Update smoke (expanding radius + upward drift)
        surviving_smoke = []
        for sm in self.smoke:
            sm["x"] += sm["vx"] * dt
            sm["y"] += sm["vy"] * dt
            sm["life"] -= dt
            growth_ratio = 1.0 - max(0.0, sm["life"] / sm["max_life"])
            sm["radius"] = 4.0 + growth_ratio * (sm["max_radius"] - 4.0)
            if sm["life"] > 0.0:
                surviving_smoke.append(sm)
        self.smoke = surviving_smoke

    def render(self, surface: pygame.Surface, camera: Camera, *, suppress_tap_token=None, suppress_maser=False):
        """Render all active effects with viewport culling."""
        cw, ch = camera.viewport_w, camera.viewport_h

        # 1. Smoke puffs
        for sm in self.smoke:
            sx, sy = camera.world_to_screen(sm["x"], sm["y"])
            r = int(sm["radius"])
            if -r <= sx <= cw + r and -r <= sy <= ch + r:
                # Alpha fade
                fade = max(0.0, min(1.0, sm["life"] / sm["max_life"]))
                alpha = int(90 * fade)
                smoke_surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
                c = sm["color"]
                pygame.draw.circle(smoke_surf, (c[0], c[1], c[2], alpha), (r + 1, r + 1), r)
                surface.blit(smoke_surf, (sx - r - 1, sy - r - 1))

        # 2. Dust puffs
        for d in self.dust:
            sx, sy = camera.world_to_screen(d["x"], d["y"])
            r = int(d["radius"])
            if -r <= sx <= cw + r and -r <= sy <= ch + r:
                fade = max(0.0, min(1.0, d["life"] / d["max_life"]))
                alpha = int(120 * fade)
                dust_surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
                c = d["color"]
                pygame.draw.circle(dust_surf, (c[0], c[1], c[2], alpha), (r + 1, r + 1), r)
                surface.blit(dust_surf, (sx - r - 1, sy - r - 1))

        # 3. Ricochet sparks
        for s in self.sparks:
            sx, sy = camera.world_to_screen(s["x"], s["y"])
            if 0 <= sx < cw and 0 <= sy < ch:
                c = s["color"]
                pygame.draw.circle(surface, c, (sx, sy), 1)

        # 4. Muzzle flashes
        for f in self.flashes:
            if f.get('lighting_only'):
                continue
            if suppress_maser and f.get('maser_presentation'):
                continue
            if (suppress_tap_token is not None and f.get('lighting_token') == suppress_tap_token
                    and not f.get('is_charged', False)):
                continue
            sx, sy = camera.world_to_screen(f["x"], f["y"])
            r = int(f["radius"])
            if -r <= sx <= cw + r and -r <= sy <= ch + r:
                # Central diamond
                pts = [
                    (sx, sy - r // 2),
                    (sx + r, sy),
                    (sx, sy + r // 2),
                    (sx - r // 4, sy),
                ] if f["direction"] == "right" else [
                    (sx, sy - r // 2),
                    (sx + r // 4, sy),
                    (sx, sy + r // 2),
                    (sx - r, sy),
                ]
                pygame.draw.polygon(surface, f["color"], pts)
                # Outer glow
                pygame.draw.circle(surface, f["glow_color"], (sx, sy), max(2, r // 3))

