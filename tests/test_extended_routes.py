"""PURPOSE: Verify the added Ohio service route through real routed input.
CALLED BY: pytest tests/test_extended_routes.py.
HOW TO MODIFY: Keep temporary saves and disclose position fixtures and enemy clearing.
"""
from pathlib import Path
import json

import pygame
import pytest

from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.encounter_director import ForwardEncounter
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.world import Room


@pytest.fixture
def game(tmp_path, monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER', 'dummy')
    monkeypatch.setenv('SDL_AUDIODRIVER', 'dummy')
    pygame.init()
    pygame.display.set_mode((960, 540))
    machine = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(tmp_path),
                               settings_store=SettingsStore(tmp_path))
    assert machine.start_new_game()[0]
    machine.change_settings(combat_mode='assisted')
    pygame.display.set_mode((machine.crt.win_w, machine.crt.win_h))
    machine.change_state(config.STATE_FIELD_OPS, room='act_01/approach.json', spawn='dish_perimeter')
    yield machine
    machine.close()
    pygame.quit()


def tap(machine, key):
    machine.input.begin_frame()
    machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))
    machine.update(1 / 60)
    machine.handle_event(pygame.event.Event(pygame.KEYUP, key=key))


def place(scene, x, y=208):
    # Only the entry and reverse exits are position fixtures; the corridor is walked.
    scene.player.x, scene.player.y = x, y
    scene.player.rect.topleft = (x, y)
    scene.player.vx = scene.player.vy = 0


def test_connected_route_and_actual_corridor_traversal(game):
    field = game.current_scene
    place(field, field.room.width_px - 24, 208)
    tap(game, pygame.K_RIGHT)
    assert field.room.room_id == 'act_01_ohio_campus'
    assert not game.input.held('jump')
    assert field.player.x == pytest.approx(64)
    game.change_settings(combat_mode='classic')
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
    jumped = set()
    release_at = -1
    checkpoint = None
    # Walk the full campus using real input; enemy clearing isolates the terrain.
    for frame in range(900):
        game.input.begin_frame()
        field.enemy_manager.clear()
        x = field.player.x
        checkpoint = field.player.active_checkpoint_id or checkpoint
        for threshold in (590, 958):
            if threshold <= x < threshold + 8 and threshold not in jumped:
                game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
                jumped.add(threshold)
                release_at = frame + 35
        if frame == release_at:
            game.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_SPACE))
        game.update(1 / 60)
        if field.room.room_id != 'act_01_ohio_campus':
            break
    game.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_RIGHT))
    assert jumped == {590, 958}
    assert checkpoint == 'campus_east'
    assert field.room.room_id == 'act_01_salvage_yard'
    place(field, 8, 208)
    tap(game, pygame.K_LEFT)
    assert field.room.room_id == 'act_01_ohio_campus'
    assert field.player.x == pytest.approx(field.room.width_px - 80)
    place(field, 0)
    tap(game, pygame.K_LEFT)
    assert field.room.room_id == 'act_01_approach'


def test_context_click_consumed_and_space_still_jumps(game):
    field = game.current_scene
    field.load_room('act_01/dish_catwalk.json', 'catwalk_start')
    place(field, field.room.width_px - 60, 208)
    p = (round(220 * game.crt.win_w / 480), round(213 * game.crt.win_h / 270))
    game.input.begin_frame()
    game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=p))
    assert field.room.room_id == 'act_01_dish_catwalk'
    assert field.objective_tracker.active_notification.title == 'ARENA SEALED'
    game.update(1 / 60)
    assert not game.input.held('fire')
    assert not field.projectile_manager.projectiles
    game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=p))
    for _ in range(20):
        game.input.begin_frame(); game.update(1 / 60)
    y = field.player.y
    tap(game, pygame.K_SPACE)
    assert field.player.y < y


def test_registered_geometry_and_finite_encounters(game):
    root = config.DATA_DIR
    room = Room.load_from_file(root / 'levels/act_01/ohio_campus.json')
    assert room.validate(json.loads((root / 'campaign.json').read_text())) == []
    assert (room.width_px, room.height_px) == (1280, 288)
    assert [room.get_tile(x, 14) for x in (40, 41, 63, 64)] == [3] * 4
    director = ForwardEncounter(room, game.current_scene.enemy_manager)
    assert len(director.entries) == 6
    assert all(director._safe(entry) for entry in director.entries)
    assert all(director.sites[entry['id']] for entry in director.entries)


def test_checkpoint_pause_reentry_and_continue(game):
    field = game.current_scene
    field.load_room('act_01/ohio_campus.json', 'campus_entry')
    traffic = field.service_traffic
    place(field, 576)
    game.update(1 / 60)
    assert field.player.active_checkpoint_id == 'service_mid'
    elapsed = traffic.elapsed
    game.open_pause()
    game.update(1)
    assert traffic.elapsed == elapsed
    game.pause.close()
    field.player.take_damage(10000, ignore_invulnerable=True)
    game.update(1 / 60)
    assert field.player.respawn_count > 0
    assert field.player.x == pytest.approx(576)
    old_director = field.forward_encounter
    field.load_room('act_01/salvage_yard.json', 'yard_entrance')
    field.load_room('act_01/ohio_campus.json', 'campus_east')
    assert field.forward_encounter is not old_director
    assert field.forward_encounter.next_trigger == 0
    assert game.save_checkpoint()
    assert game.continue_game().status == 'ok'
    assert game.current_state_name == config.STATE_BUNKER_HUB


