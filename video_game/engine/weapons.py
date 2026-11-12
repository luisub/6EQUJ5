"""
MODULE: video_game/engine/weapons.py
PURPOSE: Starter waveguide maser, continuous swept-ray collision detection,
         projectile pooling, 8-directional aiming, and combat target resolution.
CALLED BY: video_game.engine.player, video_game.engine.scenes.field, video_game.tests.test_combat.
HOW TO MODIFY: Tune weapon cadence, damage, and projectile speeds in video_game/data/balance.json;
               extend target behaviors or add new weapon archetypes by subclassing CombatTarget or StarterMaser.
"""

from dataclasses import dataclass, field
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union
import pygame

from video_game.engine import config
from video_game.engine.world import COLLISION_SOLID, Room

BALANCE_PATH = Path(__file__).resolve().parent.parent / "data" / "balance.json"


@dataclass
class WeaponConfig:
    """Tunable weapon cadence, speed, damage, and collision attributes."""
    id: str = "starter_maser"
    name: str = "1420 MHz Waveguide Maser"
    fire_cadence: float = 0.20
    projectile_speed: float = 420.0
    damage: int = 25
    charge_damage: int = 75
    lifetime: float = 1.2
    normal_pierce: int = 1
    charge_pierce: int = 3
    charge_time: float = 0.60
    recoil_duration: float = 0.12
    beam_length: float = 12.0
    beam_thickness: float = 3.0
    charge_beam_length: float = 20.0
    charge_beam_thickness: float = 5.0
    knockback_force: float = 80.0
    unlock_events: List[str] = field(default_factory=list)
    # Starter maser accessibility profile; classic values above stay unchanged.
    assist_fire_cadence: float = 0.16
    assist_center_damage: int = 50
    assist_flank_damage: int = 20
    assist_spread_degrees: float = 10.0
    # Scattergun
    pellet_count: int = 5
    spread_angles: List[float] = field(default_factory=lambda: [-16.0, -8.0, 0.0, 8.0, 16.0])
    reveal_duration: float = 4.0
    # EMP Bola
    stun_duration: float = 2.0
    # Fibonacci Coilgun
    base_damage: int = 20
    fibonacci_stages: List[int] = field(default_factory=lambda: [1, 2, 3, 5, 8])
    stage_hold_times: List[float] = field(default_factory=lambda: [0.0, 0.25, 0.55, 0.90, 1.30])
    stage_pierce: List[int] = field(default_factory=lambda: [1, 1, 2, 3, 5])

    @classmethod
    def load_from_dict(cls, data: Dict[str, Any]) -> "WeaponConfig":
        """Instantiate config from a dictionary payload."""
        assist = data.get("assist", {})
        return cls(
            id=str(data.get("id", "starter_maser")),
            name=str(data.get("name", "1420 MHz Waveguide Maser")),
            fire_cadence=float(data.get("fire_cadence", 0.20)),
            projectile_speed=float(data.get("projectile_speed", 420.0)),
            damage=int(data.get("damage", 25)),
            charge_damage=int(data.get("charge_damage", 75)),
            lifetime=float(data.get("lifetime", 1.2)),
            normal_pierce=int(data.get("normal_pierce", 1)),
            charge_pierce=int(data.get("charge_pierce", 3)),
            charge_time=float(data.get("charge_time", 0.60)),
            recoil_duration=float(data.get("recoil_duration", 0.12)),
            beam_length=float(data.get("beam_length", 12.0)),
            beam_thickness=float(data.get("beam_thickness", 3.0)),
            charge_beam_length=float(data.get("charge_beam_length", 20.0)),
            charge_beam_thickness=float(data.get("charge_beam_thickness", 5.0)),
            knockback_force=float(data.get("knockback_force", 80.0)),
            unlock_events=list(data.get("unlock_events", [])),
            assist_fire_cadence=float(assist.get("fire_cadence", 0.16)),
            assist_center_damage=int(assist.get("center_damage", 50)),
            assist_flank_damage=int(assist.get("flank_damage", 20)),
            assist_spread_degrees=float(assist.get("spread_degrees", 10.0)),
            pellet_count=int(data.get("pellet_count", 5)),
            spread_angles=list(data.get("spread_angles", [-16.0, -8.0, 0.0, 8.0, 16.0])),
            reveal_duration=float(data.get("reveal_duration", 4.0)),
            stun_duration=float(data.get("stun_duration", 2.0)),
            base_damage=int(data.get("base_damage", 20)),
            fibonacci_stages=list(data.get("fibonacci_stages", [1, 2, 3, 5, 8])),
            stage_hold_times=list(data.get("stage_hold_times", [0.0, 0.25, 0.55, 0.90, 1.30])),
            stage_pierce=list(data.get("stage_pierce", [1, 1, 2, 3, 5])),
        )

    @classmethod
    def load_from_file(cls, path: Optional[Union[str, Path]] = None, weapon_id: str = "starter_maser") -> "WeaponConfig":
        """Load weapon configuration from balance.json."""
        p = Path(path) if path else BALANCE_PATH
        if not p.exists():
            return cls()
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        w_dict = data.get("weapons", {}).get(weapon_id, {})
        return cls.load_from_dict(w_dict)


INV_SQRT2 = 0.7071067811865475


