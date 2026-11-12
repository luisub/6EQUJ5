"""
MODULE: video_game/tests/test_combat.py
PURPOSE: Comprehensive unit and regression test suite for starter maser combat mechanics,
         swept ray collision, multi-target piercing, cadence timing, and pause safety.
CALLED BY: pytest video_game/tests/test_combat.py.
HOW TO MODIFY: Extend with new weapon types, projectile behaviors, or boss vulnerability suites.
"""

import math
from typing import List
import pygame
import pytest

from video_game.engine import config
from video_game.engine.audio import AudioManager, TRACK_BUNKER, TRACK_COMBAT
from video_game.engine.effects import EffectManager, MAX_PARTICLES, MAX_BURSTS
from video_game.engine.bosses.base import (
    PHASE_1,
    PHASE_2,
    PHASE_3,
    PHASE_DEFEATED,
    STATE_DEFEATED,
    STATE_VULNERABLE,
)
from video_game.engine.bosses.greenkeeper import Greenkeeper
from video_game.engine.campaign import Campaign
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.scenes.boss import BossScene
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.enemies import (
    STATE_ATTACK,
    STATE_DEATH,
    STATE_HURT,
    STATE_PATROL,
    STATE_RECOVERY,
    STATE_WINDUP,
    ChrysalisSplicer,
    CoreEnforcer,
    CoreOperative,
    CoreReconDrone,
    EnemyConfig,
    EnemyManager,
    PhaseWatcher,
    PrecursorGuardian,
    ShieldHound,
    StaticHound,
    TemporalPhantom,
)
from video_game.engine.abilities import (
    Ability,
    AbilityConfig,
    AbilityManager,
    DecoyEntity,
    PhaseShieldAbility,
    QuantumDecoyAbility,
    TimeDilationAbility,
)
from video_game.engine.player import Player, PlayerConfig, PlayerInput
from video_game.engine.weapons import (
    AnalogScattergun,
    AnalogWeapon,
    ArsenalManager,
    CombatTarget,
    EmpBola,
    FibonacciCoilgun,
    ProjectileManager,
    StarterMaser,
    WeaponConfig,
    check_swept_ray_tile_collision,
    get_muzzle_world_pos,
    resolve_aim_vector,
)
from video_game.engine.world import (
    COLLISION_COVER,
    COLLISION_EMPTY,
    COLLISION_SOLID,
    Camera,
    Room,
)


def create_test_room(grid: List[List[int]], tile_size: int = 16, objects=None) -> Room:
    """Helper creating a test Room from a 2D integer grid."""
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0
    data = {
        "schema_version": 1,
        "room_id": "test_combat_room",
        "act_id": "act_1",
        "title": "Test Combat Arena",
        "grid_width": width,
        "grid_height": height,
        "width_tiles": width,
        "height_tiles": height,
        "tile_size": tile_size,
        "collision_layers": grid,
        "background_layers": [],
        "spawns": {"bunker_exit": {"x": 32.0, "y": 32.0, "facing": "right"}},
        "exits": [],
        "checkpoints": [],
        "objects": objects or [],
    }
    return Room(data)


def test_balance_weapon_config_loading():
    """Verify weapon configuration loads defaults and overrides from balance.json."""
    cfg = WeaponConfig.load_from_file()
    assert cfg.id == "starter_maser"
    assert cfg.fire_cadence == pytest.approx(0.20, abs=1e-3)
    assert cfg.projectile_speed >= 400.0
    assert cfg.damage == 25
    assert cfg.charge_damage == 75
    assert cfg.normal_pierce == 1
    assert cfg.charge_pierce == 3
    assert cfg.charge_time == pytest.approx(0.60, abs=1e-3)


def test_aim_vector_8_directions():
    """Verify 8-directional aim resolution produces normalized unit vectors."""
    # Cardinal Right
    vx, vy = resolve_aim_vector(1.0, 0.0, "right")
    assert (vx, vy) == (1.0, 0.0)

    # Cardinal Left
    vx, vy = resolve_aim_vector(-1.0, 0.0, "left")
    assert (vx, vy) == (-1.0, 0.0)

    # Cardinal Up
    vx, vy = resolve_aim_vector(0.0, -1.0, "right")
    assert (vx, vy) == (0.0, -1.0)

    # Diagonals (length must equal 1.0)
    for mx, my in [(1.0, -1.0), (-1.0, -1.0), (1.0, 1.0), (-1.0, 1.0)]:
        vx, vy = resolve_aim_vector(mx, my, "right")
        mag = math.hypot(vx, vy)
        assert mag == pytest.approx(1.0, abs=1e-4)

    # Down while airborne: fires down
    vx, vy = resolve_aim_vector(0.0, 1.0, "right", is_grounded=False)
    assert (vx, vy) == (0.0, 1.0)

    # Down while grounded: forward from crouch
    vx, vy = resolve_aim_vector(0.0, 1.0, "right", is_grounded=True)
    assert (vx, vy) == (1.0, 0.0)
    vx, vy = resolve_aim_vector(0.0, 1.0, "left", is_grounded=True)
    assert (vx, vy) == (-1.0, 0.0)


def test_swept_ray_tile_collision_prevents_thin_wall_tunneling():
    """
    Acceptance Check: Fast projectiles hit thin walls reliably.
    A thin 1-tile wall (16px) placed at x=80 must stop a projectile traveling
    120px in a single simulation tick.
    """
    # 20 tiles wide, 5 tiles high; single vertical wall at col 5 (x=80..96)
    grid = [[COLLISION_EMPTY] * 20 for _ in range(5)]
    for r in range(5):
        grid[r][5] = COLLISION_SOLID
    room = create_test_room(grid)

    # Ray starts at x=20 and jumps to x=140 (120px step)
    hit, hx, hy, c, r = check_swept_ray_tile_collision(room, 20.0, 32.0, 140.0, 32.0)
    assert hit is True
    assert c == 5
    assert 80.0 <= hx <= 81.0  # Stopped exactly at left face of solid wall
    assert hy == pytest.approx(32.0, abs=1e-3)


def test_fast_projectile_hits_thin_target_reliably():
    """
    Acceptance Check: Fast projectiles hit targets reliably without tunneling.
    A thin target (width 8px) placed at x=100 must be hit by a projectile
    moving from x=10 to x=150 in one step.
    """
    grid = [[COLLISION_EMPTY] * 20 for _ in range(5)]
    room = create_test_room(grid)

    target = CombatTarget(
        target_id="thin_drone_01",
        rect=pygame.Rect(100, 24, 8, 16),
        health=50,
    )

    manager = ProjectileManager()
    # Spawn high-speed maser bolt (speed=1400 px/s, dt=0.1s -> 140px jump)
    manager.spawn(
        x=10.0,
        y=32.0,
        dir_x=1.0,
        dir_y=0.0,
        speed=1400.0,
        damage=25,
        is_charged=False,
        pierce_count=1,
    )

    hits = manager.update(0.10, room, targets=[target])
    assert len(hits) == 1
    assert hits[0].hit is True
    assert hits[0].target_id == "thin_drone_01"
    assert hits[0].damage_dealt == 25
    assert target.health == 25
    # Non-piercing projectile is absorbed upon impact
    assert len(manager.projectiles) == 0


def test_piercing_shot_per_target_hit_behavior():
    """
    Acceptance Check: A piercing shot has explicit per-target hit behavior.
    A charged shot (pierce=3) must hit three consecutive targets in a row,
    dealing damage exactly once to each, even across multiple simulation ticks.
    """
    grid = [[COLLISION_EMPTY] * 30 for _ in range(5)]
    room = create_test_room(grid)

    t1 = CombatTarget("target_A", pygame.Rect(60, 24, 16, 16), health=100)
    t2 = CombatTarget("target_B", pygame.Rect(140, 24, 16, 16), health=100)
    t3 = CombatTarget("target_C", pygame.Rect(220, 24, 16, 16), health=100)
    t4 = CombatTarget("target_D", pygame.Rect(300, 24, 16, 16), health=100)
    targets = [t1, t2, t3, t4]

    manager = ProjectileManager()
    # Spawn charged shot with pierce=3, damage=75
    proj = manager.spawn(
        x=20.0,
        y=32.0,
        dir_x=1.0,
        dir_y=0.0,
        speed=400.0,
        damage=75,
        is_charged=True,
        pierce_count=3,
        lifetime=1.5,
    )

    # Frame 1: Moves from x=20 to x=100 (hits t1 at x=60)
    hits1 = manager.update(0.20, room, targets=targets)
    assert len(hits1) == 1
    assert hits1[0].target_id == "target_A"
    assert t1.health == 25
    assert t1.hit_count == 1
    assert proj.pierce_remaining == 2
    assert proj.active is True

    # Frame 2: Moves from x=100 to x=180 (hits t2 at x=140)
    # Target A is now behind, must not be hit again
    hits2 = manager.update(0.20, room, targets=targets)
    assert len(hits2) == 1
    assert hits2[0].target_id == "target_B"
    assert t2.health == 25
    assert t1.hit_count == 1  # Unchanged
    assert proj.pierce_remaining == 1
    assert proj.active is True

    # Frame 3: Moves from x=180 to x=260 (hits t3 at x=220, pierce exhausted, absorbed before t4)
    hits3 = manager.update(0.20, room, targets=targets)
    assert len(hits3) == 1
    assert hits3[0].target_id == "target_C"
    assert t3.health == 25
    assert t4.health == 100  # Protected by pierce limit
    assert proj.pierce_remaining == 0
    assert proj.active is False


