"""PURPOSE: Verify flag-derived story, camera framing and victory persistence.
CALLED BY: pytest tests/test_action_story.py.
HOW TO MODIFY: Retain temporary saves and disclose synthetic inputs, warped
positions, cleared enemies and injected boss damage; these are not human play.
"""
import json

import pygame
import pytest

from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveError, SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.story_sequence import earned_story_pages
from video_game.engine.ui.dialogue import NEXT_BUTTON


@pytest.fixture
def game(tmp_path, monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER', 'dummy')
    monkeypatch.setenv('SDL_AUDIODRIVER', 'dummy')
    pygame.init()
    pygame.display.set_mode((960, 540))
    machine = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(tmp_path),
                               settings_store=SettingsStore(tmp_path))
    machine.change_settings(scale=1)
    assert machine.start_new_game()[0]
    yield machine
    machine.close()
    pygame.quit()


def press(machine, key):
    machine.input.begin_frame()
    machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))
    machine.handle_event(pygame.event.Event(pygame.KEYUP, key=key))


def enter_victory(machine):
    # Explicit precondition: direct lethal hit isolates story lifecycle from boss skill.
    machine.change_state(config.STATE_BOSS_BOUNTY)
    scene = machine.current_scene
    machine.update(1.6)  # Allow the safe arrival reveal to finish.
    scene.boss.take_damage(1000, hit_pos=(scene.boss.x, scene.boss.y))
    machine.update(1 / 60)
    return scene


def test_actual_reward_story_inputs_pause_and_continue(game):
    scene = enter_victory(game)
    assert game.campaign.state.room_flags['greenkeeper_defeated']
    assert game.save_store.load().campaign.state.room_flags['greenkeeper_defeated']
    assert [p['title'] for p in scene.story.pages] == ['GREENKEEPER NEUTRALIZED']
    assert all('ACT II UNLOCKED' not in p['text'].upper() for p in scene.story.pages)
    health = scene.player.health
    press(game, pygame.K_F2)
    remaining = scene.story.remaining
    game.update(30)
    assert scene.story.remaining == remaining
    assert scene.destruction.elapsed == 0
    press(game, pygame.K_F2)
    game.update(3)
    game.input.begin_frame()
    game.handle_event(pygame.event.Event(pygame.CONTROLLERBUTTONDOWN, button=pygame.CONTROLLER_BUTTON_A))
    assert scene.story.index == 1 and scene.player.health == health
    assert game.current_state_name == config.STATE_FIELD_OPS
    assert game.current_scene.room.room_id == 'act_02_blackout_street'
    before = game.campaign.to_dict()
    game.change_state(config.STATE_BOSS_BOUNTY)
    assert game.current_scene.is_defeated_sequence
    game.input.begin_frame()
    game.handle_event(pygame.event.Event(pygame.CONTROLLERBUTTONDOWN, button=pygame.CONTROLLER_BUTTON_B))
    assert game.current_state_name == config.STATE_BUNKER_HUB
    assert game.campaign.to_dict() == before
    game.change_state(config.STATE_BOSS_BOUNTY)
    game.handle_event(pygame.event.Event(pygame.CONTROLLERBUTTONDOWN, button=pygame.CONTROLLER_BUTTON_BACK))
    assert game.current_state_name == config.STATE_BUNKER_HUB
    assert game.campaign.to_dict() == before
    assert game.continue_game().status == 'ok'
    assert game.campaign.state.room_flags['greenkeeper_defeated']