def resolve_aim_vector(
    move_x: float,
    move_y: float,
    facing: str,
    is_crouching: bool = False,
    is_grounded: bool = True,
    aim_x: Optional[float] = None,
    aim_y: Optional[float] = None,
) -> Tuple[float, float]:
    """
    Resolve discrete 8-directional aim unit vector.
    
    Directions:
      (1, 0), (-1, 0): Right, Left
      (0, -1), (0, 1): Up, Down
      (±INV_SQRT2, ±INV_SQRT2): Diagonals
    """
    if aim_x is not None and aim_y is not None:
        mag = math.hypot(aim_x, aim_y)
        if mag > 1e-4:
            return aim_x / mag, aim_y / mag

    ax = 0.0
    if move_x > 0.3:
        ax = 1.0
    elif move_x < -0.3:
        ax = -1.0

    ay = 0.0
    if move_y < -0.3:
        ay = -1.0  # Upwards
    elif move_y > 0.3:
        ay = 1.0   # Downwards

    # 1. Aiming Up
    if ay == -1.0:
        if ax == 1.0:
            return INV_SQRT2, -INV_SQRT2
        elif ax == -1.0:
            return -INV_SQRT2, -INV_SQRT2
        return 0.0, -1.0

    # 2. Aiming Down
    if ay == 1.0:
        if ax == 1.0:
            return INV_SQRT2, INV_SQRT2
        elif ax == -1.0:
            return -INV_SQRT2, INV_SQRT2
        # Pure down
        if not is_grounded:
            return 0.0, 1.0
        # When grounded, aiming down without X fires horizontally forward from crouch
        return (1.0, 0.0) if facing == "right" else (-1.0, 0.0)

    # 3. Horizontal / Neutral
    if ax == 1.0:
        return 1.0, 0.0
    elif ax == -1.0:
        return -1.0, 0.0

    return (1.0, 0.0) if facing == "right" else (-1.0, 0.0)


def get_muzzle_world_pos(player: Any) -> Tuple[float, float]:
    """Calculate camera-independent world coordinates for weapon muzzle."""
    foot_wx = float(player.x + (player.width / 2.0))
    foot_wy = float(player.y + 32.0)
    if getattr(player, "animator", None) is not None:
        pos = player.animator.get_attachment_world_pos("muzzle", foot_wx, foot_wy)
        if pos is not None:
            return float(pos[0]), float(pos[1])

    # Fallback geometry when animator is not attached
    facing = (getattr(player, "weapon_facing", player.facing)
              if getattr(player, "aim_facing_active", False) else player.facing)
    offset_x = (player.width + 4.0) if facing == "right" else -4.0
    offset_y = 14.0 if getattr(player, "is_crouching", False) else 18.0
    return float(player.x + offset_x), float(player.y + offset_y)


@dataclass
class HitResult:
    """Outcome of projectile impact on a damageable target."""
    hit: bool
    target_id: str
    damage_dealt: int
    target_killed: bool
    hit_x: float = 0.0
    hit_y: float = 0.0
    knockback_vx: float = 0.0
    knockback_vy: float = 0.0


class CombatTarget:
    """
    Damageable entity interface with bounding box, health, and invulnerability.
    Enforces idempotent reward claims and eliminates duplicate hits.
    """

    def __init__(
        self,
        target_id: str,
        rect: pygame.Rect,
        health: int = 50,
        max_health: int = 50,
        invulnerability_duration: float = 0.0,
    ):
        self.target_id: str = target_id
        self.rect: pygame.Rect = pygame.Rect(rect)
        self.health: int = health
        self.max_health: int = max_health
        self.is_dead: bool = (health <= 0)
        self.invulnerable_timer: float = 0.0
        self.invulnerability_duration: float = invulnerability_duration
        self.reward_claimed: bool = False
        self.hit_count: int = 0
        self.status_effects: Dict[str, float] = {}

    def apply_status(self, name: str, duration: float):
        """Apply or extend a named status condition (e.g. 'stun', 'revealed')."""
        curr = self.status_effects.get(name, 0.0)
        self.status_effects[name] = max(curr, duration)

    def has_status(self, name: str) -> bool:
        """Check if target has an active status condition."""
        return self.status_effects.get(name, 0.0) > 0.0

    def get_status(self, name: str) -> float:
        """Get remaining duration of status condition."""
        return max(0.0, self.status_effects.get(name, 0.0))

    def clear_statuses(self):
        """Clear all active status conditions."""
        self.status_effects.clear()

    def update(self, dt: float):
        """Update target timers and status conditions."""
        if self.invulnerable_timer > 0.0:
            self.invulnerable_timer = max(0.0, self.invulnerable_timer - dt)
        if self.status_effects:
            expired = []
            for s_name, s_dur in self.status_effects.items():
                new_dur = s_dur - dt
                if new_dur <= 0.0:
                    expired.append(s_name)
                else:
                    self.status_effects[s_name] = new_dur
            for s_name in expired:
                del self.status_effects[s_name]

    def take_damage(
        self,
        amount: int,
        hit_id: str = "",
        knockback: Tuple[float, float] = (0.0, 0.0),
        hit_pos: Tuple[float, float] = (0.0, 0.0),
    ) -> HitResult:
        """Apply damage and knockback. Guaranteed idempotent on death."""
        if self.is_dead:
            return HitResult(
                hit=False,
                target_id=self.target_id,
                damage_dealt=0,
                target_killed=False,
                hit_x=hit_pos[0],
                hit_y=hit_pos[1],
            )

        if self.invulnerable_timer > 0.0:
            return HitResult(
                hit=True,
                target_id=self.target_id,
                damage_dealt=0,
                target_killed=False,
                hit_x=hit_pos[0],
                hit_y=hit_pos[1],
            )

        effective_amount = amount
        if self.has_status("revealed"):
            # Target is sensor-illuminated: +25% vulnerability damage
            effective_amount = int(amount * 1.25)
        if self.has_status("prediction_shattered"):
            # Predictive targeting shattered by Serendipity: 3x Anomaly Critical Damage
            effective_amount = int(amount * 3.0)

        self.hit_count += 1
        actual_damage = min(self.health, effective_amount)
        self.health -= actual_damage
        killed = False

        if self.health <= 0:
            self.health = 0
            self.is_dead = True
            killed = True
            self.reward_claimed = True
        elif self.invulnerability_duration > 0.0:
            self.invulnerable_timer = self.invulnerability_duration

        return HitResult(
            hit=True,
            target_id=self.target_id,
            damage_dealt=actual_damage,
            target_killed=killed,
            hit_x=hit_pos[0],
            hit_y=hit_pos[1],
            knockback_vx=knockback[0],
            knockback_vy=knockback[1],
        )


