"""Verify room geometry, continuous native art and doorway rendering."""

from video_game.engine import config
import json
from pathlib import Path

import pygame
import pytest

from video_game.engine.config import ASSETS_DIR
from video_game.engine.encounter_director import ForwardEncounter
from video_game.engine.enemies import EnemyManager
from video_game.engine.native_room_assets import load_native_room_family
from video_game.engine.world import Camera, Room

ROOT = config.DATA_DIR
WIDTHS = {'approach': 960, 'perimeter_road': 960, 'ohio_campus': 1280,
          'salvage_outer': 640, 'salvage_yard': 640, 'salvage_runoff': 640,
          'dish_service': 640, 'dish_catwalk': 640, 'dish_return': 640}


def test_rooms_use_original_art_widths_and_safe_encounters():
    data = json.loads((ROOT / 'act_01_encounters.json').read_text())
    for name, width in WIDTHS.items():
        room = Room.load_from_file(ROOT / 'levels/act_01' / (name + '.json'))
        assert room.width_px == width
        for x in range(width - 32, width, 16):
            col = room.check_rect_collision(pygame.Rect(x, 208, 16, 32))
            assert not col['solid'] and not col['hazard']
        if name in ('salvage_yard', 'dish_catwalk'):
            assert all(room.get_tile(col, row) == 0
                       for col in (width // 16 - 2, width // 16 - 1)
                       for row in range(15))
        director = ForwardEncounter(room, EnemyManager())
        assert director.entries == data['rooms'][room.room_id]
        assert 3 <= len(director.entries) <= 6
        assert all(director._safe(entry) for entry in director.entries)
        assert all(0 <= spawn.x < width for spawn in room.spawns.values())
        assert any(e.x >= room.width_px - 64 for e in room.exits)
    assert sum(WIDTHS[name] for name in ('approach', 'ohio_campus', 'salvage_yard', 'dish_catwalk')) == 3520


@pytest.mark.parametrize('name,width', WIDTHS.items())
def test_native_planes_preserve_original_prefix_and_cover_full_room(name, width, monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER', 'dummy')
    pygame.display.init(); pygame.display.set_mode((1, 1))
    room_id = 'act_01_' + name
    original = load_native_room_family(ASSETS_DIR, room_id, (width, 288))
    enlarged = load_native_room_family(ASSETS_DIR, room_id, (width * 6, 288))
    assert original is not None and enlarged is not None
    assert enlarged.world is not None and enlarged.world.get_width() == width * 2
    camera = Camera(); camera.set_world_bounds(width * 6, 288)
    for x in (0, (width - 480) // 2, width - 480):
        camera.x = x
        a = original.crops(camera); b = enlarged.crops(camera)
        assert [pygame.image.tobytes(s, 'RGBA') for s in a] == [pygame.image.tobytes(s, 'RGBA') for s in b]
        assert b[1].get_parent() is enlarged.world
    camera.x = width
    assert enlarged.crops(camera)[1].get_parent() is enlarged._mirrored_world
    for x in range(0, width * 6 - 479, 73):
        camera.x = x
        far, world = enlarged.crops(camera)
        assert far.get_size() == world.get_size() == (960, 540)
    for boundary in range(width, width * 6, width):
        camera.x = boundary - 240
        _, world = enlarged.crops(camera)
        left = world.subsurface((479, 0, 1, 540))
        right = world.subsurface((480, 0, 1, 540))
        assert pygame.image.tobytes(left, 'RGBA') == pygame.image.tobytes(right, 'RGBA')
    camera.x = width * 6 - 480
    assert enlarged.crops(camera)[1].get_size() == (960, 540)
    assert load_native_room_family(ASSETS_DIR, room_id, (width * 6 + 16, 288)) is None


def test_alien_exit_uses_transparent_ring_without_changing_interaction(monkeypatch):
    from video_game.engine import world as world_module
    monkeypatch.setattr(world_module, 'get_env_asset', lambda _name: None)
    monkeypatch.setattr(world_module, 'get_airlock_label_surf',
                        lambda: (_ for _ in ()).throw(AssertionError('Earth label used for alien portal')))
    data = {'room_id':'alien_001_field', 'width_tiles':30, 'height_tiles':18,
            'tile_size':16, 'collision_layers':[[0] * 30 for _ in range(18)],
            'spawns':{'default':{'x':32, 'y':208}},
            'exits':[{'id':'test_portal','x':100,'y':100,'width':32,'height':48,
                      'target_room':'alien_001_arena','target_spawn':'default'}]}
    room = Room(data); camera = Camera(); surface = pygame.Surface((480,270))
    surface.fill((7,8,9)); before = room.exits[0].rect.copy()
    room.render_objects(surface, camera)
    assert room.exits[0].rect == before
    assert room.check_exit_trigger(pygame.Rect(110, 110, 16, 32)).id == 'test_portal'
    assert surface.get_at((116,124))[:3] == (7,8,9)  # No opaque bunker-door fill.
    assert any(surface.get_at((x,y))[:3] in ((51,112,151),(91,157,184))
               for x in range(100,132) for y in range(100,148))


def test_earth_walk_connections_draw_no_doors(monkeypatch):
    from video_game.engine import world as world_module
    monkeypatch.setattr(world_module, 'get_env_asset', lambda _name: None)
    monkeypatch.setattr(world_module, 'get_airlock_label_surf',
                        lambda: (_ for _ in ()).throw(AssertionError('Door drawn on an open path')))
    room = Room.load_from_file(ROOT / 'levels/act_01/ohio_campus.json')
    room.objects.clear()
    room.checkpoints.clear()
    surface = pygame.Surface((480, 270))
    surface.fill((7, 8, 9))
    before = pygame.image.tobytes(surface, 'RGB')
    room.render_objects(surface, Camera())
    assert pygame.image.tobytes(surface, 'RGB') == before
