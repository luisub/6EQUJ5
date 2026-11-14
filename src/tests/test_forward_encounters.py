"""PURPOSE: Verify finite forward encounters through actual field input and room boundaries.
CALLED BY: pytest tests/test_forward_encounters.py.
HOW TO MODIFY: Exercise real movement and retain isolation of defense/prototype encounters.
"""
import json
from pathlib import Path

import pygame
import pytest

from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.encounter_director import DATA_PATH, ForwardEncounter
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.world import Room


@pytest.fixture
def game(tmp_path, monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    pygame.display.set_mode((960, 540))
    machine = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(tmp_path),
                               settings_store=SettingsStore(tmp_path))
    machine.start_new_game()
    machine.change_settings(combat_mode="assisted")
    machine.change_state(config.STATE_FIELD_OPS)
    try:
        yield machine
    finally:
        machine.close()
        pygame.quit()


def step(machine, frames=1):
    for _ in range(frames):
        machine.input.begin_frame()
        machine.update(1 / 60)


def key(machine, kind, code):
    machine.handle_event(pygame.event.Event(kind, key=code))


def test_physical_movement_triggers_warning_and_arrival(game):
    field = game.current_scene
    director = field.forward_encounter
    key(game, pygame.KEYDOWN, pygame.K_d)
    step(game, 12)
    assert director.warning is not None
    assert not field.enemy_manager.enemies
    step(game, 28)
    key(game, pygame.KEYUP, pygame.K_d)
    assert field.player.x > 80
    assert len(field.enemy_manager.enemies) >= 1
    assert field.enemy_manager.enemies[0].target_id == 'approach_hound_1'


def test_queue_caps_and_releases_and_never_replays(game):
    field = game.current_scene
    game.change_settings(combat_mode='classic')
    director = field.forward_encounter
    field.player.health = 10000  # Fixture isolates the staged queue.
    # Use actual field updates and real movement, stopping to let warnings play out.
    key(game, pygame.KEYDOWN, pygame.K_d)
    step(game, 40)
    key(game, pygame.KEYUP, pygame.K_d)
    step(game, 50)
    assert field.enemy_manager.enemies
    first_id = field.enemy_manager.enemies[0].target_id
    # Cross several trigger positions, then return to make their arrival zones safe.
    field.player.x = 500
    field.player.rect.x = 500
    step(game)
    field.player.x = 48
    field.player.rect.x = 48
    step(game, 200)
    triggered = director.next_trigger
    assert triggered >= 4
    assert sum(not e.is_dead for e in field.enemy_manager.enemies) == 4
    assert director.pending
    step(game, 60)
    assert director.next_trigger == triggered
    assert director.pending
    assert sum(e.target_id == first_id for e in field.enemy_manager.enemies) == 1
    before = {e.target_id for e in field.enemy_manager.enemies}
    field.enemy_manager.enemies[0].take_damage(1000, hit_id="test_kill")
    step(game, 100)
    assert {e.target_id for e in field.enemy_manager.enemies} - before
    assert len({e.target_id for e in field.enemy_manager.enemies}) == len(field.enemy_manager.enemies)



def test_pause_and_reentry_reset(game):
    field = game.current_scene
    step(game, 10)
    director = field.forward_encounter
    elapsed = director.warning_time
    game.pause.open()
    step(game, 60)
    assert director.warning_time == elapsed
    assert not field.enemy_manager.enemies
    game.pause.close()
    step(game, 40)
    assert field.enemy_manager.enemies
    field.load_room('act_01/salvage_yard.json', 'yard_entrance')
    assert field.forward_encounter is not director
    assert not field.enemy_manager.enemies
    assert field.forward_encounter.next_trigger == 0
    field.load_room('act_01/approach.json', 'bunker_exit')
    assert field.forward_encounter.next_trigger == 0


