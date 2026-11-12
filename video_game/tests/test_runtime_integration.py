"""PURPOSE: Verify milestone mechanics through the real router, keys and save store.
CALLED BY: pytest.
HOW TO MODIFY: Use fixtures only for starting prerequisites; execute behavior via scene events.
"""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame
import pytest
from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.campaign import Campaign


@pytest.fixture
def game(tmp_path, monkeypatch):
    monkeypatch.setenv('SIX_GAME_SAVE_DIR', str(tmp_path / 'save'))
    pygame.init()
    pygame.display.set_mode((480, 270))
    machine = GameStateMachine(CRTRenderer(), development=False)
    assert machine.start_new_game()[0]
    yield machine
    machine.close()


def key(game, code):
    game.input.begin_frame()
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=code))
    game.update(1/60)
    game.handle_event(pygame.event.Event(pygame.KEYUP, key=code))


def contact(game):
    game.change_state(config.STATE_CRT_TERMINAL)
    game.contact_session.is_offline = True
    game.handle_event(pygame.event.Event(pygame.TEXTINPUT, text='2'))
    key(game, pygame.K_RETURN)
    assert 'FASR-001' in game.campaign.state.extracted_fragments
    key(game, pygame.K_ESCAPE)


def test_all_eight_science_scenarios_with_keyboard(game):
    contact(game)
    game.change_state(config.STATE_SCIENCE_LAB)
    lab = game.current_scene
    for index in range(8):
        if index:
            key(game, pygame.K_TAB)
        wb = lab.workbench
        scenario = wb.active_scenario
        assert wb.current_step != 'COMPLETED', scenario['id']
        if wb.current_step == 'EXPERIMENT':
            for code in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_SPACE, pygame.K_RETURN):
                key(game, code)
            assert wb.current_step == 'CLAIM', (scenario['id'], wb.feedback_message)
        tier = scenario['claim']['correct_tier']
        key(game, {'established':pygame.K_1,'plausible':pygame.K_2,'speculative':pygame.K_3}[tier])
        assert wb.current_step == 'EVIDENCE'
        for n, observation in enumerate(scenario['evidence_pool']):
            if observation.get('is_valid', True):
                key(game, pygame.K_1 + n)
        key(game, pygame.K_RETURN)
        assert wb.current_step == 'REPLICATION', wb.feedback_message
        for n, check in enumerate(scenario['replication_checks']):
            key(game, pygame.K_1 + n)
            if wb.replication_answers[check['id']] != check['expected']:
                key(game, pygame.K_1 + n)
        key(game, pygame.K_RETURN)
        assert wb.current_step == 'DEPLOYMENT', wb.feedback_message
        key(game, pygame.K_1)
        assert wb.current_step == 'COMPLETED', wb.feedback_message
    assert len(game.campaign.state.validation_records) == 8
    notices = game.campaign.state.world_states['bunker_hub']['science_consequences']
    assert len(notices) == 8 and not any(n['delivered'] for n in notices.values())
    key(game, pygame.K_ESCAPE)
    notices = game.campaign.state.world_states['bunker_hub']['science_consequences']
    assert sum(n['delivered'] for n in notices.values()) == 1
    assert game.save_store.load().campaign.to_dict() == game.campaign.to_dict()


def enter_annex(game):
    # A completed Act I is a fixture prerequisite, not a claimed Act I playthrough.
    game.campaign.apply_event({'event_id':'fixture_boss','type':'defeat_greenkeeper'})
    key(game, pygame.K_m)
    field = game.current_scene
    assert field.room.room_id == 'act_01_mandela_test'
    return field


