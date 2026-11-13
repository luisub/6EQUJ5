"""PURPOSE: Verify mapped movement, pointer aim, and muzzle-facing in field and boss.
CALLED BY: pytest tests/test_character_facing.py.
HOW TO MODIFY: Preserve scene-router inputs and both display and rig-facing checks.
"""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pygame
import pytest

from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.weapons import get_muzzle_world_pos


@pytest.fixture(params=[config.STATE_FIELD_OPS, config.STATE_BOSS_BOUNTY], ids=['field', 'boss'])
def game(request, tmp_path, monkeypatch):
    monkeypatch.setenv('SIX_GAME_SAVE_DIR', str(tmp_path / 'save'))
    pygame.init()
    pygame.display.set_mode((480, 270))
    machine = GameStateMachine(CRTRenderer(), development=False)
    pygame.display.set_mode((machine.crt.win_w, machine.crt.win_h))
    assert machine.start_new_game()[0]
    machine.change_state(request.param)
    scene = machine.current_scene
    # This rig/charge fixture exercises the starter weapon. Temporary pickups
    # have their own mapped-input and damage tests in test_intro_powerups.py.
    scene.weapon_pickups.items.clear()
    if request.param == config.STATE_BOSS_BOUNTY:
        # Finish the authored reveal before exercising mapped combat input.
        for _ in range(91):
            machine.update(1 / 60)
            machine.input.begin_frame()
        assert scene.encounter_intro_remaining == 0
    # A safe, grounded encounter fixture. Inputs still pass through the state router.
    scene.player.x = 150.0
    scene.player.y = 192.0 if request.param == config.STATE_FIELD_OPS else 208.0
    scene.player.vx = scene.player.vy = 0.0
    scene.camera.snap_to(scene.player.x, scene.player.y)
    if request.param == config.STATE_FIELD_OPS:
        scene.enemy_manager.enemies.clear()
    else:
        scene.is_fight_active = False
    for _ in range(30):
        machine.update(1 / 60)
        machine.input.begin_frame()
    assert scene.player.is_grounded
    yield machine
    machine.close()


def send(game, kind, **kwargs):
    game.handle_event(pygame.event.Event(kind, **kwargs))


def step(game, frames=1):
    for _ in range(frames):
        game.update(1 / 60)
        game.input.begin_frame()


def pointer(game, x):
    send(game, pygame.MOUSEMOTION, pos=(x, int(game.crt.win_h * .75)), rel=(1, 0), buttons=(0, 0, 0))


def test_mapped_movement_turns_and_opposite_fire_preserves_muzzle(game):
    scene, player = game.current_scene, game.current_scene.player
    manager = scene.projectile_manager if game.current_state_name == config.STATE_FIELD_OPS else scene.proj_mgr
    shots = []
    original = manager.spawn

    def capture_spawn(*args, **kwargs):
        shots.append((kwargs.copy(), player.x + player.width / 2, player.animator.current_clip.name))
        return original(*args, **kwargs)

    manager.spawn = capture_spawn
    target = (int(game.crt.win_w * .9), int(game.crt.win_h * .75))
    pointer(game, target[0])
    send(game, pygame.KEYDOWN, key=pygame.K_d)
    step(game, 18)
    assert player.vx > 5 and player.animator.facing == 'right'
    send(game, pygame.KEYUP, key=pygame.K_d)
    send(game, pygame.KEYDOWN, key=pygame.K_a)
    step(game)
    assert player.vx > 5 and player.animator.facing == 'right'  # braking before reversal
    step(game, 18)
    assert player.vx < -5 and player.animator.current_state == 'walk'
    assert player.animator.facing == 'left' and player.weapon_facing == 'right'
    assert player.animator.attachment_facing == 'right'
    muzzle = player.get_muzzle_world_pos()
    assert muzzle == pytest.approx(get_muzzle_world_pos(player))
    assert muzzle[0] > player.x + player.width / 2
    foot = (player.x + player.width / 2, player.y + 32)
    hand = player.animator.get_attachment_world_pos('hand', *foot)
    hurtbox = player.animator.get_hurtbox(*foot)
    player.animator.set_facing('right')
    assert player.animator.get_attachment_world_pos('hand', *foot) == hand
    assert player.animator.get_hurtbox(*foot) == hurtbox
    player.animator.set_facing('left')
    player.animator.set_attachment_facing('right')

    send(game, pygame.MOUSEBUTTONDOWN, button=1, pos=target)
    step(game)
    assert shots and shots[0][0]['x'] > shots[0][1] and shots[0][0]['dir_x'] > 0
    assert player.animator.facing == 'right'
    send(game, pygame.MOUSEBUTTONUP, button=1, pos=target)
    step(game, 18)  # recoil completes before movement-facing resumes
    assert player.vx < -5 and player.animator.facing == 'left'

    # Right button initiates/holds charge; release fires toward the pointer.
    # Reposition away from the left wall for the long held-input interval.
    player.x = 280.0
    scene.camera.snap_to(player.x, player.y)
    send(game, pygame.MOUSEBUTTONDOWN, button=3, pos=target)
    step(game, 45)
    assert player.animator.facing == 'right'
    send(game, pygame.MOUSEBUTTONUP, button=3, pos=target)
    step(game)
    assert any(s[0].get('is_charged') and s[0]['dir_x'] > 0 and s[0]['x'] > s[1] for s in shots)
    step(game, 20)
    assert player.vx < -5 and player.animator.facing == 'left'
    send(game, pygame.KEYUP, key=pygame.K_a)
    step(game, 20)
    assert abs(player.vx) <= 5 and player.animator.facing == 'right'  # stationary aim


