"""PURPOSE: Verify forward handoff, story gates, retry and art aliases.
CALLED BY: pytest tests/test_forward_flow.py.
HOW TO MODIFY: Keep routed input and explicit fixture disclosures.
Positions and campaign events below are fixtures, not a playthrough.
"""
import shutil
from pathlib import Path

import pygame
import pytest

from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.native_room_assets import load_native_room_family
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
    pygame.display.set_mode((machine.crt.win_w, machine.crt.win_h))
    assert machine.start_new_game()[0]
    machine.change_settings(combat_mode='assisted')
    machine.change_state(config.STATE_FIELD_OPS, room='act_01/approach.json', spawn='dish_perimeter')
    yield machine
    machine.close()
    pygame.quit()


def event(game, event):
    game.handle_event(event)


def place_at_exit(field, target):
    exit = next(e for e in field.room.exits if e.target_room == target)
    field.player.x = exit.rect.left
    field.player.y = exit.rect.bottom - field.player.height
    field.player.rect.topleft = (field.player.x, field.player.y)
    field.player.vx = field.player.vy = 0


def step(game, count=1):
    for _ in range(count):
        game.input.begin_frame()
        game.update(1 / 60)


def test_held_right_and_mouse_fire_cross_forward_boundary(game):
    field = game.current_scene
    place_at_exit(field, 'act_01_ohio_campus')
    event(game, pygame.event.Event(pygame.MOUSEMOTION, pos=(800, 250), rel=(0, 0), buttons=(0, 0, 0)))
    event(game, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(800, 250)))
    event(game, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
    step(game)
    assert field.room.room_id == 'act_01_ohio_campus'
    assert game.input.held('move_right') and game.input.held('auto_fire')
    x = field.player.x
    step(game, 60)
    assert field.player.x > x
    assert field.projectile_manager.projectiles or any(e.is_dead for e in field.enemy_manager.enemies)
    event(game, pygame.event.Event(pygame.KEYUP, key=pygame.K_RIGHT))
    event(game, pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(800, 250)))
    assert not game.input.held('move_right') and not game.input.held('auto_fire')


@pytest.mark.parametrize('mode', ['classic', 'assisted'])
def test_walk_connections_work_both_ways_and_preserve_health(game, mode):
    field = game.current_scene
    game.change_settings(combat_mode=mode)
    field.player.health = 73
    place_at_exit(field, 'act_01_ohio_campus')
    event(game, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
    step(game)
    assert field.room.room_id == 'act_01_ohio_campus'
    assert field.player.health == 73
    assert game.input.held('move_right')
    assert not game.input.pressed('jump')
    event(game, pygame.event.Event(pygame.KEYUP, key=pygame.K_RIGHT))
    place_at_exit(field, 'act_01_approach')
    step(game, 2)
    assert field.room.room_id == 'act_01_ohio_campus'  # Standing at an edge is safe.
    event(game, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT))
    step(game)
    assert field.room.room_id == 'act_01_approach'
    assert field.player.health == 73 and game.input.held('move_left')
    x = field.player.x
    step(game, 5)
    assert field.player.x < x
    event(game, pygame.event.Event(pygame.KEYUP, key=pygame.K_LEFT))
    assert not game.input.held('move_left')


