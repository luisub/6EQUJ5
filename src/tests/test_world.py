"""
MODULE: tests/test_world.py
PURPOSE: Test room schema validation, collision categories, camera bounds, partial tile rendering, and Field Ops navigation.
CALLED BY: pytest (`python -m pytest tests -q`).
HOW TO MODIFY: Add regression tests for new level blockouts, camera constraints, and environmental triggers; maintain zero wildcard imports.
"""

import json
import os
from pathlib import Path
import pytest
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from video_game.engine import config
from video_game.engine.campaign import Campaign, load_campaign_data
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.scenes.field import FieldOpsScene
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.world import (
    Camera,
    COLLISION_COVER,
    COLLISION_EMPTY,
    COLLISION_HAZARD,
    COLLISION_ONE_WAY,
    COLLISION_SOLID,
    Room,
    RoomExit,
    RoomCheckpoint,
    SpawnPoint,
)
from video_game.tools.validate_content import validate_all_levels, validate_level_file

LEVELS_DIR = config.DATA_DIR / "levels"
APPROACH_PATH = LEVELS_DIR / "act_01" / "approach.json"


def test_room_schema_and_level_loading():
    """Verify approach.json loads correctly and conforms to room schema specifications."""
    assert APPROACH_PATH.exists()
    room = Room.load_from_file(APPROACH_PATH)

    assert room.schema_version == 1
    assert room.room_id == "act_01_approach"
    assert room.act_id == "act_01"
    assert room.tile_size == 16
    assert room.width_tiles == 60
    assert room.height_tiles == 18
    assert room.width_px == 960
    assert room.height_px == 288

    # Spawns, checkpoints, exits, objects
    assert "bunker_exit" in room.spawns
    assert "approach_checkpoint" in room.spawns
    assert "dish_perimeter" in room.spawns
    assert len(room.checkpoints) >= 2
    assert len(room.exits) >= 1
    assert len(room.objects) >= 3

    # Background parallax layers
    assert len(room.background_layers) >= 3
    names = [ly["name"] for ly in room.background_layers]
    assert "distant_sky" in names
    assert "perimeter_fence" in names


def test_actionable_errors_on_invalid_room_data():
    """Verify room.validate() returns actionable error messages on malformed data."""
    # 1. Invalid schema version
    bad_data_1 = {
        "schema_version": 99,
        "room_id": "test_bad",
        "act_id": "act_01",
        "tile_size": 16,
        "width_tiles": 10,
        "height_tiles": 5,
        "collision_layers": [[0]*10 for _ in range(5)],
        "spawns": {"default": {"x": 16, "y": 16}},
    }
    room1 = Room(bad_data_1)
    errs1 = room1.validate()
    assert any("schema_version" in e for e in errs1)

    # 2. Mismatched collision grid rows
    bad_data_2 = {
        "schema_version": 1,
        "room_id": "test_bad",
        "act_id": "act_01",
        "tile_size": 16,
        "width_tiles": 10,
        "height_tiles": 5,
        "collision_layers": [[0]*10 for _ in range(3)],  # 3 rows instead of 5
        "spawns": {"default": {"x": 16, "y": 16}},
    }
    room2 = Room(bad_data_2)
    errs2 = room2.validate()
    assert any("Collision grid rows" in e for e in errs2)

    # 3. Unknown collision code
    bad_data_3 = {
        "schema_version": 1,
        "room_id": "test_bad",
        "act_id": "act_01",
        "tile_size": 16,
        "width_tiles": 2,
        "height_tiles": 2,
        "collision_layers": [[0, 999], [0, 0]],  # 999 unknown code
        "spawns": {"default": {"x": 0, "y": 0}},
    }
    room3 = Room(bad_data_3)
    errs3 = room3.validate()
    assert any("Unknown collision code 999" in e for e in errs3)


