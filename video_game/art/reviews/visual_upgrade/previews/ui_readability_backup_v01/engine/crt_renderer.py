"""
═══════════════════════════════════════════════════════
MODULE: video_game/engine/crt_renderer.py
PURPOSE: Composites a 960x540 native frame from logical and native layers and applies CRT/VHS effects.
CALLED BY: main.py and state_machine.py.
HOW TO MODIFY:
  - To adjust scanline darkness -> edit _build_scanline_overlay().
  - To change VHS glitch slice height -> edit present().
  - To change pixel UI font sizes -> edit __init__().
═══════════════════════════════════════════════════════
"""

import random
import pygame
from . import config


class CRTRenderer:
    """Manage 480x270 logical staging, 960x540 output, and CRT effects."""

    def __init__(self, scale=config.DEFAULT_SCALE):
        """Initialize both render surfaces, scanline overlay, and fonts."""
        self.internal_w = config.INTERNAL_WIDTH
        self.internal_h = config.INTERNAL_HEIGHT
        # World/UI code uses logical pixels; the final frame has twice the density.
        self.logical_canvas = pygame.Surface((self.internal_w, self.internal_h), pygame.SRCALPHA).convert_alpha()
        self.canvas = self.logical_canvas  # compatibility for logical drawing callers
        self.render_surface = pygame.Surface((config.RENDER_WIDTH, config.RENDER_HEIGHT), pygame.SRCALPHA).convert_alpha()
        self._finalized = False
        self.set_scale(scale)
        pygame.font.init()
        self.font_sm = pygame.font.SysFont("couriernew", 9, bold=True)
        self.font_md = pygame.font.SysFont("couriernew", 11, bold=True)
        self.font_lg = pygame.font.SysFont("couriernew", 15, bold=True)
        self.glitch_timer_ms = 0
        self.glitch_intensity = 0
        self.is_crt_enabled = True

    def set_scale(self, scale):
        """Rebuild pixel-aligned CRT layers at an integer window scale."""
        self.scale = scale
        self.win_w = config.RENDER_WIDTH * scale
        self.win_h = config.RENDER_HEIGHT * scale
        self._scaled_canvas = pygame.Surface((self.win_w, self.win_h)).convert()
        self.scanline_overlay = self._build_scanline_overlay()

    def _build_scanline_overlay(self):
        """Create interlaced scanlines and subtle CRT bezel border."""
        overlay = pygame.Surface((self.win_w, self.win_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 0))
        logical_pixel = self.scale * config.RENDER_DENSITY
        for y_pos in range(0, self.win_h, logical_pixel):
            line_y = y_pos + logical_pixel - 1
            pygame.draw.line(overlay, (0, 0, 0, 72), (0, line_y), (self.win_w, line_y))
        pygame.draw.rect(overlay, (20, 65, 35, 160), (0, 0, self.win_w, self.win_h), width=4)
        return overlay

    def trigger_glitch(self, duration_ms=220, intensity=4):
        """Trigger a VHS tape-warp / Mandela glitch effect."""
        self.glitch_timer_ms = max(self.glitch_timer_ms, duration_ms)
        self.glitch_intensity = max(self.glitch_intensity, intensity)

    def update(self, dt_seconds):
        """Advance the legacy millisecond glitch timer using seconds from the loop."""
        if self.glitch_timer_ms > 0:
            self.glitch_timer_ms = max(0, self.glitch_timer_ms - dt_seconds * 1000.0)
            if self.glitch_timer_ms == 0:
                self.glitch_intensity = 0

    def clear(self, color=config.COLOR_VOID_BLACK):
        """Start a frame and discard all staging from the previous frame."""
        self.render_surface.fill((0, 0, 0, 0))
        self.logical_canvas.fill((*color[:3], 255))
        self._finalized = False

    def _flush_logical_layer(self):
        layer = pygame.transform.scale(self.logical_canvas, self.render_surface.get_size())
        self.render_surface.blit(layer, (0, 0))
        self.logical_canvas.fill((0, 0, 0, 0))

    def composite_native(self, surface, logical_dest, logical_size):
        """Flush prior logical drawings, then composite an image at render density.

        Destination and size are in world-independent logical screen units. The
        source is sampled directly at the 2x target size, so detailed source
        pixels need not pass through the 480x270 staging surface.
        """
        if self._finalized:
            raise RuntimeError('Cannot add a native layer after frame finalization')
        self._flush_logical_layer()
        d = config.RENDER_DENSITY
        size = (max(1, round(logical_size[0] * d)), max(1, round(logical_size[1] * d)))
        image = surface if surface.get_size() == size else pygame.transform.scale(surface, size)
        self.render_surface.blit(image, (round(logical_dest[0] * d), round(logical_dest[1] * d)))

    def finalize_frame(self):
        """Flush foreground and expose the native frame to capture tools.

        After finalization, logical_canvas is a downsampled inspection snapshot;
        drawing to it no longer affects the frame until clear() starts another.
        """
        if not self._finalized:
            self._flush_logical_layer()
            # Preserve a flattened logical inspection image for legacy callers.
            # The native output never passes through this downsample.
            pygame.transform.scale(self.render_surface, self.logical_canvas.get_size(), self.logical_canvas)
            self._finalized = True
        return self.render_surface

    def draw_text(self, text, x_pos, y_pos, color=config.COLOR_CRT_GREEN, size="sm", has_shadow=True):
        """Render crisp pixel text onto the 480x270 canvas."""
        font = self.font_lg if size == "lg" else (self.font_md if size == "md" else self.font_sm)
        if has_shadow:
            shadow_surf = font.render(str(text), False, (0, 0, 0))
            self.canvas.blit(shadow_surf, (int(x_pos) + 1, int(y_pos) + 1))
        text_surf = font.render(str(text), False, color)
        self.canvas.blit(text_surf, (int(x_pos), int(y_pos)))
        return text_surf.get_rect(topleft=(int(x_pos), int(y_pos)))

    def draw_panel(self, rect, bg_color=config.COLOR_CRT_DARK, border_color=config.COLOR_CRT_GREEN, title=None):
        """Draw a retrofuturistic framed terminal/HUD panel on the 480x270 canvas."""
        panel_rect = pygame.Rect(rect)
        pygame.draw.rect(self.canvas, bg_color, panel_rect)
        pygame.draw.rect(self.canvas, border_color, panel_rect, width=1)
        if title:
            header_rect = pygame.Rect(panel_rect.x, panel_rect.y, panel_rect.w, 12)
            pygame.draw.rect(self.canvas, border_color, header_rect)
            self.draw_text(title, panel_rect.x + 4, panel_rect.y + 1, color=config.COLOR_VOID_BLACK, size="sm", has_shadow=False)

    def present(self, window_surface):
        """Integer-scale the 960x540 frame to the window and apply CRT/VHS effects."""
        self.finalize_frame()
        if getattr(self, "_scaled_canvas", None) is None or self._scaled_canvas.get_size() != (self.win_w, self.win_h):
            self._scaled_canvas = pygame.Surface((self.win_w, self.win_h)).convert()

        if self.glitch_timer_ms > 0 and self.glitch_intensity > 0:
            pygame.transform.scale(self.render_surface, (self.win_w, self.win_h), dest_surface=self._scaled_canvas)
            window_surface.fill(config.COLOR_VOID_BLACK)
            slice_h = 18 * config.RENDER_DENSITY * self.scale
            max_jitter = self.glitch_intensity * config.RENDER_DENSITY * self.scale
            for y_pos in range(0, self.win_h, slice_h):
                offset_x = random.randint(-max_jitter, max_jitter)
                actual_h = min(slice_h, self.win_h - y_pos)
                sub_surf = self._scaled_canvas.subsurface((0, y_pos, self.win_w, actual_h))
                window_surface.blit(sub_surf, (offset_x, y_pos))
        else:
            if window_surface.get_size() == (self.win_w, self.win_h):
                pygame.transform.scale(self.render_surface, (self.win_w, self.win_h), dest_surface=window_surface)
            else:
                pygame.transform.scale(self.render_surface, (self.win_w, self.win_h), dest_surface=self._scaled_canvas)
                window_surface.blit(self._scaled_canvas, (0, 0))

        if self.is_crt_enabled:
            window_surface.blit(self.scanline_overlay, (0, 0))
