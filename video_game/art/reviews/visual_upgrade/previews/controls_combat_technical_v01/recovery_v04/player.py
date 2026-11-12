"""
MODULE: video_game/engine/player.py
PURPOSE: Fixed-step kinematic player locomotion, collision resolution, jump buffers,
         coyote time, crouch, cover, slide-kicks, and health.
CALLED BY: video_game.engine.scenes.field, video_game.tests.test_player.
HOW TO MODIFY: Update physics tuning in video_game/data/balance.json; extend combat/animation in A04/A05.
"""

from dataclasses import dataclass, field, replace
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import pygame

from video_game.engine import config
from video_game.engine.world import (
    COLLISION_COVER,
    COLLISION_EMPTY,
    COLLISION_HAZARD,
    COLLISION_ONE_WAY,
    COLLISION_SOLID,
    Room,
    RoomCheckpoint,
)

BALANCE_PATH = Path(__file__).resolve().parent.parent / "data" / "balance.json"


def approach(current: float, target: float, max_delta: float) -> float:
    """Move current towards target by at most max_delta."""
    if current < target:
        return min(current + max_delta, target)
    elif current > target:
        return max(current - max_delta, target)
    return target


@dataclass
class PlayerConfig:
    """Tunable movement, combat, and simulation configuration."""
    walk_speed: float = 140.0
    run_speed: float = 180.0
    ground_acceleration: float = 1200.0
    ground_deceleration: float = 1400.0
    air_acceleration: float = 800.0
    air_deceleration: float = 600.0
    jump_velocity: float = -270.0
    jump_cut_multiplier: float = 0.5
    gravity: float = 720.0
    max_fall_speed: float = 360.0
    jump_buffer_time: float = 0.12
    coyote_time: float = 0.10
    player_width: int = 16
    player_height: int = 32
    crouch_height: int = 20
    slide_height: int = 14
    slide_speed: float = 220.0
    slide_duration: float = 0.35
    slide_cooldown: float = 0.20
    wall_slide_speed: float = 60.0
    wall_jump_vx: float = 200.0
    wall_jump_vy: float = -260.0
    grapple_speed: float = 280.0
    grapple_max_range: float = 160.0
    fibonacci_dash_speed: float = 360.0
    fibonacci_dash_duration: float = 0.20
    fibonacci_dash_cooldown: float = 0.60
    max_health: int = 100
    hazard_damage: int = 25
    hazard_invulnerability_time: float = 0.8
    hazard_knockback_vx: float = 120.0
    hazard_knockback_vy: float = -160.0
    slide_kick_damage: int = 35
    fibonacci_dash_damage: int = 30
    fixed_dt: float = 1.0 / 120.0
    max_accumulator: float = 0.10

    @classmethod
    def load_from_file(cls, path: Optional[Union[str, Path]] = None) -> "PlayerConfig":
        """Load configuration from balance.json."""
        p = Path(path) if path else BALANCE_PATH
        if not p.exists():
            return cls()
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        mv = data.get("movement", {})
        cb = data.get("combat", {})
        sm = data.get("simulation", {})
        return cls(
            walk_speed=float(mv.get("walk_speed", 140.0)),
            run_speed=float(mv.get("run_speed", 180.0)),
            ground_acceleration=float(mv.get("ground_acceleration", 1200.0)),
            ground_deceleration=float(mv.get("ground_deceleration", 1400.0)),
            air_acceleration=float(mv.get("air_acceleration", 800.0)),
            air_deceleration=float(mv.get("air_deceleration", 600.0)),
            jump_velocity=float(mv.get("jump_velocity", -270.0)),
            jump_cut_multiplier=float(mv.get("jump_cut_multiplier", 0.5)),
            gravity=float(mv.get("gravity", 720.0)),
            max_fall_speed=float(mv.get("max_fall_speed", 360.0)),
            jump_buffer_time=float(mv.get("jump_buffer_time", 0.12)),
            coyote_time=float(mv.get("coyote_time", 0.10)),
            player_width=int(mv.get("player_width", 16)),
            player_height=int(mv.get("player_height", 32)),
            crouch_height=int(mv.get("crouch_height", 20)),
            slide_height=int(mv.get("slide_height", 14)),
            slide_speed=float(mv.get("slide_speed", 220.0)),
            slide_duration=float(mv.get("slide_duration", 0.35)),
            slide_cooldown=float(mv.get("slide_cooldown", 0.20)),
            wall_slide_speed=float(mv.get("wall_slide_speed", 60.0)),
            wall_jump_vx=float(mv.get("wall_jump_vx", 200.0)),
            wall_jump_vy=float(mv.get("wall_jump_vy", -260.0)),
            grapple_speed=float(mv.get("grapple_speed", 280.0)),
            grapple_max_range=float(mv.get("grapple_max_range", 160.0)),
            fibonacci_dash_speed=float(mv.get("fibonacci_dash_speed", 360.0)),
            fibonacci_dash_duration=float(mv.get("fibonacci_dash_duration", 0.20)),
            fibonacci_dash_cooldown=float(mv.get("fibonacci_dash_cooldown", 0.60)),
            max_health=int(cb.get("max_health", 100)),
            hazard_damage=int(cb.get("hazard_damage", 25)),
            hazard_invulnerability_time=float(cb.get("hazard_invulnerability_time", 0.8)),
            hazard_knockback_vx=float(cb.get("hazard_knockback_vx", 120.0)),
            hazard_knockback_vy=float(cb.get("hazard_knockback_vy", -160.0)),
            slide_kick_damage=int(cb.get("slide_kick_damage", 35)),
            fibonacci_dash_damage=int(cb.get("fibonacci_dash_damage", 30)),
            fixed_dt=float(sm.get("fixed_dt", 1.0 / 120.0)),
            max_accumulator=float(sm.get("max_accumulator", 0.10)),
        )


