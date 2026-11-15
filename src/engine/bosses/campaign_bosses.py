"""PURPOSE: Distinct later-act encounters using the shared boss combat lifecycle.
CALLED BY: video_game.engine.scenes.boss.
HOW TO MODIFY: Keep attack warnings visible, counters achievable, and retries deterministic.
"""
import math
import pygame
from ..attack_visuals import render_attack_field, render_aim_warning, render_boss_projectile
from ..core_network import render_projection_scan

from .base import (Boss, BossAttackTelegraph, BossProjectile, boss_balance, STATE_TRANSITION,
                   STATE_TELEGRAPH, STATE_ATTACK, STATE_RECOVERY)

# A 128px body stays inside both edge views of the 640px arenas (480px camera).
TELEPORT_POSITIONS = (180, 265, 350)


class CampaignBoss(Boss):
    event_type = ''
    color = (100, 210, 240)
    attack_name = 'PULSE'

    def __init__(self, boss_id, title, health=None):
        self.tuning = boss_balance()
        if health is None:
            health = self.tuning['health'][boss_id]
        super().__init__(boss_id, 330, 144, 128, 96, health, title, self.attack_name)
        self.reset_to_pristine()

    @property
    def mortar_muzzle(self):
        return self._muzzle_at(self.rect.center, self.facing)

    def _muzzle_at(self, center, facing):
        dx, dy = self.tuning['muzzle_offsets'].get(self.target_id, (0, 0))
        return (center[0] + (-dx if facing == 'right' else dx), center[1] + dy)

    def reset_to_pristine(self):
        super().reset_to_pristine()
        self.cooldown = self.tuning['first_attack_delay']
        self.attack_timer = 0.0
        self.attack_index = 0
        self.attack_rects = []
        self.animation_time = 0.0
        self.hit_flash_timer = 0.0
        self._flash_source = None
        self._flash_surface = None
        self._art_variants = None
        self._update_weak_point()

    def _update_weak_point(self):
        self.weak_point_rect = pygame.Rect(0, 0, 30, 24)
        dx, dy = self.tuning['weak_point_offsets'].get(self.target_id, (0, 0))
        self.weak_point_rect.center = (self.rect.centerx + (-dx if self.facing == 'right' else dx), self.rect.centery + dy)
        self.weak_point_exposed = self.phase_state == STATE_RECOVERY

    def trigger_transition(self, target_phase):
        super().trigger_transition(target_phase)
        self.attack_rects.clear()
        self.cooldown = self.tuning['first_attack_delay']
        if self.target_id == 'core_prime' and target_phase >= 3:
            self.title = 'ARCHON OF SILENCE'

    def apply_defeat_reward(self, campaign):
        if not self.is_defeated or self.defeat_reward_granted:
            return False
        applied = campaign.apply_event({'event_id': f'{self.event_type}_{campaign.state.save_id}', 'type': self.event_type})
        self.defeat_reward_granted = applied
        return applied

    def take_damage(self, *args, **kwargs):
        result = super().take_damage(*args, **kwargs)
        if result.damage_dealt > 0:
            self.hit_flash_timer = 0.12
        return result

    def update(self, dt, player_pos=(120, 208)):
        if dt <= 0 or not math.isfinite(dt):
            return
        self.face_target(player_pos)
        self._track_aim_warning(player_pos)
        super().update(dt)
        self.animation_time += dt
        self.hit_flash_timer = max(0.0, self.hit_flash_timer - dt)
        if self.is_dead or self.phase_state == STATE_TRANSITION:
            self._update_weak_point()
            return
        if self.phase_state == STATE_TELEGRAPH:
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.phase_state = STATE_ATTACK
                self.attack_timer = 0.45
                self.fire(player_pos)
        elif self.phase_state == STATE_ATTACK:
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.attack_rects.clear()
                self.phase_state = STATE_RECOVERY
                self.cooldown = self.tuning['recovery_seconds'][self.current_phase - 1]
        else:
            self.cooldown -= dt
            if self.cooldown <= 0:
                self.attack_index += 1
                self.prepare(player_pos)
                self.phase_state = STATE_TELEGRAPH
                self.attack_timer = 1.25
        self.face_target(player_pos)  # Teleport attacks may have crossed the target.
        self._update_weak_point()

    def prepare(self, player_pos):
        raise NotImplementedError

    def fire(self, player_pos):
        pass

    def _warn_aim(self, player_pos, duration=1.25):
        self.telegraphs.append(BossAttackTelegraph('aim', duration))
        self._track_aim_warning(player_pos)

    def _track_aim_warning(self, player_pos):
        if not any(t.attack_type == 'aim' for t in self.telegraphs):
            return
        origin = self.rect.center
        if getattr(self, 'pattern', '').startswith('teleport'):
            origin = (self.pending_x + self.width / 2, self.rect.centery)
        elif self.target_id == 'amalgam' and hasattr(self, 'pending_x'):
            origin = (self.pending_x + self.width / 2, self.rect.centery)
        dx = player_pos[0] - origin[0]
        facing = ('right' if dx > 0 else 'left') if abs(dx) > 3 else self.facing
        origin = self._muzzle_at(origin, facing)
        for warning in self.telegraphs:
            if warning.attack_type == 'aim':
                warning.target_line = (origin, player_pos)

    def _fire_volley(self, player_pos, proj_id, speed, spread=(0,)):
        """Aim at release, after any teleport; released shots keep their course."""
        self.face_target(player_pos)
        origin = self.mortar_muzzle
        dx, dy = player_pos[0] - origin[0], player_pos[1] - origin[1]
        angle = math.atan2(dy, dx) if math.hypot(dx, dy) > .001 else (0 if self.facing == 'right' else math.pi)
        for offset in spread:
            theta = angle + math.radians(offset)
            self.projectiles.append(BossProjectile(
                f'{proj_id}_{offset}', *origin, speed * math.cos(theta), speed * math.sin(theta),
                damage=12, color=self.color))

    def check_attack_collisions(self, player_rect):
        for projectile in self.projectiles:
            if projectile.check_player_collision(player_rect):
                projectile.is_active = False
                return projectile.damage
        if self.phase_state == STATE_ATTACK and any(r.colliderect(player_rect) for r in self.attack_rects):
            return 12
        return 0

    def render(self, surface, camera, *, crt=None):
        for telegraph in self.telegraphs:
            if telegraph.target_line:
                start, end = telegraph.target_line
                render_aim_warning(surface, camera.world_to_screen(*start), camera.world_to_screen(*end),
                                   progress=telegraph.progress, color=self.color)
            if telegraph.target_rect:
                r = telegraph.target_rect.move(-int(camera.x), -int(camera.y))
                render_attack_field(surface, r, color=self.color, progress=telegraph.progress,
                                    time=self.animation_time,
                                    arrival=telegraph.attack_type in ('pod', 'teleport', 'teleport_fan'))
        for r in self.attack_rects:
            render_attack_field(surface, r.move(-int(camera.x), -int(camera.y)),
                                color=self.color, time=self.animation_time, active=True)
        r = self.rect.move(-int(camera.x), -int(camera.y))
        art = getattr(self, 'art_surface', None)
        if art is not None and art is not self._flash_source:
            self._flash_source = art
            mirror = pygame.transform.flip(art, True, False)
            flashes = []
            for image in (art, mirror):
                flash = image.copy()
                flash.fill((*self.color, 0), special_flags=pygame.BLEND_RGB_ADD)
                flashes.append(flash)
            self._art_variants = (art, mirror)
            self._flash_variants = tuple(flashes)
            self._logical_variants = tuple(pygame.transform.scale(image, (128, 96)) for image in (art, mirror))
        if art is not None:
            side = int(self.facing == 'right')
            art = self._art_variants[side]
            self._flash_surface = self._flash_variants[side]
        if art is not None and crt is not None:
            crt.composite_native(art, (r.centerx - 64, r.bottom - 96), (128, 96))
            if self.hit_flash_timer > 0:
                self._flash_surface.set_alpha(round(150 * self.hit_flash_timer / 0.12))
                crt.composite_native(self._flash_surface, (r.centerx - 64, r.bottom - 96), (128, 96))
        elif art is not None:
            surface.blit(self._logical_variants[side], (r.centerx - 64, r.bottom - 96))
        else:
            self.draw_body(surface, r)
        # Keep discharges above the native body, using their actual launch vector.
        for p in self.projectiles:
            render_boss_projectile(surface, p, camera)
        if self.weak_point_exposed:
            core = self.weak_point_rect.move(-int(camera.x), -int(camera.y))
            pygame.draw.ellipse(surface, (255, 218, 124), core, 2)
            pygame.draw.circle(surface, (255, 245, 196), core.center,
                               3 + round(1 + math.sin(self.animation_time * 9)))

    def draw_body(self, surface, r):
        pygame.draw.rect(surface, self.color, r, 3)
        pygame.draw.circle(surface, (255, 245, 170), r.center, 9)


