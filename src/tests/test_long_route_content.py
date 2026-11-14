"""PURPOSE: Verify the extended Ohio graph, geometry, and safe encounter sites.
CALLED BY: pytest tests/test_long_route_content.py.
HOW TO MODIFY: Preserve forward and reverse graph, geometry, and encounter checks.
"""

from video_game.engine import config
import json
from pathlib import Path

import pygame

from video_game.engine.encounter_director import ForwardEncounter
from video_game.engine.enemies import EnemyManager
from video_game.engine.world import Room

DATA = config.DATA_DIR
LEVELS = DATA / 'levels' / 'act_01'
NAMES = ('perimeter_road', 'salvage_outer', 'salvage_runoff', 'dish_service', 'dish_return')
FORWARD = ('approach', 'ohio_campus', 'salvage_yard', 'dish_catwalk', 'greenkeeper_arena')


def load(name):
    return Room.load_from_file(LEVELS / (name + '.json'))


def test_forward_graph_and_reverse_targets_resolve():
    rooms = {name: load(name) for name in (*FORWARD, *NAMES)}
    for source, dest in zip(FORWARD, FORWARD[1:]):
        exit_ = next(e for e in rooms[source].exits if e.target_room == 'act_01_' + dest)
        assert exit_.target_spawn in rooms[dest].spawns
    for name in NAMES:
        for exit_ in rooms[name].exits:
            target = exit_.target_room.removeprefix('act_01_')
            assert exit_.target_spawn in rooms[target].spawns
    shortcut = next(e for e in rooms['dish_catwalk'].exits if e.id == 'exit_to_approach')
    assert shortcut.target_room == 'act_01_salvage_yard'
    assert shortcut.target_spawn == 'yard_depot'


def test_safe_continuous_ground_and_registered_checkpoints():
    campaign = json.loads((DATA / 'campaign.json').read_text())
    for name in NAMES:
        room = load(name)
        assert room.validate(campaign) == []
        assert (room.width_px, room.height_px) == ((960 if name == 'perimeter_road' else 640), 288)
        assert all(room.get_tile(x, 15) == 1 for x in range(room.width_tiles))
        # A standing 16×32 player has a continuous, clear ground-level route.
        for x in range(0, room.width_px, 16):
            collisions = room.check_rect_collision(pygame.Rect(x, 208, 16, 32))
            assert not collisions['solid'] and not collisions['hazard']
        assert len(room.checkpoints) == 2


def test_all_new_encounters_load_and_have_safe_forward_sites():
    data = json.loads((DATA / 'act_01_encounters.json').read_text())
    ids = []
    for name in NAMES:
        room = load(name)
        director = ForwardEncounter(room, EnemyManager())
        expected = data['rooms'][room.room_id]
        assert len(expected) == (6 if name == 'perimeter_road' else 5)
        assert director.entries == expected
        assert all(director._safe(entry) and director.sites[entry['id']] for entry in expected)
        assert sum(entry['type'] == 'captain' for entry in expected) <= 1
        ids.extend(entry['id'] for entry in expected)
    assert len(ids) == len(set(ids)) == 26