@dataclass
class Projectile:
    """Active or pooled waveguide maser projectile."""
    id: str
    x: float
    y: float
    vx: float
    vy: float
    dir_x: float
    dir_y: float
    damage: int
    is_charged: bool
    pierce_remaining: int
    lifetime: float
    max_lifetime: float
    beam_length: float
    beam_thickness: float
    active: bool = True
    hit_target_ids: Set[str] = field(default_factory=set)
    weapon_type: str = "starter_maser"
    status_to_apply: Optional[Tuple[str, float]] = None
    color: Optional[Tuple[int, int, int]] = None
    # A volley shares only its target-hit set, not its wall/target trajectory.
    volley_hit_target_ids: Optional[Set[str]] = None
    is_primary_discharge: bool = True


def check_swept_ray_tile_collision(
    room: Room,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
) -> Tuple[bool, float, float, int, int]:
    """
    Continuous swept collision detection against room solid tiles.
    Uses Amanatides-Woo 2D grid ray-traversal to guarantee zero tunneling through thin walls.
    
    Returns:
      (hit_found, hit_x, hit_y, tile_col, tile_row)
    """
    ts = room.tile_size
    col = int(math.floor(x0 / ts))
    row = int(math.floor(y0 / ts))

    # Check origin
    if room.get_tile(col, row) == COLLISION_SOLID:
        return True, x0, y0, col, row

    dx = x1 - x0
    dy = y1 - y0
    if dx == 0.0 and dy == 0.0:
        return False, x1, y1, -1, -1

    end_col = int(math.floor(x1 / ts))
    end_row = int(math.floor(y1 / ts))

    step_x = 1 if dx > 0 else (-1 if dx < 0 else 0)
    step_y = 1 if dy > 0 else (-1 if dy < 0 else 0)

    if dx != 0:
        next_x = (col + 1) * ts if dx > 0 else col * ts
        t_max_x = (next_x - x0) / dx
        t_delta_x = abs(ts / dx)
    else:
        t_max_x = float("inf")
        t_delta_x = float("inf")

    if dy != 0:
        next_y = (row + 1) * ts if dy > 0 else row * ts
        t_max_y = (next_y - y0) / dy
        t_delta_y = abs(ts / dy)
    else:
        t_max_y = float("inf")
        t_delta_y = float("inf")

    curr_c = col
    curr_r = row

    while True:
        if t_max_x < t_max_y:
            t_curr = t_max_x
            t_max_x += t_delta_x
            curr_c += step_x
        else:
            t_curr = t_max_y
            t_max_y += t_delta_y
            curr_r += step_y

        if t_curr > 1.0:
            break

        if room.get_tile(curr_c, curr_r) == COLLISION_SOLID:
            # Clip ray to tile boundary to obtain exact contact point
            tile_rect = pygame.Rect(curr_c * ts, curr_r * ts, ts, ts)
            clip = tile_rect.clipline((x0, y0), (x1, y1))
            if clip:
                hx, hy = float(clip[0][0]), float(clip[0][1])
            else:
                hx = x0 + dx * min(1.0, max(0.0, t_curr))
                hy = y0 + dy * min(1.0, max(0.0, t_curr))
            return True, hx, hy, curr_c, curr_r

        if curr_c == end_col and curr_r == end_row:
            break

    return False, x1, y1, -1, -1


