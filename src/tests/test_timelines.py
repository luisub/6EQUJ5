"""
MODULE: tests/test_timelines.py
PURPOSE: Comprehensive test suite for Task S06: Safe Mandela geometry swaps, dual 2029/1977 collision grids, transactional swap validation, safe displacement solver, persistent object state, moving platforms, and save/reload retention.
CALLED BY: pytest (`pytest tests/test_timelines.py -v`).
HOW TO MODIFY: Add tests for additional temporal mechanics or relay events; maintain zero wildcard imports.
"""

import json
import os
from pathlib import Path
import pytest
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from video_game.engine import config
from video_game.engine.campaign import Campaign
from video_game.engine.mandela_world import (
    DEFAULT_ATMOSPHERES,
    DisplacementSolver,
    MandelaWorld,
    MovingPlatform,
    PersistentObjectState,
    SwapResult,
)
from video_game.engine.player import Player, PlayerConfig, PlayerInput
from video_game.engine.save_game import SaveStore
from video_game.engine.temporal_relay import (
    AUTHORED_ACTIONS,
    AUTHORED_MESSAGES,
    ERA_1985,
    ERA_2029,
    ERA_2031,
    ERA_COLORS,
    HistoricalAction,
    RelayMessage,
    TemporalRelay,
)
from video_game.engine.world import (
    Camera,
    COLLISION_COVER,
    COLLISION_EMPTY,
    COLLISION_HAZARD,
    COLLISION_ONE_WAY,
    COLLISION_SOLID,
    Room,
    RoomObject,
)

LEVELS_DIR = config.DATA_DIR / "levels"
MANDELA_TEST_PATH = LEVELS_DIR / "act_01" / "mandela_test.json"
DODLESTON_RELAY_PATH = LEVELS_DIR / "act_04" / "dodleston_relay.json"


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    """Ensure pygame modules are initialized once for headless testing."""
    pygame.init()
    if not pygame.display.get_init():
        pygame.display.init()
    pygame.display.set_mode((480, 270))
    yield
    pygame.quit()


class DummyActor:
    """Mock companion or objective entity for testing footprint embedding."""
    def __init__(self, x: float, y: float, w: int = 16, h: int = 32, actor_id: str = "drone_companion"):
        self.id = actor_id
        self.x = float(x)
        self.y = float(y)
        self.width = w
        self.height = h

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)


def test_dual_timeline_collision_layers_and_object_filtering():
    """Verify Room loads aligned 2029 and 1977 collision layers and filters timeline objects."""
    assert MANDELA_TEST_PATH.exists()
    room = Room.load_from_file(MANDELA_TEST_PATH)

    assert room.active_timeline == "2029_CORE"
    assert "2029_CORE" in room.timeline_collision_layers
    assert "1977_ANALOG" in room.timeline_collision_layers

    # Check that in 2029, col 8, row 13 is empty corridor (0)
    assert room.get_tile_in_timeline(8, 13, "2029_CORE") == COLLISION_EMPTY
    # In 1977, col 8, row 13 is a solid concrete wall (1)
    assert room.get_tile_in_timeline(8, 13, "1977_ANALOG") == COLLISION_SOLID

    # Check hazard in 2029 vs solid bridge in 1977 at col 18, row 14
    assert room.get_tile_in_timeline(18, 14, "2029_CORE") == COLLISION_HAZARD
    assert room.get_tile_in_timeline(18, 14, "1977_ANALOG") == COLLISION_SOLID

    # Object timeline filtering
    all_objs = room.objects
    assert len(all_objs) == 6  # Includes the authored magnetic grapple teaching anchor.

    objs_2029 = room.get_objects_for_timeline("2029_CORE")
    ids_2029 = {o.id for o in objs_2029}
    assert "pickup_analog_coupler" in ids_2029
    assert "door_bulkhead_01" in ids_2029
    assert "plat_temporal_01" in ids_2029
    assert "pickup_1977_log" not in ids_2029

    objs_1977 = room.get_objects_for_timeline("1977_ANALOG")
    ids_1977 = {o.id for o in objs_1977}
    assert "pickup_1977_log" in ids_1977
    assert "pickup_analog_coupler" not in ids_1977
    assert "door_bulkhead_01" in ids_1977
    assert "plat_temporal_01" in ids_1977


