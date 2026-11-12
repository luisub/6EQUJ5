"""
MODULE: video_game/tests/test_player.py
PURPOSE: Comprehensive unit and integration tests for fixed-step player locomotion,
         framerate invariance (30/60/120 FPS), collision geometry, tunneling prevention,
         coyote time, jump buffer, and checkpoint recovery.
CALLED BY: pytest video_game/tests/test_player.py.
HOW TO MODIFY: Add edge case scenarios, new movement mechanics, or weapon kinematic tests.
"""

import math
from pathlib import Path
import pygame
import pytest

from video_game.engine.abilities import AbilityManager, SerendipityTapeDeckAbility
from video_game.engine.enemies import CoreEnforcer, CoreReconDrone, StaticHound
from video_game.engine.player import Player, PlayerConfig, PlayerInput
from video_game.engine.weapons import CombatTarget
from video_game.engine.world import (
    COLLISION_COVER,
    COLLISION_EMPTY,
    COLLISION_HAZARD,
    COLLISION_ONE_WAY,
    COLLISION_SOLID,
    Room,
    RoomCheckpoint,
    SpawnPoint,
)


def create_test_room(grid, spawns=None, checkpoints=None, objects=None, tile_size=16):
    """Helper to construct an in-memory Room with custom collision grids."""
    h_tiles = len(grid)
    w_tiles = len(grid[0]) if h_tiles > 0 else 0
    sp_data = {}
    if spawns:
        for name, (x, y) in spawns.items():
            sp_data[name] = {"x": float(x), "y": float(y), "facing": "right"}
    else:
        sp_data["bunker_exit"] = {"x": 32.0, "y": 32.0, "facing": "right"}

    chk_data = []
    if checkpoints:
        for cid, (x, y) in checkpoints.items():
            chk_data.append({"id": cid, "x": float(x), "y": float(y), "name": cid})

    data = {
        "schema_version": 1,
        "room_id": "test_room",
        "act_id": "test_act",
        "title": "Test Room",
        "tile_size": tile_size,
        "width_tiles": w_tiles,
        "height_tiles": h_tiles,
        "collision_layers": grid,
        "background_layers": [],
        "spawns": sp_data,
        "checkpoints": chk_data,
        "exits": [],
        "objects": objects or [],
    }
    return Room(data)


def test_balance_config_loading():
    """Verify balance configuration loads defaults and overrides from balance.json."""
    cfg = PlayerConfig.load_from_file()
    assert cfg.walk_speed > 100.0
    assert cfg.jump_velocity < -200.0
    assert cfg.gravity > 400.0
    assert cfg.jump_buffer_time > 0.05
    assert cfg.coyote_time > 0.05
    assert cfg.fixed_dt == pytest.approx(1.0 / 120.0, abs=1e-5)
    assert cfg.max_accumulator <= 0.20


def test_framerate_invariance_at_30_60_120_fps():
    """
    Acceptance Check: Equivalent inputs at 30, 60, and 120 render FPS produce
    matching movement within documented tolerance (<= 0.5 px).
    """
    # 50 tiles wide flat solid floor at row 5 (y=80)
    grid = [[COLLISION_EMPTY] * 50 for _ in range(5)]
    grid.append([COLLISION_SOLID] * 50)
    room = create_test_room(grid)

    cfg = PlayerConfig.load_from_file()
    total_time = 1.0  # 1 second of simulation
    fps_targets = [30, 60, 120]
    final_positions = {}

    for fps in fps_targets:
        player = Player(32.0, 48.0, cfg)
        player.is_grounded = True
        dt_frame = 1.0 / fps
        num_frames = int(round(total_time * fps))

        p_input = PlayerInput(move_x=1.0)
        for _ in range(num_frames):
            player.update(dt_frame, p_input, room)

        final_positions[fps] = (player.x, player.vx)

    pos_30 = final_positions[30][0]
    pos_60 = final_positions[60][0]
    pos_120 = final_positions[120][0]

    # Verify matching movement across 30, 60, and 120 FPS within 0.5 pixel tolerance
    assert abs(pos_60 - pos_120) < 0.5, f"60 FPS ({pos_60}) vs 120 FPS ({pos_120}) mismatch"
    assert abs(pos_30 - pos_120) < 0.5, f"30 FPS ({pos_30}) vs 120 FPS ({pos_120}) mismatch"
    assert abs(final_positions[60][1] - final_positions[120][1]) < 0.1, "Final velocity mismatch"