class ProjectileManager:
    """
    Manages active projectiles, swept ray collision resolution,
    visual particle sparks, and memory lifecycle without leaks.
    """

    def __init__(self):
        self.projectiles: List[Projectile] = []
        self.sparks: List[Dict[str, Any]] = []
        self._next_id: int = 1

    def clear(self):
        """Immediately purge all active projectiles and particles."""
        self.projectiles.clear()
        self.sparks.clear()

    def spawn(
        self,
        x: float,
        y: float,
        dir_x: float,
        dir_y: float,
        speed: float,
        damage: int,
        is_charged: bool = False,
        pierce_count: int = 1,
        lifetime: float = 1.2,
        beam_length: float = 12.0,
        beam_thickness: float = 3.0,
        weapon_type: str = "starter_maser",
        status_to_apply: Optional[Tuple[str, float]] = None,
        color: Optional[Tuple[int, int, int]] = None,
        volley_hit_target_ids: Optional[Set[str]] = None,
        is_primary_discharge: bool = True,
    ) -> Projectile:
        """Spawn a new projectile along the normalized direction vector."""
        prefix = f"{weapon_type}_{'charged' if is_charged else 'std'}"
        p_id = f"{prefix}_{self._next_id:06d}"
        self._next_id += 1

        proj = Projectile(
            id=p_id,
            x=x,
            y=y,
            vx=dir_x * speed,
            vy=dir_y * speed,
            dir_x=dir_x,
            dir_y=dir_y,
            damage=damage,
            is_charged=is_charged,
            pierce_remaining=pierce_count,
            lifetime=lifetime,
            max_lifetime=lifetime,
            beam_length=beam_length,
            beam_thickness=beam_thickness,
            active=True,
            hit_target_ids=set(),
            weapon_type=weapon_type,
            status_to_apply=status_to_apply,
            color=color,
            volley_hit_target_ids=volley_hit_target_ids,
            is_primary_discharge=is_primary_discharge,
        )
        self.projectiles.append(proj)
        return proj

    def add_sparks(self, x: float, y: float, count: int = 4, is_charged: bool = False):
        """Generate transient impact sparks."""
        color = (255, 200, 80) if is_charged else (120, 220, 255)
        for i in range(count):
            angle = (float(i) / max(1, count)) * 2.0 * math.pi
            sp_speed = 30.0 + (i * 12.0)
            self.sparks.append({
                "x": x,
                "y": y,
                "vx": math.cos(angle) * sp_speed,
                "vy": math.sin(angle) * sp_speed,
                "life": 0.12,
                "max_life": 0.12,
                "color": color,
            })

    def update(
        self,
        dt: float,
        room: Room,
        targets: Sequence[CombatTarget] = (),
        is_paused: bool = False,
    ) -> List[HitResult]:
        """
        Step simulation using swept line collision detection.
        Respects game pause: zero movement, zero collision, zero lifetime decay when paused.
        """
        if is_paused or dt <= 0.0:
            return []

        hits_recorded: List[HitResult] = []

        # 1. Update impact sparks
        surviving_sparks = []
        for sp in self.sparks:
            sp["x"] += sp["vx"] * dt
            sp["y"] += sp["vy"] * dt
            sp["life"] -= dt
            if sp["life"] > 0.0:
                surviving_sparks.append(sp)
        self.sparks = surviving_sparks

        # 2. Update projectiles
        surviving_projectiles = []
        for proj in self.projectiles:
            if not proj.active:
                continue

            x0, y0 = proj.x, proj.y
            x1 = x0 + proj.vx * dt
            y1 = y0 + proj.vy * dt

            # Swept raycast against solid tiles
            wall_hit, wall_x, wall_y, _, _ = check_swept_ray_tile_collision(room, x0, y0, x1, y1)
            wall_dist = math.hypot(wall_x - x0, wall_y - y0) if wall_hit else float("inf")

            # Swept check against targets along ray
            target_hits = []
            for target in targets:
                if target.target_id in proj.hit_target_ids:
                    continue
                # A target killed earlier in this volley still blocks its
                # remaining rays during this update; unrelated dead targets do not.
                if (target.is_dead and
                        (proj.volley_hit_target_ids is None or
                         target.target_id not in proj.volley_hit_target_ids)):
                    continue
                clip = target.rect.clipline((x0, y0), (x1, y1))
                if clip:
                    entry_x, entry_y = float(clip[0][0]), float(clip[0][1])
                    t_dist = math.hypot(entry_x - x0, entry_y - y0)
                    if t_dist <= wall_dist:
                        target_hits.append((t_dist, entry_x, entry_y, target))

            # Sort target hits by distance along trajectory
            target_hits.sort(key=lambda item: item[0])

            # Process target collisions in exact spatial order
            projectile_absorbed = False
            for t_dist, entry_x, entry_y, target in target_hits:
                proj.hit_target_ids.add(target.target_id)
                # A flank still collides with a target struck by its volley;
                # it must not pass through that target or deal damage twice.
                if (proj.volley_hit_target_ids is not None and
                        target.target_id in proj.volley_hit_target_ids):
                    proj.pierce_remaining -= 1
                    if proj.pierce_remaining <= 0:
                        proj.x, proj.y = entry_x, entry_y
                        proj.active = False
                        projectile_absorbed = True
                        break
                    continue
                if proj.volley_hit_target_ids is not None:
                    proj.volley_hit_target_ids.add(target.target_id)
                kb_x = proj.dir_x * 40.0
                kb_y = proj.dir_y * 40.0
                if proj.status_to_apply is not None and hasattr(target, "apply_status"):
                    target.apply_status(proj.status_to_apply[0], proj.status_to_apply[1])
                res = target.take_damage(
                    proj.damage,
                    hit_id=proj.id,
                    knockback=(kb_x, kb_y),
                    hit_pos=(entry_x, entry_y),
                )
                hits_recorded.append(res)
                self.add_sparks(entry_x, entry_y, count=5 if proj.is_charged else 3, is_charged=proj.is_charged)

                proj.pierce_remaining -= 1
                if proj.pierce_remaining <= 0:
                    proj.x = entry_x
                    proj.y = entry_y
                    proj.active = False
                    projectile_absorbed = True
                    break

            if projectile_absorbed:
                continue

            # If not absorbed by targets, handle solid wall collision
            if wall_hit:
                proj.x = wall_x
                proj.y = wall_y
                proj.active = False
                self.add_sparks(wall_x, wall_y, count=6 if proj.is_charged else 4, is_charged=proj.is_charged)
                continue

            # No terminal collision: advance position and decay lifetime
            proj.x = x1
            proj.y = y1
            proj.lifetime -= dt
            if proj.lifetime <= 0.0:
                proj.active = False
                continue

            # Out of bounds check
            if proj.x < -32.0 or proj.x > room.width_px + 32.0 or proj.y < -32.0 or proj.y > room.height_px + 32.0:
                proj.active = False
                continue

            surviving_projectiles.append(proj)

        self.projectiles = surviving_projectiles
        return hits_recorded

    def render(self, surface: pygame.Surface, camera: Any, *, narrow_projectile_ids=()):
        """Render beams; an opt-in presentation may narrow selected visual strokes."""
        # 1. Render sparks
        for sp in self.sparks:
            sx, sy = camera.world_to_screen(sp["x"], sp["y"])
            if 0 <= sx < surface.get_width() and 0 <= sy < surface.get_height():
                alpha_factor = max(0.0, sp["life"] / sp["max_life"])
                c = sp["color"]
                faded = (int(c[0] * alpha_factor), int(c[1] * alpha_factor), int(c[2] * alpha_factor))
                surface.set_at((sx, sy), faded)

        # 2. Render projectiles
        for proj in self.projectiles:
            head_x, head_y = camera.world_to_screen(proj.x, proj.y)
            tail_wx = proj.x - (proj.dir_x * proj.beam_length)
            tail_wy = proj.y - (proj.dir_y * proj.beam_length)
            tail_x, tail_y = camera.world_to_screen(tail_wx, tail_wy)

            if proj.color is not None:
                glow_col = proj.color
                core_col = (255, 255, 240)
            elif proj.is_charged:
                glow_col = (255, 180, 50)
                core_col = (255, 255, 240)
            else:
                glow_col = (100, 220, 255)
                core_col = (255, 255, 240)

            # Only explicitly selected presentation IDs use narrower strokes;
            # their projectile data and world-space head/tail are unchanged.
            if proj.id in narrow_projectile_ids:
                glow_col = (145, 220, 195)
                core_col = (240, 255, 239)
                glow_thickness = 3
                core_thickness = 1
            else:
                glow_thickness = max(2, int(proj.beam_thickness + 2))
                core_thickness = max(1, int(proj.beam_thickness))
            pygame.draw.line(surface, glow_col, (tail_x, tail_y), (head_x, head_y), glow_thickness)
            # Inner core
            pygame.draw.line(surface, core_col, (tail_x, tail_y), (head_x, head_y), core_thickness)