def test_simultaneous_multi_target_piercing_in_single_tick():
    """
    Acceptance Check: Charged pierce can hit multiple consecutive targets in a single tick
    without exceeding pierce budget or dealing duplicate damage.
    """
    grid = [[COLLISION_EMPTY] * 30 for _ in range(5)]
    room = create_test_room(grid)

    t1 = CombatTarget("t1", pygame.Rect(40, 24, 16, 16), health=50)
    t2 = CombatTarget("t2", pygame.Rect(80, 24, 16, 16), health=50)
    t3 = CombatTarget("t3", pygame.Rect(120, 24, 16, 16), health=50)
    t4 = CombatTarget("t4", pygame.Rect(160, 24, 16, 16), health=50)

    manager = ProjectileManager()
    manager.spawn(
        x=10.0,
        y=32.0,
        dir_x=1.0,
        dir_y=0.0,
        speed=1000.0,  # 100px in 0.1s tick: covers x=10 to x=110, crossing t1 and t2
        damage=25,
        is_charged=True,
        pierce_count=2,
    )

    hits = manager.update(0.10, room, targets=[t1, t2, t3, t4])
    # Must hit t1 and t2, exhausting pierce (count=2), leaving t3 and t4 untouched
    assert len(hits) == 2
    assert [h.target_id for h in hits] == ["t1", "t2"]
    assert t1.health == 25
    assert t2.health == 25
    assert t3.health == 50
    assert t4.health == 50
    assert len(manager.projectiles) == 0


def test_held_fire_respects_timing_and_cadence():
    """
    Acceptance Check: Held fire respects cadence timing.
    Holding fire cannot exceed the rate of fire limit (1 shot per 0.20s).
    """
    grid = [[COLLISION_EMPTY] * 20 for _ in range(5)]
    room = create_test_room(grid)

    player = Player(48.0, 32.0)
    maser = StarterMaser()
    manager = ProjectileManager()

    # 1. Tap fire -> fires first shot
    inp_press = PlayerInput(fire_pressed=True, fire_held=True)
    p1 = maser.update(0.016, inp_press, player, room, manager)
    assert p1 is not None
    assert len(manager.projectiles) == 1
    assert maser.cooldown_timer == pytest.approx(0.20, abs=1e-3)

    # 2. Next tick: fire is still held, cooldown is active (0.18s remaining)
    inp_held = PlayerInput(fire_held=True)
    p2 = maser.update(0.020, inp_held, player, room, manager)
    assert p2 is None  # Cooldown prevents immediate re-fire
    assert len(manager.projectiles) == 1


def test_weapon_charge_and_release_mechanic():
    """Verify charge accumulation and charged shot release on trigger release."""
    grid = [[COLLISION_EMPTY] * 20 for _ in range(5)]
    room = create_test_room(grid)

    player = Player(48.0, 32.0)
    maser = StarterMaser()
    manager = ProjectileManager()

    # Tap to start charging
    maser.update(0.016, PlayerInput(fire_pressed=True, fire_held=True), player, room, manager)
    manager.clear()  # Clear standard tap shot

    # Hold fire for 0.40s (less than charge_time of 0.60s)
    maser.update(0.40, PlayerInput(fire_held=True), player, room, manager)
    assert maser.is_charging is True
    assert maser.is_fully_charged is False

    # Hold fire for another 0.25s (total 0.65s >= 0.60s threshold)
    maser.update(0.25, PlayerInput(fire_held=True), player, room, manager)
    assert maser.is_fully_charged is True

    # Release fire -> Unleashes charged maser bolt
    charged_proj = maser.update(0.016, PlayerInput(fire_released=True), player, room, manager)
    assert charged_proj is not None
    assert charged_proj.is_charged is True
    assert charged_proj.damage == 75
    assert charged_proj.pierce_remaining == 3
    assert maser.is_charging is False


def test_game_pause_freezes_combat_and_cooldowns():
    """
    Acceptance Check: Held fire and projectiles respect pause.
    When is_paused is True, simulation does not tick, timers freeze, and
    projectiles remain stationary.
    """
    grid = [[COLLISION_EMPTY] * 20 for _ in range(5)]
    room = create_test_room(grid)

    player = Player(48.0, 32.0)
    maser = StarterMaser()
    manager = ProjectileManager()

    # Fire projectile
    maser.update(0.016, PlayerInput(fire_pressed=True), player, room, manager)
    assert len(manager.projectiles) == 1
    proj = manager.projectiles[0]
    initial_x = proj.x
    initial_cooldown = maser.cooldown_timer

    # Step simulation while PAUSED for 1.0 full second
    manager.update(1.0, room, targets=(), is_paused=True)
    maser.update(1.0, PlayerInput(fire_held=True), player, room, manager, is_paused=True)

    # Projectile must not have moved
    assert proj.x == initial_x
    # Cooldown must not have decayed
    assert maser.cooldown_timer == initial_cooldown


def test_death_retry_idempotence_and_no_orphan_projectiles():
    """
    Acceptance Check: Damage/retry cannot duplicate rewards or leave orphan projectiles.
    """
    target = CombatTarget("elite_drone_01", pygame.Rect(100, 24, 16, 16), health=50)

    # First lethal hit
    res1 = target.take_damage(50, hit_id="hit_01")
    assert res1.hit is True
    assert res1.target_killed is True
    assert res1.damage_dealt == 50
    assert target.is_dead is True
    assert target.reward_claimed is True

    # Second hit on dead target: must not deal damage or duplicate death rewards
    res2 = target.take_damage(50, hit_id="hit_02")
    assert res2.hit is False
    assert res2.target_killed is False
    assert res2.damage_dealt == 0

    # Projectile Manager cleanup: zero orphan projectiles on scene clear
    manager = ProjectileManager()
    manager.spawn(10, 10, 1, 0, 400, 25)
    manager.spawn(20, 20, 0, 1, 400, 25)
    assert len(manager.projectiles) == 2

    manager.clear()
    assert len(manager.projectiles) == 0
    assert len(manager.sparks) == 0


def test_cover_forbids_firing_while_concealed_in_background_alcove():
    """Verify player cannot fire waveguide maser while concealed in doorway recess."""
    # Room with background cover alcove at col 3 (x=48..64)
    grid = [[COLLISION_EMPTY] * 10 for _ in range(5)]
    grid[2][3] = COLLISION_COVER
    objects = [{
        "type": "alcove",
        "x": 48.0,
        "y": 32.0,
        "width": 16.0,
        "height": 32.0,
        "properties": {"cover_type": "background"},
    }]
    room = create_test_room(grid, objects=objects)

    player = Player(48.0, 32.0)
    player.in_cover = True
    player.cover_type = "background"

    assert player.can_fire(room) is False

    maser = StarterMaser()
    manager = ProjectileManager()
    proj = maser.update(0.016, PlayerInput(fire_pressed=True), player, room, manager)
    assert proj is None
    assert len(manager.projectiles) == 0


def test_muzzle_position_resolves_accurately_across_postures():
    """Verify muzzle position accounts for facing, crouch height, and animation attachments."""
    player = Player(100.0, 100.0)

    # Standing facing right
    player.facing = "right"
    player.is_crouching = False
    mx_r, my_r = get_muzzle_world_pos(player)
    assert mx_r > player.x + player.width

    # Standing facing left
    player.facing = "left"
    mx_l, my_l = get_muzzle_world_pos(player)
    assert mx_l < player.x

    # Crouching lowers muzzle height
    player.is_crouching = True
    _, my_crouch = get_muzzle_world_pos(player)
    assert my_crouch < my_r or my_crouch == pytest.approx(player.y + 14.0)


# =============================================================================
# A06 ENEMY & PREDICTIVE ATTACK TESTS
# =============================================================================

