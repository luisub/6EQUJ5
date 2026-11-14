"""Crossing, mirrored combat anchors and distance-driven native insect motion."""
import json

import pygame
import pytest

from video_game.engine import config
from video_game.engine.alien_journey import journey_data
from video_game.engine.bosses.base import STATE_RECOVERY as BOSS_RECOVERY, STATE_TRANSITION
from video_game.engine.bosses.campaign_bosses import (
    AlienGuardian, Amalgam, CorePrime, EarthFinalAI, MandelaArchitect, PortalWarden, Synchronicity,
)
from video_game.engine.bosses.greenkeeper import Greenkeeper
from video_game.engine.campaign_scenery import load_campaign_boss
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.enemies import (
    ChrysalisSplicer, CoreEnforcer, CoreOperative, CoreReconDrone, EnemyManager,
    PhaseWatcher, PrecursorGuardian, ShieldHound, StaticHound, TemporalPhantom,
    STATE_PATROL, STATE_RECOVERY,
)
from video_game.engine.planet_encounters import PlanetThreat, world_config
from video_game.engine.player import Player
from video_game.engine.world import Camera
from .test_combat import create_test_room

ENEMIES = (CoreReconDrone, CoreEnforcer, CoreOperative, StaticHound, ShieldHound,
           PhaseWatcher, ChrysalisSplicer, PrecursorGuardian, TemporalPhantom)
BOSSES = (Synchronicity, Amalgam, MandelaArchitect, CorePrime, PortalWarden, EarthFinalAI)