def test_save_failure_freezes_and_retries_without_double_reward(game, monkeypatch):
    original = game.save_store.save
    def fail(*args, **kwargs):
        raise SaveError('test failure')
    monkeypatch.setattr(game.save_store, 'save', fail)
    # Enter boss directly to avoid the bunker transition's required save.
    game.session_active = False
    game.change_state(config.STATE_BOSS_BOUNTY)
    game.session_active = True
    scene = game.current_scene
    game.update(1.6)  # Allow the safe arrival reveal to finish.
    scene.boss.take_damage(1000, hit_pos=(scene.boss.x, scene.boss.y))
    game.update(1 / 60)
    assert scene.story_save_pending
    before = game.campaign.to_dict()
    game.update(60)
    press(game, pygame.K_ESCAPE)
    assert scene.story_save_pending and scene.story.index == 0
    assert game.current_state_name == config.STATE_BOSS_BOUNTY
    assert game.campaign.to_dict() == before
    monkeypatch.setattr(game.save_store, 'save', original)
    press(game, pygame.K_F5)
    assert not scene.story_save_pending
    assert game.save_store.load().campaign.to_dict() == before
    press(game, pygame.K_ESCAPE)
    assert game.current_state_name == config.STATE_BUNKER_HUB
    assert game.campaign.to_dict() == before


def test_malformed_story_and_no_victory_never_grant_content(game, tmp_path):
    bad = tmp_path / 'bad.json'
    bad.write_text(json.dumps({'schema_version': 1, 'pages': [{'when': 'fake', 'title': 'X', 'text': 'X'}]}))
    assert earned_story_pages(game.campaign, bad) == []
    assert earned_story_pages(game.campaign) == []
    scene = enter_victory(game)
    assert earned_story_pages(game.campaign, bad) == []
    start = scene.story.remaining
    game.update(1)
    assert scene.story.remaining == start
    assert scene.story.index == 0 and game.current_scene is scene


def test_simultaneous_death_does_not_grant_victory(game):
    game.change_state(config.STATE_BOSS_BOUNTY)
    scene = game.current_scene
    game.update(1.6)  # Allow the safe arrival reveal to finish.
    scene.boss.take_damage(1000, hit_pos=(scene.boss.x, scene.boss.y))
    scene.player.health = 0
    scene.player.is_dead = True
    game.update(1 / 60)
    assert not game.campaign.state.room_flags.get('greenkeeper_defeated', False)
    assert not scene.is_defeated_sequence
    press(game, pygame.K_r)
    assert not scene.player.is_dead and scene.boss.health == 300


def test_guided_signal_yard_field_repair_defense_and_boss_story(game):
    """Actual events, with position warps and enemy clearing as explicit test fixtures."""
    def tap(key):
        press(game, key)
        game.update(1 / 60)

    # Real receiver and guided validator; no campaign reward is injected.
    tap(pygame.K_SPACE)
    assert game.current_state_name == config.STATE_CRT_TERMINAL
    for _ in range(20):
        if 'FASR-001' in game.campaign.state.extracted_fragments:
            break
        tap(pygame.K_RETURN)
    assert 'FASR-001' in game.campaign.state.extracted_fragments
    tap(pygame.K_ESCAPE)
    tap(pygame.K_SPACE)
    assert game.current_state_name == config.STATE_SCIENCE_LAB
    for _ in range(5):
        tap(pygame.K_RETURN)
    assert any(r['id'] == 'FASR-001' for r in game.campaign.state.validation_records)
    tap(pygame.K_RETURN)
    assert game.current_state_name == config.STATE_BUNKER_HUB
    tap(pygame.K_RETURN)
    field = game.current_scene
    assert field.room.room_id == 'act_01_approach'

    # Warp to actual room exits/pickup to keep traversal time out of this integration test.
    def place(x, y=208):
        field.player.x, field.player.y = x, y
        field.player.rect.topleft = (x, y)
    def exit_to(target):
        exit_ = next(ex for ex in field.room.exits if ex.target_room == target)
        place(exit_.x, exit_.y)
        tap(pygame.K_e)

    exit_to('act_01_ohio_campus')
    assert field.room.room_id == 'act_01_ohio_campus'
    exit_to('act_01_salvage_yard')
    assert field.room.room_id == 'act_01_salvage_yard'
    place(520)
    game.update(1 / 60)
    assert game.campaign.state.inventory['analog_coupler'] == 1
    exit_to('act_01_dish_catwalk')
    assert field.room.room_id == 'act_01_dish_catwalk'
    assert not game.campaign.state.room_flags.get('feedhorn_repaired', False)
    place(288)
    tap(pygame.K_UP)
    assert game.campaign.state.room_flags['feedhorn_repaired']
    assert field.holdout.is_active
    assert game.save_store.load().campaign.state.room_flags['feedhorn_repaired']
    # Advance 72 seconds at the normal fixed step. Removing enemies is a fixture,
    # and clearing jams uses the real interaction rather than injecting the reward.
    jams_cleared = 0
    pygame.display.set_mode((game.crt.win_w, game.crt.win_h))
    for _ in range(4400):
        field.enemy_manager.clear()
        if field.holdout.is_jammed:
            if jams_cleared == 0:
                press(game, pygame.K_UP)
            else:
                pos = (round(220 * game.crt.win_w / 480), round(213 * game.crt.win_h / 270))
                game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
                assert not game.input.held('fire')
                game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=pos))
            assert not field.holdout.is_jammed
            jams_cleared += 1
        game.update(1 / 60)
        if field.holdout.is_completed:
            break
    assert field.holdout.is_completed
    assert jams_cleared >= 2
    assert game.campaign.state.room_flags['dish_defense_completed']
    exit_to('act_01_greenkeeper_arena')
    assert game.current_state_name == config.STATE_BOSS_BOUNTY
    scene = game.current_scene
    game.update(1.6)  # Allow the safe arrival reveal to finish.
    scene.boss.take_damage(1000, hit_pos=(scene.boss.x, scene.boss.y))
    game.update(1 / 60)
    assert [p['title'] for p in scene.story.pages] == [
        'GREENKEEPER NEUTRALIZED']
    assert game.save_store.load().campaign.state.room_flags['greenkeeper_defeated']