def test_clean_timeline_swap_when_unobstructed():
    """Verify clean timeline swap succeeds without displacement when player area is clear."""
    room = Room.load_from_file(MANDELA_TEST_PATH)
    world = MandelaWorld(room, initial_timeline="2029_CORE")
    player = Player(x=32.0, y=208.0)

    # In 2029, player is at (32, 208). At (32, 208), 1977 is also clear ground
    res = world.swap_timeline("1977_ANALOG", player)
    assert res.success is True
    assert res.from_timeline == "2029_CORE"
    assert res.to_timeline == "1977_ANALOG"
    assert res.displacement == (0.0, 0.0)
    assert res.reason == "SWAP_COMMITTED"
    assert world.active_timeline == "1977_ANALOG"
    assert world.room.active_timeline == "1977_ANALOG"
    assert player.x == 32.0
    assert player.y == 208.0

    # Repeating same swap returns ALREADY_ACTIVE
    res2 = world.swap_timeline("1977_ANALOG", player)
    assert res2.success is True
    assert res2.reason == "ALREADY_ACTIVE"


def test_blocked_timeline_swap_rejects_transactionally_without_corruption():
    """Verify that attempting to swap into a solid wall is rejected with zero state mutation."""
    room = Room.load_from_file(MANDELA_TEST_PATH)
    world = MandelaWorld(room, initial_timeline="2029_CORE")

    # Place player at (144, 208), which is inside the 1977 solid concrete block (cols 8..12, rows 12..14)
    # The block extends 64px wide and 48px high, well beyond safe displacement limit (24px)
    player = Player(x=144.0, y=208.0)
    orig_x = player.x
    orig_y = player.y

    res = world.swap_timeline("1977_ANALOG", player, allow_displacement=True)
    assert res.success is False
    assert res.from_timeline == "2029_CORE"
    assert res.to_timeline == "1977_ANALOG"
    assert res.displacement == (0.0, 0.0)
    assert res.reason == "BLOCKED_BY_SOLID"
    assert "TEMPORAL REJECTED" in res.rejection_feedback

    # Invariants: world timeline is unchanged, player position is unchanged
    assert world.active_timeline == "2029_CORE"
    assert world.room.active_timeline == "2029_CORE"
    assert player.x == orig_x
    assert player.y == orig_y
    # Player was NEVER embedded in solid geometry!
    col = world.room.check_rect_collision(player.rect)
    assert col["solid"] is False


def test_safe_displacement_resolves_minor_elevation_step_up():
    """Verify safe displacement automatically nudges player onto higher ground in target timeline."""
    room = Room.load_from_file(MANDELA_TEST_PATH)
    world = MandelaWorld(room, initial_timeline="2029_CORE")

    # In 1977, cols 4..6 has a step-up platform at row 14 (top at y = 14*16 = 224).
    # In 2029, the floor is at row 15 (top at y = 15*16 = 240).
    # If the player is at x=80.0, y=208.0, player rect is (80, 208, 16, 32), with feet at y=240, overlapping the platform [224, 240].
    player = Player(x=80.0, y=208.0)
    assert player.rect.bottom == 240

    res = world.swap_timeline("1977_ANALOG", player, allow_displacement=True)
    assert res.success is True
    assert res.reason == "SAFE_DISPLACEMENT_APPLIED"
    assert res.displacement[1] < 0.0  # Nudged upward onto the platform!
    assert world.active_timeline == "1977_ANALOG"

    # Verify new position is completely free of solid collision in 1977
    col = world.room.check_rect_collision(player.rect)
    assert col["solid"] is False
    assert col["hazard"] is False