def test_jump_arc_framerate_invariance():
    """Verify jump height and landing timing match across 30, 60, and 120 FPS."""
    grid = [[COLLISION_EMPTY] * 30 for _ in range(8)]
    grid.append([COLLISION_SOLID] * 30)
    room = create_test_room(grid)

    cfg = PlayerConfig.load_from_file()
    peak_heights = {}

    for fps in [30, 60, 120]:
        player = Player(48.0, 96.0, cfg)  # Resting on row 8 (y=128 - 32 = 96)
        player.is_grounded = True
        dt_frame = 1.0 / fps
        min_y = 96.0

        for f in range(int(fps * 0.8)):  # 0.8s jump arc
            p_input = PlayerInput(jump_pressed=(f == 0), jump_held=True)
            player.update(dt_frame, p_input, room)
            if player.y < min_y:
                min_y = player.y

        peak_heights[fps] = min_y

    # Check jump peak is within 1 pixel tolerance across all render framerates
    assert abs(peak_heights[60] - peak_heights[120]) < 1.0
    assert abs(peak_heights[30] - peak_heights[120]) < 1.0


def test_corners_and_ceilings_prevent_trapping():
    """
    Acceptance Check: Corners and ceilings cannot trap or clip the player.
    Player jumping into an inside corner can cleanly back out.
    """
    # Room with ceiling at row 1, solid floor at row 8, solid wall on right at col 10
    grid = [[COLLISION_SOLID] * 15]  # Ceiling at row 0 (y=0..16)
    for _ in range(7):
        grid.append([COLLISION_EMPTY] * 10 + [COLLISION_SOLID] * 5)
    grid.append([COLLISION_SOLID] * 15)  # Floor at row 8 (y=128)

    room = create_test_room(grid)
    player = Player(120.0, 96.0)  # Near wall col 10 (x=160)
    player.is_grounded = True

    # Jump up and right into the ceiling-wall inside corner
    for _ in range(30):
        p_input = PlayerInput(move_x=1.0, jump_pressed=True, jump_held=True)
        player.update(1.0 / 60.0, p_input, room)

    # Verify player did not clip into ceiling (y must be >= 16) or wall (x + width <= 160)
    assert player.y >= 16.0, f"Player clipped into ceiling: y={player.y}"
    assert player.x + player.width <= 160.0 + 0.01, f"Player clipped into wall: x={player.x}"

    # Verify player is not trapped: move left away from corner
    for _ in range(20):
        p_input = PlayerInput(move_x=-1.0)
        player.update(1.0 / 60.0, p_input, room)

    assert player.x < 130.0, "Player got trapped in corner and could not move away"


def test_ceiling_bonk_immediately_cancels_upward_velocity():
    """Verify hitting a ceiling zeroes vertical velocity and causes clean downward drop."""
    grid = [
        [COLLISION_SOLID] * 10,  # Ceiling at row 0 (y=0..16)
        [COLLISION_EMPTY] * 10,
        [COLLISION_EMPTY] * 10,
        [COLLISION_EMPTY] * 10,
        [COLLISION_SOLID] * 10,  # Floor at row 4 (y=64)
    ]
    room = create_test_room(grid)
    player = Player(32.0, 20.0)  # 4px below ceiling at y=16
    player.is_grounded = True

    p_input = PlayerInput(jump_pressed=True, jump_held=True)
    player.update(1.0 / 60.0, p_input, room)

    # Frame hitting ceiling snaps y to 16.0 and cancels upward velocity
    assert player.y >= 16.0
    assert player.vy >= 0.0, "Ceiling bonk did not cancel upward velocity"

    # Subsequent frame gravity pulls downward
    player.update(1.0 / 60.0, PlayerInput(), room)
    assert player.vy > 0.0, "Gravity did not pull player downward after ceiling bonk"


