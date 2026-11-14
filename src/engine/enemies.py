"""
MODULE: video_game/engine/enemies.py
PURPOSE: Core recon drones and Static Hound enemy AI, predictive laser targeting,
         telegraphed windup states, line-of-sight checks, and encounter management.
CALLED BY: video_game.engine.scenes.field, video_game.tests.test_combat.
HOW TO MODIFY: Tune speeds, ranges, and telegraphs in video_game/data/balance.json;
               extend enemy archetypes or boss behaviors by subclassing Enemy.
"""

from dataclasses import dataclass, field
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union
import pygame

from video_game.engine import config
from video_game.engine.attack_visuals import render_attack_field
from video_game.engine.native_room_assets import _inside_without_symlinks
from video_game.engine.weapons import (
    CombatTarget,
    HitResult,
    check_swept_ray_tile_collision,
)
from video_game.engine.world import (
    COLLISION_SOLID,
    Camera,
    Room,
)

BALANCE_PATH = Path(__file__).resolve().parent.parent / "data" / "balance.json"
ENEMY_SPRITES_DIR = Path(__file__).resolve().parent.parent / "assets" / "sprites" / "enemies"


@dataclass
class EnemyConfig:
    """Tuning parameters for enemy archetypes."""
    id: str
    name: str
    max_health: int
    width: int
    height: int
    patrol_speed: float
    detection_range: float
    windup_time: float
    recovery_time: float
    attack_cooldown: float
    contact_damage: int
    telegraph_color: Tuple[int, int, int]
    # Drone-specific
    lock_window: float = 0.30
    projectile_speed: float = 360.0
    projectile_damage: int = 20
    # Hound-specific
    pounce_speed: float = 240.0
    attack_duration: float = 0.40
    pounce_damage: int = 30
    # S09 Faction specifics
    teleport_range: float = 160.0
    coherence_drain_dps: float = 20.0
    shockwave_damage: int = 35
    shockwave_speed: float = 220.0

    @classmethod
    def load(cls, enemy_id: str, balance_file: Optional[Union[str, Path]] = None) -> "EnemyConfig":
        """Load archetype configuration from balance.json."""
        p = Path(balance_file) if balance_file else BALANCE_PATH
        data = {}
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
        cfg = data.get("enemies", {}).get(enemy_id, {})
        return cls(
            id=enemy_id,
            name=str(cfg.get("name", enemy_id)),
            max_health=int(cfg.get("max_health", 50)),
            width=int(cfg.get("width", 24)),
            height=int(cfg.get("height", 20)),
            patrol_speed=float(cfg.get("patrol_speed", 40.0)),
            detection_range=float(cfg.get("detection_range", 200.0)),
            windup_time=float(cfg.get("windup_time", 1.0)),
            recovery_time=float(cfg.get("recovery_time", 0.40)),
            attack_cooldown=float(cfg.get("attack_cooldown", 1.50)),
            contact_damage=int(cfg.get("contact_damage", 15)),
            telegraph_color=tuple(cfg.get("telegraph_color", [255, 30, 66])),
            lock_window=float(cfg.get("lock_window", 0.30)),
            projectile_speed=float(cfg.get("projectile_speed", 360.0)),
            projectile_damage=int(cfg.get("projectile_damage", 20)),
            pounce_speed=float(cfg.get("pounce_speed", 240.0)),
            attack_duration=float(cfg.get("attack_duration", 0.40)),
            pounce_damage=int(cfg.get("pounce_damage", 30)),
            teleport_range=float(cfg.get("teleport_range", 160.0)),
            coherence_drain_dps=float(cfg.get("coherence_drain_dps", 20.0)),
            shockwave_damage=int(cfg.get("shockwave_damage", 35)),
            shockwave_speed=float(cfg.get("shockwave_speed", 220.0)),
        )


STATE_PATROL = "patrol"
STATE_DETECT = "detect"
STATE_WINDUP = "windup"
STATE_ATTACK = "attack"
STATE_RECOVERY = "recovery"
STATE_HURT = "hurt"
STATE_DEATH = "death"


class Enemy(CombatTarget):
    """
    Base autonomous combat entity with deterministic state transitions,
    line-of-sight verification, cover awareness, and restart idempotence.
    """

    def __init__(
        self,
        target_id: str,
        x: float,
        y: float,
        cfg: EnemyConfig,
        patrol_left: Optional[float] = None,
        patrol_right: Optional[float] = None,
    ):
        super().__init__(
            target_id=target_id,
            rect=pygame.Rect(int(x), int(y), cfg.width, cfg.height),
            health=cfg.max_health,
            max_health=cfg.max_health,
        )
        self._assisted_defeat_claimed = False
        self.cfg: EnemyConfig = cfg
        self.spawn_x: float = float(x)
        self.spawn_y: float = float(y)
        self.x: float = float(x)
        self.y: float = float(y)
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.facing: str = "left"

        # Patrol boundaries
        span = 80.0
        self.patrol_left: float = patrol_left if patrol_left is not None else max(0.0, x - span)
        self.patrol_right: float = patrol_right if patrol_right is not None else (x + span)

        # State machine
        self.state: str = STATE_PATROL
        self.state_timer: float = 0.0
        self.cooldown_timer: float = 0.0
        self.anim_time: float = 0.0

        # Telegraph & targeting state
        self.has_los: bool = False
        self.telegraph_active: bool = False
        self.telegraph_locked: bool = False
        self.locked_aim_vector: Tuple[float, float] = (-1.0, 0.0)
        self.target_aim_pos: Tuple[float, float] = (0.0, 0.0)

    def reset_to_spawn(self):
        """Restore pristine spawn state on room reload or checkpoint respawn."""
        self.x = self.spawn_x
        self.y = self.spawn_y
        self.vx = 0.0
        self.vy = 0.0
        self.health = self.cfg.max_health
        self.is_dead = False
        self.reward_claimed = False
        self.clear_statuses()
        self.invulnerable_timer = 0.0
        self.state = STATE_PATROL
        self.state_timer = 0.0
        self.cooldown_timer = 0.0
        self.telegraph_active = False
        self.telegraph_locked = False
        self.rect = pygame.Rect(int(self.x), int(self.y), self.cfg.width, self.cfg.height)

    def step_patrol(self, dt: float, room: Room):
        """Move within safe patrol bounds without snapping after displacement."""
        distance = abs(self.vx) * dt
        if self.x < self.patrol_left:
            next_x = min(self.patrol_left, self.x + distance)
        elif self.x > self.patrol_right:
            next_x = max(self.patrol_right, self.x - distance)
        else:
            next_x = min(self.patrol_right, max(self.patrol_left, self.x + self.vx * dt))
        # Check short steps even if a large update is supplied.
        steps = max(1, math.ceil(abs(next_x - self.x) / 4.0))
        delta = (next_x - self.x) / steps
        for _ in range(steps):
            proposed = self.x + delta
            rect = pygame.Rect(int(proposed), int(self.y), self.cfg.width, self.cfg.height)
            if not pygame.Rect(0, 0, room.width_px, room.height_px).contains(rect):
                break
            collision = room.check_rect_collision(rect)
            if collision["solid"] or collision["hazard"]:
                break
            self.x = proposed

    def check_line_of_sight(self, player: Any, room: Room) -> bool:
        """
        Verify unobstructed visual and ballistic trajectory to player.
        Returns False if occluded by solid tiles or player is in background cover.
        """
        # Concealment in background alcove breaks all line-of-sight
        if getattr(player, "in_cover", False) and getattr(player, "cover_type", None) == "background":
            return False

        ex = self.x + self.cfg.width / 2.0
        ey = self.y + self.cfg.height / 2.0
        px = player.x + player.width / 2.0
        py = player.y + player.height / 2.0

        # Max detection range check
        dist = math.hypot(px - ex, py - ey)
        if dist > self.cfg.detection_range:
            return False

        # Raycast against solid tiles in room
        wall_hit, _, _, _, _ = check_swept_ray_tile_collision(room, ex, ey, px, py)
        return not wall_hit

    def take_damage(
        self,
        amount: int,
        hit_id: str = "",
        knockback: Tuple[float, float] = (0.0, 0.0),
        hit_pos: Tuple[float, float] = (0.0, 0.0),
    ) -> HitResult:
        """Process weapon damage and enter hurt/death state."""
        res = super().take_damage(amount, hit_id, knockback, hit_pos)
        if res.hit and res.damage_dealt > 0:
            if res.target_killed:
                self.state = STATE_DEATH
                self.state_timer = 0.50
                self.vx = 0.0
                self.vy = 0.0
                self.telegraph_active = False
            else:
                self.state = STATE_HURT
                self.state_timer = 0.12
                self.vx = knockback[0] * 0.5
                self.vy = knockback[1] * 0.5
        return res