def test_story_gates_and_pause(game):
    field = game.current_scene
    field.load_room('act_01/dish_service.json', 'east')
    place_at_exit(field, 'act_01_dish_catwalk')
    event(game, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
    step(game, 5)
    assert field.room.room_id == 'act_01_dish_service'
    game.campaign.apply_event({'event_id': 'fixture_coupler', 'type': 'collect_analog_coupler'})
    game.open_pause(); step(game, 5)
    assert field.room.room_id == 'act_01_dish_service'
    game.pause.close()
    event(game, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
    step(game)
    assert field.room.room_id == 'act_01_dish_catwalk'
    place_at_exit(field, 'act_01_greenkeeper_arena')
    step(game, 5)
    assert field.room.room_id == 'act_01_dish_catwalk'
    event(game, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP))
    assert field.room.room_id == 'act_01_dish_catwalk'


def test_old_campus_checkpoint_resolves_inside_shortened_room(game):
    field = game.current_scene
    field.load_room('act_01/ohio_campus.json', 'ohio_campus_extension_10')
    assert 0 <= field.player.x <= field.room.width_px - field.player.width
    assert field.player.x == 1200
    assert not field.room.check_rect_collision(field.player.rect)['solid']


@pytest.mark.parametrize('alias,family,size', [
    ('act_01_perimeter_road', 'ohio_approach_v2', (960, 288)),
    ('act_01_salvage_outer', 'ohio_salvage_v1', (640, 288)),
    ('act_01_salvage_runoff', 'ohio_salvage_v1', (640, 288)),
    ('act_01_dish_service', 'ohio_dish_v1', (640, 288)),
    ('act_01_dish_return', 'ohio_dish_v1', (640, 288)),
])
def test_alias_exact_size_and_complete_family(game, tmp_path, alias, family, size):
    source = config.ASSETS_DIR / 'environments' / family
    root = tmp_path / 'assets'
    shutil.copytree(source, root / 'environments' / family)
    assert load_native_room_family(root, alias, size) is not None
    assert load_native_room_family(root, alias, (size[0] + 1, size[1])) is None
    manifest = root / 'environments' / family / 'manifest.json'
    manifest.write_text('{}')
    assert load_native_room_family(root, alias, size) is None


@pytest.mark.parametrize('method', ['space', 'click'])
def test_failed_defense_retry_uses_fresh_input_without_fire_or_jump(game, method):
    field = game.current_scene
    game.campaign.apply_event({'event_id': 'fixture_retry_coupler', 'type': 'collect_analog_coupler'})
    game.campaign.apply_event({'event_id': 'fixture_retry_repair', 'type': 'repair_dish_feedhorn'})
    field.load_room('act_01/dish_catwalk.json', 'catwalk_start')
    assert field.holdout.is_active
    field.holdout.fail('fixture failure')
    assert field._context_label() == 'SPACE / CLICK: RETRY'
    game.open_pause()
    if method == 'space':
        event(game, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
    else:
        pos = (round(220 * game.crt.win_w / 480), round(213 * game.crt.win_h / 270))
        event(game, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
    assert field.holdout.is_failed
    game.pause.close()
    game.input.release_all()
    if method == 'space':
        event(game, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
    else:
        event(game, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
    assert field.holdout.is_active
    assert not game.input.held('jump') and not game.input.held('auto_fire')
    assert not game.input.pressed('cycle_ability')
    step(game)
    assert not field.projectile_manager.projectiles
    assert not field._jump_pressed
    if method == 'space':
        event(game, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE, repeat=True))
        step(game)
        assert not game.input.held('jump') and not field._jump_pressed
        event(game, pygame.event.Event(pygame.KEYUP, key=pygame.K_SPACE))


def test_yard_coupler_gate_throttles_and_allows_earned_and_repaired(game, monkeypatch):
    field = game.current_scene
    field.load_room('act_01/salvage_yard.json', 'yard_entrance')
    place_at_exit(field, 'act_01_dish_catwalk')
    notices = []
    post = field.objective_tracker.post_notification
    def record(*args, **kwargs):
        notices.append(kwargs.get('title', args[0] if args else None))
        return post(*args, **kwargs)
    monkeypatch.setattr(field.objective_tracker, 'post_notification', record)
    event(game, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
    step(game, 60)
    assert field.room.room_id == 'act_01_salvage_yard'
    assert notices.count('COUPLER REQUIRED') == 1
    game.campaign.apply_event({'event_id': 'fixture_yard_coupler', 'type': 'collect_analog_coupler'})
    step(game)
    assert field.room.room_id == 'act_01_dish_catwalk'
    game.campaign.apply_event({'event_id': 'fixture_yard_repair', 'type': 'repair_dish_feedhorn'})
    assert game.campaign.state.room_flags.get('feedhorn_repaired')
    assert not game.campaign.state.inventory.get('analog_coupler', 0)
    field.load_room('act_01/salvage_yard.json', 'yard_entrance')
    place_at_exit(field, 'act_01_dish_catwalk')
    event(game, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
    step(game)
    assert field.room.room_id == 'act_01_dish_catwalk'


def test_respawn_cancels_handed_off_controls(game):
    field = game.current_scene
    place_at_exit(field, 'act_01_ohio_campus')
    event(game, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(800, 250)))
    event(game, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
    step(game)
    assert game.input.held('move_right') and game.input.held('auto_fire')
    field.player.take_damage(10000, ignore_invulnerable=True)
    step(game)
    assert not game.input.held('move_right') and not game.input.held('auto_fire')
    assert not field.keys_held


def test_held_retry_sources_are_not_fresh(game):
    field = game.current_scene
    game.campaign.apply_event({'event_id': 'fixture_fresh_coupler', 'type': 'collect_analog_coupler'})
    game.campaign.apply_event({'event_id': 'fixture_fresh_repair', 'type': 'repair_dish_feedhorn'})
    field.load_room('act_01/dish_catwalk.json', 'catwalk_start')
    event(game, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
    event(game, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(800, 250)))
    field.holdout.fail('fixture failure')
    event(game, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE, repeat=True))
    pos = (round(220 * game.crt.win_w / 480), round(213 * game.crt.win_h / 270))
    event(game, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
    assert field.holdout.is_failed
    event(game, pygame.event.Event(pygame.KEYUP, key=pygame.K_SPACE))
    event(game, pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=pos))
    event(game, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
    assert field.holdout.is_active