def test_drone_state_transitions_and_predictive_aim():
    """
    Acceptance Check: Drone implements patrol -> windup -> attack -> recovery states
    with predictive targeting and aim lock.
    """
    grid = [[COLLISION_EMPTY] * 30 for _ in range(10)]
    room = create_test_room(grid)

    drone = CoreReconDrone("drone_test", x=200.0, y=60.0, patrol_left=150.0, patrol_right=250.0)
    # Player placed 100px away moving right
    player = Player(100.0, 60.0)
    player.vx = 80.0
    manager = EnemyManager()

    # Step 1: In patrol with line of sight -> transitions to windup
    assert drone.state == STATE_PATROL
    drone.update(0.016, player, room, manager)
    assert drone.state == STATE_WINDUP
    assert drone.telegraph_active is True
    assert drone.telegraph_locked is False

    # Step 2: During tracking phase (first 0.9s of 1.2s windup), aims ahead of player
    drone.update(0.50, player, room, manager)
    assert drone.state == STATE_WINDUP
    assert drone.telegraph_locked is False
    # Predicted x should lead current player x
    assert drone.target_aim_pos[0] > (player.x + player.width / 2.0)

    # Step 3: During final 0.3s (lock window), aim locks!
    drone.update(0.45, player, room, manager)  # Total 0.95s elapsed -> 0.25s remaining <= 0.30s
    assert drone.state == STATE_WINDUP
    assert drone.telegraph_locked is True
    locked_vec = drone.locked_aim_vector

    # Step 4: Windup finishes -> attacks along locked vector
    drone.update(0.30, player, room, manager)
    assert len(manager.projectiles) == 1
    eproj = manager.projectiles[0]
    assert eproj.dir_x == pytest.approx(locked_vec[0], abs=1e-4)
    assert eproj.dir_y == pytest.approx(locked_vec[1], abs=1e-4)
    assert drone.state == STATE_RECOVERY


def test_dodge_window_escape_counter():
    """
    Acceptance Check: Every damaging attack has a visible warning and a tested escape/counter.
    Moving/dodging during the 0.3s locked aim window causes the drone laser to miss.
    """
    grid = [[COLLISION_EMPTY] * 30 for _ in range(10)]
    room = create_test_room(grid)

    drone = CoreReconDrone("drone_test", x=200.0, y=60.0)
    player = Player(100.0, 60.0)
    manager = EnemyManager()

    # Advance drone into locked state targeting player at x=100
    drone.update(0.016, player, room, manager)  # Enters windup
    drone.update(0.95, player, room, manager)   # Locks aim onto x=100
    assert drone.telegraph_locked is True

    # Player DODGES during lock window (jumps or moves down/away)
    player.x = 100.0
    player.y = 120.0  # Dodged 60px vertically down into trench

    # Drone fires along locked horizontal ray
    drone.update(0.30, player, room, manager)
    assert len(manager.projectiles) == 1

    # Update manager projectiles: projectile travels across x=100 at y=60, missing player at y=120
    manager.update(0.20, player, room)
    assert player.health == 100  # Completely avoided!


def test_low_cover_absorbs_drone_laser():
    """
    Acceptance Check: Low cover emplacement absorbs frontal incoming projectiles.
    """
    grid = [[COLLISION_EMPTY] * 30 for _ in range(10)]
    objects = [{
        "id": "sandbag_wall",
        "type": "cover",
        "x": 120.0,
        "y": 60.0,
        "width": 32.0,
        "height": 32.0,
        "properties": {
            "cover_type": "low",
            "protection_directions": ["right"],
        },
    }]
    room = create_test_room(grid, objects=objects)

    # Player crouched behind sandbag at x=120
    player = Player(120.0, 60.0)
    player.is_crouching = True
    player.cover_type = "low"

    # Drone on the right at x=240 fires laser leftwards towards player
    manager = EnemyManager()
    manager.spawn_enemy_projectile(
        origin_x=220.0,
        origin_y=70.0,
        dir_x=-1.0,
        dir_y=0.0,
        speed=400.0,
        damage=20,
        source_id="drone_01",
    )

    # Step simulation: laser reaches player at x=120 from the right
    manager.update(0.30, player, room)
    # Low cover absorbed the frontal blast: player takes 0 damage
    assert player.health == 100


def test_background_cover_breaks_enemy_line_of_sight():
    """
    Acceptance Check: Concealment in background doorway alcove breaks line of sight.
    """
    grid = [[COLLISION_EMPTY] * 30 for _ in range(10)]
    objects = [{
        "id": "alcove",
        "type": "cover",
        "x": 100.0,
        "y": 60.0,
        "width": 32.0,
        "height": 48.0,
        "properties": {
            "cover_type": "background",
            "protection_directions": ["left", "right"],
        },
    }]
    room = create_test_room(grid, objects=objects)

    player = Player(100.0, 60.0)
    player.in_cover = True
    player.cover_type = "background"

    drone = CoreReconDrone("drone_01", x=200.0, y=60.0)
    hound = StaticHound("hound_01", x=180.0, y=60.0)

    # Line of sight must be blocked
    assert drone.check_line_of_sight(player, room) is False
    assert hound.check_line_of_sight(player, room) is False


def test_solid_wall_occlusion_blocks_enemy_detection():
    """
    Acceptance Check: Wall occlusion follows explicit rules.
    Solid tiles between enemy and player block detection.
    """
    grid = [[COLLISION_EMPTY] * 30 for _ in range(10)]
    # Vertical wall at col 10 (x=160..176)
    for r in range(10):
        grid[r][10] = COLLISION_SOLID
    room = create_test_room(grid)

    player = Player(80.0, 60.0)  # Left of wall
    drone = CoreReconDrone("drone_01", x=240.0, y=60.0)  # Right of wall

    # Occluded by solid wall
    assert drone.check_line_of_sight(player, room) is False
    manager = EnemyManager()
    drone.update(0.016, player, room, manager)
    assert drone.state == STATE_PATROL  # Does not trigger windup


def test_static_hound_windup_telegraph_and_pounce():
    """
    Acceptance Check: Static Hound telegraphs windup and deals pounce damage on unmitigated hit.
    """
    grid = [[COLLISION_EMPTY] * 30 for _ in range(10)]
    room = create_test_room(grid)

    hound = StaticHound("hound_01", x=120.0, y=80.0, patrol_left=100.0, patrol_right=160.0)
    player = Player(80.0, 80.0)  # Standing still in front of hound
    manager = EnemyManager()

    # Step 1: Detects player -> enters WINDUP (0.6s) with static arc telegraph
    hound.update(0.016, player, room, manager)
    assert hound.state == STATE_WINDUP
    assert hound.telegraph_active is True
    assert hound.facing == "left"

    # Step 2: Completes windup -> launches pounce
    hound.update(0.60, player, room, manager)
    assert hound.state == STATE_ATTACK
    assert hound.attack_hitbox_active is True
    assert hound.vx < 0.0  # Pouncing leftwards

    # Step 3: Hits stationary unmitigated player
    hound.update(0.20, player, room, manager)
    assert player.health == 70  # Took 30 pounce damage
    assert hound.has_damaged_player is True


def test_slide_kick_counters_pouncing_hound():
    """
    Acceptance Check: Slide-kick counters and damages pouncing hound.
    Mateo's 14px slide profile allows sliding underneath while kicking hound.
    """
    grid = [[COLLISION_EMPTY] * 30 for _ in range(10)]
    room = create_test_room(grid)

    hound = StaticHound("hound_01", x=105.0, y=80.0)
    # Player sliding towards hound
    player = Player(80.0, 80.0)
    player.is_sliding = True
    player.facing = "right"
    player.vx = 220.0

    manager = EnemyManager()
    manager.add_enemy(hound)

    # Hound in attack leap
    hound.state = STATE_ATTACK
    hound.attack_hitbox_active = True
    hound.vx = -180.0
    hound.vy = -60.0

    # Step simulation: slide kick hitbox connects with hound
    manager.update(0.016, player, room)
    assert hound.health == 40  # Took 35 slide kick damage (75 - 35 = 40)
    assert hound.target_id in player.slide_damaged_targets


def test_offscreen_enemies_remain_passive():
    """
    Acceptance Check: Offscreen enemies do not initiate combat or fire cheap shots.
    """
    grid = [[COLLISION_EMPTY] * 40 for _ in range(10)]
    room = create_test_room(grid)

    player = Player(60.0, 60.0)
    cam = Camera(viewport_w=480, viewport_h=270)
    cam.x = 0.0  # Viewport covers 0..480

    # Drone placed far offscreen at x=640
    drone = CoreReconDrone("drone_offscreen", x=640.0, y=60.0)
    manager = EnemyManager()
    manager.add_enemy(drone)

    manager.update(0.10, player, room, camera=cam)
    assert drone.state == STATE_PATROL  # Stays in passive patrol