class CoreReconDrone(Enemy):
    """
    Hovering dish drone with predictive laser targeting.
    Tracks player velocity, locks aim during a 0.3s dodge window, and discharges linear pulse.
    """

    def __init__(
        self,
        target_id: str,
        x: float,
        y: float,
        cfg: Optional[EnemyConfig] = None,
        patrol_left: Optional[float] = None,
        patrol_right: Optional[float] = None,
    ):
        config_obj = cfg or EnemyConfig.load("core_recon_drone")
        super().__init__(target_id, x, y, config_obj, patrol_left, patrol_right)
        self.hover_phase: float = 0.0
        self.locked_aim_vector: Tuple[float, float] = (-1.0, 0.0)

    def update(
        self,
        dt: float,
        player: Any,
        room: Room,
        manager: Any,
        is_paused: bool = False,
        decoy: Optional[Any] = None,
    ):
        """Advance drone state machine, predictive aiming, and projectile discharge."""
        if is_paused or dt <= 0.0:
            return

        super().update(dt)

        if self.has_status("stun"):
            self.telegraph_active = False
            self.telegraph_locked = False
            self.vx = 0.0
            self.vy = 0.0
            self.rect.topleft = (int(self.x), int(self.y))
            return

        self.anim_time += dt
        if self.cooldown_timer > 0.0:
            self.cooldown_timer = max(0.0, self.cooldown_timer - dt)

        # Death state decay
        if self.state == STATE_DEATH:
            self.state_timer = max(0.0, self.state_timer - dt)
            return

        # Hurt state recovery
        if self.state == STATE_HURT:
            self.state_timer = max(0.0, self.state_timer - dt)
            if self.state_timer <= 0.0:
                self.state = STATE_RECOVERY
                self.state_timer = self.cfg.recovery_time
            self.rect.topleft = (int(self.x), int(self.y))
            return

        # Recovery state
        if self.state == STATE_RECOVERY:
            self.telegraph_active = False
            self.state_timer = max(0.0, self.state_timer - dt)
            if self.state_timer <= 0.0:
                self.state = STATE_PATROL
            self.rect.topleft = (int(self.x), int(self.y))
            return

        # Target selection: prioritize active decoy over player
        aim_target = decoy if (decoy and not getattr(decoy, "is_dead", False)) else player

        # Visual line-of-sight check
        self.has_los = self.check_line_of_sight(aim_target, room)

        # 1. PATROL
        if self.state == STATE_PATROL:
            self.telegraph_active = False
            self.telegraph_locked = False
            # Sinusoidal hover bobbing
            self.hover_phase += dt * 3.0
            bob = math.sin(self.hover_phase) * 6.0
            self.y = self.spawn_y + bob

            # Horizontal pacing
            speed = self.cfg.patrol_speed
            if self.facing == "right":
                self.x += speed * dt
                if self.x >= self.patrol_right:
                    self.x = self.patrol_right
                    self.facing = "left"
            else:
                self.x -= speed * dt
                if self.x <= self.patrol_left:
                    self.x = self.patrol_left
                    self.facing = "right"

            # Transition to windup when player detected with LOS
            if self.has_los and self.cooldown_timer <= 0.0:
                self.state = STATE_WINDUP
                self.state_timer = self.cfg.windup_time
                self.telegraph_active = True
                self.telegraph_locked = False

        # 2. WINDUP (Predictive Aiming & Aim Lock)
        elif self.state == STATE_WINDUP:
            self.state_timer = max(0.0, self.state_timer - dt)
            ex = self.x + self.cfg.width / 2.0
            ey = self.y + 14.0  # Muzzle attachment
            px = aim_target.x + getattr(aim_target, "width", 16) / 2.0
            py = aim_target.y + getattr(aim_target, "height", 32) / 2.0

            # Facing updates to face target
            self.facing = "right" if px > ex else "left"

            # Check if wall occluded target mid-windup
            if not self.has_los:
                self.state = STATE_PATROL
                self.telegraph_active = False
                self.telegraph_locked = False
                self.cooldown_timer = 0.50
                self.rect.topleft = (int(self.x), int(self.y))
                return

            lock_threshold = self.cfg.lock_window  # Final 0.3s
            if self.state_timer > lock_threshold:
                # Active tracking: predict player position based on player velocity
                self.telegraph_locked = False
                pred_lead = 0.30
                pred_x = px + getattr(player, "vx", 0.0) * pred_lead
                pred_y = py + getattr(player, "vy", 0.0) * pred_lead
                self.target_aim_pos = (pred_x, pred_y)

                dx = pred_x - ex
                dy = pred_y - ey
                mag = math.hypot(dx, dy)
                if mag > 1e-4:
                    self.locked_aim_vector = (dx / mag, dy / mag)
            else:
                # AIM LOCK: Vector is locked! Dodge window active!
                self.telegraph_locked = True

            # Trigger discharge upon windup completion
            if self.state_timer <= 0.0:
                self.state = STATE_ATTACK
                dir_x, dir_y = self.locked_aim_vector
                manager.spawn_enemy_projectile(
                    origin_x=ex,
                    origin_y=ey,
                    dir_x=dir_x,
                    dir_y=dir_y,
                    speed=self.cfg.projectile_speed,
                    damage=self.cfg.projectile_damage,
                    source_id=self.target_id,
                )
                self.telegraph_active = False
                self.telegraph_locked = False
                self.state = STATE_RECOVERY
                self.state_timer = self.cfg.recovery_time
                self.cooldown_timer = self.cfg.attack_cooldown

        self.rect.topleft = (int(self.x), int(self.y))


class StaticHound(Enemy):
    """
    Cassette-punk ground scavenger quadruped.
    Paces ground, winds up with static electric spine arcs, and pounces along an airborne arc.
    """

    def __init__(
        self,
        target_id: str,
        x: float,
        y: float,
        cfg: Optional[EnemyConfig] = None,
        patrol_left: Optional[float] = None,
        patrol_right: Optional[float] = None,
    ):
        config_obj = cfg or EnemyConfig.load("static_hound")
        super().__init__(target_id, x, y, config_obj, patrol_left, patrol_right)
        self.is_grounded: bool = True
        self.attack_hitbox_active: bool = False
        self.has_damaged_player: bool = False

    def update(
        self,
        dt: float,
        player: Any,
        room: Room,
        manager: Any,
        is_paused: bool = False,
        decoy: Optional[Any] = None,
    ):
        """Advance hound movement, ground physics, pounce arc, and player collision."""
        if is_paused or dt <= 0.0:
            return

        super().update(dt)

        if self.has_status("stun"):
            self.telegraph_active = False
            self.attack_hitbox_active = False
            self.vx = 0.0
            self.vy = 0.0
            self.rect.topleft = (int(self.x), int(self.y))
            return

        self.anim_time += dt
        if self.cooldown_timer > 0.0:
            self.cooldown_timer = max(0.0, self.cooldown_timer - dt)

        # Death decay
        if self.state == STATE_DEATH:
            self.state_timer = max(0.0, self.state_timer - dt)
            return

        # Hurt recovery
        if self.state == STATE_HURT:
            self.state_timer = max(0.0, self.state_timer - dt)
            if self.state_timer <= 0.0:
                self.state = STATE_RECOVERY
                self.state_timer = self.cfg.recovery_time
            self.rect.topleft = (int(self.x), int(self.y))
            return

        # Recovery state
        if self.state == STATE_RECOVERY:
            self.attack_hitbox_active = False
            self.state_timer = max(0.0, self.state_timer - dt)
            if self.state_timer <= 0.0:
                self.state = STATE_PATROL
            self.rect.topleft = (int(self.x), int(self.y))
            return

        # Target selection: prioritize active decoy over player
        aim_target = decoy if (decoy and not getattr(decoy, "is_dead", False)) else player

        self.has_los = self.check_line_of_sight(aim_target, room)

        # 1. PATROL
        if self.state == STATE_PATROL:
            self.attack_hitbox_active = False
            self.telegraph_active = False
            speed = self.cfg.patrol_speed
            if self.facing == "right":
                self.x += speed * dt
                if self.x >= self.patrol_right:
                    self.x = self.patrol_right
                    self.facing = "left"
            else:
                self.x -= speed * dt
                if self.x <= self.patrol_left:
                    self.x = self.patrol_left
                    self.facing = "right"

            # Detect target
            if self.has_los and self.cooldown_timer <= 0.0:
                px = aim_target.x + getattr(aim_target, "width", 16) / 2.0
                hx = self.x + self.cfg.width / 2.0
                self.facing = "right" if px > hx else "left"
                self.state = STATE_WINDUP
                self.state_timer = self.cfg.windup_time
                self.telegraph_active = True

        # 2. WINDUP (Crouch & Static Arc Telegraph)
        elif self.state == STATE_WINDUP:
            self.state_timer = max(0.0, self.state_timer - dt)
            px = aim_target.x + getattr(aim_target, "width", 16) / 2.0
            hx = self.x + self.cfg.width / 2.0
            self.facing = "right" if px > hx else "left"

            # Check if player broke line of sight
            if not self.has_los:
                self.state = STATE_PATROL
                self.telegraph_active = False
                self.cooldown_timer = 0.50
                self.rect.topleft = (int(self.x), int(self.y))
                return

            if self.state_timer <= 0.0:
                # Launch pounce
                self.state = STATE_ATTACK
                self.state_timer = self.cfg.attack_duration
                self.telegraph_active = False
                self.attack_hitbox_active = True
                self.has_damaged_player = False
                # Pounce arc velocity
                p_dir = 1.0 if self.facing == "right" else -1.0
                self.vx = p_dir * self.cfg.pounce_speed
                self.vy = -90.0  # Low leaping trajectory
                self.is_grounded = False

        # 3. ATTACK (Airborne Pounce)
        elif self.state == STATE_ATTACK:
            self.state_timer = max(0.0, self.state_timer - dt)
            # Gravity
            self.vy = min(360.0, self.vy + 400.0 * dt)
            self.x += self.vx * dt
            self.y += self.vy * dt

            # Landed check
            if self.y >= self.spawn_y:
                self.y = self.spawn_y
                self.vy = 0.0
                self.vx = 0.0
                self.is_grounded = True

            self.rect.topleft = (int(self.x), int(self.y))

            # Check collision with player
            if self.attack_hitbox_active and not self.has_damaged_player:
                if self.rect.colliderect(player.rect):
                    # Check low cover protection
                    attack_dir = "left" if self.vx > 0 else "right"
                    if hasattr(player, "is_protected_from_attack") and player.is_protected_from_attack(room, attack_dir):
                        # Blocked by low cover sandbag!
                        self.attack_hitbox_active = False
                    else:
                        # Deal pounce damage
                        player.take_damage(
                            self.cfg.pounce_damage,
                            knockback_vx=self.vx * 0.4,
                            knockback_vy=-120.0,
                            damage_source="hostile",
                        )
                        self.has_damaged_player = True

            if self.state_timer <= 0.0 or (self.is_grounded and self.state_timer < self.cfg.attack_duration * 0.5):
                self.state = STATE_RECOVERY
                self.state_timer = self.cfg.recovery_time
                self.cooldown_timer = self.cfg.attack_cooldown
                self.attack_hitbox_active = False

        self.rect.topleft = (int(self.x), int(self.y))


