"""
MODULE: tests/test_input_settings.py
PURPOSE: Verify input focus, pause timing, settings persistence and development controls.
CALLED BY: pytest (`python -m pytest tests -q`).
HOW TO MODIFY: Exercise real event routing and user-data paths in temporary directories.
"""

from . import REPO_ROOT

from dataclasses import asdict
import json
import os
from pathlib import Path
import subprocess
import sys

import pygame
import pytest

from video_game.engine import config, settings
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.input import InputManager
from video_game.engine.settings import Settings, SettingsError, SettingsStore
from video_game.engine.state_machine import GameStateMachine
import video_game.main as game_main


@pytest.fixture
def display(tmp_path, monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    monkeypatch.setenv("SIX_GAME_SAVE_DIR", str(tmp_path / "user_data"))
    pygame.init()
    pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    yield
    pygame.quit()


def send(machine, event_type, key):
    machine.handle_event(pygame.event.Event(event_type, key=key))


def test_action_edges_and_multiple_physical_keys():
    actions = InputManager()
    actions.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a))
    assert actions.pressed("move_left") and actions.held("move_left")
    actions.begin_frame()
    assert not actions.pressed("move_left") and actions.held("move_left")
    actions.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT))
    actions.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_a))
    assert actions.held("move_left") and not actions.released("move_left")
    actions.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_LEFT))
    assert actions.released("move_left") and not actions.held("move_left")
    actions.begin_frame()
    assert not actions.released("move_left")


def test_pause_freezes_time_and_does_not_restore_stale_keys(display):
    machine = GameStateMachine(CRTRenderer())
    machine.change_state(config.STATE_BUNKER_HUB)
    hub = machine.current_scene
    send(machine, pygame.KEYDOWN, pygame.K_d)
    machine.update(0.2)
    assert hub.mateo_x == pytest.approx(208)
    send(machine, pygame.KEYDOWN, pygame.K_ESCAPE)
    assert machine.pause.active and not machine.input.held("move_right")
    position, animation, glitch = hub.mateo_x, hub.anim_seconds, machine.crt.glitch_timer_ms
    send(machine, pygame.KEYUP, pygame.K_d)
    machine.update(10)
    assert (hub.mateo_x, hub.anim_seconds, machine.crt.glitch_timer_ms) == (position, animation, glitch)
    send(machine, pygame.KEYDOWN, pygame.K_ESCAPE)
    assert not machine.pause.active
    machine.update(0.5)
    assert hub.mateo_x == position
    send(machine, pygame.KEYDOWN, pygame.K_d)
    machine.update(0.1)
    assert hub.mateo_x == pytest.approx(position + 11)
    machine.close()


def test_terminal_typing_and_pause_do_not_move_or_fire(display):
    machine = GameStateMachine(CRTRenderer(), development=True)
    machine.change_state(config.STATE_BUNKER_HUB)
    hub = machine.current_scene
    send(machine, pygame.KEYDOWN, pygame.K_d)
    send(machine, pygame.KEYDOWN, pygame.K_e)
    assert machine.current_state_name == config.STATE_CRT_TERMINAL
    assert not machine.input.held("move_right")
    terminal = machine.current_scene
    for code in (pygame.K_a, pygame.K_d, pygame.K_x, pygame.K_p, pygame.K_c):
        send(machine, pygame.KEYDOWN, code)
    machine.handle_event(pygame.event.Event(pygame.TEXTINPUT, text="adxpc"))
    assert terminal.text_buffer == ""  # The authored receiver ignores typed text.
    assert not machine.input.held("move_left") and not machine.input.held("move_right")
    assert not machine.input.held("fire")
    position, pose, civ = hub.mateo_x, hub.pose_idx, hub.civ_idx
    machine.update(0.5)
    assert (hub.mateo_x, hub.pose_idx, hub.civ_idx) == (position, pose, civ)
    send(machine, pygame.KEYDOWN, pygame.K_F2)
    assert machine.pause.active
    machine.handle_event(pygame.event.Event(pygame.TEXTINPUT, text="blocked"))
    assert terminal.text_buffer == ""
    send(machine, pygame.KEYDOWN, pygame.K_ESCAPE)
    assert not machine.pause.active and machine.current_state_name == config.STATE_CRT_TERMINAL
    send(machine, pygame.KEYDOWN, pygame.K_BACKSPACE)
    assert terminal.text_buffer == ""
    send(machine, pygame.KEYDOWN, pygame.K_ESCAPE)
    assert machine.current_state_name == config.STATE_BUNKER_HUB
    machine.update(0.5)
    assert hub.mateo_x == position and not machine.input.held("fire")
    machine.close()


@pytest.mark.parametrize("event_type", [pygame.WINDOWFOCUSLOST, pygame.WINDOWMINIMIZED,
                                        pygame.VIDEORESIZE, pygame.WINDOWRESIZED,
                                        pygame.WINDOWSIZECHANGED, pygame.QUIT])
def test_focus_resize_and_quit_release_held_inputs(display, event_type):
    machine = GameStateMachine(CRTRenderer())
    machine.change_state(config.STATE_BUNKER_HUB)
    send(machine, pygame.KEYDOWN, pygame.K_d)
    assert machine.input.held("move_right")
    machine.handle_event(pygame.event.Event(event_type))
    assert not machine.input.held("move_right")
    if event_type in (pygame.WINDOWFOCUSLOST, pygame.WINDOWMINIMIZED):
        assert machine.pause.active
    machine.close()


