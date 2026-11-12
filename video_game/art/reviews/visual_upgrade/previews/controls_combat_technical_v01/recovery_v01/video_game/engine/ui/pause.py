"""
MODULE: video_game/engine/ui/pause.py
PURPOSE: Present paused-game settings, checkpoint save and resume controls.
CALLED BY: The game state machine while the pause overlay owns focus.
HOW TO MODIFY: Route all overlay input here and update settings through the
  machine so persistence and display/audio effects remain coordinated.
"""

import pygame

from .. import config


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
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_ESCAPE, pygame.K_F2):
            self.close()
        elif event.key in (pygame.K_UP, pygame.K_w):
            self.selected = (self.selected - 1) % 5
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.selected = (self.selected + 1) % 5
        elif event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_RETURN, pygame.K_SPACE):
            direction = -1 if event.key == pygame.K_LEFT else 1
            settings = self.machine.settings
            if self.selected == 0:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.close()
            elif self.selected == 1:
                self.machine.change_settings(volume=max(0, min(100, settings.volume + 10 * direction)))
            elif self.selected == 2:
                self.machine.change_settings(crt_effects=not settings.crt_effects)
            elif self.selected == 3:
                self.machine.change_settings(scale=max(1, min(4, settings.scale + direction)))
            elif self.selected == 4 and event.key in (pygame.K_RETURN, pygame.K_SPACE):
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
            "SAVE CHECKPOINT",
        )
        for index, label in enumerate(rows):
            prefix = "> " if index == self.selected else "  "
            color = config.COLOR_FIBO_GOLD if index == self.selected else config.COLOR_CRT_GREEN
            crt.draw_text(prefix + label, 112, 50 + index * 24, color=color, size="md")
        crt.draw_text("UP/DOWN SELECT  LEFT/RIGHT CHANGE", 108, 183, color=config.COLOR_CORE_STEEL)
        crt.draw_text("ENTER CONFIRM  ESC / F2 RESUME", 108, 197, color=config.COLOR_CORE_STEEL)
        message = self.message or self.machine.settings_notice
        if message:
            crt.draw_text(message[:43], 108, 217, color=config.COLOR_AMBER_1977)
