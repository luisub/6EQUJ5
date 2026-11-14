"""PURPOSE: Exercise bunker exits through routed physical events and isolated saves.
CALLED BY: pytest.
HOW TO MODIFY: Preserve temporary stores, earned progression and real key events.
"""
import copy

import pygame
import pytest

from video_game.engine import config
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


def key(game, code, kind=pygame.KEYDOWN):
    game.handle_event(pygame.event.Event(kind, key=code))


def setup_stage(game, stage):
    events = [('record_contact', {'civilization_id': 'FASR-001'}),
              ('grant_fragment_fasr_001', {}), ('validate_fasr_001_deploy', {}),
              ('collect_analog_coupler', {}), ('repair_dish_feedhorn', {}),
              ('complete_dish_defense', {}), ('defeat_greenkeeper', {})]
    count = {'fresh': 0, 'validated': 3, 'coupler': 4, 'repaired': 5,
             'defense': 6, 'complete': 7}[stage]
    for i, (event_type, payload) in enumerate(events[:count]):
        assert game.campaign.apply_event({'event_id': f'fixture_{i}', 'type': event_type, 'payload': payload})


@pytest.mark.parametrize('stage', ['fresh', 'validated', 'coupler', 'repaired', 'defense', 'complete'])
@pytest.mark.parametrize('code', [pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_UP])
@pytest.mark.parametrize('position', [124, 268, 364])
def test_exit_at_any_position_and_stage(game, stage, code, position):
    setup_stage(game, stage)
    game.current_scene.mateo_x = position
    before = copy.deepcopy(game.campaign.to_dict())
    key(game, code)
    expected = config.STATE_BOSS_BOUNTY if stage == 'defense' else config.STATE_FIELD_OPS
    assert game.current_state_name == expected
    if expected == config.STATE_FIELD_OPS:
        room = 'dish_catwalk.json' if stage == 'repaired' else 'blackout_street.json' if stage == 'complete' else 'approach.json'
        assert game.current_scene.room_path.name == room
    assert game.campaign.to_dict() == before
    assert game.save_store.load().campaign.to_dict() == before
    assert not game.input.held('jump') and not game.input.held('fire')
    game.update(1 / 60)
    assert not game.input.held('jump') and not game.input.held('fire')
    if expected == config.STATE_FIELD_OPS:
        assert not game.current_scene.projectile_manager.projectiles
        if stage == 'coupler':
            notice = game.current_scene.objective_tracker.active_notification
            assert notice and 'FEEDHORN' in notice.text
    key(game, code, pygame.KEYUP)


def test_station_airlock_uses_same_exit_and_prompt_is_visible(game, monkeypatch):
    setup_stage(game, 'complete')
    bunker = game.current_scene
    bunker.mateo_x = 348
    assert bunker.station_prompt(game.crt)[0] == 'E: CONTINUE MISSION'
    drawn = []
    original = game.crt.draw_text
    def capture(text, *args, **kwargs):
        drawn.append(text)
        return original(text, *args, **kwargs)
    monkeypatch.setattr(game.crt, 'draw_text', capture)
    game.render()
    assert 'ENTER / UP: CONTINUE MISSION' in drawn
    assert 12 + game.crt.font_sm.size('ENTER / UP: CONTINUE MISSION')[0] < bunker.DETAILS_BUTTON.left
    key(game, pygame.K_e)
    assert game.current_state_name == config.STATE_FIELD_OPS
    assert game.current_scene.room_path.name == 'blackout_street.json'


def test_dossier_and_pause_capture_exit_keys(game):
    key(game, pygame.K_TAB)
    for code in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_UP):
        key(game, code)
        key(game, code, pygame.KEYUP)
        assert game.current_state_name == config.STATE_BUNKER_HUB
    key(game, pygame.K_ESCAPE)
    key(game, pygame.K_ESCAPE)
    assert game.pause.active
    for code in (pygame.K_UP, pygame.K_RETURN, pygame.K_KP_ENTER):
        key(game, code)
        key(game, code, pygame.KEYUP)
        assert game.current_state_name == config.STATE_BUNKER_HUB
        if not game.pause.active:
            key(game, pygame.K_ESCAPE)
            assert game.pause.active


def test_exit_clears_held_jump_and_fire_without_charging(game):
    key(game, pygame.K_w)
    key(game, pygame.K_x)
    game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=3, pos=(400, 250)))
    assert game.input.held('jump') and game.input.held('fire')
    key(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_FIELD_OPS
    game.update(1 / 60)
    weapon = game.current_scene.player.weapon
    assert not game.input.held('jump') and not game.input.held('fire')
    assert not weapon.is_charging and weapon.charge_timer == 0
    assert not game.current_scene.projectile_manager.projectiles
    for code in (pygame.K_w, pygame.K_x, pygame.K_RETURN):
        key(game, code, pygame.KEYUP)
    game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=3, pos=(400, 250)))
    game.update(1 / 60)
    assert not game.current_scene.projectile_manager.projectiles


def test_save_failure_does_not_preload_surface_room(game, monkeypatch):
    from video_game.engine.save_game import SaveError
    setup_stage(game, 'repaired')
    field = game.scenes[config.STATE_FIELD_OPS]
    original_room = field.room_path
    before = copy.deepcopy(game.campaign.to_dict())
    def fail(*args, **kwargs):
        raise SaveError('fixture failure')
    monkeypatch.setattr(game.save_store, 'save', fail)
    key(game, pygame.K_UP)
    assert game.current_state_name == config.STATE_BUNKER_HUB
    assert field.room_path == original_room
    assert game.save_notice.startswith('SAVE FAILED')
    assert game.campaign.to_dict() == before
    drawn = []
    original_draw = game.crt.draw_text
    def capture(text, *args, **kwargs):
        drawn.append(text)
        return original_draw(text, *args, **kwargs)
    monkeypatch.setattr(game.crt, 'draw_text', capture)
    game.render()
    assert 'SAVE FAILED - F5 RETRY' in drawn
    assert not game.input.held('jump')


def test_click_airlock_uses_same_exit(game):
    setup_stage(game, 'complete')
    pygame.display.set_mode((game.crt.win_w, game.crt.win_h))
    bunker = game.current_scene
    bunker.mateo_x = 348
    _, prompt = bunker.station_prompt(game.crt)
    pos = (round(prompt.centerx * game.crt.win_w / 480),
           round(prompt.centery * game.crt.win_h / 270))
    game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
    assert game.current_state_name == config.STATE_FIELD_OPS
    assert game.current_scene.room_path.name == 'blackout_street.json'
