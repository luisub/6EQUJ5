"""PURPOSE: Finite, telegraphed threats for alien-world field traversal.
CALLED BY: FieldOpsScene's existing encounter lifecycle.
HOW TO MODIFY: Preserve visit-local progress, safe spawns and EnemyManager damage.
"""
from functools import lru_cache
import json
import math
from pathlib import Path

import pygame

from .enemies import (Enemy, EnemyConfig, STATE_ATTACK, STATE_DEATH, STATE_HURT,
                      STATE_PATROL, STATE_RECOVERY, STATE_WINDUP)
from .world import COLLISION_ONE_WAY, COLLISION_SOLID

DATA_PATH = Path(__file__).resolve().parent.parent / 'data' / 'planet_encounters.json'
STYLES = frozenset(('strafe', 'swoop', 'pulse', 'lunge'))
MIN_CLEARANCE = 120


@lru_cache(maxsize=8)
def _data(path):
    try:
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        if data.get('schema_version') != 1 or not isinstance(data.get('worlds'), dict):
            return {}
        return data['worlds']
    except (OSError, ValueError, TypeError, AttributeError):
        return {}


def world_config(world_id, path=DATA_PATH):
    """Return only a fully validated world definition; invalid data is inert."""
    value = _data(str(path)).get(world_id)
    if not isinstance(value, dict):
        return None
    for key in ('enemy_id', 'name', 'art_id'):
        if not isinstance(value.get(key), str) or not value[key] or len(value[key]) > 100:
            return None
    if value.get('style') not in STYLES:
        return None
    bounds = {'health': (110, 170), 'contact_damage': (1, 30),
              'encounter_count': (16, 24), 'first_trigger_x': (120, 1200),
              'spacing': (120, 240), 'max_active': (1, 5)}
    for key, (low, high) in bounds.items():
        if type(value.get(key)) is not int or not low <= value[key] <= high:
            return None
    warning = value.get('telegraph_seconds')
    if isinstance(warning, bool) or not isinstance(warning, (float, int)) or not math.isfinite(warning) or not 0.8 <= warning <= 3:
        return None
    if value['first_trigger_x'] + (value['encounter_count'] - 1) * value['spacing'] > 3500:
        return None
    return value