@pytest.fixture(autouse=True)
def display(monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER', 'dummy')
    monkeypatch.setenv('SDL_AUDIODRIVER', 'dummy')
    pygame.init(); pygame.display.set_mode((960, 540))
    yield
    pygame.quit()


def room():
    return create_test_room([[0]*40 for _ in range(15)] + [[1]*40])


@pytest.mark.parametrize('factory', BOSSES + tuple(range(11)))
def test_every_campaign_boss_turns_across_and_above_player(factory):
    boss = AlienGuardian(journey_data()['worlds'][factory]) if isinstance(factory, int) else factory()
    boss.phase_state = STATE_TRANSITION
    boss.transition_timer = 10
    boss.art_surface = load_campaign_boss(config.ASSETS_DIR, boss.target_id)
    assert boss.art_surface is not None
    for x, side in ((100, 'left'), (600, 'right'), (boss.rect.centerx, 'right'), (100, 'left')):
        boss.update(.01, (x, 50))
        assert boss.facing == side
        surface = pygame.Surface((640, 270), pygame.SRCALPHA)
        boss.render(surface, Camera(640, 270))
    assert pygame.image.tobytes(boss._art_variants[1], 'RGBA') == pygame.image.tobytes(
        pygame.transform.flip(boss.art_surface, True, False), 'RGBA')
    boss.phase_state = BOSS_RECOVERY
    boss.cooldown = 10
    boss.update(.01, (100, 50)); left = boss.weak_point_rect.copy()
    boss.update(.01, (600, 50)); right = boss.weak_point_rect.copy()
    assert right.centerx - boss.rect.centerx == boss.rect.centerx - left.centerx
    assert right.centery == left.centery
    result = boss.take_damage(5, hit_id='mirrored_core', hit_pos=right.center)
    assert result.damage_dealt == 10
    boss.reset_to_pristine()
    assert boss.facing == 'left'


def test_greenkeeper_turns_body_muzzle_core_and_warned_charge():
    boss = Greenkeeper()
    boss.attack_cycle_timer = 10
    boss.update(.01, (100, 50))
    left, muzzle = boss.weak_point_rect.copy(), boss.mortar_muzzle
    boss.update(.01, (600, 50))
    assert boss.facing == 'right'
    assert boss.weak_point_rect.left == 2 * boss.rect.centerx - left.right
    assert boss.mortar_muzzle[0] == 2 * boss.rect.centerx - muzzle[0]
    assert pygame.image.tobytes(boss.heavy_right['idle'], 'RGBA') == pygame.image.tobytes(
        pygame.transform.flip(boss.heavy_sprites['idle'], True, False), 'RGBA')
    boss.current_phase = 2; boss.volley_count = 1
    boss._schedule_next_attack((600, 208))
    assert boss.telegraphs[0].target_rect.left == boss.rect.right
    # Crossing after a warning does not redirect its committed charge.
    boss.face_target((100, 50))
    boss._execute_telegraphed_attack()
    assert boss.charge_vx > 0 and boss.facing == 'right'
    x = boss.x; boss.update(.1, (100, 50))
    assert boss.x > x and boss.facing == 'right'
    boss.reset_to_pristine(); assert boss.facing == 'left'


@pytest.mark.parametrize('cls', ENEMIES)
def test_every_earth_enemy_turns_in_recovery_and_has_native_motion(cls):
    manager = EnemyManager(); enemy = cls('turn', 220, 208)
    manager.add_enemy(enemy)
    enemy.state, enemy.state_timer = STATE_RECOVERY, 5
    player = Player(100, 100)
    for x, side in ((100, 'left'), (350, 'right'), (100, 'left')):
        player.x = x; player.rect.x = x
        manager.update(.01, player, room())
        assert enemy.facing == side
    prefix = manager._get_enemy_prefix(enemy)
    frames = [manager.native_sprites[f'{prefix}_patrol_{i}'][1] for i in range(1, 5)]
    assert len({pygame.image.tobytes(f, 'RGBA') for f in frames}) == 4
    assert all(f.get_size() == (enemy.cfg.width*2, enemy.cfg.height*2) for f in frames)
    assert all(f.get_bounding_rect().height > 8 for f in frames)
    manager.reset_all(); assert enemy.facing == 'left' and enemy.travel_distance == 0


@pytest.mark.parametrize('world', journey_data()['worlds'], ids=lambda w:w['id'])
def test_each_planet_threat_turns_when_player_crosses(world):
    enemy = PlanetThreat('turn', 220, 208, world_config(world['id']), custom_body=True)
    enemy.state, enemy.state_timer = STATE_RECOVERY, 5
    manager = EnemyManager(); manager.add_enemy(enemy)
    player = Player(350, 100)
    manager.update(.01, player, room()); assert enemy.facing == 'right'
    player.x = 100; player.rect.x = 100
    manager.update(.01, player, room()); assert enemy.facing == 'left'


def test_ground_gait_follows_distance_and_stops_when_blocked_or_paused():
    manager = EnemyManager(); enemy = CoreEnforcer('walk', 200, 208, patrol_left=150, patrol_right=250)
    manager.add_enemy(enemy)
    player = Player(20, 208); player.in_cover = True; player.cover_type = 'background'
    enemy.cooldown_timer = 100
    crt = CRTRenderer(scale=1); camera = Camera()
    frames = set()
    for _ in range(70):
        manager.update(1/60, player, room())
        crt.clear(); manager.render(crt.canvas, camera, crt=crt)
        image = crt.finalize_frame().subsurface((int(enemy.x)*2, int(enemy.y)*2, enemy.cfg.width*2, enemy.cfg.height*2))
        frames.add(pygame.image.tobytes(image, 'RGBA'))
    assert len(frames) >= 4 and enemy.travel_distance > 12
    prior = enemy.travel_distance
    manager.update(1, player, room(), is_paused=True)
    assert enemy.travel_distance == prior
    enemy.state, enemy.state_timer = STATE_RECOVERY, 1
    manager.update(.01, player, room())
    assert enemy.travel_distance == prior and enemy.last_travel == 0


def test_corrupt_native_frame_is_rejected(tmp_path, monkeypatch):
    import video_game.engine.enemies as module
    directory = tmp_path/'core_operative'; directory.mkdir()
    manifest = json.loads((config.ASSETS_DIR/'sprites/enemies/manifest.json').read_text())
    (tmp_path/'manifest.json').write_text(json.dumps(manifest))
    image = pygame.Surface((40,64), pygame.SRCALPHA); image.fill('red')
    pygame.image.save(image,directory/'patrol_1.png')
    monkeypatch.setattr(module,'ENEMY_SPRITES_DIR',tmp_path)
    manager = EnemyManager()
    assert 'core_operative_patrol_1' not in manager.sprite_cache
