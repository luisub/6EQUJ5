"""
═══════════════════════════════════════════════════════
MODULE: tests/test_act_01_playthrough.py
PURPOSE: Gate G2 and Task A14 acceptance regression tests:
         end-to-end Act I route walkthrough, hazard death recovery,
         72s dish defense failure & retry, Greenkeeper 3-phase combat,
         and save/reload roundtrip persistence.
CALLED BY: pytest (`pytest tests/test_act_01_playthrough.py -v`).
HOW TO MODIFY:
  - Add edge-case assertion branches or route variants.
═══════════════════════════════════════════════════════
"""

from . import REPO_ROOT

import os
import sys
from pathlib import Path

REPO_ROOT_DIR = REPO_ROOT
if str(REPO_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT_DIR))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402
import pytest  # noqa: E402
from video_game.engine import config  # noqa: E402
from video_game.engine.bosses.greenkeeper import Greenkeeper  # noqa: E402
from video_game.engine.objectives import DishDefenseHoldout  # noqa: E402
from video_game.tools.play_act_01 import Act01PlaythroughRunner  # noqa: E402


@pytest.fixture(autouse=True)
def isolated_save_directory(tmp_path, monkeypatch):
    monkeypatch.setenv("SIX_GAME_SAVE_DIR", str(tmp_path / "saves"))
    monkeypatch.setattr("video_game.tools.play_act_01.EVIDENCE_DIR", tmp_path)


def test_act_01_canonical_playthrough_route():
    """Exercise campaign components with fixture shortcuts; this is not gate acceptance."""
    runner = Act01PlaythroughRunner(headless=True)
    try:
        payload = runner.run_full_act_01_playthrough()
        assert payload["status"] == "PASSED"
        assert payload["gate_g2_verdict"] == "NOT_VERIFIED"
        assert payload["final_campaign_state"]["act_01_completed"] is True
        assert payload["final_campaign_state"]["act_02_unlocked"] is True
        assert "FASR-001" in payload["final_campaign_state"]["extracted_fragments"]
        assert "FASR-007" in payload["final_campaign_state"]["extracted_fragments"]
        assert payload["final_campaign_state"]["validation_count"] == 1
    finally:
        runner.machine.close()


def test_act_01_dish_defense_holdout_dynamics():
    """Verify 72-second defense progression, wave spawning, and failure reset."""
    holdout = DishDefenseHoldout()
    holdout.start()
    assert holdout.is_active is True

    # Test integrity failure
    holdout.damage_dish(120.0)
    assert holdout.is_failed is True
    assert holdout.failure_reason == "DISH DESTROYED BY HOSTILES"

    # Reset and simulate clean 72s completion
    holdout.reset()
    holdout.start()
    assert holdout.is_active is True

    # Step through 72 seconds
    for _ in range(73):
        events = holdout.update(1.0)
        if holdout.is_jammed:
            holdout.unjam()

    assert holdout.is_completed is True
    assert holdout.elapsed_time >= 72.0


def test_act_01_greenkeeper_3phase_mechanics():
    """Verify 3-phase combat, transition state immunity, and defeat idempotence."""
    boss = Greenkeeper(100.0, 100.0)
    boss.skip_intro()
    assert boss.current_phase == 1
    assert boss.health == 300

    # Phase 1 -> Phase 2 (100 damage)
    res = boss.take_damage(100)
    assert res.damage_dealt == 100
    assert boss.current_phase == 2
    assert boss.phase_state == "TRANSITION"

    # Advance through transition
    boss.update(1.0)
    assert boss.phase_state != "TRANSITION"

    # Phase 2 -> Phase 3 (100 damage)
    res = boss.take_damage(100)
    assert res.damage_dealt == 100
    assert boss.current_phase == 3
    assert boss.phase_state == "TRANSITION"

    boss.update(1.0)

    # Phase 3 -> Defeated (100 damage)
    res = boss.take_damage(100)
    assert res.damage_dealt == 100
    assert boss.is_defeated is True