class AnalogWeapon:
    """Base interface for all analog arsenal firearms."""

    def __init__(self, config_obj: Optional[WeaponConfig] = None):
        self.cfg: WeaponConfig = config_obj or WeaponConfig()
        self.id: str = self.cfg.id
        self.name: str = self.cfg.name
        self.cooldown_timer: float = 0.0
        self.charge_timer: float = 0.0
        self.is_charging: bool = False
        self.is_unlocked: bool = (len(self.cfg.unlock_events) == 0)

    def check_unlocked(self, campaign: Optional[Any] = None) -> bool:
        """Verify if weapon has been unlocked in campaign state."""
        if len(self.cfg.unlock_events) == 0:
            self.is_unlocked = True
            return True
        if campaign is None:
            return self.is_unlocked

        st = getattr(campaign, "state", None)
        recorded = list(getattr(st, "events_recorded", [])) + list(getattr(st, "completed_event_types", [])) + list(getattr(st, "applied_event_ids", []))
        records = getattr(st, "validation_records", [])
        rec_ids = {r.get("id") if isinstance(r, dict) else getattr(r, "id", "") for r in records}
        inventory = getattr(st, "inventory", {})
        room_flags = getattr(st, "room_flags", {})

        self.is_unlocked = False
        for ev in self.cfg.unlock_events:
            if ev in recorded or ev in rec_ids or inventory.get(ev, 0) > 0 or room_flags.get(ev, False):
                self.is_unlocked = True
                return True
        return self.is_unlocked

    def reset(self):
        """Reset weapon state on player death or respawn."""
        self.cooldown_timer = 0.0
        self.charge_timer = 0.0
        self.is_charging = False

    def update(
        self,
        dt: float,
        p_input: Any,
        player: Any,
        room: Room,
        manager: ProjectileManager,
        is_paused: bool = False,
    ) -> Optional[Projectile]:
        """Update weapon firing and cadence. Subclasses override."""
        raise NotImplementedError


