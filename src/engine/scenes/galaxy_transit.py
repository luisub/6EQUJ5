"""Saved, skippable travel along the signal route, then through a centered gate."""
import math
import pygame

from .. import config
from ..alien_journey import journey_data, ledger
from ..galaxy_transit import arrive, display_name, route_ids
from ..galaxy_transit_assets import load_galaxy_transit, render_constellation
from .base import BaseScene

MAP_SECONDS = 1.65
VORTEX_SECONDS = 1.6
ARRIVAL_SECONDS = 0.45
TOTAL_SECONDS = MAP_SECONDS + VORTEX_SECONDS + ARRIVAL_SECONDS
MAP_AREA = (32, 76, 416, 132)
VORTEX_CENTER = (240, 134)
VORTEX_FRAME_SIZE = 384


class GalaxyTransitScene(BaseScene):
    """Travel presentation; the campaign owns the pending leg until arrival saves."""
    def __init__(self, machine):
        super().__init__(machine)
        self.elapsed = 0.0
        self.pending = None
        self.save_failed = False
        self.assets = None
        self.vortex_frames = []
        self.receipts = []
        self.shade = pygame.Surface((480, 270), pygame.SRCALPHA)

    def on_enter(self, **kwargs):
        current = ledger(self.machine.campaign)
        self.pending = current.get('pending_transit')
        if not self.pending:
            self.machine.change_state(config.STATE_BUNKER_HUB)
            return
        self.elapsed = 0.0
        self.save_failed = False
        # A previous scene's brief glitch should not flash over the travel map.
        self.machine.crt.glitch_timer_ms = 0
        self.machine.crt.glitch_intensity = 0
        self.receipts = list(current.get('receipts', []))
        self.assets = load_galaxy_transit(getattr(getattr(self.machine, 'assets', None), 'root', None))
        self.vortex_frames = []
        if self.assets:
            # Fixed-size native frames keep the aperture centered as it rotates.
            # Nothing is transformed, decoded or allocated during the animation.
            vortex = self.assets['vortex']
            for index in range(64):
                progress = index / 63
                eased = progress * progress * (3 - 2 * progress)
                angle = 110 * progress
                extent = 92 + 212 * eased
                scale = extent / vortex.get_width()
                rotated = pygame.transform.rotozoom(vortex, angle, scale)
                frame = pygame.Surface((VORTEX_FRAME_SIZE, VORTEX_FRAME_SIZE), pygame.SRCALPHA)
                frame.blit(rotated, rotated.get_rect(center=frame.get_rect().center))
                self.vortex_frames.append(frame)
        self.machine.input.release_all()

    def on_exit(self):
        # Never persist on exit: New/Continue may already own a different campaign.
        self.machine.input.release_all()
        self.assets = None
        self.vortex_frames = []

    def _finish(self):
        if not arrive(self.machine):
            self.save_failed = True

    def handle_event(self, event):
        skip = ((event.type == pygame.KEYDOWN and not getattr(event, 'repeat', False)
                 and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_F5))
                or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1))
        if skip:
            self._finish()

    def update(self, dt):
        if self.save_failed or not isinstance(dt, (int, float)) or not math.isfinite(dt) or dt <= 0:
            return
        self.elapsed = min(TOTAL_SECONDS, self.elapsed + dt)
        if self.elapsed >= TOTAL_SECONDS:
            self._finish()

    @property
    def phase(self):
        if self.elapsed < MAP_SECONDS:
            return 'map'
        if self.elapsed < MAP_SECONDS + VORTEX_SECONDS:
            return 'vortex'
        return 'arrival'

    def _map(self, crt):
        source, destination = self.pending['source'], self.pending['destination']
        visited = {'earth'} | {w['id'] for w in journey_data()['worlds'] if w['civ_id'] in self.receipts}
        progress = min(1.0, self.elapsed / MAP_SECONDS)
        progress = progress * progress * (3 - 2 * progress)
        render_constellation(crt, MAP_AREA, leg=(source, destination), progress=progress,
                             visited=visited, time=self.elapsed)

    def _vortex(self, crt):
        progress = max(0.0, min(1.0, (self.elapsed - MAP_SECONDS) / (VORTEX_SECONDS + ARRIVAL_SECONDS)))
        cx, cy = VORTEX_CENTER
        # Expanding perspective rings and accelerating radial stars pull the
        # viewer through the aperture. Work and geometry stay bounded.
        opening = min(1.0, progress * 4)
        for index in range(8):
            depth = (index / 8 + progress * 1.4) % 1
            radius = 9 + 154 * depth ** 2 * opening
            color = (round(25 + 33 * depth), round(50 + 74 * depth), round(78 + 82 * depth))
            pygame.draw.ellipse(crt.canvas, color,
                                (cx - radius, cy - radius * .48, radius * 2, radius * .96), 1)
        for index in range(32):
            angle = index * math.tau / 32 + .13 * math.sin(index * 7)
            depth = (index * .173 + progress * (1 + progress * 2)) % 1
            radius = 28 + 230 * depth ** 2
            extent = 2 + 27 * depth * progress
            start = (cx + math.cos(angle) * radius, cy + math.sin(angle) * radius * .46)
            end = (cx + math.cos(angle) * (radius + extent), cy + math.sin(angle) * (radius + extent) * .46)
            color = (round(44 + 86 * depth), round(72 + 100 * depth), round(109 + 91 * depth))
            pygame.draw.line(crt.canvas, color, start, end, 1)
        if self.vortex_frames:
            frame = self.vortex_frames[round(progress * (len(self.vortex_frames) - 1))]
            size = VORTEX_FRAME_SIZE // 2
            dest = (cx - size // 2, cy - size // 2)
            crt.composite_native(frame, dest, (size, size))
        else:
            # The gate remains visible even when optional bitmap art is missing.
            for radius in (24, 31, 40):
                r = max(2, round(radius * opening))
                pygame.draw.circle(crt.canvas, (55, 196, 224), (cx, cy), r, 2)

    def _captions(self, crt):
        source, destination = self.pending['source'], self.pending['destination']
        route = route_ids()
        heading = 'ARRIVING' if self.phase == 'arrival' else 'IN TRANSIT' if self.phase == 'vortex' else 'FROM ' + display_name(source).upper()
        crt.draw_text(heading, 24, 17, color=(137, 175, 190), size='sm', has_shadow=False)
        crt.draw_text(display_name(destination), 24, 33, color=(232, 235, 227), size='md', has_shadow=False)
        steps = len(route) - 1
        step = route.index(destination) if destination != 'earth' else steps
        crt.draw_text(f'{step:02d} / {steps:02d}', 405, 22, color=(241, 201, 123), size='sm', has_shadow=False)
        pygame.draw.line(crt.canvas, (39, 62, 79), (24, 57), (456, 57))
        for index in range(len(journey_data()['worlds'])):
            color = (107, 218, 220) if index < len(self.receipts) else (52, 70, 86)
            pygame.draw.rect(crt.canvas, color, (25 + index * 11, 242, 6, 3))
        message = 'SAVE FAILED — ENTER / F5: RETRY' if self.save_failed else 'ENTER / A / CLICK: SKIP'
        width = crt.font_sm.size(message)[0]
        crt.draw_text(message, 456 - width, 238, color=(241, 201, 123), size='sm', has_shadow=False)

    def render(self, crt):
        crt.clear((2, 4, 12))
        if self.pending:
            if self.assets:
                crt.composite_native(self.assets['galaxy_map'], (0, 0), (480, 270))
            self.shade.fill((2, 7, 15, 145 if self.phase == 'map' else 225))
            crt.canvas.blit(self.shade, (0, 0))
            if self.phase == 'map':
                self._map(crt)
            else:
                self._vortex(crt)
            self._captions(crt)
