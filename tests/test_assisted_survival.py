"""PURPOSE: Verify Assisted hostile damage and safe-hub recovery behavior.
CALLED BY: pytest tests/test_assisted_survival.py.
HOW TO MODIFY: Extend when hostile damage classification or recovery behavior changes.
"""
import json

import pygame
import pytest

from video_game.engine.abilities import AbilityManager
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.enemies import EnemyManager, ShieldHound, StaticHound, STATE_ATTACK
from video_game.engine.player import Player, PlayerConfig, PlayerInput
from video_game.engine.scenes.boss import BossScene
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.world import COLLISION_EMPTY, COLLISION_HAZARD, Room


def room(hazard=False):
    grid = [[COLLISION_EMPTY] * 30 for _ in range(12)]
    if hazard:
        grid[4][3] = COLLISION_HAZARD
    return Room({
        "schema_version": 1, "room_id": "assist_test", "act_id": "act_1",
        "title": "Assist test", "grid_width": 30, "grid_height": 12,
        "width_tiles": 30, "height_tiles": 12, "tile_size": 16,
        "collision_layers": grid,
        "background_layers": [], "spawns": {}, "exits": [], "checkpoints": [], "objects": [],
    })


def test_assisted_projectile_hit_and_classic_parity():
    for assisted, expected in [(True, 90), (False, 75)]:
        player = Player(100, 60)
        player.set_combat_assisted(assisted)
        manager = EnemyManager()
        manager.spawn_enemy_projectile(90, 70, 1, 0, 100, 25, "drone")
        manager.update(0.2, player, room())
        assert player.health == expected
        assert not manager.projectiles


@pytest.mark.parametrize("hound_type", [StaticHound, ShieldHound])
def test_assisted_hound_pounce(hound_type):
    player = Player(100, 80)
    player.set_combat_assisted(True)
    hound = hound_type("hound", 100, 80)
    hound.state = STATE_ATTACK
    hound.state_timer = hound.cfg.attack_duration
    hound.attack_hitbox_active = True
    hound.is_grounded = False
    hound.update(0.001, player, room(), EnemyManager())
    assert hound.has_damaged_player
    assert player.health == 100 - round(hound.cfg.pounce_damage * 0.4)


def test_reduction_precedes_real_shield_absorption():
    player = Player(100, 60)
    player.set_combat_assisted(True)
    player.abilities = AbilityManager()
    shield = player.abilities.abilities["shielding"]
    shield.is_active = True
    shield.remaining_shield_hp = 10
    player.take_damage(30, damage_source="hostile")
    assert shield.remaining_shield_hp == 0
    assert player.health == 98


def test_iframes_profile_toggle_and_generic_hazard():
    player = Player(100, 60)
    player.health = 10
    player.invulnerable_timer = 0.5
    player.set_combat_assisted(True)
    player.take_damage(25, damage_source="hostile")
    assert player.health == 10 and not player.is_dead
    player.take_damage(10, damage_source="hostile", ignore_invulnerable=True)
    assert player.health == 6
    player.set_combat_assisted(False)
    player.take_damage(6, damage_source="hostile")
    assert player.is_dead  # Classic retains its existing lethal-hit iframe rule.

    player = Player(100, 60)
    player.set_combat_assisted(True)
    player.take_damage(player.cfg.hazard_damage)
    assert player.health == 75


@pytest.mark.parametrize("assisted", [True, False])
def test_actual_hazard_damage_is_unchanged(assisted):
    player = Player(48, 32)
    player.update(1 / 60, PlayerInput(combat_assisted=assisted), room(hazard=True))
    assert player.health == 75


def test_assisted_safe_hub_recovery_is_explicit_and_alive_only():
    player = Player(100, 60)
    player.health = 40
    assert player.recover_health_at_safe_hub() == 0
    assert player.health == 40
    player.set_combat_assisted(True)
    assert player.health == 40
    assert player.recover_health_at_safe_hub() == 60
    assert player.health == player.cfg.max_health
    player.health, player.is_dead = 0, True
    assert player.recover_health_at_safe_hub() == 0
    assert player.health == 0 and player.is_dead


def test_profile_is_updated_before_fixed_physics(monkeypatch):
    player = Player(100, 60)
    seen = []
    monkeypatch.setattr(player, "fixed_update", lambda dt, p_input, current_room: seen.append(player.combat_assisted))
    player.update(player.cfg.fixed_dt, PlayerInput(combat_assisted=True), room())
    player.update(player.cfg.fixed_dt, PlayerInput(combat_assisted=False), room())
    assert seen == [True, False]


@pytest.mark.parametrize("value", [None, "invalid", -0.1, 0, 1.2, float("nan")])
def test_invalid_assisted_multiplier_uses_default(tmp_path, value):
    path = tmp_path / "balance.json"
    path.write_text(json.dumps({"combat": {"assisted_hostile_damage_multiplier": value}}))
    assert PlayerConfig.load_from_file(path).assisted_hostile_damage_multiplier == 0.4


def test_boss_scene_applies_assisted_damage(monkeypatch):
    pygame.init()
    pygame.display.set_mode((1, 1))
    machine = GameStateMachine(CRTRenderer(), development=True)
    scene = BossScene(machine)
    scene.on_enter()
    scene.update(1.6)  # Arrival reveal is safe before combat begins.
    original_prepare = machine.prepare_player_input
    def assisted_input(p_input):
        p_input = original_prepare(p_input)
        p_input.combat_assisted = True
        return p_input
    monkeypatch.setattr(machine, "prepare_player_input", assisted_input)
    monkeypatch.setattr(scene.boss, "check_attack_collisions", lambda rect: 25)
    scene.update(1 / 60)
    assert scene.player.health == 90
