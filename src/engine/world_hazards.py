"""PURPOSE: Telegraph and animate bounded, jumpable local foreground hazards.
CALLED BY: FieldOpsScene after player movement and before actor rendering.
HOW TO MODIFY: Preserve warning, context allowlists, cached art and one hit per pass.
"""
import math
from pathlib import Path

import pygame

from .planet_threat_assets import WORLD_THREAT_IDS, load_planet_threat

# Only traversable contemporary exteriors; never archaeological or alien rooms.
MODERN_WAGON_ACTS = {
    'act_01_perimeter_road': 'act_01', 'act_02_blackout_street': 'act_02',
    'act_03_salt_flats': 'act_03', 'act_04_rail_yard': 'act_04',
}
MODERN_WAGON_ROOMS = frozenset(MODERN_WAGON_ACTS)
ARCHAEOLOGICAL_EFFIGY_ROOMS = frozenset({
    'act_05_pillar_approach', 'act_05_buried_archive', 'act_05_crust_waveguide',
})
GROUND_Y = 240


def _number(value, low, high):
    return type(value) in (int, float) and math.isfinite(value) and low <= value <= high


class WorldHazards:
    """One warned visual object travels left across the view, with no persistence."""

    def __init__(self, asset_root, room, config):
        self.room = room
        self.enabled = False
        self.image = None
        self.hit_bounds = None
        self.contact_bounds = None
        self.kind = None
        self.damage = 0
        self.speed = 0.0
        self.warning_seconds = 0.0
        self.cooldown_seconds = 0.0
        self.initial_delay = 0.0
        self.phase = 'disabled'
        self.timer = 0.0
        self.x = 0.0
        self.hit_this_pass = False
        self.action_cue = False
        self._cue_player = None
        if asset_root is None or not isinstance(config, dict):
            return
        if set(config) != {'kind', 'art_id', 'damage', 'speed', 'warning_seconds', 'cooldown_seconds', 'initial_delay'}:
            return
        damage, speed = config['damage'], config['speed']
        warning, cooldown, delay = config['warning_seconds'], config['cooldown_seconds'], config['initial_delay']
        if (type(damage) is not int or not 1 <= damage <= 25
                or not _number(speed, 40, 140) or not _number(warning, 1.2, 10)
                or not _number(cooldown, 5, 60) or not _number(delay, 8, 120)):
            return
        room_id = getattr(room, 'room_id', None)
        kind, art_id = config['kind'], config['art_id']
        if kind in ('planet_charge', 'stone_effigy'):
            if kind == 'planet_charge':
                if not isinstance(room_id, str) or not room_id.endswith('_field'):
                    return
                world = room_id.removesuffix('_field')
                if WORLD_THREAT_IDS.get(world) != art_id:
                    return
            elif (room_id not in ARCHAEOLOGICAL_EFFIGY_ROOMS
                  or getattr(room, 'act_id', None) != 'act_05' or art_id != 'resonance_effigy'):
                return
            loaded = load_planet_threat(asset_root, art_id)
            if loaded is None:
                return
            source, bounds, pivot = loaded
            if pivot != (48, 64):
                return
            # Directional source bodies face right; this pass moves left.
            # Mirror once at entry and mirror bounds before mapping to logical pixels.
            self.image = pygame.transform.scale(pygame.transform.flip(source, True, False), (120, 90))
            left, top, right, bottom = bounds
            left, right = source.get_width() - right, source.get_width() - left
            # Source-space bounds become logical coordinates after 1.25x at 2x density.
            self.hit_bounds = pygame.Rect(math.floor(left * .625), math.floor(top * .625),
                                          math.ceil(right * .625) - math.floor(left * .625),
                                          math.ceil(bottom * .625) - math.floor(top * .625))
            self.logical_size = (60, 45)
            self.origin_y = GROUND_Y - 40  # authored pivot y=64 at 1.25x native
        elif kind == 'earth_wagon':
            if (room_id not in MODERN_WAGON_ROOMS or art_id != 'ohio_wagon'
                    or getattr(room, 'act_id', None) != MODERN_WAGON_ACTS[room_id]):
                return
            try:
                source = pygame.image.load(str(Path(asset_root) / 'environments/ohio_salvage_v1/wagon_168x76_rgba.png')).convert_alpha()
                self.image = pygame.transform.scale(source, (144, 66))
            except (OSError, pygame.error):
                return
            bounds = pygame.mask.from_surface(self.image, 0).get_bounding_rects()
            if not bounds:
                self.image = None
                return
            native = bounds[0].unionall(bounds[1:])
            left, top = native.left // 2, native.top // 2
            self.hit_bounds = pygame.Rect(left, top, math.ceil(native.right / 2) - left,
                                          math.ceil(native.bottom / 2) - top)
            self.logical_size = (72, 33)
            self.origin_y = GROUND_Y - 33
        else:
            return
        if self.hit_bounds.height > 35 or self.hit_bounds.width <= 0 or self.hit_bounds.height <= 0:
            self.image = None
            self.hit_bounds = None
            return
        # Preserve full authored visibility/placement while making the actual
        # contact a low, central, jumpable portion of that visible body.
        width = min(16, self.hit_bounds.width)
        height = min(18, self.hit_bounds.height)
        self.contact_bounds = pygame.Rect(self.hit_bounds.centerx - width // 2,
                                          self.hit_bounds.bottom - height, width, height)
        self.kind = kind
        self.damage, self.speed = damage, float(speed)
        self.warning_seconds, self.cooldown_seconds, self.initial_delay = float(warning), float(cooldown), float(delay)
        self.enabled = True
        self.reset()

    def reset(self):
        """Cancel a pass and reapply the safe initial delay on respawn/room exit."""
        self.phase = 'delay' if self.enabled else 'disabled'
        self.timer = self.initial_delay if self.enabled else 0.0
        self.x = 0.0
        self.hit_this_pass = False
        self.action_cue = False
        self._cue_player = None

    def _body(self, x):
        return self.hit_bounds.move(round(x), self.origin_y)

    def _contact_body(self, x):
        return self.contact_bounds.move(round(x), self.origin_y)

    def _update_action_cue(self, player, camera):
        """Show a jump window only when current motion permits a 0.2s response."""
        if self.phase != 'active' or self.hit_this_pass or not getattr(player, 'is_grounded', False):
            return
        core = self._contact_body(self.x)
        visible = self._body(self.x).clip(pygame.Rect(round(camera.x), 0, camera.viewport_w,
                                                       max(1, getattr(camera, 'world_h', 288))))
        if not visible or not player.rect.colliderect(pygame.Rect(round(camera.x), 0, camera.viewport_w,
                                                                  max(1, getattr(camera, 'world_h', 288)))):
            return
        gap = core.left - player.rect.right
        speed = self.speed + getattr(player, 'vx', 0.0)
        if not _number(speed, .01, 1000) or gap < 0:
            return
        cfg = getattr(player, 'cfg', None)
        launch = -getattr(cfg, 'jump_velocity', 0.0)
        gravity = getattr(cfg, 'gravity', 0.0)
        height = player.rect.bottom - core.top
        if not _number(launch, .01, 10000) or not _number(gravity, .01, 10000) or height <= 0:
            return
        discriminant = launch * launch - 2 * gravity * height
        if discriminant <= 0:
            return
        root = math.sqrt(discriminant)
        rise = (launch - root) / gravity
        fall = (launch + root) / gravity
        overlap_time = (player.rect.width + core.width) / speed
        # In a valid window, jumping immediately or after 0.2 seconds both
        # clear the complete core. A small margin covers fixed-step rounding.
        earliest = rise + .2 + .015
        latest = fall - overlap_time - .025
        time_to_contact = gap / speed
        if earliest <= latest and rise + .015 <= time_to_contact <= (earliest + latest) / 2:
            self.action_cue = True

    def update(self, dt, player, camera, *, paused=False, alive=True, blocking=False, crowded=False):
        """Advance one short simulation frame; pause/blocking cannot harm the player."""
        self.action_cue = False
        self._cue_player = player
        if not self.enabled:
            return
        if not alive or getattr(player, 'is_dead', False):
            self.reset()
            return
        if blocking:
            # The player may move while crowding or an interaction is active;
            # do not resume an old hazard on top of them afterward.
            if self.phase == 'active':
                self.reset()
            return
        if paused or not _number(dt, 0, 10) or dt == 0:
            return
        if crowded and self.phase != 'active':
            # Postpone new passes; an already announced pass is withdrawn
            # before it appears, never after its object is on screen.
            if self.phase == 'warning':
                self.phase, self.timer = 'cooldown', self.cooldown_seconds
            return
        remaining = min(float(dt), 0.1)
        # Time left over at phase boundaries contributes to the next phase.
        while remaining > 1e-9:
            if self.phase in ('delay', 'warning', 'cooldown'):
                elapsed = min(self.timer, remaining)
                self.timer -= elapsed
                remaining -= elapsed
                if self.timer > 1e-9:
                    break
                if self.phase in ('delay', 'cooldown'):
                    self.phase, self.timer = 'warning', self.warning_seconds
                else:
                    self.phase = 'active'
                    self.x = float(camera.x + camera.viewport_w + 8 - self.hit_bounds.left)
                    self.hit_this_pass = False
                continue
            if self.phase == 'active':
                old = self._contact_body(self.x)
                self.x -= self.speed * remaining
                body = self._contact_body(self.x)
                swept = old.union(body)
                viewport = pygame.Rect(round(camera.x), 0, camera.viewport_w, max(1, getattr(camera, 'world_h', 288)))
                visible_path = swept.clip(viewport)
                visible_player = player.rect.clip(viewport)
                if (not self.hit_this_pass and visible_path.colliderect(visible_player)):
                    self.hit_this_pass = True
                    player.take_damage(self.damage, damage_source='hostile')
                remaining = 0.0
                if self._body(self.x).right < camera.x - 8:
                    self.phase, self.timer = 'cooldown', self.cooldown_seconds
                break
            break
        if self.phase == 'active' and not getattr(player, 'is_dead', False):
            self._update_action_cue(player, camera)

    def render(self, crt, camera):
        """Draw a visible edge warning or the authored cached sprite; never load art."""
        if not self.enabled:
            return
        if self.phase == 'warning':
            x = camera.viewport_w - 14
            pygame.draw.polygon(crt.canvas, (244, 189, 75), [(x, 184), (x + 9, 178), (x + 9, 190)])
            crt.draw_text('INCOMING', camera.viewport_w - 95, 162, color=(255, 210, 125), size='sm')
        elif self.phase == 'active':
            sx, sy = camera.world_to_screen(self.x, self.origin_y)
            crt.composite_native(self.image, (sx, sy), self.logical_size)
            player = self._cue_player
            scene = getattr(player, 'combat_context', None)
            machine = getattr(scene, 'machine', None)
            paused = getattr(getattr(machine, 'pause', None), 'active', False)
            modal = bool(getattr(scene, 'route_story', None) or getattr(getattr(scene, 'reality', None), 'panel_open', False))
            if (self.action_cue and not paused and not modal and not getattr(player, 'is_dead', False)
                    and getattr(player, 'is_grounded', False) and not self.hit_this_pass):
                body = self._body(self.x)
                center_x = (player.rect.centerx + self._contact_body(self.x).centerx) / 2
                sx, sy = camera.world_to_screen(center_x, min(player.rect.top, body.top) - 20)
                font = getattr(crt, 'font_sm', None)
                width = font.size('HOLD JUMP')[0] if font is not None else 55
                x = max(4, min(camera.viewport_w - width - 4, sx - width // 2))
                y = max(40, min(camera.viewport_h - 20, sy))
                crt.draw_text('HOLD JUMP', x, y, color=(255, 210, 125), size='sm')