@pytest.mark.parametrize('mode, cap', [('assisted', 5), ('classic', 4)])
def test_service_encounters_respect_profile_cap(game, mode, cap):
    assert game.change_settings(combat_mode=mode)
    field = game.current_scene
    field.load_room('act_01/ohio_campus.json', 'campus_entry')
    # Position and health fixtures allow several arrivals without making combat a prerequisite.
    place(field, 550)
    field.player.health = 10000
    observed = 0
    for _ in range(500):
        game.input.begin_frame()
        game.update(1 / 60)
        alive = sum(not enemy.is_dead for enemy in field.enemy_manager.enemies)
        observed = max(observed, alive)
        assert alive <= cap
    assert observed >= 3  # Safe-site spacing can leave the higher cap unused.


def test_up_jumps_away_from_context_and_right_walks_into_next_area(game):
    game.change_settings(combat_mode='classic')
    field = game.current_scene
    field.load_room('act_01/ohio_campus.json', 'campus_entry')
    for _ in range(20):
        game.input.begin_frame(); game.update(1 / 60)
    y = field.player.y
    tap(game, pygame.K_UP)
    assert field.player.y < y
    place(field, field.room.width_px - 62)
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
    for _ in range(30):
        game.input.begin_frame(); game.update(1 / 60)
    game.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_RIGHT))
    assert field.room.room_id == 'act_01_salvage_yard'


def test_approach_right_boundary_remains_actionable(game):
    game.change_settings(combat_mode='classic')
    field = game.current_scene
    place(field, field.room.width_px - 44, 208)
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
    for _ in range(40):
        game.input.begin_frame(); game.update(1 / 60)
    game.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_RIGHT))
    assert field.room.room_id == 'act_01_ohio_campus'
    assert field.player.x > 64


def test_context_up_does_not_consume_separate_held_space(game):
    field = game.current_scene
    field.load_room('act_01/dish_catwalk.json', 'catwalk_start')
    place(field, 288)
    game.input.begin_frame()
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP))
    # Validation guard declines the repair without leaving the room.
    assert field.room.room_id == 'act_01_dish_catwalk'
    assert game.input.held('jump')
    game.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_UP))
    assert game.input.held('jump')
    assert not field._jump_released
    game.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_SPACE))
    assert not game.input.held('jump')


def test_open_edges_and_bunker_door_have_distinct_presentation():
    root = config.DATA_DIR / 'levels/act_01'
    campus = Room.load_from_file(root / 'ohio_campus.json')
    west, east = campus.exits
    assert west.transition == east.transition == 'walk'
    assert west.rect.left == 0 and east.rect.right == campus.width_px
    approach = Room.load_from_file(root / 'approach.json')
    unchanged = next(e for e in approach.exits if e.id == 'exit_to_bunker')
    assert unchanged.transition == 'door'
    assert approach.exit_visual_rect(unchanged) == unchanged.rect


def test_checkpoint_notice_expires_pauses_respawns_and_clears_on_room_change(game):
    field = game.current_scene
    field.load_room('act_01/ohio_campus.json', 'campus_entry')
    game.input.begin_frame(); game.update(1 / 60)
    assert field.player.active_checkpoint_id == 'campus_start'
    assert field.prompt_text == 'CHECKPOINT'
    initial = field._checkpoint_notice_remaining
    for _ in range(30):
        field.enemy_manager.clear()  # Isolate the notice timer from combat damage.
        game.input.begin_frame(); game.update(1 / 60)
    remaining = field._checkpoint_notice_remaining
    assert 0 < remaining < initial
    game.open_pause()
    field.update(1.0)  # Direct scene update also respects an active pause.
    assert field._checkpoint_notice_remaining == remaining
    game.pause.close()
    for _ in range(160):
        field.enemy_manager.clear()
        game.input.begin_frame(); game.update(1 / 60)
    assert field._checkpoint_notice_remaining == 0
    assert field.prompt_text != 'CHECKPOINT'
    assert field.player.active_checkpoint_id == 'campus_start'
    field.player.take_damage(10000, ignore_invulnerable=True)
    game.input.begin_frame(); game.update(1 / 60)
    assert field.player.respawn_count > 0
    assert field.player.active_checkpoint_id == 'campus_start'
    assert field._checkpoint_notice_remaining == pytest.approx(2.5)
    field.load_room('act_01/salvage_yard.json', 'yard_entrance')
    assert field._checkpoint_notice_remaining == 0
    assert field.prompt_text == ''


def test_enemy_hit_does_not_claim_voltage_and_real_hazard_does(game):
    field = game.current_scene
    field.load_room('act_01/ohio_campus.json', 'campus_entry')
    place(field, 320)
    field.player.invulnerable_timer = 1.0
    game.input.begin_frame(); game.update(1 / 60)
    assert field.prompt_text == 'HIT'
    place(field, 640)
    game.input.begin_frame(); game.update(1 / 60)
    assert field.prompt_text == 'HIGH VOLTAGE'


def test_top_threat_label_preserves_real_enemy_telegraph_lock(game, monkeypatch):
    from video_game.engine.enemies import CoreReconDrone
    field = game.current_scene
    field.load_room('act_01/ohio_campus.json', 'campus_entry')
    place(field, 320)
    enemy = CoreReconDrone('lock_fixture', x=440, y=116, patrol_left=432, patrol_right=448)
    enemy.telegraph_locked = True
    field.enemy_manager.enemies = [enemy]
    seen = {}
    monkeypatch.setattr(game, 'render_global_hud', lambda _crt, **kwargs: seen.update(kwargs))
    field.render(game.crt)
    assert seen['threat_level'] == 'LOCKED'