class PlanetThreat(Enemy):
    """A local Core obstruction; all hits and rewards use the shared enemy base."""

    def __init__(self, target_id, x, y, spec, *, custom_body=False):
        cfg = EnemyConfig(id='core_recon_drone', name=spec['name'], max_health=spec['health'],
                          width=40, height=24, patrol_speed=24, detection_range=225,
                          windup_time=spec['telegraph_seconds'], recovery_time=.7,
                          attack_cooldown=2.8, contact_damage=spec['contact_damage'],
                          telegraph_color=(255, 186, 72), projectile_damage=spec['contact_damage'],
                          projectile_speed=190, pounce_speed=135, attack_duration=.7)
        super().__init__(target_id, x, y, cfg, x - 20, x + 20)
        self.style = spec['style']
        self.suppress_default_sprite = custom_body
        self._attack_hit = False
        self._start_y = y
        # Hover is a patrol motion. Keep its phase fixed during attacks,
        # damage, stun and recovery so resuming patrol cannot jump in y.
        self.hover_phase = 0.0

    def reset_to_spawn(self):
        super().reset_to_spawn()
        self._attack_hit = False
        self.hover_phase = 0.0

    def update(self, dt, player, room, manager, is_paused=False, decoy=None):
        if is_paused or dt <= 0:
            return
        super().update(dt)
        self.anim_time += dt
        self.cooldown_timer = max(0, self.cooldown_timer - dt)
        if self.state == STATE_DEATH:
            self.state_timer = max(0, self.state_timer - dt)
            return
        if self.has_status('stun'):
            self.telegraph_active = False
            return
        if self.state in (STATE_HURT, STATE_RECOVERY):
            self.telegraph_active = False
            self.state_timer = max(0, self.state_timer - dt)
            if self.state_timer <= 0:
                self.state = STATE_PATROL
            return
        target = decoy if decoy and not getattr(decoy, 'is_dead', False) else player
        if self.state == STATE_PATROL:
            self.telegraph_active = False
            self.vx = self.cfg.patrol_speed if self.facing == 'right' else -self.cfg.patrol_speed
            self.step_patrol(dt, room)
            if self.x <= self.patrol_left:
                self.facing = 'right'
            elif self.x >= self.patrol_right:
                self.facing = 'left'
            if self.style == 'swoop':
                self.hover_phase += dt * 2
                self.y = self._start_y - 6 - 5 * math.sin(self.hover_phase)
            if self.cooldown_timer <= 0 and self.check_line_of_sight(target, room):
                self.state = STATE_WINDUP
                self.state_timer = self.cfg.windup_time
                self.target_aim_pos = target.rect.center
                self.telegraph_active = True
        elif self.state == STATE_WINDUP:
            self.state_timer = max(0, self.state_timer - dt)
            tx, ty = target.rect.center
            self.target_aim_pos = (tx, ty)
            self.facing = 'left' if tx < self.rect.centerx else 'right'
            if not self.check_line_of_sight(target, room):
                self.state, self.telegraph_active, self.cooldown_timer = STATE_PATROL, False, .5
            elif self.state_timer <= 0:
                self.telegraph_active = False
                if self.style in ('lunge', 'swoop'):
                    self.state, self.state_timer, self._attack_hit = STATE_ATTACK, .65, False
                    self.vx = -self.cfg.pounce_speed if self.facing == 'left' else self.cfg.pounce_speed
                else:
                    ex, ey = self.rect.center
                    dx, dy = tx - ex, ty - ey
                    length = math.hypot(dx, dy) or 1
                    manager.spawn_enemy_projectile(ex, ey, dx / length, dy / length,
                                                   self.cfg.projectile_speed if self.style == 'strafe' else 145,
                                                   self.cfg.projectile_damage, self.target_id,
                                                   color=(255, 190, 72), length=8, thickness=2)
                    self.state, self.state_timer = STATE_RECOVERY, self.cfg.recovery_time
                    self.cooldown_timer = self.cfg.attack_cooldown
        elif self.state == STATE_ATTACK:
            self.state_timer = max(0, self.state_timer - dt)
            proposed = self.x + self.vx * dt
            rect = pygame.Rect(round(proposed), round(self.y), self.cfg.width, self.cfg.height)
            collision = room.check_rect_collision(rect)
            if not collision['solid'] and not collision['hazard'] and 0 <= rect.left and rect.right <= room.width_px:
                self.x = proposed
            self.rect.topleft = (round(self.x), round(self.y))
            if not self._attack_hit and self.rect.colliderect(player.rect):
                player.take_damage(self.cfg.contact_damage, knockback_vx=self.vx * .3,
                                   knockback_vy=-80, damage_source='hostile')
                self._attack_hit = True
            if self.state_timer <= 0:
                self.state, self.state_timer = STATE_RECOVERY, self.cfg.recovery_time
                self.cooldown_timer = self.cfg.attack_cooldown
        self.rect.topleft = (round(self.x), round(self.y))


