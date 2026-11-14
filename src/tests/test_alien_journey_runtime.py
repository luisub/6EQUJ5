"""PURPOSE: Exercise the new journey through routed inputs and isolated saves.
CALLED BY: pytest.
HOW TO MODIFY: Declare setup fixtures and never present them as a full playthrough.
"""
import copy
import pygame
import pytest
from video_game.engine import config
from video_game.engine.alien_journey import journey_data, ledger, save_ledger
from video_game.engine.save_game import SaveError
from video_game.engine.scenes.galaxy_transit import TOTAL_SECONDS
from .test_campaign_world_route import game, key


def portal_fixture(game):
    assert game.campaign.apply_event({'event_id': 'fixture_portal', 'type': 'defeat_portal_warden'})
    assert game.save_checkpoint()


def finish_travel(game):
    assert game.current_state_name == config.STATE_GALAXY_TRANSIT
    game.update(TOTAL_SECONDS + 0.1)


def enter_first_guardian(game, *, acknowledge=True):
    portal_fixture(game)
    key(game, pygame.K_RETURN)
    finish_travel(game)
    field = game.current_scene
    world = journey_data()['worlds'][0]
    assert field.room.room_id == 'alien_001_field'
    exit_ = next(e for e in field.room.exits if e.target_room == 'alien_001_arena')
    field.player.x, field.player.y = exit_.x, exit_.y
    key(game, pygame.K_e)
    assert game.current_state_name == config.STATE_BOSS_BOUNTY
    scene = game.current_scene
    for _ in range(100):
        game.update(1/60)
    scene.player.x, scene.player.y = 250, 208
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_x))
    for _ in range(2400):
        game.update(1/60)
        if game.current_state_name != config.STATE_BOSS_BOUNTY or scene.is_defeated_sequence or scene.player.is_dead:
            break
    game.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_x))
    assert scene.is_defeated_sequence and scene.boss.is_defeated
    if acknowledge:
        game.update(3)
        key(game, pygame.K_RETURN)
    return world, scene


def test_guardian_then_conversation_then_teleport(game):
    world, _ = enter_first_guardian(game)
    assert game.current_state_name == config.STATE_ALIEN_CONTACT
    assert game.campaign.state.room_flags[world['defeat_flag']]
    assert ledger(game.campaign)['stage'] == 'contact'
    assert ledger(game.campaign)['receipts'] == []
    pages = len(world['contact_pages'])
    for _ in range(pages):
        key(game, pygame.K_RETURN)
    assert ledger(game.campaign)['receipts'] == ['FASR-001']
    assert 'FASR-001' in game.campaign.state.extracted_fragments
    finish_travel(game)
    assert game.current_state_name == config.STATE_FIELD_OPS
    assert game.current_scene.room.room_id == 'alien_003_field'
    assert game.save_store.load().campaign.state.world_states['bunker_hub']['alien_journey']['receipts'] == ['FASR-001']