class CoreEnforcer(Enemy):
    """
    Core Collective heavy synthetic chassis enforcer.
    Heavy frontal armor absorbs 50% damage from front.
    EMP Overload Counter: Stunned state overloads circuits, dealing 1.5x damage.
    Slide-kick forces immediate stagger recovery (1.2s), breaking firing windup.
    Fires 3-round burst of plasma pulses.
    """

    def __init__(
        self,
        target_id: str,
        x: float,
        y: float,
        cfg: Optional[EnemyConfig] = None,
        patrol_left: Optional[float] = None,
        patrol_right: Optional[float] = None,
    ):
        config_obj = cfg or EnemyConfig.load("core_enforcer")
        super().__init__(target_id, x, y, config_obj, patrol_left, patrol_right)
        self.burst_count: int = 0
        self.burst_timer: float = 0.0

    def reset_to_spawn(self):
        super().reset_to_spawn()
        self.burst_count = 0
        self.burst_timer = 0.0

    def on_slide_kicked(self):
        """Slide-kick stagger counter: interrupts windup and forces 1.2s recovery."""
        self.state = STATE_RECOVERY
        self.state_timer = 1.20
        self.telegraph_active = False
        self.telegraph_locked = False
        self.burst_count = 0

    def take_damage(
        self,
        amount: int,
        hit_id: str = "",
        knockback: Tuple[float, float] = (0.0, 0.0),
        hit_pos: Tuple[float, float] = (0.0, 0.0),
    ) -> HitResult:
        if self.is_dead:
            return super().take_damage(amount, hit_id, knockback, hit_pos)

        # EMP Overload counterplay: 1.5x damage when stunned
        if self.has_status("stun"):
            modified_amount = int(amount * 1.5)
            return super().take_damage(modified_amount, hit_id, knockback, hit_pos)

        # Frontal armor check
        is_frontal = False
        if hit_pos[0] != 0.0:
            if self.facing == "left" and hit_pos[0] <= self.x + self.cfg.width / 2.0:
                is_frontal = True
            elif self.facing == "right" and hit_pos[0] >= self.x + self.cfg.width / 2.0:
                is_frontal = True
        elif knockback[0] != 0.0:
            if (self.facing == "left" and knockback[0] > 0) or (self.facing == "right" and knockback[0] < 0):
                is_frontal = True

        if is_frontal:
            modified_amount = max(1, int(amount * 0.50))
        else:
            modified_amount = amount

        return super().take_damage(modified_amount, hit_id, knockback, hit_pos)

    def update(
        self,
        dt: float,
        player: Any,
        room: Room,
        manager: Any,
        is_paused: bool = False,
        decoy: Optional[Any] = None,
    ):
        if is_paused or dt <= 0.0:
            return

        super().update(dt)

        if self.has_status("stun"):
            self.telegraph_active = False
            self.telegraph_locked = False
            self.burst_count = 0
            self.vx = 0.0
            self.vy = 0.0
            self.rect.topleft = (int(self.x), int(self.y))
            return

        self.anim_time += dt
        if self.cooldown_timer > 0.0:
            self.cooldown_timer = max(0.0, self.cooldown_timer - dt)

        if self.state == STATE_DEATH:
            self.state_timer = max(0.0, self.state_timer - dt)
            return

        if self.state == STATE_HURT:
            self.state_timer = max(0.0, self.state_timer - dt)
            if self.state_timer <= 0.0:
                self.state = STATE_RECOVERY
                self.state_timer = self.cfg.recovery_time
            self.rect.topleft = (int(self.x), int(self.y))
            return

        if self.state == STATE_RECOVERY:
            self.state_timer = max(0.0, self.state_timer - dt)
            if self.state_timer <= 0.0:
                self.state = STATE_PATROL
            self.rect.topleft = (int(self.x), int(self.y))
            return

        aim_target = decoy if (decoy and not getattr(decoy, "is_dead", False)) else player
        self.has_los = self.check_line_of_sight(aim_target, room)

        # 1. PATROL
        if self.state == STATE_PATROL:
            self.telegraph_active = False
            self.telegraph_locked = False
            speed = self.cfg.patrol_speed
            if self.facing == "left":
                self.vx = -speed
                if self.x <= self.patrol_left:
                    self.facing = "right"
            else:
                self.vx = speed
                if self.x >= self.patrol_right:
                    self.facing = "left"

            self.step_patrol(dt, room)

            if self.has_los and self.cooldown_timer <= 0.0:
                self.state = STATE_WINDUP
                self.state_timer = self.cfg.windup_time
                self.telegraph_active = True
                self.telegraph_locked = False
                self.facing = "right" if aim_target.x > self.x else "left"

        # 2. WINDUP
        elif self.state == STATE_WINDUP:
            self.vx = 0.0
            self.facing = "right" if aim_target.x > self.x else "left"
            self.state_timer = max(0.0, self.state_timer - dt)

            ex = self.x + self.cfg.width / 2.0
            ey = self.y + 16.0
            tx = aim_target.x + aim_target.width / 2.0
            ty = aim_target.y + aim_target.height / 2.0
            dx, dy = tx - ex, ty - ey
            dist = math.hypot(dx, dy)
            if dist > 1e-4:
                self.locked_aim_vector = (dx / dist, dy / dist)
            self.target_aim_pos = (tx, ty)

            if self.state_timer <= self.cfg.lock_window:
                self.telegraph_locked = True

            if not self.has_los and not self.telegraph_locked:
                self.state = STATE_PATROL
                self.telegraph_active = False
                self.telegraph_locked = False

            if self.state_timer <= 0.0:
                self.state = STATE_ATTACK
                self.burst_count = 3
                self.burst_timer = 0.0
                self.telegraph_active = False
                self.telegraph_locked = False

        # 3. ATTACK (Burst Fire)
        elif self.state == STATE_ATTACK:
            self.vx = 0.0
            self.burst_timer -= dt
            if self.burst_timer <= 0.0 and self.burst_count > 0:
                self.burst_timer = 0.12
                self.burst_count -= 1
                ex = self.x + self.cfg.width / 2.0
                ey = self.y + 16.0
                dir_x, dir_y = self.locked_aim_vector
                manager.spawn_enemy_projectile(
                    origin_x=ex,
                    origin_y=ey,
                    dir_x=dir_x,
                    dir_y=dir_y,
                    speed=self.cfg.projectile_speed,
                    damage=self.cfg.projectile_damage,
                    source_id=self.target_id,
                    color=(192, 216, 240),
                )

            if self.burst_count <= 0 and self.burst_timer <= 0.0:
                self.state = STATE_RECOVERY
                self.state_timer = self.cfg.recovery_time
                self.cooldown_timer = self.cfg.attack_cooldown

        self.rect.topleft = (int(self.x), int(self.y))


class CoreOperative(Enemy):
    """
    Agile mesh-networked guard with high mobility and rapid flechette rifle.
    Cover Occlusion Counter: If player enters low cover or background cover during windup,
    the mesh network loses optical lock and immediately aborts to patrol.
    Takes 1.25x damage when caught in recovery state.
    """

    def __init__(
        self,
        target_id: str,
        x: float,
        y: float,
        cfg: Optional[EnemyConfig] = None,
        patrol_left: Optional[float] = None,
        patrol_right: Optional[float] = None,
    ):
        config_obj = cfg or EnemyConfig.load("core_operative")
        super().__init__(target_id, x, y, config_obj, patrol_left, patrol_right)

    def take_damage(
        self,
        amount: int,
        hit_id: str = "",
        knockback: Tuple[float, float] = (0.0, 0.0),
        hit_pos: Tuple[float, float] = (0.0, 0.0),
    ) -> HitResult:
        if self.state == STATE_RECOVERY:
            amount = int(amount * 1.25)
        return super().take_damage(amount, hit_id, knockback, hit_pos)

    def update(
        self,
        dt: float,
        player: Any,
        room: Room,
        manager: Any,
        is_paused: bool = False,
        decoy: Optional[Any] = None,
    ):
        if is_paused or dt <= 0.0:
            return

        super().update(dt)

        if self.has_status("stun"):
            self.telegraph_active = False
            self.telegraph_locked = False
            self.vx = 0.0
            self.vy = 0.0
            self.rect.topleft = (int(self.x), int(self.y))
            return

        self.anim_time += dt
        if self.cooldown_timer > 0.0:
            self.cooldown_timer = max(0.0, self.cooldown_timer - dt)

        if self.state == STATE_DEATH:
            self.state_timer = max(0.0, self.state_timer - dt)
            return

        if self.state == STATE_HURT:
            self.state_timer = max(0.0, self.state_timer - dt)
            if self.state_timer <= 0.0:
                self.state = STATE_RECOVERY
                self.state_timer = self.cfg.recovery_time
            self.rect.topleft = (int(self.x), int(self.y))
            return

        if self.state == STATE_RECOVERY:
            self.state_timer = max(0.0, self.state_timer - dt)
            if self.state_timer <= 0.0:
                self.state = STATE_PATROL
            self.rect.topleft = (int(self.x), int(self.y))
            return

        aim_target = decoy if (decoy and not getattr(decoy, "is_dead", False)) else player
        self.has_los = self.check_line_of_sight(aim_target, room)

        # 1. PATROL
        if self.state == STATE_PATROL:
            self.telegraph_active = False
            self.telegraph_locked = False
            speed = self.cfg.patrol_speed
            if self.facing == "left":
                self.vx = -speed
                if self.x <= self.patrol_left:
                    self.facing = "right"
            else:
                self.vx = speed
                if self.x >= self.patrol_right:
                    self.facing = "left"

            self.step_patrol(dt, room)

            if self.has_los and self.cooldown_timer <= 0.0:
                self.state = STATE_WINDUP
                self.state_timer = self.cfg.windup_time
                self.telegraph_active = True
                self.telegraph_locked = False
                self.facing = "right" if aim_target.x > self.x else "left"

        # 2. WINDUP
        elif self.state == STATE_WINDUP:
            self.vx = 0.0
            self.facing = "right" if aim_target.x > self.x else "left"

            # Cover Occlusion Counter: If player takes low cover or background cover, lock breaks immediately
            if getattr(player, "in_cover", False) or getattr(player, "is_crouching", False) or getattr(player, "is_sliding", False):
                self.state = STATE_PATROL
                self.telegraph_active = False
                self.telegraph_locked = False
                self.cooldown_timer = 0.50
                self.rect.topleft = (int(self.x), int(self.y))
                return

            self.state_timer = max(0.0, self.state_timer - dt)

            ex = self.x + self.cfg.width / 2.0
            ey = self.y + 16.0
            tx = aim_target.x + aim_target.width / 2.0
            ty = aim_target.y + aim_target.height / 2.0
            dx, dy = tx - ex, ty - ey
            dist = math.hypot(dx, dy)
            if dist > 1e-4:
                self.locked_aim_vector = (dx / dist, dy / dist)
            self.target_aim_pos = (tx, ty)

            if self.state_timer <= self.cfg.lock_window:
                self.telegraph_locked = True

            if not self.has_los and not self.telegraph_locked:
                self.state = STATE_PATROL
                self.telegraph_active = False
                self.telegraph_locked = False

            if self.state_timer <= 0.0:
                self.state = STATE_ATTACK
                dir_x, dir_y = self.locked_aim_vector
                manager.spawn_enemy_projectile(
                    origin_x=ex,
                    origin_y=ey,
                    dir_x=dir_x,
                    dir_y=dir_y,
                    speed=self.cfg.projectile_speed,
                    damage=self.cfg.projectile_damage,
                    source_id=self.target_id,
                    color=(255, 30, 66),
                )
                self.telegraph_active = False
                self.telegraph_locked = False
                self.state = STATE_RECOVERY
                self.state_timer = self.cfg.recovery_time
                self.cooldown_timer = self.cfg.attack_cooldown

        self.rect.topleft = (int(self.x), int(self.y))


