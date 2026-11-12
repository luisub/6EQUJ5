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

from collections import OrderedDict
from contextlib import contextmanager
import math
import random
import pygame
from . import config


_UI_GLYPHS = str.maketrans({'▶': '>', '✔': '+', '■': '#', '●': '*',
                            '○': 'o', '▌': '|', '→': '->'})


class LogicalFont:
    """Native font whose measurements are reported in 480-grid units."""

    def __init__(self, native_size):
        self.native = pygame.font.Font(None, native_size)

    def size(self, text):
        width, height = self.native.size(str(text).translate(_UI_GLYPHS))
        return math.ceil(width / config.RENDER_DENSITY), math.ceil(height / config.RENDER_DENSITY)


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
        self._initial_layer = False
        self.set_scale(scale)
        pygame.font.init()
        # pygame ships FreeSansBold. Native-size text is independent of host fonts.
        self.font_sm = LogicalFont(26)
        self.font_md = LogicalFont(32)
        self.font_lg = LogicalFont(42)
        self._text_cache = OrderedDict()
        self._text_batch_depth = 0
        self._text_batch_ready = False
        self._text_batch_region = None
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
        self._initial_layer = True

    def _flush_logical_layer(self):
        # clear() starts with an opaque full-screen layer; scaling the whole
        # first layer is correct even if callers later clear individual pixels.
        if self._initial_layer:
            bounds = self.logical_canvas.get_rect()
            self._initial_layer = False
        else:
            bounds = self.logical_canvas.get_bounding_rect()
        if bounds.w and bounds.h:
            density = config.RENDER_DENSITY
            layer = pygame.transform.scale(self.logical_canvas.subsurface(bounds),
                                           (bounds.w * density, bounds.h * density))
            self.render_surface.blit(layer, (bounds.x * density, bounds.y * density))
            self.logical_canvas.fill((0, 0, 0, 0))

    @contextmanager
    def text_batch(self, dirty_region=None):
        """Group adjacent text-only draws; no logical canvas writes inside the block.

        A region may be supplied only when pending writes outside that region
        cannot overlap the batched text; those other areas remain staged.
        """
        if self._text_batch_depth == 0:
            self._text_batch_ready = False
            self._text_batch_region = pygame.Rect(dirty_region) if dirty_region is not None else None
        self._text_batch_depth += 1
        try:
            yield
        finally:
            self._text_batch_depth -= 1
            if self._text_batch_depth == 0:
                self._text_batch_ready = False
                self._text_batch_region = None

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
        """Render native-density text at its original position in scene order."""
        font = self.font_lg if size == "lg" else (self.font_md if size == "md" else self.font_sm)
        text = str(text).translate(_UI_GLYPHS)
        if not text:
            return pygame.Rect(int(x_pos), int(y_pos), 0, 0)
        # Dim green was designed for scanlines, but was illegible on dark panels.
        if tuple(color) == tuple(config.COLOR_CRT_DIM):
            color = (112, 207, 143)
        color = tuple(color)
        def glyphs(glyph_color):
            key = (size, text, glyph_color)
            cached = self._text_cache.get(key)
            if cached is None:
                cached = font.native.render(text, True, glyph_color)
                self._text_cache[key] = cached
                if len(self._text_cache) > 256:
                    self._text_cache.popitem(last=False)
            else:
                self._text_cache.move_to_end(key)
            return cached
        text_surf = glyphs(color)
        width, height = text_surf.get_size()
        logical_size = (width / config.RENDER_DENSITY, height / config.RENDER_DENSITY)
        if self._finalized:
            raise RuntimeError('Cannot draw text after frame finalization')
        if not self._text_batch_depth or not self._text_batch_ready:
            if self._text_batch_region is None or self._initial_layer:
                self._flush_logical_layer()
            else:
                bounds = self._text_batch_region.clip(self.logical_canvas.get_rect())
                if bounds.w and bounds.h:
                    density = config.RENDER_DENSITY
                    layer = pygame.transform.scale(self.logical_canvas.subsurface(bounds),
                                                   (bounds.w * density, bounds.h * density))
                    self.render_surface.blit(layer, (bounds.x * density, bounds.y * density))
                    self.logical_canvas.fill((0, 0, 0, 0), bounds)
            self._text_batch_ready = bool(self._text_batch_depth)
        dest = (int(x_pos) * config.RENDER_DENSITY, int(y_pos) * config.RENDER_DENSITY)
        if has_shadow:
            shadow_surf = glyphs((0, 0, 0))
            self.render_surface.blit(shadow_surf, (dest[0] + 1, dest[1] + 1))
        self.render_surface.blit(text_surf, dest)
        return pygame.Rect(int(x_pos), int(y_pos), math.ceil(logical_size[0]), math.ceil(logical_size[1]))

    def draw_panel(self, rect, bg_color=config.COLOR_CRT_DARK, border_color=config.COLOR_CRT_GREEN, title=None):
        """Draw a retrofuturistic framed terminal/HUD panel on the 480x270 canvas."""
        panel_rect = pygame.Rect(rect)
        pygame.draw.rect(self.canvas, bg_color, panel_rect)
        pygame.draw.rect(self.canvas, border_color, panel_rect, width=1)
        if title:
            header_rect = pygame.Rect(panel_rect.x, panel_rect.y, panel_rect.w, 12)
            pygame.draw.rect(self.canvas, border_color, header_rect)
            label = str(title)
            max_width = max(0, panel_rect.w - 8)
            if self.font_sm.size(label)[0] > max_width:
                while label and self.font_sm.size(label + '...')[0] > max_width:
                    label = label[:-1]
                label = label + '...' if label else ''
            self.draw_text(label, panel_rect.x + 4, panel_rect.y + 1, color=config.COLOR_VOID_BLACK, size="sm", has_shadow=False)

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
