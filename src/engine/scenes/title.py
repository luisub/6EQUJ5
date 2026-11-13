"""
MODULE: video_game/engine/scenes/title.py
PURPOSE: Offer a clear start action and safe optional save recovery.
CALLED BY: GameStateMachine.
HOW TO MODIFY: Keep destructive replacement explicit and preserve save errors.
"""

import math

import pygame

from .. import config
from ..alien_journey import ledger
from ..ui.viewport import window_to_logical
from .base import BaseScene


class TitleBootScene(BaseScene):
    """1977 FASR boot screen and save-slot controls."""

    PRIMARY = pygame.Rect(56, 105, 178, 28)
    NEW_GAME = pygame.Rect(246, 105, 178, 28)
    OPTIONS = pygame.Rect(56, 146, 178, 24)
    LOWER_LEFT = pygame.Rect(56, 178, 178, 26)
    LOWER_RIGHT = pygame.Rect(246, 178, 178, 26)
    DETAILS = pygame.Rect(246, 146, 178, 24)

    def __init__(self, machine):
        super().__init__(machine)
        self.elapsed_seconds = 0.0
        self.stars = [((i * 73) % config.INTERNAL_WIDTH, (i * 41) % 190, (i % 3) + 1) for i in range(55)]
        self.confirm_new = False
        self.show_options = False
        self.show_details = False
        self.focus = 0
        self.status = ""
        self._activation_guard = None
        self.journey_complete = False

    def on_enter(self, **kwargs):
        self.confirm_new = False
        self.show_options = False
        self.show_details = False
        self.focus = 0
        self.status = ""
        self._activation_guard = None
        self.journey_complete = ledger(self.machine.campaign).get('stage') == 'complete'

    def _new_game(self):
        if self.machine.save_store.has_existing_data():
            self.confirm_new = True
            self.focus = 0  # Cancel must be the default, including controller A.
            self.status = "REPLACE EXISTING SAVE?"
            return
        success, message = self.machine.start_new_game(show_opening=True, opening_guard=self._activation_guard)
        if not success:
            self.status = "SAVE FAILED. TRY AGAIN."
            self.machine.save_notice = message

    def _replace_game(self):
        self.confirm_new = False
        success, message = self.machine.start_new_game(replace_existing=True, show_opening=True,
                                                       opening_guard=self._activation_guard)
        if not success:
            self.status = "SAVE FAILED. TRY AGAIN."
            self.machine.save_notice = message

    def _cancel_replace(self):
        self.confirm_new = False
        self.show_options = False
        self.focus = 0
        self.status = "NEW GAME CANCELLED"

    def _continue(self, recover=False):
        result = self.machine.continue_game(recover=recover)
        if result.status == "ok":
            return
        messages = {
            "missing": "NO SAVE FOUND. OPEN SAVE OPTIONS.",
            "corrupt": "DAMAGED SAVE. TRY RESTORE BACKUP.",
            "future_version": "NEWER SAVE. TRY RESTORE BACKUP.",
            "old_version": "SAVE VERSION UNSUPPORTED. TRY BACKUP.",
            "migration_failed": "SAVE MIGRATION FAILED. TRY BACKUP.",
            "io_error": "SAVE UNAVAILABLE. TRY AGAIN OR BACKUP.",
        }
        self.status = messages.get(result.status, "LOAD FAILED. TRY AGAIN OR BACKUP.")
        if recover:
            backup_messages = {
                "missing": "NO BACKUP FOUND.",
                "corrupt": "BACKUP DAMAGED. TRY AGAIN.",
                "future_version": "BACKUP IS FROM A NEWER VERSION.",
                "old_version": "BACKUP VERSION UNSUPPORTED.",
                "migration_failed": "BACKUP MIGRATION FAILED.",
                "io_error": "BACKUP UNAVAILABLE. TRY AGAIN.",
            }
            self.status = backup_messages.get(result.status, "BACKUP FAILED. TRY AGAIN.")
        self.show_options = True
        self.focus = 0
        self.machine.save_notice = result.message

    def _buttons(self):
        if self.show_details:
            return [("BACK", self.DETAILS, self._toggle_details)]
        if self.confirm_new:
            return [("CANCEL", self.LOWER_LEFT, self._cancel_replace),
                    ("REPLACE SAVE", self.LOWER_RIGHT, self._replace_game)]
        primary = "CONTINUE" if self.machine.save_store.has_existing_data() else "START"
        buttons = [(primary, self.PRIMARY, self._primary)]
        if self.machine.save_store.has_existing_data():
            buttons.append(("NEW GAME", self.NEW_GAME, self._new_game))
        buttons.append(("CLOSE OPTIONS" if self.show_options else "SAVE OPTIONS", self.OPTIONS, self._toggle_options))
        if self.show_options:
            buttons.append(("RESTORE BACKUP", self.LOWER_LEFT, lambda: self._continue(recover=True)))
        buttons.append(("DETAILS", self.DETAILS, self._toggle_details))
        return buttons

    def _toggle_details(self):
        self.show_details = not self.show_details
        self.focus = 0

    def _primary(self):
        if self.machine.save_store.has_existing_data():
            self._continue()
        else:
            self._new_game()

    def _toggle_options(self):
        self.show_options = not self.show_options
        self.focus = next(i for i, (_, rect, _) in enumerate(self._buttons()) if rect == self.OPTIONS)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if getattr(event, 'controller_semantic', False) and hasattr(event, 'controller_button'):
                self._activation_guard = ('controller', getattr(event, 'controller_instance', None), event.controller_button)
            else:
                self._activation_guard = ('key', event.key)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self._activation_guard = ('mouse', event.button)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            position = window_to_logical(event.pos, self.machine.crt)
            if position is not None:
                for index, (_, rect, action) in enumerate(self._buttons()):
                    if rect.collidepoint(position):
                        self.focus = index
                        action()
                        return
            return
        if event.type != pygame.KEYDOWN or getattr(event, 'repeat', False):
            return
        if self.show_details:
            if event.key == pygame.K_ESCAPE:
                self._toggle_details()
                return
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self._toggle_details()
            return
        if self.confirm_new:
            if event.key == pygame.K_y:
                self._replace_game()
                return
            if event.key in (pygame.K_ESCAPE, pygame.K_n):
                self._cancel_replace()
                return
        else:
            if event.key == pygame.K_n:
                self._new_game()
                return
            if event.key == pygame.K_c:
                self._continue()
                return
            if event.key == pygame.K_r:
                self._continue(recover=True)
                return
            if event.key == pygame.K_ESCAPE and self.show_options:
                self.show_options = False
                self.focus = 0
                return
        buttons = self._buttons()
        if event.key in (pygame.K_DOWN, pygame.K_RIGHT, pygame.K_TAB):
            self.focus = (self.focus + 1) % len(buttons)
        elif event.key in (pygame.K_UP, pygame.K_LEFT):
            self.focus = (self.focus - 1) % len(buttons)
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            buttons[self.focus][2]()

    def update(self, dt_seconds):
        self.elapsed_seconds += dt_seconds

    def render(self, crt):
        crt.clear(config.COLOR_VOID_BLACK)
        pulse = 0.5 + 0.5 * math.sin(self.elapsed_seconds * 4.2)
        for star_x, star_y, star_size in self.stars:
            value = int(110 + 145 * pulse) if star_size > 1 else 90
            color = (value // 2, value, value // 2) if star_size == 3 else (value, value, value)
            pygame.draw.rect(crt.canvas, color, (star_x, star_y, star_size, star_size))
        crt.draw_panel((40, 24, 400, 216), bg_color=(7, 17, 25), border_color=(65, 101, 115))
        crt.draw_text("6 E Q U J 5", 56, 39, color=(112, 223, 229), size="lg")
        crt.draw_text("THE FERMI OVERRIDE", 56, 68, color=(180, 198, 205), size="sm")
        if self.show_details:
            crt.draw_text("Follow a signal that Earth heard only once.", 56, 96, color=config.COLOR_PAPER_WHITE, size='md')
            crt.draw_text("Cross eleven worlds. Bring their messages home.", 56, 117, color=(180, 198, 205), size='sm')
        elif self.confirm_new:
            crt.draw_text("Start again from the observatory?", 56, 101, color=config.COLOR_PAPER_WHITE, size='md')
            crt.draw_text("This replaces your current journey's progress.", 56, 125, color=(180, 198, 205), size='sm')
            crt.draw_text("Choose Cancel to keep playing your saved game.", 56, 143, color=(180, 198, 205), size='sm')
        elif not self.show_options:
            hint = ('Journey complete. Eleven messages brought home.' if self.journey_complete else
                    'Continue your journey, or start again with New Game.'
                    if self.machine.save_store.has_existing_data() else 'Your journey begins at the Big Ear observatory.')
            crt.draw_text(hint, 56, 186, color=(180, 198, 205), size='sm')
        for index, (label, rect, _) in enumerate(self._buttons()):
            selected = index == self.focus
            pygame.draw.rect(crt.canvas, (38, 49, 51) if selected else (13, 27, 37), rect, border_radius=3)
            pygame.draw.rect(crt.canvas, config.COLOR_FIBO_GOLD if selected else (65, 101, 115), rect, 1, border_radius=3)
            crt.draw_text(label, rect.x + 10, rect.y + (rect.height - 10) // 2,
                          color=config.COLOR_FIBO_GOLD if selected else (180, 198, 205), size="sm")
        if self.status and not self.show_details and not self.confirm_new:
            crt.draw_text(self.status, 56, 218, color=config.COLOR_FIBO_GOLD, size="sm")
        else:
            crt.draw_text('ARROWS: CHOOSE    ENTER / A: SELECT', 56, 218, color=(156, 180, 188), size='sm')
        self.machine.render_global_hud(crt, location_label="BOOT // 1420.4056 MHz",
                                       footer_text="[ARROWS] CHOOSE  [ENTER] SELECT  [ESC] BACK")