class ShieldHound(Enemy):
    """
    Static Hound scavenger with welded CRT-glass riot shield.
    Blocks 100% of frontal projectile damage during patrol and pounce.
    Counterplay: Slide-kick knocks the hound onto its side into stagger recovery (1.2s),
    disabling the shield and exposing its rear battery pack for 2.0x critical damage.
    """

    def __init__(
        self,
        target_id: str,
        x: float,
        y: float,
        cfg: Optional[EnemyConfig] = None,
        patrol_left: Optional[float] = None,
        patrol_right: Optional[float] = None,
    ):
        config_obj = cfg or EnemyConfig.load("shield_hound")
        super().__init__(target_id, x, y, config_obj, patrol_left, patrol_right)
        self.is_knocked_down: bool = False
        self.is_grounded: bool = True
        self.attack_hitbox_active: bool = False
        self.has_damaged_player: bool = False

    def reset_to_spawn(self):
        super().reset_to_spawn()
        self.is_knocked_down = False
        self.is_grounded = True
        self.attack_hitbox_active = False
        self.has_damaged_player = False

    def on_slide_kicked(self):
        """Slide-kick knockdown: knocks shield hound onto side, exposing rear battery."""
        self.is_knocked_down = True
        self.state = STATE_RECOVERY
        self.state_timer = 1.20
        self.telegraph_active = False
        self.attack_hitbox_active = False

    def take_damage(
        self,
        amount: int,
        hit_id: str = "",
        knockback: Tuple[float, float] = (0.0, 0.0),
        hit_pos: Tuple[float, float] = (0.0, 0.0),
    ) -> HitResult:
        if self.is_dead:
            return super().take_damage(amount, hit_id, knockback, hit_pos)

        # When knocked down (in recovery from slide-kick) or stunned, shield is down and rear battery is exposed
        if self.is_knocked_down or self.state == STATE_RECOVERY or self.has_status("stun"):
            critical_amount = int(amount * 2.0)
            return super().take_damage(critical_amount, hit_id, knockback, hit_pos)

        # Frontal shield block
        is_front = False
        if hit_pos[0] != 0.0:
            if self.facing == "left" and hit_pos[0] <= self.x + self.cfg.width / 2.0:
                is_front = True
            elif self.facing == "right" and hit_pos[0] >= self.x + self.cfg.width / 2.0:
                is_front = True
        elif knockback[0] != 0.0:
            if (self.facing == "left" and knockback[0] > 0) or (self.facing == "right" and knockback[0] < 0):
                is_front = True

        if is_front:
            # Deflected 100% by welded CRT glass shield!
            return HitResult(
                hit=True,
                target_id=self.target_id,
                damage_dealt=0,
                target_killed=False,
                hit_x=hit_pos[0],
                hit_y=hit_pos[1],
            )

        # Rear attack: deals 2.0x critical damage to exposed battery pack
        critical_amount = int(amount * 2.0)
        return super().take_damage(critical_amount, hit_id, knockback, hit_pos)

    def update(
        self,
        dt: float,
        player: Any,
        room: Room,
        manager: Any,
        is_paused: bool = False,
        decoy: Optional[Any] = None,
    ):
        if is_paused or dt <= 0.0:
            return

        super().update(dt)

        if self.has_status("stun"):
            self.telegraph_active = False
            self.attack_hitbox_active = False
            self.vx = 0.0
            self.vy = 0.0
            self.rect.topleft = (int(self.x), int(self.y))
            return

        self.anim_time += dt
        if self.cooldown_timer > 0.0:
            self.cooldown_timer = max(0.0, self.cooldown_timer - dt)

        if self.state == STATE_DEATH:
            self.state_timer = max(0.0, self.state_timer - dt)
            return

        if self.state == STATE_HURT:
            self.state_timer = max(0.0, self.state_timer - dt)
            if self.state_timer <= 0.0:
                self.state = STATE_RECOVERY
                self.state_timer = self.cfg.recovery_time
            self.rect.topleft = (int(self.x), int(self.y))
            return

        if self.state == STATE_RECOVERY:
            self.attack_hitbox_active = False
            self.state_timer = max(0.0, self.state_timer - dt)
            if not self.is_grounded:
                # An interrupted pounce can stop in the air. Descend through
                # checked steps rather than freezing or teleporting to spawn.
                self.vy = min(360.0, max(0.0, self.vy) + 400.0 * dt)
                fall = self.vy * dt
                steps = max(1, math.ceil(fall))
                for _ in range(steps):
                    next_y = min(self.spawn_y, self.y + fall / steps)
                    candidate = pygame.Rect(int(self.x), int(next_y), self.cfg.width, self.cfg.height)
                    if not pygame.Rect(0, 0, room.width_px, room.height_px).contains(candidate):
                        break
                    collision = room.check_rect_collision(candidate)
                    if collision["solid"] or collision["hazard"]:
                        if collision["solid"] and not collision["hazard"]:
                            self.is_grounded = True
                        self.vy = 0.0
                        break
                    self.y = next_y
                    if self.y >= self.spawn_y:
                        support = room.check_rect_collision(candidate.move(0, 1))
                        self.is_grounded = bool(support["solid"] or support["one_way"])
                        self.vy = 0.0
                        break
            if self.state_timer <= 0.0 and self.is_grounded:
                self.state = STATE_PATROL
                self.is_knocked_down = False
            self.rect.topleft = (int(self.x), int(self.y))
            return

        aim_target = decoy if (decoy and not getattr(decoy, "is_dead", False)) else player
        self.has_los = self.check_line_of_sight(aim_target, room)

        # 1. PATROL
        if self.state == STATE_PATROL:
            self.telegraph_active = False
            self.attack_hitbox_active = False
            self.has_damaged_player = False
            speed = self.cfg.patrol_speed
            if self.facing == "left":
                self.vx = -speed
                if self.x <= self.patrol_left:
                    self.facing = "right"
            else:
                self.vx = speed
                if self.x >= self.patrol_right:
                    self.facing = "left"

            self.step_patrol(dt, room)

            if self.has_los and self.cooldown_timer <= 0.0:
                self.state = STATE_WINDUP
                self.state_timer = self.cfg.windup_time
                self.telegraph_active = True
                self.facing = "right" if aim_target.x > self.x else "left"

        # 2. WINDUP
        elif self.state == STATE_WINDUP:
            self.vx = 0.0
            self.facing = "right" if aim_target.x > self.x else "left"
            self.state_timer = max(0.0, self.state_timer - dt)

            if not self.has_los:
                self.state = STATE_PATROL
                self.telegraph_active = False

            elif self.state_timer <= 0.0:
                self.state = STATE_ATTACK
                self.state_timer = self.cfg.attack_duration
                self.telegraph_active = False
                self.attack_hitbox_active = True
                self.has_damaged_player = False
                pounce_dir = 1.0 if self.facing == "right" else -1.0
                self.vx = pounce_dir * self.cfg.pounce_speed
                self.vy = -120.0
                self.is_grounded = False

        # 3. ATTACK (Pounce)
        elif self.state == STATE_ATTACK:
            self.state_timer = max(0.0, self.state_timer - dt)
            self.vy = min(360.0, self.vy + 400.0 * dt)
            # Substeps prevent a pounce crossing a wall or hazard between frames.
            dx, dy = self.vx * dt, self.vy * dt
            steps = max(1, math.ceil(max(abs(dx), abs(dy)) / 4.0))
            blocked = False
            for _ in range(steps):
                next_x = self.x + dx / steps
                next_y = min(self.spawn_y, self.y + dy / steps)
                bounds = pygame.Rect(int(next_x), int(next_y), self.cfg.width, self.cfg.height)
                within_room = pygame.Rect(0, 0, room.width_px, room.height_px).contains(bounds)
                collision = room.check_rect_collision(bounds) if within_room else {"solid": True, "hazard": False}
                if collision["solid"] or collision["hazard"]:
                    blocked = True
                    break
                self.x, self.y = next_x, next_y
            if blocked:
                self.vx = self.vy = 0.0
                self.state = STATE_RECOVERY
                self.state_timer = self.cfg.recovery_time
                self.cooldown_timer = self.cfg.attack_cooldown
                self.attack_hitbox_active = False

            if self.y >= self.spawn_y:
                self.y = self.spawn_y
                self.vy = 0.0
                self.vx = 0.0
                self.is_grounded = True

            self.rect.topleft = (int(self.x), int(self.y))

            if self.attack_hitbox_active and not self.has_damaged_player:
                if self.rect.colliderect(player.rect):
                    attack_dir = "left" if self.vx > 0 else "right"
                    is_prot = False
                    if hasattr(player, "is_protected_from_attack"):
                        is_prot = player.is_protected_from_attack(room, attack_dir)
                    elif hasattr(player, "check_protection"):
                        is_prot = player.check_protection(attack_dir, room)

                    if is_prot:
                        self.attack_hitbox_active = False
                    else:
                        player.take_damage(
                            self.cfg.pounce_damage,
                            knockback_vx=self.vx * 0.4,
                            knockback_vy=-120.0,
                            damage_source="hostile",
                        )
                        self.has_damaged_player = True

            if self.state_timer <= 0.0 or (self.is_grounded and self.state_timer < self.cfg.attack_duration * 0.5):
                self.state = STATE_RECOVERY
                self.state_timer = self.cfg.recovery_time
                self.cooldown_timer = self.cfg.attack_cooldown
                self.attack_hitbox_active = False

        self.rect.topleft = (int(self.x), int(self.y))