def test_boss_camera_keeps_player_visible_and_frames_full_body(game, monkeypatch):
    game.change_state(config.STATE_BOSS_BOUNTY)
    scene = game.current_scene
    # Isolate framing from combat while representing the accepted 128x96 body.
    scene.boss.x = 428
    scene.boss.width = 128
    monkeypatch.setattr(scene.boss, 'update', lambda *args, **kwargs: None)
    monkeypatch.setattr(scene.boss, 'check_attack_collisions', lambda *args: 0)
    scene.player.x = 250
    scene.player.y = 208
    for _ in range(90):
        game.update(1 / 60)
    assert scene.camera.x <= scene.player.x
    assert scene.camera.x + scene.camera.viewport_w >= scene.boss.x + 128
    # A rightward charge while Mateo is near the left edge does not hide Mateo.
    scene.player.x = 32
    scene.player.y = 208
    scene.boss.x = 480
    for _ in range(90):
        game.update(1 / 60)
    assert scene.camera.x <= scene.player.x
    assert scene.player.x + scene.player.width <= scene.camera.x + scene.camera.viewport_w


@pytest.mark.parametrize('crt_effects', [True, False])
def test_native_boss_preserves_hud_across_frames(game, monkeypatch, crt_effects):
    game.change_settings(crt_effects=crt_effects)
    game.change_state(config.STATE_BOSS_BOUNTY)
    scene = game.current_scene
    assert scene.boss.heavy_sprites is not None
    assert (scene.boss.x, scene.boss.y, scene.boss.width, scene.boss.height) == (428, 144, 128, 96)
    scene.player.x = 250
    scene.camera.snap_to(370, scene.player.y)
    render = scene.boss.render
    # Logical body rendering is a control for native-composite ordering. Scene HUD
    # and every other layer run normally in both paths.
    monkeypatch.setattr(scene.boss, 'render', lambda surface, camera, *, crt: render(surface, camera))
    game.render()
    reference = game.crt.render_surface.copy()
    monkeypatch.setattr(scene.boss, 'render', render)
    for _ in range(4):
        game.render()
        actual = game.crt.render_surface
        for rect in ((0, 0, 960, 34), (0, 508, 960, 32)):
            assert pygame.image.tobytes(actual.subsurface(rect), 'RGBA') == \
                   pygame.image.tobytes(reference.subsurface(rect), 'RGBA')
        # Exercise the output path with CRT on and off as well.
        game.crt.present(pygame.display.get_surface())