def test_fresh_save_normal_input_reaches_salvage_yard():
    """Actual events cross the approach sump and wall before taking the exit."""
    from video_game.tools.act_01_traversal import traverse
    result = traverse()
    assert result['room'] == 'act_01_salvage_yard'
    assert [entry['action'] for entry in result['trace'][:2]] == ['contact', 'formal_validation']
    assert [entry['obstacle'] for entry in result['trace'] if entry['action'] == 'jump'] == [
        'sump', 'wall', 'service_hazard_west', 'service_hazard_east']
    assert [entry['room'] for entry in result['trace'] if entry['action'] == 'exit_interaction'] == [
        'act_01_ohio_campus', 'act_01_salvage_yard']
    assert result['field_health'] > 0
    assert result['gate_g2'] == 'not verified'


def test_salvage_encounter_starts_within_room(tmp_path):
    """Room entry never leaves the yard hound outside its world bounds."""
    from video_game.engine.crt_renderer import CRTRenderer
    from video_game.engine.save_game import SaveStore
    from video_game.engine.state_machine import GameStateMachine

    pygame.init()
    pygame.display.set_mode((480, 270))
    machine = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(str(tmp_path)))
    try:
        field = machine.scenes[config.STATE_FIELD_OPS]
        field.load_room('act_01/salvage_yard.json')
        for enemy in field.enemy_manager.enemies:
            assert 0 <= enemy.rect.left < enemy.rect.right <= field.room.width_px
            assert 0 <= enemy.patrol_left <= enemy.patrol_right <= field.room.width_px - enemy.rect.width
            collision = field.room.check_rect_collision(enemy.rect)
            assert not collision["solid"] and not collision["hazard"]
    finally:
        machine.close()


def test_complete_fresh_save_keyboard_route_and_child_reload(tmp_path):
    """The ordered offline route completes the actual holdout and boss with keys."""
    from video_game.tools.act_01_traversal import traverse
    result = traverse(complete=True, output_dir=tmp_path)
    actions = result['trace']
    assert [e['room'] for e in actions if e['action'] == 'exit_interaction'] == [
        'act_01_ohio_campus', 'act_01_salvage_yard', 'act_01_dish_catwalk']
    assert next(e for e in actions if e['action'] == 'coupler_pickup')['physical']
    assert next(e for e in actions if e['action'] == 'feedhorn_repaired')['room'] == 'act_01_dish_catwalk'
    assert next(e for e in actions if e['action'] == 'boss_entry')['method'] == 'up'
    assert sum(v['defeated'] for v in result['forward_observations'].values()) > 0
    defense = next(e for e in actions if e['action'] == 'defense_result')
    assert defense['completed'] and defense['elapsed_seconds'] == 72.0
    assert defense['waves'] == ['wave_01', 'wave_02', 'wave_03']
    assert next(e for e in actions if e['action'] == 'boss_defeated')['boss_changes'][-1]['health'] == 0
    loaded = next(e for e in actions if e['action'] == 'separate_process_save_load')['state']
    assert loaded['scene'] == 'BUNKER_HUB'
    assert {'FASR-001', 'FASR-007'} <= set(loaded['fragments'])
    assert loaded['flags']['act_01_completed'] and loaded['flags']['act_02_unlocked']
    assert 'formal_fasr_001' in loaded['validations']
    assert result['gate_g2'] == 'not verified'


