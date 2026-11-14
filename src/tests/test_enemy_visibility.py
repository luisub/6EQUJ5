"""PURPOSE: Verify bounded Assisted-only enemy visibility cues.
CALLED BY: pytest tests/test_enemy_visibility.py.
HOW TO MODIFY: Preserve default pixels, caller coverage and cache lifecycle checks.
"""
import json
import pygame
import pytest

from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.enemies import (CoreEnforcer, CoreReconDrone, EnemyManager,
                                        PhaseWatcher, StaticHound, ShieldHound)
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.world import Camera


@pytest.fixture
def display(monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER', 'dummy')
    monkeypatch.setenv('SDL_AUDIODRIVER', 'dummy')
    pygame.init()
    pygame.display.set_mode((960, 540))
    yield
    pygame.quit()


def sprite(color=(50, 45, 35, 255)):
    surface = pygame.Surface((12, 10), pygame.SRCALPHA)
    pygame.draw.rect(surface, color, (2, 1, 4, 7))
    pygame.draw.rect(surface, color, (6, 5, 4, 3))
    return surface


def pixels(manager, *, highlight=False):
    surface = pygame.Surface((120, 80), pygame.SRCALPHA)
    surface.fill((20, 25, 30, 255))
    manager.render(surface, Camera(120, 80), highlight_hostiles=highlight)
    return pygame.image.tobytes(surface, 'RGBA')


def test_opt_in_is_restricted_to_living_exact_act_one_classes(display):
    manager = EnemyManager()
    for cls in (CoreReconDrone, StaticHound, CoreEnforcer):
        manager.clear()
        enemy = cls('visible', 30, 30)
        manager.enemies.append(enemy)
        baseline = pixels(manager)
        assert pixels(manager, highlight=True) != baseline
        enemy.is_dead = True
        assert pixels(manager, highlight=True) == pixels(manager)
    class FutureHound(StaticHound):
        pass
    for cls in (ShieldHound, PhaseWatcher, FutureHound):
        manager.clear()
        manager.enemies.append(cls('future', 30, 30))
        assert pixels(manager, highlight=True) == pixels(manager)


def test_default_pixels_and_both_hound_facings_with_cache_invalidation(display, monkeypatch):
    manager = EnemyManager()
    manager.sprite_cache = {'static_hound_patrol_1': sprite()}
    hound = StaticHound('hound', 30, 30)
    manager.enemies.append(hound)
    camera = Camera(120, 80)
    for facing in ('left', 'right'):
        hound.facing = facing
        target = pygame.Surface((120, 80), pygame.SRCALPHA)
        manager.render(target, camera)
        default = pygame.image.tobytes(target, 'RGBA')
        assert default == pixels_transparent(manager, highlight=False)
        first = pixels(manager, highlight=True)
        rim = manager._hostile_rims[('static_hound_patrol_1', facing == 'right')][1]
        with monkeypatch.context() as patch:
            patch.setattr(pygame.mask, 'from_surface', lambda *_: pytest.fail('rebuilt mask'))
            assert pixels(manager, highlight=True) == first
            assert manager._hostile_rims[('static_hound_patrol_1', facing == 'right')][1] is rim
    old = manager._hostile_rims[('static_hound_patrol_1', True)][1]
    manager.sprite_cache['static_hound_patrol_1'] = sprite((20, 80, 50, 255))
    pixels(manager, highlight=True)
    assert manager._hostile_rims[('static_hound_patrol_1', True)][1] is not old
    assert manager._hostile_rims[('static_hound_patrol_1', True)][0] is manager.sprite_cache['static_hound_patrol_1']
    manager.clear()
    assert not manager._hostile_rims and not manager._flipped_sprites


def pixels_transparent(manager, *, highlight):
    surface = pygame.Surface((120, 80), pygame.SRCALPHA)
    manager.render(surface, Camera(120, 80), highlight_hostiles=highlight)
    return pygame.image.tobytes(surface, 'RGBA')


def test_bounded_cache_reload_and_missing_sprite(display, monkeypatch, tmp_path):
    import video_game.engine.enemies as module
    directory = tmp_path / 'static_hound'
    directory.mkdir()
    path = directory / 'patrol_1.png'
    pygame.image.save(sprite(), path)
    monkeypatch.setattr(module, 'ENEMY_SPRITES_DIR', tmp_path)
    (tmp_path / 'manifest.json').write_text(json.dumps({'schema_version': 1, 'enemies': {
        'static_hound': {'animations': {'patrol': {
            'frames': ['sprites/enemies/static_hound/patrol_1.png'] * 2,
            'frame_duration_ms': 250, 'loop': True}}}}}))
    manager = EnemyManager()
    manager.enemies.append(StaticHound('hound', 30, 30))
    before = pixels(manager, highlight=True)
    assert len(manager._hostile_rims) == 1
    pygame.image.save(sprite((150, 40, 50, 255)), path)
    manager._load_sprites()
    assert not manager._hostile_rims
    assert pixels(manager, highlight=True) != before
    # Different keys and source objects remain bounded even in unusual dynamic use.
    for i in range(80):
        image = sprite()
        manager._hostile_rim(str(i), False, image, image)
        assert len(manager._hostile_rims) <= 64
    manager.sprite_cache.clear()
    assert pixels(manager, highlight=True) != pixels(manager)  # existing rectangle plus tick


def test_assisted_field_call_pause_and_reentry(display, tmp_path, monkeypatch):
    machine = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(tmp_path),
                               settings_store=SettingsStore(tmp_path))
    try:
        assert machine.start_new_game()[0]
        machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        machine.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_RETURN))
        assert machine.current_state_name == config.STATE_FIELD_OPS
        field = machine.current_scene
        manager = field.enemy_manager
        calls = []
        render = manager.render
        def record(*args, **kwargs):
            calls.append(kwargs.get('highlight_hostiles', False))
            return render(*args, **kwargs)
        monkeypatch.setattr(manager, 'render', record)
        assert machine.change_settings(combat_mode='classic')
        machine.render()
        assert calls.pop() is False
        assert machine.change_settings(combat_mode='assisted')
        for _ in range(40):
            machine.input.begin_frame()
            machine.update(1/60)
        assert manager.enemies
        machine.render()
        assert calls.pop() is True and manager._hostile_rims
        machine.pause.open()
        machine.render()
        assert calls.pop() is True
        machine.pause.close()
        # Field reentry clears encounter and render caches without mutating sprites.
        machine.change_state(config.STATE_BUNKER_HUB)
        machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        assert machine.current_state_name == config.STATE_FIELD_OPS
        assert not manager._hostile_rims
        machine.render()
        assert calls.pop() is True
    finally:
        machine.close()
