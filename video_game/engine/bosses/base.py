"""
# PURPOSE: Base framework for Act-culminating sector bosses, phase transitions, and arena reset mechanics.
# CALLED BY: video_game.engine.bosses.greenkeeper, video_game.engine.scenes.boss, video_game.tests.test_combat.
# HOW TO MODIFY: Inherit Boss and implement phase-specific attacks, telegraph rendering, and weak point logic.
"""

from typing import Any, Dict, List, Optional, Tuple
import pygame

from video_game.engine.weapons import CombatTarget, HitResult

# Boss phase constants
PHASE_INTRO: int = 0
PHASE_1: int = 1
PHASE_2: int = 2
PHASE_3: int = 3
PHASE_DEFEATED: int = 4

# Boss operational states
STATE_IDLE: str = "IDLE"
STATE_INTRO: str = "INTRO"
STATE_TELEGRAPH: str = "TELEGRAPH"
STATE_ATTACK: str = "ATTACK"
STATE_RECOVERY: str = "RECOVERY"
STATE_VULNERABLE: str = "VULNERABLE"
STATE_TRANSITION: str = "TRANSITION"
STATE_DEFEATED: str = "DEFEATED"


class BossAttackTelegraph:
    """Visual and spatial warning indicator preceding an active boss attack."""

    def __init__(
        self,
        attack_type: str,
        duration: float,
        target_rect: Optional[pygame.Rect] = None,
        target_line: Optional[Tuple[Tuple[float, float], Tuple[float, float]]] = None,
        radius: float = 0.0,
        center: Tuple[float, float] = (0.0, 0.0),
        color: Tuple[int, int, int] = (255, 180, 50),
    ):
        self.attack_type: str = attack_type
        self.duration: float = duration
        self.timer: float = duration
        self.target_rect: Optional[pygame.Rect] = target_rect
        self.target_line: Optional[Tuple[Tuple[float, float], Tuple[float, float]]] = target_line
        self.radius: float = radius
        self.center: Tuple[float, float] = center
        self.color: Tuple[int, int, int] = color

    @property
    def is_expired(self) -> bool:
        return self.timer <= 0.0

    @property
    def progress(self) -> float:
        """Normalized progress 0.0 (started) to 1.0 (about to strike)."""
        if self.duration <= 0.0:
            return 1.0
        return max(0.0, min(1.0, 1.0 - (self.timer / self.duration)))

    def update(self, dt: float):
        if self.timer > 0.0:
            self.timer = max(0.0, self.timer - dt)


class BossProjectile:
    """Autonomous projectile spawned by boss attacks."""

    def __init__(
        self,
        proj_id: str,
        x: float,
        y: float,
        vx: float,
        vy: float,
        radius: float = 6.0,
        damage: int = 25,
        lifetime: float = 3.0,
        color: Tuple[int, int, int] = (255, 60, 60),
    ):
        self.proj_id: str = proj_id
        self.x: float = float(x)
        self.y: float = float(y)
        self.vx: float = float(vx)
        self.vy: float = float(vy)
        self.radius: float = float(radius)
        self.damage: int = damage
        self.lifetime: float = float(lifetime)
        self.color: Tuple[int, int, int] = color
        self.is_active: bool = True

    @property
    def rect(self) -> pygame.Rect:
        r = int(self.radius)
        return pygame.Rect(int(self.x) - r, int(self.y) - r, r * 2, r * 2)

    def update(self, dt: float):
        if not self.is_active:
            return
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= dt
        if self.lifetime <= 0.0:
            self.is_active = False

    def check_player_collision(self, player_rect: pygame.Rect) -> bool:
        if not self.is_active:
            return False
        return self.rect.colliderect(player_rect)