def test_reality_relay_save_reload_and_new_game_isolation(game):
    field = enter_annex(game)
    key(game, pygame.K_t)
    assert game.campaign.timeline_mode == field.room.active_timeline == '1977_ANALOG'
    key(game, pygame.K_t)
    assert game.campaign.timeline_mode == '2029_CORE'
    key(game, pygame.K_F6)
    assert field.room.room_id == 'act_04_dodleston_relay'
    assert field.room.get_tile(16, 13) == 1  # Closed bulkhead is actually solid.
    # Walk to relay from entrance with ordinary held movement.
    game.input.begin_frame()
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_d))
    for _ in range(30):
        game.input.begin_frame(); game.update(1/60)
    game.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_d))
    key(game, pygame.K_e)
    assert field.reality.panel_open
    key(game, pygame.K_2)  # wrong coolant choice
    assert field.reality.relay.puzzle_flags['pipe_ruptured']
    assert game.save_store.load().status == 'ok'
    key(game, pygame.K_r)  # recovery
    key(game, pygame.K_1)  # power
    key(game, pygame.K_1)  # cache
    assert field.reality.relay.puzzle_flags['dodleston_cassette_cached']
    assert field.room.get_tile(16, 13) == 0
    key(game, pygame.K_ESCAPE)  # close relay
    walk_to(game, 384)
    assert game.campaign.state.inventory['relay_cipher_cassette'] == 1
    key(game, pygame.K_ESCAPE)  # bunker
    assert game.continue_game().status == 'ok'
    key(game, pygame.K_m); key(game, pygame.K_F6)
    restored = game.current_scene
    assert restored.reality.relay.puzzle_flags['dodleston_cassette_cached']
    assert restored.reality.world.state.get_door_state('door_bulkhead_relay')['open']
    assert game.start_new_game(replace_existing=True)[0]
    field = game.scenes[config.STATE_FIELD_OPS]
    assert not field.player.arsenal.weapons['scattergun'].is_unlocked
    assert not game.campaign.state.extracted_fragments
    assert not game.campaign.state.contacted_civs
    assert not game.campaign.state.world_states


def test_input_pause_and_counterplay_have_runtime_callers(game):
    field = enter_annex(game)
    key(game, pygame.K_n)
    assert len(field.enemy_manager.enemies) == 2
    before = field.player.x
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_d))
    key(game, pygame.K_F2)
    assert not field.keys_held
    game.update(2)
    assert field.player.x == before
    game.pause.active = False
    game.campaign.apply_event({'event_id':'fixture_anchor','type':'complete_flashback_1977'})
    field.player.abilities.sync_unlocks(game.campaign)
    assert field.player.abilities.select_ability('serendipity_tape_deck')
    enemy = field.enemy_manager.enemies[0]
    enemy.telegraph_active = enemy.telegraph_locked = True
    key(game, pygame.K_k)
    assert not enemy.telegraph_locked
    assert enemy.has_status('prediction_shattered')
    key(game, pygame.K_LSHIFT)
    assert field.player.is_dashing


def test_old_campaign_snapshot_additive_migration_and_nonfinite_rejection():
    data = Campaign().to_dict(); data.pop('world_states')
    campaign = Campaign(data)
    assert campaign.state.world_states == {}
    before = campaign.to_dict()
    with pytest.raises(ValueError):
        campaign.store_world_state('act_01_mandela_test', {'x': float('nan')})
    assert campaign.to_dict() == before


def walk_to(game, target_x):
    field = game.current_scene
    code = pygame.K_d if field.player.x < target_x else pygame.K_a
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=code))
    for _ in range(1000):
        game.input.begin_frame(); game.update(1/60)
        if abs(field.player.x - target_x) < 3:
            break
    game.handle_event(pygame.event.Event(pygame.KEYUP, key=code))
    assert abs(field.player.x - target_x) < 4


def test_flashback_normal_keys_and_real_process_reload(game):
    import subprocess, sys, json
    enter_annex(game)
    key(game, pygame.K_F7)
    assert game.current_scene.flashback
    walk_to(game, 110)
    key(game, pygame.K_e); key(game, pygame.K_e)
    walk_to(game, 375)
    key(game, pygame.K_e); key(game, pygame.K_e)
    assert game.current_scene.room.room_id == 'act_01_mandela_test'
    assert game.current_scene.flashback is None
    assert game.campaign.state.inventory['reality_anchor_1977'] == 1
    assert game.save_checkpoint()
    result = subprocess.run([sys.executable, '-c',
        'import json; from video_game.engine.save_game import SaveStore; r=SaveStore().load(); assert r.status=="ok"; print(json.dumps(r.campaign.to_dict()))'],
        capture_output=True, text=True, check=True)
    restored = json.loads(result.stdout)
    assert restored['inventory']['reality_anchor_1977'] == 1
    assert restored['world_states'] == game.campaign.state.world_states


def test_grapple_and_pickup_remain_available_after_checkpoint(game):
    field = enter_annex(game)
    key(game, pygame.K_g)
    assert field.player.is_grappling
    # Exit grapple, use the timeline keyboard control, walk to the log.
    key(game, pygame.K_g)
    key(game, pygame.K_t)
    # Isolated contact with the pickup tests ownership, duplicate grant and persistence.
    field.player.x, field.player.y = 220, 208
    game.update(1/60)
    assert game.campaign.state.inventory['dossier_1977'] == 1
    key(game, pygame.K_t); key(game, pygame.K_t)
    assert game.campaign.state.inventory['dossier_1977'] == 1
    assert game.save_store.load().campaign.state.inventory['dossier_1977'] == 1


