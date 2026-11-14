"""Arcade title: the banner, soundtrack and one fresh-start action."""
import math
import random

import pygame

from .. import config
from ..ui.viewport import window_to_logical
from .base import BaseScene


class TitleBootScene(BaseScene):
    """Start a fresh run without save-selection or confirmation screens."""

    PRIMARY = pygame.Rect(150, 194, 180, 42)

    def __init__(self, machine):
        super().__init__(machine)
        self.elapsed_seconds = 0.0
        self.status = ""
        rng = random.Random(1977)
        self.stars = [(rng.randrange(480), rng.randrange(270), rng.randint(1, 3))
                      for _ in range(45)]
        source = machine.assets.image("ui/title_banner.png", (2172, 724))
        self.banner = pygame.transform.scale(source, (960, 320)).convert()
        font = pygame.font.Font(pygame.font.get_default_font(), 16)
        self.credit = font.render("by @luisub 2026", True, (160, 190, 211))

    def on_enter(self, **kwargs):
        self.elapsed_seconds = 0.0
        self.status = ""

    def _new_game(self, guard):
        success, message = self.machine.start_new_game(
            replace_existing=True, show_opening=True, opening_guard=guard)
        if success:
            self.machine.audio.play_sfx("station_chime", volume=0.65)
        else:
            self.status = "COULD NOT SAVE. PRESS START TO RETRY."
            self.machine.save_notice = message

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if window_to_logical(event.pos, self.machine.crt) is not None:
                self._new_game(("mouse", event.button))
        elif (event.type == pygame.KEYDOWN and not getattr(event, "repeat", False)
              and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_n)):
            if getattr(event, "controller_semantic", False):
                guard = ("controller", getattr(event, "controller_instance", None), event.controller_button)
            else:
                guard = ("key", event.key)
            self._new_game(guard)

    def update(self, dt_seconds):
        self.elapsed_seconds += dt_seconds

    def render(self, crt):
        crt.clear((3, 5, 15))
        for x, y, depth in self.stars:
            drift = (y + self.elapsed_seconds * depth * 1.5) % 270
            light = 65 + depth * 28
            pygame.draw.rect(crt.canvas, (light // 2, light, min(255, light + 35)),
                             (x, round(drift), 1, 1))
        crt.composite_native(self.banner, (0, 18), (480, 160))
        width, height = self.credit.get_size()
        crt.composite_native(self.credit, ((960 - width) / 4, 96), (width / 2, height / 2))
        pulse = 0.5 + 0.5 * math.sin(self.elapsed_seconds * 3)
        color = (round(165 + 70 * pulse), round(211 + 35 * pulse), 255)
        label = "PRESS START"
        crt.draw_text(label, (480 - crt.font_lg.size(label)[0]) / 2, 201,
                      color=color, size="lg", has_shadow=True)
        controls = "ENTER / A / START / CLICK"
        crt.draw_text(controls, (480 - crt.font_sm.size(controls)[0]) / 2, 230,
                      color=(136, 163, 185), size="sm")
        footer = self.status or "F2: SETTINGS"
        crt.draw_text(footer, (480 - crt.font_sm.size(footer)[0]) / 2, 252,
                      color=config.COLOR_FIBO_GOLD if self.status else (97, 122, 149), size="sm")
