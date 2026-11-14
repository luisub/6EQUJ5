"""Saved, skippable travel along the signal route, then through a centered gate."""
import math
import pygame

from .. import config
from ..alien_journey import journey_data, ledger
from ..galaxy_transit import arrive, display_name, map_points, leg_position, leg_points, route_ids
from ..galaxy_transit_assets import load_galaxy_transit
from .base import BaseScene

MAP_SECONDS = 2.5
VORTEX_SECONDS = 1.2
ARRIVAL_SECONDS = 0.4
TOTAL_SECONDS = MAP_SECONDS + VORTEX_SECONDS + ARRIVAL_SECONDS
MAP_AREA = (32, 68, 416, 132)
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
                angle = 65 * progress
                extent = 128 + 176 * eased
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
        route = route_ids()
        points = map_points(MAP_AREA)
        visited = {'earth'} | {w['id'] for w in journey_data()['worlds'] if w['civ_id'] in self.receipts}
        for origin, target in zip(route, route[1:]):
            if origin not in points or target not in points:
                continue
            completed = target in visited and target != 'earth'
            color = (76, 139, 150) if completed else (49, 64, 82)
            pygame.draw.lines(crt.canvas, color, False, leg_points(origin, target, MAP_AREA), 1)
        if source in points and destination in points:
            progress = min(1.0, self.elapsed / MAP_SECONDS)
            pygame.draw.lines(crt.canvas, (101, 154, 166), False, leg_points(source, destination, MAP_AREA), 1)
            pygame.draw.lines(crt.canvas, (241, 201, 123), False,
                              leg_points(source, destination, MAP_AREA, progress), 2)
            travel = leg_position(source, destination, MAP_AREA, progress)
            pygame.draw.circle(crt.canvas, (255, 237, 183), travel, 4)
        for index, loc_id in enumerate(route[:-1]):
            if loc_id not in points:
                continue
            x, y = points[loc_id]
            color = ((241, 201, 123) if loc_id == source else (112, 223, 229) if loc_id == destination
                     else (120, 175, 184) if loc_id in visited else (98, 115, 139))
            pygame.draw.circle(crt.canvas, (5, 13, 23), (x, y), 6)
            pygame.draw.circle(crt.canvas, color, (x, y), 5 if loc_id in (source, destination) else 3, 1)
            # Only route numbers live on the map; full names have room in the caption.
            label = 'Earth' if index == 0 else str(index)
            lx = x + 8
            ly = y - 10
            crt.draw_text(label, lx, ly, color=color, size='sm', has_shadow=False)

    def _vortex(self, crt):
        if not self.vortex_frames:
            return
        progress = max(0.0, min(1.0, (self.elapsed - MAP_SECONDS) / (VORTEX_SECONDS + ARRIVAL_SECONDS)))
        frame = self.vortex_frames[round(progress * (len(self.vortex_frames) - 1))]
        size = VORTEX_FRAME_SIZE // 2
        dest = (VORTEX_CENTER[0] - size // 2, VORTEX_CENTER[1] - size // 2)
        crt.composite_native(frame, dest, (size, size))

    def _captions(self, crt):
        source, destination = self.pending['source'], self.pending['destination']
        route = route_ids()
        pygame.draw.rect(crt.canvas, (7, 17, 25), (12, 8, 456, 49), border_radius=4)
        pygame.draw.rect(crt.canvas, (7, 17, 25), (12, 215, 456, 48), border_radius=4)
        heading = 'ARRIVING' if self.phase == 'arrival' else 'ENTERING THE GATE' if self.phase == 'vortex' else 'FOLLOWING THE SIGNAL'
        crt.draw_text(heading, 24, 16, color=(241, 201, 123), size='sm', has_shadow=False)
        crt.draw_text(display_name(destination), 24, 32, color=(232, 235, 227), size='lg', has_shadow=False)
        step = route.index(destination) if destination != 'earth' else 12
        crt.draw_text(f'LEG {step} / 12', 384, 17, color=(156, 180, 188), size='sm', has_shadow=False)
        crt.draw_text(f'{len(self.receipts)} / 11 messages', 352, 41,
                      color=(156, 180, 188), size='sm', has_shadow=False)
        crt.draw_text('From ' + display_name(source), 24, 220, color=(112, 223, 229), size='sm', has_shadow=False)
        objective = 'Confront the Core with all eleven messages.' if destination == 'earth' else 'Find the guardian. Recover the next message.'
        crt.draw_text(objective, 24, 234, color=(232, 235, 227), size='sm', has_shadow=False)
        message = 'Could not save. Enter / F5: retry arrival' if self.save_failed else 'Enter / A / click: arrive'
        crt.draw_text(message, 24, 249, color=(241, 201, 123), size='sm', has_shadow=False)
        crt.draw_text('Schematic · not to scale', 330, 249, color=(156, 180, 188), size='sm', has_shadow=False)

    def render(self, crt):
        crt.clear((2, 4, 12))
        if self.pending:
            if self.assets:
                crt.composite_native(self.assets['galaxy_map'], (0, 0), (480, 270))
            self.shade.fill((2, 7, 15, 100 if self.phase == 'map' else 210))
            crt.canvas.blit(self.shade, (0, 0))
            if self.phase == 'map':
                self._map(crt)
            else:
                self._vortex(crt)
            self._captions(crt)