@dataclass
class PlayerInput:
    """Action-level input representation decoupled from hardware keys."""
    move_x: float = 0.0          # -1.0 for left, +1.0 for right, 0.0 for idle
    move_y: float = 0.0          # -1.0 for up, +1.0 for down (crouch)
    jump_pressed: bool = False
    jump_held: bool = False
    jump_released: bool = False
    crouch_held: bool = False
    slide_pressed: bool = False
    dash_pressed: bool = False
    grapple_pressed: bool = False
    cover_pressed: bool = False
    fire_pressed: bool = False
    fire_held: bool = False
    fire_released: bool = False
    auto_fire_held: bool = False
    ability_pressed: bool = False
    cycle_weapon_pressed: bool = False
    cycle_ability_pressed: bool = False
    aim_x: Optional[float] = None
    aim_y: Optional[float] = None
    aim_target_x: Optional[float] = None
    aim_target_y: Optional[float] = None
    combat_assisted: bool = False

    @classmethod
    def from_input_manager(cls, input_mgr: Any) -> "PlayerInput":
        """Build PlayerInput from engine InputManager state."""
        mx = 0.0
        if input_mgr.held("move_left"):
            mx -= 1.0
        if input_mgr.held("move_right"):
            mx += 1.0

        my = 0.0
        if input_mgr.held("jump"):
            my -= 1.0
        if input_mgr.held("crouch"):
            my += 1.0

        crouch_held = input_mgr.held("crouch")
        crouch_pressed = input_mgr.pressed("crouch")
        slide_pressed = crouch_pressed and (input_mgr.held("move_left") or input_mgr.held("move_right"))
        dash_pressed = input_mgr.pressed("dash") if hasattr(input_mgr, "has_action") and input_mgr.has_action("dash") else False
        grapple_pressed = input_mgr.pressed("grapple") if hasattr(input_mgr, "has_action") and input_mgr.has_action("grapple") else False
        cover_pressed = input_mgr.pressed("interact")
        fire_pressed = input_mgr.pressed("fire")
        fire_held = input_mgr.held("fire")
        fire_released = input_mgr.released("fire")
        ability_pressed = input_mgr.pressed("ability")
        cycle_weapon_pressed = input_mgr.pressed("cycle_weapon")
        cycle_ability_pressed = input_mgr.pressed("cycle_ability")

        return cls(
            move_x=mx,
            move_y=my,
            jump_pressed=input_mgr.pressed("jump"),
            jump_held=input_mgr.held("jump"),
            jump_released=input_mgr.released("jump"),
            crouch_held=crouch_held,
            slide_pressed=slide_pressed,
            dash_pressed=dash_pressed,
            grapple_pressed=grapple_pressed,
            cover_pressed=cover_pressed,
            fire_pressed=fire_pressed,
            fire_held=fire_held,
            fire_released=fire_released,
            auto_fire_held=input_mgr.held("auto_fire"),
            ability_pressed=ability_pressed,
            cycle_weapon_pressed=cycle_weapon_pressed,
            cycle_ability_pressed=cycle_ability_pressed,
        )

    def apply_aim_context(self, input_mgr: Any, camera: Any, crt: Any) -> None:
        """Map an active pointer or stick to the current logical world viewport."""
        source = getattr(input_mgr, 'aim_source', None)
        if source == 'mouse':
            position = getattr(input_mgr, 'mouse_position', None)
            width, height = getattr(crt, 'win_w', 0), getattr(crt, 'win_h', 0)
            if position is not None and width > 0 and height > 0:
                x, y = position
                if 0 <= x < width and 0 <= y < height:
                    self.aim_target_x = x * config.INTERNAL_WIDTH / width + camera.x
                    self.aim_target_y = y * config.INTERNAL_HEIGHT / height + camera.y
        elif source == 'controller':
            aim = getattr(input_mgr, 'controller_aim', None)
            if aim is not None:
                self.aim_x, self.aim_y = aim


