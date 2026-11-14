"""PURPOSE: Bounded decorative traffic for the fictional Ohio service edge.
CALLED BY: video_game.engine.scenes.field.FieldOpsScene.
HOW TO MODIFY: Use cached authored art only; activity must never affect collisions or combat.
"""
from pathlib import Path

import pygame


class ServiceTraffic:
    """A single background vehicle with a fixed path and no gameplay state."""

    def __init__(self, asset_root):
        self.elapsed = 0.0
        self.right = self.left = None
        if asset_root is None:
            return
        path = Path(asset_root) / "environments/ohio/salvage_yard/wagon.png"
        try:
            image = pygame.image.load(str(path)).convert_alpha()
            self.left = pygame.transform.scale(image, (72, 33))
            self.right = pygame.transform.flip(self.left, True, False)
        except (OSError, pygame.error):
            pass

    def update(self, dt, paused=False):
        if not paused and dt > 0:
            self.elapsed = (self.elapsed + min(dt, 0.1)) % 36.0

    def render(self, surface, camera):
        if self.right is None:
            return
        # Travel for 16 seconds in each direction with two-second end pauses.
        phase = self.elapsed
        if phase < 16:
            x, image = 304 + phase * 36, self.right
        elif phase < 18:
            x, image = 880, self.right
        elif phase < 34:
            x, image = 880 - (phase - 18) * 36, self.left
        else:
            x, image = 304, self.left
        # Wheels sit just above the authored pavement, behind all actors.
        sx, sy = camera.world_to_screen(x, 207)
        if -image.get_width() < sx < camera.viewport_w:
            surface.blit(image, (sx, sy))