class Synchronicity(CampaignBoss):
    event_type = 'defeat_synchronicity'
    attack_name = 'DISH SWEEP'
    color = (110, 200, 240)

    def __init__(self):
        super().__init__('synchronicity', 'SYNCHRONICITY ARRAY')

    def prepare(self, player_pos):
        # Alternating ground/high lanes leave an obvious standing or jumping counter.
        y = 208 if self.attack_index % 2 else 150
        self.pending_lane = pygame.Rect(80, y, 345, 20)
        self.telegraphs.append(BossAttackTelegraph('dish_lane', 1.25, target_rect=self.pending_lane))

    def fire(self, player_pos):
        self.attack_rects = [self.pending_lane]

    def draw_body(self, surface, r):
        pygame.draw.circle(surface, self.color, r.center, 42, 4)
        pygame.draw.line(surface, self.color, r.topleft, r.bottomright, 4)
        pygame.draw.line(surface, self.color, r.topright, r.bottomleft, 4)
        pygame.draw.circle(surface, (255, 240, 150), r.center, 10)


class Amalgam(CampaignBoss):
    event_type = 'defeat_amalgam'
    attack_name = 'POD STRIKE'
    color = (200, 100, 180)

    def __init__(self):
        super().__init__('amalgam', 'THE AMALGAM')

    def prepare(self, player_pos):
        self.pending_x = TELEPORT_POSITIONS[self.attack_index % len(TELEPORT_POSITIONS)]
        self.telegraphs.append(BossAttackTelegraph('pod', 1.25, target_rect=pygame.Rect(self.pending_x, 144, self.width, self.height)))
        self._warn_aim(player_pos)

    def fire(self, player_pos):
        self.x = self.pending_x
        self.rect.x = int(self.x)
        self._fire_volley(player_pos, 'pod_spore', self.tuning['amalgam_projectile_speed'])

    def draw_body(self, surface, r):
        pygame.draw.ellipse(surface, self.color, r, 4)
        for x in (r.x + 25, r.x + 48, r.x + 71):
            pygame.draw.circle(surface, (255, 200, 220), (x, r.centery), 7)


