"""MODULE: tests/test_guided_hub.py
PURPOSE: Exercise guided title and bunker actions through real Pygame events.
CALLED BY: pytest.
HOW TO MODIFY: Keep temporary saves and injected campaign events explicit;
  synthetic input is not a human playthrough or physical controller test.
"""
import json

import pygame
import pytest

from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.objectives import DishDefenseHoldout, ObjectiveTracker
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


def game(tmp_path, scale=1):
    pygame.display.set_mode((960 * scale, 540 * scale))
    settings = SettingsStore(tmp_path)
    settings.save(Settings(scale=scale, combat_mode='classic'))
    return GameStateMachine(CRTRenderer(scale=scale), save_store=SaveStore(tmp_path), settings_store=settings)


def key(machine, value):
    machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=value))


def click(machine, logical_x, logical_y):
    machine.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
        pos=(round(logical_x * machine.crt.win_w / 480), round(logical_y * machine.crt.win_h / 270))))


def skip_opening(machine):
    """Release the title activation, then skip with one ordinary arrow press."""
    machine.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_RETURN))
    machine.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(0, 0)))
    key(machine, pygame.K_DOWN)
    machine.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_DOWN))
    assert machine.current_scene.opening_story is None


def test_start_always_replaces_prior_run(tmp_path):
    first = game(tmp_path)
    try:
        assert first.current_scene.banner.get_size() == (960, 320)
        key(first, pygame.K_RETURN)
        assert first.current_state_name == config.STATE_BUNKER_HUB
        save_id = first.campaign.state.save_id
    finally:
        first.close()
    second = game(tmp_path)
    try:
        key(second, pygame.K_RETURN)
        assert second.current_state_name == config.STATE_BUNKER_HUB
        assert second.current_scene.opening_story.index == 0
        assert second.campaign.state.save_id != save_id
        assert second.save_store.load().campaign.state.save_id == second.campaign.state.save_id
        assert second.settings.combat_mode == 'classic'
    finally:
        second.close()


def test_missing_backup_api_leaves_main_save_intact(tmp_path):
    store = SaveStore(tmp_path)
    tmp_path.mkdir(parents=True, exist_ok=True)
    store.path.write_text('{broken')
    original = store.path.read_bytes()
    machine = game(tmp_path)
    try:
        assert machine.continue_game(recover=True).status == 'missing'
        assert machine.current_state_name == config.STATE_TITLE_BOOT
        assert store.path.read_bytes() == original
        assert machine.continue_game().status == 'corrupt'
        assert store.path.read_bytes() == original
    finally:
        machine.close()


def test_start_preserves_unreadable_save_before_starting_fresh(tmp_path):
    store = SaveStore(tmp_path)
    tmp_path.mkdir(parents=True, exist_ok=True)
    store.path.write_text(json.dumps({'schema_version': 999}))
    original = store.path.read_bytes()
    machine = game(tmp_path)
    try:
        key(machine, pygame.K_RETURN)
        assert machine.current_state_name == config.STATE_BUNKER_HUB
        assert store.load().status == 'ok'
        assert next(store.directory.glob('campaign.preserved-*.json')).read_bytes() == original
    finally:
        machine.close()


def test_next_and_manual_interact_use_different_existing_stations(tmp_path):
    machine = game(tmp_path)
    try:
        key(machine, pygame.K_RETURN)
        skip_opening(machine)
        bunker = machine.current_scene
        bunker.mateo_x = 140
        key(machine, pygame.K_SPACE)
        assert machine.current_state_name == config.STATE_CRT_TERMINAL
        machine.change_state(config.STATE_BUNKER_HUB)
        bunker.mateo_x = 140
        key(machine, pygame.K_e)
        assert machine.current_state_name == config.STATE_SCIENCE_LAB
    finally:
        machine.close()


def test_contact_without_fragment_keeps_receiver_next(tmp_path):
    machine = game(tmp_path)
    try:
        key(machine, pygame.K_RETURN)
        skip_opening(machine)
        machine.campaign.apply_event({'event_id': 'fixture_contact', 'type': 'record_contact',
                                      'payload': {'civilization_id': 'FASR-001'}})
        objective = ObjectiveTracker().get_active_objective(machine.campaign)
        assert objective.id == 'obj_tune_receiver' and objective.station_id == 'terminal'
        machine.campaign.apply_event({'event_id': 'fixture_fragment', 'type': 'grant_fragment_fasr_001'})
        objective = ObjectiveTracker().get_active_objective(machine.campaign)
        assert objective.id == 'obj_validate_signal' and objective.station_id == 'lab'
        key(machine, pygame.K_SPACE)
        assert machine.current_state_name == config.STATE_SCIENCE_LAB
    finally:
        machine.close()


def test_mouse_uses_actual_clipped_window_for_next(tmp_path):
    machine = game(tmp_path, scale=2)
    try:
        click(machine, *machine.current_scene.PRIMARY.center)
        assert machine.current_state_name == config.STATE_BUNKER_HUB
        skip_opening(machine)
        # Renderer is still 1920x1080 while this real dummy window is clipped to 960x540.
        pygame.display.set_mode((960, 540))
        machine.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(60, 190)))
        assert machine.current_state_name == config.STATE_CRT_TERMINAL
    finally:
        machine.close()