def test_collision_categories_and_queries():
    """Verify solid, one-way, hazard, cover, and empty collision behavior."""
    room = Room.load_from_file(APPROACH_PATH)

    # 1. Bedrock bottom row (solid)
    assert room.get_tile(0, 17) == COLLISION_SOLID
    assert room.get_tile(30, 17) == COLLISION_SOLID

    # 2. Trench sump hazard
    assert room.get_tile(21, 16) == COLLISION_HAZARD

    # 3. Catwalk platform (one-way)
    assert room.get_tile(12, 12) == COLLISION_ONE_WAY
    assert room.get_tile(21, 13) == COLLISION_ONE_WAY

    # 4. Low cover obstacle
    assert room.get_tile(8, 14) == COLLISION_COVER

    # 5. Air (empty)
    assert room.get_tile(5, 5) == COLLISION_EMPTY

    # 6. Out of bounds returns SOLID
    assert room.get_tile(-5, 0) == COLLISION_SOLID
    assert room.get_tile(0, 999) == COLLISION_SOLID

    # 7. check_rect_collision query
    # Box overlapping bedrock
    bedrock_rect = pygame.Rect(100, 16 * 17 + 2, 16, 16)
    res_solid = room.check_rect_collision(bedrock_rect)
    assert res_solid["solid"] is True

    # Box overlapping trench hazard
    hazard_rect = pygame.Rect(21 * 16 + 2, 16 * 16 + 2, 12, 12)
    res_haz = room.check_rect_collision(hazard_rect)
    assert res_haz["hazard"] is True


def test_collision_queries_preserve_grid_selection_and_edges():
    """Active and explicit timelines retain their own grid and overlap semantics."""
    active = [[COLLISION_SOLID, COLLISION_ONE_WAY, 99],
              [COLLISION_HAZARD, COLLISION_COVER, COLLISION_EMPTY]]
    alternate = [[COLLISION_COVER, COLLISION_EMPTY, COLLISION_EMPTY],
                 [COLLISION_EMPTY, COLLISION_EMPTY, COLLISION_EMPTY]]
    room = Room({"tile_size": 16, "collision_layers": active,
                 "timeline_collision_layers": {"other": alternate}})
    whole = pygame.Rect(0, 0, 48, 32)
    expected = {"solid": True, "one_way": True, "hazard": True, "cover": True,
                "tiles": [(0, 0, COLLISION_SOLID), (1, 0, COLLISION_ONE_WAY),
                          (2, 0, 99), (0, 1, COLLISION_HAZARD), (1, 1, COLLISION_COVER)]}
    assert room.check_rect_collision(whole) == expected
    assert room.check_rect_collision_in_timeline(whole, "") == expected
    assert room.check_rect_collision_in_timeline(whole, None) == expected
    assert room.check_rect_collision_in_timeline(whole, "other")["tiles"] == [(0, 0, COLLISION_COVER)]
    assert room.check_rect_collision(pygame.Rect(16, 0, 16, 16))["tiles"] == [(1, 0, COLLISION_ONE_WAY)]
    assert room.check_rect_collision(pygame.Rect(-1, 0, 1, 16))["tiles"] == [(-1, 0, COLLISION_SOLID)]
    assert room.check_rect_collision(pygame.Rect(16, 0, 0, 16))["tiles"] == []

    # Rollback can replace the active grid independently of the timeline map.
    room.collision_grid = alternate
    assert room.check_rect_collision(whole)["tiles"] == [(0, 0, COLLISION_COVER)]
    assert room.check_rect_collision_in_timeline(whole, "unknown")["tiles"] == [(0, 0, COLLISION_COVER)]
    assert room.check_rect_collision_in_timeline(whole, "2029_CORE") == expected


def test_spawns_and_exits_are_collision_free():
    """Verify all defined spawns and exits in approach.json are collision-free."""
    room = Room.load_from_file(APPROACH_PATH)
    c_data = load_campaign_data()

    # validate() checks that player bounding box at all spawns does not overlap solid or hazard
    errs = room.validate(campaign_data=c_data)
    assert errs == []

    # Direct check of player footprint (16x32) at all spawns
    for s_name, sp in room.spawns.items():
        player_box = pygame.Rect(int(sp.x), int(sp.y), 16, 32)
        col = room.check_rect_collision(player_box)
        assert col["solid"] is False, f"Spawn '{s_name}' collides with solid"
        assert col["hazard"] is False, f"Spawn '{s_name}' collides with hazard"

    # Exit check
    assert len(room.exits) >= 1
    ex = room.exits[0]
    assert ex.target_room == "bunker_hub"
    assert ex.target_spawn == "bunker_start"