class Player:
    """
    Fixed-step kinematic player simulation.

    Manages sub-pixel position integration, acceleration, jump buffering,
    coyote time, crouch, legal standing clearance, cover states, slide-kicks,
    axis-separated collision resolution, one-way platform landing, hazard
    damage/knockback, and checkpoint respawning.
    """

    def __init__(self, x: float, y: float, config_obj: Optional[PlayerConfig] = None):
        self.cfg = config_obj or PlayerConfig.load_from_file()
        self.x: float = float(x)
        self.y: float = float(y)
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.facing: str = "right"
        self.weapon_facing: str = "right"
        self.aim_facing_active: bool = False
        self.is_grounded: bool = False
        self.is_crouching: bool = False
        self.is_sliding: bool = False
        self.in_cover: bool = False
        self.cover_type: Optional[str] = None
        self.health: int = self.cfg.max_health
        self.coherence: float = 100.0
        self.max_coherence: float = 100.0
        self.is_dead: bool = False
        self.respawn_count: int = 0

        # Timers and buffers
        self.coyote_timer: float = 0.0
        self.jump_buffer_timer: float = 0.0
        self.invulnerable_timer: float = 0.0
        self.knockback_active: bool = False
        self.slide_timer: float = 0.0
        self.slide_cooldown_timer: float = 0.0
        self.slide_damaged_targets: Set[str] = set()
        self.accumulator: float = 0.0

        # Checkpoints
        self.active_checkpoint_id: Optional[str] = None
        self.spawn_x: float = float(x)
        self.spawn_y: float = float(y)

        # Combat & recoil
        self.recoil_timer: float = 0.0
        self.weapon: Optional[Any] = None
        self.arsenal: Optional[Any] = None
        self.abilities: Optional[Any] = None

        # Advanced traversal states (S10)
        self.is_wall_sliding: bool = False
        self.wall_contact_dir: int = 0
        self.wall_jump_lock_timer: float = 0.0

        self.is_grappling: bool = False
        self.grapple_anchor: Optional[Any] = None
        self.grapple_anchor_pos: Optional[Tuple[float, float]] = None
        self._pending_grapple_press = False

        self.is_dashing: bool = False
        self.dash_timer: float = 0.0
        self.dash_cooldown_timer: float = 0.0
        self.dash_damaged_targets: Set[str] = set()

        # Prediction counterplay / Serendipity buff
        self.has_serendipity_buff: bool = False
        self.serendipity_timer: float = 0.0

        # Animation coordinator
        self.animator: Optional[Any] = None

    @property
    def width(self) -> int:
        return self.cfg.player_width

    @property
    def height(self) -> int:
        if self.is_sliding or self.is_dashing:
            return self.cfg.slide_height
        if self.is_crouching:
            return self.cfg.crouch_height
        return self.cfg.player_height

    @property
    def rect(self) -> pygame.Rect:
        """Bounding rectangle in integer world coordinates anchoring feet at y + 32."""
        if self.is_sliding or self.is_dashing:
            # Slide/dash footprint: top at y + 18, height 14 (feet at y + 32)
            return pygame.Rect(int(self.x), int(self.y + 18), self.width, 14)
        if self.is_crouching:
            # Crouch footprint: top at y + 12, height 20 (feet at y + 32)
            return pygame.Rect(int(self.x), int(self.y + 12), self.width, 20)
        return pygame.Rect(int(self.x), int(self.y), self.width, 32)

    @property
    def animation_state(self) -> str:
        """Categorical animation posture for sprite/rendering selection."""
        if self.is_dead:
            return "death"
        if self.in_cover and self.cover_type == "background":
            return "cover_background"
        if self.is_dashing or self.is_sliding:
            return "slide"
        if self.is_grappling:
            return "jump"
        if self.is_wall_sliding:
            return "crouch"
        if self.is_crouching:
            return "cover_low" if self.cover_type == "low" else "crouch"
        if not self.is_grounded:
            return "jump" if self.vy < 0.0 else "fall"
        if self.recoil_timer > 0.0:
            return "recoil"
        if abs(self.vx) > self.cfg.walk_speed * 1.1:
            return "run"
        if abs(self.vx) > 5.0:
            return "walk"
        return "idle"

    def discard_pending_edges(self):
        """Discard buffered grapple input when focus or controls are released."""
        self._pending_grapple_press = False

    def cancel_traversal(self):
        """Clear transient motion when leaving a scene or relocating rooms."""
        self.is_grappling = False
        self.grapple_anchor = None
        self.grapple_anchor_pos = None
        self._pending_grapple_press = False
        self.is_dashing = False
        self.dash_timer = 0.0
        self.dash_sweep_rect = None
        self.dash_damaged_targets.clear()
        self.is_sliding = False
        self.slide_timer = 0.0
        self.slide_damaged_targets.clear()
        self.is_wall_sliding = False
        self.wall_contact_dir = 0
        self.wall_jump_lock_timer = 0.0
        self.jump_buffer_timer = 0.0
        self.coyote_timer = 0.0
        self.accumulator = 0.0
        self.vx = self.vy = 0.0

    def trigger_fire_recoil(self, duration: float = 0.12):
        """Trigger weapon discharge recoil animation posture."""
        self.recoil_timer = duration

    def can_fire(self, room: Optional[Room] = None) -> bool:
        """Verify weapon discharge clearance (forbids firing while concealed in background cover)."""
        if self.is_dead:
            return False
        if self.in_cover and self.cover_type == "background":
            return False
        return True

    def get_muzzle_world_pos(self) -> Tuple[float, float]:
        """Query world coordinates of weapon muzzle from animation rig or fallback geometry."""
        foot_wx = float(self.x + (self.width / 2.0))
        foot_wy = float(self.y + 32.0)
        if self.animator is not None:
            pos = self.animator.get_attachment_world_pos("muzzle", foot_wx, foot_wy)
            if pos is not None:
                return float(pos[0]), float(pos[1])
        facing = self.weapon_facing if self.aim_facing_active else self.facing
        offset_x = (self.width + 4.0) if facing == "right" else -4.0
        offset_y = 14.0 if self.is_crouching else 18.0
        return float(self.x + offset_x), float(self.y + offset_y)

    @property
    def slide_kick_rect(self) -> Optional[pygame.Rect]:
        """Leading hitbox for slide-kick attack during active slide."""
        if not self.is_sliding:
            return None
        kick_w = 12
        kick_h = 14
        top = int(self.y + 18)
        if self.facing == "right":
            return pygame.Rect(int(self.x + self.width), top, kick_w, kick_h)
        return pygame.Rect(int(self.x - kick_w), top, kick_w, kick_h)

    def can_stand(self, room: Room) -> bool:
        """Check if legal 32px standing headroom clearance exists above Mateo."""
        # Top 12px region above crouch level (y .. y + 12)
        headroom_rect = pygame.Rect(int(self.x + 2), int(self.y), max(1, self.width - 4), 12)
        col = room.check_rect_collision(headroom_rect)
        return not col["solid"]

    def apply_slide_kick(self, target_id: str, target_health: int) -> Tuple[int, bool]:
        """Apply slide-kick damage to a target at most once per slide."""
        if not self.is_sliding or target_id in self.slide_damaged_targets:
            return target_health, False
        self.slide_damaged_targets.add(target_id)
        new_hp = max(0, target_health - self.cfg.slide_kick_damage)
        return new_hp, True

    @property
    def dash_attack_rect(self) -> Optional[pygame.Rect]:
        """Leading hitbox for dash attack during active Fibonacci dash."""
        if not self.is_dashing:
            return None
        dash_w = 16
        dash_h = 14
        top = int(self.y + 18)
        if self.facing == "right":
            return pygame.Rect(int(self.x + self.width), top, dash_w, dash_h)
        return pygame.Rect(int(self.x - dash_w), top, dash_w, dash_h)

    def apply_dash_attack(self, target: Any) -> bool:
        """Apply cadence dash damage to a target at most once per dash sequence."""
        if not self.is_dashing:
            return False
        tid = getattr(target, "id", None) or getattr(target, "enemy_id", None) or str(id(target))
        if tid in self.dash_damaged_targets:
            return False
        self.dash_damaged_targets.add(tid)
        dmg = int(self.cfg.fibonacci_dash_damage)
        if hasattr(target, "take_damage"):
            target.take_damage(dmg)
            return True
        elif hasattr(target, "health"):
            target.health = max(0, target.health - dmg)
            return True
        return False

    def check_protection(self, attack_direction: str, room: Room) -> bool:
        """Determine if an incoming attack is blocked by current cover / posture."""
        return room.check_attack_protection(
            self.rect,
            attack_direction,
            is_crouching=(self.is_crouching or self.is_sliding),
            in_background_cover=self.in_cover,
        )

    def is_protected_from_attack(self, room: Room, attack_direction: str) -> bool:
        """Alias for cover attack protection check."""
        return self.check_protection(attack_direction, room)

    def drain_coherence(self, amount: float):
        """Drain player mental/subspace coherence and ability energy."""
        if self.abilities is not None and getattr(self.abilities, "current_energy", 0.0) > 0:
            self.abilities.current_energy = max(0.0, self.abilities.current_energy - amount)
        self.coherence = max(0.0, self.coherence - amount)

    def set_checkpoint(self, checkpoint_id: str, x: float, y: float):
        """Register active checkpoint position for death recovery."""
        self.active_checkpoint_id = checkpoint_id
        self.spawn_x = float(x)
        self.spawn_y = float(y)

    def take_damage(
        self,
        amount: int,
        knockback_vx: Optional[float] = None,
        knockback_vy: Optional[float] = None,
        ignore_invulnerable: bool = False,
    ):
        """Apply damage and knockback unless invulnerable."""
        if self.is_dead:
            return
        if not ignore_invulnerable and self.invulnerable_timer > 0.0 and amount < self.health:
            return

        actual_amount = amount
        if self.abilities is not None:
            absorbed, spillover = self.abilities.absorb_shield_damage(actual_amount)
            actual_amount = spillover
            if actual_amount <= 0:
                # Completely absorbed by active phase shield
                return

        self.health = max(0, self.health - actual_amount)
        self.invulnerable_timer = self.cfg.hazard_invulnerability_time
        self.knockback_active = True
        self.is_grounded = False

        if knockback_vx is not None:
            self.vx = knockback_vx
        else:
            self.vx = -self.cfg.hazard_knockback_vx if self.facing == "right" else self.cfg.hazard_knockback_vx

        if knockback_vy is not None:
            self.vy = knockback_vy
        else:
            self.vy = self.cfg.hazard_knockback_vy

        if self.health <= 0:
            self.is_dead = True

    def respawn_at_checkpoint(self, room: Optional[Room] = None):
        """Restore player to active checkpoint or initial spawn with coherent full state."""
        self.respawn_count += 1
        target_x = self.spawn_x
        target_y = self.spawn_y

        if room and self.active_checkpoint_id:
            chk = next((c for c in room.checkpoints if c.id == self.active_checkpoint_id), None)
            if chk:
                target_x = chk.x
                target_y = chk.y
        elif room and not self.active_checkpoint_id:
            sp = room.spawns.get("bunker_exit") or room.spawns.get("default")
            if sp:
                target_x = sp.x
                target_y = sp.y

        self.x = target_x
        self.y = target_y
        self.vx = 0.0
        self.vy = 0.0
        self.health = self.cfg.max_health
        self.coherence = self.max_coherence
        self.is_dead = False
        self.is_grounded = True
        self.is_crouching = False
        self.is_sliding = False
        self.in_cover = False
        self.cover_type = None
        self.knockback_active = False
        self.invulnerable_timer = 0.0
        self.coyote_timer = 0.0
        self.jump_buffer_timer = 0.0
        self.slide_timer = 0.0
        self.slide_cooldown_timer = 0.0
        self.slide_damaged_targets.clear()
        self.is_wall_sliding = False
        self.wall_contact_dir = 0
        self.wall_jump_lock_timer = 0.0
        self.is_grappling = False
        self.grapple_anchor = None
        self.grapple_anchor_pos = None
        self._pending_grapple_press = False
        self.is_dashing = False
        self.dash_timer = 0.0
        self.dash_cooldown_timer = 0.0
        self.dash_damaged_targets.clear()
        self.has_serendipity_buff = False
        self.serendipity_timer = 0.0
        self.accumulator = 0.0
        if self.abilities is not None:
            self.abilities.reset_on_checkpoint()
        if self.arsenal is not None:
            self.arsenal.reset_all()

    def fixed_update(self, dt: float, p_input: PlayerInput, room: Room):
        """Execute one deterministic fixed-step simulation tick."""
        if self.is_dead:
            self.respawn_at_checkpoint(room)
            return

        # 1. Update timers
        if self.coyote_timer > 0.0:
            self.coyote_timer = max(0.0, self.coyote_timer - dt)
        if self.jump_buffer_timer > 0.0:
            self.jump_buffer_timer = max(0.0, self.jump_buffer_timer - dt)
        if self.invulnerable_timer > 0.0:
            self.invulnerable_timer = max(0.0, self.invulnerable_timer - dt)
            if self.invulnerable_timer <= 0.0:
                self.knockback_active = False
        if self.slide_cooldown_timer > 0.0:
            self.slide_cooldown_timer = max(0.0, self.slide_cooldown_timer - dt)
        if self.dash_cooldown_timer > 0.0:
            self.dash_cooldown_timer = max(0.0, self.dash_cooldown_timer - dt)
        if self.wall_jump_lock_timer > 0.0:
            self.wall_jump_lock_timer = max(0.0, self.wall_jump_lock_timer - dt)
        if self.serendipity_timer > 0.0:
            self.serendipity_timer = max(0.0, self.serendipity_timer - dt)
            if self.serendipity_timer <= 0.0:
                self.has_serendipity_buff = False
        if self.recoil_timer > 0.0:
            self.recoil_timer = max(0.0, self.recoil_timer - dt)

        # 2. Cover interaction
        cov = room.get_cover_at(self.rect)
        if cov and cov.get("cover_type") == "background":
            if p_input.cover_pressed or (p_input.move_y < -0.5 and not p_input.jump_pressed):
                self.in_cover = not self.in_cover if p_input.cover_pressed else True
                self.cover_type = "background" if self.in_cover else None
                if self.in_cover:
                    self.vx = 0.0
        else:
            self.in_cover = False
            self.cover_type = None

        if self.in_cover and p_input.move_x != 0.0:
            self.in_cover = False
            self.cover_type = None

        if not self.in_cover and cov and cov.get("cover_type") == "low":
            self.cover_type = "low" if (self.is_crouching or self.is_sliding) else None

        # 2B. Fibonacci Dash Initiation & Update (S10)
        can_dash = not self.in_cover and not self.is_dashing and self.dash_cooldown_timer <= 0.0
        if can_dash and getattr(p_input, "dash_pressed", False):
            self.is_dashing = True
            self.dash_timer = self.cfg.fibonacci_dash_duration
            self.dash_cooldown_timer = self.cfg.fibonacci_dash_cooldown
            self.invulnerable_timer = max(self.invulnerable_timer, 0.15)
            self.dash_damaged_targets.clear()
            dash_dir = 1.0 if self.facing == "right" else -1.0
            if p_input.move_x > 0.1:
                dash_dir = 1.0
            elif p_input.move_x < -0.1:
                dash_dir = -1.0
            self.facing = "right" if dash_dir > 0 else "left"
            self.vx = dash_dir * self.cfg.fibonacci_dash_speed
            self.vy = 0.0
            self.is_grappling = False
            self.grapple_anchor = None
            self.grapple_anchor_pos = None
            self.is_wall_sliding = False
            self.is_sliding = False

        if self.is_dashing:
            self.dash_timer = max(0.0, self.dash_timer - dt)
            self.vy = 0.0
            if self.dash_timer <= 0.0:
                self.is_dashing = False

        # 2C. Magnetic Grapple Anchor Interaction (S10)
        just_latched = False
        if not self.is_grappling and not self.in_cover and not self.is_dashing:
            wants_grapple = getattr(p_input, "grapple_pressed", False)
            if wants_grapple and hasattr(room, "get_nearest_grapple_anchor"):
                center_x = self.x + self.width / 2.0
                center_y = self.y + self.height / 2.0
                anchor = room.get_nearest_grapple_anchor(center_x, center_y, self.cfg.grapple_max_range)
                if anchor is not None:
                    self.is_grappling = True
                    self.grapple_anchor = anchor
                    self.grapple_anchor_pos = (anchor.x + anchor.width / 2.0, anchor.y + anchor.height / 2.0)
                    self.is_grounded = False
                    self.is_crouching = False
                    self.is_sliding = False
                    just_latched = True

        if self.is_grappling:
            ax, ay = self.grapple_anchor_pos
            center_x = self.x + self.width / 2.0
            center_y = self.y + self.height / 2.0
            dx = ax - center_x
            dy = ay - center_y
            dist = math.hypot(dx, dy)

            if (p_input.grapple_pressed and not just_latched) or p_input.jump_pressed or dist < 16.0:
                self.is_grappling = False
                self.grapple_anchor = None
                self.grapple_anchor_pos = None
                self.vy = max(-360.0, min(-100.0, self.vy - 60.0))
            else:
                pull_speed = self.cfg.grapple_speed
                if dist > 1e-4:
                    ux = dx / dist
                    uy = dy / dist
                    self.vx = approach(self.vx, ux * pull_speed, 1400.0 * dt)
                    self.vy = approach(self.vy, uy * pull_speed, 1400.0 * dt)

        # 3. Slide Initiation
        can_slide = self.is_grounded and not self.is_sliding and not self.is_dashing and self.slide_cooldown_timer <= 0.0 and not self.in_cover
        wants_slide = p_input.slide_pressed or (p_input.crouch_held and abs(self.vx) > 30.0)
        if can_slide and wants_slide:
            self.is_sliding = True
            self.slide_timer = self.cfg.slide_duration
            self.slide_damaged_targets.clear()
            self.vx = self.cfg.slide_speed if self.facing == "right" else -self.cfg.slide_speed

        # 4. Crouch & Clearance Logic
        if not self.is_sliding and not self.is_dashing:
            if p_input.crouch_held:
                self.is_crouching = True
            elif self.is_crouching:
                # User released crouch: verify legal standing clearance
                if self.can_stand(room):
                    self.is_crouching = False
                else:
                    self.is_crouching = True

        # 5. Slide Update & Duration Decay
        if self.is_sliding:
            self.slide_timer = max(0.0, self.slide_timer - dt)
            if self.slide_timer <= 0.0:
                self.is_sliding = False
                self.slide_cooldown_timer = self.cfg.slide_cooldown
                if not self.can_stand(room) or p_input.crouch_held:
                    self.is_crouching = True
                else:
                    self.is_crouching = False

        # 6. Jump Input & Buffers
        if p_input.jump_pressed and not self.in_cover and not self.is_grappling:
            self.jump_buffer_timer = self.cfg.jump_buffer_time

        can_jump = ((self.is_grounded or self.coyote_timer > 0.0) and not self.is_wall_sliding
                    and not self.knockback_active and not self.in_cover and not self.is_grappling)
        if self.jump_buffer_timer > 0.0 and can_jump:
            if self.can_stand(room):
                self.vy = self.cfg.jump_velocity
                self.is_grounded = False
                self.is_crouching = False
                self.is_sliding = False
                self.coyote_timer = 0.0
                self.jump_buffer_timer = 0.0

        # Jump cut
        if p_input.jump_released and self.vy < 0.0 and not self.is_grappling:
            self.vy *= self.cfg.jump_cut_multiplier

        # 7. Horizontal Kinematics
        if not self.knockback_active and not self.is_sliding and not self.is_dashing and not self.is_grappling and not self.in_cover:
            if self.wall_jump_lock_timer <= 0.0:
                target_vx = p_input.move_x * (self.cfg.walk_speed * 0.5 if self.is_crouching else self.cfg.walk_speed)
                if p_input.move_x != 0.0:
                    self.facing = "right" if p_input.move_x > 0 else "left"
                    accel = self.cfg.ground_acceleration if self.is_grounded else self.cfg.air_acceleration
                    self.vx = approach(self.vx, target_vx, accel * dt)
                else:
                    decel = self.cfg.ground_deceleration if self.is_grounded else self.cfg.air_deceleration
                    self.vx = approach(self.vx, 0.0, decel * dt)

        # 8. Vertical Kinematics (gravity & wall slide)
        if not self.is_grounded and not self.in_cover and not self.is_dashing and not self.is_grappling:
            self.vy = min(self.cfg.max_fall_speed, self.vy + self.cfg.gravity * dt)

            # Wall slide check when descending in mid-air
            col_l = room.check_rect_collision(pygame.Rect(int(self.x - 2), int(self.y + 4), 2, max(4, self.height - 8)))
            col_r = room.check_rect_collision(pygame.Rect(int(self.x + self.width), int(self.y + 4), 2, max(4, self.height - 8)))
            touch_dir = 0
            if col_l["solid"]:
                touch_dir = -1
            elif col_r["solid"]:
                touch_dir = 1

            if touch_dir != 0 and self.vy > 0.0:
                holding_wall = (touch_dir == -1 and p_input.move_x < -0.1) or (touch_dir == 1 and p_input.move_x > 0.1)
                if holding_wall:
                    self.is_wall_sliding = True
                    self.wall_contact_dir = touch_dir
                    self.vy = min(self.vy, self.cfg.wall_slide_speed)
                else:
                    self.is_wall_sliding = False
            else:
                self.is_wall_sliding = False

            # Wall jump execution
            if self.is_wall_sliding and (p_input.jump_pressed or self.jump_buffer_timer > 0.0):
                self.vy = self.cfg.wall_jump_vy
                self.vx = -self.wall_contact_dir * self.cfg.wall_jump_vx
                self.facing = "right" if self.vx > 0 else "left"
                self.is_wall_sliding = False
                self.wall_jump_lock_timer = 0.15
                self.jump_buffer_timer = 0.0
                self.coyote_timer = 0.0
        else:
            self.is_wall_sliding = False

        # 9. Move & Resolve Horizontally
        self.x += self.vx * dt
        max_x = float(room.width_px - self.width)
        if self.x < 0.0:
            self.x = 0.0
            self.vx = 0.0
        elif self.x > max_x:
            self.x = max_x
            self.vx = 0.0

        x_check = int(self.x) - (1 if self.vx < 0 else 0)
        w_check = self.width + (1 if self.vx > 0 else 0) + (1 if self.vx < 0 else 0)
        col_h = room.check_rect_collision(pygame.Rect(x_check, int(self.y), w_check, self.height))
        if col_h["solid"]:
            if self.is_sliding:
                # Solid wall stops slide immediately
                self.is_sliding = False
                self.slide_timer = 0.0
                self.slide_cooldown_timer = self.cfg.slide_cooldown
                if not self.can_stand(room) or p_input.crouch_held:
                    self.is_crouching = True
                else:
                    self.is_crouching = False

            if self.is_dashing:
                # Solid wall stops dash immediately (swept anti-tunneling)
                self.is_dashing = False
                self.dash_timer = 0.0

            if self.vx > 0:
                solid_cols = [c for c, r, code in col_h["tiles"] if code == COLLISION_SOLID]
                if solid_cols:
                    self.x = float(min(solid_cols) * room.tile_size - self.width)
                self.vx = 0.0
            elif self.vx < 0:
                solid_cols = [c for c, r, code in col_h["tiles"] if code == COLLISION_SOLID]
                if solid_cols:
                    self.x = float((max(solid_cols) + 1) * room.tile_size)
                self.vx = 0.0

        # 10. Move & Resolve Vertically
        prev_bottom = self.y + 32  # Feet anchor
        self.y += self.vy * dt

        if self.y < 0.0:
            self.y = 0.0
            self.vy = 0.0

        y_check = int(self.y) - (1 if self.vy < 0 else 0)
        h_check = self.height + (1 if self.vy > 0 else 0) + (1 if self.vy < 0 else 0)
        col_v = room.check_rect_collision(pygame.Rect(int(self.x), y_check, self.width, h_check))

        # A. Solid tile resolution
        if col_v["solid"]:
            if self.vy > 0:
                solid_rows = [r for c, r, code in col_v["tiles"] if code == COLLISION_SOLID]
                if solid_rows:
                    self.y = float(min(solid_rows) * room.tile_size - 32)
                self.vy = 0.0
                self.is_grounded = True
                self.coyote_timer = 0.0
                if self.jump_buffer_timer > 0.0 and not self.knockback_active and not self.in_cover:
                    if self.can_stand(room):
                        self.vy = self.cfg.jump_velocity
                        self.is_grounded = False
                        self.is_crouching = False
                        self.is_sliding = False
                        self.jump_buffer_timer = 0.0
            elif self.vy < 0:
                solid_rows = [r for c, r, code in col_v["tiles"] if code == COLLISION_SOLID]
                if solid_rows:
                    self.y = float((max(solid_rows) + 1) * room.tile_size)
                self.vy = 0.0

        # B. One-way platform resolution
        elif col_v["one_way"] and self.vy >= 0 and not p_input.crouch_held:
            for c, r, code in col_v["tiles"]:
                if code == COLLISION_ONE_WAY:
                    plat_top = float(r * room.tile_size)
                    if prev_bottom <= plat_top + 6.0 and (self.y + 32) >= plat_top:
                        self.y = plat_top - 32
                        self.vy = 0.0
                        self.is_grounded = True
                        self.coyote_timer = 0.0
                        if self.jump_buffer_timer > 0.0 and not self.knockback_active and not self.in_cover:
                            if self.can_stand(room):
                                self.vy = self.cfg.jump_velocity
                                self.is_grounded = False
                                self.is_crouching = False
                                self.is_sliding = False
                                self.jump_buffer_timer = 0.0
                        break

        # C. Ground retention / ledge departure
        if self.is_grounded:
            below_rect = pygame.Rect(int(round(self.x + 2)), int(round(self.y + 32)), max(1, self.width - 4), 2)
            col_below = room.check_rect_collision(below_rect)
            on_solid = col_below["solid"]
            on_oneway = False
            if col_below["one_way"]:
                for c, r, code in col_below["tiles"]:
                    if code == COLLISION_ONE_WAY and abs((self.y + 32) - r * room.tile_size) <= 2.0:
                        on_oneway = True
                        break
            if not on_solid and not on_oneway:
                self.is_grounded = False
                self.coyote_timer = self.cfg.coyote_time

        # 11. Hazards & Falling Out of Bounds
        h_pad = 2 if (self.is_grounded or self.vy >= 0) else 0
        hazard_check_rect = pygame.Rect(
            int(self.x),
            int(self.y),
            self.width,
            32 + h_pad,
        )
        col_hazard = room.check_rect_collision(hazard_check_rect)
        if col_hazard["hazard"]:
            self.take_damage(self.cfg.hazard_damage)

        if self.y > float(room.height_px):
            self.health = 0
            self.is_dead = True
            self.respawn_at_checkpoint(room)

        # 12. Checkpoints
        chk = room.check_checkpoint_trigger(self.rect)
        if chk and chk.id != self.active_checkpoint_id:
            self.set_checkpoint(chk.id, chk.x, chk.y)

    def update(
        self,
        dt: float,
        p_input: PlayerInput,
        room: Room,
        projectile_manager: Optional[Any] = None,
        is_paused: bool = False,
    ):
        """Update simulation with fixed-timestep accumulator, clamping backlog after stalls."""
        if is_paused:
            self._pending_grapple_press = False
        else:
            # Preserve a key edge until a physics step is available, then
            # consume it once even if this render frame runs multiple steps.
            self._pending_grapple_press |= p_input.grapple_pressed
            clamped_dt = min(dt, self.cfg.max_accumulator)
            self.accumulator += clamped_dt
            if self.accumulator > self.cfg.max_accumulator:
                self.accumulator = self.cfg.max_accumulator

            while self.accumulator >= self.cfg.fixed_dt:
                step_input = replace(p_input, grapple_pressed=self._pending_grapple_press)
                self._pending_grapple_press = False
                self.fixed_update(self.cfg.fixed_dt, step_input, room)
                self.accumulator -= self.cfg.fixed_dt

        # Handle weapon cycling
        if not is_paused and getattr(p_input, "cycle_weapon_pressed", False) and self.arsenal is not None:
            self.arsenal.cycle_weapon()
            self.weapon = self.arsenal.active_weapon

        # Handle ability cycling and activation
        if self.abilities is not None:
            if not is_paused and getattr(p_input, "cycle_ability_pressed", False):
                self.abilities.cycle_ability()
            if not is_paused and not getattr(self, "is_flashback", False) and getattr(p_input, "ability_pressed", False):
                self.abilities.trigger_selected_ability(self, getattr(self, "combat_context", None))
            self.abilities.update(dt, is_paused=is_paused)

        # Advance weapon firing and charge (suppressed inside historical flashback)
        active_w = self.weapon if self.weapon is not None else (self.arsenal.active_weapon if self.arsenal is not None else None)
        # Resolve pointing after movement, without changing movement/dash facing.
        aim_x, aim_y = p_input.aim_x, p_input.aim_y
        target = p_input.aim_target_x is not None and p_input.aim_target_y is not None
        if target:
            aim_x = p_input.aim_target_x - (self.x + self.width / 2.0)
            aim_y = p_input.aim_target_y - (self.y + self.height / 2.0)
        explicit_aim = aim_x is not None and aim_y is not None and math.hypot(aim_x, aim_y) > 1e-4
        self.aim_facing_active = explicit_aim
        self.weapon_facing = ('right' if aim_x > 0 else 'left') if explicit_aim and abs(aim_x) > 1e-4 else self.facing
        if self.animator is not None:
            self.animator.set_facing(self.weapon_facing)
        if target and explicit_aim:
            muzzle_x, muzzle_y = self.get_muzzle_world_pos()
            p_input = replace(p_input, aim_x=p_input.aim_target_x - muzzle_x, aim_y=p_input.aim_target_y - muzzle_y)
        set_assisted = getattr(active_w, 'set_assisted', None)
        if set_assisted is not None:
            set_assisted(p_input.combat_assisted)
        if not getattr(self, "is_flashback", False) and active_w is not None and projectile_manager is not None:
            active_w.update(dt, p_input, self, room, projectile_manager, is_paused=is_paused)

        if not is_paused and self.animator is not None:
            self.animator.set_state(self.animation_state)
            self.animator.set_facing(self.weapon_facing)
            self.animator.update(dt)
