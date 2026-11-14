"""PURPOSE: Focused routed controls and temporary-save recovery for campaign worlds.
CALLED BY: pytest.
HOW TO MODIFY: Disclose fixture shortcuts; these checks are not a full playthrough.
"""
import pygame
import pytest

from video_game.engine import config
from video_game.engine.campaign_route import route_data, saved_route
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine


@pytest.fixture
def game(tmp_path, monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER', 'dummy')
    monkeypatch.setenv('SDL_AUDIODRIVER', 'dummy')
    pygame.init()
    pygame.display.set_mode((960, 540))
    machine = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(tmp_path),
                               settings_store=SettingsStore(tmp_path))
    assert machine.start_new_game()[0]
    yield machine
    machine.close()
    pygame.quit()


def key(machine, code):
    machine.input.begin_frame()
    machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=code))
    machine.update(1 / 60)
    machine.handle_event(pygame.event.Event(pygame.KEYUP, key=code))


def ohio_fixture(machine):
    assert machine.campaign.apply_event({'event_id': 'fixture_ohio', 'type': 'defeat_greenkeeper'})


def test_continue_resolves_checkpoint_from_the_old_long_corridor(game):
    from video_game.engine.campaign_route import store_route
    ohio_fixture(game)
    checkpoint = 'act_02_blackout_street_checkpoint_4'
    store_route(game.campaign, 'act_02_blackout_street', checkpoint)
    assert game.save_checkpoint()
    assert game.continue_game().status == 'ok'
    key(game, pygame.K_RETURN)
    scene = game.current_scene
    assert scene.room.room_id == 'act_02_blackout_street'
    assert scene.player.x == 640  # Formerly x=2560; the checkpoint ID still resolves.
    assert scene.room.width_px == 960
    assert not scene.room.check_rect_collision(scene.player.rect)['solid']


def dismiss_story(machine):
    for _ in range(10):
        scene = machine.current_scene
        if getattr(scene, 'destruction', None) and not scene.destruction.done:
            machine.update(3)
        if not getattr(scene, 'route_story', None) and not getattr(scene, 'is_defeated_sequence', False):
            return
        key(machine, pygame.K_RETURN)


def test_bunker_dispatch_checkpoint_resume_and_new_game(game):
    ohio_fixture(game)
    key(game, pygame.K_RETURN)
    scene = game.current_scene
    assert scene.room.room_id == 'act_02_blackout_street'
    dismiss_story(game)
    checkpoint = scene.room.checkpoints[1]
    scene.player.x, scene.player.y = checkpoint.x, checkpoint.y - 16
    game.update(1 / 60)
    assert saved_route(game.campaign)['checkpoint'] == checkpoint.id
    assert game.save_store.load().campaign.state.world_states['bunker_hub']['campaign_route']['checkpoint'] == checkpoint.id
    key(game, pygame.K_ESCAPE)
    key(game, pygame.K_RETURN)
    assert game.current_scene.room.room_id == 'act_02_blackout_street'
    assert game.current_scene.player.active_checkpoint_id == checkpoint.id
    assert game.continue_game().status == 'ok'
    assert game.current_state_name == config.STATE_BUNKER_HUB
    key(game, pygame.K_RETURN)
    assert game.current_scene.player.active_checkpoint_id == checkpoint.id
    assert game.start_new_game(replace_existing=True)[0]
    assert saved_route(game.campaign) == {}
    key(game, pygame.K_RETURN)
    assert game.current_scene.room.room_id == 'act_01_approach'