class StarterMaser(AnalogWeapon):
    """
    Starter Waveguide Maser firearm controller.
    Enforces cadence timing, charge accumulation, 8-way aim vectoring, and pause safety.
    """

    def __init__(self, config_obj: Optional[WeaponConfig] = None):
        cfg = config_obj or WeaponConfig.load_from_file(weapon_id="starter_maser")
        super().__init__(cfg)
        self.assisted = False
        self._charge_cancelled = False

    def cancel_charge(self) -> None:
        """Discard an interrupted keyboard/controller charge without firing."""
        self.charge_timer = 0.0
        self.is_charging = False
        # Ignore a still-held trigger until it is released or pressed afresh.
        self._charge_cancelled = True

    def reset(self) -> None:
        """Clear transient fire state while retaining the selected profile."""
        super().reset()
        self._charge_cancelled = True

    def set_assisted(self, enabled: bool) -> None:
        """Select the per-instance profile without mutating classic config."""
        enabled = bool(enabled)
        if enabled != self.assisted:
            self.cancel_charge()
            self.assisted = enabled

    def _fire_tap(self, manager: ProjectileManager, player: Any,
                  muzzle_x: float, muzzle_y: float,
                  dir_x: float, dir_y: float) -> Projectile:
        """Spawn one classic ray or a three-ray assisted volley, center first."""
        volley_hits: Optional[Set[str]] = set() if self.assisted else None
        center = manager.spawn(
            x=muzzle_x, y=muzzle_y, dir_x=dir_x, dir_y=dir_y,
            speed=self.cfg.projectile_speed,
            damage=self.cfg.assist_center_damage if self.assisted else self.cfg.damage,
            is_charged=False, pierce_count=self.cfg.normal_pierce,
            lifetime=self.cfg.lifetime, beam_length=self.cfg.beam_length,
            beam_thickness=self.cfg.beam_thickness, weapon_type="starter_maser",
            volley_hit_target_ids=volley_hits,
        )
        if self.assisted:
            base_angle = math.atan2(dir_y, dir_x)
            for degrees in (-self.cfg.assist_spread_degrees, self.cfg.assist_spread_degrees):
                angle = base_angle + math.radians(degrees)
                manager.spawn(
                    x=muzzle_x, y=muzzle_y, dir_x=math.cos(angle), dir_y=math.sin(angle),
                    speed=self.cfg.projectile_speed, damage=self.cfg.assist_flank_damage,
                    is_charged=False, pierce_count=self.cfg.normal_pierce,
                    lifetime=self.cfg.lifetime, beam_length=self.cfg.beam_length,
                    beam_thickness=self.cfg.beam_thickness, weapon_type="starter_maser",
                    volley_hit_target_ids=volley_hits, is_primary_discharge=False,
                )
        self.cooldown_timer = self.cfg.assist_fire_cadence if self.assisted else self.cfg.fire_cadence
        if hasattr(player, "trigger_fire_recoil"):
            player.trigger_fire_recoil(self.cfg.recoil_duration)
        return center

    @property
    def is_fully_charged(self) -> bool:
        """True when held fire duration meets or exceeds charge threshold."""
        return self.charge_timer >= self.cfg.charge_time

    @property
    def charge_ratio(self) -> float:
        """Normalized charge progression [0.0, 1.0]."""
        if self.cfg.charge_time <= 0.0:
            return 1.0
        return min(1.0, max(0.0, self.charge_timer / self.cfg.charge_time))

    def update(
        self,
        dt: float,
        p_input: Any,
        player: Any,
        room: Room,
        manager: ProjectileManager,
        is_paused: bool = False,
    ) -> Optional[Projectile]:
        """
        Update weapon state, cadence cooldown, charge build-up, and projectile spawning.
        Pause safety: zero state mutations when is_paused is True.
        """
        if is_paused or dt <= 0.0:
            return None

        # Cadence cooldown decay
        if self.cooldown_timer > 0.0:
            self.cooldown_timer = max(0.0, self.cooldown_timer - dt)

        # Cover check: player cannot fire while concealed in background doorway alcoves
        can_fire = getattr(player, "can_fire", lambda r: True)(room)
        if not can_fire:
            self.cancel_charge()
            return None

        spawned_proj: Optional[Projectile] = None

        # Aim direction
        dir_x, dir_y = resolve_aim_vector(
            move_x=getattr(p_input, "move_x", 0.0),
            move_y=getattr(p_input, "move_y", 0.0),
            facing=getattr(player, "facing", "right"),
            is_crouching=getattr(player, "is_crouching", False),
            is_grounded=getattr(player, "is_grounded", True),
            aim_x=getattr(p_input, "aim_x", None),
            aim_y=getattr(p_input, "aim_y", None),
        )

        muzzle_x, muzzle_y = get_muzzle_world_pos(player)

        # 1. Fire Pressed: Immediate tap shot if off cooldown
        if getattr(p_input, "fire_pressed", False):
            self._charge_cancelled = False
            if self.cooldown_timer <= 0.0:
                spawned_proj = self._fire_tap(manager, player, muzzle_x, muzzle_y, dir_x, dir_y)

            self.charge_timer = 0.0
            self.is_charging = True

        # 2. Fire Held: Charge accumulation
        elif getattr(p_input, "fire_held", False):
            if not self._charge_cancelled:
                self.is_charging = True
                self.charge_timer += dt

        # 3. Fire Released: Release charged beam if charged
        elif getattr(p_input, "fire_released", False):
            if not self._charge_cancelled and self.is_fully_charged:
                spawned_proj = manager.spawn(
                    x=muzzle_x,
                    y=muzzle_y,
                    dir_x=dir_x,
                    dir_y=dir_y,
                    speed=self.cfg.projectile_speed * 1.15,
                    damage=self.cfg.charge_damage,
                    is_charged=True,
                    pierce_count=self.cfg.charge_pierce,
                    lifetime=self.cfg.lifetime,
                    beam_length=self.cfg.charge_beam_length,
                    beam_thickness=self.cfg.charge_beam_thickness,
                    weapon_type="starter_maser",
                )
                self.cooldown_timer = self.cfg.fire_cadence
                if hasattr(player, "trigger_fire_recoil"):
                    player.trigger_fire_recoil(self.cfg.recoil_duration * 1.5)

            self.charge_timer = 0.0
            self.is_charging = False
            self._charge_cancelled = False

        # Dedicated mouse/controller auto intent is separate from charging.
        # Press/hold/release above always take priority if inputs overlap.
        elif getattr(p_input, "auto_fire_held", False):
            # A stale or interrupted charge must never discharge on a later
            # release after the player has handed control to auto-fire.
            self.cancel_charge()
            if self.cooldown_timer <= 0.0:
                spawned_proj = self._fire_tap(manager, player, muzzle_x, muzzle_y, dir_x, dir_y)
        else:
            self.is_charging = False

        return spawned_proj