def test_room_definitions_are_safe_finite_and_unique(tmp_path, game):
    field = game.current_scene
    data = json.loads(DATA_PATH.read_text())
    all_ids = []
    for filename in ('approach', 'salvage_yard', 'dish_catwalk'):
        room = Room.load_from_file(config.DATA_DIR / 'levels/act_01' / (filename + '.json'))
        director = ForwardEncounter(room, field.enemy_manager)
        assert director.entries and all(director._safe(e) for e in director.entries)
        all_ids.extend(e['id'] for e in director.entries)
    assert len(all_ids) == len(set(all_ids))
    bad = tmp_path / 'bad.json'
    data['rooms']['act_01_approach'][0]['x'] = -10
    bad.write_text(json.dumps(data))
    assert not ForwardEncounter(field.room, field.enemy_manager, data_path=bad).entries
    bad.write_text('{')
    assert not ForwardEncounter(field.room, field.enemy_manager, data_path=bad).entries
    field.load_room('act_01/mandela_test.json', 'default')
    assert field.forward_encounter is None
    field.load_room('flashback/ehman_1977.json', 'ehman_entrance')
    assert field.forward_encounter is None
    assert not field.enemy_manager.enemies


def test_respawn_restarts_and_defense_excludes_director(game):
    field = game.current_scene
    step(game, 50)
    old = field.forward_encounter
    assert field.enemy_manager.enemies
    field.player.take_damage(10000, ignore_invulnerable=True)
    step(game, 2)
    assert field.player.respawn_count > 0
    assert field.forward_encounter is not old
    assert not field.enemy_manager.enemies
    assert field.forward_encounter.next_trigger == 1
    # The actual campaign event owns the repaired flag, as in the bunker repair route.
    game.campaign.apply_event({"event_id": "test_collect_coupler", "type": "collect_analog_coupler"})
    game.campaign.apply_event({"event_id": "test_repair", "type": "repair_dish_feedhorn"})
    field.load_room("act_01/dish_catwalk.json", "catwalk_start")
    assert field.holdout.is_active
    assert field.forward_encounter is None
    step(game, 60)
    assert field.holdout.elapsed_time > 0
    assert field.forward_encounter is None


def test_forward_catwalk_repair_requires_real_prerequisites_and_saves(game):
    from video_game.engine.campaign import seeded_development_campaign

    field = game.current_scene
    field.load_room('act_01/dish_service.json', 'east')
    field.player.x, field.player.y = field.room.width_px - 24, 208
    field.player.rect.topleft = (field.player.x, field.player.y)
    key(game, pygame.KEYDOWN, pygame.K_e)
    assert field.room.room_id == 'act_01_dish_catwalk'
    assert not game.campaign.state.inventory.get('analog_coupler', 0)
    field.player.x, field.player.y = 288, 208
    field.player.rect.topleft = (288, 208)
    key(game, pygame.KEYDOWN, pygame.K_e)
    assert not game.campaign.state.room_flags.get('feedhorn_repaired')
    assert field.objective_tracker.active_notification.title == 'VALIDATION REQUIRED'

    # Deliberately seeded validation is a fixture; the actual repair uses the normal key/event/save path.
    game.campaign = seeded_development_campaign()
    game.campaign.apply_event({'event_id': 'fixture_coupler_2', 'type': 'collect_analog_coupler'})
    key(game, pygame.KEYDOWN, pygame.K_e)
    assert game.campaign.state.room_flags['feedhorn_repaired']
    assert not game.campaign.state.inventory.get('analog_coupler', 0)
    assert field.holdout.is_active and field.forward_encounter is None
    assert game.save_store.load().campaign.state.room_flags['feedhorn_repaired']
    before = game.campaign.to_dict()
    key(game, pygame.KEYDOWN, pygame.K_e)
    assert game.campaign.to_dict() == before


def test_assisted_captain_profile_is_ready_before_enemy_step(game, tmp_path, monkeypatch):
    field = game.current_scene
    entry = {'id': 'test_captain', 'type': 'captain', 'trigger_x': 0, 'x': 224, 'y': 208}
    path = tmp_path / 'captain.json'
    path.write_text(json.dumps({'schema_version': 1, 'rooms': {field.room.room_id: [entry]}}))
    field.forward_encounter = ForwardEncounter(field.room, field.enemy_manager, True, path)
    observations = []
    actual_update = field.enemy_manager.update

    def observe(*args, **kwargs):
        if field.enemy_manager.enemies:
            enemy = field.enemy_manager.enemies[0]
            observations.append((field.player.combat_assisted, enemy.health, enemy.cfg.windup_time))
        return actual_update(*args, **kwargs)

    monkeypatch.setattr(field.enemy_manager, 'update', observe)
    step(game, 45)
    assert observations and observations[0] == (True, 30, 1.2)
    captain = field.enemy_manager.enemies[0]
    captain.facing = 'left'
    for i in range(3):
        captain.take_damage(25, hit_id=f'hit_{i}', hit_pos=(captain.x, captain.y))
    assert captain.is_dead