def test_one_way_platforms_traversal_and_edges():
    """
    Acceptance Check: One-way platforms allow upward passage, land when falling from above,
    and cleanly depart from edges.
    """
    # Grid: floor at row 6, one-way platform at row 3 (col 2..6)
    grid = [[COLLISION_EMPTY] * 10 for _ in range(3)]
    grid.append([COLLISION_EMPTY, COLLISION_EMPTY] + [COLLISION_ONE_WAY] * 5 + [COLLISION_EMPTY] * 3)  # row 3: y=48
    grid.append([COLLISION_EMPTY] * 10)
    grid.append([COLLISION_EMPTY] * 10)
    grid.append([COLLISION_SOLID] * 10)  # row 6: y=96

    room = create_test_room(grid)
    cfg = PlayerConfig.load_from_file()

    # 1. Jump up from below through the one-way platform
    player = Player(48.0, 64.0, cfg)  # Below platform (row 3 is at y=48)
    player.is_grounded = True
    p_input = PlayerInput(jump_pressed=True, jump_held=True)

    for _ in range(15):
        player.update(1.0 / 60.0, p_input, room)
        # Should jump up above the platform (y < 48 - 32 = 16)
        if player.y < 20.0:
            break

    assert player.y < 30.0, "Player was blocked from jumping through one-way platform from below"

    # 2. Allow falling back down onto the one-way platform
    idle_input = PlayerInput()
    for _ in range(30):
        player.update(1.0 / 60.0, idle_input, room)
        if player.is_grounded:
            break

    assert player.is_grounded is True
    # Platform top is at 48; player height is 32 -> y should land at 16.0
    assert player.y == pytest.approx(16.0, abs=0.5)

    # 3. Walk off the edge of the one-way platform (cols 2..6 = x 32..112)
    right_input = PlayerInput(move_x=1.0)
    for _ in range(40):
        player.update(1.0 / 60.0, right_input, room)
        if not player.is_grounded and player.x > 112.0:
            break

    assert player.x > 112.0
    assert player.is_grounded is False, "Player did not fall when walking off one-way platform edge"


def test_fast_fall_does_not_tunnel_through_thin_floors():
    """
    Acceptance Check: Fast falls cannot tunnel through 16px solid geometry.
    """
    # 10 rows of empty space with a 1-tile thick solid floor at row 10 (y=160..176)
    grid = [[COLLISION_EMPTY] * 10 for _ in range(10)]
    grid.append([COLLISION_SOLID] * 10)  # Row 10: y=160
    grid.append([COLLISION_EMPTY] * 10)  # Row 11: empty beneath!
    grid.append([COLLISION_EMPTY] * 10)

    room = create_test_room(grid)
    cfg = PlayerConfig.load_from_file()
    player = Player(32.0, 0.0, cfg)
    player.vy = cfg.max_fall_speed  # Max fall velocity (360 px/s)

    # Simulate free fall
    landed = False
    for _ in range(60):
        player.update(1.0 / 60.0, PlayerInput(), room)
        if player.is_grounded:
            landed = True
            break

    assert landed is True, "Fast-falling player tunneled through solid floor"
    assert player.y == pytest.approx(160.0 - 32.0, abs=0.1)


def test_coyote_time_allows_grace_period_jump():
    """Verify coyote time allows jumping within the configured window after leaving a ledge."""
    # Floor ends at col 3 (x=48)
    grid = [[COLLISION_EMPTY] * 10 for _ in range(4)]
    grid.append([COLLISION_SOLID] * 3 + [COLLISION_EMPTY] * 7)  # Floor at row 4 (y=64)
    room = create_test_room(grid)
    cfg = PlayerConfig.load_from_file()

    player = Player(32.0, 32.0, cfg)  # On solid floor
    player.is_grounded = True

    # Walk right off the ledge
    walk_right = PlayerInput(move_x=1.0)
    for _ in range(15):
        player.update(1.0 / 60.0, walk_right, room)
        if not player.is_grounded:
            break

    assert player.is_grounded is False
    assert player.coyote_timer > 0.0, "Coyote timer was not primed when walking off ledge"

    # Press jump during coyote time
    jump_input = PlayerInput(jump_pressed=True, jump_held=True)
    player.update(1.0 / 60.0, jump_input, room)

    assert player.vy < -100.0, "Coyote jump was not executed while in coyote grace period"


def test_jump_buffering_triggers_on_landing():
    """Verify jump buffer executes jump immediately upon touching ground."""
    grid = [[COLLISION_EMPTY] * 10 for _ in range(5)]
    grid.append([COLLISION_SOLID] * 10)  # Floor at row 5 (y=80)
    room = create_test_room(grid)
    cfg = PlayerConfig.load_from_file()

    # Player falling 4px above ground (floor top is 80; player bottom at 76 -> y = 44)
    player = Player(32.0, 44.0, cfg)
    player.vy = 100.0
    player.is_grounded = False

    # Press jump in air 0.05s before landing (buffered within jump_buffer_time = 0.12s)
    jump_input = PlayerInput(jump_pressed=True, jump_held=True)
    player.update(1.0 / 60.0, jump_input, room)

    # Step through landing within buffer window
    idle_input = PlayerInput(jump_held=True)
    for _ in range(5):
        player.update(1.0 / 60.0, idle_input, room)
        if player.vy < -200.0:
            break

    # Player landed and immediately triggered buffered jump
    assert player.vy < -200.0, "Jump buffer did not trigger jump upon landing"