def test_actual_forward_exits_and_milestones(game):
    ohio_fixture(game)
    key(game, pygame.K_RETURN)
    dismiss_story(game)
    visited = []
    while game.current_state_name == config.STATE_FIELD_OPS:
        scene = game.current_scene
        visited.append(scene.room.room_id)
        meta = route_data()['rooms'][scene.room.room_id]
        for milestone in meta.get('milestones', []):
            scene.player.x = milestone['x'] - 7
            scene.player.y = 208
            game.update(1 / 60)
        next_id = meta['next_room']
        exit_ = next(ex for ex in scene.room.exits if ex.target_room == next_id)
        scene.player.x = exit_.x
        scene.player.y = exit_.y
        key(game, pygame.K_e)
    assert visited == ['act_02_blackout_street', 'act_02_relay_rooftops', 'act_02_amplifier_station']
    assert game.current_state_name == config.STATE_BOSS_BOUNTY
    assert game.current_scene.boss.target_id == 'synchronicity'
    # Earth clues do not grant alien messages before their guardian conversations.
    assert not {'FASR-003', 'FASR-004', 'FASR-005'} & set(game.campaign.state.extracted_fragments)
    assert game.save_store.load().campaign.state.extracted_fragments == game.campaign.state.extracted_fragments


def test_later_boss_retry_and_earned_next_sector(game):
    ohio_fixture(game)
    act = route_data()['acts']['act_02']
    game.change_state(config.STATE_BOSS_BOUNTY, room=act['boss_room'], boss_id=act['boss_id'],
                      campaign_act='act_02', spawn='boss_spawn')
    boss_scene = game.current_scene
    for _ in range(100):
        game.update(1 / 60)
    boss_scene.player.health = 0
    boss_scene.player.is_dead = True
    key(game, pygame.K_r)
    assert boss_scene.player.health > 0 and boss_scene.boss.health == boss_scene.boss.max_health
    # Fire through the actual input router; starting position is a combat fixture.
    boss_scene.player.x, boss_scene.player.y = 250, 208
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_x))
    for _ in range(1800):
        game.update(1 / 60)
        if boss_scene.is_defeated_sequence or boss_scene.player.is_dead:
            break
    game.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_x))
    assert boss_scene.is_defeated_sequence
    assert game.campaign.state.room_flags['synchronicity_defeated']
    dismiss_story(game)
    assert game.current_state_name == config.STATE_FIELD_OPS
    assert game.current_scene.room.room_id == 'act_03_salt_flats'
    assert game.save_store.load().campaign.state.room_flags['synchronicity_defeated']


@pytest.mark.parametrize('act_id,previous_events,expected_boss,next_room', [
    ('act_03', ['defeat_synchronicity'], 'amalgam', 'act_04_rail_yard'),
    ('act_04', ['defeat_synchronicity', 'defeat_amalgam'], 'architect', 'act_05_pillar_approach'),
    ('act_05', ['defeat_synchronicity', 'defeat_amalgam', 'defeat_architect'], 'portal_warden', 'alien_001_field'),
])
def test_other_bosses_accept_real_fire_and_unlock_route(game, act_id, previous_events, expected_boss, next_room):
    ohio_fixture(game)
    for i, event in enumerate(previous_events):
        game.campaign.apply_event({'event_id': f'prior_{i}', 'type': event})
    act = route_data()['acts'][act_id]
    game.change_state(config.STATE_BOSS_BOUNTY, room=act['boss_room'], boss_id=act['boss_id'],
                      campaign_act=act_id, spawn='boss_spawn')
    scene = game.current_scene
    assert scene.boss.target_id == expected_boss
    for _ in range(100):
        game.update(1 / 60)
    scene.player.x, scene.player.y = 250, 208
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_x))
    for _ in range(2400):
        game.update(1 / 60)
        if scene.is_defeated_sequence or scene.player.is_dead:
            break
    game.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_x))
    assert scene.is_defeated_sequence
    assert game.campaign.state.room_flags[act['complete_flag']]
    dismiss_story(game)
    if game.current_state_name == config.STATE_GALAXY_TRANSIT:
        # The Earth portal now begins a real timed world-to-world trip.
        from video_game.engine.scenes.galaxy_transit import TOTAL_SECONDS
        game.update(TOTAL_SECONDS + 0.1)
    if next_room:
        assert game.current_scene.room.room_id == next_room
    else:
        assert game.current_state_name == config.STATE_BUNKER_HUB


