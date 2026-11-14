"""PURPOSE: Verify registered, bounded presentation without changing combat.
CALLED BY: pytest.
HOW TO MODIFY: Cover normal input, rendering, fallback and projectile invariants.
"""

from . import REPO_ROOT
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path

import pygame
import pytest

from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.effects import EffectManager, load_maser_presentation
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.weapons import ProjectileManager
from video_game.tools.build_maser_discharge import build_discharge

SOURCE = (REPO_ROOT / 'src/art/source/effects'
          / 'maser_discharge_v02/export/maser_discharge_v02_64x32.png')


@pytest.fixture
def presentation(tmp_path):
    root = tmp_path / 'assets'
    root.mkdir()
    pygame.init()
    pygame.display.set_mode((960, 540))
    build_discharge(assets_dir=root, archive_dir=tmp_path/'archive', source=SOURCE, promote=True)
    yield load_maser_presentation(root)
    pygame.quit()


def test_actor_alpha_cache_rotation_and_pause(presentation):
    class Camera:
        viewport_w, viewport_h = 480, 270
        def world_to_screen(self, x, y):
            return round(x), round(y)
    camera = Camera()
    effects = EffectManager()
    effects.add_muzzle_flash(100, 100, maser_presentation=True)
    flash = effects.flashes[0]
    sprite = pygame.Surface((48, 64), pygame.SRCALPHA)
    pygame.draw.rect(sprite, (30, 40, 50, 180), (4, 4, 35, 48))
    lit = presentation.light_actor(sprite, (180, 175), camera, [flash])
    assert pygame.image.tobytes(lit, 'RGBA')[3::4] == pygame.image.tobytes(sprite, 'RGBA')[3::4]
    assert pygame.image.tobytes(lit, 'RGB') != pygame.image.tobytes(sprite, 'RGB')
    crt = CRTRenderer(scale=1)
    for vector in ((1, 0), (-1, 0), (0, -1), (0, 1), (.7, -.7)):
        flash['aim_vector'] = vector
        presentation.render_bursts(crt, camera, [flash])
    assert len(presentation.bursts) == 5
    assert presentation.bursts[(False, 0, 8)][1] == (12, 16)
    assert presentation.bursts[(False, 180, 8)][1] == (51, 15)
    before = deepcopy(flash)
    effects.update(.1, is_paused=True)
    assert flash == before
    effects.update(.1)
    assert not effects.flashes


def test_enhanced_trail_preserves_projectile_data_and_other_weapons(presentation):
    class Camera:
        def world_to_screen(self, x, y):
            return round(x), round(y)
    camera = Camera()
    manager = ProjectileManager()
    manager.spawn(80, 40, 1, 0, 180, 7, weapon_type='starter_maser')
    manager.spawn(80, 80, 1, 0, 180, 9, weapon_type='scattergun')
    before = [asdict(p) for p in manager.projectiles]
    old = pygame.Surface((150, 100))
    new = old.copy()
    manager.render(old, camera)
    manager.render(new, camera, enhanced_maser=True)
    assert [asdict(p) for p in manager.projectiles] == before
    assert pygame.image.tobytes(old.subsurface((0, 70, 150, 20)), 'RGB') == pygame.image.tobytes(new.subsurface((0, 70, 150, 20)), 'RGB')
    assert pygame.image.tobytes(old, 'RGB') != pygame.image.tobytes(new, 'RGB')


@pytest.mark.parametrize('state,room,spawn', [
    (config.STATE_FIELD_OPS, 'act_01/ohio_campus.json', 'campus_west'),
    (config.STATE_BOSS_BOUNTY, None, None),
])
def test_scene_real_fire_uses_primary_origin(presentation, tmp_path, state, room, spawn):
    machine = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(tmp_path/'save'),
                               settings_store=SettingsStore(tmp_path/'save'))
    try:
        assert machine.start_new_game()[0]
        if room:
            machine.change_state(state, room=room, spawn=spawn)
        else:
            machine.change_state(state)
        scene = machine.current_scene
        scene.maser_presentation = presentation
        scene.energy_filament = None  # Explicitly exercise the retained v2 fallback.
        # The boss requires the actual reveal to finish before it accepts fire.
        for _ in range(112 if state == config.STATE_BOSS_BOUNTY else 20):
            machine.input.begin_frame()
            machine.update(1/60)
        if state == config.STATE_BOSS_BOUNTY:
            assert scene.encounter_intro_remaining == 0
        manager = scene.projectile_manager if room else scene.proj_mgr
        records = []
        original = manager.spawn
        def record(*args, **kwargs):
            result = original(*args, **kwargs)
            records.append((result.x, result.y, result.dir_x, result.dir_y, result.is_primary_discharge))
            return result
        manager.spawn = record
        machine.input.begin_frame()
        machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_j))
        machine.update(1/60)
        machine.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_j))
        primary = next(item for item in records if item[4])
        flash = scene.effects.flashes[-1]
        assert (flash['x'], flash['y'], *flash['aim_vector']) == primary[:4]
        assert flash['maser_presentation'] and flash['life'] == pytest.approx(.08 - 1/60)
        machine.render()
    finally:
        machine.close()