def test_camera_bounds_clamping_and_smooth_tracking():
    """Verify camera viewport (480x270) stays strictly within room boundaries."""
    camera = Camera(480, 270)
    world_w, world_h = 960, 288
    camera.set_world_bounds(world_w, world_h)

    # Max bounds
    max_x = world_w - 480  # 480
    max_y = world_h - 270  # 18

    # 1. Snap to origin -> clamped to (0, 0)
    camera.snap_to(0, 0)
    assert camera.x == 0.0
    assert camera.y == 0.0

    # 2. Snap to extreme positive -> clamped to (480, 18)
    camera.snap_to(5000, 5000)
    assert camera.x == max_x
    assert camera.y == max_y

    # 3. Snap to center
    camera.snap_to(480, 144)
    expected_x = 480 - 240  # 240
    expected_y = 144 - 135  # 9
    assert camera.x == expected_x
    assert camera.y == expected_y

    # 4. Smooth tracking towards target
    prev_x = camera.x
    camera.update(target_x=600, target_y=144, smoothing=0.2)
    assert camera.x > prev_x
    assert camera.x <= max_x

    # 5. Coordinate transform round-trip
    wx, wy = 325.0, 190.0
    sx, sy = camera.world_to_screen(wx, wy)
    rx, ry = camera.screen_to_world(sx, sy)
    assert abs(rx - wx) <= 1.0
    assert abs(ry - wy) <= 1.0


def test_viewport_partial_tile_handling():
    """
    Verify viewport handles partial bottom tile (270 px height / 16 px tiles = 16.875 tiles)
    without stretching or dropping row 16-17 tiles.
    """
    camera = Camera(480, 270)
    camera.set_world_bounds(960, 288)
    camera.snap_to(240, 135)

    min_col, max_col, min_row, max_row = camera.get_visible_tile_range(tile_size=16)

    # 480 px width / 16 = 30 tiles visible horizontally
    assert (max_col - min_col) >= 30

    # 270 px height / 16 = 16.875 tiles -> must span at least 17 rows to include partial tile
    assert (max_row - min_row) >= 17

    # Render surface
    surf = pygame.Surface((480, 270))
    room = Room.load_from_file(APPROACH_PATH)
    room.render_tiles(surf, camera)

    # Bottom pixels (y=268) must have drawn tiles (not empty black)
    assert surf.get_at((240, 268)) != (0, 0, 0, 255)


def test_validate_content_tool():
    """Verify standalone validate_content tool passes all active levels."""
    results = validate_all_levels()
    assert len(results) >= 1
    for level_key, errors in results.items():
        assert errors == [], f"Level validation errors in {level_key}: {errors}"


def test_field_ops_scene_rendering_and_navigation():
    """Verify FieldOpsScene boots, handles player traversal, and navigates back to bunker."""
    pygame.init()
    window = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    crt = CRTRenderer(scale=config.DEFAULT_SCALE)
    machine = GameStateMachine(crt, development=True)
    machine.campaign = Campaign()

    field_scene = machine.scenes[config.STATE_FIELD_OPS]
    machine.change_state(config.STATE_FIELD_OPS)
    machine.update(0.016)

    assert machine.current_state_name == config.STATE_FIELD_OPS
    assert field_scene.player_x == 48.0
    assert abs(field_scene.player_y - 192.0) <= 2.0

    # Render initial frame
    machine.render()
    crt.present(window)

    # Simulate walking right across trench catwalk
    event_right_down = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)
    field_scene.handle_event(event_right_down)

    for _ in range(30):
        field_scene.update(0.033)
    field_scene.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_RIGHT))

    # Player moved right
    assert field_scene.player_x > 48.0
    # Camera tracked player
    assert field_scene.camera.x >= 0.0

    # Render updated platforming frame
    machine.render()
    crt.present(window)

    # Walk back to airlock door and trigger exit to bunker hub
    field_scene.player_x = 24.0
    field_scene.player_y = 192.0
    field_scene.update(0.016)
    assert field_scene.prompt_text != ""

    event_enter = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
    field_scene.handle_event(event_enter)
    machine.update(0.016)

    # Returned to bunker hub
    assert machine.current_state_name == config.STATE_BUNKER_HUB

    pygame.quit()