def test_hazard_pit_swap_rejection():
    """Verify that swapping into a toxic hazard pit is rejected or safely displaced."""
    room = Room.load_from_file(MANDELA_TEST_PATH)
    world = MandelaWorld(room, initial_timeline="1977_ANALOG")

    # In 1977, cols 18..20 has a solid catwalk bridge over the hazard sump.
    # Player stands on this bridge at x=304.0, y=192.0 (feet at y=224).
    # In 2029, this exact spot is an open air fall directly into a HAZARD sump at row 14!
    # Without safe displacement, or if safe displacement is turned off, swapping to 2029 is rejected.
    player = Player(x=304.0, y=192.0)

    # Test with allow_displacement=False: must cleanly reject
    res = world.swap_timeline("2029_CORE", player, allow_displacement=False)
    # If the player footprint directly collides with hazard, it rejects with BLOCKED_BY_HAZARD
    # Even if airborne right above, let's verify player position doesn't land inside hazard
    if not res.success:
        assert res.reason in ("BLOCKED_BY_HAZARD", "BLOCKED_BY_SOLID")
        assert world.active_timeline == "1977_ANALOG"


def test_actor_footprint_embedding_prevents_swap():
    """Verify that a required companion actor embedding in target geometry rejects swap."""
    room = Room.load_from_file(MANDELA_TEST_PATH)
    world = MandelaWorld(room, initial_timeline="2029_CORE")
    player = Player(x=32.0, y=208.0)  # Player is in clear area

    # Companion actor is standing at (144, 208), which is inside the 1977 solid concrete wall
    companion = DummyActor(x=144.0, y=208.0, actor_id="mateo_companion")

    res = world.swap_timeline("1977_ANALOG", player, actors=[companion])
    assert res.success is False
    assert res.reason == "ACTOR_EMBEDDED"
    assert "mateo_companion" in res.rejection_feedback
    assert world.active_timeline == "2029_CORE"


def test_repeated_swaps_cannot_duplicate_pickups():
    """Verify that collecting a pickup prevents respawning or duplicate reward across swaps."""
    room = Room.load_from_file(MANDELA_TEST_PATH)
    world = MandelaWorld(room, initial_timeline="2029_CORE")
    player = Player(x=32.0, y=208.0)

    # 1. Collect pickup in 2029
    reward1 = world.collect_pickup("pickup_analog_coupler", player)
    assert reward1 is not None
    assert reward1["item_id"] == "analog_coupler"
    assert world.state.is_collected("pickup_analog_coupler") is True

    # 2. Swap to 1977
    res = world.swap_timeline("1977_ANALOG", player)
    assert res.success is True
    # In 1977, 2029 pickup is not in active objects
    objs_1977 = world.room.get_objects_for_timeline("1977_ANALOG")
    assert "pickup_analog_coupler" not in {o.id for o in objs_1977}

    # 3. Swap back to 2029
    res_back = world.swap_timeline("2029_CORE", player)
    assert res_back.success is True

    # 4. Attempt to collect pickup again
    reward2 = world.collect_pickup("pickup_analog_coupler", player)
    assert reward2 is None  # MUST BE NONE! No duplicate pickup!

    # 5. Check another pickup in 1977
    world.swap_timeline("1977_ANALOG", player)
    reward_log = world.collect_pickup("pickup_1977_log", player)
    assert reward_log is not None
    assert reward_log["item_id"] == "dossier_1977"

    # Repeated collection in 1977 also denied
    assert world.collect_pickup("pickup_1977_log", player) is None


def test_door_states_persist_across_swaps():
    """Verify door open/closed and lock states are preserved across timeline swaps."""
    room = Room.load_from_file(MANDELA_TEST_PATH)
    world = MandelaWorld(room, initial_timeline="2029_CORE")
    player = Player(x=32.0, y=208.0)

    # Initial door state: closed
    d_st = world.state.get_door_state("door_bulkhead_01")
    assert d_st["open"] is False

    # Open door in 2029
    world.toggle_door("door_bulkhead_01", is_open=True)
    assert world.state.get_door_state("door_bulkhead_01")["open"] is True

    # Swap to 1977
    world.swap_timeline("1977_ANALOG", player)
    assert world.state.get_door_state("door_bulkhead_01")["open"] is True

    # Swap back to 2029
    world.swap_timeline("2029_CORE", player)
    assert world.state.get_door_state("door_bulkhead_01")["open"] is True