def test_passed_spawn_retries_at_a_validated_ahead_site(game, tmp_path):
    field = game.current_scene
    entry = {'id': 'delayed', 'type': 'hound', 'trigger_x': 0, 'x': 224, 'y': 220}
    path = tmp_path / 'delayed.json'
    path.write_text(json.dumps({'schema_version': 1, 'rooms': {field.room.room_id: [entry]}}))
    field.forward_encounter = ForwardEncounter(field.room, field.enemy_manager, True, path)
    field.player.x = 240
    field.player.rect.x = 240
    step(game, 45)
    assert len(field.enemy_manager.enemies) == 1
    enemy = field.enemy_manager.enemies[0]
    assert enemy.target_id == 'delayed'
    assert enemy.spawn_x > entry['x']
    assert enemy.spawn_x - field.player.rect.right >= 64
    assert field.forward_encounter._safe(dict(entry, x=enemy.spawn_x))


def test_catwalk_arena_exit_requires_no_repair_or_defense(game):
    field = game.current_scene
    field.load_room('act_01/dish_catwalk.json', 'catwalk_start')
    field.player.x, field.player.y = field.room.width_px - 60, 208
    field.player.rect.topleft = (field.player.x, field.player.y)
    key(game, pygame.KEYDOWN, pygame.K_e)
    assert game.current_state_name == config.STATE_BOSS_BOUNTY
    assert not game.campaign.state.room_flags.get('dish_defense_completed', False)


def test_bypassed_hostiles_retire_without_starving_forward_arrivals(game):
    field = game.current_scene
    director = field.forward_encounter
    seen = set()
    key(game, pygame.KEYDOWN, pygame.K_d)
    for frame in range(600):
        if frame >= 40 and (frame - 40) % 65 == 0:
            key(game, pygame.KEYDOWN, pygame.K_SPACE)
        if frame >= 50 and (frame - 50) % 65 == 0:
            key(game, pygame.KEYUP, pygame.K_SPACE)
        step(game)
        assert field.forward_encounter is director  # No death or room reset in this route.
        seen.update(enemy.target_id for enemy in field.enemy_manager.enemies)
        if field.player.x >= 850:
            break
    key(game, pygame.KEYUP, pygame.K_d)
    assert field.player.x > 500
    assert director.retired_ids
    assert len(seen | director.retired_ids) > 2
    assert not (director.retired_ids & {e.target_id for e in field.enemy_manager.enemies})
    assert not (director.retired_ids & {p.source_id for p in field.enemy_manager.projectiles})
    assert not (director.retired_ids & {e['id'] for e in director.pending})
    assert len(director.retired_ids) == len(set(director.retired_ids))


def test_field_repair_save_failure_is_visible_and_retryable(game, monkeypatch):
    from video_game.engine.campaign import seeded_development_campaign
    from video_game.engine.save_game import SaveError
    game.campaign = seeded_development_campaign()
    game.campaign.apply_event({'event_id': 'fixture_coupler_failure', 'type': 'collect_analog_coupler'})
    field = game.current_scene
    field.load_room('act_01/dish_catwalk.json', 'catwalk_start')
    field.player.x, field.player.y = 288, 208
    field.player.rect.topleft = (288, 208)
    save = game.save_store.save
    def fail(*args, **kwargs):
        raise SaveError('injected save failure')
    monkeypatch.setattr(game.save_store, 'save', fail)
    key(game, pygame.KEYDOWN, pygame.K_e)
    assert field.holdout.is_active
    assert game.campaign.state.room_flags['feedhorn_repaired']
    assert game.save_notice.startswith('SAVE FAILED')
    assert field.objective_tracker.active_notification.title == 'SAVE FAILED'
    assert not game.save_store.load().campaign.state.room_flags.get('feedhorn_repaired')
    before = game.campaign.to_dict()
    monkeypatch.setattr(game.save_store, 'save', save)
    key(game, pygame.KEYDOWN, pygame.K_F5)
    assert game.save_notice == 'CHECKPOINT SAVED'
    assert game.save_store.load().campaign.to_dict() == before
