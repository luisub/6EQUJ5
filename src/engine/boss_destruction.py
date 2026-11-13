"""A bounded, deterministic boss breakup rendered from the defeated body."""

import math
import random

import pygame

from . import config

DURATION = 2.6
BREAK_TIME = 0.45


class BossDestruction:
    """Charge, rupture, flying body fragments, then fading embers. No gameplay damage."""

    def __init__(self, boss):
        self.elapsed = 0.0
        self.rect = boss.rect.copy()
        self.color = getattr(boss, 'color', (255, 165, 75))
        rng = random.Random(boss.target_id)
        art = getattr(boss, 'art_surface', None)
        if art is None:
            # Capture the existing silhouette, including bosses drawn procedurally.
            from .world import Camera
            surface = pygame.Surface((480, 270), pygame.SRCALPHA)
            camera = Camera(480, 270)
            camera.x, camera.y = self.rect.x - 20, self.rect.y - 20
            boss.render(surface, camera)
            art = surface.subsurface((20, 20, self.rect.w, self.rect.h)).copy()
        self.shards = []
        if art is not None:
            width, height = self.rect.w * config.RENDER_DENSITY, self.rect.h * config.RENDER_DENSITY
            body = pygame.transform.scale(art, (width, height))
            for row in range(4):
                for col in range(6):
                    x0, x1 = round(col * width / 6), round((col + 1) * width / 6)
                    y0, y1 = round(row * height / 4), round((row + 1) * height / 4)
                    piece = body.subsurface((x0, y0, x1 - x0, y1 - y0)).copy()
                    self.shards.append((piece, (x0 / config.RENDER_DENSITY - self.rect.w / 2,
                                                y0 / config.RENDER_DENSITY - self.rect.h / 2),
                                        ((col - 2.5) * 23 + rng.uniform(-12, 12),
                                         (row - 2) * 24 - rng.uniform(25, 65))))
        self.embers = [(rng.uniform(0, math.tau), rng.uniform(25, 120), rng.uniform(.65, 1.8))
                       for _ in range(42)]
        self.glow = pygame.Surface((360, 300), pygame.SRCALPHA)
        for radius in range(145, 0, -5):
            strength = int(45 * (1 - radius / 150))
            pygame.draw.circle(self.glow, (255, 140, 55, strength), (180, 150), radius)
        self.flash = pygame.Surface((192, 192))
        self.flash.fill((0, 0, 0))
        for radius in range(96, 0, -1):
            strength = (1 - radius / 96) ** 2
            color = tuple(round(channel * strength) for channel in (255, 235, 190))
            pygame.draw.circle(self.flash, color, (96, 96), radius)

    @property
    def done(self):
        return self.elapsed >= DURATION

    @property
    def body_visible(self):
        return self.elapsed < BREAK_TIME

    def update(self, dt):
        if math.isfinite(dt) and dt > 0:
            self.elapsed = min(DURATION, self.elapsed + dt)

    def render(self, crt, camera):
        if self.done:
            return
        density = config.RENDER_DENSITY
        center = camera.world_to_screen(*self.rect.center)
        cx, cy = round(center[0] * density), round(center[1] * density)
        t = self.elapsed
        layer = pygame.Surface((config.RENDER_WIDTH, config.RENDER_HEIGHT), pygame.SRCALPHA)
        if t < BREAK_TIME:
            strength = t / BREAK_TIME
            for index in range(7):
                angle = index * math.tau / 7 + .25
                outer = (cx + round(math.cos(angle) * 75), cy + round(math.sin(angle) * 64))
                bend = (cx + round(math.cos(angle + .2) * 24), cy + round(math.sin(angle + .2) * 22))
                pygame.draw.lines(layer, (120, 238, 255, round(230 * strength)), False,
                                  [(cx, cy), bend, outer], 2)
            pygame.draw.circle(layer, (235, 254, 255, round(220 * strength)), (cx, cy), round(5 + 12 * strength))
        else:
            age = t - BREAK_TIME
            fade = max(0, 1 - age / (DURATION - BREAK_TIME))
            self.glow.set_alpha(round(220 * fade))
            layer.blit(self.glow, (cx - 180, cy - 150))
            for delay, tint in ((0, (255, 215, 130)), (.18, self.color)):
                ring_age = age - delay
                if 0 <= ring_age < 1.1:
                    radius = round(30 + ring_age * 180)
                    pygame.draw.ellipse(layer, (*tint, round(220 * (1 - ring_age / 1.1))),
                                        (cx - radius, cy - radius // 2, radius * 2, radius), 3)
            for piece, offset, velocity in self.shards:
                x = cx + round((offset[0] + velocity[0] * age) * density)
                y = cy + round((offset[1] + velocity[1] * age + 42 * age * age) * density)
                fragment = pygame.transform.rotozoom(piece, age * (velocity[0] + 35), 1 - .12 * age)
                fragment.set_alpha(round(255 * fade))
                layer.blit(fragment, fragment.get_rect(center=(x + piece.get_width() // 2,
                                                               y + piece.get_height() // 2)))
            for angle, speed, life in self.embers:
                if age < life:
                    x = cx + round(math.cos(angle) * speed * age * density)
                    y = cy + round((math.sin(angle) * speed * age + 24 * age * age) * density)
                    tail = (x - round(math.cos(angle) * 7), y - round(math.sin(angle) * 7))
                    pygame.draw.line(layer, (255, 171, 83, round(230 * (1 - age / life))), tail, (x, y), 2)
        crt.composite_native(layer, (0, 0), (480, 270))
        age = t - BREAK_TIME
        if 0 <= age < .6:
            flash = self.flash.copy()
            strength = round(255 * (1 - age / .6))
            flash.fill((strength, strength, strength), special_flags=pygame.BLEND_RGB_MULT)
            crt.composite_native_effects([(flash, (cx - 96, cy - 96), pygame.BLEND_RGB_ADD)])
