"""MODULE: video_game/tests/test_accessible_controls_integration.py
PURPOSE: Exercise accessible combat via actual game-state event routing.
CALLED BY: pytest video_game/tests/test_accessible_controls_integration.py.
HOW TO MODIFY: Keep Pygame events, temporary saves and fixture injections explicit.
"""
import json
import math

import pygame
import pytest

from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import Settings, SettingsStore
from video_game.engine.state_machine import GameStateMachine


@pytest.fixture(autouse=True)
def dummy_display(monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER', 'dummy')
    monkeypatch.setenv('SDL_AUDIODRIVER', 'dummy')
    pygame.init()
    pygame.display.set_mode((960, 540))
    yield
    pygame.quit()


def setup_game(tmp_path, scene_name, scale=1, mode='assisted'):
    pygame.display.set_mode((config.RENDER_WIDTH * scale, config.RENDER_HEIGHT * scale))
    store = SettingsStore(tmp_path)
    store.save(Settings(scale=scale, combat_mode=mode))
    machine = GameStateMachine(CRTRenderer(scale=scale), save_store=SaveStore(tmp_path), settings_store=store)
    assert machine.start_new_game()[0]
    machine.change_state(scene_name)
    scene = machine.current_scene
    scene.player.x = 400
    scene.player.y = 208
    scene.player.vx = scene.player.vy = 0
    scene.camera.x, scene.camera.y = 200, 18
    if hasattr(scene, 'enemy_manager'):
        scene.enemy_manager.clear()
    manager = scene.projectile_manager if scene_name == config.STATE_FIELD_OPS else scene.proj_mgr
    calls = []
    spawn = manager.spawn
    def record_spawn(*args, **kwargs):
        calls.append(dict(kwargs))
        return spawn(*args, **kwargs)
    manager.spawn = record_spawn
    return machine, scene, calls


def key(machine, kind, value):
    machine.handle_event(pygame.event.Event(kind, key=value))


def mouse(machine, kind, button, pos):
    machine.handle_event(pygame.event.Event(kind, button=button, pos=pos))


def step(machine, n=1):
    for _ in range(n):
        machine.update(1 / 60)
        machine.input.begin_frame()


def screen_position(machine, scene, world_x, world_y):
    return (round((world_x - scene.camera.x) * machine.crt.win_w / config.INTERNAL_WIDTH),
            round((world_y - scene.camera.y) * machine.crt.win_h / config.INTERNAL_HEIGHT))


@pytest.mark.parametrize('scene_name', [config.STATE_FIELD_OPS, config.STATE_BOSS_BOUNTY])
@pytest.mark.parametrize('scale', [1, 2])
@pytest.mark.parametrize('horizontal', [-1, 1])
def test_mouse_aim_and_muzzle_use_live_camera_and_window(scene_name, scale, horizontal, tmp_path):
    machine, scene, calls = setup_game(tmp_path, scene_name, scale)
    try:
        player = scene.player
        old_center = player.x + player.width / 2
        # Deliberately start facing the opposite way to exercise origin synchronization.
        player.facing = 'right' if horizontal < 0 else 'left'
        player.animator.set_facing(player.facing)
        pos = screen_position(machine, scene, old_center + horizontal * 100, player.y - 35)
        mouse(machine, pygame.MOUSEBUTTONDOWN, 1, pos)
        step(machine)
        assert len(calls) == 3
        center = calls[0]
        assert center['damage'] == 50 and center['weapon_type'] == 'starter_maser'
        assert horizontal * center['dir_x'] > 0 and center['dir_y'] < 0
        assert math.hypot(center['dir_x'], center['dir_y']) == pytest.approx(1.0)
        assert horizontal * (center['x'] - old_center) > 0
        assert [item['damage'] for item in calls] == [50, 20, 20]
    finally:
        machine.close()


def test_pause_profile_choice_persists_and_classic_mouse_repeat(tmp_path):
    machine, scene, calls = setup_game(tmp_path, config.STATE_FIELD_OPS)
    try:
        assert machine.settings.combat_mode == 'assisted'
        key(machine, pygame.KEYDOWN, pygame.K_F2)
        assert machine.pause.active
        for _ in range(4):
            key(machine, pygame.KEYDOWN, pygame.K_DOWN)
        key(machine, pygame.KEYDOWN, pygame.K_RETURN)
        assert machine.settings.combat_mode == 'classic'
        assert SettingsStore(tmp_path).load().combat_mode == 'classic'
        key(machine, pygame.KEYDOWN, pygame.K_ESCAPE)
        assert not machine.pause.active
        pos = screen_position(machine, scene, scene.player.x + 100, scene.player.y)
        mouse(machine, pygame.MOUSEBUTTONDOWN, 1, pos)
        step(machine, 30)
        assert len(calls) >= 2
        assert all(c['damage'] == 25 and c['weapon_type'] == 'starter_maser' for c in calls)
    finally:
        machine.close()


@pytest.mark.parametrize('scene_name', [config.STATE_FIELD_OPS, config.STATE_BOSS_BOUNTY])
def test_focus_loss_cancels_mouse_charge_without_release_shot(scene_name, tmp_path):
    machine, scene, calls = setup_game(tmp_path, scene_name, mode='classic')
    try:
        pos = screen_position(machine, scene, scene.player.x + 100, scene.player.y)
        mouse(machine, pygame.MOUSEBUTTONDOWN, 3, pos)
        step(machine, 40)
        before = len(calls)
        machine.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
        assert machine.pause.active
        mouse(machine, pygame.MOUSEBUTTONUP, 3, pos)
        key(machine, pygame.KEYDOWN, pygame.K_ESCAPE)
        step(machine, 2)
        assert len(calls) == before
        assert not machine.input.held('fire') and not machine.input.held('auto_fire')
    finally:
        machine.close()


def test_q_then_mouse_uses_unlocked_scattergun_not_assisted_starter(tmp_path):
    machine, scene, calls = setup_game(tmp_path, config.STATE_FIELD_OPS)
    try:
        # Only the unlock is injected; weapon switch and shot use real game events.
        scene.player.arsenal.weapons['scattergun'].is_unlocked = True
        key(machine, pygame.KEYDOWN, pygame.K_q)
        step(machine)
        key(machine, pygame.KEYUP, pygame.K_q)
        assert scene.player.arsenal.active_weapon_id == 'scattergun'
        pos = screen_position(machine, scene, scene.player.x + 100, scene.player.y)
        mouse(machine, pygame.MOUSEBUTTONDOWN, 1, pos)
        step(machine)
        assert len(calls) == 5
        assert all(c['weapon_type'] == 'scattergun' and c['damage'] == 12 for c in calls)
    finally:
        machine.close()


@pytest.mark.parametrize('schema,scale', [(1, 3), (2, 2)])
def test_old_settings_migrate_in_memory_without_rewrite(tmp_path, schema, scale):
    store = SettingsStore(tmp_path)
    payload = {'schema_version': schema, 'volume': 41, 'crt_effects': False, 'scale': scale}
    store.path.write_text(json.dumps(payload))
    before = store.path.read_bytes()
    loaded = store.load()
    assert loaded.combat_mode == 'classic' and loaded.volume == 41 and loaded.scale == 2
    assert store.path.read_bytes() == before


def test_pointer_uses_origin_aligned_clipped_actual_window(tmp_path):
    machine, scene, calls = setup_game(tmp_path, config.STATE_FIELD_OPS, scale=2)
    try:
        # Renderer still draws 1920x1080 at origin, clipped by the actual smaller SDL surface.
        pygame.display.set_mode((960, 540))
        assert pygame.display.get_surface().get_size() == (960, 540)
        assert (machine.crt.win_w, machine.crt.win_h) == (1920, 1080)
        # x=600 is logical x=150 of the drawn 1920-wide frame, NOT x=300 stretched to the window.
        mouse(machine, pygame.MOUSEBUTTONDOWN, 1, (600, 200))
        step(machine)
        assert len(calls) == 3
        assert calls[0]['dir_x'] < 0 and calls[0]['dir_y'] < 0
        assert calls[0]['x'] < scene.player.x + scene.player.width / 2
    finally:
        machine.close()


def connect_fake_controller(machine, monkeypatch):
    from pygame._sdl2 import controller
    class Joy:
        def __init__(self, index): self.index = index
        def get_instance_id(self): return 100 + self.index
    class Device:
        def __init__(self, index): self.index = index
        def quit(self): pass
    monkeypatch.setattr(controller, 'get_init', lambda: True)
    monkeypatch.setattr(controller, 'is_controller', lambda index: index == 0)
    monkeypatch.setattr(controller, 'Controller', Device)
    monkeypatch.setattr(pygame.joystick, 'Joystick', Joy)
    machine.handle_event(pygame.event.Event(pygame.CONTROLLERDEVICEADDED, device_index=0))


def axis(machine, name, value):
    machine.handle_event(pygame.event.Event(pygame.CONTROLLERAXISMOTION, instance_id=100, axis=name, value=value))


@pytest.mark.parametrize('scene_name', [config.STATE_FIELD_OPS, config.STATE_BOSS_BOUNTY])
def test_controller_aim_autofire_then_disconnect_stops_shots(scene_name, tmp_path, monkeypatch):
    machine, scene, calls = setup_game(tmp_path, scene_name)
    try:
        connect_fake_controller(machine, monkeypatch)
        axis(machine, pygame.CONTROLLER_AXIS_RIGHTX, -24000)
        axis(machine, pygame.CONTROLLER_AXIS_RIGHTY, -18000)
        axis(machine, pygame.CONTROLLER_AXIS_TRIGGERRIGHT, 32767)
        step(machine, 20)
        assert len(calls) >= 6
        assert calls[0]['dir_x'] < 0 and calls[0]['dir_y'] < 0
        machine.handle_event(pygame.event.Event(pygame.CONTROLLERDEVICEREMOVED, instance_id=100))
        prior = len(calls)
        step(machine, 30)
        assert len(calls) == prior and not machine.input.held('auto_fire')
    finally:
        machine.close()


def test_disconnect_cancels_charged_controller_trigger(tmp_path, monkeypatch):
    machine, scene, calls = setup_game(tmp_path, config.STATE_FIELD_OPS, mode='classic')
    try:
        connect_fake_controller(machine, monkeypatch)
        axis(machine, pygame.CONTROLLER_AXIS_TRIGGERLEFT, 32767)
        step(machine, 40)
        prior = len(calls)
        machine.handle_event(pygame.event.Event(pygame.CONTROLLERDEVICEREMOVED, instance_id=100))
        step(machine, 3)
        assert len(calls) == prior and not any(c.get('is_charged') for c in calls)
    finally:
        machine.close()


def test_relay_panel_captures_mouse_fire_without_latching(tmp_path):
    machine, scene, calls = setup_game(tmp_path, config.STATE_FIELD_OPS)
    try:
        # Direct room entry is only fixture setup; interaction uses E events.
        scene.load_room('act_04/dodleston_relay.json', spawn_name='relay_terminal_post')
        key(machine, pygame.KEYDOWN, pygame.K_e)
        assert scene.reality.panel_open
        mouse(machine, pygame.MOUSEBUTTONDOWN, 1, (400, 250))
        step(machine, 15)
        key(machine, pygame.KEYDOWN, pygame.K_e)
        assert not scene.reality.panel_open
        step(machine, 15)
        assert not calls and not machine.input.held('auto_fire')
    finally:
        machine.close()


def test_flashback_suppresses_mouse_and_controller_fire(tmp_path, monkeypatch):
    machine, scene, calls = setup_game(tmp_path, config.STATE_FIELD_OPS)
    try:
        scene.load_room('flashback/ehman_1977.json', spawn_name='ehman_desk')
        connect_fake_controller(machine, monkeypatch)
        mouse(machine, pygame.MOUSEBUTTONDOWN, 1, (400, 250))
        axis(machine, pygame.CONTROLLER_AXIS_TRIGGERRIGHT, 32767)
        step(machine, 30)
        assert not calls
        key(machine, pygame.KEYDOWN, pygame.K_e)
        assert scene.flashback.is_printout_open
        step(machine, 10)
        assert not calls
    finally:
        machine.close()
