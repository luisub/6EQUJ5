"""
PURPOSE: Focused contracts for the opt-in starter-maser combat profile.
CALLED BY: pytest.
HOW TO MODIFY: Update combat assist cone, target acquisition, or starter maser behavior.
"""

import math
from types import SimpleNamespace

import pygame
import pytest

from video_game.engine.weapons import (
    AnalogScattergun, CombatTarget, FibonacciCoilgun, ProjectileManager, StarterMaser,
    get_muzzle_world_pos,
)
from video_game.engine.world import COLLISION_EMPTY, COLLISION_SOLID, Room


def _room(wall_column=None):
    grid = [[COLLISION_EMPTY] * 30 for _ in range(12)]
    if wall_column is not None:
        for row in grid:
            row[wall_column] = COLLISION_SOLID
    return Room({
        "schema_version": 1, "room_id": "combat_assist_test", "act_id": "test",
        "title": "Test", "grid_width": 30, "grid_height": 12,
        "width_tiles": 30, "height_tiles": 12, "tile_size": 16,
        "collision_layers": grid, "background_layers": [], "spawns": {},
        "exits": [], "checkpoints": [], "objects": [],
    })


def _player():
    return SimpleNamespace(x=0.0, y=32.0, width=16, facing="right",
                           is_grounded=True, is_crouching=False,
                           can_fire=lambda room: True)


def _input(**kwargs):
    return SimpleNamespace(**kwargs)


def test_classic_auto_repeats_without_changing_keyboard_charge():
    room, player, manager, weapon = _room(), _player(), ProjectileManager(), StarterMaser()
    first = weapon.update(0.01, _input(auto_fire_held=True), player, room, manager)
    assert first.damage == 25 and first.is_primary_discharge
    assert len(manager.projectiles) == 1
    assert weapon.update(0.19, _input(auto_fire_held=True), player, room, manager) is None
    assert weapon.update(0.011, _input(auto_fire_held=True), player, room, manager) is not None
    assert len(manager.projectiles) == 2

    weapon.reset()
    manager.clear()
    weapon.update(0.01, _input(fire_pressed=True, fire_held=True), player, room, manager)
    weapon.update(0.61, _input(fire_held=True, auto_fire_held=True), player, room, manager)
    assert len(manager.projectiles) == 1  # held charge has priority over auto
    charged = weapon.update(0.01, _input(fire_released=True, auto_fire_held=True), player, room, manager)
    assert charged.is_charged and charged.damage == 75 and charged.pierce_remaining == 3
    assert len(manager.projectiles) == 2


@pytest.mark.parametrize("aim", [(1.0, 0.0), (-1.0, 0.0), (3.0, -4.0)])
def test_assisted_fan_is_center_first_symmetric_normalized_and_bounded(aim):
    room, player, manager, weapon = _room(), _player(), ProjectileManager(), StarterMaser()
    weapon.set_assisted(True)
    center = weapon.update(0.01, _input(auto_fire_held=True, aim_x=aim[0], aim_y=aim[1]), player, room, manager)
    assert len(manager.projectiles) == 3 and manager.projectiles[0] is center
    assert [p.damage for p in manager.projectiles] == [50, 20, 20]
    assert [p.is_primary_discharge for p in manager.projectiles] == [True, False, False]
    assert all(p.volley_hit_target_ids is center.volley_hit_target_ids for p in manager.projectiles)
    assert all(math.hypot(p.dir_x, p.dir_y) == pytest.approx(1.0) for p in manager.projectiles)
    base = math.atan2(center.dir_y, center.dir_x)
    offsets = [math.degrees(math.atan2(math.sin(math.atan2(p.dir_y, p.dir_x) - base),
                                       math.cos(math.atan2(p.dir_y, p.dir_x) - base)))
               for p in manager.projectiles[1:]]
    assert offsets == pytest.approx([-10.0, 10.0])
    assert weapon.cooldown_timer == pytest.approx(0.16)
    assert weapon.update(0.159, _input(auto_fire_held=True), player, room, manager) is None
    assert len(manager.projectiles) == 3
    assert weapon.update(0.002, _input(auto_fire_held=True), player, room, manager) is not None
    assert len(manager.projectiles) == 6
    # A long update never spawns an unbounded catch-up burst.
    weapon.update(10.0, _input(auto_fire_held=True), player, room, manager)
    assert len(manager.projectiles) == 9


def test_one_damage_application_per_target_and_flanks_still_stop_on_target():
    room, player, manager, weapon = _room(), _player(), ProjectileManager(), StarterMaser()
    weapon.set_assisted(True)
    target = CombatTarget("near", pygame.Rect(60, 30, 30, 40), health=200, max_health=200,
                          invulnerability_duration=1.0)
    behind = CombatTarget("behind", pygame.Rect(110, 25, 30, 50), health=200, max_health=200)
    weapon.update(0.01, _input(auto_fire_held=True), player, room, manager)
    hits = manager.update(0.30, room, [target, behind])
    assert target.health == 150 and target.hit_count == 1
    assert len(hits) == 1 and hits[0].damage_dealt == 50
    assert behind.health == 200
    assert not manager.projectiles  # the two suppressed flanks are still absorbed


def test_lethal_center_still_blocks_the_rest_of_its_volley():
    room, player, manager, weapon = _room(), _player(), ProjectileManager(), StarterMaser()
    weapon.set_assisted(True)
    target = CombatTarget("near", pygame.Rect(60, 30, 30, 40), health=40, max_health=40)
    behind = CombatTarget("behind", pygame.Rect(110, 25, 30, 50), health=200, max_health=200)
    weapon.update(0.01, _input(auto_fire_held=True), player, room, manager)
    manager.update(0.30, room, [target, behind])
    assert target.is_dead and target.hit_count == 1
    assert behind.health == 200 and not manager.projectiles