def test_jam_rate_defaults_to_classic_and_can_be_assisted():
    classic = DishDefenseHoldout()
    assisted = DishDefenseHoldout(jam_drain_rate=0.6)
    for holdout in (classic, assisted):
        holdout.start()
        holdout.is_jammed = True
        holdout.update(2.0)
    assert classic.dish_integrity == pytest.approx(98.0)
    assert assisted.dish_integrity == pytest.approx(98.8)


def test_next_repair_uses_campaign_event_and_keeps_manual_guard(tmp_path):
    machine = game(tmp_path)
    try:
        key(machine, pygame.K_RETURN)
        skip_opening(machine)
        campaign = machine.campaign
        # Explicitly injected progression sets up the repair stage.
        campaign.apply_event({'event_id': 'setup_contact', 'type': 'record_contact',
                              'payload': {'civilization_id': 'FASR-001'}})
        campaign.apply_event({'event_id': 'setup_fragment', 'type': 'grant_fragment_fasr_001'})
        campaign.apply_event({'event_id': 'setup_validation', 'type': 'validate_fasr_001_deploy'})
        campaign.apply_event({'event_id': 'setup_coupler', 'type': 'collect_analog_coupler'})
        assert ObjectiveTracker().get_active_objective(campaign).station_id == 'repair'
        key(machine, pygame.K_SPACE)
        assert campaign.state.room_flags.get('feedhorn_repaired')
        assert ObjectiveTracker().get_active_objective(campaign).id == 'obj_defeat_greenkeeper'
        assert machine.current_state_name == config.STATE_BUNKER_HUB
    finally:
        machine.close()


def test_dossier_captures_mouse_and_does_not_trigger_next(tmp_path):
    machine = game(tmp_path)
    try:
        key(machine, pygame.K_RETURN)
        skip_opening(machine)
        key(machine, pygame.K_TAB)
        assert machine.current_scene.dossier_open
        click(machine, 20, 50)
        assert machine.current_state_name == config.STATE_BUNKER_HUB
        assert machine.current_scene.dossier_open
    finally:
        machine.close()


def test_controller_a_starts_exits_and_restarts(tmp_path, monkeypatch):
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
    machine = game(tmp_path)
    def button(kind, value):
        machine.handle_event(pygame.event.Event(kind, instance_id=100, button=value))
    try:
        machine.handle_event(pygame.event.Event(pygame.CONTROLLERDEVICEADDED, device_index=0))
        button(pygame.CONTROLLERBUTTONDOWN, pygame.CONTROLLER_BUTTON_A)
        button(pygame.CONTROLLERBUTTONUP, pygame.CONTROLLER_BUTTON_A)
        assert machine.current_state_name == config.STATE_BUNKER_HUB
        button(pygame.CONTROLLERBUTTONDOWN, pygame.CONTROLLER_BUTTON_A)
        button(pygame.CONTROLLERBUTTONUP, pygame.CONTROLLER_BUTTON_A)
        assert machine.current_state_name == config.STATE_BUNKER_HUB
        button(pygame.CONTROLLERBUTTONDOWN, pygame.CONTROLLER_BUTTON_A)
        button(pygame.CONTROLLERBUTTONUP, pygame.CONTROLLER_BUTTON_A)
        assert machine.current_state_name == config.STATE_FIELD_OPS
        old_id = machine.campaign.state.save_id
        machine.change_state(config.STATE_TITLE_BOOT)
        button(pygame.CONTROLLERBUTTONDOWN, pygame.CONTROLLER_BUTTON_A)
        assert machine.current_state_name == config.STATE_BUNKER_HUB
        assert machine.campaign.state.save_id != old_id
        assert machine.current_scene.opening_story.index == 0
    finally:
        machine.close()


def test_one_click_starts_new_save(tmp_path):
    first = game(tmp_path)
    try:
        key(first, pygame.K_RETURN)
        old_id = first.campaign.state.save_id
    finally:
        first.close()
    second = game(tmp_path)
    try:
        click(second, *second.current_scene.PRIMARY.center)
        assert second.current_state_name == config.STATE_BUNKER_HUB
        assert second.campaign.state.save_id != old_id
    finally:
        second.close()


def test_all_next_labels_fit_button_and_completed_stage_is_honest(tmp_path):
    machine = game(tmp_path)
    try:
        key(machine, pygame.K_RETURN)
        bunker = machine.current_scene
        tracker = ObjectiveTracker()
        sequence = [
            ('record_contact', {'civilization_id': 'FASR-001'}),
            ('grant_fragment_fasr_001', {}),
            ('validate_fasr_001_deploy', {}),
            ('collect_analog_coupler', {}),
            ('repair_dish_feedhorn', {}),
            ('complete_dish_defense', {}),
            ('defeat_greenkeeper', {}),
        ]
        for index, (kind, payload) in enumerate(sequence):
            objective = tracker.get_active_objective(machine.campaign)
            label = 'NEXT: ' + objective.title
            assert machine.crt.font_sm.size(label)[0] <= bunker.NEXT_BUTTON.width - 14
            machine.campaign.apply_event({'event_id': f'fixture_{index}', 'type': kind, 'payload': payload})
        objective = tracker.get_active_objective(machine.campaign)
        assert not objective.is_completed and objective.station_id == 'field'
        assert 'NEO-DENVER' in objective.title
    finally:
        machine.close()