class PhaseWatcher(Enemy):
    """
    Subspace-teleporting moon-grey infiltrator from the Watchers faction.
    Channels a continuous coherence drain beam that siphons player coherence and ability energy.
    Teleports safely to valid solid-free flanking positions.
    Counterplay:
      - Tagging with Scattergun (revealed status) disables teleportation.
      - EMP bola stun interrupts coherence channel.
    """

    def __init__(
        self,
        target_id: str,
        x: float,
        y: float,
        cfg: Optional[EnemyConfig] = None,
        patrol_left: Optional[float] = None,
        patrol_right: Optional[float] = None,
    ):
        config_obj = cfg or EnemyConfig.load("phase_watcher")
        super().__init__(target_id, x, y, config_obj, patrol_left, patrol_right)
        self.is_channeling: bool = False
        self.teleport_cooldown: float = 0.0

    def reset_to_spawn(self):
        super().reset_to_spawn()
        self.is_channeling = False
        self.teleport_cooldown = 0.0

    def try_teleport(self, player: Any, room: Room) -> bool:
        """
        Attempt tactical teleport to valid flanking coordinates.
        Revealed status completely suppresses teleportation.
        Guarantees solid-geometry safety: avoids solid tiles, hazard tiles, and out of bounds.
        """
        if self.has_status("revealed") or self.has_status("stun"):
            return False

        offsets = [-100.0, 100.0, -140.0, 140.0, -70.0, 70.0]
        px = player.x
        py = player.y
        player_feet = py + 32.0 if hasattr(player, "height") else py
        cand_y = player_feet - self.cfg.height

        for off in offsets:
            cand_x = px + off
            if cand_x < 0 or cand_x + self.cfg.width > room.width_px:
                continue
            if cand_y < 0 or cand_y + self.cfg.height > room.height_px:
                continue

            test_rect = pygame.Rect(int(cand_x), int(cand_y), self.cfg.width, self.cfg.height)
            col = room.check_rect_collision(test_rect)
            if col["solid"] or col["hazard"]:
                continue

            ground_rect = pygame.Rect(int(cand_x + 2), int(cand_y + self.cfg.height), max(1, self.cfg.width - 4), 4)
            col_ground = room.check_rect_collision(ground_rect)
            if not col_ground["solid"] and not col_ground["one_way"]:
                continue

            # Safe candidate found!
            self.x = cand_x
            self.y = cand_y
            self.rect.topleft = (int(self.x), int(self.y))
            self.facing = "right" if px > self.x else "left"
            return True

        return False

    def update(
        self,
        dt: float,
        player: Any,
        room: Room,
        manager: Any,
        is_paused: bool = False,
        decoy: Optional[Any] = None,
    ):
        if is_paused or dt <= 0.0:
            return

        super().update(dt)

        if self.teleport_cooldown > 0.0:
            self.teleport_cooldown = max(0.0, self.teleport_cooldown - dt)

        # Stun breaks coherence channel
        if self.has_status("stun"):
            self.is_channeling = False
            self.telegraph_active = False
            self.vx = 0.0
            self.vy = 0.0
            self.rect.topleft = (int(self.x), int(self.y))
            return

        self.anim_time += dt
        if self.cooldown_timer > 0.0:
            self.cooldown_timer = max(0.0, self.cooldown_timer - dt)

        if self.state == STATE_DEATH:
            self.is_channeling = False
            self.state_timer = max(0.0, self.state_timer - dt)
            return

        if self.state == STATE_HURT:
            self.is_channeling = False
            self.state_timer = max(0.0, self.state_timer - dt)
            if self.state_timer <= 0.0:
                self.state = STATE_RECOVERY
                self.state_timer = self.cfg.recovery_time
            self.rect.topleft = (int(self.x), int(self.y))
            return

        if self.state == STATE_RECOVERY:
            self.is_channeling = False
            self.state_timer = max(0.0, self.state_timer - dt)
            if self.state_timer <= 0.0:
                self.state = STATE_PATROL
            self.rect.topleft = (int(self.x), int(self.y))
            return

        aim_target = decoy if (decoy and not getattr(decoy, "is_dead", False)) else player
        self.has_los = self.check_line_of_sight(aim_target, room)

        # 1. PATROL
        if self.state == STATE_PATROL:
            self.is_channeling = False
            self.telegraph_active = False
            speed = self.cfg.patrol_speed
            if self.facing == "left":
                self.vx = -speed
                if self.x <= self.patrol_left:
                    self.facing = "right"
            else:
                self.vx = speed
                if self.x >= self.patrol_right:
                    self.facing = "left"

            self.step_patrol(dt, room)

            if self.has_los and self.cooldown_timer <= 0.0:
                # Try tactical teleport before windup if off cooldown and not revealed
                if self.teleport_cooldown <= 0.0 and not self.has_status("revealed"):
                    teleported = self.try_teleport(aim_target, room)
                    if teleported:
                        self.teleport_cooldown = 4.0

                self.state = STATE_WINDUP
                self.state_timer = self.cfg.windup_time
                self.telegraph_active = True
                self.facing = "right" if aim_target.x > self.x else "left"

        # 2. WINDUP
        elif self.state == STATE_WINDUP:
            self.vx = 0.0
            self.facing = "right" if aim_target.x > self.x else "left"
            self.state_timer = max(0.0, self.state_timer - dt)

            ex = self.x + self.cfg.width / 2.0
            ey = self.y + 14.0
            tx = aim_target.x + aim_target.width / 2.0
            ty = aim_target.y + aim_target.height / 2.0
            self.target_aim_pos = (tx, ty)

            if not self.has_los:
                self.state = STATE_PATROL
                self.telegraph_active = False
                self.is_channeling = False

            elif self.state_timer <= 0.0:
                self.state = STATE_ATTACK
                self.state_timer = 1.0  # Channel duration
                self.is_channeling = True

        # 3. ATTACK (Coherence Drain Channel)
        elif self.state == STATE_ATTACK:
            self.vx = 0.0
            self.state_timer = max(0.0, self.state_timer - dt)

            if self.has_los and self.is_channeling:
                drain_amount = self.cfg.coherence_drain_dps * dt
                if hasattr(player, "drain_coherence"):
                    player.drain_coherence(drain_amount)
                elif hasattr(player, "coherence"):
                    player.coherence = max(0.0, player.coherence - drain_amount)

            if self.state_timer <= 0.0 or not self.has_los:
                self.is_channeling = False
                self.telegraph_active = False
                self.state = STATE_RECOVERY
                self.state_timer = self.cfg.recovery_time
                self.cooldown_timer = self.cfg.attack_cooldown

        self.rect.topleft = (int(self.x), int(self.y))


class ChrysalisSplicer(Enemy):
    """
    Biomechanical hybrid insectoid/synth from the Chrysalis faction.
    Spits parabolic ballistic acid arcs over barriers.
    Counterplay:
      - Acid splash is absorbed by low cover (crouch / slide).
      - Pressurized internal sacs rupture from piercing weapons (e.g. coilgun), dealing 1.5x damage.
    """

    def __init__(
        self,
        target_id: str,
        x: float,
        y: float,
        cfg: Optional[EnemyConfig] = None,
        patrol_left: Optional[float] = None,
        patrol_right: Optional[float] = None,
    ):
        config_obj = cfg or EnemyConfig.load("chrysalis_splicer")
        super().__init__(target_id, x, y, config_obj, patrol_left, patrol_right)

    def take_damage(
        self,
        amount: int,
        hit_id: str = "",
        knockback: Tuple[float, float] = (0.0, 0.0),
        hit_pos: Tuple[float, float] = (0.0, 0.0),
    ) -> HitResult:
        # Piercing vulnerability: coilgun or piercing attacks deal 1.5x rupture damage
        if "pierce" in hit_id or "coilgun" in hit_id or "fibonacci" in hit_id:
            amount = int(amount * 1.50)
        return super().take_damage(amount, hit_id, knockback, hit_pos)

    def update(
        self,
        dt: float,
        player: Any,
        room: Room,
        manager: Any,
        is_paused: bool = False,
        decoy: Optional[Any] = None,
    ):
        if is_paused or dt <= 0.0:
            return

        super().update(dt)

        if self.has_status("stun"):
            self.telegraph_active = False
            self.vx = 0.0
            self.vy = 0.0
            self.rect.topleft = (int(self.x), int(self.y))
            return

        self.anim_time += dt
        if self.cooldown_timer > 0.0:
            self.cooldown_timer = max(0.0, self.cooldown_timer - dt)

        if self.state == STATE_DEATH:
            self.state_timer = max(0.0, self.state_timer - dt)
            return

        if self.state == STATE_HURT:
            self.state_timer = max(0.0, self.state_timer - dt)
            if self.state_timer <= 0.0:
                self.state = STATE_RECOVERY
                self.state_timer = self.cfg.recovery_time
            self.rect.topleft = (int(self.x), int(self.y))
            return

        if self.state == STATE_RECOVERY:
            self.state_timer = max(0.0, self.state_timer - dt)
            if self.state_timer <= 0.0:
                self.state = STATE_PATROL
            self.rect.topleft = (int(self.x), int(self.y))
            return

        aim_target = decoy if (decoy and not getattr(decoy, "is_dead", False)) else player
        self.has_los = self.check_line_of_sight(aim_target, room)

        # 1. PATROL
        if self.state == STATE_PATROL:
            self.telegraph_active = False
            speed = self.cfg.patrol_speed
            if self.facing == "left":
                self.vx = -speed
                if self.x <= self.patrol_left:
                    self.facing = "right"
            else:
                self.vx = speed
                if self.x >= self.patrol_right:
                    self.facing = "left"

            self.step_patrol(dt, room)

            if self.has_los and self.cooldown_timer <= 0.0:
                self.state = STATE_WINDUP
                self.state_timer = self.cfg.windup_time
                self.telegraph_active = True
                self.facing = "right" if aim_target.x > self.x else "left"

        # 2. WINDUP
        elif self.state == STATE_WINDUP:
            self.vx = 0.0
            self.facing = "right" if aim_target.x > self.x else "left"
            self.state_timer = max(0.0, self.state_timer - dt)

            ex = self.x + self.cfg.width / 2.0
            ey = self.y + 12.0
            tx = aim_target.x + aim_target.width / 2.0
            ty = aim_target.y + aim_target.height / 2.0
            self.target_aim_pos = (tx, ty)

            if not self.has_los:
                self.state = STATE_PATROL
                self.telegraph_active = False

            elif self.state_timer <= 0.0:
                self.state = STATE_ATTACK
                dir_x = 1.0 if self.facing == "right" else -1.0
                # Launch ballistic parabolic acid blob
                manager.spawn_enemy_projectile(
                    origin_x=ex,
                    origin_y=ey,
                    dir_x=dir_x,
                    dir_y=-0.5,
                    speed=self.cfg.projectile_speed,
                    damage=self.cfg.projectile_damage,
                    source_id=self.target_id,
                    color=(60, 220, 130),
                    gravity=380.0,
                    vx=dir_x * 200.0,
                    vy=-160.0,
                    length=10.0,
                    thickness=4.0,
                )
                self.telegraph_active = False
                self.state = STATE_RECOVERY
                self.state_timer = self.cfg.recovery_time
                self.cooldown_timer = self.cfg.attack_cooldown

        self.rect.topleft = (int(self.x), int(self.y))


