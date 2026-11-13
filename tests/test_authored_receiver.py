"""MODULE: video_game/tests/test_authored_receiver.py
PURPOSE: Exercise workerless authored receiver, physical input and durable evidence.
CALLED BY: pytest video_game/tests/test_authored_receiver.py.
HOW TO MODIFY: Keep temporary saves, existing campaign events and no-model assertions.
"""
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
    pygame.display.set_mode((1920, 1080))
    machine = GameStateMachine(CRTRenderer(scale=2), save_store=SaveStore(tmp_path),
                               settings_store=SettingsStore(tmp_path))
    yield machine
    machine.close()
    pygame.quit()


def key(machine, code):
    machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=code))
    machine.update(1 / 60)
    machine.input.begin_frame()
    machine.handle_event(pygame.event.Event(pygame.KEYUP, key=code))
    machine.update(1 / 60)
    machine.input.begin_frame()


def start_receiver(machine):
    key(machine, pygame.K_n)
    assert machine.current_state_name == config.STATE_BUNKER_HUB
    key(machine, pygame.K_DOWN)  # Skip the title-start opening before receiver input.
    key(machine, pygame.K_e)
    assert machine.current_state_name == config.STATE_CRT_TERMINAL
    assert machine.current_scene.session.worker is None
    return machine.current_scene


def complete_pages(machine):
    while machine.current_scene._primary_label() == 'NEXT':
        key(machine, pygame.K_RETURN)


def test_workerless_startup_keyboard_receive_save_and_idempotent_reentry(game):
    terminal = start_receiver(game)
    assert terminal.session.is_offline and terminal.session.worker is None
    game.handle_event(pygame.event.Event(pygame.TEXTINPUT, text='2'))
    key(game, pygame.K_2)
    assert terminal.text_buffer == '' and not game.campaign.state.extracted_fragments
    complete_pages(game)
    key(game, pygame.K_RETURN)
    assert terminal.stage == 'received'
    assert 'FASR-001' in game.campaign.state.extracted_fragments
    assert 'FASR-001' in game.campaign.state.contacted_civs
    assert game.save_store.load().campaign.state.extracted_fragments == ['FASR-001']
    event_types = list(game.campaign.state.completed_event_types)
    complete_pages(game)
    key(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_BUNKER_HUB
    key(game, pygame.K_e)
    complete_pages(game)
    key(game, pygame.K_RETURN)
    assert game.current_scene.stage == 'received'
    assert game.campaign.state.completed_event_types == event_types
    assert game.campaign.state.extracted_fragments == ['FASR-001']


def test_mouse_hitboxes_receive_and_return(game):
    terminal = start_receiver(game)
    def click(rect):
        x, y = rect.center
        factor_x = game.crt.win_w / config.INTERNAL_WIDTH
        factor_y = game.crt.win_h / config.INTERNAL_HEIGHT
        game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                             pos=(int(x * factor_x), int(y * factor_y))))
    while terminal._primary_label() == 'NEXT':
        click(terminal.PRIMARY_RECT)
    click(terminal.PRIMARY_RECT)
    assert 'FASR-001' in game.campaign.state.extracted_fragments
    click(terminal.BACK_RECT)
    assert game.current_state_name == config.STATE_BUNKER_HUB


def test_controller_semantic_confirm_and_optional_seventh_signal(game):
    terminal = start_receiver(game)
    for _ in range(6):
        key(game, pygame.K_TAB)
    assert terminal.session.active_civ_id == 'FASR-007'
    complete_pages(game)
    game.handle_event(pygame.event.Event(pygame.CONTROLLERBUTTONDOWN,
                                         button=pygame.CONTROLLER_BUTTON_A, instance_id=999))
    assert 'FASR-007' in game.campaign.state.extracted_fragments
    assert terminal.session.target_mhz == 1418.9
    game.handle_event(pygame.event.Event(pygame.CONTROLLERBUTTONDOWN,
                                         button=pygame.CONTROLLER_BUTTON_B, instance_id=999))
    assert game.current_state_name == config.STATE_BUNKER_HUB


def test_all_known_archives_are_browsable_without_claiming_evidence(game):
    terminal = start_receiver(game)
    visited = []
    for _ in range(11):
        visited.append(terminal.session.active_civ_id)
        assert terminal.body and terminal._pages()
        assert all(len(page) <= terminal.LINES_PER_PAGE for page in terminal._pages())
        key(game, pygame.K_TAB)
    assert len(set(visited)) == 11
    assert terminal.session.active_civ_id == 'FASR-001'
    assert not game.campaign.state.extracted_fragments


def test_unavailable_or_unlocked_signal_does_not_fake_reward(game):
    terminal = start_receiver(game)
    complete_pages(game)
    terminal.session.is_locked = False
    key(game, pygame.K_RETURN)
    assert terminal.stage == 'greeting' and 'LOCK' in terminal.notice
    assert not game.campaign.state.extracted_fragments
    terminal.session.snap_to_carrier()
    terminal.session.offline_data['civilizations']['FASR-001']['evidence']['action'] = 'WRONG'
    key(game, pygame.K_RETURN)
    assert terminal.stage == 'greeting' and 'UNAVAILABLE' in terminal.notice
    assert not game.campaign.state.extracted_fragments


def test_save_failure_retry_never_regrants_evidence(game, monkeypatch):
    terminal = start_receiver(game)
    complete_pages(game)
    save = game.save_checkpoint
    monkeypatch.setattr(game, 'save_checkpoint', lambda: False)
    key(game, pygame.K_RETURN)
    assert terminal.stage == 'save_failed'
    assert game.campaign.state.extracted_fragments == ['FASR-001']
    event_types = list(game.campaign.state.completed_event_types)
    monkeypatch.setattr(game, 'save_checkpoint', save)
    complete_pages(game)
    key(game, pygame.K_RETURN)
    assert terminal.stage == 'received'
    assert game.campaign.state.completed_event_types == event_types
    assert game.save_store.load().campaign.state.extracted_fragments == ['FASR-001']


def test_workerless_signal_retry_is_not_blocked_by_chat_exchange_limit(game, monkeypatch):
    terminal = start_receiver(game)
    complete_pages(game)
    validator = terminal.session.validator
    original = validator.validate_and_grant_fragment
    monkeypatch.setattr(validator, 'validate_and_grant_fragment', lambda *args, **kwargs: (False, 'unavailable', None))
    for _ in range(13):
        key(game, pygame.K_RETURN)
        assert terminal.stage == 'greeting' and not game.campaign.state.extracted_fragments
    assert terminal.session.exchange_count == 13
    monkeypatch.setattr(validator, 'validate_and_grant_fragment', original)
    key(game, pygame.K_RETURN)
    assert terminal.stage == 'received'
    assert game.campaign.state.extracted_fragments == ['FASR-001']