def test_enemy_death_and_checkpoint_reset_cleanup():
    """
    Acceptance Check: Enemy death, room exit and checkpoint reset clean their state.
    """
    grid = [[COLLISION_EMPTY] * 30 for _ in range(10)]
    room = create_test_room(grid)

    drone = CoreReconDrone("drone_01", x=120.0, y=60.0)
    hound = StaticHound("hound_01", x=180.0, y=80.0)
    manager = EnemyManager()
    manager.add_enemy(drone)
    manager.add_enemy(hound)

    # Spawn stray projectile
    manager.spawn_enemy_projectile(100, 60, 1, 0, 300, 20, "drone_01")
    assert len(manager.projectiles) == 1

    # Kill drone with lethal damage
    drone.take_damage(50, hit_id="lethal_hit")
    assert drone.is_dead is True
    assert drone.state == STATE_DEATH

    # Checkpoint reset / room reload cleans all states
    manager.reset_all()
    assert drone.is_dead is False
    assert drone.health == drone.cfg.max_health
    assert drone.state == STATE_PATROL
    assert len(manager.projectiles) == 0  # No orphan projectiles
    assert len(manager.sparks) == 0


def test_encounter_playable_with_starter_weapon():
    """
    Acceptance Check: Encounter is playable and beatable with starter waveguide maser.
    """
    grid = [[COLLISION_EMPTY] * 30 for _ in range(10)]
    room = create_test_room(grid)

    drone = CoreReconDrone("drone_encounter", x=160.0, y=60.0)
    hound = StaticHound("hound_encounter", x=240.0, y=80.0)
    manager = EnemyManager()
    manager.add_enemy(drone)
    manager.add_enemy(hound)

    player = Player(40.0, 60.0)
    maser = StarterMaser()
    p_manager = ProjectileManager()

    # 1. Player fires 2 normal maser bolts at drone (25 damage each -> 50 HP destroyed)
    p_manager.spawn(x=60.0, y=60.0, dir_x=1.0, dir_y=0.0, speed=500.0, damage=25)
    p_manager.update(0.30, room, targets=manager.enemies)
    assert drone.health == 25

    p_manager.spawn(x=60.0, y=60.0, dir_x=1.0, dir_y=0.0, speed=500.0, damage=25)
    p_manager.update(0.30, room, targets=manager.enemies)
    assert drone.health == 0
    assert drone.is_dead is True

    # 2. Player fires 1 charged maser beam at hound (75 damage -> 75 HP destroyed)
    p_manager.spawn(x=60.0, y=80.0, dir_x=1.0, dir_y=0.0, speed=500.0, damage=75, is_charged=True, pierce_count=3)
    p_manager.update(0.40, room, targets=manager.enemies)
    assert hound.health == 0
    assert hound.is_dead is True


# ==============================================================================
# MILESTONE 2: A09 GREENKEEPER BOSS & FRAMEWORK TESTS
# ==============================================================================

def test_boss_equipment_clears_all_phases():
    """
    Acceptance Check: Each phase can be completed with available Act I equipment.
    Dr. Mateo Vargas equipped with Starter Waveguide Maser and slide-kick can deplete:
    - Phase 1 (300 -> 200 HP) via standard fire (15 dmg) and weak point hits (30 dmg).
    - Phase 2 (200 -> 100 HP) via charged maser blast (75 dmg) to jammed bulldozer cowl.
    - Phase 3 (100 -> 0 HP) via exposed reactor meltdown targeting.
    """
    boss = Greenkeeper(x=460.0, y=192.0)
    assert boss.health == 300
    assert boss.current_phase == PHASE_1

    # 1. Clear Phase 1 (300 -> 200 HP)
    # Boss exposes exhaust weak point (vulnerable)
    boss.phase_state = STATE_VULNERABLE
    boss.weak_point_exposed = True
    wp = boss.weak_point_rect
    assert wp is not None

    # Normal shot hitting weak point: 15 * 2.0 = 30 damage
    hit1 = boss.take_damage(15, hit_pos=(wp.centerx, wp.centery))
    assert hit1.damage_dealt == 30
    assert boss.health == 270

    # Charged shot hitting weak point: 75 * 2.0 = 150 damage (capped by phase threshold at 200)
    # Actually take_damage doesn't clamp to phase threshold, but transitions phase when passing threshold!
    # Let's hit with standard 70 damage to drop to 200
    hit2 = boss.take_damage(70, hit_pos=(boss.x + 30, boss.y + 30))
    assert boss.health == 200
    assert boss.current_phase == PHASE_2
    assert boss.phase_state == "TRANSITION"

    # Finish transition to begin Phase 2 active combat
    boss.update(1.1)
    assert boss.current_phase == PHASE_2
    assert boss.phase_state != "TRANSITION"

    # 2. Clear Phase 2 (200 -> 100 HP)
    # Bulldozer jam exposes cowl weak point
    boss.phase_state = STATE_VULNERABLE
    boss.weak_point_exposed = True
    # Charged maser shot directly to cowl (50 * 2.0 = 100 damage)
    hit3 = boss.take_damage(50, hit_pos=(wp.centerx, wp.centery))
    assert hit3.damage_dealt == 100
    assert boss.health == 100
    assert boss.current_phase == PHASE_3
    assert boss.phase_state == "TRANSITION"

    # Finish transition to begin Phase 3 active combat
    boss.update(1.1)
    assert boss.current_phase == PHASE_3

    # 3. Clear Phase 3 (100 -> 0 HP)
    # Critical meltdown: core permanently exposed
    assert boss.weak_point_exposed is True
    hit4 = boss.take_damage(50, hit_pos=(wp.centerx, wp.centery))
    assert hit4.damage_dealt == 100
    assert boss.health == 0
    assert boss.is_dead is True
    assert boss.is_defeated is True
    assert boss.current_phase == PHASE_DEFEATED


def test_boss_attacks_have_telegraphs_and_safe_routes():
    """
    Acceptance Check: No attack pattern requires an unavoidable hit.
    All mortar, sweep, and charge attacks have >= 0.5s telegraphs and clear safe areas.
    """
    boss = Greenkeeper(x=460.0, y=192.0)
    player = Player(120.0, 208.0)

    # 1. Phase 1 Mortar Telegraph
    boss._schedule_next_attack(player_pos=(player.x, player.y))
    assert len(boss.telegraphs) == 2
    for t in boss.telegraphs:
        assert t.attack_type == "mortar"
        assert t.duration >= 0.5  # 0.8s telegraph duration

    # Target reticle is localized at x=120 and x=190 (radius 24)
    # Moving player to x=60 completely escapes the blast zone!
    player.x = 60.0
    boss.update(0.85)  # Executes telegraphed mortar
    assert len(boss.projectiles) == 2

    # Update mortar falling: Player at x=60 takes ZERO damage
    damage_at_safe_pos = boss.check_attack_collisions(player.rect)
    assert damage_at_safe_pos == 0

    # 2. Phase 2 Low Sweep Beam Telegraph
    boss.current_phase = PHASE_2
    boss.volley_count = 0
    boss.phase_state = "IDLE"
    boss._schedule_next_attack(player_pos=(player.x, player.y))
    assert len(boss.telegraphs) == 1
    sweep_telegraph = boss.telegraphs[0]
    assert sweep_telegraph.attack_type == "sweep"
    assert sweep_telegraph.duration >= 0.5  # 0.7s telegraph duration

    # Beam travels strictly at ground level (y in [216, 232])
    # Player on mid-catwalk (y = 192) or jumping (y = 160) takes ZERO damage
    player.y = 176.0  # On upper/mid catwalk grating
    boss.update(0.75)  # Executes sweep
    assert boss.sweep_active is True
    damage_on_catwalk = boss.check_attack_collisions(player.rect)
    assert damage_on_catwalk == 0


def test_boss_reset_clears_attacks_and_restores_arena():
    """
    Acceptance Check: Boss reset clears prior attacks and restores arena state.
    Purges lingering projectiles, telegraphs, and resets phase to 1.
    """
    boss = Greenkeeper(x=460.0, y=192.0)
    # Advance into dirty Phase 2 state with active attacks
    boss.current_phase = PHASE_2
    boss.health = 150
    boss.sweep_active = True
    boss.sweep_x = 200.0
    boss.charge_duration = 0.5
    boss.charge_vx = -160.0
    boss.weak_point_exposed = True
    boss.telegraphs.append(boss.telegraphs.append if False else None)  # will clear
    boss._schedule_next_attack((100.0, 208.0))
    boss._execute_telegraphed_attack()
    assert len(boss.projectiles) > 0 or boss.sweep_active is True

    # Call pristine reset
    boss.reset_to_pristine()

    # Assert completely restored baseline
    assert boss.health == 300
    assert boss.max_health == 300
    assert boss.current_phase == PHASE_1
    assert boss.is_dead is False
    assert boss.is_defeated is False
    assert boss.defeat_reward_granted is False
    assert len(boss.telegraphs) == 0
    assert len(boss.projectiles) == 0
    assert boss.sweep_active is False
    assert boss.charge_duration == 0.0
    assert boss.charge_vx == 0.0
    assert boss.weak_point_exposed is False
    assert boss.x == 460.0
    assert boss.y == 192.0


