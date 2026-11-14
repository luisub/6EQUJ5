"""PURPOSE: Verify saved inter-world travel, mapped input and safe recovery.
CALLED BY: pytest and galaxy transit integration checks.
HOW TO MODIFY: Use temporary saves and retain ordered receipt and failure boundaries.
"""
import copy
import pygame
import pytest

from video_game.engine import config
from video_game.engine.alien_journey import journey_data, ledger, save_ledger, start_ledger
from video_game.engine.galaxy_transit import navigation_data, valid_pending
from video_game.engine.scenes.galaxy_transit import TOTAL_SECONDS
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
    assert game.campaign.apply_event({'event_id': 'fixture_guardian', 'type': 'defeat_guardian_001'})
    prior = {'version': 1, 'world_id': 'alien_001', 'stage': 'contact', 'checkpoint': None, 'receipts': []}
    save_ledger(game.campaign, prior)
    assert game.save_checkpoint()
    game.change_state(config.STATE_ALIEN_CONTACT, world_id='alien_001')
    key(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_GALAXY_TRANSIT


def test_all_twelve_ordered_legs_and_schematic_locations():
    worlds = journey_data()['worlds']
    locations = navigation_data()['locations']
    assert len(locations) == 12
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
        assert not valid_pending({'source': world['id'], 'destination': 'alien_001'}, worlds, receipts,
                                 'field' if next_id != 'earth' else 'final',
                                 next_id if next_id != 'earth' else None)


def test_automatic_phases_and_saved_arrival_do_not_repeat_on_continue(game):
    begin(game)
    scene = game.current_scene
    assert ledger(game.campaign)['pending_transit'] == {'source': 'earth', 'destination': 'alien_001'}
    assert game.save_store.load().campaign.state.world_states['bunker_hub']['alien_journey']['pending_transit'] == scene.pending
    assert scene.phase == 'map'
    game.update(2.6); assert scene.phase == 'vortex'
    game.update(1.2); assert scene.phase == 'arrival'
    game.update(0.4)
    assert game.current_state_name == config.STATE_FIELD_OPS
    assert game.current_scene.room.room_id == 'alien_001_field'
    assert 'pending_transit' not in ledger(game.campaign)
    assert 'pending_transit' not in game.save_store.load().campaign.state.world_states['bunker_hub']['alien_journey']
    assert game.continue_game().status == 'ok'
    key(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_FIELD_OPS
    assert game.current_scene.room.room_id == 'alien_001_field'


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
    expected = {'source': 'alien_001', 'destination': 'alien_003'}
    assert ledger(game.campaign)['pending_transit'] == expected
    assert ledger(game.campaign)['receipts'] == ['FASR-001']
    assert game.continue_game().status == 'ok'
    key(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_GALAXY_TRANSIT
    assert game.current_scene.pending == expected
    game.update(TOTAL_SECONDS + 0.1)
    assert game.current_scene.room.room_id == 'alien_003_field'
    assert ledger(game.campaign)['receipts'] == ['FASR-001']


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
    assert ledger(game.campaign)['pending_transit']['destination'] == 'alien_001'
    assert game.save_store.path.read_bytes() == saved_before
    monkeypatch.setattr(game.save_store, 'save', original)
    key(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_FIELD_OPS
    assert 'pending_transit' not in ledger(game.campaign)
    assert 'pending_transit' not in game.save_store.load().campaign.state.world_states['bunker_hub']['alien_journey']


def test_old_ledger_without_pending_resumes_directly(game):
    assert game.campaign.apply_event({'event_id':'old_portal', 'type':'defeat_portal_warden'})
    old = {'version':1, 'world_id':'alien_001', 'stage':'field', 'checkpoint':'default', 'receipts':[]}
    save_ledger(game.campaign, old)
    assert game.save_checkpoint()
    key(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_FIELD_OPS
    assert game.current_scene.room.room_id == 'alien_001_field'


def test_forged_leg_is_rejected_without_replacing_existing_snapshot(game):
    assert game.campaign.apply_event({'event_id':'forged_portal', 'type':'defeat_portal_warden'})
    raw = {'version':1, 'world_id':'alien_003', 'stage':'field', 'checkpoint':'default', 'receipts':[],
           'pending_transit':{'source':'earth','destination':'alien_003'}}
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