def test_mirrored_aim_and_mapped_slide_dash(game):
    scene, player = game.current_scene, game.current_scene.player
    manager = scene.projectile_manager if game.current_state_name == config.STATE_FIELD_OPS else scene.proj_mgr
    shots = []
    original = manager.spawn
    def capture_spawn(*args, **kwargs):
        shots.append((kwargs.copy(), player.x + player.width / 2))
        return original(*args, **kwargs)
    manager.spawn = capture_spawn
    target = (int(game.crt.win_w * .05), int(game.crt.win_h * .75))
    pointer(game, target[0])
    send(game, pygame.KEYDOWN, key=pygame.K_d)
    step(game, 12)
    assert player.vx > 5 and player.animator.facing == 'right' and player.weapon_facing == 'left', (player.x, player.y, player.animation_state, player.is_grounded)
    assert player.get_muzzle_world_pos()[0] < player.x + player.width / 2
    send(game, pygame.MOUSEBUTTONDOWN, button=1, pos=target)
    step(game)
    assert shots and shots[0][0]['x'] < shots[0][1] and shots[0][0]['dir_x'] < 0
    assert player.animator.facing == 'left'
    send(game, pygame.MOUSEBUTTONUP, button=1, pos=target)
    step(game, 15)
    send(game, pygame.KEYDOWN, key=pygame.K_s)
    step(game)
    assert player.is_sliding and player.vx > 0 and player.animator.facing == 'right'
    send(game, pygame.KEYUP, key=pygame.K_s)
    step(game, 30)
    send(game, pygame.KEYDOWN, key=pygame.K_LSHIFT)
    step(game)
    assert player.is_dashing and player.vx > 0 and player.animator.facing == 'right'


def test_controller_neutral_pause_and_retry(game):
    scene, player = game.current_scene, game.current_scene.player
    # Register an SDL-style controller state without requiring physical hardware.
    game.input._controller_state[77] = {'buttons': set(), 'axes': {}}
    def axis(axis_id, value):
        send(game, pygame.CONTROLLERAXISMOTION, instance_id=77, axis=axis_id, value=value)
    axis(pygame.CONTROLLER_AXIS_RIGHTX, 30000)
    axis(pygame.CONTROLLER_AXIS_LEFTX, -30000)
    step(game, 14)
    assert player.vx < -5 and player.weapon_facing == 'right' and player.animator.facing == 'left'
    axis(pygame.CONTROLLER_AXIS_RIGHTX, 0)
    step(game)
    assert game.input.controller_aim is None and player.weapon_facing == 'left'
    before = (player.x, player.animator.facing, player.animator.time_accumulated)
    send(game, pygame.KEYDOWN, key=pygame.K_F2)
    step(game, 4)
    assert (player.x, player.animator.facing, player.animator.time_accumulated) == before
    send(game, pygame.KEYUP, key=pygame.K_F2)
    send(game, pygame.KEYDOWN, key=pygame.K_F2)
    step(game)
    assert not game.pause.active
    if game.current_state_name == config.STATE_BOSS_BOUNTY:
        player.is_dead = True
        send(game, pygame.KEYDOWN, key=pygame.K_r)
        step(game)
        assert not player.is_dead and not game.input.held('move_left')
        assert player.animator.facing in ('left', 'right')
    else:
        player.respawn_at_checkpoint(scene.room)  # field's ordinary hazard retry path
        step(game)
        assert not player.is_dead
