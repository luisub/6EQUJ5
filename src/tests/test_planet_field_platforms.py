"""PURPOSE: Verify the reachable one-way paths on all eleven alien fields.
CALLED BY: pytest and the planet-field accessibility verification.
HOW TO MODIFY: Keep normal jump input, unmodified physics and an open ground route.
"""
import json
from pathlib import Path

import pygame
import pytest

from video_game.engine import config
from .test_gobekli_traversal import machine, jump_to, key, step

ROOT = config.DATA_DIR / 'levels/alien_worlds'
ROOMS = tuple(f'alien_{code}' for code in ('001', '003', '005', '004', '008', '009',
                                                '006', '002', 'scan_h', '010', '007'))
BASES = (18, 58, 98, 138, 178, 218)


@pytest.mark.parametrize('world', ROOMS)
def test_six_reachable_steps_preserve_floor_and_original_platforms(world):
    data = json.loads((ROOT / f'{world}_field.json').read_text())
    assert (data['tile_size'], data['width_tiles'], data['height_tiles']) == (16, 240, 18)
    grid = data['collision_layers']
    assert all(cell == 1 for cell in grid[15])
    assert all(cell != 1 for row in grid[:15] for cell in row)
    for base in BASES:
        assert grid[13][base - 5:base - 1] == [2] * 4  # y=208
        assert grid[11][base - 2:base + 2] == [2] * 4  # y=176
        assert grid[10][base:base + 5] == [2] * 5     # original y=160


def enter_at_first_chain(machine, world, *, isolate):
    # Direct entry and starting placement are temporary geometry fixtures, not
    # campaign progression. Isolation removes encounters and hazards only for
    # examining the mapped jump arcs; normal physics and collision stay active.
    machine.change_state(config.STATE_FIELD_OPS, room=f'alien_worlds/{world}_field.json',
                         spawn='default', journey_world=world)
    scene = machine.current_scene
    if isolate:
        scene.forward_encounter = None
        scene.world_hazards = None
        scene.enemy_manager.clear()
    p = scene.player
    p.x, p.y, p.vx, p.vy = 190., 208., 0., 0.
    p.rect.topleft = (190, 208)
    for _ in range(5):
        step(machine)
    return scene


def climb(machine):
    landings = []
    for x, tops in ((235, (208,)), (275, (176, 160))):
        trace = jump_to(machine, x, tops, 9)  # physical Space held 0.15s
        landings.append(trace[-1][1])
        for _ in range(4):
            step(machine)
    if landings[-1] == 176:
        landings.append(jump_to(machine, 310, (160,), 9)[-1][1])
    assert landings[0] == 208 and landings[-1] == 160


@pytest.mark.parametrize('world', ROOMS)
def test_short_mapped_jumps_climb_each_alien_world(machine, world):
    enter_at_first_chain(machine, world, isolate=True)
    climb(machine)


def test_short_jumps_with_planet_encounter_enabled(machine):
    scene = enter_at_first_chain(machine, 'alien_001', isolate=False)
    assert scene.forward_encounter is not None
    climb(machine)
    # Let the normal director finish its warning and spawn a real enemy.
    for _ in range(90):
        step(machine)
        if scene.enemy_manager.enemies:
            break
    assert scene.enemy_manager.enemies
    assert not scene.player.is_dead