def test_death_and_checkpoint_recovery():
    """
    Acceptance Check: Death returns to a valid checkpoint with coherent state.
    """
    # Room with floor, hazard pit in middle, and checkpoint at col 6
    grid = [
        [COLLISION_EMPTY] * 12,
        [COLLISION_EMPTY] * 12,
        [COLLISION_EMPTY] * 12,
        [COLLISION_EMPTY] * 12,
        [COLLISION_SOLID] * 3 + [COLLISION_HAZARD] * 2 + [COLLISION_SOLID] * 7,  # row 4: y=64
    ]
    spawns = {"bunker_exit": (16.0, 32.0)}
    checkpoints = {"chk_mid": (96.0, 32.0)}
    room = create_test_room(grid, spawns=spawns, checkpoints=checkpoints)

    player = Player(16.0, 32.0)
    assert player.health == 100
    assert player.is_dead is False

    # 1. Take hazard damage
    player.x = 48.0  # Over col 3 (hazard)
    player.y = 32.0
    player.update(1.0 / 60.0, PlayerInput(), room)

    assert player.health < 100
    assert player.invulnerable_timer > 0.0
    assert player.knockback_active is True

    # 2. Trigger fatal damage
    player.take_damage(amount=200)
    assert player.health == 0
    assert player.is_dead is True

    # 3. Update should trigger respawn at bunker_exit with coherent state
    player.update(1.0 / 60.0, PlayerInput(), room)
    assert player.is_dead is False
    assert player.health == 100
    assert player.x == 16.0
    assert player.y == 32.0
    assert player.vx == 0.0
    assert player.vy == 0.0

    # 4. Activate checkpoint and test death respawn at new checkpoint
    player.x = 96.0  # At chk_mid
    player.y = 32.0
    player.update(1.0 / 60.0, PlayerInput(), room)
    assert player.active_checkpoint_id == "chk_mid"

    # Fatal drop out of world
    player.y = 200.0  # Below room height (80px)
    player.update(1.0 / 60.0, PlayerInput(), room)

    assert player.is_dead is False
    assert player.health == 100
    assert player.x == 96.0
    assert player.y == 32.0


def test_simulation_backlog_clamping_after_stall():
    """Verify simulation accumulator does not spiral out of control during massive stalls."""
    grid = [[COLLISION_SOLID] * 10]
    room = create_test_room(grid)
    cfg = PlayerConfig.load_from_file()
    player = Player(32.0, 32.0, cfg)

    # Massive 2.0 second stall
    player.update(2.0, PlayerInput(), room)

    # Accumulator must be clamped to max_accumulator (0.10s) and remaining steps consumed
    assert player.accumulator < cfg.fixed_dt, "Accumulator retained unbounded backlog"


def test_cover_protection_matches_attack_direction_and_type():
    """
    Acceptance Check: Protection matches attack direction and cover type.
    - Low cover protects when crouching against attacks from its direction.
    - Background doorway cover protects against horizontal attacks when concealed.
    - Cannot fire weapon while fully concealed in doorway cover.
    """
    grid = [[COLLISION_EMPTY] * 20 for _ in range(4)]
    grid.append([COLLISION_SOLID] * 20)

    objects = [
        {
            "id": "sandbag_wall",
            "type": "cover",
            "x": 64.0,
            "y": 48.0,
            "width": 16.0,
            "height": 16.0,
            "properties": {
                "cover_type": "low",
                "protection_directions": ["right"],
            },
        },
        {
            "id": "doorway_alcove",
            "type": "cover",
            "x": 160.0,
            "y": 16.0,
            "width": 32.0,
            "height": 48.0,
            "properties": {
                "cover_type": "background",
                "protection_directions": ["left", "right"],
            },
        },
    ]
    room = create_test_room(grid, objects=objects)

    # 1. Low cover test at sandbags (x=64)
    player = Player(48.0, 32.0)
    player.is_grounded = True

    # Standing: low cover provides NO protection
    assert player.check_protection("right", room) is False

    # Crouching: low cover blocks frontal attacks from the right
    player.is_crouching = True
    assert player.check_protection("right", room) is True
    # Flank attack from behind (left) is NOT blocked
    assert player.check_protection("left", room) is False
    # Attack from above is NOT blocked
    assert player.check_protection("above", room) is False

    # 2. Background doorway cover test at alcove (x=160)
    player.x = 160.0
    player.y = 32.0
    player.is_crouching = False
    player.in_cover = False

    # Not concealed: no protection
    assert player.check_protection("right", room) is False
    assert player.can_fire(room) is True

    # Conceal in background cover
    player.in_cover = True
    player.cover_type = "background"
    assert player.check_protection("right", room) is True
    assert player.check_protection("left", room) is True
    assert player.check_protection("above", room) is False

    # Forbidden geometry: cannot fire weapon while concealed in doorway recess
    assert player.can_fire(room) is False
    assert player.animation_state == "cover_background"


