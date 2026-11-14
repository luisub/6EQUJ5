"""PURPOSE: Validate connected-world blockouts, route links, and discoveries.
CALLED BY: pytest and connected-world content verification.
HOW TO MODIFY: Keep assertions tied to playable geometry, campaign events, and the route data contract.
"""

from video_game.engine import config
import json
from pathlib import Path

import pytest

from video_game.engine.campaign import Campaign, load_campaign_data
from video_game.engine.encounter_director import ForwardEncounter
from video_game.engine.world import Room

DATA = config.DATA_DIR
ROUTE = json.loads((DATA / 'campaign_route.json').read_text())


def test_graph_connects_registered_rooms_and_preserves_the_relay():
    campaign = load_campaign_data()
    rooms = ROUTE['rooms']
    assert ROUTE['schema_version'] == 1
    assert len(rooms) == 17
    visited = []
    room_id = 'act_02_blackout_street'
    while room_id is not None:
        assert room_id not in visited
        visited.append(room_id)
        info = rooms[room_id]
        room = Room.load_from_file(DATA / 'levels' / info['path'])
        assert room.room_id == room_id
        assert room.validate(campaign) == []
        assert info['act_id'] == room.act_id
        assert room.width_px == (480 if room_id == 'act_04_dodleston_relay' else 640 if room_id.endswith('_arena') else 960)
        target = info['next_room']
        if target is not None:
            assert rooms[target]['previous_room'] == room_id
        room_id = target
    assert set(visited) == set(rooms)
    assert visited[9:13] == ['act_04_rift_array', 'act_04_relay_approach', 'act_04_dodleston_relay', 'act_04_architect_arena']
    assert rooms['act_04_dodleston_relay']['milestones'][0]['x'] < 128


def test_walkable_floor_checkpoints_exits_and_encounter_placement(tmp_path):
    """Each new traversal room has continuous support and accepted finite spawns."""
    for room_id, info in ROUTE['rooms'].items():
        if room_id.endswith('_arena') or room_id == 'act_04_dodleston_relay':
            continue
        room = Room.load_from_file(DATA / 'levels' / info['path'])
        assert all(tile == 1 for tile in room.collision_grid[15])
        if room_id.startswith('act_05_'):
            # Low one-way steps admit movement in both directions at floor level.
            assert all(tile in (0, 2) for tile in room.collision_grid[13])
            assert all(tile == 0 for tile in room.collision_grid[14])
        else:
            assert all(tile == 0 for row in room.collision_grid[13:15] for tile in row)
        checkpoints = sorted(cp.x for cp in room.checkpoints)
        assert max(b-a for a, b in zip([0, *checkpoints], [*checkpoints, room.width_px])) <= 640
        assert {'default', 'from_east'} <= set(room.spawns)
        assert len(room.exits) == 2
        encounter_file = tmp_path / 'encounters.json'
        encounter_file.write_text(json.dumps({'schema_version': 1, 'rooms': {room_id: info['encounters']}}))
        director = ForwardEncounter(room, manager=None, data_path=encounter_file)
        assert len(director.entries) == len(info['encounters']) > 0, room_id


def test_earth_field_signals_are_clues_without_auto_grants():
    # Earlier Ohio contact remains available through its existing receiver;
    # later-world information is earned only after a guardian conversation.
    milestones = [m for info in ROUTE['rooms'].values() for m in info['milestones']]
    assert milestones
    assert all(m['events'] == [] for m in milestones)
    assert ROUTE['acts']['act_05']['boss_id'] == 'portal_warden'
    assert ROUTE['acts']['act_05']['complete_flag'] == 'portal_warden_defeated'


@pytest.mark.parametrize('act_id', ['act_02','act_03','act_04','act_05'])
def test_boss_completion_event_is_registered_and_idempotent(act_id):
    act = ROUTE['acts'][act_id]
    campaign = Campaign(save_id=f'connected_{act_id}')
    event = {'event_id': f'{act_id}_boss', 'type': act['boss_event'], 'payload': {}}
    assert campaign.apply_event(event)
    assert campaign.state.room_flags[act['complete_flag']]
    assert not campaign.apply_event(event)


def test_background_art_ranges_and_interior_overrides():
    expected = {
        'act_03_s4_hangar': 'area_51_hangar_v1',
        'act_03_telepod_vault': 'area_51_hangar_v1',
        'act_05_buried_archive': 'gobekli_archive_v1',
        'act_05_crust_waveguide': 'gobekli_archive_v1',
    }
    allowed = {'neo_denver_v1','area_51_v1','vla_rift_v1','gobekli_tepe_v1',*expected.values()}
    for room_id, info in ROUTE['rooms'].items():
        assert info['art_id'] in allowed
        if room_id in expected:
            assert info['art_id'] == expected[room_id]
        if 'art_view' in info:
            start, end = info['art_view']
            assert 0 <= start <= end <= 1
            assert start < end or room_id.endswith('_arena')
    assert all(info.get('art_view') == [0.5, 0.5] for room_id, info in ROUTE['rooms'].items() if room_id.endswith('_arena'))
    for ids in [
        ['act_02_blackout_street','act_02_relay_rooftops','act_02_amplifier_station'],
        ['act_04_rail_yard','act_04_rift_array','act_04_relay_approach'],
        ['act_03_s4_hangar','act_03_telepod_vault'],
        ['act_05_buried_archive','act_05_crust_waveguide'],
    ]:
        windows = [ROUTE['rooms'][room_id]['art_view'] for room_id in ids]
        assert windows[0][0] == 0 and windows[-1][1] == 1
        assert all(abs(a[1]-b[0]) < 0.00001 for a,b in zip(windows,windows[1:]))
