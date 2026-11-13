"""PURPOSE: Distinct later-act encounters using the shared boss combat lifecycle.
CALLED BY: video_game.engine.scenes.boss.
HOW TO MODIFY: Keep attack warnings visible, counters achievable, and retries deterministic.
"""
import math
import pygame

from .base import (Boss, BossAttackTelegraph, BossProjectile, STATE_TRANSITION,
                   STATE_TELEGRAPH, STATE_ATTACK, STATE_RECOVERY)


class CampaignBoss(Boss):
    event_type = ''
    color = (100, 210, 240)
    attack_name = 'PULSE'

    def __init__(self, boss_id, title, health=300):
        super().__init__(boss_id, 330, 144, 128, 96, health, title, self.attack_name)
        self.reset_to_pristine()

    @property
    def mortar_muzzle(self):
        return self.rect.center

    def reset_to_pristine(self):
        super().reset_to_pristine()
        self.cooldown = 1.5
        self.attack_timer = 0.0
        self.attack_index = 0
        self.attack_rects = []
        self.weak_point_rect = self.rect.copy()
        self.weak_point_exposed = True

    def trigger_transition(self, target_phase):
        super().trigger_transition(target_phase)
        self.attack_rects.clear()
        self.cooldown = 1.5
        if self.target_id == 'core_prime' and target_phase >= 3:
            self.title = 'ARCHON OF SILENCE'

    def apply_defeat_reward(self, campaign):
        if not self.is_defeated or self.defeat_reward_granted:
            return False
        applied = campaign.apply_event({'event_id': f'{self.event_type}_{campaign.state.save_id}', 'type': self.event_type})
        self.defeat_reward_granted = applied
        return applied

    def update(self, dt, player_pos=(120, 208)):
        super().update(dt)
        if self.is_dead or self.phase_state == STATE_TRANSITION:
            return
        self.weak_point_exposed = True
        self.weak_point_rect = self.rect.copy()
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
                self.cooldown = 1.7
        else:
            self.cooldown -= dt
            if self.cooldown <= 0:
                self.attack_index += 1
                self.prepare(player_pos)
                self.phase_state = STATE_TELEGRAPH
                self.attack_timer = 1.25

    def prepare(self, player_pos):
        raise NotImplementedError

    def fire(self, player_pos):
        pass

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
            if telegraph.target_rect:
                r = telegraph.target_rect.move(-int(camera.x), -int(camera.y))
                pygame.draw.rect(surface, (255, 190, 65), r, 2)
        for r in self.attack_rects:
            pygame.draw.rect(surface, (255, 90, 65), r.move(-int(camera.x), -int(camera.y)))
        for p in self.projectiles:
            pygame.draw.circle(surface, p.color, camera.world_to_screen(p.x, p.y), int(p.radius))
        r = self.rect.move(-int(camera.x), -int(camera.y))
        art = getattr(self, 'art_surface', None)
        if art is not None and crt is not None:
            crt.composite_native(art, (r.centerx - 64, r.bottom - 96), (128, 96))
        elif art is not None:
            surface.blit(pygame.transform.smoothscale(art, (128, 96)), (r.centerx - 64, r.bottom - 96))
        else:
            self.draw_body(surface, r)

    def draw_body(self, surface, r):
        pygame.draw.rect(surface, self.color, r, 3)
        pygame.draw.circle(surface, (255, 245, 170), r.center, 9)


class Synchronicity(CampaignBoss):
    event_type = 'defeat_synchronicity'
    attack_name = 'DISH SWEEP'
    color = (110, 200, 240)

    def __init__(self):
        super().__init__('synchronicity', 'SYNCHRONICITY ARRAY', 270)

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
        super().__init__('amalgam', 'THE AMALGAM', 300)

    def prepare(self, player_pos):
        self.pending_x = (360, 440, 510)[self.attack_index % 3]
        self.telegraphs.append(BossAttackTelegraph('pod', 1.25, target_rect=pygame.Rect(self.pending_x, 144, self.width, self.height)))

    def fire(self, player_pos):
        self.x = self.pending_x
        self.rect.x = int(self.x)
        dx, dy = player_pos[0] - self.rect.centerx, player_pos[1] - self.rect.centery
        length = max(1, math.hypot(dx, dy))
        self.projectiles.append(BossProjectile('pod_spore', *self.rect.center, 130 * dx / length, 130 * dy / length, damage=12, color=self.color))

    def draw_body(self, surface, r):
        pygame.draw.ellipse(surface, self.color, r, 4)
        for x in (r.x + 25, r.x + 48, r.x + 71):
            pygame.draw.circle(surface, (255, 200, 220), (x, r.centery), 7)