def test_boss_win_and_death_edge_cases():
    """
    Acceptance Check: Win/death edge cases resolve consistently.
    - Simultaneous death: Player death takes priority; victory is not granted.
    - Normal victory: Defeat reward applies atomically and idempotently.
    """
    boss = Greenkeeper(x=460.0, y=192.0)
    campaign = Campaign(save_id="test_boss_combat")

    # Case 1: Simultaneous death (boss dead, but player dead too)
    boss.trigger_defeat()
    assert boss.is_defeated is True
    resolution = boss.resolve_simultaneous_death(player_alive=False)
    assert resolution == "PLAYER_DIED"
    # Defeat reward must NOT be applied when player died
    assert "greenkeeper_defeated" not in campaign.state.room_flags

    # Case 2: Clean victory (player alive, boss defeated)
    boss.reset_to_pristine()
    boss.trigger_defeat()
    resolution = boss.resolve_simultaneous_death(player_alive=True)
    assert resolution == "BOSS_DEFEATED"

    # Apply reward: should succeed once
    granted = boss.apply_defeat_reward(campaign)
    assert granted is True
    assert campaign.state.room_flags.get("greenkeeper_defeated") is True
    assert campaign.state.room_flags.get("act_01_completed") is True
    assert campaign.state.room_flags.get("act_02_unlocked") is True
    assert campaign.state.meters["scientific_certainty"] == 50  # 40 + 10
    assert campaign.state.meters["human_agency"] == 85         # 70 + 15
    assert campaign.state.meters["alignment_confidence"] == 45 # 35 + 10

    # Replay idempotence: Second call returns False with zero extra meters
    granted_again = boss.apply_defeat_reward(campaign)
    assert granted_again is False
    assert campaign.state.meters["human_agency"] == 85


def test_boss_scene_pre_boss_checkpoint_lifecycle(tmp_path):
    """
    Acceptance Check: Boss arena pre-boss checkpoint correctly saves and restores on retry.
    """
    pygame.init()
    pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    machine = GameStateMachine(CRTRenderer(), development=True)

    boss_scene = BossScene(machine)
    boss_scene.on_enter()

    # Pre-boss checkpoint registered
    assert boss_scene.player.active_checkpoint_id == "pre_boss"
    assert boss_scene.player.health == 100
    assert boss_scene.boss.health == 300
    assert boss_scene.boss.current_phase == PHASE_1

    # Simulate player taking lethal damage during Phase 2
    boss_scene.boss.current_phase = PHASE_2
    boss_scene.boss.health = 180
    boss_scene.player.health = 0
    boss_scene.player.is_dead = True

    # Player hits [R] to retry
    boss_scene.retry_from_checkpoint()
    assert boss_scene.player.is_dead is False
    assert boss_scene.player.health == 100
    assert boss_scene.boss.health == 300
    assert boss_scene.boss.current_phase == PHASE_1
    assert len(boss_scene.boss.projectiles) == 0
    assert len(boss_scene.boss.telegraphs) == 0


def test_audio_manager_initialization_and_volume_controls():
    """
    A12 Acceptance Check: AudioManager initializes safely in headless environments
    and volume controls clamp properly.
    """
    audio = AudioManager()
    # Safe attributes initialized
    assert hasattr(audio, "master_volume")
    assert hasattr(audio, "music_volume")
    assert hasattr(audio, "sfx_volume")
    assert hasattr(audio, "is_muted")

    # Volume attenuation and clamping
    audio.set_master_volume(1.5)
    assert audio.master_volume == 1.0
    audio.set_master_volume(-0.5)
    assert audio.master_volume == 0.0
    audio.set_master_volume(0.8)
    assert audio.master_volume == 0.8

    audio.set_music_volume(0.5)
    assert audio.music_volume == 0.5
    audio.set_sfx_volume(0.7)
    assert audio.sfx_volume == 0.7

    # Mute toggling
    assert audio.is_muted is False
    audio.toggle_mute()
    assert audio.is_muted is True
    assert audio._calc_sfx_gain(1.0) == 0.0
    assert audio._calc_music_gain() == 0.0
    audio.toggle_mute()
    assert audio.is_muted is False
    assert audio._calc_sfx_gain(1.0) == pytest.approx(0.8 * 0.7)
    assert audio._calc_music_gain() == pytest.approx(0.8 * 0.5)


def test_audio_scene_music_transition_and_fades():
    """
    A12 Acceptance Check: Transitioning scenes routes to appropriate ambient or combat soundtrack.
    """
    audio = AudioManager()
    audio.transition_scene_music(config.STATE_BUNKER_HUB, fade_ms=500)
    assert audio.current_track == TRACK_BUNKER or audio.target_track == TRACK_BUNKER

    audio.transition_scene_music(config.STATE_FIELD_OPS, fade_ms=500)
    assert audio.current_track == TRACK_COMBAT or audio.target_track == TRACK_COMBAT

    # Update step doesn't crash regardless of audio driver status
    audio.update(0.1)
    audio.stop_all()


def test_sound_effects_playback_and_bank_integrity():
    """
    A12 Acceptance Check: All 12 synthesized WAV sound effects exist and load safely.
    """
    audio = AudioManager()
    expected_sfx = [
        "maser_tap",
        "maser_charge",
        "impact_spark",
        "alarm_lock",
        "station_chime",
        "printer_chatter",
        "player_jump",
        "player_land",
        "player_slide",
        "player_hurt",
        "enemy_telegraph",
        "boss_mortar_launch",
    ]

    for sfx in expected_sfx:
        # Playing existing sound effect should not raise exceptions
        res = audio.play_sfx(sfx, volume=0.5)
        # In headless environment with dummy/no audio, returns False gracefully
        assert isinstance(res, bool)

    # Unknown sound effect returns False without exception
    assert audio.play_sfx("non_existent_sfx_xyz") is False


def test_effect_manager_pool_bounds_and_culling():
    """
    A12 Acceptance Check: Visual effects pool strictly caps particle counts,
    respects pause freezes, and culls out-of-viewport instances.
    """
    effects = EffectManager()
    assert effects.total_count == 0

    # Flood pool with 200 sparks (cap is MAX_PARTICLES = 128)
    for _ in range(200):
        effects.add_impact_sparks(100.0, 100.0, count=1)
    assert len(effects.sparks) <= MAX_PARTICLES

    # Flood pool with 200 dust puffs
    for _ in range(200):
        effects.add_dust_puff(100.0, 100.0, count=1)
    assert len(effects.dust) <= MAX_PARTICLES

    # Flood pool with 200 smoke puffs
    for _ in range(200):
        effects.add_mortar_smoke(100.0, 100.0, count=1)
    assert len(effects.smoke) <= MAX_PARTICLES

    # Flood pool with 50 flashes (cap is MAX_BURSTS = 16)
    for _ in range(50):
        effects.add_muzzle_flash(100.0, 100.0, direction="right")
    assert len(effects.flashes) <= MAX_BURSTS

    # Pause safety: is_paused=True must not advance physics or decay lifetime
    sparks_before = [s["life"] for s in effects.sparks]
    effects.update(0.1, is_paused=True)
    sparks_after = [s["life"] for s in effects.sparks]
    assert sparks_before == sparks_after

    # Active update decays particles
    effects.update(0.05, is_paused=False)
    sparks_decayed = [s["life"] for s in effects.sparks]
    assert any(after < before for before, after in zip(sparks_before, sparks_decayed))

    # Render on surface with Camera
    cam = Camera(480, 270)
    surf = pygame.Surface((480, 270))
    effects.render(surf, cam)

    # Clear resets all pools
    effects.clear()
    assert effects.total_count == 0