def test_continue_resumes_pending_conversation(game):
    enter_first_guardian(game)
    assert game.continue_game().status == 'ok'
    assert game.current_state_name == config.STATE_BUNKER_HUB
    key(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_ALIEN_CONTACT
    assert ledger(game.campaign)['receipts'] == []


def test_final_page_failed_save_blocks_teleport_and_retry_is_idempotent(game, monkeypatch):
    world, _ = enter_first_guardian(game)
    for _ in range(len(world['contact_pages']) - 1):
        key(game, pygame.K_RETURN)
    original = game.save_store.save
    def fail(*args, **kwargs):
        raise SaveError('fixture failure')
    monkeypatch.setattr(game.save_store, 'save', fail)
    key(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_ALIEN_CONTACT
    assert game.current_scene.save_pending
    before = copy.deepcopy(game.campaign.to_dict())
    key(game, pygame.K_RETURN)
    assert game.campaign.to_dict() == before
    monkeypatch.setattr(game.save_store, 'save', original)
    key(game, pygame.K_F5)
    finish_travel(game)
    assert game.current_state_name == config.STATE_FIELD_OPS
    assert ledger(game.campaign)['receipts'] == ['FASR-001']


def test_old_fragments_and_legacy_final_flag_cannot_unlock_final_ai(game):
    portal_fixture(game)
    game.campaign.apply_event({'event_id':'old_core_fixture', 'type':'defeat_core_prime'})
    game.campaign.apply_event({'event_id':'old_contact_fixture', 'type':'record_contact',
                               'payload':{'civilization_id':'FASR-001'}})
    game.campaign.apply_event({'event_id':'old_fragment_fixture', 'type':'grant_fragment_fasr_001'})
    final = journey_data()['final_earth']
    game.change_state(config.STATE_BOSS_BOUNTY, room=final['arena_room'],
                      boss_id=final['boss_id'], journey_final=True)
    assert game.current_state_name == config.STATE_BUNKER_HUB
    assert not game.campaign.state.room_flags.get('earth_ai_defeated', False)
    key(game, pygame.K_RETURN)
    finish_travel(game)
    assert game.current_scene.room.room_id == 'alien_001_field'
    assert ledger(game.campaign)['receipts'] == []


def test_final_page_waits_for_acknowledgement_and_pause(game):
    world, _ = enter_first_guardian(game)
    contact = game.current_scene
    game.open_pause()
    game.update(60)
    assert contact.page == 0 and ledger(game.campaign)['receipts'] == []
    game.pause.active = False
    for _ in range(len(world['contact_pages']) - 1):
        key(game, pygame.K_RETURN)
    game.update(30)
    assert game.current_state_name == config.STATE_ALIEN_CONTACT
    assert ledger(game.campaign)['receipts'] == []
    game.handle_event(pygame.event.Event(pygame.CONTROLLERBUTTONDOWN, button=pygame.CONTROLLER_BUTTON_A))
    finish_travel(game)
    assert game.current_state_name == config.STATE_FIELD_OPS
    assert ledger(game.campaign)['receipts'] == ['FASR-001']


def test_final_ai_requires_all_guardians_and_receipts_then_plays_epilogue(game):
    portal_fixture(game)
    worlds = journey_data()['worlds']
    # Explicit fixture: prepare the post-conversation ledger; this is not a journey playthrough.
    for index, world in enumerate(worlds):
        game.campaign.apply_event({'event_id': f'fixture_guardian_{index}', 'type': world['defeat_event']})
    value = {'version': 1, 'world_id': None, 'stage': 'final', 'checkpoint': None,
             'receipts': [world['civ_id'] for world in worlds]}
    save_ledger(game.campaign, value)
    key(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_BOSS_BOUNTY
    scene = game.current_scene
    for _ in range(100):
        game.update(1/60)
    scene.player.x, scene.player.y = 250, 208
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_x))
    saw_archon = False
    for _ in range(2400):
        game.update(1/60)
        if scene.boss.final_stage == 2 and not saw_archon:
            saw_archon = True
            assert scene.boss.health == scene.boss.max_health
            assert scene.boss.title == 'ARCHON OF SILENCE'
            assert not game.campaign.state.room_flags.get('earth_ai_defeated', False)
        if scene.is_defeated_sequence or scene.player.is_dead:
            break
    game.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_x))
    assert saw_archon and scene.is_defeated_sequence
    assert game.campaign.state.room_flags['earth_ai_defeated']
    assert ledger(game.campaign)['stage'] == 'final'  # Epilogue has not finished.
    game.update(30)  # Destruction completes, but the ending must wait for input.
    assert game.current_scene is scene and scene.story.index == 0
    for _ in scene.story.pages:
        key(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_TITLE_BOOT
    assert ledger(game.campaign)['stage'] == 'complete'
    assert game.save_store.load().campaign.state.room_flags['earth_ai_defeated']


def test_teleport_waits_through_pause_and_ignores_inputs(game):
    world, _ = enter_first_guardian(game)
    for _ in world['contact_pages']:
        key(game, pygame.K_RETURN)
    transit = game.current_scene
    assert game.current_state_name == config.STATE_GALAXY_TRANSIT
    game.open_pause()
    elapsed = transit.elapsed
    game.update(2.0)
    assert transit.elapsed == elapsed
    game.pause.active = False
    key(game, pygame.K_ESCAPE)
    assert game.current_state_name == config.STATE_GALAXY_TRANSIT
    game.update(TOTAL_SECONDS + 0.1)
    assert game.current_scene.room.room_id == 'alien_003_field'


def test_continue_mid_teleport_resumes_saved_destination(game):
    world, _ = enter_first_guardian(game)
    for _ in world['contact_pages']:
        key(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_GALAXY_TRANSIT
    assert game.continue_game().status == 'ok'
    assert game.current_state_name == config.STATE_BUNKER_HUB
    key(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_GALAXY_TRANSIT
    game.update(TOTAL_SECONDS + 0.1)
    assert game.current_scene.room.room_id == 'alien_003_field'
    assert ledger(game.campaign)['receipts'] == ['FASR-001']


def test_world_and_arena_scenery_resolve_authored_art(game):
    portal_fixture(game)
    key(game, pygame.K_RETURN)
    finish_travel(game)
    field = game.current_scene
    assert field.campaign_scenery.background_source == {'kind': 'native', 'art_id': 'realm_fasr_001_v1'}
    game.render()
    exit_ = next(e for e in field.room.exits if e.target_room == 'alien_001_arena')
    field.player.x, field.player.y = exit_.x, exit_.y
    key(game, pygame.K_e)
    arena = game.current_scene
    assert arena.campaign_scenery.background_source == {'kind': 'native', 'art_id': 'realm_fasr_001_v1'}
    assert arena.boss.art_surface is not None
    game.render()


def test_next_world_and_proxima_use_native_landscapes(game):
    from types import SimpleNamespace
    from video_game.engine.campaign_scenery import CampaignScenery, load_campaign_background
    world, _ = enter_first_guardian(game)
    for _ in world['contact_pages']:
        key(game, pygame.K_RETURN)
    finish_travel(game)
    scene = game.current_scene
    assert scene.room.room_id == 'alien_003_field'
    root = game.assets.root
    assert load_campaign_background(root, 'realm_fasr_003_v1') is not None
    assert scene.campaign_scenery.background_source == {'kind':'native', 'art_id':'realm_fasr_003_v1'}
    game.render()
    assert load_campaign_background(root, 'realm_fasr_005_v1') is not None
    later = CampaignScenery(root, SimpleNamespace(act_id='act_05', room_id='alien_005_field', width_px=3840),
                            {'art_id':'realm_fasr_005_v1'})
    assert later.background_source == {'kind':'native', 'art_id':'realm_fasr_005_v1'}


def test_earned_journey_objective_overrides_missing_ohio_signal(game):
    from video_game.engine.objectives import ObjectiveTracker
    portal_fixture(game)
    assert 'FASR-001' not in game.campaign.state.extracted_fragments
    assert not game.campaign.state.validation_records
    key(game, pygame.K_RETURN)
    objective = ObjectiveTracker().get_active_objective(game.campaign)
    assert (objective.id, objective.title) == ('obj_alien_world', 'REACH FASR-001')
    assert not game.campaign.state.extracted_fragments
    assert not game.campaign.state.validation_records


def test_earned_earth_progress_overrides_missing_opening_signal(game):
    from video_game.engine.objectives import ObjectiveTracker
    game.campaign.apply_event({'event_id': 'fixture_defense', 'type': 'complete_dish_defense'})
    objective = ObjectiveTracker().get_active_objective(game.campaign)
    assert objective.id == 'obj_defeat_greenkeeper'
    game.campaign.apply_event({'event_id': 'fixture_ohio', 'type': 'defeat_greenkeeper'})
    objective = ObjectiveTracker().get_active_objective(game.campaign)
    assert objective.id == 'obj_act_02'
    assert not game.campaign.state.extracted_fragments
    assert not game.campaign.state.validation_records


def test_immediate_boss_arrival_has_no_false_attack_alerts(game, monkeypatch):
    from video_game.engine.bosses.base import STATE_ATTACK, STATE_TELEGRAPH, BossAttackTelegraph
    portal_fixture(game)
    key(game, pygame.K_RETURN)
    finish_travel(game)
    scene = game.current_scene
    exit_ = next(e for e in scene.room.exits if e.target_room == 'alien_001_arena')
    scene.player.x, scene.player.y = exit_.x, exit_.y
    key(game, pygame.K_e)
    scene = game.current_scene
    drawn = []
    original = game.crt.draw_text
    def capture(text, *args, **kwargs):
        drawn.append(text)
        return original(text, *args, **kwargs)
    monkeypatch.setattr(game.crt, 'draw_text', capture)
    game.render()
    assert 'SECTOR BOSS APPROACHING' not in drawn
    assert any(scene.boss.title in text for text in drawn)
    assert not any('LOCK-ON' in text or 'TARGETED' in text for text in drawn)
    assert any('VULNERABLE' in text for text in drawn) == scene.boss.weak_point_exposed
    assert scene._active_threat() is None
    scene.boss.phase_state = STATE_TELEGRAPH
    scene.boss.telegraphs.append(BossAttackTelegraph('fixture', 1.0))
    assert scene._active_threat() == 'AIMING'
    scene.boss.telegraphs.clear()
    scene.boss.phase_state = STATE_ATTACK
    assert scene._active_threat() == 'LOCKED'


def test_valid_journey_ledger_precedes_all_legacy_objectives(game):
    from video_game.engine.objectives import ObjectiveTracker
    # Explicit persisted-ledger fixture isolates the objective selection contract.
    save_ledger(game.campaign, {'version': 1, 'world_id': 'alien_001', 'stage': 'field',
                                'checkpoint': 'default', 'receipts': []})
    objective = ObjectiveTracker().get_active_objective(game.campaign)
    assert (objective.id, objective.title) == ('obj_alien_world', 'REACH FASR-001')
    assert not game.campaign.state.extracted_fragments
    assert not game.campaign.state.room_flags.get('portal_warden_defeated', False)