class Boss(CombatTarget):
    """
    Base class for sector bosses.

    Provides multi-phase state transitions, exposed weak point vulnerability,
    telegraph scheduling, clean arena resets, and deterministic death edge case resolution.
    """

    def __init__(
        self,
        boss_id: str,
        x: float,
        y: float,
        width: int,
        height: int,
        max_health: int = 300,
        title: str = "SECTOR BOSS",
        subtitle: str = "CORE WARDEN",
    ):
        super().__init__(
            target_id=boss_id,
            rect=pygame.Rect(int(x), int(y), width, height),
            health=max_health,
            max_health=max_health,
        )
        self.spawn_x: float = float(x)
        self.spawn_y: float = float(y)
        self.x: float = float(x)
        self.y: float = float(y)
        self.width: int = width
        self.height: int = height
        self.title: str = title
        self.subtitle: str = subtitle

        # Phase tracking (Thresholds default to 3 equal segments)
        self.current_phase: int = PHASE_1
        self.phase_state: str = STATE_IDLE
        self.phase_thresholds: Dict[int, int] = {
            PHASE_1: max_health,
            PHASE_2: int(max_health * 2 / 3),
            PHASE_3: int(max_health / 3),
        }

        # Timers
        self.state_timer: float = 0.0
        self.intro_timer: float = 0.0
        self.intro_duration: float = 2.0
        self.transition_timer: float = 0.0
        self.vulnerability_timer: float = 0.0
        self.death_timer: float = 0.0

        # Weak point configuration
        self.weak_point_rect: Optional[pygame.Rect] = None
        self.weak_point_exposed: bool = False
        self.weak_point_multiplier: float = 2.0

        # Combat containers
        self.telegraphs: List[BossAttackTelegraph] = []
        self.projectiles: List[BossProjectile] = []

        # Lifecycle flags
        self.is_defeated: bool = False
        self.defeat_reward_granted: bool = False

    def start_intro(self):
        """Begin boss arrival intro animation."""
        self.current_phase = PHASE_INTRO
        self.phase_state = STATE_INTRO
        self.intro_timer = self.intro_duration

    def skip_intro(self):
        """Skip intro directly into active Phase 1 combat."""
        self.current_phase = PHASE_1
        self.phase_state = STATE_IDLE
        self.intro_timer = 0.0

    def trigger_transition(self, target_phase: int):
        """Execute phase transition: clears attacks, presents brief window."""
        self.current_phase = target_phase
        self.phase_state = STATE_TRANSITION
        self.transition_timer = 1.0
        self.telegraphs.clear()
        self.projectiles.clear()
        self.weak_point_exposed = False

    def trigger_defeat(self):
        """Transition boss to defeated state and purge lingering attacks."""
        self.health = 0
        self.is_dead = True
        self.is_defeated = True
        self.phase_state = STATE_DEFEATED
        self.current_phase = PHASE_DEFEATED
        self.death_timer = 2.5
        self.telegraphs.clear()
        self.projectiles.clear()
        self.weak_point_exposed = False

    def reset_to_pristine(self):
        """
        Full reset: restores health, clears all attacks/projectiles,
        resets phase to Phase 1, and repositions to spawn.
        """
        self.health = self.max_health
        self.is_dead = False
        self.is_defeated = False
        self.reward_claimed = False
        self.defeat_reward_granted = False
        self.x = self.spawn_x
        self.y = self.spawn_y
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        self.current_phase = PHASE_1
        self.phase_state = STATE_IDLE
        self.state_timer = 0.0
        self.intro_timer = 0.0
        self.transition_timer = 0.0
        self.vulnerability_timer = 0.0
        self.death_timer = 0.0
        self.weak_point_exposed = False
        self.telegraphs.clear()
        self.projectiles.clear()

    def take_damage(
        self,
        amount: int,
        hit_id: str = "",
        knockback: Tuple[float, float] = (0.0, 0.0),
        hit_pos: Tuple[float, float] = (0.0, 0.0),
    ) -> HitResult:
        """
        Damage calculation with weak point multiplier and phase triggers.
        Invulnerable during intro and transition states.
        """
        if self.is_dead or self.is_defeated:
            return HitResult(
                hit=False,
                target_id=self.target_id,
                damage_dealt=0,
                target_killed=False,
                hit_x=hit_pos[0],
                hit_y=hit_pos[1],
            )

        if self.phase_state in (STATE_INTRO, STATE_TRANSITION):
            # Boss is completely immune to damage during cinematics/transitions
            return HitResult(
                hit=True,
                target_id=self.target_id,
                damage_dealt=0,
                target_killed=False,
                hit_x=hit_pos[0],
                hit_y=hit_pos[1],
            )

        # Check weak point intersection
        effective_damage = amount
        hit_weak_point = False
        if self.weak_point_exposed and self.weak_point_rect is not None:
            hit_point = (int(hit_pos[0]), int(hit_pos[1]))
            if self.weak_point_rect.collidepoint(hit_point):
                effective_damage = int(round(amount * self.weak_point_multiplier))
                hit_weak_point = True

        actual_damage = min(self.health, effective_damage)
        self.health -= actual_damage
        self.hit_count += 1
        killed = False

        # Phase threshold checks
        if self.health <= 0:
            self.trigger_defeat()
            killed = True
        elif self.health <= self.phase_thresholds[PHASE_3] and self.current_phase < PHASE_3:
            self.trigger_transition(PHASE_3)
        elif self.health <= self.phase_thresholds[PHASE_2] and self.current_phase < PHASE_2:
            self.trigger_transition(PHASE_2)

        return HitResult(
            hit=True,
            target_id=self.target_id,
            damage_dealt=actual_damage,
            target_killed=killed,
            hit_x=hit_pos[0],
            hit_y=hit_pos[1],
        )

    def apply_defeat_reward(self, campaign: Any) -> bool:
        """
        Atomically grant defeat campaign reward.
        Guaranteed idempotent: returns True on first grant, False on replay.
        """
        if self.defeat_reward_granted:
            return False
        if not self.is_defeated:
            return False

        event = {
            "event_id": f"defeat_greenkeeper_{getattr(campaign, 'save_id', 'slot')}",
            "type": "defeat_greenkeeper",
        }
        applied = campaign.apply_event(event)
        if applied:
            self.defeat_reward_granted = True
            return True
        return False

    def resolve_simultaneous_death(self, player_alive: bool) -> str:
        """
        Resolve combat outcome edge cases.
        If player died, defeat does not count: player death takes precedence.
        """
        if not player_alive and self.is_defeated:
            # Simultaneous death edge case: player died before / at same frame as victory
            return "PLAYER_DIED"
        if not player_alive:
            return "PLAYER_DIED"
        if self.is_defeated:
            return "BOSS_DEFEATED"
        return "COMBAT_ACTIVE"

    def update(self, dt: float):
        """Base update ticking general timers and projectiles."""
        super().update(dt)

        # Update telegraphs
        for t in self.telegraphs:
            t.update(dt)
        self.telegraphs = [t for t in self.telegraphs if not t.is_expired]

        # Update projectiles
        for p in self.projectiles:
            p.update(dt)
        self.projectiles = [p for p in self.projectiles if p.is_active]

        # State timers
        if self.phase_state == STATE_INTRO:
            self.intro_timer -= dt
            if self.intro_timer <= 0.0:
                self.skip_intro()

        elif self.phase_state == STATE_TRANSITION:
            self.transition_timer -= dt
            if self.transition_timer <= 0.0:
                self.phase_state = STATE_IDLE

        elif self.phase_state == STATE_VULNERABLE:
            self.vulnerability_timer -= dt
            if self.vulnerability_timer <= 0.0:
                self.weak_point_exposed = False
                self.phase_state = STATE_IDLE

        elif self.phase_state == STATE_DEFEATED:
            if self.death_timer > 0.0:
                self.death_timer = max(0.0, self.death_timer - dt)
