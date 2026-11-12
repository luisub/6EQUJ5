"""
MODULE: video_game/engine/ui/pause.py
PURPOSE: Present paused-game settings, checkpoint save and resume controls.
CALLED BY: The game state machine while the pause overlay owns focus.
HOW TO MODIFY: Route all overlay input here and update settings through the
  machine so persistence and display/audio effects remain coordinated.
"""

import pygame

from .. import config
from ..settings import MAX_SCALE


class PauseOverlay:
    """Pause menu with keyboard selection and immediate settings feedback."""

    def __init__(self, machine):
        self.machine = machine
        self.active = False
        self.selected = 0
        self.message = ""
        self.shade = pygame.Surface((config.INTERNAL_WIDTH, config.INTERNAL_HEIGHT), pygame.SRCALPHA)
        self.shade.fill((0, 0, 0, 170))

    def open(self):
        self.active = True
        self.selected = 0
        self.message = self.machine.settings_store.warning

    def close(self):
        self.active = False
        self.machine.input.release_all()
        if self.machine.current_state_name == config.STATE_CRT_TERMINAL:
            pygame.key.start_text_input()

    def handle_event(self, event):
        key = None
        if event.type == pygame.KEYDOWN:
            key = event.key
        elif event.type == pygame.CONTROLLERBUTTONDOWN:
            key = {pygame.CONTROLLER_BUTTON_START: pygame.K_F2,
                   pygame.CONTROLLER_BUTTON_B: pygame.K_ESCAPE,
                   pygame.CONTROLLER_BUTTON_A: pygame.K_RETURN,
                   pygame.CONTROLLER_BUTTON_DPAD_UP: pygame.K_UP,
                   pygame.CONTROLLER_BUTTON_DPAD_DOWN: pygame.K_DOWN,
                   pygame.CONTROLLER_BUTTON_DPAD_LEFT: pygame.K_LEFT,
                   pygame.CONTROLLER_BUTTON_DPAD_RIGHT: pygame.K_RIGHT}.get(event.button)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            x = event.pos[0] * config.INTERNAL_WIDTH / self.machine.crt.win_w
            y = event.pos[1] * config.INTERNAL_HEIGHT / self.machine.crt.win_h
            if 108 <= x < 375 and 48 <= y < 168:
                self.selected = int((y - 48) // 20)
                key = pygame.K_RETURN
        if key is None:
            return
        if key in (pygame.K_ESCAPE, pygame.K_F2):
            self.close()
        elif key in (pygame.K_UP, pygame.K_w):
            self.selected = (self.selected - 1) % 6
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.selected = (self.selected + 1) % 6
        elif key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_RETURN, pygame.K_SPACE):
            direction = -1 if key == pygame.K_LEFT else 1
            settings = self.machine.settings
            if self.selected == 0:
                if key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.close()
            elif self.selected == 1:
                self.machine.change_settings(volume=max(0, min(100, settings.volume + 10 * direction)))
            elif self.selected == 2:
                self.machine.change_settings(crt_effects=not settings.crt_effects)
            elif self.selected == 3:
                self.machine.change_settings(scale=max(1, min(MAX_SCALE, settings.scale + direction)))
            elif self.selected == 4:
                mode = 'classic' if settings.combat_mode == 'assisted' else 'assisted'
                self.machine.change_settings(combat_mode=mode)
            elif self.selected == 5 and key in (pygame.K_RETURN, pygame.K_SPACE):
                self.message = "CHECKPOINT SAVED" if self.machine.save_checkpoint() else "SAVE UNAVAILABLE - RETRY"

    def render(self, crt):
        crt.canvas.blit(self.shade, (0, 0))
        crt.draw_panel((94, 27, 292, 212), bg_color=(4, 16, 11), border_color=config.COLOR_CRT_GREEN,
                       title="PAUSED // SETTINGS")
        settings = self.machine.settings
        rows = (
            "RESUME",
            f"VOLUME: {settings.volume}%",
            f"CRT EFFECTS: {'ON' if settings.crt_effects else 'OFF'}",
            f"WINDOW SCALE: {settings.scale}X",
            f"COMBAT: {settings.combat_mode.upper()}",
            "SAVE CHECKPOINT",
        )
        for index, label in enumerate(rows):
            prefix = "> " if index == self.selected else "  "
            color = config.COLOR_FIBO_GOLD if index == self.selected else config.COLOR_CRT_GREEN
            crt.draw_text(prefix + label, 112, 50 + index * 20, color=color, size="md")
        crt.draw_text("MOUSE L/R: FIRE/CHARGE  PAD RT/LT", 108, 168, color=config.COLOR_CORE_STEEL)
        crt.draw_text("UP/DOWN SELECT  LEFT/RIGHT CHANGE", 108, 183, color=config.COLOR_CORE_STEEL)
        crt.draw_text("ENTER/A CONFIRM  ESC/F2/START RESUME", 108, 197, color=config.COLOR_CORE_STEEL)
        message = self.message or self.machine.settings_notice
        if message:
            crt.draw_text(message[:43], 108, 217, color=config.COLOR_AMBER_1977)
