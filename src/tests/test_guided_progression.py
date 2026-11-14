"""PURPOSE: Verify guided first progression and Assisted safety at actual scene boundaries.
CALLED BY: pytest video_game/tests/test_guided_progression.py.
HOW TO MODIFY: Preserve real input routing, actual validators and temporary save isolation.
"""
from types import SimpleNamespace

import pygame
import pytest

from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.objectives import DishDefenseHoldout
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import Settings, SettingsStore
from video_game.engine.state_machine import GameStateMachine


@pytest.fixture
def game(tmp_path, monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER', 'dummy')
    monkeypatch.setenv('SDL_AUDIODRIVER', 'dummy')
    pygame.init()
    pygame.display.set_mode((960, 540))
    machine = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(tmp_path),
                               settings_store=SettingsStore(tmp_path))
    try:
        yield machine
    finally:
        machine.close()
        pygame.quit()


def tap(machine, code):
    machine.input.begin_frame()
    machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=code))
    machine.update(1/60)
    machine.handle_event(pygame.event.Event(pygame.KEYUP, key=code))


def test_fresh_guided_route_validates_without_typing_or_ai(game):
    tap(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_BUNKER_HUB
    tap(game, pygame.K_DOWN)  # Skip the title-start opening before guided interaction.
    game.current_scene.mateo_x = 248  # Visit the optional receiver explicitly.
    tap(game, pygame.K_e)
    assert game.current_state_name == config.STATE_CRT_TERMINAL
    assert game.contact_session.worker is None
    terminal = game.current_scene
    initial = (terminal.stage, terminal.page_index)
    game.handle_event(pygame.event.Event(pygame.TEXTINPUT, text='2'))
    assert (terminal.stage, terminal.page_index) == initial
    for _ in range(20):
        if 'FASR-001' in game.campaign.state.extracted_fragments:
            break
        tap(game, pygame.K_RETURN)
    assert 'FASR-001' in game.campaign.state.extracted_fragments
    tap(game, pygame.K_ESCAPE)
    assert game.current_state_name == config.STATE_BUNKER_HUB
    game.current_scene.mateo_x = 140  # Visit the optional lab explicitly.
    tap(game, pygame.K_e)
    assert game.current_state_name == config.STATE_SCIENCE_LAB
    lab = game.current_scene
    assert lab.guided and lab.workbench.active_scenario_id == 'formal_fasr_001'
    for expected in ('CLAIM', 'EVIDENCE', 'REPLICATION', 'DEPLOYMENT', 'COMPLETED'):
        tap(game, pygame.K_RETURN)
        assert lab.workbench.current_step == expected
    records = [r for r in game.campaign.state.validation_records if r['scenario_id'] == 'formal_fasr_001']
    assert len(records) == 1 and records[0]['deployment_decision'] == 'deploy_analog_filter'
    assert game.save_store.load().campaign.to_dict() == game.campaign.to_dict()
    tap(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_BUNKER_HUB
    before = game.campaign.to_dict()
    game.change_state(config.STATE_SCIENCE_LAB)  # Explicit replay fixture.
    assert game.current_scene.workbench.current_step == 'COMPLETED'
    tap(game, pygame.K_RETURN)
    assert game.campaign.to_dict() == before
    # A held click on the base's NEXT button must not become a field shot.
    game.input.begin_frame()
    pos = (round(40 * game.crt.win_w / 480), round(50 * game.crt.win_h / 270))
    game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
    assert game.current_state_name == config.STATE_FIELD_OPS
    game.update(1/60)
    assert not game.current_scene.projectile_manager.projectiles
    assert len([r for r in game.campaign.state.validation_records if r['scenario_id'] == 'formal_fasr_001']) == 1


def test_returning_from_manual_advanced_reselects_first_guided_lesson(game):
    assert game.start_new_game()[0]
    game.change_state(config.STATE_CRT_TERMINAL)
    for _ in range(20):
        if 'FASR-001' in game.campaign.state.extracted_fragments:
            break
        tap(game, pygame.K_RETURN)
    assert 'FASR-001' in game.campaign.state.extracted_fragments
    game.change_state(config.STATE_SCIENCE_LAB)
    lab = game.current_scene
    tap(game, pygame.K_m)
    assert not lab.guided
    lab._select_active(lab.scenario_keys.index('formal_adv_fasr_001'))
    assert lab.workbench.active_scenario_id == 'formal_adv_fasr_001'
    tap(game, pygame.K_m)
    assert lab.guided and lab.guided_intro
    assert lab.workbench.active_scenario_id == 'formal_fasr_001'
    tap(game, pygame.K_RETURN)
    assert lab.workbench.active_scenario_id == 'formal_fasr_001'
    assert not game.campaign.state.validation_records


def test_controller_confirm_exits_and_back_works_in_guided_scene(game):
    def button(value):
        game.input.begin_frame()
        game.handle_event(pygame.event.Event(pygame.CONTROLLERBUTTONDOWN, instance_id=37, button=value))
        game.update(1/60)
        game.handle_event(pygame.event.Event(pygame.CONTROLLERBUTTONUP, instance_id=37, button=value))
    game.input._controller_state[37] = {'buttons':set(), 'axes':{}}
    button(pygame.CONTROLLER_BUTTON_A)
    assert game.current_state_name == config.STATE_BUNKER_HUB
    button(pygame.CONTROLLER_BUTTON_A)  # Skip the title-start opening.
    button(pygame.CONTROLLER_BUTTON_A)
    assert game.current_state_name == config.STATE_FIELD_OPS
    game.change_state(config.STATE_CRT_TERMINAL)
    button(pygame.CONTROLLER_BUTTON_B)
    assert game.current_state_name == config.STATE_BUNKER_HUB


@pytest.mark.parametrize('mode, expected', [('assisted', 100), ('classic', 40)])
def test_safe_bunker_heals_only_assisted_and_not_room_entry(game, mode, expected):
    assert game.start_new_game()[0]
    assert game.change_settings(combat_mode=mode)
    game.change_state(config.STATE_FIELD_OPS, room='act_01/approach.json', spawn='approach_checkpoint')
    scene = game.current_scene
    scene.player.health = 40
    scene.load_room('act_01/salvage_yard.json', spawn_name='yard_entrance')
    assert scene.player.health == 40
    game.change_state(config.STATE_BUNKER_HUB)
    assert scene.player.health == expected


@pytest.mark.parametrize('mode, enemy_drain, jam_drain', [('assisted', .35, .6), ('classic', .65, 1.0)])
def test_holdout_profile_rates_and_unjam(game, mode, enemy_drain, jam_drain):
    assert game.start_new_game()[0]
    assert game.change_settings(combat_mode=mode)
    game.change_state(config.STATE_FIELD_OPS, room='act_01/dish_catwalk.json', spawn='catwalk_start')
    scene = game.current_scene
    defense = DishDefenseHoldout()
    defense.start()
    defense.update(.01)  # Consume the scheduled first-wave event for the isolated rate fixture.
    scene.holdout = defense
    scene.enemy_manager.enemies = [SimpleNamespace(is_dead=False)]
    scene._defense_pressure_delay = 0
    scene._update_defense(1.0, False)
    assert defense.dish_integrity == pytest.approx(100 - enemy_drain)
    scene.enemy_manager.enemies = []
    defense.is_jammed = True
    scene._update_defense(1.0, False)
    assert defense.dish_integrity == pytest.approx(100 - enemy_drain - jam_drain)
    scene.player.x = 312
    tap(game, pygame.K_e)
    assert not defense.is_jammed