def test_fresh_save_failure_retry_and_save_boundaries(tmp_path):
    """Actual enemy pressure and boss attacks precede retry and victory."""
    from video_game.tools.act_01_traversal import traverse
    result = traverse(recovery=True, output_dir=tmp_path)
    actions = {entry['action']: entry for entry in result['trace']}
    assert actions['defense_pause']['paused_frames'] == 120
    assert actions['defense_exit_reentry']['saved_repair']
    assert actions['defense_failed']['reason'] == 'DISH INTEGRITY COLLAPSED'
    assert actions['failed_defense_exit_reentry']['integrity'] == 100
    assert not actions['failed_defense_exit_reentry']['saved_completion']
    assert actions['defense_failed_again']['reason']
    assert not actions['defense_retry']['ability_edge_pending']
    assert actions['defense_retry']['ability_before'] == actions['defense_retry']['ability_after']
    assert actions['defense_result']['completed'] and actions['defense_saved']['completed']
    assert actions['boss_death']['boss_health'] == 300
    assert actions['boss_death_exit_reentry']['health'] == 100
    assert actions['boss_death_exit_reentry']['boss_health'] == 300
    assert not actions['boss_death_exit_reentry']['saved_completion']
    assert actions['boss_death_again']['boss_health'] == 300
    assert actions['boss_retry']['ability_before'] == actions['boss_retry']['ability_after']
    assert actions['boss_replay_idempotent']['saved_before_exit'] is True
    assert actions['boss_exit_saved']['completed']
    assert actions['separate_process_save_load']['state']['flags']['act_01_completed']


@pytest.mark.parametrize('scene_name', [config.STATE_FIELD_OPS, config.STATE_BOSS_BOUNTY])
def test_retry_consumes_r_without_disabling_later_ability_cycle(tmp_path, scene_name):
    """Fixture sets failure and two unlocks to expose the shared R binding."""
    from video_game.engine.crt_renderer import CRTRenderer
    from video_game.engine.save_game import SaveStore
    from video_game.engine.settings import SettingsStore
    from video_game.engine.state_machine import GameStateMachine

    pygame.init()
    pygame.display.set_mode((480, 270))
    machine = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(tmp_path),
                               settings_store=SettingsStore(tmp_path))
    try:
        machine.change_state(scene_name)
        scene = machine.current_scene
        if scene_name == config.STATE_FIELD_OPS:
            scene.holdout = DishDefenseHoldout()
            scene.holdout.start()
            scene.holdout.fail('fixture failure')
        else:
            # Begin the retry fixture after the real encounter reveal.
            machine.update(1.6)
            scene.player.is_dead = True
        abilities = scene.player.abilities
        for ability in abilities.abilities.values():
            ability.is_unlocked = False
        abilities.abilities['decoy'].is_unlocked = True
        abilities.abilities['time_dilation'].is_unlocked = True
        abilities.selected_ability_id = 'decoy'

        def press(code):
            machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=code))
            machine.update(1 / 60)
            machine.input.begin_frame()
            machine.handle_event(pygame.event.Event(pygame.KEYUP, key=code))
            machine.update(1 / 60)
            machine.input.begin_frame()

        press(pygame.K_r)
        assert abilities.selected_ability_id == 'decoy'
        press(pygame.K_r)
        assert abilities.selected_ability_id == 'time_dilation'
    finally:
        machine.close()


def test_boss_checkpoint_failure_is_reported_once(tmp_path, monkeypatch):
    """Fixture simulates a reward and a failing store; it is not route evidence."""
    from video_game.engine.crt_renderer import CRTRenderer
    from video_game.engine.save_game import SaveError, SaveStore
    from video_game.engine.settings import SettingsStore
    from video_game.engine.state_machine import GameStateMachine

    pygame.init()
    pygame.display.set_mode((480, 270))
    store = SaveStore(tmp_path)
    machine = GameStateMachine(CRTRenderer(scale=1), save_store=store,
                               settings_store=SettingsStore(tmp_path))
    try:
        machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_n))
        machine.change_state(config.STATE_BOSS_BOUNTY)
        # Exercise failure after the intro has actually elapsed.
        machine.update(1.6)
        boss = machine.current_scene.boss
        monkeypatch.setattr(boss, 'resolve_simultaneous_death', lambda alive: 'BOSS_DEFEATED')
        monkeypatch.setattr(boss, 'apply_defeat_reward', lambda campaign: True)
        attempts = []
        def fail_save(campaign):
            attempts.append(1)
            raise SaveError('fixture failure')
        monkeypatch.setattr(store, 'save', fail_save)
        machine.update(1 / 60)
        machine.update(1 / 60)
        assert len(attempts) == 1
        assert machine.save_notice.startswith('SAVE FAILED - F5 RETRY:')
    finally:
        machine.close()