class PrecursorGuardian(Enemy):
    """
    Subterranean ancient hominid construct with heavy stone-fused fists.
    Executes a leaping ground shockwave slam that sends seismic waves along the floor.
    Counterplay:
      - Shockwave travels strictly on the floor (ground_only). Jumping or catwalk elevation completely avoids damage.
      - Locked in extended recovery (0.8s) post-slam, creating a wide counter-attack window.
    """

    def __init__(
        self,
        target_id: str,
        x: float,
        y: float,
        cfg: Optional[EnemyConfig] = None,
        patrol_left: Optional[float] = None,
        patrol_right: Optional[float] = None,
    ):
        config_obj = cfg or EnemyConfig.load("precursor_guardian")
        super().__init__(target_id, x, y, config_obj, patrol_left, patrol_right)

    def update(
        self,
        dt: float,
        player: Any,
        room: Room,
        manager: Any,
        is_paused: bool = False,
        decoy: Optional[Any] = None,
    ):
        if is_paused or dt <= 0.0:
            return

        super().update(dt)

        if self.has_status("stun"):
            self.telegraph_active = False
            self.vx = 0.0
            self.vy = 0.0
            self.rect.topleft = (int(self.x), int(self.y))
            return

        self.anim_time += dt
        if self.cooldown_timer > 0.0:
            self.cooldown_timer = max(0.0, self.cooldown_timer - dt)

        if self.state == STATE_DEATH:
            self.state_timer = max(0.0, self.state_timer - dt)
            return

        if self.state == STATE_HURT:
            self.state_timer = max(0.0, self.state_timer - dt)
            if self.state_timer <= 0.0:
                self.state = STATE_RECOVERY
                self.state_timer = self.cfg.recovery_time
            self.rect.topleft = (int(self.x), int(self.y))
            return

        if self.state == STATE_RECOVERY:
            self.state_timer = max(0.0, self.state_timer - dt)
            if self.state_timer <= 0.0:
                self.state = STATE_PATROL
            self.rect.topleft = (int(self.x), int(self.y))
            return

        aim_target = decoy if (decoy and not getattr(decoy, "is_dead", False)) else player
        self.has_los = self.check_line_of_sight(aim_target, room)

        # 1. PATROL
        if self.state == STATE_PATROL:
            self.telegraph_active = False
            speed = self.cfg.patrol_speed
            if self.facing == "left":
                self.vx = -speed
                if self.x <= self.patrol_left:
                    self.facing = "right"
            else:
                self.vx = speed
                if self.x >= self.patrol_right:
                    self.facing = "left"

            self.step_patrol(dt, room)

            if self.has_los and self.cooldown_timer <= 0.0:
                self.state = STATE_WINDUP
                self.state_timer = self.cfg.windup_time
                self.telegraph_active = True
                self.facing = "right" if aim_target.x > self.x else "left"

        # 2. WINDUP
        elif self.state == STATE_WINDUP:
            self.vx = 0.0
            self.facing = "right" if aim_target.x > self.x else "left"
            self.state_timer = max(0.0, self.state_timer - dt)

            tx = aim_target.x + aim_target.width / 2.0
            ty = aim_target.y + aim_target.height / 2.0
            self.target_aim_pos = (tx, ty)

            if not self.has_los:
                self.state = STATE_PATROL
                self.telegraph_active = False

            elif self.state_timer <= 0.0:
                self.state = STATE_ATTACK
                # Spawn left and right ground shockwaves
                ground_y = self.y + self.cfg.height - 4
                manager.spawn_enemy_projectile(
                    origin_x=self.x,
                    origin_y=ground_y,
                    dir_x=-1.0,
                    dir_y=0.0,
                    speed=self.cfg.shockwave_speed,
                    damage=self.cfg.shockwave_damage,
                    source_id=self.target_id,
                    color=(245, 205, 65),
                    is_shockwave=True,
                    ground_only=True,
                    length=18.0,
                    thickness=4.0,
                )
                manager.spawn_enemy_projectile(
                    origin_x=self.x + self.cfg.width,
                    origin_y=ground_y,
                    dir_x=1.0,
                    dir_y=0.0,
                    speed=self.cfg.shockwave_speed,
                    damage=self.cfg.shockwave_damage,
                    source_id=self.target_id,
                    color=(245, 205, 65),
                    is_shockwave=True,
                    ground_only=True,
                    length=18.0,
                    thickness=4.0,
                )
                self.telegraph_active = False
                self.state = STATE_RECOVERY
                self.state_timer = self.cfg.recovery_time
                self.cooldown_timer = self.cfg.attack_cooldown

        self.rect.topleft = (int(self.x), int(self.y))


class TemporalPhantom(Enemy):
    """
    Wireframe timeline anomaly flickering between alternate quantum states.
    Phasing damage reduction: takes 75% reduced damage while unanchored.
    Counterplay: Tagging with Scattergun (revealed status) collapses its quantum superposition,
    anchoring the wireframe into the current timeline and dealing 1.5x amplified damage.
    """

    def __init__(
        self,
        target_id: str,
        x: float,
        y: float,
        cfg: Optional[EnemyConfig] = None,
        patrol_left: Optional[float] = None,
        patrol_right: Optional[float] = None,
    ):
        config_obj = cfg or EnemyConfig.load("temporal_phantom")
        super().__init__(target_id, x, y, config_obj, patrol_left, patrol_right)

    def take_damage(
        self,
        amount: int,
        hit_id: str = "",
        knockback: Tuple[float, float] = (0.0, 0.0),
        hit_pos: Tuple[float, float] = (0.0, 0.0),
    ) -> HitResult:
        if self.is_dead:
            return super().take_damage(amount, hit_id, knockback, hit_pos)

        # Counterplay: revealed status anchors phantom and amplifies damage
        if self.has_status("revealed"):
            anchored_amount = int(amount * 1.50)
            rev_time = self.status_effects.pop("revealed")
            res = super().take_damage(anchored_amount, hit_id, knockback, hit_pos)
            self.status_effects["revealed"] = rev_time
            return res

        # Default unanchored phasing: 75% damage reduction (takes 25%)
        phasing_amount = max(1, int(amount * 0.25))
        return super().take_damage(phasing_amount, hit_id, knockback, hit_pos)

    def update(
        self,
        dt: float,
        player: Any,
        room: Room,
        manager: Any,
        is_paused: bool = False,
        decoy: Optional[Any] = None,
    ):
        if is_paused or dt <= 0.0:
            return

        super().update(dt)

        if self.has_status("stun"):
            self.telegraph_active = False
            self.vx = 0.0
            self.vy = 0.0
            self.rect.topleft = (int(self.x), int(self.y))
            return

        self.anim_time += dt
        if self.cooldown_timer > 0.0:
            self.cooldown_timer = max(0.0, self.cooldown_timer - dt)

        if self.state == STATE_DEATH:
            self.state_timer = max(0.0, self.state_timer - dt)
            return

        if self.state == STATE_HURT:
            self.state_timer = max(0.0, self.state_timer - dt)
            if self.state_timer <= 0.0:
                self.state = STATE_RECOVERY
                self.state_timer = self.cfg.recovery_time
            self.rect.topleft = (int(self.x), int(self.y))
            return

        if self.state == STATE_RECOVERY:
            self.state_timer = max(0.0, self.state_timer - dt)
            if self.state_timer <= 0.0:
                self.state = STATE_PATROL
            self.rect.topleft = (int(self.x), int(self.y))
            return

        aim_target = decoy if (decoy and not getattr(decoy, "is_dead", False)) else player
        self.has_los = self.check_line_of_sight(aim_target, room)

        # 1. PATROL
        if self.state == STATE_PATROL:
            self.telegraph_active = False
            speed = self.cfg.patrol_speed
            if self.facing == "left":
                self.vx = -speed
                if self.x <= self.patrol_left:
                    self.facing = "right"
            else:
                self.vx = speed
                if self.x >= self.patrol_right:
                    self.facing = "left"

            self.step_patrol(dt, room)

            if self.has_los and self.cooldown_timer <= 0.0:
                self.state = STATE_WINDUP
                self.state_timer = self.cfg.windup_time
                self.telegraph_active = True
                self.facing = "right" if aim_target.x > self.x else "left"

        # 2. WINDUP
        elif self.state == STATE_WINDUP:
            self.vx = 0.0
            self.facing = "right" if aim_target.x > self.x else "left"
            self.state_timer = max(0.0, self.state_timer - dt)

            ex = self.x + self.cfg.width / 2.0
            ey = self.y + 14.0
            tx = aim_target.x + aim_target.width / 2.0
            ty = aim_target.y + aim_target.height / 2.0
            dx, dy = tx - ex, ty - ey
            dist = math.hypot(dx, dy)
            if dist > 1e-4:
                self.locked_aim_vector = (dx / dist, dy / dist)
            self.target_aim_pos = (tx, ty)

            if not self.has_los:
                self.state = STATE_PATROL
                self.telegraph_active = False

            elif self.state_timer <= 0.0:
                self.state = STATE_ATTACK
                dir_x, dir_y = self.locked_aim_vector
                manager.spawn_enemy_projectile(
                    origin_x=ex,
                    origin_y=ey,
                    dir_x=dir_x,
                    dir_y=dir_y,
                    speed=self.cfg.projectile_speed,
                    damage=self.cfg.projectile_damage,
                    source_id=self.target_id,
                    color=(230, 160, 40),
                )
                self.telegraph_active = False
                self.state = STATE_RECOVERY
                self.state_timer = self.cfg.recovery_time
                self.cooldown_timer = self.cfg.attack_cooldown

        self.rect.topleft = (int(self.x), int(self.y))


@dataclass
class EnemyProjectile:
    """Active enemy energy projectile, parabolic acid spit, or ground shockwave."""
    id: str
    x: float
    y: float
    vx: float
    vy: float
    dir_x: float
    dir_y: float
    damage: int
    lifetime: float
    source_id: str
    active: bool = True
    length: float = 14.0
    thickness: float = 3.0
    color: Tuple[int, int, int] = (255, 30, 66)
    gravity: float = 0.0
    is_shockwave: bool = False
    ground_only: bool = False


