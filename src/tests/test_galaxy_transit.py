"""PURPOSE: Verify saved inter-world travel, mapped input and safe recovery.
CALLED BY: pytest and galaxy transit integration checks.
HOW TO MODIFY: Use temporary saves and retain ordered receipt and failure boundaries.
"""
import copy
import pygame
import pytest

from video_game.engine import config
from video_game.engine.alien_journey import journey_data, ledger, save_ledger, start_ledger
from video_game.engine.galaxy_transit import navigation_data, valid_pending, leg_position, leg_points, route_ids
from video_game.engine.scenes.galaxy_transit import TOTAL_SECONDS, MAP_SECONDS, MAP_AREA, VORTEX_CENTER
from video_game.engine.save_game import SaveError
from .test_campaign_world_route import game, key


def begin(game):
    # Explicit portal victory fixture, not an Earth playthrough.
    assert game.campaign.apply_event({'event_id': 'transit_portal_fixture', 'type': 'defeat_portal_warden'})
    assert game.save_checkpoint()
    key(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_GALAXY_TRANSIT


def complete_contact_fixture(game):
    """Fixture one defeated guardian, then use the actual contact UI."""
    assert game.campaign.apply_event({'event_id': 'fixture_guardian', 'type': 'defeat_guardian_008'})
    prior = {'version': 1, 'world_id': 'alien_008', 'stage': 'contact', 'checkpoint': None, 'receipts': []}
    save_ledger(game.campaign, prior)
    assert game.save_checkpoint()
    game.change_state(config.STATE_ALIEN_CONTACT, world_id='alien_008')
    key(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_GALAXY_TRANSIT


def test_all_eight_ordered_legs_and_schematic_locations():
    worlds = journey_data()['worlds']
    locations = navigation_data()['locations']
    assert len(locations) == 8
    assert {loc['id'] for loc in locations} == {'earth', *(w['id'] for w in worlds)}
    assert 'UNKNOWN' in next(loc['name'] for loc in locations if loc['id'] == 'alien_scan_h')
    assert 'EARTH MEMORY' in next(loc['name'] for loc in locations if loc['id'] == 'alien_010')
    assert valid_pending({'source': 'earth', 'destination': worlds[0]['id']}, worlds, [], 'field', worlds[0]['id'])
    receipts = []
    for index, world in enumerate(worlds):
        receipts.append(world['civ_id'])
        next_id = worlds[index + 1]['id'] if index + 1 < len(worlds) else 'earth'
        assert valid_pending({'source': world['id'], 'destination': next_id}, worlds, receipts,
                             'field' if next_id != 'earth' else 'final',
                             next_id if next_id != 'earth' else None)
        assert not valid_pending({'source': world['id'], 'destination': 'alien_008'}, worlds, receipts,
                                 'field' if next_id != 'earth' else 'final',
                                 next_id if next_id != 'earth' else None)


def test_automatic_phases_and_saved_arrival_do_not_repeat_on_continue(game):
    begin(game)
    scene = game.current_scene
    assert ledger(game.campaign)['pending_transit'] == {'source': 'earth', 'destination': 'alien_008'}
    assert game.save_store.load().campaign.state.world_states['bunker_hub']['alien_journey']['pending_transit'] == scene.pending
    assert scene.phase == 'map'
    game.update(MAP_SECONDS + .1); assert scene.phase == 'vortex'
    game.update(1.6); assert scene.phase == 'arrival'
    game.update(0.4)
    assert game.current_state_name == config.STATE_FIELD_OPS
    assert game.current_scene.room.room_id == 'alien_008_field'
    assert 'pending_transit' not in ledger(game.campaign)
    assert 'pending_transit' not in game.save_store.load().campaign.state.world_states['bunker_hub']['alien_journey']
    assert game.continue_game().status == 'ok'
    key(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_FIELD_OPS
    assert game.current_scene.room.room_id == 'alien_008_field'


def test_immediate_arrival_ignores_repeats_and_clears_controller_input(game):
    begin(game)
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, repeat=True))
    assert game.current_state_name == config.STATE_GALAXY_TRANSIT
    game.handle_event(pygame.event.Event(pygame.CONTROLLERBUTTONDOWN, button=pygame.CONTROLLER_BUTTON_A))
    assert game.current_state_name == config.STATE_FIELD_OPS
    assert not game.input.held('move_right') and not game.input.held('fire')


def test_pause_and_focus_loss_freeze_travel(game):
    begin(game)
    scene = game.current_scene
    game.update(0.9)
    before = scene.elapsed
    game.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
    assert game.pause.active
    game.update(5.0)
    assert scene.elapsed == before
    key(game, pygame.K_F2)
    assert not game.pause.active
    game.update(0.2)
    assert scene.elapsed > before


def test_pending_contact_leg_survives_continue_without_duplicate_receipt(game):
    begin(game); game.update(TOTAL_SECONDS + 0.1)
    complete_contact_fixture(game)
    expected = {'source': 'alien_008', 'destination': 'alien_009'}
    assert ledger(game.campaign)['pending_transit'] == expected
    assert ledger(game.campaign)['receipts'] == ['FASR-008']
    assert game.continue_game().status == 'ok'
    key(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_GALAXY_TRANSIT
    assert game.current_scene.pending == expected
    game.update(TOTAL_SECONDS + 0.1)
    assert game.current_scene.room.room_id == 'alien_009_field'
    assert ledger(game.campaign)['receipts'] == ['FASR-008']


def test_arrival_save_failure_retains_pending_and_retry_is_safe(game, monkeypatch):
    begin(game)
    saved_before = game.save_store.path.read_bytes()
    original = game.save_store.save
    def fail(*args, **kwargs):
        raise SaveError('transit fixture')
    monkeypatch.setattr(game.save_store, 'save', fail)
    key(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_GALAXY_TRANSIT
    assert game.current_scene.save_failed
    assert ledger(game.campaign)['pending_transit']['destination'] == 'alien_008'
    assert game.save_store.path.read_bytes() == saved_before
    monkeypatch.setattr(game.save_store, 'save', original)
    key(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_FIELD_OPS
    assert 'pending_transit' not in ledger(game.campaign)
    assert 'pending_transit' not in game.save_store.load().campaign.state.world_states['bunker_hub']['alien_journey']


def test_old_ledger_without_pending_resumes_directly(game):
    assert game.campaign.apply_event({'event_id':'old_portal', 'type':'defeat_portal_warden'})
    old = {'version':1, 'world_id':'alien_008', 'stage':'field', 'checkpoint':'default', 'receipts':[]}
    save_ledger(game.campaign, old)
    assert game.save_checkpoint()
    key(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_FIELD_OPS
    assert game.current_scene.room.room_id == 'alien_008_field'


def test_forged_leg_is_rejected_without_replacing_existing_snapshot(game):
    assert game.campaign.apply_event({'event_id':'forged_portal', 'type':'defeat_portal_warden'})
    raw = {'version':1, 'world_id':'alien_009', 'stage':'field', 'checkpoint':'default', 'receipts':[],
           'pending_transit':{'source':'earth','destination':'alien_009'}}
    save_ledger(game.campaign, raw)
    assert ledger(game.campaign) == {}
    assert start_ledger(game.campaign) == {}
    assert game.campaign.state.world_states['bunker_hub']['alien_journey'] == raw


def test_new_game_does_not_inherit_pending_leg(game):
    begin(game)
    assert ledger(game.campaign)['pending_transit']
    assert game.start_new_game(replace_existing=True)[0]
    assert ledger(game.campaign) == {}
    key(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_FIELD_OPS
    assert game.current_scene.room.room_id == 'act_01_approach'


def test_briefing_and_transit_share_every_curve_at_different_sizes():
    route = route_ids()
    for source, destination in zip(route, route[1:]):
        normalized = leg_points(source, destination, (0, 0, 1, 1))
        assert all(0 <= x <= 1 and 0 <= y <= 1 for x, y in normalized)
        for area in (MAP_AREA, (60, 78, 355, 64)):
            x, y, width, height = area
            expected = [(x + px * width, y + py * height) for px, py in normalized]
            for actual, point in zip(leg_points(source, destination, area), expected):
                assert actual == pytest.approx(point)
        for progress in (0, .1, .5, .9, 1):
            assert leg_points(source, destination, MAP_AREA, progress)[-1] == pytest.approx(leg_position(source, destination, MAP_AREA, progress))


def test_vortex_stays_centered_for_edge_destinations_and_return_to_earth(game):
    begin(game)
    scene = game.current_scene
    route = route_ids()
    assert scene.vortex_frames
    # These are display-only leg fixtures. Earned arrivals remain covered above.
    for source, destination in zip(route, route[1:]):
        scene.pending = {'source': source, 'destination': destination}
        for elapsed in (MAP_SECONDS + .05, 3.3, TOTAL_SECONDS - .01):
            scene.elapsed = elapsed
            game.render()
            pixels = pygame.surfarray.array3d(game.crt.render_surface)
            # Bright cyan gate pixels, excluding the caption bands.
            gate = (pixels[:, 114:430, 1] > 165) & (pixels[:, 114:430, 2] > 130) & (pixels[:, 114:430, 0] < 90)
            xs, ys = gate.nonzero()
            assert len(xs) > 50
            center = ((xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2 + 114)
            assert center == pytest.approx((2 * VORTEX_CENTER[0], 2 * VORTEX_CENTER[1]), abs=12)
            assert 114 < ys.min() + 114 < ys.max() + 114 < 430


def test_gate_render_uses_cached_frames_and_missing_art_still_arrives(game, monkeypatch):
    begin(game)
    scene = game.current_scene
    def unexpected(*args, **kwargs):
        raise AssertionError('Travel frame transformed or loaded during rendering')
    with monkeypatch.context() as rendering:
        rendering.setattr(pygame.transform, 'rotozoom', unexpected)
        rendering.setattr(pygame.image, 'load', unexpected)
        for elapsed in (MAP_SECONDS + .01, 3.1, 3.9):
            scene.elapsed = elapsed
            game.render()
    scene.assets = None
    scene.vortex_frames = []
    game.render()
    key(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_FIELD_OPS
    assert 'pending_transit' not in ledger(game.campaign)


@pytest.mark.parametrize('index', range(4))
@pytest.mark.parametrize('stage', ('field', 'guardian', 'contact'))
def test_saves_in_retired_worlds_resume_first_active_stop_without_granting_progress(game, index, stage):
    assert game.campaign.apply_event({'event_id': 'old_portal', 'type': 'defeat_portal_warden'})
    retired = journey_data()['retired_prefix']
    for previous in retired[:index]:
        assert game.campaign.apply_event({'event_id': previous['id'],
            'type': 'defeat_' + previous['defeat_flag'].removesuffix('_defeated')})
    old = {'version': 1, 'world_id': retired[index]['id'], 'stage': stage,
           'checkpoint': retired[index]['id'] + '_mid',
           'receipts': [w['civ_id'] for w in retired[:index]]}
    save_ledger(game.campaign, old)
    before = game.campaign.to_dict()
    current = ledger(game.campaign)
    assert current['world_id'] == journey_data()['worlds'][0]['id']
    assert current['stage'] == 'field' and current['checkpoint'] == 'default'
    assert current['receipts'] == []
    assert current['pending_transit'] == {'source': 'earth', 'destination': current['world_id']}
    assert game.campaign.to_dict() == before  # Reading the save never mutates it.
    assert not game.campaign.state.extracted_fragments
    key(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_GALAXY_TRANSIT
    key(game, pygame.K_RETURN)
    assert game.current_scene.room.room_id == current['world_id'] + '_field'
    saved = game.save_store.load().campaign.state.world_states['bunker_hub']['alien_journey']
    assert saved['world_id'] == current['world_id'] and saved['receipts'] == []
    assert 'pending_transit' not in saved


@pytest.mark.parametrize('completed', range(8))
def test_old_route_preserves_retained_victories_receipts_finale_and_return_leg(game, completed):
    assert game.campaign.apply_event({'event_id': 'old_portal', 'type': 'defeat_portal_warden'})
    retired, worlds = journey_data()['retired_prefix'], journey_data()['worlds']
    for world in retired + worlds[:completed]:
        assert game.campaign.apply_event({'event_id': world['id'],
            'type': 'defeat_' + world['defeat_flag'].removesuffix('_defeated')})
    destination = worlds[completed]['id'] if completed < len(worlds) else None
    old = {'version': 1, 'world_id': destination, 'stage': 'field' if destination else 'final',
           'checkpoint': 'default' if destination else None,
           'receipts': [w['civ_id'] for w in retired + worlds[:completed]],
           'pending_transit': {'source': (worlds[completed - 1] if completed else retired[-1])['id'],
                               'destination': destination or 'earth'}}
    save_ledger(game.campaign, old)
    current = ledger(game.campaign)
    assert current['receipts'] == [w['civ_id'] for w in worlds[:completed]]
    assert current['world_id'] == destination and current['stage'] == old['stage']
    assert current['pending_transit']['source'] == (worlds[completed - 1]['id'] if completed else 'earth')
    assert current['pending_transit']['destination'] == (destination or 'earth')


def test_retired_receipts_cannot_bypass_missing_retained_victories(game):
    worlds = journey_data()['retired_prefix'] + journey_data()['worlds']
    save_ledger(game.campaign, {'version': 1, 'world_id': None, 'stage': 'final',
                               'checkpoint': None, 'receipts': [w['civ_id'] for w in worlds]})
    assert ledger(game.campaign) == {}


def test_completed_legacy_save_keeps_its_park_page_and_both_form_victory(game):
    assert game.campaign.apply_event({'event_id': 'old_portal', 'type': 'defeat_portal_warden'})
    old_worlds = journey_data()['retired_prefix'] + journey_data()['worlds']
    for world in old_worlds:
        assert game.campaign.apply_event({'event_id': world['id'],
            'type': 'defeat_' + world['defeat_flag'].removesuffix('_defeated')})
    assert game.campaign.apply_event({'event_id': 'old_final', 'type': 'defeat_earth_ai'})
    save_ledger(game.campaign, {'version': 1, 'world_id': None, 'stage': 'complete',
        'checkpoint': None, 'receipts': [w['civ_id'] for w in old_worlds], 'restoration_page': 2})
    assert game.save_checkpoint()
    assert game.continue_game().status == 'ok'
    key(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_RESTORED_EARTH
    assert game.current_scene.page == 2
    assert ledger(game.campaign)['stage'] == 'complete'
    assert len(ledger(game.campaign)['receipts']) == 7
    assert game.campaign.state.room_flags['earth_ai_defeated']