def test_legacy_focus_loss_clears_input_and_pauses(display):
    machine = GameStateMachine(CRTRenderer())
    machine.change_state(config.STATE_BUNKER_HUB)
    send(machine, pygame.KEYDOWN, pygame.K_d)
    machine.handle_event(pygame.event.Event(pygame.ACTIVEEVENT, state=2, gain=0))
    assert machine.pause.active and not machine.input.held("move_right")
    machine.close()


def test_pause_settings_apply_and_persist_after_restart(display, tmp_path):
    directory = tmp_path / "user_data"
    machine = GameStateMachine(CRTRenderer())
    machine.change_state(config.STATE_BUNKER_HUB)
    send(machine, pygame.KEYDOWN, pygame.K_ESCAPE)
    send(machine, pygame.KEYDOWN, pygame.K_DOWN)
    send(machine, pygame.KEYDOWN, pygame.K_RIGHT)
    send(machine, pygame.KEYDOWN, pygame.K_DOWN)
    send(machine, pygame.KEYDOWN, pygame.K_RIGHT)
    send(machine, pygame.KEYDOWN, pygame.K_DOWN)
    send(machine, pygame.KEYDOWN, pygame.K_LEFT)
    assert machine.settings == Settings(volume=80, crt_effects=False, scale=1)
    assert machine.crt.scale == 1 and machine.crt.is_crt_enabled is False
    assert SettingsStore(directory).load() == machine.settings
    machine.close()
    script = '''
import json
from dataclasses import asdict
from video_game.engine.settings import SettingsStore
print(json.dumps(asdict(SettingsStore().load()), sort_keys=True))
'''
    env = dict(os.environ, SIX_GAME_SAVE_DIR=str(directory))
    result = subprocess.run([sys.executable, "-c", script], cwd=REPO_ROOT,
                            env=env, capture_output=True, text=True, check=True)
    assert json.loads(result.stdout) == asdict(Settings(volume=80, crt_effects=False, scale=1))


def test_invalid_settings_fallback_and_failed_write_preserves_previous(tmp_path, monkeypatch):
    store = SettingsStore(tmp_path)
    store.path.write_text('{"schema_version":1,"volume":101,"scale":0,"crt_effects":"yes"}')
    assert store.load() == Settings(combat_mode="classic")
    assert store.warning and store.path.read_text().startswith('{"schema_version"')
    store.path.write_text('{"schema_version":1,"volume":20,"scale":99,"crt_effects":false}')
    assert store.load() == Settings(volume=20, crt_effects=False, scale=2, combat_mode="classic")
    store.path.write_text('{broken')
    assert store.load() == Settings() and store.warning
    valid = Settings(volume=50, crt_effects=False, scale=2)
    store.save(valid)
    prior = store.path.read_bytes()

    def fail_replace(source, destination):
        raise OSError("simulated settings replacement failure")

    monkeypatch.setattr(settings.os, "replace", fail_replace)
    with pytest.raises(SettingsError, match="simulated"):
        store.save(Settings(volume=40, crt_effects=True, scale=1))
    assert store.path.read_bytes() == prior and store.load() == valid


def test_resize_event_updates_integer_scale_and_releases_input(display, monkeypatch):
    original_set_mode = pygame.display.set_mode
    sizes = []

    def record_set_mode(size, *args, **kwargs):
        sizes.append(size)
        return original_set_mode(size, *args, **kwargs)

    event = pygame.event.Event(pygame.VIDEORESIZE, size=(1000, 600), w=1000, h=600)
    monkeypatch.setattr(pygame.display, "set_mode", record_set_mode)
    monkeypatch.setattr(pygame.event, "get", lambda: [event])
    assert game_main.run_game(max_frames=1) == 1
    assert sizes[-1] == (960, 540)
    assert SettingsStore().load().scale == 1


def test_normal_and_development_controls_are_separate(display):
    normal = GameStateMachine(CRTRenderer())
    normal.change_state(config.STATE_BUNKER_HUB)
    hub = normal.current_scene
    for key in (pygame.K_c, pygame.K_o, pygame.K_v, pygame.K_q, pygame.K_l, pygame.K_f, pygame.K_b):
        send(normal, pygame.KEYDOWN, key)
    assert (hub.civ_idx, hub.outfit_idx, hub.view_mode) == (0, 0, 0)
    assert normal.campaign.timeline_mode == "2029_CORE" and normal.current_state_name == config.STATE_BUNKER_HUB
    normal.close()
    dev = GameStateMachine(CRTRenderer(), development=True)
    dev.change_state(config.STATE_BUNKER_HUB)
    hub = dev.current_scene
    for key in (pygame.K_c, pygame.K_o, pygame.K_v, pygame.K_q):
        send(dev, pygame.KEYDOWN, key)
    assert (hub.civ_idx, hub.outfit_idx, hub.view_mode) == (1, 1, 1)
    assert dev.campaign.timeline_mode == "1977_ANALOG"
    send(dev, pygame.KEYDOWN, pygame.K_l)
    assert dev.current_state_name == config.STATE_SCIENCE_LAB
    dev.close()


def test_game_launch_receives_explicit_development_mode(display, monkeypatch):
    observed = []
    original = game_main.GameStateMachine

    class ObservedMachine(original):
        def __init__(self, crt, *args, **kwargs):
            super().__init__(crt, *args, **kwargs)
            observed.append(self.development)

    monkeypatch.setattr(game_main, "GameStateMachine", ObservedMachine)
    monkeypatch.setattr(pygame.event, "get", lambda: [pygame.event.Event(pygame.QUIT)])
    assert game_main.run_game(development=False) == 0
    assert game_main.run_game(development=True) == 0
    assert observed == [False, True]
    result = subprocess.run([sys.executable, "-m", "video_game.main", "--help"],
                            cwd=REPO_ROOT, capture_output=True, text=True, check=True)
    assert "--dev" in result.stdout