def test_dialogue_quota_can_recover_without_losing_evidence(game):
    contact(game)
    session = game.contact_session
    for _ in range(11):
        assert session.send_message('1')
    assert not session.send_message('2')
    assert session.send_message('/choices')
    assert session.send_message('/restart')
    assert session.send_message('2')
    assert game.campaign.state.extracted_fragments.count('FASR-001') == 1


def test_boss_input_mapping_and_defeat_wait_for_explicit_retry(game):
    game.change_state(config.STATE_BOSS_BOUNTY)
    boss_scene = game.current_scene
    start = boss_scene.player.x
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_d))
    for _ in range(20):
        game.input.begin_frame(); game.update(1/60)
    assert boss_scene.player.x > start
    game.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_d))
    boss_scene.player.take_damage(10000, ignore_invulnerable=True)
    game.update(1/60)
    assert boss_scene.player.is_dead
    key(game, pygame.K_r)
    assert not boss_scene.player.is_dead
    assert boss_scene.boss.current_phase == 1


def test_full_lab_prompt_overlay_and_delayed_notice(game):
    contact(game)
    game.change_state(config.STATE_SCIENCE_LAB)
    lab = game.current_scene
    key(game, pygame.K_h)
    assert lab.details_open
    assert ' '.join(lab.get_details_lines()).find('Apparatus outputs continuous') >= 0
    key(game, pygame.K_PAGEDOWN)
    assert lab.details_offset > 0
    key(game, pygame.K_h)
    assert not lab.details_open


def test_relay_rejects_geometry_edit_with_no_safe_displacement(game):
    from copy import deepcopy
    from types import SimpleNamespace
    from video_game.engine.mandela_world import MandelaWorld
    from video_game.engine.temporal_relay import TemporalRelay
    from video_game.engine.world import Room
    room = Room.load_from_file(config.DATA_DIR / 'levels/act_04/dodleston_relay.json')
    world = MandelaWorld(room)
    relay = TemporalRelay(game.campaign)
    actor = SimpleNamespace(x=0., y=0., rect=pygame.Rect(0, 0, room.width_px, room.height_px))
    before = deepcopy(room.collision_grid)
    campaign_before = game.campaign.to_dict()
    ok, message = relay.apply_action('action_open_cistern_flood', world, actor)
    assert not ok and 'BLOCKED' in message
    assert room.collision_grid == before
    assert game.campaign.to_dict() == campaign_before


def test_moving_platform_catches_falling_player(game):
    from video_game.engine.mandela_world import MandelaWorld
    from video_game.engine.world import Room
    from video_game.engine.player import Player
    room = Room.load_from_file(config.DATA_DIR / 'levels/act_01/mandela_test.json')
    world = MandelaWorld(room)
    player = Player(208., 130.)
    player.vy = 100
    world.update(0.05, player)
    assert player.is_grounded
    assert player.y == pytest.approx(128.)


def test_all_faction_pairs_are_reachable_and_bounded(game):
    field = enter_annex(game)
    observed = set()
    for _ in range(4):
        key(game, pygame.K_n)
        assert len(field.enemy_manager.enemies) == 2
        observed.update(type(e).__name__ for e in field.enemy_manager.enemies)
        for _ in range(10):
            game.input.begin_frame(); game.update(1/60)
    assert observed == {'CoreEnforcer', 'CoreOperative', 'ShieldHound', 'PhaseWatcher',
                        'ChrysalisSplicer', 'PrecursorGuardian', 'TemporalPhantom', 'CoreReconDrone'}


def test_dash_damage_has_live_enemy_manager_caller(game):
    from video_game.engine.enemies import CoreReconDrone
    field = enter_annex(game)
    target = CoreReconDrone('dash_target', 80., 208.)
    field.enemy_manager.clear(); field.enemy_manager.add_enemy(target)
    field.player.is_dashing = True
    field.player.dash_sweep_rect = target.rect.copy()
    before = target.health
    field.enemy_manager.update(0.001, field.player, field.room)
    assert target.health < before
    once = target.health
    field.enemy_manager.update(0.001, field.player, field.room)
    assert target.health == once