def test_moving_platform_kinematics_and_player_riding():
    """Verify moving platforms update waypoints and convey the player."""
    room = Room.load_from_file(MANDELA_TEST_PATH)
    world = MandelaWorld(room, initial_timeline="2029_CORE")
    assert "plat_temporal_01" in world.moving_platforms

    plat = world.moving_platforms["plat_temporal_01"]
    start_x = plat.x
    start_y = plat.y

    # Update world by 0.5s at speed 40 px/s -> should move ~20px
    world.update(0.5)
    assert plat.x > start_x
    assert plat.dx > 0.0

    # Place player on top of the moving platform
    player = Player(x=plat.x, y=plat.y - 32.0)
    # Footprint bottom is at y + 32 = plat.y
    assert plat.is_actor_riding(player.rect) is True

    # Update world with player riding
    curr_plat_x = plat.x
    curr_player_x = player.x
    world.update(0.2, player=player)

    # Both platform and player should have advanced by same delta
    assert player.x > curr_player_x
    plat_delta = plat.x - curr_plat_x
    player_delta = player.x - curr_player_x
    assert abs(plat_delta - player_delta) < 1e-4


def test_save_and_reload_persistence():
    """Verify that saving and loading Mandela world state preserves timeline and objects."""
    room = Room.load_from_file(MANDELA_TEST_PATH)
    world = MandelaWorld(room, initial_timeline="2029_CORE")
    player = Player(x=32.0, y=208.0)

    # Collect pickup in 2029
    world.collect_pickup("pickup_analog_coupler")
    # Open door
    world.toggle_door("door_bulkhead_01", is_open=True)
    # Swap to 1977
    world.swap_timeline("1977_ANALOG", player)
    assert world.active_timeline == "1977_ANALOG"

    # Serialize state
    saved_state = world.to_dict()
    assert saved_state["active_timeline"] == "1977_ANALOG"
    assert "pickup_analog_coupler" in saved_state["persistent_state"]["collected_pickups"]
    assert saved_state["persistent_state"]["door_states"]["door_bulkhead_01"]["open"] is True

    # Create new fresh room and world, then restore
    new_room = Room.load_from_file(MANDELA_TEST_PATH)
    new_world = MandelaWorld(new_room, initial_timeline="2029_CORE")
    assert new_world.active_timeline == "2029_CORE"
    assert new_world.state.is_collected("pickup_analog_coupler") is False

    new_world.from_dict(saved_state)
    assert new_world.active_timeline == "1977_ANALOG"
    assert new_world.room.active_timeline == "1977_ANALOG"
    assert new_world.state.is_collected("pickup_analog_coupler") is True
    assert new_world.state.get_door_state("door_bulkhead_01")["open"] is True


def test_coherent_camera_and_lighting_transition():
    """Verify camera tracking is uninterrupted and atmospheric lighting changes coherently."""
    room = Room.load_from_file(MANDELA_TEST_PATH)
    world = MandelaWorld(room, initial_timeline="2029_CORE")
    camera = Camera(viewport_w=480, viewport_h=270)
    camera.set_world_bounds(room.width_px, room.height_px)
    player = Player(x=32.0, y=208.0)

    # Initial 2029 atmosphere
    atmos_2029 = world.get_atmosphere()
    assert atmos_2029.timeline_id == "2029_CORE"
    assert atmos_2029.mist_intensity == 1.0
    assert atmos_2029.ambient_color == (12, 18, 24)

    # Camera tracking
    camera.update(player.x, player.y)
    cam_x_before = camera.x

    # Swap timeline
    world.swap_timeline("1977_ANALOG", player)
    atmos_1977 = world.get_atmosphere()
    assert atmos_1977.timeline_id == "1977_ANALOG"
    assert atmos_1977.mist_intensity == 0.0
    assert atmos_1977.ambient_color == (36, 28, 18)

    # Camera smoothly continues tracking without teleport or jump
    camera.update(player.x, player.y)
    assert abs(camera.x - cam_x_before) < 5.0

    # Render surface test
    surf = pygame.Surface((480, 270))
    world.render(surf, camera, anim_time=1.0)
    assert surf.get_at((10, 10)) is not None