def test_failed_save_vetoes_forward_transition(game, monkeypatch):
    ohio_fixture(game)
    key(game, pygame.K_RETURN)
    dismiss_story(game)
    scene = game.current_scene
    next_id = route_data()['rooms'][scene.room.room_id]['next_room']
    exit_ = next(ex for ex in scene.room.exits if ex.target_room == next_id)
    scene.player.x, scene.player.y = exit_.x, exit_.y
    real_save = game.save_checkpoint
    monkeypatch.setattr(game, 'save_checkpoint', lambda: False)
    key(game, pygame.K_e)
    assert game.current_scene is scene and scene.room.room_id == 'act_02_blackout_street'
    monkeypatch.setattr(game, 'save_checkpoint', real_save)
    key(game, pygame.K_e)
    assert scene.room.room_id == next_id


def test_relay_side_passage_and_original_exit(game):
    ohio_fixture(game)
    for i, event in enumerate(('defeat_synchronicity', 'defeat_amalgam')):
        game.campaign.apply_event({'event_id': f'prior_{i}', 'type': event})
    game.change_state(config.STATE_FIELD_OPS, room='act_04/dodleston_relay.json',
                      spawn='relay_entrance', campaign_route=True)
    scene = game.current_scene
    assert any(ex.target_room == 'bunker_hub' for ex in scene.room.exits)
    passage = next(ex for ex in scene.room.exits if ex.id == 'campaign_passage')
    scene.player.x, scene.player.y = passage.x, passage.y
    key(game, pygame.K_UP)
    assert game.current_state_name == config.STATE_BOSS_BOUNTY
    assert game.current_scene.boss.target_id == 'architect'


def test_relay_is_crossable_from_entrance_with_held_right(game):
    ohio_fixture(game)
    for i, event in enumerate(('defeat_synchronicity', 'defeat_amalgam')):
        game.campaign.apply_event({'event_id': f'prior_{i}', 'type': event})
    game.change_settings(combat_mode='assisted')
    game.change_state(config.STATE_FIELD_OPS, room='act_04/dodleston_relay.json',
                      spawn='relay_entrance', campaign_route=True)
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
    for _ in range(100):
        game.update(1 / 60)
        if game.current_state_name == config.STATE_BOSS_BOUNTY:
            break
    assert game.current_state_name == config.STATE_BOSS_BOUNTY
    assert game.current_scene.player.x == 64
    assert game.current_scene.player.health == 100


def test_boss_arrival_accepts_movement_and_fire_immediately(game):
    ohio_fixture(game)
    act = route_data()['acts']['act_02']
    game.change_state(config.STATE_BOSS_BOUNTY, room=act['boss_room'], boss_id=act['boss_id'],
                      campaign_act='act_02', spawn='default')
    scene = game.current_scene
    assert scene.encounter_intro_remaining == 0
    assert scene.camera.x <= scene.player.x < scene.camera.x + scene.camera.viewport_w
    x, health = scene.player.x, scene.player.health
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
    game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(900, 250)))
    game.update(1 / 60)
    assert scene.player.x > x and scene.player.health == health
    assert scene.proj_mgr.projectiles
    assert game.input.held('move_right') and game.input.held('auto_fire')


def test_route_is_cached_and_rejects_escaping_paths(monkeypatch):
    import copy
    import json
    import video_game.engine.campaign_route as route
    data = copy.deepcopy(route.route_data())

    class FakePath:
        calls = 0
        def read_text(self, **kwargs):
            self.calls += 1
            return json.dumps(data)

    fake = FakePath()
    monkeypatch.setattr(route, 'ROUTE_PATH', fake)
    try:
        route.route_data.cache_clear()
        for _ in range(10):
            assert route.room_meta('act_02_blackout_street')
        assert fake.calls == 1
        data['rooms']['act_02_blackout_street']['path'] = '../../outside.json'
        route.route_data.cache_clear()
        assert route.route_data() == {'acts': {}, 'rooms': {}}
    finally:
        route.route_data.cache_clear()


def test_malformed_recovery_snapshot_is_ignored(game):
    ohio_fixture(game)
    game.campaign.store_world_state('bunker_hub', {'campaign_route': ['bad']})
    assert saved_route(game.campaign) == {}
    key(game, pygame.K_RETURN)
    assert game.current_scene.room.room_id == 'act_02_blackout_street'