def test_volley_hit_history_survives_across_updates():
    room, player, manager, weapon = _room(), _player(), ProjectileManager(), StarterMaser()
    weapon.set_assisted(True)
    target = CombatTarget("moving", pygame.Rect(60, 48, 30, 4), health=200, max_health=200)
    weapon.update(0.01, _input(auto_fire_held=True), player, room, manager)
    manager.update(0.1, room, [target])  # center hits; flanks miss the narrow target
    assert target.health == 150 and len(manager.projectiles) == 2
    target.rect = pygame.Rect(62, 20, 50, 60)  # later flank contact with same target
    assert manager.update(0.1, room, [target]) == []
    assert target.health == 150 and target.hit_count == 1 and not manager.projectiles


def test_assisted_keyboard_hold_still_releases_one_classic_charged_shot():
    room, player, manager, weapon = _room(), _player(), ProjectileManager(), StarterMaser()
    weapon.set_assisted(True)
    weapon.update(0.01, _input(fire_pressed=True, fire_held=True), player, room, manager)
    assert [p.damage for p in manager.projectiles] == [50, 20, 20]
    weapon.update(0.61, _input(fire_held=True, auto_fire_held=True), player, room, manager)
    assert len(manager.projectiles) == 3
    shot = weapon.update(0.01, _input(fire_released=True, auto_fire_held=True), player, room, manager)
    assert shot.is_charged and shot.damage == 75 and shot.pierce_remaining == 3
    assert len(manager.projectiles) == 4


def test_other_weapons_ignore_dedicated_auto_intent():
    room, player, manager = _room(), _player(), ProjectileManager()
    scatter = AnalogScattergun()
    scatter.is_unlocked = True
    assert scatter.update(0.5, _input(auto_fire_held=True), player, room, manager) is None
    assert not manager.projectiles


def test_every_fan_ray_stops_at_solid_wall():
    room, player, manager, weapon = _room(wall_column=4), _player(), ProjectileManager(), StarterMaser()
    weapon.set_assisted(True)
    target = CombatTarget("behind-wall", pygame.Rect(100, 15, 30, 70), health=100, max_health=100)
    weapon.update(0.01, _input(auto_fire_held=True), player, room, manager)
    assert manager.update(0.4, room, [target]) == []
    assert target.health == 100 and not manager.projectiles


def test_pause_cancel_profile_change_and_cover_never_release_a_charge():
    room, player, manager, weapon = _room(), _player(), ProjectileManager(), StarterMaser()
    weapon.update(0.01, _input(fire_pressed=True), player, room, manager)
    weapon.update(0.7, _input(fire_held=True), player, room, manager)
    assert weapon.is_fully_charged
    count = len(manager.projectiles)
    weapon.update(1.0, _input(auto_fire_held=True), player, room, manager, is_paused=True)
    assert len(manager.projectiles) == count and weapon.is_fully_charged
    weapon.cancel_charge()  # scene invokes on pause/focus/disconnect/handoff
    weapon.update(1.0, _input(fire_held=True), player, room, manager)
    assert not weapon.is_fully_charged
    assert weapon.update(0.01, _input(fire_released=True), player, room, manager) is None
    weapon.update(0.01, _input(fire_pressed=True), player, room, manager)
    weapon.update(0.7, _input(fire_held=True), player, room, manager)
    weapon.set_assisted(True)
    weapon.update(1.0, _input(fire_held=True), player, room, manager)
    assert not weapon.is_fully_charged
    assert weapon.update(0.01, _input(fire_released=True), player, room, manager) is None
    weapon.update(0.01, _input(fire_pressed=True), player, room, manager)
    weapon.update(0.7, _input(fire_held=True), player, room, manager)
    player.can_fire = lambda room: False
    weapon.update(0.01, _input(auto_fire_held=True), player, room, manager)
    player.can_fire = lambda room: True
    assert weapon.update(0.01, _input(fire_released=True), player, room, manager) is None
    weapon.reset()
    assert weapon.assisted and weapon.cooldown_timer == 0 and not weapon.is_charging


def test_explicit_weapon_facing_controls_muzzle_fallback():
    player = _player()
    player.weapon_facing = "left"
    player.aim_facing_active = True
    assert get_muzzle_world_pos(player)[0] == pytest.approx(player.x - 4.0)
    assert player.facing == "right"
    player.aim_facing_active = False
    assert get_muzzle_world_pos(player)[0] == pytest.approx(player.x + player.width + 4.0)


def test_coilgun_cancel_suppresses_stale_hold_and_release_but_preserves_new_charge():
    room, player, manager, weapon = _room(), _player(), ProjectileManager(), FibonacciCoilgun()
    weapon.is_unlocked = True
    weapon.update(0.01, _input(fire_pressed=True), player, room, manager)
    weapon.update(0.7, _input(fire_held=True), player, room, manager)
    assert weapon.charge_timer == pytest.approx(0.7)
    weapon.cooldown_timer = 0.1
    weapon.cancel_charge()
    assert weapon.cooldown_timer == pytest.approx(0.1)
    weapon.update(0.8, _input(fire_held=True), player, room, manager)
    assert weapon.charge_timer == 0 and not weapon.is_charging
    assert weapon.update(0.01, _input(fire_released=True), player, room, manager) is None
    assert not manager.projectiles

    weapon.update(0.01, _input(fire_pressed=True), player, room, manager)
    weapon.update(0.3, _input(fire_held=True), player, room, manager)
    shot = weapon.update(0.01, _input(fire_released=True), player, room, manager)
    assert shot.damage == 40 and shot.pierce_remaining == 1
    assert weapon.cooldown_timer == pytest.approx(0.35)