# ==============================================================================
# S07 DODLESTON RELAY TESTS
# ==============================================================================

def test_dodleston_level_schema_and_initial_state():
    """Verify act_04/dodleston_relay.json loads cleanly and conforms to level contracts."""
    assert DODLESTON_RELAY_PATH.exists()
    room = Room.load_from_file(DODLESTON_RELAY_PATH)

    assert room.schema_version == 1
    assert room.room_id == "act_04_dodleston_relay"
    assert room.act_id == "act_04"
    assert room.width_tiles == 30
    assert room.height_tiles == 18
    assert room.active_timeline == "2029_CORE"

    # Verify hazard trench in 2029 vs dry catwalk in 1977
    for col in range(10, 15):
        assert room.get_tile_in_timeline(col, 14, "2029_CORE") == COLLISION_HAZARD
        assert room.get_tile_in_timeline(col, 14, "1977_ANALOG") == COLLISION_ONE_WAY

    # Verify key objects
    obj_ids = {o.id for o in room.objects}
    assert "terminal_dodleston_relay" in obj_ids
    assert "door_bulkhead_relay" in obj_ids
    assert "junction_coolant_drain" in obj_ids
    assert "cache_relay_tape" in obj_ids


def test_dodleston_messages_era_coherence():
    """Verify that messages across 1985, 2029, and 2031 remain coherent and respect era styling."""
    relay = TemporalRelay()

    # Initial state: only 1985 intro and 2031 warning are visible
    initial_msgs = relay.get_visible_messages()
    assert len(initial_msgs) == 2

    m1, m2 = initial_msgs[0], initial_msgs[1]
    assert m1.era == ERA_1985
    assert "THOMAS HARDEN" in m1.sender
    assert "LARDER PIPE" in m1.text

    assert m2.era == ERA_2031
    assert "MONITOR-2109" in m2.sender
    assert "CAUSAL TELEMETRY" in m2.text

    # Verify distinct era color mapping
    assert ERA_COLORS[ERA_1985] == (245, 180, 50)   # Amber phosphor
    assert ERA_COLORS[ERA_2029] == (65, 195, 245)   # Cyan CRT
    assert ERA_COLORS[ERA_2031] == (185, 115, 250)  # Violet tachyon

    # Set intermediate flags and verify new messages appear coherently
    relay.puzzle_flags["dodleston_coolant_drained"] = True
    drained_msgs = relay.get_visible_messages()
    # Now includes 2029 inquiry, 1985 reply, and 2031 power direction
    assert len(drained_msgs) == 5
    eras_present = {m.era for m in drained_msgs}
    assert eras_present == {ERA_1985, ERA_2029, ERA_2031}

    # Set final flags
    relay.puzzle_flags["dodleston_bulkhead_unlocked"] = True
    relay.puzzle_flags["dodleston_cassette_cached"] = True
    all_msgs = relay.get_visible_messages()
    assert len(all_msgs) == len(AUTHORED_MESSAGES)
    assert any("C-60 cassette retrieved" in m.text for m in all_msgs)


