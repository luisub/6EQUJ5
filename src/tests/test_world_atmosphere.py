"""Environmental motion stays restrained, deterministic and paused with play."""
import random
from types import SimpleNamespace

import pygame
import pytest

from video_game.engine.alien_journey import journey_data
from video_game.engine.combat_feedback import SceneAtmosphere


def frame(effect, camera_x=0):
    canvas = pygame.Surface((480, 270))
    effect.render(SimpleNamespace(canvas=canvas), SimpleNamespace(x=camera_x))
    return canvas


def pixels(effect, camera_x=0):
    return pygame.image.tobytes(frame(effect, camera_x), 'RGB')


@pytest.mark.parametrize('world', journey_data()['worlds'], ids=lambda world: world['id'])
def test_world_motion_is_visible_but_keeps_hud_and_combat_clear(world):
    effect = SceneAtmosphere(world['id'] + '_field')
    initial = pixels(effect)
    for _ in range(60):
        effect.update(1 / 60)
    moved = frame(effect)
    assert pygame.image.tobytes(moved, 'RGB') != initial
    # Environmental marks must never compete with bright combat/UI signals.
    values = pygame.surfarray.array3d(moved)
    assert 0 < (values.max(axis=2) > 0).sum() < 100
    assert values.max() < 130
    assert not values[:, :68].any()
    assert not values[:, 230:].any()
    assert len(effect.motes) == 16


@pytest.mark.parametrize('world', journey_data()['worlds'], ids=lambda world: world['id'])
def test_field_and_guardian_share_weather_without_random_gameplay_side_effects(world):
    before = random.getstate()
    field = SceneAtmosphere(world['id'] + '_field')
    arena = SceneAtmosphere(world['id'] + '_arena')
    for _ in range(30):
        field.update(1 / 60)
        arena.update(1 / 60)
    assert pixels(field) == pixels(arena)
    assert pixels(field, camera_x=120) != pixels(field)
    assert random.getstate() == before


@pytest.mark.parametrize('room', ['act_01_approach', 'alien_006_field', 'alien_scan_h_arena'])
def test_pause_and_invalid_delta_preserve_weather_frame(room):
    effect = SceneAtmosphere(room)
    effect.update(.1)
    before = pixels(effect)
    effect.update(10, paused=True)
    for dt in (0, -1, float('inf'), float('-inf'), float('nan'), None):
        effect.update(dt)
    assert pixels(effect) == before
    effect.update(1e30)
    assert effect.elapsed == pytest.approx(.2)
    assert pixels(effect) != before
