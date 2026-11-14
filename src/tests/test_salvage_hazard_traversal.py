"""PURPOSE: Verify the narrowed salvage-yard hazard remains fair and dangerous.
CALLED BY: pytest tests/test_salvage_hazard_traversal.py.
HOW TO MODIFY: Preserve real mapper events, both directions, rates and landing checks.
"""

from video_game.engine import config
from pathlib import Path

import pygame
import pytest

from video_game.engine.input import InputManager
from video_game.engine.player import Player, PlayerInput
from video_game.engine.world import Camera, Room, preload_env_assets


LEVEL = config.DATA_DIR / 'levels/act_01/salvage_yard.json'
HAZARD_LEFT, HAZARD_RIGHT = 304, 336


def traverse(direction, fps, gap, *, from_rest=False, jump=True):
    """Walk toward the hazard and optionally hold Space at a leading-edge gap."""
    room = Room.load_from_file(LEVEL)
    trigger = HAZARD_LEFT - gap if direction == 1 else HAZARD_RIGHT + gap
    if from_rest:
        start = trigger - 16 if direction == 1 else trigger
    else:
        start = 208 if direction == 1 else 408
    player = Player(start, 208)
    player.is_grounded = True
    player.facing = 'right' if direction == 1 else 'left'
    manager = InputManager()
    manager.begin_frame()
    move_key = pygame.K_d if direction == 1 else pygame.K_a
    manager.handle_event(pygame.event.Event(pygame.KEYDOWN, key=move_key))
    launched = None
    airborne = False
    for frame in range(fps * 2):
        if frame:
            manager.begin_frame()
        leading = player.x + player.width if direction == 1 else player.x
        if jump and launched is None and ((leading >= trigger) if direction == 1 else (leading <= trigger)):
            manager.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
            launched = leading
        player.update(1 / fps, PlayerInput.from_input_manager(manager), room)
        airborne |= not player.is_grounded
        if player.health < 100:
            return {'safe': False, 'launched': launched, 'health': player.health, 'player': player}
        past = player.x >= HAZARD_RIGHT + 4 if direction == 1 else player.x + player.width <= HAZARD_LEFT - 4
        if airborne and player.is_grounded and past:
            return {'safe': True, 'launched': launched, 'health': player.health, 'player': player}
    return {'safe': False, 'launched': launched, 'health': player.health, 'player': player}


@pytest.mark.parametrize('direction', [1, -1])
@pytest.mark.parametrize('fps', [60, 120])
@pytest.mark.parametrize('gap', range(12, 45, 4))
def test_walking_jump_clears_and_lands(direction, fps, gap):
    result = traverse(direction, fps, gap)
    assert result['safe'] and result['health'] == 100
    assert result['launched'] is not None and not result['player'].is_dashing


@pytest.mark.parametrize('direction', [1, -1])
@pytest.mark.parametrize('fps', [60, 120])
@pytest.mark.parametrize('gap', range(4, 33, 4))
def test_from_rest_jump_clears_and_lands(direction, fps, gap):
    result = traverse(direction, fps, gap, from_rest=True)
    assert result['safe'] and result['health'] == 100
    assert result['launched'] is not None and not result['player'].is_dashing


@pytest.mark.parametrize('direction', [1, -1])
@pytest.mark.parametrize('fps', [60, 120])
def test_walking_without_jump_and_jumping_too_late_still_hurt(direction, fps):
    no_jump = traverse(direction, fps, 0, jump=False)
    too_late = traverse(direction, fps, 4)
    assert no_jump['health'] < 100 and no_jump['launched'] is None
    assert too_late['health'] < 100 and too_late['launched'] is not None


def test_visible_tiles_match_two_collision_cells():
    pygame.init()
    pygame.display.set_mode((480, 270))
    try:
        preload_env_assets()
        room = Room.load_from_file(LEVEL)
        assert [i for i in range(room.width_tiles) if room.get_tile(i, 14) == 3] == [19, 20]
        assert all(room.get_tile(i, 15) == 1 for i in range(18, 23))
        camera = Camera(480, 270)
        camera.set_world_bounds(room.width_px, room.height_px)
        tile_layer = pygame.Surface((480, 270), pygame.SRCALPHA)
        room.render_tiles(tile_layer, camera)
        for col in (18, 19, 20, 21, 22):
            alpha = pygame.mask.from_surface(tile_layer.subsurface((col * 16, 224, 16, 16)), 0).count()
            assert (alpha > 0) == (col in (19, 20))
    finally:
        pygame.quit()