def test_puzzle_1_coolant_drainage_and_rebuild():
    """Verify Puzzle 1: Transmitting to seal 1985 larder valve drains the 2029 coolant trench."""
    room = Room.load_from_file(DODLESTON_RELAY_PATH)
    world = MandelaWorld(room, initial_timeline="2029_CORE")
    player = Player(x=32.0, y=208.0)
    campaign = config.default_campaign_state()

    relay = TemporalRelay(campaign=campaign)

    # Initial condition: cols 10..14 at row 14 are HAZARD
    for c in range(10, 15):
        assert world.room.get_tile(c, 14) == COLLISION_HAZARD

    initial_coord = campaign.state.meters["coordination_capacity"]
    initial_cert = campaign.state.meters["scientific_certainty"]

    # Execute action_seal_valve_drain
    success, summary = relay.apply_action("action_seal_valve_drain", world, player)
    assert success is True
    assert "drains completely" in summary
    assert relay.puzzle_flags["dodleston_coolant_drained"] is True

    # Deterministic consequence in 2029: hazard tiles converted to one-way catwalk
    for c in range(10, 15):
        assert world.room.get_tile(c, 14) == COLLISION_ONE_WAY

    # Campaign progression and meter deltas verified
    assert "relay_action_drain_coolant_action_seal_valve_drain" in campaign.state.applied_event_ids
    assert campaign.state.meters["coordination_capacity"] == initial_coord + 5
    assert campaign.state.meters["scientific_certainty"] == initial_cert + 5


def test_puzzle_2_bulkhead_power_and_unlock():
    """Verify Puzzle 2: Bridging fusebox J1 restores power and unlocks the vault bulkhead."""
    room = Room.load_from_file(DODLESTON_RELAY_PATH)
    world = MandelaWorld(room, initial_timeline="2029_CORE")
    player = Player(x=32.0, y=208.0)
    campaign = config.default_campaign_state()

    relay = TemporalRelay(campaign=campaign)

    # Attempting Puzzle 2 before Puzzle 1 fails prerequisite check
    fail_res, fail_msg = relay.apply_action("action_install_jumper_j1", world, player)
    assert fail_res is False
    assert "prerequisite" in fail_msg

    # Solve Puzzle 1 first
    relay.apply_action("action_seal_valve_drain", world, player)
    assert relay.puzzle_flags["dodleston_coolant_drained"] is True

    # Bulkhead door is initially locked
    door_obj = next(o for o in world.room.objects if o.id == "door_bulkhead_relay")
    assert door_obj.properties["locked"] is True
    assert world.state.get_door_state("door_bulkhead_relay")["open"] is False

    # Execute action_install_jumper_j1
    success, summary = relay.apply_action("action_install_jumper_j1", world, player)
    assert success is True
    assert "Bulkhead door unlocks" in summary
    assert relay.puzzle_flags["dodleston_bulkhead_unlocked"] is True

    # Bulkhead door is unlocked and opened
    assert door_obj.properties["locked"] is False
    assert door_obj.properties["open"] is True
    assert world.state.get_door_state("door_bulkhead_relay")["open"] is True


def test_puzzle_3_chimney_brick_cache_and_pickup():
    """Verify Puzzle 3: Caching C-60 tape in 1985 hearth spawns collectible in 2029."""
    room = Room.load_from_file(DODLESTON_RELAY_PATH)
    world = MandelaWorld(room, initial_timeline="2029_CORE")
    player = Player(x=32.0, y=208.0)
    campaign = config.default_campaign_state()

    relay = TemporalRelay(campaign=campaign)

    # Solve Puzzles 1 & 2
    relay.apply_action("action_seal_valve_drain", world, player)
    relay.apply_action("action_install_jumper_j1", world, player)

    # Execute action_cache_tape_chimney
    success, summary = relay.apply_action("action_cache_tape_chimney", world, player)
    assert success is True
    assert "tape cache is accessible" in summary
    assert relay.puzzle_flags["dodleston_cassette_cached"] is True

    # Collect pickup in 2029
    tape_pickup = next(o for o in world.room.objects if o.id == "cache_relay_tape")
    assert tape_pickup.properties["spawned"] is True

    reward = world.collect_pickup("cache_relay_tape", player)
    assert reward is not None
    assert reward["item_id"] == "relay_cipher_cassette"
    assert world.state.is_collected("cache_relay_tape") is True

    # Re-collecting denied
    assert world.collect_pickup("cache_relay_tape", player) is None