def test_standing_under_low_ceilings_rejected_safely():
    """
    Acceptance Check: Standing under low ceilings is rejected safely.
    Crouching and sliding under a 16px crawlspace prevents uncrouching.
    """
    # Ceiling at row 2 (y=32..48), crawlspace at row 3 (gap 16px), floor at row 4 (y=64)
    # Cols 5..10 have ceiling overhead. Cols 0..4 have open headroom.
    grid = [
        [COLLISION_EMPTY] * 15,
        [COLLISION_EMPTY] * 15,
        [COLLISION_EMPTY] * 5 + [COLLISION_SOLID] * 6 + [COLLISION_EMPTY] * 4,
        [COLLISION_EMPTY] * 15,
        [COLLISION_SOLID] * 15,
    ]
    room = create_test_room(grid)

    player = Player(16.0, 32.0)  # At col 1 (open headroom)
    player.is_grounded = True

    # Open area: can stand freely
    assert player.can_stand(room) is True

    # Enter crawlspace while crouching
    player.x = 96.0  # Under ceiling at col 6
    player.y = 32.0
    player.is_crouching = True

    # Headroom check under 16px crawlspace
    assert player.can_stand(room) is False

    # Attempt to stand up by releasing crouch key
    p_input = PlayerInput(crouch_held=False)
    player.update(1.0 / 60.0, p_input, room)

    # Must safely reject standing and remain crouched
    assert player.is_crouching is True, "Player was allowed to stand up into solid ceiling"
    assert player.rect.height == 20
    assert player.rect.top == 44  # y(32) + 12 = 44, bottom is 64

    # Crawl out of crawlspace to col 2 (open area)
    player.x = 32.0
    assert player.can_stand(room) is True

    # Now releasing crouch successfully returns to standing
    player.update(1.0 / 60.0, PlayerInput(crouch_held=False), room)
    assert player.is_crouching is False
    assert player.rect.height == 32


def test_sliding_wall_stop_and_slide_kick_target_tracking():
    """
    Acceptance Check: Sliding cannot cross solid walls or repeatedly damage one target per slide.
    """
    grid = [
        [COLLISION_EMPTY] * 15,
        [COLLISION_EMPTY] * 15,
        [COLLISION_EMPTY] * 10 + [COLLISION_SOLID] * 5,
        [COLLISION_EMPTY] * 10 + [COLLISION_SOLID] * 5,
        [COLLISION_SOLID] * 15,
    ]
    room = create_test_room(grid)

    player = Player(32.0, 32.0)
    player.is_grounded = True
    player.vx = 100.0

    # 1. Initiate slide
    slide_input = PlayerInput(slide_pressed=True, move_x=1.0)
    player.update(1.0 / 60.0, slide_input, room)

    assert player.is_sliding is True
    assert player.vx == player.cfg.slide_speed
    assert player.animation_state == "slide"
    assert player.slide_kick_rect is not None

    # 2. Slide kick target damage tracking
    # Hit dummy 1
    new_hp, damaged = player.apply_slide_kick("target_drone_01", 100)
    assert damaged is True
    assert new_hp == 100 - player.cfg.slide_kick_damage  # 65 HP

    # Immediate second collision with dummy 1 during SAME slide: must NOT deal damage again
    new_hp2, damaged2 = player.apply_slide_kick("target_drone_01", new_hp)
    assert damaged2 is False
    assert new_hp2 == new_hp, "Repeated damage occurred on same target in one slide"

    # Different target drone 2 can still be damaged in this slide
    new_hp_b, damaged_b = player.apply_slide_kick("target_drone_02", 100)
    assert damaged_b is True
    assert new_hp_b == 65

    # 3. Solid wall collision during slide: cannot cross wall and slide terminates
    for _ in range(40):
        player.update(1.0 / 60.0, PlayerInput(), room)

    assert player.is_sliding is False, "Slide did not terminate on wall collision"
    assert player.x + player.width <= 160.0 + 0.01, "Player crossed or clipped into solid wall during slide"
    assert player.vx == 0.0


