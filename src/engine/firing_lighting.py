"""MODULE: video_game/engine/firing_lighting.py
PURPOSE: Compose and validate the Ohio approach firing-light presentation.
CALLED BY: FieldOpsScene on room entry and while rendering.
HOW TO MODIFY: Keep validation on entry and masks bounded, world-anchored and alpha-preserving.
"""
import hashlib
import io
import json
import logging
import math
from pathlib import Path

import pygame
from PIL import Image

FLASH_FAMILY = Path('effects/approach_maser_flash_v1')
FLASH_NAME = 'flash_64x32.png'
FLASH_SHA256 = '027df21d8bb8d6d21f1421ad7bb50845e941a6907de2af430571fd95374ef7e5'
FLASH_MANIFEST = {'schema_version': 1, 'room_id': 'act_01_approach',
                  'file': FLASH_NAME, 'sha256': FLASH_SHA256,
                  'dimensions': [64, 32], 'pivot_right': [12, 16], 'pivot_left': [51, 16]}


def validate_flash_bytes(data):
    """Validate the exact reviewed RGBA export before decoding or staging it."""
    if hashlib.sha256(data).hexdigest() != FLASH_SHA256:
        raise ValueError('Firing flash does not match the reviewed export')
    with Image.open(io.BytesIO(data)) as image:
        image.load()
        if image.format != 'PNG' or image.mode != 'RGBA' or image.size != (64, 32):
            raise ValueError('Firing flash must be a 64x32 RGBA PNG')
        low, high = image.getchannel('A').getextrema()
        if low != 0 or high == 0:
            raise ValueError('Firing flash needs transparent and visible pixels')


def load_firing_lighting(asset_root, world_surface):
    """Load the complete reviewed family at entry; any invalid family falls back."""
    if asset_root is None or world_surface is None:
        return None
    root = Path(asset_root).resolve()
    family = root / FLASH_FAMILY
    manifest = family / 'manifest.json'
    image = family / FLASH_NAME
    journal = root.parent / f'.{root.name}-asset-build-pending.json'
    try:
        if journal.exists() or journal.is_symlink():
            return None
        if not manifest.exists() and not manifest.is_symlink():
            return None
        for path in (root / 'effects', family, manifest, image):
            if path.is_symlink():
                raise ValueError('Symlinked firing flash family')
        data = json.loads(manifest.read_text(encoding='utf-8'))
        if json.dumps(data, sort_keys=True) != json.dumps(FLASH_MANIFEST, sort_keys=True):
            raise ValueError('Invalid firing flash manifest')
        image_bytes = image.read_bytes()
        validate_flash_bytes(image_bytes)
        burst = pygame.image.load(io.BytesIO(image_bytes), FLASH_NAME).convert_alpha()
        return FiringLighting(burst, world_surface)
    except (OSError, ValueError, TypeError, pygame.error) as exc:
        logging.getLogger(__name__).warning('Firing lighting unavailable: %s', exc)
        return None

LIGHT_SIZE = (144, 112)
FADE_LEVELS = 8
MAX_ACTIVE_FLASHES = 16
AMBIENT_RGB = (181, 186, 199)
# Authored light pools in the 2x-native world, as measured from the installed plate.
LAMP_POOLS = (
    (185, 334, 145, 110),  # left fixture, center (257, 389)
    (170, 410, 237, 160),  # left pool on the wall/floor
    (1010, 401, 144, 80),  # right fixture, center (1082, 441)
    (998, 450, 212, 120),  # right pool on the wall/floor
)


