"""PURPOSE: Render a compact energy stream without changing projectile simulation.
CALLED BY: FieldOpsScene and BossScene after verified art loads at scene entry.
HOW TO MODIFY: Keep visible segments clipped to active projectile heads and caches bounded.
"""
from collections import OrderedDict
import math
import pygame

from .weapons import check_swept_ray_tile_collision
from .combat_feedback import draw_energy_bolt


class EnergyFilament:
    """Native-density, bounded muzzle stream plus tiny active projectile glows."""
    MAX_CACHE = 192
    MAX_TRACKED = 128
    MAX_STEM = 46.0  # The 96px bitmap extends 92 native px beyond its pivot.
    STEM_TIME = 0.16
    OVERLAP_TIME = 0.27  # Bridge consecutive real volleys, never an isolated shot.
    PIVOT = (4, 12)
    MAX_TRACK_DEVIATION = 3.0
    MUZZLE_FLAME_TIME = 0.06
    MUZZLE_FLAME_LENGTH = 4.0

    def __init__(self, image):
        if image.get_size() != (96, 24) or not image.get_flags() & pygame.SRCALPHA:
            raise ValueError('Expected a 96x24 alpha energy filament')
        self.image = image
        self.cache = OrderedDict()
        self.packet_cache = OrderedDict()
        self.emitter_cache = OrderedDict()
        self.emitter = self._emitter()
        self.origins = OrderedDict()
        self.primary_glow = self._glow(3, (255, 235, 175), (90, 205, 220))
        self.support_glow = self._glow(2, (210, 250, 245), (75, 150, 165))

    @staticmethod
    def _emitter():
        """A small translucent light, centered three native pixels behind the muzzle."""
        surface = pygame.Surface((13, 9), pygame.SRCALPHA)
        pygame.draw.circle(surface, (70, 170, 190, 54), (6, 4), 4)
        pygame.draw.circle(surface, (255, 188, 105, 125), (6, 4), 2)
        pygame.draw.circle(surface, (255, 246, 215, 210), (6, 4), 1)
        return surface

    @staticmethod
    def _glow(radius, core, halo):
        # Keep the luminous packet behind its collision head, not ahead of it.
        surface = pygame.Surface((radius + 1, radius * 2 + 1), pygame.SRCALPHA)
        center = (radius, radius)
        pygame.draw.circle(surface, (*halo, 60), center, radius)
        pygame.draw.circle(surface, (*core, 225), center, max(1, radius // 2))
        return surface

    def register(self, projectiles, generation):
        """Record real muzzle origins at spawn; this is presentation-only state."""
        for projectile in projectiles:
            if projectile.weapon_type != 'starter_maser' or projectile.is_charged:
                continue
            self.origins[projectile.id] = (projectile.x, projectile.y, generation)
            self.origins.move_to_end(projectile.id)
            if len(self.origins) > self.MAX_TRACKED:
                self.origins.popitem(last=False)

    def _rotated_segment(self, length, angle, phase=0):
        """Crop to the active head before rotating; the pivot stays at the muzzle."""
        # Floor plus one native-pixel safety margin prevents the strip reaching
        # beyond a collision head even at a quantized heading.
        extent = max(0, min(91, int(math.floor(length * 2)) - 1))
        if not extent:
            return None
        direction = int(round(angle / 2.0) * 2) % 360
        key = (extent, direction, phase)
        cached = self.cache.get(key)
        if cached is not None:
            self.cache.move_to_end(key)
            return cached
        width = self.PIVOT[0] + extent
        source = self.image.subsurface((0, 0, width, 24)).copy()
        # A one-native-pixel cool rim softens the authored strand without
        # widening the beam or altering its master image.
        rim = source.copy()
        rim.fill((100, 175, 200, 72), special_flags=pygame.BLEND_RGBA_MULT)
        softened = pygame.Surface((width, 24), pygame.SRCALPHA)
        softened.blit(rim, (0, -1))
        softened.blit(rim, (0, 1))
        softened.blit(source, (0, 0))
        # White-hot branching filament with cyan falloff and a fine gold strand.
        # Clip before rotation, using the same collision-bounded source extent.
        softened.set_clip((0, 8, width, 9))
        draw_energy_bolt(softened, self.PIVOT, (width - 2, self.PIVOT[1]), phase)
        softened.set_clip(None)
        image = pygame.transform.rotate(softened, -direction)
        radians = math.radians(direction)
        offset = self.PIVOT[0] - width / 2.0
        pivot = (round(image.get_width() / 2.0 + offset * math.cos(radians)),
                 round(image.get_height() / 2.0 + offset * math.sin(radians)))
        value = (image, pivot)
        self.cache[key] = value
        if len(self.cache) > self.MAX_CACHE:
            self.cache.popitem(last=False)
        return value

    def _rotated_emitter(self, safe_length, angle):
        """Crop the forward edge before rotation so light cannot pass an obstacle."""
        ahead = max(0, min(3, int(math.floor(safe_length * 2)) - 1))
        direction = int(round(angle / 2.0) * 2) % 360
        key = (ahead, direction)
        cached = self.emitter_cache.get(key)
        if cached is not None:
            self.emitter_cache.move_to_end(key)
            return cached
        pivot_x, pivot_y = 9, 4
        width = pivot_x + ahead
        source = self.emitter.subsurface((0, 0, width, 9)).copy()
        image = pygame.transform.rotate(source, -direction)
        radians = math.radians(direction)
        offset_x = pivot_x - width / 2.0
        offset_y = pivot_y - 9 / 2.0
        pivot = (round(image.get_width() / 2.0 + offset_x * math.cos(radians) - offset_y * math.sin(radians)),
                 round(image.get_height() / 2.0 + offset_x * math.sin(radians) + offset_y * math.cos(radians)))
        value = (image, pivot)
        self.emitter_cache[key] = value
        if len(self.emitter_cache) > self.MAX_CACHE:
            self.emitter_cache.popitem(last=False)
        return value

    def _rotated_packet(self, primary, angle):
        direction = int(round(angle / 2.0) * 2) % 360
        key = (primary, direction)
        cached = self.packet_cache.get(key)
        if cached is not None:
            self.packet_cache.move_to_end(key)
            return cached
        source = self.primary_glow if primary else self.support_glow
        image = pygame.transform.rotate(source, -direction)
        radians = math.radians(direction)
        # The front edge is the head; all source pixels sit behind this pivot.
        offset_x = source.get_width() - source.get_width() / 2.0
        offset_y = (source.get_height() - 1) / 2.0 - source.get_height() / 2.0
        pivot = (round(image.get_width() / 2.0 + offset_x * math.cos(radians) - offset_y * math.sin(radians)),
                 round(image.get_height() / 2.0 + offset_x * math.sin(radians) + offset_y * math.cos(radians)))
        value = (image, pivot)
        self.packet_cache[key] = value
        if len(self.packet_cache) > self.MAX_CACHE:
            self.packet_cache.popitem(last=False)
        return value

    @staticmethod
    def current_aim(player_input, muzzle, facing):
        """Use the same pointer/stick or facing context as the actual player shot."""
        if player_input is not None and player_input.aim_target_x is not None and player_input.aim_target_y is not None:
            dx, dy = player_input.aim_target_x - muzzle[0], player_input.aim_target_y - muzzle[1]
        elif player_input is not None and player_input.aim_x is not None and player_input.aim_y is not None:
            dx, dy = player_input.aim_x, player_input.aim_y
        else:
            dx, dy = (-1.0 if facing == 'left' else 1.0), 0.0
        length = math.hypot(dx, dy)
        return (dx / length, dy / length) if length > 1e-6 else ((-1.0 if facing == 'left' else 1.0), 0.0)

    @classmethod
    def _visible_stem(cls, projectile, muzzle, room=None, targets=(), aim_vector=None, *, max_age=None):
        """Anchor to the current muzzle and conservatively clip to visible geometry."""
        mx, my = muzzle
        dx, dy = projectile.dir_x, projectile.dir_y
        if aim_vector is not None and dx * aim_vector[0] + dy * aim_vector[1] < 0.98:
            return 0.0
        hx, hy = projectile.x - mx, projectile.y - my
        along = hx * dx + hy * dy
        if along <= 0:
            return 0.0
        age = projectile.max_lifetime - projectile.lifetime
        if age < 0 or age > (cls.STEM_TIME if max_age is None else max_age):
            return 0.0
        deviation = abs(hx * dy - hy * dx)
        if deviation > cls.MAX_TRACK_DEVIATION:
            if age > cls.MUZZLE_FLAME_TIME:
                return 0.0
            length = min(cls.MUZZLE_FLAME_LENGTH, along)
        else:
            length = min(cls.MAX_STEM, along)
        end_x, end_y = mx + dx * length, my + dy * length
        if room is not None:
            hit, x, y, _, _ = check_swept_ray_tile_collision(room, mx, my, end_x, end_y)
            if hit:
                length = min(length, math.hypot(x - mx, y - my))
        for target in targets:
            if getattr(target, 'is_dead', False):
                continue
            clip = target.rect.clipline((mx, my), (end_x, end_y))
            if clip:
                length = min(length, math.hypot(clip[0][0] - mx, clip[0][1] - my))
        return max(0.0, length - 0.5)

    def render(self, crt, camera, projectiles, generation, *, blocked=False,
               muzzle=None, room=None, targets=(), aim_vector=None, collect_layers=False):
        """Draw only live tracked shots; collision/expiry removes their visuals."""
        live = {projectile.id for projectile in projectiles if projectile.active}
        for ident in tuple(self.origins):
            if ident not in live:
                self.origins.pop(ident, None)
        if blocked:
            return []
        layers = []
        primaries = [p for p in projectiles
                     if p.active and p.is_primary_discharge and p.id in self.origins
                     and self.origins[p.id][2] == generation
                     and p.weapon_type == 'starter_maser' and not p.is_charged]
        latest_primary = primaries[-1] if primaries else None
        stem_projectile, stem_length = None, 0.0
        if latest_primary is not None:
            latest_origin = self.origins[latest_primary.id]
            current_muzzle = muzzle if muzzle is not None else latest_origin[:2]
            latest_length = self._visible_stem(latest_primary, current_muzzle, room, targets, aim_vector)
            if latest_length > 0:
                stem_projectile, stem_length = latest_primary, latest_length
                # A prior live primary may bridge only a newer, valid real tap.
                for previous in primaries[:-1]:
                    length = self._visible_stem(previous, current_muzzle, room, targets,
                                                aim_vector, max_age=self.OVERLAP_TIME)
                    if length > stem_length:
                        stem_projectile, stem_length = previous, length
        for projectile in projectiles:
            origin = self.origins.get(projectile.id)
            if (not projectile.active or origin is None or origin[2] != generation
                    or projectile.weapon_type != 'starter_maser' or projectile.is_charged):
                continue
            x, y = camera.world_to_screen(projectile.x, projectile.y)
            if projectile.is_primary_discharge:
                current_muzzle = muzzle if muzzle is not None else origin[:2]
                length = stem_length if projectile is stem_projectile else 0.0
                if length > 0:
                    phase = int((projectile.max_lifetime - projectile.lifetime) * 30) % 4
                    segment = self._rotated_segment(length,
                                                    math.degrees(math.atan2(projectile.dir_y, projectile.dir_x)), phase)
                    if segment is not None:
                        image, pivot = segment
                        ox, oy = camera.world_to_screen(*current_muzzle)
                        emitter, emitter_pivot = self._rotated_emitter(
                            length, math.degrees(math.atan2(projectile.dir_y, projectile.dir_x)))
                        layers.append((emitter, (2 * ox - emitter_pivot[0], 2 * oy - emitter_pivot[1]), 0))
                        layers.append((image, (2 * ox - pivot[0], 2 * oy - pivot[1]), 0))
            angle = math.degrees(math.atan2(projectile.dir_y, projectile.dir_x))
            packet, pivot = self._rotated_packet(projectile.is_primary_discharge, angle)
            # A one-logical-pixel setback absorbs camera rounding near solid edges.
            head_x = round(2 * x - 2 * projectile.dir_x)
            head_y = round(2 * y - 2 * projectile.dir_y)
            layers.append((packet, (head_x - pivot[0], head_y - pivot[1]), 0))
        if layers and not collect_layers:
            crt.composite_native_effects(layers)
        return layers