def test_locomotion_reset_on_death_and_pause():
    """
    Acceptance Check: Pause/death/reset restore the right locomotion state.
    """
    grid = [[COLLISION_SOLID] * 10 for _ in range(5)]
    room = create_test_room(grid)

    player = Player(32.0, 32.0)
    player.is_grounded = True
    player.is_sliding = True
    player.is_crouching = True
    player.in_cover = True
    player.cover_type = "background"
    player.slide_damaged_targets.add("drone_x")

    # Trigger death & checkpoint respawn
    player.respawn_at_checkpoint(room)

    # All locomotion and combat stance states must be reset to coherent neutral
    assert player.is_sliding is False
    assert player.is_crouching is False
    assert player.in_cover is False
    assert player.cover_type is None
    assert len(player.slide_damaged_targets) == 0
    assert player.slide_timer == 0.0
    assert player.animation_state in ("idle", "walk", "jump", "fall")
    assert player.health == 100


def test_wall_slide_and_wall_jump_kinematics():
    """
    S10 Verification:
    - Wall slide clamps fall speed to wall_slide_speed (60 px/s) when pressing toward wall.
    - Wall jump launches upward/outward with wall_jump_vy (-260 px/s) and wall_jump_vx (200 px/s).
    - Wall jump lock timer (0.15s) prevents immediate turnaround into the wall.
    - Symmetrical behavior verified on both left and right solid vertical walls.
    """
    grid = []
    for r in range(10):
        row = [COLLISION_SOLID] + [COLLISION_EMPTY] * 7 + [COLLISION_SOLID]
        grid.append(row)
    grid.append([COLLISION_SOLID] * 9)
    room = create_test_room(grid)

    cfg = PlayerConfig.load_from_file()

    # 1. Right wall slide:
    # Right wall starts at col 8 * 16 = 128.
    player = Player(112.0, 30.0, cfg)
    player.is_grounded = False
    player.vy = 120.0

    p_input = PlayerInput(move_x=1.0)
    player.update(1.0 / 60.0, p_input, room)

    assert player.is_wall_sliding is True, "Player failed to engage wall slide on right wall"
    assert player.wall_contact_dir == 1
    assert player.vy <= player.cfg.wall_slide_speed + 1.0, f"Vertical fall speed not clamped: vy={player.vy}"
    assert player.animation_state == "crouch"

    # Advance 5 frames holding wall: velocity remains clamped around 60 px/s
    for _ in range(5):
        player.update(1.0 / 60.0, PlayerInput(move_x=1.0), room)
    assert player.vy <= player.cfg.wall_slide_speed + 1.0

    # 2. Wall jump off right wall
    jump_input = PlayerInput(jump_pressed=True, move_x=1.0)
    player.update(1.0 / 60.0, jump_input, room)

    assert player.is_wall_sliding is False, "Wall slide not cleared upon wall jump"
    assert player.vy == pytest.approx(player.cfg.wall_jump_vy, abs=10.0)
    assert player.vx == pytest.approx(-player.cfg.wall_jump_vx, abs=10.0)  # Launched leftward (-200 px/s)
    assert player.facing == "left"
    assert player.wall_jump_lock_timer > 0.0

    # Verify input lock: player holds right for next tick, but vx remains strongly negative
    player.update(1.0 / 60.0, PlayerInput(move_x=1.0), room)
    assert player.vx < -150.0, "Input lock failed: player abruptly reversed towards wall"

    # 3. Left wall slide & jump symmetry:
    # Col 0 is solid (0..16). Place player at x = 16.0, y = 30.0
    player_left = Player(16.0, 30.0, cfg)
    player_left.is_grounded = False
    player_left.vy = 100.0

    player_left.update(1.0 / 60.0, PlayerInput(move_x=-1.0), room)
    assert player_left.is_wall_sliding is True
    assert player_left.wall_contact_dir == -1
    assert player_left.vy <= player_left.cfg.wall_slide_speed + 1.0

    player_left.update(1.0 / 60.0, PlayerInput(jump_pressed=True, move_x=-1.0), room)
    assert player_left.is_wall_sliding is False
    assert player_left.vy == pytest.approx(player_left.cfg.wall_jump_vy, abs=10.0)
    assert player_left.vx == pytest.approx(player_left.cfg.wall_jump_vx, abs=10.0)
    assert player_left.facing == "right"


