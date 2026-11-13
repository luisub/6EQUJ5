"""PURPOSE: Validate the authored alien-world route and its content registries.
CALLED BY: pytest and alien-journey content verification.
HOW TO MODIFY: Check usable geometry, coherent route IDs and distinct story/event ownership.
"""

from video_game.engine import config
import json
from pathlib import Path

from video_game.engine.campaign import Campaign, load_campaign_data
from video_game.engine.encounter_director import ForwardEncounter
from video_game.engine.world import COLLISION_EMPTY, COLLISION_ONE_WAY, COLLISION_SOLID, Room

DATA = config.DATA_DIR
JOURNEY = json.loads((DATA / 'alien_journey.json').read_text())


def test_all_civilizations_have_ordered_worlds_portraits_and_registry():
    worlds = JOURNEY['worlds']
    assert [w['civ_id'] for w in worlds] == [
        'FASR-001','FASR-003','FASR-005','FASR-004','FASR-008','FASR-009',
        'FASR-006','FASR-002','FASR-SCAN-H','FASR-010','FASR-007']
    assert len(JOURNEY['rooms']) == 23
    assert len({world['guardian_title'] for world in worlds}) == 11
    for i, world in enumerate(worlds):
        assert world['next_world'] == (worlds[i+1]['id'] if i+1 < len(worlds) else None)
        assert len(world['contact_pages']) == 2
        assert len({page['title'] for page in world['contact_pages']}) == 2
        assert all(1 <= len(page['title'].strip()) <= 60 for page in world['contact_pages'])
        assert all(len(page['text'].split()) <= 45 for page in world['contact_pages'])
        assert (DATA.parent / 'assets' / world['portrait']).is_file()
        for key in ('field_room','arena_room'):
            path = world[key]
            assert (DATA / 'levels' / path).is_file()
            room_id = Path(path).stem
            assert JOURNEY['rooms'][room_id]['path'] == path
    assert JOURNEY['final_earth']['arena_room'] == 'earth_finale/core_prime_arena.json'
    assert 'archive' in worlds[6]['world_brief'].lower() or 'memorial' in worlds[6]['world_brief'].lower()
    assert 'terrestrial' in worlds[9]['world_brief'].lower()


def test_alien_room_geometry_links_and_encounter_positions(tmp_path):
    campaign = load_campaign_data()
    for rid, info in JOURNEY['rooms'].items():
        room = Room.load_from_file(DATA / 'levels' / info['path'])
        assert room.room_id == rid and room.validate(campaign) == []
        arena = rid.endswith('_arena')
        assert room.width_px == (640 if arena else 3840)
        if arena:
            assert info['encounters'] == []
            continue
        assert all(tile == COLLISION_SOLID for tile in room.collision_grid[15])
        # One-way steps are passable from below; solid and hazard tiles are not.
        assert all(tile in (COLLISION_EMPTY, COLLISION_ONE_WAY)
                   for row in room.collision_grid[13:15] for tile in row)
        xs = sorted(cp.x for cp in room.checkpoints)
        assert max(b-a for a,b in zip([0,*xs],[*xs,room.width_px])) <= 640
        path = tmp_path / 'encounters.json'
        path.write_text(json.dumps({'schema_version':1,'rooms':{rid:info['encounters']}}))
        assert len(ForwardEncounter(room,manager=None,data_path=path).entries) == len(info['encounters']) > 0


def test_guardian_and_final_events_have_separate_flags_from_legacy_finale():
    data = load_campaign_data()
    for world in JOURNEY['worlds']:
        campaign = Campaign(data=data, save_id=world['id'])
        assert campaign.apply_event({'event_id':'guardian_test','type':world['defeat_event']})
        assert campaign.state.room_flags[world['defeat_flag']]
        assert not campaign.state.extracted_fragments
        assert not campaign.state.validation_records
    assert 'core_prime_defeated' in data['flag_ids']
    assert JOURNEY['final_earth']['defeat_flag'] == 'earth_ai_defeated'
    assert JOURNEY['final_earth']['defeat_event'] != 'defeat_core_prime'
