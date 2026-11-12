"""
MODULE: video_game/engine/scenes/terminal.py
PURPOSE: Interactive dual-monitor CRT receiver interface providing 1400-1440 MHz frequency tuning,
         codec-backed 6EQUJ5 intensity telemetry, and scrollable alien dialogue.
CALLED BY: GameStateMachine in video_game/engine/state_machine.py.
HOW TO MODIFY:
  - To adjust receiver panel dimensions or layout -> edit render().
  - To adjust text input handling -> edit handle_event().
"""

import pygame
from .. import config
from .base import BaseScene
from .bunker import MILESTONE_CIVS
from ..contact_session import ContactSession
from ..ui.text import TextInputBuffer, TranscriptScroller, wrap_text_chars


class CRTTerminalScene(BaseScene):
    """Dual-Monitor 1420.4056 MHz Receiver displaying layered portrait, 6EQUJ5 telemetry and dialogue."""

    def __init__(self, machine):
        super().__init__(machine)
        # Shared or persistent session across re-entries
        campaign = getattr(self.machine, "campaign", None)
        if not hasattr(self.machine, "contact_session") or self.machine.contact_session is None:
            self.machine.contact_session = ContactSession(campaign=campaign)
        self.session: ContactSession = self.machine.contact_session
        if self.session.campaign is None and campaign is not None:
            self.session.campaign = campaign

        self.input_buffer = TextInputBuffer(max_length=128)
        self.scroller = TranscriptScroller(visible_lines=9)
        self.cursor_blink_timer = 0.0
        self.last_transcript_len = 0
        self._sync_transcript()

    @property
    def text_buffer(self) -> str:
        """Expose current input buffer text for tests and UI inspections."""
        return self.input_buffer.text

    @text_buffer.setter
    def text_buffer(self, val: str):
        self.input_buffer.set_text(val)

    def on_enter(self, **kwargs):
        pygame.key.start_text_input()
        if hasattr(self.machine, "campaign") and self.machine.campaign is not None:
            self.session.campaign = self.machine.campaign
        # Sync active civilization with hub
        hub = self.machine.scenes.get(config.STATE_BUNKER_HUB)
        if hub and hub.active_civ != self.session.active_civ_id:
            self.session.switch_target(hub.active_civ)
        self._sync_transcript()

    def on_exit(self):
        pygame.key.stop_text_input()

    def _sync_transcript(self):
        """Rebuild scroller lines from session transcript entries."""
        self.scroller.clear()
        for role_prefix, text_color in [("user", config.COLOR_FIBO_GOLD), ("assistant", config.COLOR_CRT_GREEN)]:
            pass

        for entry in self.session.transcripts.get(self.session.active_civ_id, []):
            role = entry["role"]
            text = entry["text"]
            if role == "user":
                header = "> OPERATOR:"
                color = config.COLOR_FIBO_GOLD
            else:
                header = f"[{self.session.active_civ_id}]:"
                color = config.COLOR_CRT_GREEN

            wrapped = wrap_text_chars(f"{header} {text}", max_chars=38)
            for line in wrapped:
                self.scroller.add_line(line, color=color)

        if self.session.is_streaming and self.session.current_incoming_tokens:
            partial = "".join(self.session.current_incoming_tokens)
            wrapped = wrap_text_chars(f"[{self.session.active_civ_id}]: {partial}", max_chars=38)
            for line in wrapped:
                self.scroller.add_line(line, color=config.COLOR_CRT_DIM)

    def handle_event(self, event):
        if event.type == pygame.TEXTINPUT:
            self.input_buffer.insert(event.text)
            return

        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            self.machine.change_state(config.STATE_BUNKER_HUB)

        elif event.key == pygame.K_RETURN:
            text = self.input_buffer.text.strip()
            if text:
                if self.session.send_message(text):
                    if hasattr(self.machine, "audio") and self.machine.audio:
                        self.machine.audio.play_sfx("printer_chatter")
                    self.input_buffer.clear()
                    self._sync_transcript()
                    self.scroller.scroll_to_bottom()

        elif event.key == pygame.K_BACKSPACE:
            self.input_buffer.backspace()

        elif event.key == pygame.K_DELETE:
            self.input_buffer.delete()

        elif event.key == pygame.K_LEFT:
            self.input_buffer.move_left()

        elif event.key == pygame.K_RIGHT:
            self.input_buffer.move_right()

        elif event.key == pygame.K_UP:
            self.scroller.scroll_up(1)

        elif event.key == pygame.K_DOWN:
            self.scroller.scroll_down(1)

        elif event.key == pygame.K_PAGEUP:
            self.scroller.scroll_up(5)

        elif event.key == pygame.K_PAGEDOWN:
            self.scroller.scroll_down(5)

        elif event.key == pygame.K_TAB:
            # Switch target civilization
            hub = self.machine.scenes[config.STATE_BUNKER_HUB]
            hub.civ_idx = (hub.civ_idx + 1) % len(MILESTONE_CIVS)
            self.session.switch_target(hub.active_civ)
            self._sync_transcript()
            self.scroller.scroll_to_bottom()

        elif event.key == pygame.K_c and self.session.is_streaming:
            self.session.cancel_transmission()
            self._sync_transcript()

        elif event.key == pygame.K_LEFTBRACKET:
            self.session.tune_frequency(-0.0500)

        elif event.key == pygame.K_RIGHTBRACKET:
            self.session.tune_frequency(+0.0500)

    def update(self, dt_seconds):
        self.cursor_blink_timer += dt_seconds
        prev_streaming = self.session.is_streaming
        prev_token_len = len(self.session.current_incoming_tokens)

        self.session.update(dt_seconds)

        # Update scroller if new tokens arrived or stream completed
        if self.session.is_streaming or prev_streaming != self.session.is_streaming or prev_token_len != len(self.session.current_incoming_tokens):
            self._sync_transcript()

    def render(self, crt):
        crt.clear((4, 10, 8))
        civ_id = self.session.active_civ_id
        hub = self.machine.scenes.get(config.STATE_BUNKER_HUB)
        civ_idx = hub.civ_idx if hub else 0

        # ═══════════════════════════════════════════════════════
        # LEFT CRT: PORTRAIT & CARRIER TUNING
        # ═══════════════════════════════════════════════════════
        crt.draw_panel((12, 20, 150, 224), bg_color=(6, 14, 12), border_color=config.COLOR_CRT_GREEN,
                       title=f"LEFT CRT // {civ_id}")

        # Layered 128x128 plate
        for suf in ("env", "face"):
            surf = self.machine.assets.civilization(civ_id, suf)
            if surf:
                crt.canvas.blit(surf, (23, 36))

        # Carrier tuning metadata
        y_info = 170
        freq_color = config.COLOR_CRT_GREEN if self.session.is_locked else config.COLOR_AMBER_1977
        crt.draw_text(f"CARRIER: {self.session.target_mhz:.4f} MHz", 20, y_info, color=freq_color, size="sm")
        crt.draw_text(f"TUNER:   {self.session.tuner_mhz:.4f} MHz", 20, y_info + 12, color=config.COLOR_CORE_STEEL, size="sm")

        # Lock indicator & signal meter
        lock_label = "● CARRIER LOCKED" if self.session.is_locked else "○ SEARCHING..."
        crt.draw_text(lock_label, 20, y_info + 24, color=freq_color, size="sm")

        # Tuning meter bar
        bar_w = int(self.session.signal_strength * 130)
        pygame.draw.rect(crt.canvas, (12, 32, 22), (22, y_info + 38, 130, 4))
        pygame.draw.rect(crt.canvas, freq_color, (22, y_info + 38, bar_w, 4))

        # Target index indicator
        crt.draw_text(f"[TAB] TARGET {civ_idx + 1}/11", 20, y_info + 46, color=config.COLOR_FIBO_GOLD, size="sm")

        # ═══════════════════════════════════════════════════════
        # RIGHT CRT: 6EQUJ5 TELEMETRY & SCROLLABLE DIALOGUE
        # ═══════════════════════════════════════════════════════
        mode_badge = "OFFLINE ARCHIVE" if self.session.is_offline else "LIVE OLLAMA"
        crt.draw_panel((168, 20, 300, 224), bg_color=(6, 14, 12), border_color=config.COLOR_CRT_GREEN,
                       title=f"RIGHT CRT // [{mode_badge}] DIALOGUE")

        # 1. 6EQUJ5 Intensity Histogram Header
        hist_x, hist_y = 178, 36
        bins = self.session.decode_bins  # [6, 14, 26, 30, 19, 5]
        bin_chars = ["6", "E", "Q", "U", "J", "5"]

        for idx, (b_val, b_ch) in enumerate(zip(bins, bin_chars)):
            bx = hist_x + idx * 16
            bar_h = int((b_val / 35.0) * 16)
            b_col = config.COLOR_EHMAN_RED if b_ch == "U" else config.COLOR_CRT_GREEN
            # Background slot
            pygame.draw.rect(crt.canvas, (10, 26, 18), (bx, hist_y + 16 - 16, 12, 16))
            # Active bar
            pygame.draw.rect(crt.canvas, b_col, (bx, hist_y + 16 - bar_h, 12, bar_h))
            crt.draw_text(b_ch, bx + 2, hist_y + 18, color=b_col, size="sm", has_shadow=False)

        # Distinguish 72-second transit duration and 30-sigma peak intensity (Corrects I10)
        crt.draw_text("6EQUJ5 INTENSITY (PEAK: 30σ // DURATION: 72s)", 280, hist_y - 1, color=config.COLOR_FIBO_GOLD, size="sm")
        mode_color = config.COLOR_AMBER_1977 if self.session.is_offline else config.COLOR_CRT_GREEN
        mode_text = "MODE: OFFLINE (CANONICAL)" if self.session.is_offline else "MODE: ONLINE (LIVE MODEL)"
        crt.draw_text(mode_text, 280, hist_y + 11, color=mode_color, size="sm")
        crt.draw_text(f"EXCHANGES: {self.session.exchange_count}/{self.session.max_exchanges}", 280, hist_y + 23, color=config.COLOR_AMBER_1977, size="sm")

        # Separator line
        pygame.draw.line(crt.canvas, (16, 52, 34), (174, 70), (462, 70), width=1)

        # 2. Scrollable Transcript Area
        t_y = 74
        visible_lines = self.scroller.get_visible_lines()
        for l_idx, (line_text, line_col) in enumerate(visible_lines):
            crt.draw_text(line_text, 178, t_y + l_idx * 11, color=line_col, size="sm")

        # Scroll indicator
        if len(self.scroller.lines) > self.scroller.visible_lines:
            pct = self.scroller.scroll_offset / float(max(1, len(self.scroller.lines) - self.scroller.visible_lines))
            s_top = 74 + int(pct * 80)
            pygame.draw.line(crt.canvas, (16, 52, 34), (463, 74), (463, 174), width=2)
            pygame.draw.circle(crt.canvas, config.COLOR_CRT_GREEN, (463, s_top), 2)

        # Separator above input
        pygame.draw.line(crt.canvas, (16, 52, 34), (174, 182), (462, 182), width=1)

        # 3. Interactive Text Input Prompt
        slice_text, cursor_offset = self.input_buffer.get_visible_slice(max_chars=36)
        show_cursor = (int(self.cursor_blink_timer * 2.5) % 2 == 0) and not self.session.is_streaming
        cursor_char = "▌" if show_cursor else " "

        prompt_str = f"TX> {slice_text}"
        crt.draw_text(prompt_str, 178, 188, color=config.COLOR_FIBO_GOLD, size="sm")
        if show_cursor:
            cursor_x = 178 + (4 + cursor_offset) * 7
            crt.draw_text(cursor_char, cursor_x, 188, color=config.COLOR_FIBO_GOLD, size="sm", has_shadow=False)

        # Status text feedback line
        status_color = config.COLOR_EHMAN_RED if "ERR" in self.session.status_text or "ABORT" in self.session.status_text else config.COLOR_CORE_STEEL
        crt.draw_text(self.session.status_text, 178, 202, color=status_color, size="sm")

        # Global Bottom HUD Footer
        footer = "[ENTER] SEND  [1-3] CHANNELS  [UP/DN] SCROLL  [/RECONNECT] SYNC  [TAB] NEXT  [ESC] EXIT"
        self.machine.render_global_hud(crt, location_label=f"CRT RECEIVER // {civ_id} // 1420.4056 MHz", footer_text=footer)
