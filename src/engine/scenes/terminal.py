"""MODULE: video_game/engine/scenes/terminal.py
PURPOSE: Present authored receiver messages and validate signal evidence without typing.
CALLED BY: GameStateMachine and the bunker receiver station.
HOW TO MODIFY: Keep evidence on the validated campaign path and preserve save feedback.
"""
import pygame

from .. import config
from ..contact_session import ContactSession
from ..ui.text import ellipsize_pixels, wrap_text_pixels
from ..ui.viewport import window_to_logical
from .base import BaseScene
from .bunker import MILESTONE_CIVS


class CRTTerminalScene(BaseScene):
    """Button-driven archive receiver; the normal game does not construct an AI worker."""

    PRIMARY_RECT = pygame.Rect(177, 194, 174, 24)
    BACK_RECT = pygame.Rect(356, 194, 101, 24)
    TARGET_RECT = pygame.Rect(18, 211, 138, 22)
    LINES_PER_PAGE = 8

    def __init__(self, machine):
        super().__init__(machine)
        if not getattr(machine, "contact_session", None):
            machine.contact_session = ContactSession(campaign=getattr(machine, "campaign", None))
        self.session = machine.contact_session
        self.stage = "greeting"
        self.page_index = 0
        self.body = ""
        self.notice = ""
        self._show_greeting()

    @property
    def text_buffer(self):
        """The authored receiver has no editable transmission buffer."""
        return ""

    def _catalog(self):
        return self.session.offline_data.get("civilizations", {}).get(self.session.active_civ_id, {})

    def _show_greeting(self):
        self.stage = "greeting"
        self.page_index = 0
        self.body = self._catalog().get("initial_greeting", "This signal archive is unavailable.")
        if self.session.active_civ_id == "FASR-001":
            self.body = self.body.removesuffix(" Speak, Operator.")
        self.notice = ""

    def on_enter(self, **kwargs):
        pygame.key.stop_text_input()
        self.session.campaign = self.machine.campaign
        hub = self.machine.scenes.get(config.STATE_BUNKER_HUB)
        if hub and hub.active_civ != self.session.active_civ_id:
            self.session.switch_target(hub.active_civ)
        self._show_greeting()

    def on_exit(self):
        pygame.key.stop_text_input()

    def _pages(self):
        lines = wrap_text_pixels(self.body, self.machine.crt.font_sm, 278) or [""]
        return [lines[i:i + self.LINES_PER_PAGE] for i in range(0, len(lines), self.LINES_PER_PAGE)]

    def _cycle_target(self):
        hub = self.machine.scenes.get(config.STATE_BUNKER_HUB)
        if hub:
            hub.civ_idx = (hub.civ_idx + 1) % len(MILESTONE_CIVS)
            target = hub.active_civ
        else:
            target = MILESTONE_CIVS[(MILESTONE_CIVS.index(self.session.active_civ_id) + 1) % len(MILESTONE_CIVS)]
        self.session.switch_target(target)
        self._show_greeting()

    def _primary_label(self):
        if self.page_index + 1 < len(self._pages()):
            return "NEXT"
        if self.stage == "received":
            return "RETURN TO BASE"
        if self.stage == "save_failed":
            return "RETRY SAVE"
        return "RECEIVE SIGNAL"

    def _primary(self):
        if self.page_index + 1 < len(self._pages()):
            self.page_index += 1
            return
        if self.stage == "received":
            self.machine.change_state(config.STATE_BUNKER_HUB)
            return
        if self.stage == "save_failed":
            if self.machine.save_checkpoint():
                self.stage = "received"
                self.notice = "SIGNAL SAVED"
            else:
                self.notice = "SAVE FAILED // RETRY"
            return
        try:
            success, message = self.session.receive_authored_evidence()
        except (ValueError, KeyError, TypeError):
            success, message = False, "SIGNAL ARCHIVE UNAVAILABLE"
        if not success:
            self.notice = message
            return
        self.body = message
        self.page_index = 0
        if self.machine.session_active and not self.machine.save_checkpoint():
            self.stage = "save_failed"
            self.notice = "SIGNAL RECEIVED // SAVE FAILED"
        else:
            self.stage = "received"
            self.notice = "SIGNAL RECEIVED"
        if getattr(self.machine, "audio", None):
            self.machine.audio.play_sfx("printer_chatter")

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            point = window_to_logical(event.pos, self.machine.crt)
            if point is None:
                return
            if self.PRIMARY_RECT.collidepoint(point):
                self._primary()
            elif self.BACK_RECT.collidepoint(point):
                self.machine.change_state(config.STATE_BUNKER_HUB)
            elif self.TARGET_RECT.collidepoint(point):
                self._cycle_target()
            return
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self._primary()
        elif event.key == pygame.K_ESCAPE:
            self.machine.change_state(config.STATE_BUNKER_HUB)
        elif event.key == pygame.K_TAB:
            self._cycle_target()

    def update(self, dt_seconds):
        self.session.update(dt_seconds)

    def render(self, crt):
        crt.clear((4, 10, 8))
        civ_id = self.session.active_civ_id
        crt.draw_panel((12, 20, 150, 224), bg_color=(6, 14, 12), border_color=config.COLOR_CRT_GREEN)
        for suffix in ("env", "face"):
            image = self.machine.assets.civilization(civ_id, suffix)
            if image:
                crt.canvas.blit(image, (23, 36))
        pygame.draw.rect(crt.canvas, (18, 58, 37), self.TARGET_RECT, border_radius=2)
        pygame.draw.rect(crt.canvas, config.COLOR_CRT_GREEN, self.TARGET_RECT, width=1, border_radius=2)
        crt.draw_panel((168, 20, 300, 224), bg_color=(6, 14, 12), border_color=config.COLOR_CRT_GREEN,
                       title="SIGNAL ARCHIVE")
        pygame.draw.rect(crt.canvas, (34, 91, 52), self.PRIMARY_RECT, border_radius=2)
        pygame.draw.rect(crt.canvas, config.COLOR_CRT_GREEN, self.PRIMARY_RECT, width=1, border_radius=2)
        pygame.draw.rect(crt.canvas, (19, 40, 29), self.BACK_RECT, border_radius=2)
        pygame.draw.rect(crt.canvas, config.COLOR_CRT_DIM, self.BACK_RECT, width=1, border_radius=2)
        pages = self._pages()
        self.page_index = min(self.page_index, len(pages) - 1)
        with crt.text_batch():
            crt.draw_text(ellipsize_pixels(civ_id, crt.font_sm, 130), 20, 173, color=config.COLOR_FIBO_GOLD)
            crt.draw_text(f"{self.session.target_mhz:.4f} MHz", 20, 188, color=config.COLOR_CRT_GREEN)
            crt.draw_text("OTHER SIGNAL [TAB]", 23, 217, color=config.COLOR_CRT_GREEN)
            crt.draw_text("INCOMING TRANSMISSION", 178, 42, color=config.COLOR_FIBO_GOLD)
            for index, line in enumerate(pages[self.page_index]):
                crt.draw_text(line, 178, 62 + index * 13, color=config.COLOR_CRT_GREEN)
            if len(pages) > 1:
                crt.draw_text(f"PAGE {self.page_index + 1}/{len(pages)}", 178, 169, color=config.COLOR_CORE_STEEL)
            if self.notice:
                crt.draw_text(ellipsize_pixels(self.notice, crt.font_sm, 280), 178, 181, color=config.COLOR_AMBER_1977)
            crt.draw_text(ellipsize_pixels(self._primary_label(), crt.font_sm, 164), 185, 201, color=config.COLOR_CRT_GREEN)
            crt.draw_text("BACK", 380, 201, color=config.COLOR_CRT_GREEN)
        self.machine.render_global_hud(crt, location_label=f"CRT RECEIVER // {civ_id}",
                                       footer_text="[ENTER/A] CONTINUE   [TAB] OTHER SIGNAL   [ESC/B] BACK")