class MandelaArchitect(CampaignBoss):
    event_type = 'defeat_architect'
    attack_name = 'REALITY LANES'
    color = (120, 220, 170)

    def __init__(self):
        super().__init__('architect', 'MANDELA ARCHITECT', 300)

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
        super().__init__('core_prime', 'CORE PRIME', 390)

    def prepare(self, player_pos):
        # The final third becomes Archon and exchanges the floor wave for aimed bolts.
        if self.current_phase >= 3:
            self.title = 'ARCHON OF SILENCE'
            self.pending_lane = pygame.Rect(max(80, min(370, int(player_pos[0]) - 20)), 160, 40, 80)
        else:
            self.pending_lane = pygame.Rect(80, 210, 345, 20)
        self.telegraphs.append(BossAttackTelegraph('core_pulse', 1.25, target_rect=self.pending_lane))

    def fire(self, player_pos):
        self.attack_rects = [self.pending_lane]
        if self.current_phase >= 3:
            for vy in (-45, 45):
                self.projectiles.append(BossProjectile('archon_bolt', *self.rect.center, -115, vy, damage=12, color=self.color))

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
        CampaignBoss.__init__(self, 'portal_warden', 'GOBEKLI PORTAL WARDEN', 300)


class EarthFinalAI(CorePrime):
    """Core Prime reforms as the Archon with a separate full health bar."""
    event_type = 'defeat_earth_ai'

    def reset_to_pristine(self):
        super().reset_to_pristine()
        self.final_stage = 1

    def trigger_transition(self, target_phase):
        # Core Prime retains its identity through its own three health phases.
        Boss.trigger_transition(self, target_phase)
        self.attack_rects.clear()
        self.cooldown = 1.5

    def trigger_defeat(self):
        if self.final_stage == 1:
            self.final_stage = 2
            self.health = self.max_health
            self.title = 'ARCHON OF SILENCE'
            self.attack_rects.clear()
            self.cooldown = 1.5
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
        if self.final_stage == 2 and not self.is_defeated:
            outline = self.rect.move(-int(camera.x), -int(camera.y)).inflate(8, 8)
            pygame.draw.ellipse(surface, (200, 115, 245), outline, 2)

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
    'guardian_fasr_001': ((100, 220, 245), 'lanes', 0, 1.25),
    'guardian_fasr_003': ((240, 125, 95), 'volley', 1, 1.10),
    'guardian_fasr_005': ((170, 230, 135), 'columns', 2, 1.35),
    'guardian_fasr_004': ((195, 130, 245), 'crossfire', 3, 1.30),
    'guardian_fasr_008': ((245, 200, 110), 'fan', 4, 1.20),
    'guardian_fasr_009': ((140, 195, 240), 'lance', 5, 1.15),
    'guardian_fasr_006': ((210, 180, 135), 'teleport', 6, 1.40),
    'guardian_fasr_002': ((150, 245, 215), 'teleport_fan', 7, 1.25),
    'guardian_fasr_scan_h': ((245, 215, 145), 'paired_columns', 8, 1.40),
    'guardian_fasr_010': ((145, 210, 150), 'alternating', 9, 1.30),
    'guardian_fasr_007': ((240, 115, 150), 'pulse_fan', 10, 1.20),
}


class AlienGuardian(CampaignBoss):
    """A world's guardian; all attacks leave visible safe space and use starter weapons."""
    def __init__(self, world):
        self.world = world
        self.event_type = world['defeat_event']
        self.color, self.pattern, self.silhouette, self.warning_seconds = GUARDIAN_PATTERNS[world['boss_id']]
        title = world.get('guardian_title', world.get('title', 'ALIEN GUARDIAN'))
        super().__init__(world['boss_id'], title.upper(), 270 + 15 * (self.silhouette % 3))

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
        self.pending_x = (345, 420, 495)[self.attack_index % 3]
        if self.pattern in ('columns', 'paired_columns'):
            x = (110, 235, 360)[self.attack_index % 3]
            self.pending_lane = pygame.Rect(x, 150, 55, 90)
        elif self.pattern in ('lanes', 'alternating', 'pulse_fan', 'crossfire'):
            y = 208 if self.attack_index % 2 else 145
            self.pending_lane = pygame.Rect(80, y, 335, 20)
        elif self.pattern.startswith('teleport'):
            self.pending_lane = pygame.Rect(self.pending_x, 144, self.width, self.height)
        else:
            # Aim line announces the projectile direction without obscuring the floor.
            self.pending_lane = pygame.Rect(100, 195 + (self.attack_index % 2) * 20, 250, 12)
        self.telegraphs.append(BossAttackTelegraph(self.pattern, self.warning_seconds, target_rect=self.pending_lane))

    def fire(self, player_pos):
        pattern = self.pattern
        if pattern in ('teleport', 'teleport_fan'):
            self.x = self.pending_x
            self.rect.x = int(self.x)
        if pattern in ('lanes', 'alternating', 'columns', 'crossfire', 'pulse_fan', 'paired_columns'):
            self.attack_rects = [self.pending_lane]
            if pattern == 'paired_columns':
                x = 110 if self.pending_lane.x != 110 else 360
                self.attack_rects.append(pygame.Rect(x, 150, 55, 90))
        if pattern in ('volley', 'fan', 'lance', 'teleport', 'teleport_fan', 'crossfire', 'pulse_fan'):
            dx, dy = player_pos[0] - self.rect.centerx, player_pos[1] - self.rect.centery
            length = max(1, math.hypot(dx, dy))
            offsets = (-35, 0, 35) if pattern in ('fan', 'teleport_fan', 'pulse_fan') else (0,)
            for offset in offsets:
                self.projectiles.append(BossProjectile(f'{pattern}_{offset}', *self.rect.center,
                                                       115 * dx / length, 115 * dy / length + offset,
                                                       damage=12, color=self.color))

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