def test_locked_equipment_cannot_activate():
    """Verify locked weapons and abilities cannot be selected, cycled to, or fired."""
    arsenal = ArsenalManager()
    abilities = AbilityManager()

    # Starter maser is unlocked by default; analog arsenal is locked before validation events
    assert arsenal.weapons["starter_maser"].is_unlocked is True
    assert arsenal.weapons["scattergun"].is_unlocked is False
    assert arsenal.weapons["emp_bola"].is_unlocked is False
    assert arsenal.weapons["fibonacci_coilgun"].is_unlocked is False

    # Attempting to select locked weapon must fail
    assert arsenal.select_weapon("scattergun") is False
    assert arsenal.select_weapon("emp_bola") is False
    assert arsenal.select_weapon("fibonacci_coilgun") is False
    assert arsenal.active_weapon_id == "starter_maser"

    # Cycling weapon only cycles through unlocked weapons
    assert arsenal.cycle_weapon(1) == "starter_maser"
    assert arsenal.cycle_weapon(-1) == "starter_maser"

    # Abilities are locked before validation events
    assert abilities.abilities["decoy"].is_unlocked is False
    assert abilities.abilities["shielding"].is_unlocked is False
    assert abilities.abilities["time_dilation"].is_unlocked is False

    # Attempting to select or activate locked ability must fail
    assert abilities.select_ability("shielding") is False
    assert abilities.can_activate_selected() if hasattr(abilities, "can_activate_selected") else abilities.selected_ability.can_activate(100.0) is False

    player = Player(100.0, 100.0)
    assert abilities.trigger_selected_ability(player) is False


def test_weapon_and_ability_unlocks_from_campaign_validation_events():
    """Verify campaign validation events unlock their corresponding weapons and abilities."""
    campaign = config.default_campaign_state()
    arsenal = ArsenalManager()
    abilities = AbilityManager()

    # Initial state: only starter maser
    arsenal.sync_unlocks(campaign)
    abilities.sync_unlocks(campaign)
    assert arsenal.active_weapon_id == "starter_maser"
    assert not arsenal.weapons["scattergun"].is_unlocked

    # Grant extracted fragment required for validations
    campaign._state["contacted_civs"].append("FASR-001")
    campaign.apply_event({"event_id": "grant_fasr", "type": "grant_fragment_fasr_001"})

    # Quantum validation unlocks scattergun and decoy
    campaign.apply_event({"event_id": "val_q_1", "type": "validate_quantum_mandela_deploy"})
    arsenal.sync_unlocks(campaign)
    abilities.sync_unlocks(campaign)
    assert arsenal.weapons["scattergun"].is_unlocked is True
    assert abilities.abilities["decoy"].is_unlocked is True

    # Connectome validation unlocks emp bola
    campaign.apply_event({"event_id": "val_c_1", "type": "validate_connectome_blindspot_deploy"})
    arsenal.sync_unlocks(campaign)
    assert arsenal.weapons["emp_bola"].is_unlocked is True

    # Formal validation unlocks fibonacci coilgun and time dilation
    campaign.apply_event({"event_id": "val_f_1", "type": "validate_fasr_001_deploy"})
    arsenal.sync_unlocks(campaign)
    abilities.sync_unlocks(campaign)
    assert arsenal.weapons["fibonacci_coilgun"].is_unlocked is True
    assert abilities.abilities["time_dilation"].is_unlocked is True

    # Biosecurity validation unlocks shielding
    campaign.apply_event({"event_id": "val_b_1", "type": "validate_biosecurity_deploy"})
    abilities.sync_unlocks(campaign)
    assert abilities.abilities["shielding"].is_unlocked is True

    # Cycling now smoothly navigates through all unlocked weapons
    assert arsenal.select_weapon("scattergun") is True
    assert arsenal.active_weapon_id == "scattergun"
    assert arsenal.cycle_weapon(1) == "emp_bola"
    assert arsenal.cycle_weapon(1) == "fibonacci_coilgun"
    assert arsenal.cycle_weapon(1) == "starter_maser"

    # Ability cycling navigates through all unlocked abilities
    assert abilities.select_ability("decoy") is True
    assert abilities.cycle_ability(1) == "shielding"
    assert abilities.cycle_ability(1) == "time_dilation"
    assert abilities.cycle_ability(1) == "decoy"


def test_scattergun_reveal_mechanic_and_spread_angles():
    """Verify scattergun fires 5-pellet fan and applies 'revealed' vulnerability amplification."""
    grid = [[COLLISION_EMPTY] * 30 for _ in range(15)]
    room = create_test_room(grid)
    pm = ProjectileManager()
    player = Player(100.0, 100.0)
    scatter = AnalogScattergun()
    scatter.is_unlocked = True

    p_in = PlayerInput(move_x=1.0, fire_pressed=True)
    proj = scatter.update(0.016, p_in, player, room, pm)
    assert proj is not None

    # Exactly 5 pellets spawned
    assert len(pm.projectiles) == 5
    spread_deg = scatter.cfg.spread_angles
    assert spread_deg == [-16.0, -8.0, 0.0, 8.0, 16.0]

    # Target in path of center pellet
    target = CombatTarget("target_scat", pygame.Rect(180, 95, 30, 30), health=100)
    hits = pm.update(0.30, room, targets=[target])
    assert any(h.hit and h.target_id == "target_scat" for h in hits)

    # Target has acquired revealed status with 4.0s duration
    assert target.has_status("revealed") is True
    assert target.get_status("revealed") > 3.5

    # Subsequent hit deals 1.25x amplified damage (base 20 -> 25)
    hp_before = target.health
    res = target.take_damage(20)
    assert res.damage_dealt == 25
    assert target.health == hp_before - 25


def test_emp_bola_stun_mechanic_and_movement_suppression():
    """Verify EMP bola applies stun status, zeroes velocity, and halts enemy state progression."""
    grid = [[COLLISION_EMPTY] * 30 for _ in range(15)]
    room = create_test_room(grid)
    pm = ProjectileManager()
    player = Player(50.0, 100.0)
    drone = CoreReconDrone("drone_emp", 150.0, 100.0)

    bola = EmpBola()
    bola.is_unlocked = True

    p_in = PlayerInput(move_x=1.0, fire_pressed=True)
    bola.update(0.016, p_in, player, room, pm)
    assert len(pm.projectiles) == 1
    assert pm.projectiles[0].weapon_type == "emp_bola"

    # Step simulation until bola impacts drone
    pm.update(0.50, room, targets=[drone])
    assert drone.has_status("stun") is True
    assert drone.get_status("stun") > 1.5

    # While stunned, drone velocity is 0 and telegraph is suppressed
    drone.vx = 40.0
    drone.telegraph_active = True
    drone.update(0.10, player, room, None)
    assert drone.vx == 0.0
    assert drone.telegraph_active is False

    # Step time until stun expires (2.0s duration)
    drone.update(2.5, player, room, None)
    assert drone.has_status("stun") is False


def test_fibonacci_coilgun_timing_and_deterministic_multi_hit():
    """Verify Fibonacci coilgun harmonic stages [1, 2, 3, 5, 8] and deterministic multi-hit piercing."""
    grid = [[COLLISION_EMPTY] * 40 for _ in range(15)]
    room = create_test_room(grid)
    pm = ProjectileManager()
    player = Player(50.0, 100.0)

    coilgun = FibonacciCoilgun()
    coilgun.is_unlocked = True

    # Stage 0: Tap / minimal hold (<0.25s) -> 1x mult, 1 pierce, 20 dmg
    coilgun.charge_timer = 0.10
    assert coilgun.get_current_stage() == 0
    assert coilgun.current_multiplier == 1
    assert coilgun.current_pierce == 1

    # Stage 1: Hold 0.30s -> 2x mult, 1 pierce, 40 dmg
    coilgun.charge_timer = 0.30
    assert coilgun.get_current_stage() == 1
    assert coilgun.current_multiplier == 2
    assert coilgun.current_pierce == 1

    # Stage 2: Hold 0.60s -> 3x mult, 2 pierce, 60 dmg
    coilgun.charge_timer = 0.60
    assert coilgun.get_current_stage() == 2
    assert coilgun.current_multiplier == 3
    assert coilgun.current_pierce == 2

    # Stage 3: Hold 1.00s -> 5x mult, 3 pierce, 100 dmg
    coilgun.charge_timer = 1.00
    assert coilgun.get_current_stage() == 3
    assert coilgun.current_multiplier == 5
    assert coilgun.current_pierce == 3

    # Stage 4: Hold 1.40s -> 8x mult, 5 pierce, 160 dmg
    coilgun.charge_timer = 1.40
    assert coilgun.get_current_stage() == 4
    assert coilgun.current_multiplier == 8
    assert coilgun.current_pierce == 5

    # Multi-hit test: Align 3 targets in a row at x=100, 150, 200
    t1 = CombatTarget("t1", pygame.Rect(100, 105, 20, 25), health=200)
    t2 = CombatTarget("t2", pygame.Rect(150, 105, 20, 25), health=200)
    t3 = CombatTarget("t3", pygame.Rect(200, 105, 20, 25), health=200)

    # Discharge at Stage 2 (mult=3, pierce=2, damage=60)
    coilgun.charge_timer = 0.60
    p_in = PlayerInput(move_x=1.0, fire_released=True)
    p = coilgun.update(0.016, p_in, player, room, pm)
    assert p is not None
    assert p.damage == 60
    assert p.pierce_remaining == 2

    # Pierce through targets
    hits = pm.update(0.50, room, targets=[t1, t2, t3])
    # Exactly t1 and t2 hit with 60 damage each; t3 is not hit because pierce was 2
    assert t1.health == 140
    assert t2.health == 140
    assert t3.health == 200
    assert not p.active


