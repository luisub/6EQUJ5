"""PURPOSE: Verify Act V raised paths using real mapped movement and jumps.
CALLED BY: pytest.
HOW TO MODIFY: Preserve the uninterrupted ground route and test normal jump releases.
"""
import json
from pathlib import Path

import pygame
import pytest

from video_game.engine import config
from video_game.engine.campaign_route import store_route
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine

ROOMS = ('pillar_approach', 'buried_archive', 'crust_waveguide')
BASES = (18, 44)


@pytest.fixture
def machine(tmp_path, monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER', 'dummy')
    monkeypatch.setenv('SDL_AUDIODRIVER', 'dummy')
    pygame.init()
    pygame.display.set_mode((960, 540))
    m = GameStateMachine(CRTRenderer(scale=2), save_store=SaveStore(tmp_path / 'save'),
                         settings_store=SettingsStore(tmp_path / 'settings'))
    assert m.start_new_game()[0]
    yield m
    m.close()
    pygame.quit()


def step(machine):
    machine.update(1 / 60)
    machine.input.begin_frame()


def key(machine, event, value):
    machine.handle_event(pygame.event.Event(event, key=value))


def jump_to(machine, target_x, expected_y, hold_frames):
    """Jump right, release the direction near the landing, then land naturally."""
    p = machine.current_scene.player
    assert p.is_grounded
    key(machine, pygame.KEYDOWN, pygame.K_RIGHT)
    key(machine, pygame.KEYDOWN, pygame.K_SPACE)
    direction_held = True
    trace = []
    for frame in range(100):
        step(machine)
        trace.append((round(p.x, 2), round(p.y + 32, 2), p.is_grounded))
        if frame + 1 == hold_frames:
            key(machine, pygame.KEYUP, pygame.K_SPACE)
        if direction_held and p.x >= target_x - 8:
            key(machine, pygame.KEYUP, pygame.K_RIGHT)
            direction_held = False
        if frame >= 3 and p.is_grounded:
            key(machine, pygame.KEYUP, pygame.K_SPACE)
            if direction_held:
                key(machine, pygame.KEYUP, pygame.K_RIGHT)
            assert p.y + 32 in expected_y, trace
            return trace
    pytest.fail(f'Jump failed to land: {trace}')


@pytest.mark.parametrize('room', ROOMS)
def test_all_repeated_platforms_have_one_way_steps_and_clear_floor(room):
    data = json.loads((config.DATA_DIR / 'levels/act_05' / f'{room}.json').read_text())
    grid = data['collision_layers']
    assert all(cell == 1 for cell in grid[15])
    assert all(cell != 1 for row in grid[:15] for cell in row)
    for base in BASES:
        assert grid[13][base - 5:base - 1] == [2] * 4  # y=208, 64px wide
        assert grid[11][base - 2:base + 2] == [2] * 4  # y=176, 64px wide
        assert grid[10][base:base + 5] == [2] * 5     # original y=160 top


@pytest.mark.parametrize('room', ROOMS)
@pytest.mark.parametrize('platform_index', (0, 1))
@pytest.mark.parametrize('hold_frames', (9, 35), ids=('short-press', 'held-jump'))
def test_mapped_jump_sequence_reaches_top_and_walks_off(machine, room, platform_index, hold_frames):
    machine.change_state(config.STATE_FIELD_OPS, room=f'act_05/{room}.json', spawn='default')
    scene = machine.current_scene
    scene.forward_encounter = None
    scene.enemy_manager.clear()
    origin = (BASES[platform_index] - BASES[0]) * 16
    p = scene.player
    p.x, p.y, p.vx, p.vy = origin + 190., 208., 0., 0.
    p.rect.topleft = (round(p.x), 208)
    for _ in range(5):
        step(machine)
    landings = []
    for target_x, tops in ((origin + 235, (208,)), (origin + 275, (176, 160))):
        trace = jump_to(machine, target_x, tops, hold_frames)
        landings.append(trace[-1])
        for _ in range(4):
            step(machine)
    if landings[-1][1] == 176:
        trace = jump_to(machine, origin + 310, (160,), hold_frames)
        landings.append(trace[-1])
    assert landings[0][1] == 208 and landings[-1][1] == 160
    key(machine, pygame.KEYDOWN, pygame.K_RIGHT)
    for _ in range(100):
        step(machine)
        if p.x > origin + 390 and p.is_grounded and p.y + 32 == 240:
            break
    key(machine, pygame.KEYUP, pygame.K_RIGHT)
    assert p.x > origin + 390 and p.is_grounded and p.y + 32 == 240


@pytest.mark.parametrize('room', ROOMS)
def test_mapped_ground_route_remains_open(machine, room):
    machine.change_state(config.STATE_FIELD_OPS, room=f'act_05/{room}.json', spawn='default')
    scene = machine.current_scene
    scene.forward_encounter = None
    scene.enemy_manager.clear()
    key(machine, pygame.KEYDOWN, pygame.K_RIGHT)
    for _ in range(1800):
        step(machine)
        if scene.player.x >= 860:
            break
    key(machine, pygame.KEYUP, pygame.K_RIGHT)
    assert scene.player.x >= 860
    assert scene.player.is_grounded and scene.player.y + 32 == 240


def test_existing_campaign_continue_reloads_updated_geometry(machine):
    # Disposable existing-campaign fixture: earn required Earth unlock flags and
    # persist the previously available checkpoint, then use actual Continue.
    for event in ('defeat_greenkeeper', 'defeat_synchronicity', 'defeat_amalgam', 'defeat_architect'):
        assert machine.campaign.apply_event({'event_id': 'fixture_' + event, 'type': event})
    checkpoint = 'act_05_pillar_approach_checkpoint_1'
    store_route(machine.campaign, 'act_05_pillar_approach', checkpoint)
    assert machine.save_checkpoint()
    assert machine.continue_game().status == 'ok'
    assert machine.current_state_name == config.STATE_BUNKER_HUB
    key(machine, pygame.KEYDOWN, pygame.K_RETURN)
    step(machine)
    key(machine, pygame.KEYUP, pygame.K_RETURN)
    assert machine.current_scene.room.room_id == 'act_05_pillar_approach'
    assert machine.current_scene.player.active_checkpoint_id == checkpoint
    room = machine.current_scene.room
    assert room.get_tile(13, 13) == room.get_tile(16, 11) == 2