class MandelaArchitect(CampaignBoss):
    event_type = 'defeat_architect'
    attack_name = 'REALITY LANES'
    color = (120, 220, 170)

    def __init__(self):
        super().__init__('architect', 'MANDELA ARCHITECT')

    def prepare(self, player_pos):
        # Three alternate vertical sectors, one remains safe between them.
        x = (100, 230, 360)[self.attack_index % 3]
        self.pending_lane = pygame.Rect(x, 145, 65, 95)
        self.telegraphs.append(BossAttackTelegraph('reality_lane', 1.25, target_rect=self.pending_lane))

    def fire(self, player_pos):
        self.attack_rects = [self.pending_lane]

    def draw_body(self, surface, r):
        pygame.draw.polygon(surface, self.color, [r.midtop, r.midright, r.midbottom, r.midleft], 4)
        pygame.draw.rect(surface, (245, 255, 180), r.inflate(-65, -65), 2)


class CorePrime(CampaignBoss):
    event_type = 'defeat_core_prime'
    attack_name = 'CORE PULSE'
    color = (240, 120, 90)

    def __init__(self):
        super().__init__('core_prime', 'CORE PRIME')

    def prepare(self, player_pos):
        # The final third becomes Archon and exchanges the floor wave for aimed bolts.
        if self.current_phase >= 3:
            self.title = 'ARCHON OF SILENCE'
            self.pending_lane = pygame.Rect(max(80, min(370, int(player_pos[0]) - 20)), 160, 40, 80)
        else:
            self.pending_lane = pygame.Rect(80, 210, 345, 20)
        self.telegraphs.append(BossAttackTelegraph('core_pulse', 1.25, target_rect=self.pending_lane))
        if self.current_phase >= 3:
            self._warn_aim(player_pos)

    def fire(self, player_pos):
        self.attack_rects = [self.pending_lane]
        if self.current_phase >= 3:
            spread = self.tuning['archon_fan_degrees']
            self._fire_volley(player_pos, 'archon_bolt', self.tuning['archon_projectile_speed'], (-spread, spread))

    def reset_to_pristine(self):
        super().reset_to_pristine()
        self.title = 'CORE PRIME'

    def draw_body(self, surface, r):
        pygame.draw.polygon(surface, self.color, [r.midtop, r.topright, r.midbottom, r.topleft], 4)
        pygame.draw.circle(surface, (255, 245, 190), r.center, 12 if self.current_phase < 3 else 20, 3)