def test_magnetic_grapple_anchor_latch_and_momentum_release():
    """
    S10 Verification:
    - Grapple anchor within range (<= 160 px) latches on grapple_pressed.
    - Out of range anchor (> 160 px) is safely ignored.
    - Active grapple applies kinematic reeling acceleration toward anchor.
    - Jump release imparts upward tangential momentum boost.
    """
    objects = [
        {
            "id": "anchor_01",
            "type": "grapple_anchor",
            "x": 100.0,
            "y": 20.0,
            "width": 16,
            "height": 16,
        }
    ]
    grid = [[COLLISION_EMPTY] * 20 for _ in range(12)]
    grid.append([COLLISION_SOLID] * 20)
    room = create_test_room(grid, objects=objects)

    cfg = PlayerConfig.load_from_file()

    # 1. Out of range check
    far_player = Player(280.0, 160.0, cfg)
    far_player.is_grounded = False
    far_player.update(1.0 / 60.0, PlayerInput(grapple_pressed=True), room)
    assert far_player.is_grappling is False
    assert far_player.grapple_anchor is None

    # 2. In range latch
    player = Player(100.0, 80.0, cfg)
    player.is_grounded = False
    player.update(1.0 / 60.0, PlayerInput(grapple_pressed=True), room)

    assert player.is_grappling is True
    assert player.grapple_anchor is not None
    assert player.grapple_anchor.id == "anchor_01"
    assert player.animation_state == "jump"

    # 3. Pull acceleration toward anchor
    initial_dist = math.hypot(108.0 - (player.x + player.width / 2.0), 28.0 - (player.y + player.height / 2.0))
    for _ in range(5):
        player.update(1.0 / 60.0, PlayerInput(), room)

    new_dist = math.hypot(108.0 - (player.x + player.width / 2.0), 28.0 - (player.y + player.height / 2.0))
    assert new_dist < initial_dist, "Player did not move closer to grapple anchor during reel"
    assert player.vy < 0.0, "Upward reeling velocity was not produced"

    # 4. Jump release with momentum fling
    player.update(1.0 / 60.0, PlayerInput(jump_pressed=True), room)
    assert player.is_grappling is False
    assert player.grapple_anchor is None
    assert player.vy <= -100.0, f"Momentum fling did not preserve upward velocity: vy={player.vy}"


def test_fibonacci_dash_swept_collision_and_invulnerability():
    """
    S10 Verification:
    - Fibonacci dash initiates at 360 px/s with invulnerability frames (0.15s).
    - Invulnerability negates hazard/incoming damage during active window.
    - Swept axis-separated collision halts dash immediately at solid wall face without tunneling.
    - Cadence dash damage deals 30 damage to combat target exactly once per sequence.
    """
    grid = [[COLLISION_EMPTY] * 15 for _ in range(5)]
    solid_row = [COLLISION_EMPTY] * 6 + [COLLISION_SOLID] * 2 + [COLLISION_EMPTY] * 7
    grid.append(solid_row)
    grid.append([COLLISION_SOLID] * 15)
    room = create_test_room(grid)

    cfg = PlayerConfig.load_from_file()
    player = Player(20.0, 64.0, cfg)
    player.is_grounded = True

    # 1. Dash initiation
    player.update(1.0 / 60.0, PlayerInput(dash_pressed=True, move_x=1.0), room)
    assert player.is_dashing is True
    assert player.vx == player.cfg.fibonacci_dash_speed
    assert player.invulnerable_timer >= 0.14
    assert player.dash_attack_rect is not None

    # 2. Invulnerability protection
    orig_hp = player.health
    player.take_damage(25)
    assert player.health == orig_hp, "Damage taken during dash invulnerability frame"

    # 3. Cadence dash attack tracking
    dummy = CombatTarget("core_drone_dummy", pygame.Rect(40, 64, 16, 16), health=100, max_health=100)
    hit_1 = player.apply_dash_attack(dummy)
    assert hit_1 is True
    assert dummy.health == 100 - player.cfg.fibonacci_dash_damage

    # Repeated hit during same dash must NOT re-apply damage
    hit_2 = player.apply_dash_attack(dummy)
    assert hit_2 is False
    assert dummy.health == 70

    # 4. Anti-tunneling wall collision stop
    for _ in range(25):
        player.update(1.0 / 60.0, PlayerInput(move_x=1.0), room)

    assert player.x + player.width <= 96.0 + 0.01, f"Player tunneled into/through wall: x={player.x}"
    assert player.is_dashing is False, "Dash remained active after solid collision"
    assert player.vx == 0.0