def test_charged_release_pause_and_reset_on_actual_field(presentation, tmp_path, monkeypatch):
    machine = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(tmp_path/'save'),
                               settings_store=SettingsStore(tmp_path/'save'))
    try:
        assert machine.change_settings(combat_mode='classic')
        assert machine.start_new_game()[0]
        machine.change_state(config.STATE_FIELD_OPS, room='act_01/approach.json', spawn='approach_checkpoint')
        scene = machine.current_scene
        scene.maser_presentation = presentation
        scene.enemy_manager.clear()
        machine.input.begin_frame()
        machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_j))
        machine.update(1/60)
        for _ in range(48):
            machine.input.begin_frame()
            machine.update(1/60)
        machine.input.begin_frame()
        machine.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_j))
        machine.update(1/60)
        flash = scene.effects.flashes[-1]
        assert flash['is_charged'] and flash['maser_presentation']
        assert flash['aim_vector'] == (scene.projectile_manager.projectiles[-1].dir_x,
                                        scene.projectile_manager.projectiles[-1].dir_y)
        # Scene music preloads on its worker; this assertion concerns warmed rendering.
        music_worker = machine.audio._load_thread
        if music_worker is not None:
            music_worker.join(3)
            assert not music_worker.is_alive(), 'music preload did not finish'
        with monkeypatch.context() as patch:
            patch.setattr(Path, 'read_bytes', lambda *_: pytest.fail('per-frame asset read'))
            patch.setattr(Path, 'read_text', lambda *_args, **_kwargs: pytest.fail('per-frame manifest read'))
            patch.setattr(pygame.image, 'load', lambda *_args, **_kwargs: pytest.fail('per-frame decode'))
            machine.render()
        before = deepcopy(flash)
        scene.effects.update(.5, is_paused=True)
        assert flash == before
        scene.reset_to_spawn('approach_checkpoint')
        assert not presentation.active_flashes(scene.effects.flashes)
    finally:
        machine.close()


def test_suppression_preserves_other_weapon_flash(presentation):
    class Camera:
        viewport_w, viewport_h = 480, 270
        def world_to_screen(self, x, y):
            return round(x), round(y)
    effects = EffectManager()
    effects.add_muzzle_flash(70, 70, maser_presentation=True)
    effects.add_muzzle_flash(130, 70)
    baseline = pygame.Surface((200, 140))
    suppressed = baseline.copy()
    effects.render(baseline, Camera())
    effects.render(suppressed, Camera(), suppress_maser=True)
    assert baseline.get_at((70, 70)) != suppressed.get_at((70, 70))
    assert baseline.get_at((130, 70)) == suppressed.get_at((130, 70))
    assert suppressed.get_at((130, 70)) != pygame.Color('black')


def test_approach_retains_bounce_without_old_shot_drawing(presentation, tmp_path, monkeypatch):
    machine = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(tmp_path/'save'),
                               settings_store=SettingsStore(tmp_path/'save'))
    try:
        assert machine.start_new_game()[0]
        machine.change_state(config.STATE_FIELD_OPS, room='act_01/approach.json', spawn='approach_checkpoint')
        scene = machine.current_scene
        assert scene.firing_lighting is not None
        scene.maser_presentation = presentation
        scene.energy_filament = None  # Explicitly exercise the retained v2 fallback.
        scene.enemy_manager.clear()
        seen = []
        bounce = scene.firing_lighting.render_world_bounce
        def record_bounce(*args):
            seen.append(True)
            return bounce(*args)
        monkeypatch.setattr(scene.firing_lighting, 'render_world_bounce', record_bounce)
        monkeypatch.setattr(scene.firing_lighting, 'render_bursts', lambda *_: pytest.fail('old burst doubled'))
        monkeypatch.setattr(scene.firing_lighting, 'light_actor', lambda *_: pytest.fail('old actor light doubled'))
        machine.input.begin_frame()
        machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_j))
        machine.update(1/60)
        machine.render()
        assert seen
    finally:
        machine.close()