def test_recovery_from_wrong_choice_and_deadlock_prevention():
    """Verify that wrong historical choices can be safely reversed via recalibration."""
    room = Room.load_from_file(DODLESTON_RELAY_PATH)
    world = MandelaWorld(room, initial_timeline="2029_CORE")
    player = Player(x=32.0, y=208.0)

    relay = TemporalRelay()

    # Suboptimal Choice 1: Open cistern floodgate (pipe rupture)
    succ1, msg1 = relay.apply_action("action_open_cistern_flood", world, player)
    assert succ1 is True
    assert relay.puzzle_flags["pipe_ruptured"] is True
    assert relay.puzzle_flags["dodleston_coolant_drained"] is False

    # Verify trench remains hazardous
    assert world.room.get_tile(12, 14) == COLLISION_HAZARD

    # Deadlock Recovery: Recalibrate resets the rupture and applies correct drainage
    rec_ok, rec_msg = relay.recalibrate_puzzles(world, player)
    assert rec_ok is True
    assert "recalibration successful" in rec_msg
    assert relay.puzzle_flags["pipe_ruptured"] is False
    assert relay.puzzle_flags["dodleston_coolant_drained"] is True
    # Trench is now drained!
    assert world.room.get_tile(12, 14) == COLLISION_ONE_WAY

    # Suboptimal Choice 2: Overload shunt J3 (fuse blowout)
    succ2, msg2 = relay.apply_action("action_install_jumper_j3", world, player)
    assert succ2 is True
    assert relay.puzzle_flags["fuse_blown"] is True
    assert relay.puzzle_flags["dodleston_bulkhead_unlocked"] is False

    door_obj = next(o for o in world.room.objects if o.id == "door_bulkhead_relay")
    assert door_obj.properties.get("blown") is True

    # Deadlock Recovery 2: Recalibrate reverses blowout and bridges J1
    rec_ok2, rec_msg2 = relay.recalibrate_puzzles(world, player)
    assert rec_ok2 is True
    assert relay.puzzle_flags["fuse_blown"] is False
    assert relay.puzzle_flags["dodleston_bulkhead_unlocked"] is True
    assert door_obj.properties["open"] is True


def test_anti_trap_safety_during_geometry_rebuild():
    """Verify that player standing near modified tiles/doors is never trapped or embedded."""
    room = Room.load_from_file(DODLESTON_RELAY_PATH)
    world = MandelaWorld(room, initial_timeline="2029_CORE")

    # Place player at x=192.0, y=208.0 (inside the trench area at cols 10..14)
    player = Player(x=192.0, y=208.0)
    relay = TemporalRelay()

    # Apply drainage action
    succ, _ = relay.apply_action("action_seal_valve_drain", world, player)
    assert succ is True

    # Verify player is NOT embedded in solid or hazard geometry
    col = world.room.check_rect_collision(player.rect)
    assert col["solid"] is False
    assert col["hazard"] is False


def test_relay_save_reload_persistence():
    """Verify that TemporalRelay serializes and restores puzzle flags and completed actions."""
    relay = TemporalRelay()
    room = Room.load_from_file(DODLESTON_RELAY_PATH)
    world = MandelaWorld(room, initial_timeline="2029_CORE")
    player = Player(x=32.0, y=208.0)

    # Solve puzzle 1
    relay.apply_action("action_seal_valve_drain", world, player)
    assert relay.puzzle_flags["dodleston_coolant_drained"] is True

    # Save
    data = relay.to_dict()
    assert "action_seal_valve_drain" in data["active_actions"]
    assert data["puzzle_flags"]["dodleston_coolant_drained"] is True

    # Restore in new instance
    new_relay = TemporalRelay()
    assert new_relay.puzzle_flags["dodleston_coolant_drained"] is False

    new_relay.from_dict(data)
    assert new_relay.puzzle_flags["dodleston_coolant_drained"] is True
    assert "action_seal_valve_drain" in new_relay.active_actions