def test_serendipity_tape_deck_prediction_disruption():
    """
    S10 Verification:
    - Serendipity tape deck activation broadcasts analog adversarial noise.
    - Core enemies (drone, enforcer) have active aim telegraphs canceled and forced into recovery.
    - prediction_shattered status condition is applied to enemies.
    - Shattered targets take 3.0x Anomaly Critical Damage from weapons.
    """
    abilities = AbilityManager()
    tape_deck = abilities.abilities["serendipity_tape_deck"]
    tape_deck.is_unlocked = True

    player = Player(100.0, 100.0)
    player.abilities = abilities

    drone = CoreReconDrone("recon_01", 140.0, 100.0)
    drone.telegraph_active = True
    drone.telegraph_locked = True
    drone.state = "attack"

    enforcer = CoreEnforcer("enforcer_01", 170.0, 100.0)
    enforcer.telegraph_active = True
    enforcer.state = "windup"

    hound = StaticHound("hound_01", 200.0, 100.0)

    class MockContext:
        class enemy_manager:
            enemies = [drone, enforcer, hound]

    tape_deck.activate(player, context=MockContext)

    assert player.has_serendipity_buff is True
    assert player.serendipity_timer > 0.0

    # Core recon drone telegraph shattered and staggered into recovery
    assert drone.telegraph_active is False
    assert drone.telegraph_locked is False
    assert drone.state == "recovery"
    assert drone.has_status("prediction_shattered") is True

    # Core enforcer telegraph shattered
    assert enforcer.telegraph_active is False
    assert enforcer.state == "recovery"
    assert enforcer.has_status("prediction_shattered") is True

    # Anomaly critical damage check:
    # 1. Enforcer with 120 HP takes 25 * 3.0 = 75 anomaly damage, leaving 45 HP
    hit_result = enforcer.take_damage(25)
    assert hit_result.damage_dealt == 75
    assert enforcer.health == enforcer.cfg.max_health - 75  # 120 - 75 = 45
    assert enforcer.is_dead is False

    # 2. Drone with 50 HP takes up to remaining HP (50 dealt) and is eliminated
    drone_hit = drone.take_damage(25)
    assert drone_hit.damage_dealt == 50
    assert drone.health == 0
    assert drone.is_dead is True


def test_advanced_traversal_mid_action_interruptions():
    """
    S10 Verification:
    - Pausing game freezes dash timers, grapple velocity, and wall slides without corruption.
    - Checkpoint respawn cleans up all active traversal states to neutral posture.
    """
    grid = [[COLLISION_SOLID] * 10 for _ in range(5)]
    room = create_test_room(grid)

    player = Player(32.0, 32.0)
    player.is_dashing = True
    player.dash_timer = 0.18
    player.is_grappling = True
    player.is_wall_sliding = True
    player.wall_jump_lock_timer = 0.12
    player.has_serendipity_buff = True
    player.serendipity_timer = 2.5

    # 1. Pause freeze
    player.update(0.016, PlayerInput(), room, is_paused=True)
    assert player.is_dashing is True
    assert player.dash_timer == 0.18
    assert player.serendipity_timer == 2.5

    # 2. Checkpoint respawn cleanup
    player.respawn_at_checkpoint(room)
    assert player.is_dashing is False
    assert player.dash_timer == 0.0
    assert player.is_grappling is False
    assert player.grapple_anchor is None
    assert player.is_wall_sliding is False
    assert player.wall_jump_lock_timer == 0.0
    assert player.has_serendipity_buff is False
    assert player.serendipity_timer == 0.0
    assert len(player.dash_damaged_targets) == 0