class AnalogScattergun(AnalogWeapon):
    """
    Model 77 Analog Scattergun.
    Discharges wide multi-pellet spread that illuminates targets and applies 'revealed' status.
    Revealed targets take 1.25x amplified damage.
    """

    def __init__(self, config_obj: Optional[WeaponConfig] = None):
        cfg = config_obj or WeaponConfig.load_from_file(weapon_id="scattergun")
        super().__init__(cfg)

    def update(
        self,
        dt: float,
        p_input: Any,
        player: Any,
        room: Room,
        manager: ProjectileManager,
        is_paused: bool = False,
    ) -> Optional[Projectile]:
        if is_paused or dt <= 0.0:
            return None
        if not self.is_unlocked:
            return None

        if self.cooldown_timer > 0.0:
            self.cooldown_timer = max(0.0, self.cooldown_timer - dt)

        can_fire = getattr(player, "can_fire", lambda r: True)(room)
        if not can_fire:
            return None

        primary_proj: Optional[Projectile] = None
        if getattr(p_input, "fire_pressed", False):
            if self.cooldown_timer <= 0.0:
                dir_x, dir_y = resolve_aim_vector(
                    move_x=getattr(p_input, "move_x", 0.0),
                    move_y=getattr(p_input, "move_y", 0.0),
                    facing=getattr(player, "facing", "right"),
                    is_crouching=getattr(player, "is_crouching", False),
                    is_grounded=getattr(player, "is_grounded", True),
                    aim_x=getattr(p_input, "aim_x", None),
                    aim_y=getattr(p_input, "aim_y", None),
                )
                muzzle_x, muzzle_y = get_muzzle_world_pos(player)
                base_angle = math.atan2(dir_y, dir_x)

                for deg in self.cfg.spread_angles:
                    rad = base_angle + math.radians(deg)
                    p_dx = math.cos(rad)
                    p_dy = math.sin(rad)
                    p = manager.spawn(
                        x=muzzle_x,
                        y=muzzle_y,
                        dir_x=p_dx,
                        dir_y=p_dy,
                        speed=self.cfg.projectile_speed,
                        damage=self.cfg.damage,
                        is_charged=False,
                        pierce_count=1,
                        lifetime=self.cfg.lifetime,
                        beam_length=6.0,
                        beam_thickness=2.0,
                        weapon_type="scattergun",
                        status_to_apply=("revealed", self.cfg.reveal_duration),
                        color=(255, 175, 45),
                    )
                    if primary_proj is None:
                        primary_proj = p

                self.cooldown_timer = self.cfg.fire_cadence
                if hasattr(player, "trigger_fire_recoil"):
                    player.trigger_fire_recoil(self.cfg.recoil_duration)

        return primary_proj


class EmpBola(AnalogWeapon):
    """
    Inductive EMP Bola.
    Fires an electromagnetic tether that applies 'stun' status for 2.0s on impact.
    Stunned targets have velocity suppressed and cannot initiate attacks.
    """

    def __init__(self, config_obj: Optional[WeaponConfig] = None):
        cfg = config_obj or WeaponConfig.load_from_file(weapon_id="emp_bola")
        super().__init__(cfg)

    def update(
        self,
        dt: float,
        p_input: Any,
        player: Any,
        room: Room,
        manager: ProjectileManager,
        is_paused: bool = False,
    ) -> Optional[Projectile]:
        if is_paused or dt <= 0.0:
            return None
        if not self.is_unlocked:
            return None

        if self.cooldown_timer > 0.0:
            self.cooldown_timer = max(0.0, self.cooldown_timer - dt)

        can_fire = getattr(player, "can_fire", lambda r: True)(room)
        if not can_fire:
            return None

        spawned_proj: Optional[Projectile] = None
        if getattr(p_input, "fire_pressed", False):
            if self.cooldown_timer <= 0.0:
                dir_x, dir_y = resolve_aim_vector(
                    move_x=getattr(p_input, "move_x", 0.0),
                    move_y=getattr(p_input, "move_y", 0.0),
                    facing=getattr(player, "facing", "right"),
                    is_crouching=getattr(player, "is_crouching", False),
                    is_grounded=getattr(player, "is_grounded", True),
                    aim_x=getattr(p_input, "aim_x", None),
                    aim_y=getattr(p_input, "aim_y", None),
                )
                muzzle_x, muzzle_y = get_muzzle_world_pos(player)
                spawned_proj = manager.spawn(
                    x=muzzle_x,
                    y=muzzle_y,
                    dir_x=dir_x,
                    dir_y=dir_y,
                    speed=self.cfg.projectile_speed,
                    damage=self.cfg.damage,
                    is_charged=False,
                    pierce_count=self.cfg.normal_pierce,
                    lifetime=self.cfg.lifetime,
                    beam_length=10.0,
                    beam_thickness=4.0,
                    weapon_type="emp_bola",
                    status_to_apply=("stun", self.cfg.stun_duration),
                    color=(130, 205, 255),
                )
                self.cooldown_timer = self.cfg.fire_cadence
                if hasattr(player, "trigger_fire_recoil"):
                    player.trigger_fire_recoil(self.cfg.recoil_duration)

        return spawned_proj