BOSSES = {'synchronicity': Synchronicity, 'amalgam': Amalgam,
          'architect': MandelaArchitect, 'mandela_architect': MandelaArchitect, 'core_prime': CorePrime}


class PortalWarden(MandelaArchitect):
    """Earth's Göbekli gatekeeper, separate from the AI encountered at the end."""
    event_type = 'defeat_portal_warden'
    color = (210, 175, 110)

    def __init__(self):
        CampaignBoss.__init__(self, 'portal_warden', 'GOBEKLI PORTAL WARDEN')


class EarthFinalAI(CorePrime):
    """Core Prime reforms as the Archon with a separate full health bar."""
    event_type = 'defeat_earth_ai'
    color = (88, 235, 150)

    def reset_to_pristine(self):
        super().reset_to_pristine()
        self.final_stage = 1

    def trigger_transition(self, target_phase):
        # Core Prime retains its identity through its own three health phases.
        Boss.trigger_transition(self, target_phase)
        self.attack_rects.clear()
        self.cooldown = self.tuning['first_attack_delay']

    def trigger_defeat(self):
        if self.final_stage == 1:
            self.final_stage = 2
            self.health = self.max_health
            self.title = 'ARCHON OF SILENCE'
            self.attack_rects.clear()
            self.cooldown = self.tuning['first_attack_delay']
            Boss.trigger_transition(self, 3)
        else:
            super().trigger_defeat()

    def take_damage(self, *args, **kwargs):
        result = super().take_damage(*args, **kwargs)
        if result.target_killed and not self.is_defeated:
            result.target_killed = False
        return result

    def render(self, surface, camera, *, crt=None):
        super().render(surface, camera, crt=crt)
        render_projection_scan(surface, self, camera)

    def prepare(self, player_pos):
        if self.final_stage == 1:
            self.pending_lane = pygame.Rect(80, 210, 345, 20)
            self.telegraphs.append(BossAttackTelegraph('core_pulse', 1.25, target_rect=self.pending_lane))
        else:
            super().prepare(player_pos)

    def fire(self, player_pos):
        if self.final_stage == 1:
            self.attack_rects = [self.pending_lane]
        else:
            super().fire(player_pos)


# Each guardian has its own silhouette, attack rhythm and mixture of threats.
# They share the existing readable telegraph and projectile lifecycle.
GUARDIAN_PATTERNS = {
    'guardian_fasr_008': ((245, 200, 110), 'fan', 0, 1.20),
    'guardian_fasr_009': ((140, 195, 240), 'lance', 1, 1.15),
    'guardian_fasr_006': ((235, 178, 100), 'teleport', 2, 1.40),
    'guardian_fasr_002': ((185, 220, 255), 'teleport_fan', 3, 1.25),
    'guardian_fasr_scan_h': ((180, 220, 202), 'paired_columns', 4, 1.40),
    'guardian_fasr_010': ((230, 185, 95), 'alternating', 5, 1.30),
    'guardian_fasr_007': ((215, 145, 235), 'pulse_fan', 6, 1.20),
}