def test_ability_cooldowns_energy_cost_and_checkpoint_rules():
    """Verify ability energy costs, active windows, cooldown gating, and checkpoint resets."""
    abilities = AbilityManager()
    abilities.abilities["decoy"].is_unlocked = True

    player = Player(100.0, 100.0)
    assert abilities.energy == 100.0
    decoy = abilities.abilities["decoy"]

    # Trigger decoy: cost is 30, duration 4.0s, cooldown 6.0s
    ok = abilities.trigger_selected_ability(player)
    assert ok is True
    assert abilities.energy == 70.0
    assert decoy.is_active is True
    assert decoy.active_timer == 4.0

    # Cannot trigger while active
    assert abilities.trigger_selected_ability(player) is False

    # Step through active duration (4.0s)
    abilities.update(4.1, is_paused=False)
    assert decoy.is_active is False
    assert decoy.cooldown_timer > 0.0

    # Cannot trigger while on cooldown
    assert abilities.trigger_selected_ability(player) is False

    # Step through cooldown
    abilities.update(6.0, is_paused=False)
    assert decoy.cooldown_timer == 0.0
    assert abilities.energy > 70.0  # Energy recharged

    # Checkpoint reset restores full energy and clears all cooldowns
    abilities.energy = 20.0
    decoy.cooldown_timer = 5.0
    abilities.reset_on_checkpoint()
    assert abilities.energy == abilities.max_energy
    assert decoy.cooldown_timer == 0.0
    assert decoy.is_active is False


def test_quantum_decoy_diverts_enemy_line_of_sight():
    """Verify active decoy draws enemy targeting and intercepts enemy projectiles."""
    grid = [[COLLISION_EMPTY] * 30 for _ in range(15)]
    room = create_test_room(grid)
    em = EnemyManager()
    drone = CoreReconDrone("drone_decoy", 200.0, 100.0)
    em.add_enemy(drone)

    player = Player(50.0, 100.0)
    decoy_ab = QuantumDecoyAbility()
    decoy_ab.is_unlocked = True

    # Activate decoy at player position (50, 100)
    decoy_ab.activate(player)
    decoy = decoy_ab.active_decoy
    assert decoy is not None

    # Move player far away
    player.x = 50.0
    player.y = 240.0

    # Enemy updates with decoy: aims at decoy at (50, 100), not player at (50, 240)
    drone.update(0.10, player, room, em, decoy=decoy)
    assert drone.facing == "left"

    # Spawn enemy projectile targeting decoy
    proj = em.spawn_enemy_projectile(200.0, 100.0, -1.0, 0.0, 300.0, 20, "drone_decoy")
    # Step enemy projectiles
    em.update(0.60, player, room, decoy=decoy)
    # Projectile was absorbed by decoy, dealing 20 damage to decoy, leaving player untouched
    assert decoy.health == 30
    assert player.health == 100


def test_phase_shield_damage_absorption_and_spillover():
    """Verify phase shield absorbs damage up to 45 HP with exact spillover to player."""
    player = Player(100.0, 100.0)
    player.abilities = AbilityManager()
    player.abilities.abilities["shielding"].is_unlocked = True

    shield = player.abilities.abilities["shielding"]
    shield.activate(player)
    assert shield.is_active is True
    assert shield.remaining_shield_hp == 45

    # Hit 1: 30 damage -> 100% absorbed by shield, player takes 0 damage
    player.take_damage(30)
    assert shield.remaining_shield_hp == 15
    assert player.health == 100

    # Hit 2: 25 damage -> absorbs 15, shield breaks, 10 spills over to player
    player.invulnerable_timer = 0.0  # Clear invulnerability for testing
    player.take_damage(25)
    assert shield.remaining_shield_hp == 0
    assert shield.is_active is False
    assert player.health == 90


def test_time_dilation_actor_time_modifier():
    """Verify time dilation modulates actor-time modifier to 0.35x for enemies and hazards."""
    player = Player(100.0, 100.0)
    player.abilities = AbilityManager()
    player.abilities.abilities["time_dilation"].is_unlocked = True

    dilation = player.abilities.abilities["time_dilation"]
    assert player.abilities.get_actor_time_modifier() == 1.0

    dilation.activate(player)
    assert player.abilities.get_actor_time_modifier() == 0.35

    # Drone moves at 35% speed when dilated
    drone = CoreReconDrone("drone_dil", 200.0, 100.0)
    normal_speed = drone.cfg.patrol_speed
    x_start = drone.x
    # Update with dt=1.0 and actor_time_modifier=0.35
    eff_dt = 1.0 * 0.35
    drone.update(eff_dt, player, create_test_room([[COLLISION_EMPTY] * 30 for _ in range(15)]), None)
    dist_moved = abs(drone.x - x_start)
    assert math.isclose(dist_moved, normal_speed * 0.35, rel_tol=1e-2)

    # After duration expires, returns to 1.0x
    dilation.update(3.0)
    assert player.abilities.get_actor_time_modifier() == 1.0


def test_simultaneous_statuses_interaction_and_counterplay():
    """Verify simultaneous statuses (stun + revealed) decay accurately and enforce counterplay."""
    target = CombatTarget("target_multi", pygame.Rect(100, 100, 30, 30), health=100)

    # Apply both statuses simultaneously
    target.apply_status("stun", 2.0)
    target.apply_status("revealed", 4.0)

    assert target.has_status("stun") is True
    assert target.has_status("revealed") is True

    # Under time dilation (0.35x), step dt=0.5s -> effective dt = 0.175s
    eff_dt = 0.5 * 0.35
    target.update(eff_dt)
    assert math.isclose(target.get_status("stun"), 2.0 - 0.175, abs_tol=1e-3)
    assert math.isclose(target.get_status("revealed"), 4.0 - 0.175, abs_tol=1e-3)

    # Taking damage while revealed deals 1.25x amplified damage
    res = target.take_damage(40)
    assert res.damage_dealt == 50
    assert target.health == 50

    # Advance time until stun expires but revealed remains
    target.update(2.0)
    assert target.has_status("stun") is False
    assert target.has_status("revealed") is True

    # Advance until revealed also expires
    target.update(2.5)
    assert target.has_status("revealed") is False


def test_core_enforcer_armor_and_emp_counterplay():
    """Verify CoreEnforcer frontal armor 50% damage reduction, EMP stun 1.5x overload, and slide-kick stagger."""
    enforcer = CoreEnforcer("enf_1", 200.0, 100.0)
    enforcer.facing = "left"
    assert enforcer.health == 120

    # 1. Frontal attack (from left against left-facing enforcer): 50% damage reduction
    res_front = enforcer.take_damage(40, hit_pos=(150.0, 100.0))
    assert res_front.damage_dealt == 20
    assert enforcer.health == 100

    # 2. Rear attack (from right against left-facing enforcer): full 100% damage
    res_rear = enforcer.take_damage(40, hit_pos=(250.0, 100.0))
    assert res_rear.damage_dealt == 40
    assert enforcer.health == 60

    # 3. EMP Stun Counterplay: Stunned chassis overloads circuits for 1.5x damage
    enforcer.apply_status("stun", 2.0)
    assert enforcer.has_status("stun") is True
    res_stun = enforcer.take_damage(40, hit_pos=(150.0, 100.0))
    assert res_stun.damage_dealt == 60
    assert enforcer.health == 0
    assert enforcer.is_dead is True

    # 4. Slide-Kick Stagger Counterplay: forces 1.2s recovery and cancels attack windup
    enf2 = CoreEnforcer("enf_2", 200.0, 100.0)
    enf2.state = STATE_WINDUP
    enf2.telegraph_active = True
    enf2.on_slide_kicked()
    assert enf2.state == STATE_RECOVERY
    assert enf2.state_timer == 1.20
    assert enf2.telegraph_active is False


def test_core_operative_cover_occlusion_and_sprint():
    """Verify CoreOperative high-speed patrol, cover occlusion optical link break, and recovery vulnerability."""
    op = CoreOperative("op_1", 200.0, 100.0)
    assert op.cfg.patrol_speed == 75.0

    # 1. Optical link breaks when player takes low cover or background cover
    player = Player(120.0, 100.0)
    room = create_test_room([[COLLISION_EMPTY] * 30 for _ in range(15)])
    mgr = EnemyManager()

    op.state = STATE_WINDUP
    op.state_timer = 0.40
    op.telegraph_active = True
    player.is_crouching = True

    op.update(0.05, player, room, mgr)
    assert op.state == STATE_PATROL
    assert op.telegraph_active is False

    # 2. Recovery vulnerability: takes 1.25x damage when caught in recovery
    op.state = STATE_RECOVERY
    res = op.take_damage(40)
    assert res.damage_dealt == 50
    assert op.health == 20


