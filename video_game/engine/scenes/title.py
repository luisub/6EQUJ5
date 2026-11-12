"""
MODULE: video_game/engine/scenes/title.py
PURPOSE: Offer new game, continue, retry and explicit backup recovery.
CALLED BY: GameStateMachine.
HOW TO MODIFY: Keep destructive replacement explicit and show actionable save
  status without changing files merely by opening the title screen.
"""

import math

import pygame

from .. import config
from .base import BaseScene


class TitleBootScene(BaseScene):
    """1977 FASR boot screen and save-slot controls."""

    def __init__(self, machine):
        super().__init__(machine)
        self.elapsed_seconds = 0.0
        self.stars = [((i * 73) % config.INTERNAL_WIDTH, (i * 41) % 190, (i % 3) + 1) for i in range(55)]
        self.confirm_new = False
        self.status = "SELECT A SAVE OPTION"

    def on_enter(self, **kwargs):
        self.confirm_new = False
        self.status = "SELECT A SAVE OPTION"

    def _new_game(self):
        if self.machine.save_store.has_existing_data():
            self.confirm_new = True
            self.status = "REPLACE SAVE?  Y: YES  ESC: CANCEL"
            return
        success, message = self.machine.start_new_game()
        if not success:
            self.status = "SAVE FAILED. N: RETRY"
            self.machine.save_notice = message

    def _continue(self, recover=False):
        result = self.machine.continue_game(recover=recover)
        if result.status == "ok":
            return
        messages = {
            "missing": "NO SAVE. N: NEW  R: BACKUP  C: RETRY",
            "corrupt": "DAMAGED SAVE. R: BACKUP  C: RETRY",
            "future_version": "NEWER SAVE. R: BACKUP  C: RETRY",
            "old_version": "UNSUPPORTED SAVE. R: BACKUP  C: RETRY",
            "migration_failed": "SAVE MIGRATION FAILED. R: BACKUP",
            "io_error": "SAVE UNAVAILABLE. C: RETRY  R: BACKUP",
        }
        self.status = messages.get(result.status, "LOAD FAILED. C: RETRY  R: BACKUP")
        if recover:
            backup_messages = {
                "missing": "NO BACKUP. N: NEW  C: RETRY",
                "corrupt": "BACKUP DAMAGED. N: NEW  C: RETRY",
                "future_version": "BACKUP TOO NEW. N: NEW  C: RETRY",
                "old_version": "BACKUP TOO OLD. N: NEW  C: RETRY",
                "migration_failed": "BACKUP MIGRATION FAILED. N: NEW",
                "io_error": "BACKUP UNAVAILABLE. R: RETRY",
            }
            self.status = backup_messages.get(result.status, "BACKUP FAILED. R: RETRY")
        self.machine.save_notice = result.message

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if self.confirm_new:
            if event.key == pygame.K_y:
                self.confirm_new = False
                success, message = self.machine.start_new_game(replace_existing=True)
                if not success:
                    self.status = "SAVE FAILED. N: RETRY"
                    self.machine.save_notice = message
            elif event.key in (pygame.K_ESCAPE, pygame.K_n):
                self.confirm_new = False
                self.status = "NEW GAME CANCELLED"
            return
        if event.key == pygame.K_n:
            self._new_game()
        elif event.key == pygame.K_c:
            self._continue()
        elif event.key == pygame.K_r:
            self._continue(recover=True)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.machine.save_store.has_existing_data():
                self._continue()
            else:
                self._new_game()

    def update(self, dt_seconds):
        self.elapsed_seconds += dt_seconds

    def render(self, crt):
        crt.clear(config.COLOR_VOID_BLACK)
        pulse = 0.5 + 0.5 * math.sin(self.elapsed_seconds * 4.2)
        for star_x, star_y, star_size in self.stars:
            value = int(110 + 145 * pulse) if star_size > 1 else 90
            color = (value // 2, value, value // 2) if star_size == 3 else (value, value, value)
            pygame.draw.rect(crt.canvas, color, (star_x, star_y, star_size, star_size))
        crt.draw_panel((40, 18, 400, 190), bg_color=(5, 14, 9), border_color=config.COLOR_CRT_GREEN,
                       title="FASR DIRECTIVE 1420-A // LEVEL 7 CLASSIFIED")
        crt.draw_text("6 E Q U J 5 : T H E   F E R M I   O V E R R I D E", 56, 38, color=config.COLOR_CRT_GREEN, size="md")
        crt.draw_text("YEAR 2029 // THE CORE CONTROLS DIGITAL NETWORKS.", 56, 62, color=config.COLOR_CORE_STEEL)
        crt.draw_text("ONLY ANALOG HARDWARE & DEEP SPACE REMAIN UNTOUCHED.", 56, 76, color=config.COLOR_AMBER_1977)
        crt.draw_text("[N] NEW GAME   [C] CONTINUE   [R] RESTORE BACKUP", 56, 112, color=config.COLOR_CRT_GREEN)
        crt.draw_text(self.status, 56, 135, color=config.COLOR_FIBO_GOLD)
        if (int((self.elapsed_seconds + 1e-9) / 0.45)) % 2 == 0:
            crt.draw_text("[ENTER] START / CONTINUE", 56, 165, color=config.COLOR_CRT_GREEN)
        self.machine.render_global_hud(crt, location_label="BOOT // 1420.4056 MHz",
                                       footer_text="[N] NEW  [C] CONTINUE  [R] BACKUP  [ENTER] START")
