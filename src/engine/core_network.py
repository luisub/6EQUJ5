"""Bounded green-code activity for the Core's physical control chamber."""
import math

import pygame


class CoreNetwork:
    def __init__(self):
        font = pygame.font.Font(pygame.font.get_default_font(), 8)
        self.glyphs = tuple(font.render(char, False, (79, 175, 113)) for char in '01:<>/+=')
        self.layer = pygame.Surface((480, 270), pygame.SRCALPHA)

    def render(self, crt, boss, camera, destruction=None):
        fade = max(0, 1 - destruction.elapsed / 2.0) if destruction else (0 if boss.is_defeated else 1)
        if fade <= 0:
            return
        self.layer.fill((0, 0, 0, 0))
        time = boss.animation_time + (destruction.elapsed if destruction else 0)
        speed = 22 if boss.final_stage == 1 else 39
        for column in range(24):
            x = round((column * 29 - camera.x * .12) % 510) - 15
            head = (time * (speed + column % 4 * 3) + column * 47) % 320 - 40
            for row in range(6):
                y = round(head - row * 9)
                if 18 < y < 209:
                    glyph = self.glyphs[(column * 3 + row + int(time * 2)) % len(self.glyphs)]
                    self.layer.blit(glyph, (x, y))
        self.layer.set_alpha(round((85 if boss.final_stage == 1 else 125) * fade))
        crt.canvas.blit(self.layer, (0, 0))


def render_projection_scan(surface, boss, camera):
    """A soft scan passes across the projected face; phase two breaks into code."""
    if boss.is_defeated:
        return
    rect = boss.rect.move(-round(camera.x), -round(camera.y))
    y = rect.top + 7 + round((boss.animation_time * 17) % 60)
    width = 30 + round(math.sin(boss.animation_time * 2) * 6)
    pygame.draw.line(surface, (104, 228, 159), (rect.centerx - width // 2, y), (rect.centerx + width // 2, y))
    if boss.final_stage == 2:
        for i in range(7):
            x = rect.left + 19 + i * 14
            y = rect.top + (boss.animation_time * 43 + i * 27) % 90
            pygame.draw.line(surface, (112, 240, 169), (x, y), (x, y + 3 + i % 3 * 2))
