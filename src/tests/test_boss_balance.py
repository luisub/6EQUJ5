"""Boss endurance checks using actual weapon cadence and swept projectile hits.

The firing fixture aims perfectly and ignores incoming damage; it measures the
shortest practical encounter, not a human playthrough or survival guarantee.
"""
import pygame
import pytest

from video_game.engine.alien_journey import journey_data
from video_game.engine import config
from video_game.engine.bosses.base import STATE_ATTACK, STATE_RECOVERY, STATE_TRANSITION
from video_game.engine.bosses.campaign_bosses import AlienGuardian, Amalgam, EarthFinalAI, Synchronicity
from video_game.engine.bosses.greenkeeper import Greenkeeper
from video_game.engine.player import Player, PlayerInput
from video_game.engine.temporary_weapons import TemporaryWeapon
from video_game.engine.weapons import ProjectileManager, StarterMaser, get_muzzle_world_pos
from video_game.engine.world import Camera, Room
from .test_combat import create_test_room


@pytest.fixture(autouse=True)
def display(monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER', 'dummy')
    pygame.display.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.display.quit()


def firing_trial(boss, weapon_id='assisted', max_seconds=90):
    room = create_test_room([[0] * 70 for _ in range(20)])
    player = Player(100, 208)
    player.facing = 'right'
    player.is_grounded = True
    weapon = TemporaryWeapon(weapon_id) if weapon_id in ('arc_lance', 'nova_scatter') else StarterMaser()
    if isinstance(weapon, StarterMaser):
        weapon.set_assisted(weapon_id == 'assisted')
    player.weapon = weapon
    projectiles = ProjectileManager()
    attacks = 0
    phases = set()
    dt = 1 / 120
    boss.skip_intro()
    for frame in range(round(max_seconds / dt)):
        previous = boss.phase_state
        boss.update(dt, player.rect.center)
        if boss.phase_state == STATE_ATTACK and previous != STATE_ATTACK:
            attacks += 1
        phases.add(boss.current_phase)
        muzzle = get_muzzle_world_pos(player)
        target = boss.weak_point_rect.center if boss.weak_point_exposed else boss.rect.center
        intent = PlayerInput(auto_fire_held=True, aim_x=target[0] - muzzle[0], aim_y=target[1] - muzzle[1])
        weapon.update(dt, intent, player, room, projectiles)
        projectiles.update(dt, room, targets=[boss])
        if boss.is_defeated:
            return {'seconds': round((frame + 1) * dt, 3), 'attacks': attacks,
                    'phases': sorted(phases), 'health': boss.max_health}
    pytest.fail(f'{boss.target_id} survived {max_seconds}s of {weapon_id} fire')


@pytest.mark.parametrize('index', range(11))
@pytest.mark.parametrize('weapon_id', ['assisted', 'classic', 'arc_lance', 'nova_scatter'])
def test_guardians_survive_bursts_and_use_attacks(index, weapon_id):
    boss = AlienGuardian(journey_data()['worlds'][index])
    trial = firing_trial(boss, weapon_id)
    assert 6 <= trial['seconds'] <= 40
    assert trial['attacks'] >= 2
    assert {1, 2, 3} <= set(trial['phases'])


def test_later_guardians_increase_endurance_in_journey_order():
    guardians = [AlienGuardian(world) for world in journey_data()['worlds']]
    assert all(a.max_health < b.max_health for a, b in zip(guardians, guardians[1:]))


def test_beacon_weak_point_tracks_its_chest_reactor():
    boss = AlienGuardian(journey_data()['worlds'][-1])
    boss.phase_state = STATE_RECOVERY
    boss._update_weak_point()
    assert boss.weak_point_rect.center == (boss.rect.left + 41, boss.rect.top + 54)
    assert boss.rect.contains(boss.weak_point_rect)
    assert boss.take_damage(25, hit_pos=boss.weak_point_rect.center).damage_dealt == 50


@pytest.mark.parametrize('world_id', ['alien_006', 'alien_002', 'amalgam'])
def test_teleport_body_and_destination_warning_stay_visible_at_both_camera_edges(world_id):
    if world_id == 'amalgam':
        from video_game.engine.campaign_route import route_data
        boss = Amalgam()
        arena = route_data()['acts']['act_03']['boss_room']
    else:
        world = next(w for w in journey_data()['worlds'] if w['id'] == world_id)
        boss = AlienGuardian(world)
        arena = world['arena_room']
    room = Room.load_from_file(config.DATA_DIR / 'levels' / arena)
    camera = Camera(config.INTERNAL_WIDTH, config.INTERNAL_HEIGHT)
    camera.set_world_bounds(room.width_px, room.height_px)
    for attack_index in range(3):
        boss.attack_index = attack_index
        boss.telegraphs.clear()
        boss.prepare((100, 208))
        destination_warning = boss.telegraphs[-1].target_rect.copy()
        boss.fire((100, 208))
        assert boss.rect == destination_warning
        for x in (0, room.width_px - camera.viewport_w):
            for y in (0, room.height_px - camera.viewport_h):
                viewport = pygame.Rect(x, y, camera.viewport_w, camera.viewport_h)
                assert viewport.contains(boss.rect)
                assert viewport.contains(destination_warning)
        assert not boss.rect.colliderect(pygame.Rect(100, 208, 16, 32))


def test_paired_columns_warn_both_strike_zones_before_firing():
    world = next(w for w in journey_data()['worlds'] if w['id'] == 'alien_scan_h')
    boss = AlienGuardian(world)
    for _ in range(3):
        boss.attack_index += 1
        boss.telegraphs.clear()
        boss.prepare((200, 208))
        warned = [t.target_rect.copy() for t in boss.telegraphs]
        assert len(warned) == 2
        assert all(t.duration >= 1.0 for t in boss.telegraphs)
        boss.fire((200, 208))
        assert boss.attack_rects == warned
        assert not any(r.colliderect(pygame.Rect(180, 208, 16, 32)) for r in warned)


def test_campaign_core_bonus_requires_recovery_and_correct_aim():
    boss = Synchronicity()
    assert not boss.weak_point_exposed
    assert boss.take_damage(25, hit_pos=boss.rect.center).damage_dealt == 25
    while boss.phase_state != STATE_RECOVERY:
        boss.update(1 / 120)
    assert boss.weak_point_exposed
    assert boss.take_damage(25, hit_pos=boss.rect.topleft).damage_dealt == 25
    assert boss.take_damage(25, hit_pos=boss.weak_point_rect.center).damage_dealt == 50
    boss.reset_to_pristine()
    assert boss.health == boss.max_health and not boss.weak_point_exposed


def test_exposed_core_hits_obey_wall_ordering_and_volley_deduplication():
    boss = Synchronicity()
    boss.phase_state = STATE_RECOVERY
    boss._update_weak_point()
    player = Player(100, boss.rect.centery - 16)
    weapon = StarterMaser()
    weapon.set_assisted(True)
    room = create_test_room([[0] * 50 for _ in range(20)])
    manager = ProjectileManager()
    weapon._fire_tap(manager, player, 300, boss.rect.centery, 1, 0)
    for _ in range(90):
        manager.update(1 / 120, room, targets=[boss])
    assert boss.health == boss.max_health - 100
    boss.reset_to_pristine()
    boss.phase_state = STATE_RECOVERY
    boss._update_weak_point()
    grid = [[0] * 50 for _ in range(20)]
    for row in grid:
        row[22] = 1  # A solid wall after body entry but before the exposed core.
    room = create_test_room(grid)
    manager = ProjectileManager()
    weapon._fire_tap(manager, player, 300, boss.rect.centery, 1, 0)
    for _ in range(90):
        manager.update(1 / 120, room, targets=[boss])
    assert boss.health == boss.max_health


def test_final_form_and_retry_keep_full_endurance():
    boss = EarthFinalAI()
    boss.take_damage(boss.max_health, hit_pos=boss.rect.topleft)
    assert boss.final_stage == 2 and not boss.is_defeated
    assert boss.health == boss.max_health and boss.phase_state == STATE_TRANSITION
    assert boss.take_damage(boss.max_health).damage_dealt == 0
    boss.reset_to_pristine()
    assert boss.final_stage == 1 and boss.health == boss.max_health
    assert not boss.projectiles and not boss.telegraphs and not boss.weak_point_exposed


@pytest.mark.parametrize('weapon_id', ['classic', 'assisted', 'arc_lance'])
def test_greenkeeper_is_a_full_fight_with_starting_equipment(weapon_id):
    trial = firing_trial(Greenkeeper(), weapon_id)
    assert 5 <= trial['seconds'] <= 35
    assert {1, 2, 3} <= set(trial['phases'])