def _radial_rgb(size, maximum):
    """Build one cached additive/multiplier mask; black pixels do nothing."""
    width, height = size
    surface = pygame.Surface(size).convert()
    surface.fill((0, 0, 0))
    for step in range(24, 0, -1):
        fraction = step / 24.0
        strength = (1.0 - fraction) ** 1.4
        color = tuple(round(c * strength) for c in maximum)
        w = max(1, round(width * fraction))
        h = max(1, round(height * fraction))
        pygame.draw.ellipse(surface, color, ((width - w) // 2, (height - h) // 2, w, h))
    return surface


class FiringLighting:
    """Cached render-only lighting masks bound to the validated room background."""

    def __init__(self, burst, world_surface):
        if not isinstance(burst, pygame.Surface) or burst.get_size() != (64, 32) or not (burst.get_flags() & pygame.SRCALPHA):
            raise ValueError('burst must be a 64x32 RGBA surface')
        if not isinstance(world_surface, pygame.Surface) or world_surface.get_size() != (1920, 576) or not (world_surface.get_flags() & pygame.SRCALPHA):
            raise ValueError('world_surface must be the validated 1920x576 RGBA approach plane')
        self.world_source = world_surface
        # The alpha mask is data from the original architecture, not new artwork.
        self.material_mask = pygame.mask.from_surface(world_surface, 0).to_surface(
            setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 255)).convert()
        self.glow_scratch = tuple(pygame.Surface(LIGHT_SIZE).convert() for _ in range(MAX_ACTIVE_FLASHES))
        self.lamp_masks = tuple(_radial_rgb((w, h), (74, 69, 56)) for _, _, w, h in LAMP_POOLS)
        # Ambient and authored lamps are world-fixed. Compute their identical
        # multiplier once, then crop it to the camera at draw time.
        self.ambient_world = pygame.Surface(world_surface.get_size()).convert()
        self.ambient_world.fill(AMBIENT_RGB)
        recovery = pygame.Surface(world_surface.get_size()).convert()
        recovery.fill((0, 0, 0))
        for (world_x, world_y, _, _), mask in zip(LAMP_POOLS, self.lamp_masks):
            recovery.blit(mask, (world_x, world_y), special_flags=pygame.BLEND_RGB_ADD)
        recovery.blit(self.material_mask, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        self.ambient_world.blit(recovery, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        self.world_glows = tuple(_radial_rgb(LIGHT_SIZE, (round(99*i/FADE_LEVELS), round(44*i/FADE_LEVELS), round(60*i/FADE_LEVELS))) for i in range(FADE_LEVELS + 1))
        self.actor_glows = tuple(_radial_rgb(LIGHT_SIZE, (round(136*i/FADE_LEVELS), round(65*i/FADE_LEVELS), round(48*i/FADE_LEVELS))) for i in range(FADE_LEVELS + 1))
        self.bursts = {}
        self.burst_sources = {'right': burst, 'left': pygame.transform.flip(burst, True, False)}
        self.rotated_bursts = {}  # At most 26 directions × 8 fade levels.
        for direction in ('right', 'left'):
            source = self.burst_sources[direction]
            for level in range(1, FADE_LEVELS + 1):
                image = source.copy()
                image.set_alpha(round(255 * level / FADE_LEVELS))
                self.bursts[direction, level] = image

    @staticmethod
    def active_flashes(flashes, token):
        """Only current-scene normal shots participate; old/charged flashes stay legacy."""
        return [f for f in flashes if f.get('lighting_token') == token
                and not f.get('is_charged', False) and f.get('life', 0) > 0]

    @staticmethod
    def _level(flash):
        life = max(0.0, min(1.0, flash['life'] / flash['max_life']))
        return min(FADE_LEVELS, max(1, round(life * FADE_LEVELS)))

    @staticmethod
    def _position(flash, camera):
        x, y = camera.world_to_screen(flash['x'], flash['y'])
        return (2*x, 2*y)

    def render_ambient(self, crt, camera):
        """Dim authored backdrop; restore lamp pools only on architecture pixels."""
        crop = pygame.Rect(2 * round(camera.x), 2 * round(camera.y), 960, 540)
        if not self.material_mask.get_rect().contains(crop):
            return False
        crt.composite_native_effects([(self.ambient_world.subsurface(crop), (0, 0), pygame.BLEND_RGB_MULT)])
        return True

    def render_world_bounce(self, crt, camera, flashes):
        """Light only authored material pixels, never empty sky or gameplay tiles."""
        camera_x = 2 * round(camera.x)
        camera_y = 2 * round(camera.y)
        layers = []
        for flash, scratch in zip(flashes, self.glow_scratch):
            sx, sy = self._position(flash, camera)
            left, top = sx - 72, sy - 56
            world_rect = pygame.Rect(camera_x + left, camera_y + top, *LIGHT_SIZE)
            clipped = world_rect.clip(self.material_mask.get_rect())
            if clipped.width <= 0 or clipped.height <= 0:
                continue
            offset = (clipped.x - world_rect.x, clipped.y - world_rect.y)
            scratch.fill((0, 0, 0))
            scratch.blit(self.world_glows[self._level(flash)], offset,
                         area=pygame.Rect(offset, clipped.size))
            scratch.blit(self.material_mask, offset, area=clipped, special_flags=pygame.BLEND_RGB_MULT)
            layers.append((scratch, (left, top), pygame.BLEND_RGB_ADD))
        if layers:
            crt.composite_native_effects(layers)

    def light_actor(self, sprite, dest, camera, flashes):
        """Tint only native sprite RGB inside the light; preserve its exact alpha."""
        result = None
        rect = pygame.Rect(dest, sprite.get_size())
        for flash in flashes:
            sx, sy = self._position(flash, camera)
            light_rect = pygame.Rect(sx - 72, sy - 56, *LIGHT_SIZE)
            if rect.colliderect(light_rect):
                if result is None:
                    result = sprite.copy()
                result.blit(self.actor_glows[self._level(flash)], (light_rect.x - rect.x, light_rect.y - rect.y), special_flags=pygame.BLEND_RGB_ADD)
        return result if result is not None else sprite

    def render_bursts(self, crt, camera, flashes):
        """Draw authored native burst above weather and below interface."""
        layers = []
        for flash in flashes:
            sx, sy = self._position(flash, camera)
            direction = 'left' if flash.get('direction') == 'left' else 'right'
            pivot_x = 51 if direction == 'left' else 12
            level = self._level(flash)
            vector = flash.get('aim_vector')
            relative = 0
            if vector is not None and math.hypot(*vector) > 1e-4:
                heading = math.degrees(math.atan2(vector[1], vector[0]))
                relative = (heading - (180 if direction == 'left' else 0) + 180) % 360 - 180
                relative = max(-90, min(90, 15 * round(relative / 15)))
            if relative:
                key = (direction, relative, level)
                if key not in self.rotated_bursts:
                    image = pygame.transform.rotate(self.burst_sources[direction], -relative)
                    image.set_alpha(round(255 * level / FADE_LEVELS))
                    radians = math.radians(relative)
                    dx = pivot_x - 32
                    pivot = (round(image.get_width() / 2 + math.cos(radians) * dx),
                             round(image.get_height() / 2 + math.sin(radians) * dx))
                    self.rotated_bursts[key] = (image, pivot)
                image, pivot = self.rotated_bursts[key]
            else:
                image, pivot = self.bursts[direction, level], (pivot_x, 16)
            if -96 <= sx < 1056 and -96 <= sy < 636:
                layers.append((image, (sx - pivot[0], sy - pivot[1]), 0))
        if layers:
            crt.composite_native_effects(layers)