class AlienGuardian(CampaignBoss):
    """A world's guardian; all attacks leave visible safe space and use starter weapons."""
    def __init__(self, world):
        self.world = world
        self.event_type = world['defeat_event']
        self.color, self.pattern, self.silhouette, self.warning_seconds = GUARDIAN_PATTERNS[world['boss_id']]
        title = world.get('guardian_title', world.get('title', 'ALIEN GUARDIAN'))
        tuning = boss_balance()
        health = tuning['guardian_base_health'] + tuning['guardian_health_per_world'] * self.silhouette
        super().__init__(world['boss_id'], title.upper(), health)

    def update(self, dt, player_pos=(120, 208)):
        # Base's common 1.25s warning is adjusted by each guardian after creation.
        was_idle = self.phase_state not in (STATE_TELEGRAPH, STATE_ATTACK)
        super().update(dt, player_pos)
        if was_idle and self.phase_state == STATE_TELEGRAPH:
            self.attack_timer = self.warning_seconds
            if self.telegraphs:
                self.telegraphs[-1].duration = self.warning_seconds
                self.telegraphs[-1].timer = self.warning_seconds

    def prepare(self, player_pos):
        self.pending_lane = None
        self.pending_x = TELEPORT_POSITIONS[self.attack_index % len(TELEPORT_POSITIONS)]
        if self.pattern in ('columns', 'paired_columns'):
            x = (110, 235, 360)[self.attack_index % 3]
            self.pending_lane = pygame.Rect(x, 150, 55, 90)
        elif self.pattern in ('lanes', 'alternating', 'pulse_fan', 'crossfire'):
            y = 208 if self.attack_index % 2 else 145
            self.pending_lane = pygame.Rect(80, y, 335, 20)
        elif self.pattern.startswith('teleport'):
            self.pending_lane = pygame.Rect(self.pending_x, 144, self.width, self.height)
        else:
            self.pending_lane = None
        if self.pending_lane is not None:
            self.telegraphs.append(BossAttackTelegraph(self.pattern, self.warning_seconds, target_rect=self.pending_lane))
        if self.pattern in ('volley', 'fan', 'lance', 'teleport', 'teleport_fan', 'crossfire', 'pulse_fan'):
            self._warn_aim(player_pos, self.warning_seconds)
        if self.pattern == 'paired_columns':
            x = 110 if self.pending_lane.x != 110 else 360
            self.pending_secondary_lane = pygame.Rect(x, 150, 55, 90)
            self.telegraphs.append(BossAttackTelegraph(self.pattern, self.warning_seconds,
                                                       target_rect=self.pending_secondary_lane))

    def fire(self, player_pos):
        pattern = self.pattern
        if pattern in ('teleport', 'teleport_fan'):
            self.x = self.pending_x
            self.rect.x = int(self.x)
        if pattern in ('lanes', 'alternating', 'columns', 'crossfire', 'pulse_fan', 'paired_columns'):
            self.attack_rects = [self.pending_lane]
            if pattern == 'paired_columns':
                self.attack_rects.append(self.pending_secondary_lane)
        if pattern in ('volley', 'fan', 'lance', 'teleport', 'teleport_fan', 'crossfire', 'pulse_fan'):
            spread = self.tuning['guardian_fan_degrees']
            offsets = (-spread, 0, spread) if pattern in ('fan', 'teleport_fan', 'pulse_fan') else (0,)
            self._fire_volley(player_pos, pattern, self.tuning['guardian_projectile_speed'], offsets)

    def draw_body(self, surface, r):
        # The diagnostic fallback remains distinct when optional body art is absent.
        shape = self.silhouette % 4
        if shape == 0:
            pygame.draw.ellipse(surface, self.color, r.inflate(-8, -8), 4)
        elif shape == 1:
            pygame.draw.polygon(surface, self.color, [r.midtop, r.topright, r.midbottom, r.topleft], 4)
        elif shape == 2:
            pygame.draw.rect(surface, self.color, r.inflate(-16, -8), 4, border_radius=8)
        else:
            pygame.draw.polygon(surface, self.color, [r.midtop, r.midright, r.midbottom, r.midleft], 4)
        for i in range(1 + self.silhouette % 3):
            pygame.draw.circle(surface, (255, 245, 190), (r.centerx + (i - 1) * 16, r.centery), 6, 2)