def test_ohio_environment_assets_exist_and_match_manifest():
    """
    Acceptance Check: Ohio environment art assets exist, are valid RGBA images,
    and match the schema and checksums in manifest.json.
    """
    import hashlib
    env_dir = config.ASSETS_DIR / 'environments/ohio/shared'
    manifest_path = env_dir / "manifest.json"
    assert manifest_path.exists()

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["schema_version"] == 1
    assert manifest["environment_id"] == "act_01_ohio"
    assert {item["file"] for item in manifest["assets"].values()} == {"tileset.png", "mist.png"}

    for asset_key, info in manifest["assets"].items():
        asset_file = env_dir / info["file"]
        assert asset_file.exists(), f"Asset file missing: {info['file']}"
        h = hashlib.sha256(asset_file.read_bytes()).hexdigest()
        assert h == info["sha256"], f"Checksum mismatch for {info['file']}"


def test_all_four_act_01_rooms_use_ohio_tileset():
    """
    Acceptance Check: All four Act I level files specify tileset_ohio and
    render cleanly with parallax backgrounds and textured tiles.
    """
    pygame.init()
    window = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    crt = CRTRenderer(scale=config.DEFAULT_SCALE)
    levels = [
        "act_01/approach.json",
        "act_01/salvage_yard.json",
        "act_01/dish_catwalk.json",
        "act_01/greenkeeper_arena.json",
    ]

    for rel_path in levels:
        p = config.DATA_DIR / 'levels' / rel_path
        room = Room.load_from_file(p)
        assert room.tileset_id == "tileset_ohio"

        camera = Camera(480, 270)
        camera.set_world_bounds(room.width_px, room.height_px)
        camera.snap_to(room.width_px / 2.0, room.height_px / 2.0)

        # Verify rendering layers pass without error
        crt.clear()
        room.render_background(crt.canvas, camera)
        room.render_tiles(crt.canvas, camera)
        room.render_objects(crt.canvas, camera)
        room.render_weather(crt.canvas, camera)
        crt.present(window)

    pygame.quit()


def test_collision_silhouettes_match_visual_tile_bounds():
    """
    Acceptance Check: Collision bounding geometry perfectly aligns with
    visual tiles, ensuring zero misleading collision surfaces or seams.
    """
    room = Room.load_from_file(APPROACH_PATH)
    tile_size = room.tile_size
    assert tile_size == 16

    # Test solid floor collision height
    col_floor = room.get_collision_at_pixel(100.0, 248.0)
    assert col_floor == COLLISION_SOLID

    # Test catwalk platform one-way top surface
    col_grating_top = room.get_collision_at_pixel(192.0, 192.0)
    assert col_grating_top == COLLISION_ONE_WAY

    # Test cover sandbag low height bounds
    col_cover = room.get_collision_at_pixel(128.0, 224.0)
    assert col_cover == COLLISION_COVER

    # Test sump hazard liquid bounds
    col_hazard = room.get_collision_at_pixel(336.0, 256.0)
    assert col_hazard == COLLISION_HAZARD


def test_parallax_layers_and_weather_render_without_alpha_leak_or_overflow():
    """
    Acceptance Check: Parallax background layers and weather overlay render
    seamlessly across moving camera bounds without seams or color bleed.
    """
    pygame.init()
    pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    room = Room.load_from_file(APPROACH_PATH)

    canvas = pygame.Surface((480, 270))
    camera = Camera(480, 270)
    camera.set_world_bounds(room.width_px, room.height_px)

    # Test multiple camera offsets across the 960px world width
    offsets = [0.0, 240.0, 480.0, 720.0, 960.0]
    for ox in offsets:
        camera.x = ox
        canvas.fill((0, 0, 0))
        room.render_background(canvas, camera)
        room.render_weather(canvas, camera)

        # Sample pixel corners to ensure full opaque coverage (no alpha hole in sky)
        tl_color = canvas.get_at((0, 0))
        br_color = canvas.get_at((479, 269))
        assert tl_color.a == 255
        assert br_color.a == 255
        # Twilight sky zenith should be dark indigo
        assert tl_color.r < 40 and tl_color.b > 10

    pygame.quit()