class EnemyManager:
    """
    Coordinates enemy lifecycles, offscreen culling, enemy projectiles,
    predictive targeting lines, and player damage resolution.
    """

    def __init__(self):
        self.enemies: List[Enemy] = []
        self.projectiles: List[EnemyProjectile] = []
        self.sparks: List[Dict[str, Any]] = []
        self.sprite_cache: Dict[str, pygame.Surface] = {}
        self._flipped_sprites: Dict[str, Tuple[pygame.Surface, pygame.Surface]] = {}
        self._hostile_rims: Dict[Tuple[str, bool], Tuple[pygame.Surface, pygame.Surface]] = {}
        self._telegraph_surface: Optional[pygame.Surface] = None
        self._next_proj_id: int = 1
        self._load_sprites()

    def _load_sprites(self):
        """Load canonical frame files through their animation aliases."""
        self.sprite_cache.clear()
        self._flipped_sprites.clear()
        self._hostile_rims.clear()
        root = ENEMY_SPRITES_DIR.resolve()
        try:
            manifest_path = _inside_without_symlinks(root, Path("manifest.json"))
            entries = json.loads(manifest_path.read_text(encoding="utf-8"))["enemies"]
        except (OSError, ValueError, KeyError, TypeError):
            return
        if not isinstance(entries, dict):
            return
        decoded = {}
        for name in (
            "core_recon_drone", "static_hound", "core_enforcer", "core_operative",
            "shield_hound", "phase_watcher", "chrysalis_splicer", "precursor_guardian",
            "temporal_phantom",
        ):
            entry = entries.get(name, {})
            animations = entry.get("animations", {}) if isinstance(entry, dict) else {}
            if not isinstance(animations, dict):
                continue
            for animation, clip in animations.items():
                if not isinstance(animation, str) or not isinstance(clip, dict):
                    continue
                frames = clip.get("frames", [])
                if not isinstance(frames, list):
                    continue
                key_name = "pounce" if animation == "attack" and "hound" in name else animation
                for index, frame in enumerate(frames, 1):
                    try:
                        if not isinstance(frame, str):
                            raise ValueError("Enemy frame path must be a string")
                        relative = Path(frame)
                        if (relative.is_absolute() or ".." in relative.parts
                                or relative.parts[:3] != ("sprites", "enemies", name)):
                            raise ValueError("Enemy frame must stay in its own sprite family")
                        path = _inside_without_symlinks(root, Path(*relative.parts[2:]))
                        if path not in decoded:
                            decoded[path] = pygame.image.load(str(path)).convert_alpha()
                        key = f"{name}_{key_name}" + (f"_{index}" if len(frames) > 1 else "")
                        self.sprite_cache[key] = decoded[path]
                    except (OSError, ValueError, pygame.error):
                        continue

    def add_enemy(self, enemy: Enemy):
        """Register enemy in manager."""
        self.enemies.append(enemy)

    def clear(self):
        """Purge all enemies and projectiles."""
        self.enemies.clear()
        self.projectiles.clear()
        self.sparks.clear()
        self._flipped_sprites.clear()
        self._hostile_rims.clear()
        self._telegraph_surface = None

    def reset_all(self):
        """Reset all living and defeated enemies back to spawn points."""
        for enemy in self.enemies:
            enemy.reset_to_spawn()
        self.projectiles.clear()
        self.sparks.clear()

    def spawn_enemy_projectile(
        self,
        origin_x: float,
        origin_y: float,
        dir_x: float,
        dir_y: float,
        speed: float,
        damage: int,
        source_id: str,
        color: Tuple[int, int, int] = (255, 30, 66),
        lifetime: float = 1.0,
        gravity: float = 0.0,
        is_shockwave: bool = False,
        ground_only: bool = False,
        length: float = 14.0,
        thickness: float = 3.0,
        vx: Optional[float] = None,
        vy: Optional[float] = None,
    ) -> EnemyProjectile:
        """Spawn enemy laser pulse, ballistic acid, or seismic shockwave."""
        actual_vx = vx if vx is not None else dir_x * speed
        actual_vy = vy if vy is not None else dir_y * speed
        proj = EnemyProjectile(
            id=f"eproj_{self._next_proj_id:05d}",
            x=origin_x,
            y=origin_y,
            vx=actual_vx,
            vy=actual_vy,
            dir_x=dir_x,
            dir_y=dir_y,
            damage=damage,
            lifetime=lifetime,
            source_id=source_id,
            color=color,
            gravity=gravity,
            is_shockwave=is_shockwave,
            ground_only=ground_only,
            length=length,
            thickness=thickness,
        )
        self._next_proj_id += 1
        self.projectiles.append(proj)
        return proj

    def add_sparks(self, x: float, y: float, count: int = 4, color=(255, 60, 60)):
        """Spawn transient impact spark particles."""
        for i in range(count):
            ang = (i / max(1, count)) * 2.0 * math.pi
            sp = 35.0 + (i * 10.0)
            self.sparks.append({
                "x": x,
                "y": y,
                "vx": math.cos(ang) * sp,
                "vy": math.sin(ang) * sp,
                "life": 0.12,
                "max_life": 0.12,
                "color": color,
            })

    def update(
        self,
        dt: float,
        player: Any,
        room: Room,
        camera: Optional[Camera] = None,
        is_paused: bool = False,
        actor_time_modifier: float = 1.0,
        decoy: Optional[Any] = None,
    ):
        """Step all enemy logic, line-of-sight checks, and enemy projectiles."""
        if is_paused or dt <= 0.0:
            return

        # Query actor time modifier and decoy from player abilities if attached
        if hasattr(player, "abilities") and player.abilities is not None:
            if actor_time_modifier == 1.0:
                actor_time_modifier = player.abilities.get_actor_time_modifier()
            if decoy is None:
                decoy = player.abilities.get_active_decoy()

        eff_dt = dt * actor_time_modifier

        # 1. Update sparks
        surviving_sparks = []
        for sp in self.sparks:
            sp["x"] += sp["vx"] * eff_dt
            sp["y"] += sp["vy"] * eff_dt
            sp["life"] -= eff_dt
            if sp["life"] > 0.0:
                surviving_sparks.append(sp)
        self.sparks = surviving_sparks

        # 2. Update enemies (with camera offscreen culling)
        cam_x = camera.x if camera else 0.0
        active_min_x = cam_x - 96.0
        active_max_x = cam_x + (camera.viewport_w if camera else 480.0) + 96.0

        for enemy in self.enemies:
            # Offscreen enemies remain in passive patrol
            if enemy.x < active_min_x or enemy.x > active_max_x:
                if enemy.state in (STATE_WINDUP, STATE_ATTACK):
                    enemy.state = STATE_PATROL
                    enemy.telegraph_active = False
                continue

            enemy.update(eff_dt, player, room, self, is_paused=is_paused, decoy=decoy)

            dash_rect = getattr(player, "dash_sweep_rect", None) or getattr(player, "dash_attack_rect", None)
            if not enemy.is_dead and getattr(player, "is_dashing", False) and dash_rect and dash_rect.colliderect(enemy.rect):
                player.apply_dash_attack(enemy)

            # Slide-kick interaction from player
            if getattr(player, "is_sliding", False) and not enemy.is_dead:
                sk_rect = getattr(player, "slide_kick_rect", None)
                if sk_rect and sk_rect.colliderect(enemy.rect):
                    if enemy.target_id not in player.slide_damaged_targets:
                        player.slide_damaged_targets.add(enemy.target_id)
                        if hasattr(enemy, "on_slide_kicked"):
                            enemy.on_slide_kicked()
                        enemy.take_damage(
                            player.cfg.slide_kick_damage,
                            hit_id=f"slide_kick_{id(player)}",
                            knockback=(player.vx * 0.5, -80.0),
                            hit_pos=(enemy.x + enemy.cfg.width / 2.0, enemy.y + enemy.cfg.height / 2.0),
                        )
                        # Damage normally switches survivors to HURT. Preserve the
                        # counter's intended recovery after applying its damage,
                        # without replacing a lethal DEATH state.
                        if not enemy.is_dead and hasattr(enemy, "on_slide_kicked"):
                            enemy.on_slide_kicked()
                        self.add_sparks(enemy.x + enemy.cfg.width / 2.0, enemy.y + enemy.cfg.height / 2.0, count=5, color=(255, 200, 60))

        # Claim each actual enemy defeat once, even if the player is dead or
        # the profile later changes. Room retreats remove living enemies only.
        for enemy in self.enemies:
            if isinstance(enemy, Enemy) and enemy.is_dead and not enemy._assisted_defeat_claimed:
                enemy._assisted_defeat_claimed = True
                recover = getattr(player, "recover_health_on_enemy_defeat", None)
                if recover is not None:
                    recover()

        # 3. Update enemy projectiles (swept continuous collision)
        surviving_proj = []
        for proj in self.projectiles:
            if not proj.active:
                continue

            if proj.gravity != 0.0:
                proj.vy += proj.gravity * eff_dt

            x0, y0 = proj.x, proj.y
            x1 = x0 + proj.vx * eff_dt
            y1 = y0 + proj.vy * eff_dt

            # Swept ray against solid tiles
            wall_hit, wx, wy, _, _ = check_swept_ray_tile_collision(room, x0, y0, x1, y1)
            w_dist = math.hypot(wx - x0, wy - y0) if wall_hit else float("inf")

            # Swept ray against decoy if active
            d_hit = False
            dx_hit, dy_hit = 0.0, 0.0
            d_dist = float("inf")
            if decoy and not getattr(decoy, "is_dead", False):
                clip_d = decoy.rect.clipline((x0, y0), (x1, y1))
                if clip_d:
                    dx_hit, dy_hit = float(clip_d[0][0]), float(clip_d[0][1])
                    d_dist = math.hypot(dx_hit - x0, dy_hit - y0)

            # Swept ray against player
            p_hit = False
            px_hit, py_hit = 0.0, 0.0
            p_dist = float("inf")

            clip = player.rect.clipline((x0, y0), (x1, y1))
            if clip:
                px_hit, py_hit = float(clip[0][0]), float(clip[0][1])
                p_dist = math.hypot(px_hit - x0, py_hit - y0)

            # Check ground_only projectile counterplay: jumping avoids shockwave!
            if proj.ground_only:
                is_player_grounded = getattr(player, "is_grounded", False)
                player_feet = player.y + 32.0
                if not is_player_grounded or (player_feet < proj.y - 6.0):
                    p_dist = float("inf")  # Pass harmlessly under airborne player

            # Check if projectile hits decoy first
            if d_dist <= w_dist and d_dist <= p_dist and d_dist < float("inf"):
                proj.active = False
                proj.x = dx_hit
                proj.y = dy_hit
                self.add_sparks(dx_hit, dy_hit, count=5, color=(120, 220, 255))
                if hasattr(decoy, "take_damage"):
                    decoy.take_damage(proj.damage)
                continue

            if p_dist <= w_dist and p_dist < float("inf"):
                # Hit player before wall
                proj.active = False
                proj.x = px_hit
                proj.y = py_hit
                self.add_sparks(px_hit, py_hit, count=5, color=proj.color)

                # Low cover check
                attack_dir = "left" if proj.vx > 0 else "right"
                is_prot = False
                if hasattr(player, "is_protected_from_attack"):
                    is_prot = player.is_protected_from_attack(room, attack_dir)
                elif hasattr(player, "check_protection"):
                    is_prot = player.check_protection(attack_dir, room)

                if is_prot:
                    # Absorbed by sandbag cover!
                    self.add_sparks(px_hit, py_hit, count=4, color=(160, 140, 100))
                else:
                    player.take_damage(
                        proj.damage,
                        knockback_vx=proj.dir_x * 80.0,
                        knockback_vy=-80.0,
                        damage_source="hostile",
                    )
                continue

            if wall_hit:
                # Stopped by solid wall
                proj.active = False
                proj.x = wx
                proj.y = wy
                self.add_sparks(wx, wy, count=4, color=proj.color)
                continue

            # Advance
            proj.x = x1
            proj.y = y1
            proj.lifetime -= eff_dt
            if proj.lifetime <= 0.0:
                proj.active = False
                continue

            surviving_proj.append(proj)

        self.projectiles = surviving_proj

    def _get_enemy_prefix(self, enemy: Enemy) -> str:
        """Resolve sprite prefix from enemy archetype."""
        if isinstance(enemy, CoreReconDrone):
            return "core_recon_drone"
        if isinstance(enemy, StaticHound):
            return "static_hound"
        if isinstance(enemy, CoreEnforcer):
            return "core_enforcer"
        if isinstance(enemy, CoreOperative):
            return "core_operative"
        if isinstance(enemy, ShieldHound):
            return "shield_hound"
        if isinstance(enemy, PhaseWatcher):
            return "phase_watcher"
        if isinstance(enemy, ChrysalisSplicer):
            return "chrysalis_splicer"
        if isinstance(enemy, PrecursorGuardian):
            return "precursor_guardian"
        if isinstance(enemy, TemporalPhantom):
            return "temporal_phantom"
        return getattr(enemy.cfg, "id", "core_recon_drone")

    def _hostile_rim(self, key: str, mirrored: bool, source: pygame.Surface,
                     drawn: pygame.Surface) -> pygame.Surface:
        """Cache a one-pixel silhouette behind this exact sprite and orientation."""
        cache_key = (key, mirrored)
        cached = self._hostile_rims.get(cache_key)
        if cached is None or cached[0] is not source:
            if len(self._hostile_rims) >= 64:
                self._hostile_rims.clear()
            mask = pygame.mask.from_surface(drawn, 1)
            silhouette = mask.to_surface(setcolor=(255, 190, 92, 255),
                                         unsetcolor=(0, 0, 0, 0))
            rim = pygame.Surface((drawn.get_width() + 2, drawn.get_height() + 2), pygame.SRCALPHA)
            for offset in ((0, 1), (2, 1), (1, 0), (1, 2)):
                rim.blit(silhouette, offset)
            cached = (source, rim)
            self._hostile_rims[cache_key] = cached
        return cached[1]

    def render(self, surface: pygame.Surface, camera: Camera, *, highlight_hostiles: bool = False):
        """Render telegraph lines, enemy sprites, and projectiles."""
        # 1. Telegraph Warning Lasers & Aim Lines
        for enemy in self.enemies:
            if enemy.is_dead or not enemy.telegraph_active:
                continue

            em_wx = enemy.x + enemy.cfg.width / 2.0
            em_wy = enemy.y + enemy.cfg.height / 2.0
            em_sx, em_sy = camera.world_to_screen(em_wx, em_wy)

            if isinstance(enemy, CoreReconDrone):
                dx, dy = enemy.locked_aim_vector
                beam_len = 320.0
                end_wx = em_wx + dx * beam_len
                end_wy = em_wy + dy * beam_len
                end_sx, end_sy = camera.world_to_screen(end_wx, end_wy)

                if enemy.telegraph_locked:
                    pygame.draw.line(surface, (255, 30, 66), (em_sx, em_sy), (end_sx, end_sy), 2)
                    pygame.draw.line(surface, (255, 230, 230), (em_sx, em_sy), (end_sx, end_sy), 1)
                    tx, ty = camera.world_to_screen(enemy.target_aim_pos[0], enemy.target_aim_pos[1])
                    pygame.draw.circle(surface, (255, 30, 66), (tx, ty), 6, 1)
                else:
                    if self._telegraph_surface is None or self._telegraph_surface.get_size() != surface.get_size():
                        self._telegraph_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
                    laser_surf = self._telegraph_surface
                    laser_surf.fill((0, 0, 0, 0))
                    pygame.draw.line(laser_surf, (255, 30, 66, 140), (em_sx, em_sy), (end_sx, end_sy), 1)
                    surface.blit(laser_surf, (0, 0))

            elif isinstance(enemy, StaticHound) or isinstance(enemy, ShieldHound):
                hx, hy = camera.world_to_screen(enemy.x + enemy.cfg.width / 2.0, enemy.y + 6)
                pygame.draw.circle(surface, enemy.cfg.telegraph_color, (hx, hy), 8, 1)

            elif isinstance(enemy, PhaseWatcher):
                # Purple coherence drain beam
                tx, ty = camera.world_to_screen(enemy.target_aim_pos[0], enemy.target_aim_pos[1])
                pygame.draw.line(surface, (185, 115, 250), (em_sx, em_sy), (tx, ty), 2)
                pygame.draw.line(surface, (240, 220, 255), (em_sx, em_sy), (tx, ty), 1)

            elif isinstance(enemy, ChrysalisSplicer):
                # Green ballistic arc indicator
                tx, ty = camera.world_to_screen(enemy.target_aim_pos[0], enemy.target_aim_pos[1])
                mid_sx = (em_sx + tx) // 2
                mid_sy = min(em_sy, ty) - 24
                pygame.draw.lines(surface, (60, 220, 130), False, [(em_sx, em_sy), (mid_sx, mid_sy), (tx, ty)], 1)

            elif isinstance(enemy, PrecursorGuardian):
                # Golden seismic ground circle
                gx, gy = camera.world_to_screen(enemy.x + enemy.cfg.width / 2.0, enemy.y + enemy.cfg.height - 2)
                pygame.draw.ellipse(surface, (245, 205, 65), (gx - 24, gy - 6, 48, 12), 2)

            elif isinstance(enemy, TemporalPhantom):
                # Rising phase motes replace the old rectangular wireframe.
                bx, by = camera.world_to_screen(enemy.x, enemy.y)
                render_attack_field(surface, (bx - 2, by - 2, enemy.cfg.width + 4, enemy.cfg.height + 4),
                                    color=(230, 160, 40), time=enemy.anim_time, arrival=True)

            else:
                # Default linear telegraph
                tx, ty = camera.world_to_screen(enemy.target_aim_pos[0], enemy.target_aim_pos[1])
                pygame.draw.line(surface, enemy.cfg.telegraph_color, (em_sx, em_sy), (tx, ty), 1)

        # 2. Render Enemy Sprites
        for enemy in self.enemies:
            if enemy.state == STATE_DEATH and enemy.state_timer <= 0.0:
                continue
            # Native-density actors draw their own body in the field scene.
            if getattr(enemy, "suppress_default_sprite", False):
                continue

            sx, sy = camera.world_to_screen(enemy.x, enemy.y)
            prefix = self._get_enemy_prefix(enemy)
            anim_name = enemy.state
            if anim_name == STATE_ATTACK and "hound" in prefix:
                anim_name = "pounce"

            frame_idx = 2 if int(enemy.anim_time * 8) % 2 == 1 else 1
            key = f"{prefix}_{anim_name}_{frame_idx}"
            if key not in self.sprite_cache:
                key = f"{prefix}_{anim_name}"
            if key not in self.sprite_cache:
                key = f"{prefix}_patrol_1"

            cached = self.sprite_cache.get(key)
            highlighted = (highlight_hostiles and not enemy.is_dead and
                           type(enemy) in (CoreReconDrone, StaticHound, CoreEnforcer))
            if cached:
                draw_surf = cached
                mirrored = enemy.facing == "right" and "hound" in prefix
                if mirrored:
                    pair = self._flipped_sprites.get(key)
                    if pair is None or pair[0] is not cached:
                        if len(self._flipped_sprites) >= 64:
                            self._flipped_sprites.clear()
                        pair = (cached, pygame.transform.flip(cached, True, False))
                        self._flipped_sprites[key] = pair
                    draw_surf = pair[1]
                if highlighted:
                    surface.blit(self._hostile_rim(key, mirrored, cached, draw_surf), (sx - 1, sy - 1))
                surface.blit(draw_surf, (sx, sy))
            else:
                pygame.draw.rect(surface, enemy.cfg.telegraph_color, (sx, sy, enemy.cfg.width, enemy.cfg.height), 2)
            if highlighted:
                mid = int(sx + enemy.cfg.width / 2)
                pygame.draw.lines(surface, (255, 190, 92), False,
                                  ((mid - 2, sy - 5), (mid, sy - 3), (mid + 2, sy - 5)), 1)

        # 3. Render Enemy Projectiles
        for proj in self.projectiles:
            hx, hy = camera.world_to_screen(proj.x, proj.y)
            if proj.is_shockwave:
                sw_w = 14
                sw_h = 10
                sw_sx, sw_sy = camera.world_to_screen(proj.x - sw_w / 2.0, proj.y - sw_h)
                pygame.draw.arc(surface, proj.color, (sw_sx, sw_sy, sw_w * 2, sw_h * 2), 0, math.pi, 2)
            else:
                tx_w = proj.x - proj.dir_x * proj.length
                ty_w = proj.y - proj.dir_y * proj.length
                tx, ty = camera.world_to_screen(tx_w, ty_w)
                pygame.draw.line(surface, proj.color, (tx, ty), (hx, hy), int(proj.thickness + 2))
                pygame.draw.line(surface, (255, 255, 255), (tx, ty), (hx, hy), int(proj.thickness))

        # 4. Render Sparks
        for sp in self.sparks:
            spx, spy = camera.world_to_screen(sp["x"], sp["y"])
            if 0 <= spx < surface.get_width() and 0 <= spy < surface.get_height():
                surface.set_at((spx, spy), sp["color"])
