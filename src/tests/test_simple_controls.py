"""PURPOSE: Guard the compact interface and simple physical input routes.
CALLED BY: pytest.
HOW TO MODIFY: Exercise real routed events and temporary user data; keep legacy controls.
"""
import pygame
import pytest

from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.input import InputManager
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine


@pytest.fixture
def game(tmp_path):
    pygame.init()
    pygame.display.set_mode((960, 540))
    machine = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(tmp_path),
                               settings_store=SettingsStore(tmp_path))
    machine.start_new_game()
    yield machine
    machine.close()
    pygame.quit()


def key(machine, value):
    machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=value))


def test_consumed_up_preserves_space_and_controller_jump():
    actions = InputManager()
    actions.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP))
    assert actions.pressed("jump")
    actions.consume_key(pygame.K_UP)
    assert not actions.held("jump") and not actions.pressed("jump")
    actions.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
    actions.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP))
    actions.consume_key(pygame.K_UP)
    assert actions.held("jump") and actions.pressed("jump")
    actions.release_all()
    actions._controller_state[7] = {"buttons": set(), "axes": {}}
    actions.handle_event(pygame.event.Event(pygame.CONTROLLERBUTTONDOWN,
                         instance_id=7, button=pygame.CONTROLLER_BUTTON_A))
    actions.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP))
    actions.consume_key(pygame.K_UP)
    assert actions.held("jump") and actions.pressed("jump")


def test_pause_space_arrows_mouse_and_focus_reset(game):
    game.change_state(config.STATE_FIELD_OPS)
    key(game, pygame.K_RIGHT)
    game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=3, pos=(400, 250)))
    assert game.input.held("move_right") and game.input.held("fire")
    game.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
    assert game.pause.active and not game.input.held("move_right") and not game.input.held("fire")
    key(game, pygame.K_DOWN)
    assert game.pause.selected == 1
    before = game.settings.volume
    key(game, pygame.K_SPACE)
    assert game.settings.volume != before
    # Scale 1 maps a displayed logical point to a 960x540 viewport.
    game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(int(112 * game.crt.win_w / 480), int(52 * game.crt.win_h / 270))))
    assert not game.pause.active and not game.input.held("auto_fire")


def test_hud_shows_goal_without_persistent_control_legend(game, monkeypatch):
    game.change_state(config.STATE_FIELD_OPS)
    drawn = []
    original = game.crt.draw_text
    def capture(text, *args, **kwargs):
        drawn.append(text)
        return original(text, *args, **kwargs)
    monkeypatch.setattr(game.crt, 'draw_text', capture)
    game.render()
    assert 'RECEIVE THE SIGNAL' in drawn and any(text.startswith('HP ') for text in drawn)
    assert not any('MOUSE AIM' in text or '2029_CORE' in text for text in drawn)


def test_title_start_and_bunker_context_are_clickable(game):
    game.change_state(config.STATE_TITLE_BOOT)
    pygame.display.set_mode((game.crt.win_w, game.crt.win_h))
    def click(rect):
        game.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1,
            pos=(int(rect.centerx * game.crt.win_w / 480),
                 int(rect.centery * game.crt.win_h / 270))))
    title = game.current_scene
    click(title.PRIMARY)
    assert game.current_state_name == config.STATE_BUNKER_HUB
    game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(0, 0)))
    key(game, pygame.K_DOWN)
    game.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_DOWN))
    bunker = game.current_scene
    assert bunker.opening_story is None
    click(bunker.DETAILS_BUTTON)
    assert bunker.dossier_open
    click(bunker.DETAILS_BUTTON)
    assert not bunker.dossier_open
    click(bunker.DETAILS_BUTTON)
    key(game, pygame.K_ESCAPE)
    assert not bunker.dossier_open and not game.pause.active
    bunker.mateo_x = 140
    _, prompt = bunker.station_prompt(game.crt)
    click(prompt)
    assert game.current_state_name == config.STATE_SCIENCE_LAB


def test_bunker_up_exits_without_jump(game):
    game.change_state(config.STATE_BUNKER_HUB)
    game.current_scene.mateo_x = 140
    key(game, pygame.K_UP)
    assert game.current_state_name == config.STATE_FIELD_OPS
    assert not game.input.held("jump")