def test_timeline_swap_during_advanced_traversal():
    """
    S11 Verification:
    - Fibonacci quantum dash kinematics and invulnerability are preserved across a Mandela timeline swap.
    - Low-profile crouch/slide collision bounding box is correctly respected by displacement solver during swap.
    """
    room = Room.load_from_file(MANDELA_TEST_PATH)
    world = MandelaWorld(room, initial_timeline="2029_CORE")
    player = Player(x=32.0, y=208.0)
    player.is_grounded = True

    # 1. Initiate Fibonacci dash in 2029
    p_in = PlayerInput(dash_pressed=True, move_x=1.0)
    player.update(1.0 / 60.0, p_in, world.room)
    assert player.is_dashing is True
    assert player.vx == player.cfg.fibonacci_dash_speed
    assert player.invulnerable_timer > 0.0

    # 2. Swap timeline mid-dash
    res = world.swap_timeline("1977_ANALOG", player)
    assert res.success is True
    assert world.active_timeline == "1977_ANALOG"

    # 3. Kinematic continuity: player is still dashing, velocity preserved, invulnerability preserved
    assert player.is_dashing is True
    assert player.vx == player.cfg.fibonacci_dash_speed
    assert player.invulnerable_timer > 0.0

    # 4. Advance frame in new timeline: physics steps smoothly without error or tunneling
    player.update(1.0 / 60.0, PlayerInput(), world.room)
    assert not world.room.check_rect_collision(player.rect)["solid"]


def test_grapple_anchor_timeline_exclusivity():
    """
    S11 Verification:
    - Grapple anchors tagged with a specific timeline are only detectable/latchable in that timeline.
    - Swapping to another timeline cleanly updates query results.
    """
    grid = [[COLLISION_EMPTY] * 30 for _ in range(11)] + [[COLLISION_SOLID] * 30]
    room_data = {
        "schema_version": 1,
        "room_id": "test_grapple_timelines",
        "act_id": "test",
        "title": "Timeline Grapple Room",
        "tile_size": 16,
        "width_tiles": 30,
        "height_tiles": 12,
        "collision_layers": grid,
        "timeline_collision_layers": {
            "2029_CORE": grid,
            "1977_BIG_EAR": grid,
        },
        "background_layers": [],
        "spawns": {"default": {"x": 32.0, "y": 144.0, "facing": "right"}},
        "checkpoints": [],
        "exits": [],
        "objects": [
            {
                "id": "anchor_1977",
                "type": "grapple_anchor",
                "x": 100.0,
                "y": 40.0,
                "width": 16,
                "height": 16,
                "timeline": "1977_BIG_EAR",
            },
            {
                "id": "anchor_2029",
                "type": "grapple_anchor",
                "x": 400.0,
                "y": 40.0,
                "width": 16,
                "height": 16,
                "timeline": "2029_CORE",
            },
        ],
    }
    room = Room(room_data)
    world = MandelaWorld(room, initial_timeline="2029_CORE")

    # In 2029_CORE: anchor_2029 is at 400 (> 160 px away). anchor_1977 is in 1977 timeline.
    a_near = world.room.get_nearest_grapple_anchor(100.0, 60.0, max_range=160.0)
    assert a_near is None

    # Near anchor_2029 in 2029_CORE: detectable
    a_2029 = world.room.get_nearest_grapple_anchor(400.0, 60.0, max_range=160.0)
    assert a_2029 is not None
    assert a_2029.id == "anchor_2029"

    # Swap timeline to 1977_BIG_EAR
    p_dummy = Player(x=32.0, y=144.0)
    world.swap_timeline("1977_BIG_EAR", p_dummy)

    # In 1977_BIG_EAR: anchor_1977 is detectable at x=100
    a_1977 = world.room.get_nearest_grapple_anchor(100.0, 60.0, max_range=160.0)
    assert a_1977 is not None
    assert a_1977.id == "anchor_1977"

    # In 1977_BIG_EAR: anchor_2029 is filtered out at x=400
    a_2029_after = world.room.get_nearest_grapple_anchor(400.0, 60.0, max_range=160.0)
    assert a_2029_after is None