class PlanetEncounter:
    """Monotonic, bounded spawns: nothing is persisted to campaign state."""

    def __init__(self, room, manager, world_id, assisted=False, *, body=None, data_path=DATA_PATH):
        self.room, self.manager, self.assisted = room, manager, assisted
        self.spec = world_config(world_id, data_path)
        self.body = body
        self.next_trigger = 0
        self.pending = []
        self.warning = None
        self.warning_time = 0.0
        self.high_water = -1.0
        self.retired_last_update = 0
        self.entries = [] if not self.spec else [
            {'id': f"{self.spec['enemy_id']}_{i+1:02}", 'trigger_x': self.spec['first_trigger_x'] + i * self.spec['spacing']}
            for i in range(self.spec['encounter_count'])]
        # Authored threat bodies face right. Cache the mirror and both hit
        # variants once; reflecting native x=48 across 96 pixels yields x=47.
        self.body_left = None
        self.hurt_body = None
        self.hurt_body_left = None
        if body is not None:
            self.body_left = pygame.transform.flip(body, True, False)
            self.hurt_body = body.copy()
            self.hurt_body.fill((255, 175, 130, 255), special_flags=pygame.BLEND_RGBA_MULT)
            self.hurt_body_left = pygame.transform.flip(self.hurt_body, True, False)

    def _safe(self, x):
        rect = pygame.Rect(x, 216, 40, 24)
        if not pygame.Rect(0, 0, self.room.width_px, self.room.height_px).contains(rect.inflate(8, 0)):
            return False
        collision = self.room.check_rect_collision(rect.inflate(8, 0))
        if collision['solid'] or collision['hazard'] or collision['one_way']:
            return False
        return all(self.room.get_tile(c, 15) in (COLLISION_SOLID, COLLISION_ONE_WAY)
                   for c in range(rect.left // 16, (rect.right - 1) // 16 + 1))

    def update(self, dt, player, paused=False, camera=None):
        self.retired_last_update = 0
        if paused or dt <= 0 or player.is_dead or self.spec is None:
            return
        if camera is not None:
            retired = {e.target_id for e in self.manager.enemies if isinstance(e, PlanetThreat)
                       and not e.is_dead and e.rect.right < camera.x - 32 and e.rect.right < player.rect.left - 160}
            if retired:
                self.manager.enemies[:] = [e for e in self.manager.enemies if e.target_id not in retired]
                self.manager.projectiles[:] = [p for p in self.manager.projectiles if p.source_id not in retired]
                self.retired_last_update = len(retired)
        self.high_water = max(self.high_water, player.rect.centerx)
        while self.next_trigger < len(self.entries) and self.entries[self.next_trigger]['trigger_x'] <= self.high_water:
            self.pending.append(self.entries[self.next_trigger])
            self.next_trigger += 1
        if sum(not e.is_dead for e in self.manager.enemies) >= self.spec['max_active']:
            self.warning, self.warning_time = None, 0.0
            return
        if self.warning is None and self.pending:
            # Allow for the warning time while the player runs, then retain 120px.
            run_speed = max(0.0, float(getattr(getattr(player, 'cfg', None), 'run_speed', 180.0)))
            lead = MIN_CLEARANCE + run_speed * self.spec['telegraph_seconds'] + 32
            x = int(math.ceil(max(self.pending[0]['trigger_x'] + lead, player.rect.right + lead) / 16) * 16)
            while x < self.room.width_px - 48 and not self._safe(x):
                x += 16
            if self._safe(x):
                self.warning = {'entry': self.pending[0], 'x': x}
                self.warning_time = 0
        if self.warning is None:
            return
        x = self.warning['x']
        occupied = any(not e.is_dead and e.rect.inflate(48, 32).colliderect(pygame.Rect(x, 216, 40, 24)) for e in self.manager.enemies)
        if x - player.rect.right < MIN_CLEARANCE or occupied:
            self.warning, self.warning_time = None, 0.0
            return
        self.warning_time += min(dt, .1)
        if self.warning_time < self.spec['telegraph_seconds']:
            return
        enemy = PlanetThreat(self.warning['entry']['id'], x, 216, self.spec, custom_body=self.body is not None)
        self.manager.add_enemy(enemy)
        self.pending.remove(self.warning['entry'])
        self.warning, self.warning_time = None, 0.0
        return enemy

    def render(self, crt, camera):
        if self.warning:
            x, y = camera.world_to_screen(self.warning['x'], 216)
            x = max(8, min(camera.viewport_w - 56, x))
            crt.draw_text('INCOMING', int(x), int(y) - 14, color=(255, 190, 65), size='sm')
        if self.body is None:
            return
        layers = []
        for enemy in self.manager.enemies:
            if not isinstance(enemy, PlanetThreat) or (enemy.is_dead and enemy.state_timer <= 0):
                continue
            x, y = camera.world_to_screen(enemy.rect.centerx, enemy.rect.bottom)
            left = enemy.facing == 'left'
            if enemy.state == STATE_HURT:
                image = self.hurt_body_left if left else self.hurt_body
            else:
                image = self.body_left if left else self.body
            layers.append((image, (2 * x - (47 if left else 48), 2 * y - 64), 0))
        if layers:
            crt.composite_native_effects(layers)