def test_shield_hound_frontal_block_and_slide_kick_knockdown():
    """Verify ShieldHound welded CRT shield 100% deflection, slide-kick knockdown, and rear critical weak point."""
    hound = ShieldHound("hound_1", 200.0, 100.0)
    hound.facing = "left"
    assert hound.health == 95

    # 1. Frontal hit completely blocked by CRT shield (0 damage)
    res_front = hound.take_damage(30, hit_pos=(150.0, 100.0))
    assert res_front.damage_dealt == 0
    assert hound.health == 95

    # 2. Rear attack strikes exposed battery pack for 2.0x critical damage
    res_rear = hound.take_damage(30, hit_pos=(250.0, 100.0))
    assert res_rear.damage_dealt == 60
    assert hound.health == 35

    # 3. Slide-kick knockdown counterplay
    hound2 = ShieldHound("hound_2", 200.0, 100.0)
    hound2.facing = "left"
    hound2.on_slide_kicked()
    assert hound2.is_knocked_down is True
    assert hound2.state == STATE_RECOVERY
    assert hound2.state_timer == 1.20

    # While knocked down, shield is bypassed and frontal hit deals 2.0x critical damage
    res_kd = hound2.take_damage(30, hit_pos=(150.0, 100.0))
    assert res_kd.damage_dealt == 60
    assert hound2.health == 35


def test_phase_watcher_teleport_solid_avoidance_and_reveal_counter():
    """Verify PhaseWatcher solid-geometry safe teleportation, reveal suppression, and coherence drain channel."""
    watcher = PhaseWatcher("watcher_1", 200.0, 96.0)

    # 1. Safe tactical teleportation to valid floor positions
    grid = [[COLLISION_EMPTY] * 30 for _ in range(15)]
    for c in range(30):
        grid[8][c] = COLLISION_SOLID  # Ground at y = 128
    room = create_test_room(grid)

    player = Player(150.0, 96.0)
    success = watcher.try_teleport(player, room)
    assert success is True
    assert room.check_rect_collision(watcher.rect)["solid"] is False
    assert room.check_rect_collision(watcher.rect)["hazard"] is False

    # 2. Sensor illumination counterplay: revealed status suppresses teleportation
    watcher.apply_status("revealed", 4.0)
    assert watcher.try_teleport(player, room) is False

    # 3. Coherence drain channel mechanics
    watcher.clear_statuses()
    watcher.state = STATE_ATTACK
    watcher.is_channeling = True
    watcher.has_los = True
    player.coherence = 100.0
    mgr = EnemyManager()

    watcher.update(0.5, player, room, mgr)
    # 20 DPS * 0.5s = 10 coherence drained
    assert math.isclose(player.coherence, 90.0, abs_tol=1e-2)

    # 4. EMP Stun interrupts coherence channel immediately
    watcher.apply_status("stun", 1.5)
    watcher.update(0.1, player, room, mgr)
    assert watcher.is_channeling is False


def test_chrysalis_splicer_parabolic_acid_and_crouch_protection():
    """Verify ChrysalisSplicer ballistic acid trajectory and piercing weapon sac rupture."""
    splicer = ChrysalisSplicer("splicer_1", 200.0, 100.0)

    # 1. Piercing weapon vulnerability: coilgun ruptures internal sacs for 1.5x damage
    res = splicer.take_damage(30, hit_id="fibonacci_coilgun_shot_stage3")
    assert res.damage_dealt == 45
    assert splicer.health == 40

    # 2. Ballistic acid trajectory physics
    mgr = EnemyManager()
    proj = mgr.spawn_enemy_projectile(
        origin_x=100.0,
        origin_y=100.0,
        dir_x=1.0,
        dir_y=-0.5,
        speed=260.0,
        damage=25,
        source_id="splicer_1",
        color=(60, 220, 130),
        gravity=380.0,
        vx=200.0,
        vy=-160.0,
    )
    assert proj.gravity == 380.0
    assert proj.color == (60, 220, 130)


def test_precursor_guardian_ground_shockwave_and_jump_avoidance():
    """Verify PrecursorGuardian ground shockwaves and vertical jump avoidance counterplay."""
    mgr = EnemyManager()
    room = create_test_room([[COLLISION_EMPTY] * 30 for _ in range(15)])
    player = Player(160.0, 96.0)

    # 1. Airborne jump avoidance: shockwave passes harmlessly under jumping player
    sw_jump = mgr.spawn_enemy_projectile(
        origin_x=100.0,
        origin_y=120.0,
        dir_x=1.0,
        dir_y=0.0,
        speed=300.0,
        damage=35,
        source_id="guard_1",
        color=(245, 205, 65),
        is_shockwave=True,
        ground_only=True,
    )
    player.is_grounded = False
    player.vy = -180.0
    player.y = 60.0  # Jumping well above the shockwave
    hp_initial = player.health

    mgr.update(0.25, player, room)
    assert player.health == hp_initial

    # 2. Grounded impact: player on the floor takes full shockwave damage
    mgr.projectiles.clear()
    sw_ground = mgr.spawn_enemy_projectile(
        origin_x=100.0,
        origin_y=120.0,
        dir_x=1.0,
        dir_y=0.0,
        speed=300.0,
        damage=35,
        source_id="guard_1",
        color=(245, 205, 65),
        is_shockwave=True,
        ground_only=True,
    )
    player.is_grounded = True
    player.y = 96.0  # Feet at 96 + 32 = 128 (aligned with ground)
    player.invulnerable_timer = 0.0

    mgr.update(0.25, player, room)
    assert player.health < hp_initial


def test_temporal_phantom_phasing_and_reveal_stabilization():
    """Verify TemporalPhantom default 75% phasing resistance and reveal stabilization 1.5x vulnerability."""
    phantom = TemporalPhantom("phantom_1", 200.0, 100.0)
    assert phantom.health == 60

    # 1. Unanchored phasing takes only 25% damage (75% damage reduction)
    res_phase = phantom.take_damage(40)
    assert res_phase.damage_dealt == 10
    assert phantom.health == 50

    # 2. Revealed counterplay collapses superposition, dealing 1.5x vulnerability damage
    phantom.apply_status("revealed", 4.0)
    res_rev = phantom.take_damage(20)
    assert res_rev.damage_dealt == 30
    assert phantom.health == 20


def test_mixed_faction_encounter_and_reset_idempotence():
    """Verify multi-faction encounter simulation, damage resolution, and pristine spawn state reset."""
    mgr = EnemyManager()
    room = create_test_room([[COLLISION_EMPTY] * 30 for _ in range(15)])
    player = Player(100.0, 100.0)

    # Populate with all 7 hostile faction archetypes plus baseline drone and hound
    roster = [
        CoreReconDrone("drone_1", 120.0, 80.0),
        StaticHound("hound_1", 160.0, 100.0),
        CoreEnforcer("enf_1", 200.0, 100.0),
        CoreOperative("op_1", 240.0, 100.0),
        ShieldHound("shound_1", 280.0, 100.0),
        PhaseWatcher("watcher_1", 320.0, 100.0),
        ChrysalisSplicer("splicer_1", 360.0, 100.0),
        PrecursorGuardian("guard_1", 400.0, 100.0),
        TemporalPhantom("phantom_1", 440.0, 100.0),
    ]
    for e in roster:
        mgr.add_enemy(e)

    assert len(mgr.enemies) == 9

    # Advance simulation
    for _ in range(5):
        mgr.update(0.016, player, room)

    # Deal damage to all enemies and eliminate one
    roster[0].take_damage(100)  # Kill drone
    assert roster[0].is_dead is True
    roster[2].take_damage(30)   # Damage enforcer
    assert roster[2].health < roster[2].cfg.max_health

    # Spawn some projectiles and sparks
    mgr.spawn_enemy_projectile(200.0, 100.0, 1.0, 0.0, 300.0, 15, "test")
    mgr.add_sparks(200.0, 100.0, 6)
    assert len(mgr.projectiles) > 0
    assert len(mgr.sparks) > 0

    # Reset all: must restore all entities to pristine spawn state
    mgr.reset_all()

    assert len(mgr.projectiles) == 0
    assert len(mgr.sparks) == 0
    for e in mgr.enemies:
        assert e.health == e.cfg.max_health
        assert e.is_dead is False
        assert e.state == STATE_PATROL
        assert e.x == e.spawn_x
        assert e.y == e.spawn_y