class FibonacciCoilgun(AnalogWeapon):
    """
    Harmonic Fibonacci Coilgun.
    Discharges precision rail pulses matching the Fibonacci sequence [1, 2, 3, 5, 8].
    Charge hold time unlocks discrete stages with deterministic damage and piercing multipliers.
    """

    def __init__(self, config_obj: Optional[WeaponConfig] = None):
        cfg = config_obj or WeaponConfig.load_from_file(weapon_id="fibonacci_coilgun")
        super().__init__(cfg)
        self._charge_cancelled = False

    def cancel_charge(self) -> None:
        """Discard interrupted charge until release or a fresh press."""
        self.charge_timer = 0.0
        self.is_charging = False
        self._charge_cancelled = True

    def reset(self) -> None:
        super().reset()
        self._charge_cancelled = True

    def get_current_stage(self) -> int:
        """Calculate discrete Fibonacci stage index [0..4] based on hold duration."""
        times = self.cfg.stage_hold_times
        stage_idx = 0
        for i, t in enumerate(times):
            if self.charge_timer >= t:
                stage_idx = i
            else:
                break
        return stage_idx

    @property
    def current_multiplier(self) -> int:
        idx = self.get_current_stage()
        return self.cfg.fibonacci_stages[idx]

    @property
    def current_pierce(self) -> int:
        idx = self.get_current_stage()
        return self.cfg.stage_pierce[idx]

    def update(
        self,
        dt: float,
        p_input: Any,
        player: Any,
        room: Room,
        manager: ProjectileManager,
        is_paused: bool = False,
    ) -> Optional[Projectile]:
        if is_paused or dt <= 0.0:
            return None
        if not self.is_unlocked:
            return None

        if self.cooldown_timer > 0.0:
            self.cooldown_timer = max(0.0, self.cooldown_timer - dt)

        can_fire = getattr(player, "can_fire", lambda r: True)(room)
        if not can_fire:
            self.cancel_charge()
            return None

        spawned_proj: Optional[Projectile] = None
        dir_x, dir_y = resolve_aim_vector(
            move_x=getattr(p_input, "move_x", 0.0),
            move_y=getattr(p_input, "move_y", 0.0),
            facing=getattr(player, "facing", "right"),
            is_crouching=getattr(player, "is_crouching", False),
            is_grounded=getattr(player, "is_grounded", True),
            aim_x=getattr(p_input, "aim_x", None),
            aim_y=getattr(p_input, "aim_y", None),
        )
        muzzle_x, muzzle_y = get_muzzle_world_pos(player)

        if getattr(p_input, "fire_pressed", False):
            self._charge_cancelled = False
            self.charge_timer = 0.0
            self.is_charging = True

        elif getattr(p_input, "fire_held", False):
            if not self._charge_cancelled:
                self.is_charging = True
                self.charge_timer += dt

        elif getattr(p_input, "fire_released", False):
            if not self._charge_cancelled and self.cooldown_timer <= 0.0:
                stage_idx = self.get_current_stage()
                mult = self.cfg.fibonacci_stages[stage_idx]
                pierce = self.cfg.stage_pierce[stage_idx]
                dmg = self.cfg.base_damage * mult
                speed = self.cfg.projectile_speed * (1.0 + 0.08 * stage_idx)

                spawned_proj = manager.spawn(
                    x=muzzle_x,
                    y=muzzle_y,
                    dir_x=dir_x,
                    dir_y=dir_y,
                    speed=speed,
                    damage=dmg,
                    is_charged=(stage_idx >= 2),
                    pierce_count=pierce,
                    lifetime=self.cfg.lifetime,
                    beam_length=14.0 + 4.0 * stage_idx,
                    beam_thickness=3.0 + 0.8 * stage_idx,
                    weapon_type="fibonacci_coilgun",
                    color=(245, 215, 65),
                )
                self.cooldown_timer = self.cfg.fire_cadence
                if hasattr(player, "trigger_fire_recoil"):
                    player.trigger_fire_recoil(self.cfg.recoil_duration * (1.0 + 0.2 * stage_idx))

            self.charge_timer = 0.0
            self.is_charging = False
            self._charge_cancelled = False
        else:
            self.is_charging = False

        return spawned_proj


class ArsenalManager:
    """Coordinates player analog arsenal weapons, cycling, and campaign unlocks."""

    def __init__(self, balance_file: Optional[Union[str, Path]] = None):
        self.weapons: Dict[str, AnalogWeapon] = {
            "starter_maser": StarterMaser(WeaponConfig.load_from_file(balance_file, "starter_maser")),
            "scattergun": AnalogScattergun(WeaponConfig.load_from_file(balance_file, "scattergun")),
            "emp_bola": EmpBola(WeaponConfig.load_from_file(balance_file, "emp_bola")),
            "fibonacci_coilgun": FibonacciCoilgun(WeaponConfig.load_from_file(balance_file, "fibonacci_coilgun")),
        }
        self.weapon_order: List[str] = ["starter_maser", "scattergun", "emp_bola", "fibonacci_coilgun"]
        self.active_weapon_id: str = "starter_maser"

    @property
    def active_weapon(self) -> AnalogWeapon:
        return self.weapons[self.active_weapon_id]

    def sync_unlocks(self, campaign: Optional[Any] = None):
        """Update unlock state for all weapons from campaign recorded events."""
        for w in self.weapons.values():
            w.check_unlocked(campaign)

    def select_weapon(self, weapon_id: str) -> bool:
        """Select active weapon by id. Refuses if weapon is locked."""
        if weapon_id not in self.weapons:
            return False
        w = self.weapons[weapon_id]
        if not w.is_unlocked:
            return False
        self.active_weapon_id = weapon_id
        return True

    def cycle_weapon(self, direction: int = 1) -> str:
        """Cycle to the next unlocked weapon in arsenal."""
        unlocked = [wid for wid in self.weapon_order if self.weapons[wid].is_unlocked]
        if not unlocked:
            return self.active_weapon_id
        if self.active_weapon_id not in unlocked:
            self.active_weapon_id = unlocked[0]
            return self.active_weapon_id
        curr_idx = unlocked.index(self.active_weapon_id)
        next_idx = (curr_idx + direction) % len(unlocked)
        self.active_weapon_id = unlocked[next_idx]
        return self.active_weapon_id

    def reset_all(self):
        """Reset weapon states on player respawn or death."""
        for w in self.weapons.values():
            w.reset()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize arsenal state for checkpoint/save persistence."""
        return {
            "active_weapon_id": self.active_weapon_id,
            "unlocked_weapons": {wid: w.is_unlocked for wid, w in self.weapons.items()},
        }

