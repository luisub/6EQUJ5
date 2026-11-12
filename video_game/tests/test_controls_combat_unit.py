"""PURPOSE: Test control-profile migration, aim mapping and interrupt-safe fire.
CALLED BY: pytest.
HOW TO MODIFY: Use actual events, temporary saves and preserve Classic compatibility.
"""
import json
import pygame
import pytest

from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import Settings, SettingsStore
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.ui.viewport import window_to_logical


@pytest.fixture
def game(tmp_path):
    pygame.init()
    pygame.display.set_mode((960, 540))
    machine = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(tmp_path / 'save'),
                               settings_store=SettingsStore(tmp_path / 'save'))
    try:
        assert machine.start_new_game()[0]
        machine.change_state(config.STATE_FIELD_OPS, room='act_01/approach.json', spawn='approach_checkpoint')
        scene = machine.current_scene
        scene.enemy_manager.clear()
        scene.player.x, scene.player.y = 400, 208
        for _ in range(30):
            machine.input.begin_frame()
            machine.update(1 / 60)
        yield machine
    finally:
        machine.close()
        pygame.quit()


def test_legacy_profiles_migrate_without_rewrite_and_fresh_is_assisted(tmp_path):
    store = SettingsStore(tmp_path)
    assert store.load().combat_mode == 'assisted'
    for schema, scale, expected_scale in [(1, 3, 2), (2, 1, 1)]:
        old = {'schema_version':schema, 'volume':42, 'crt_effects':False, 'scale':scale}
        store.path.write_text(json.dumps(old))
        before = store.path.read_bytes()
        assert store.load() == Settings(volume=42, crt_effects=False, scale=expected_scale, combat_mode='classic')
        assert not store.warning and store.path.read_bytes() == before
    for mode in ('classic', 'assisted'):
        value = Settings(volume=21, crt_effects=False, scale=1, combat_mode=mode)
        store.save(value)
        assert json.loads(store.path.read_text())['schema_version'] == 3
        assert store.load() == value
    bad = {'schema_version':3, 'volume':42, 'crt_effects':False, 'scale':1, 'combat_mode':'unknown'}
    store.path.write_text(json.dumps(bad))
    assert store.load() == Settings(volume=42, crt_effects=False, scale=1, combat_mode='assisted')
    assert store.warning


def test_clipped_window_mapping_matches_presented_canvas():
    pygame.init()
    pygame.display.set_mode((960, 540))
    try:
        crt = CRTRenderer(scale=2)
        assert window_to_logical((480,270),crt) == (120,67.5)
        assert window_to_logical((960,270),crt) is None
    finally:
        pygame.quit()


def test_assisted_primary_is_only_flash_and_all_rays_are_narrow(game):
    scene = game.current_scene
    scene.camera.x, scene.camera.y = 160, 18
    game.input.begin_frame()
    target = (690,250)
    game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,pos=target,button=1))
    game.update(1/60)
    projectiles = scene.projectile_manager.projectiles
    assert len(projectiles) == 3 and [p.is_primary_discharge for p in projectiles] == [True,False,False]
    assert len(scene.effects.flashes) == 1
    assert scene._firing_light_projectile_ids == {p.id for p in projectiles}
    assert scene.effects.flashes[0]['aim_vector'] == (projectiles[0].dir_x,projectiles[0].dir_y)


def test_fresh_charge_and_same_batch_handoff_require_neutral(game):
    scene = game.current_scene
    # Same event batch: keyboard charge starts, then a mapped controller takes over.
    controller = 31
    game.input._controller_state[controller] = {'buttons':set(), 'axes':{}}
    game.input.begin_frame()
    game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_j))
    game.handle_event(pygame.event.Event(pygame.CONTROLLERAXISMOTION,instance_id=controller,
                                         axis=pygame.CONTROLLER_AXIS_RIGHTX,value=32767))
    game.update(1/60)
    assert not scene.projectile_manager.projectiles and not scene.player.weapon.is_charging
    game.input.begin_frame()
    game.handle_event(pygame.event.Event(pygame.KEYUP,key=pygame.K_j))
    game.update(1/60)
    game.input.begin_frame()
    game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_j))
    game.update(1/60)
    assert len(scene.projectile_manager.projectiles) == 3
    assert scene.player.weapon.is_charging


def test_fresh_charge_works_on_first_frame_after_scene_entry(game):
    game.change_state(config.STATE_BUNKER_HUB)
    game.change_state(config.STATE_FIELD_OPS, room='act_01/approach.json', spawn='approach_checkpoint')
    scene = game.current_scene
    scene.enemy_manager.clear()
    game.input.begin_frame()
    game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_j))
    game.update(1/60)
    assert scene.player.weapon.is_charging
    assert len(scene.projectile_manager.projectiles) == 3


def test_unlocked_coilgun_charge_cancelled_on_focus_loss(game):
    scene = game.current_scene
    coil = scene.player.arsenal.weapons['fibonacci_coilgun']
    coil.is_unlocked = True  # Isolated unlock precondition; cycling and input are real.
    game.input.begin_frame()
    game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_q))
    game.update(1/60)
    game.handle_event(pygame.event.Event(pygame.KEYUP,key=pygame.K_q))
    assert scene.player.weapon is coil
    game.input.begin_frame()
    game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_j))
    for _ in range(50):
        game.update(1/60)
        game.input.begin_frame()
    assert coil.charge_timer > 0 and coil.is_charging
    game.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
    assert game.pause.active and coil.charge_timer == 0 and not coil.is_charging
    game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE))
    game.input.begin_frame()
    game.handle_event(pygame.event.Event(pygame.KEYUP,key=pygame.K_j))
    game.update(1/60)
    assert not scene.projectile_manager.projectiles
    game.input.begin_frame()
    game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_j))
    game.update(1/60)
    game.input.begin_frame()
    game.handle_event(pygame.event.Event(pygame.KEYUP,key=pygame.K_j))
    game.update(1/60)
    assert len(scene.projectile_manager.projectiles) == 1
    assert scene.projectile_manager.projectiles[0].weapon_type == 'fibonacci_coilgun'
