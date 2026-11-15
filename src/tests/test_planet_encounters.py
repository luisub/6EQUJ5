"""PURPOSE: Verify finite planetary threats using the existing combat pipeline.
CALLED BY: pytest.
HOW TO MODIFY: Keep mapped input, safe warnings, visit-local reset and real damage.
"""
import json
from pathlib import Path

import pygame
import pytest

from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.planet_encounters import PlanetEncounter, PlanetThreat, world_config
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.world_hazards import WorldHazards


@pytest.fixture
def game(tmp_path, monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER', 'dummy')
    monkeypatch.setenv('SDL_AUDIODRIVER', 'dummy')
    pygame.init()
    pygame.display.set_mode((960, 540))
    machine = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(tmp_path/'save'),
                               settings_store=SettingsStore(tmp_path/'settings'))
    assert machine.start_new_game()[0]
    assert machine.change_settings(combat_mode='assisted')
    machine.change_state(config.STATE_FIELD_OPS, room='alien_worlds/alien_008_field.json',
                         spawn='default', journey_world='alien_008', campaign_route=True)
    yield machine
    machine.close()
    pygame.quit()


def step(game, n=1):
    for _ in range(n):
        game.update(1/60)
        game.input.begin_frame()


def press(game, key, down=True):
    game.handle_event(pygame.event.Event(pygame.KEYDOWN if down else pygame.KEYUP, key=key))


def place_at_first_trigger(game):
    """Start near the first trigger; progression and shots use mapped controls."""
    scene = game.current_scene
    scene.player.x = 240
    scene.player.rect.x = 240
    scene.camera.snap_to(248, 224)
    return scene


def test_authored_worlds_have_distinct_ids_and_bounded_config():
    data = json.loads((config.DATA_DIR / 'planet_encounters.json').read_text())
    assert len(data['worlds']) == 7
    assert len({w['enemy_id'] for w in data['worlds'].values()}) == 7
    assert {w['style'] for w in data['worlds'].values()} == {'strafe', 'pulse', 'lunge'}
    for world_id in data['worlds']:
        spec = world_config(world_id)
        assert spec is not None and spec['encounter_count'] == 24
        assert spec['first_trigger_x'] + (spec['encounter_count'] - 1) * spec['spacing'] == 3276
        assert spec['telegraph_seconds'] >= .8 and spec['max_active'] <= 5


def test_planet_director_warns_before_safe_spawn_and_freezes_on_focus_loss(game):
    scene = place_at_first_trigger(game)
    director = scene.forward_encounter
    assert isinstance(director, PlanetEncounter)
    step(game, 1)
    assert director.warning is not None and not scene.enemy_manager.enemies
    warning_time = director.warning_time
    game.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
    assert game.pause.active
    step(game, 60)
    assert director.warning_time == warning_time and not scene.enemy_manager.enemies
    game.pause.close()
    step(game, 60)
    assert len(scene.enemy_manager.enemies) == 1
    enemy = scene.enemy_manager.enemies[0]
    assert isinstance(enemy, PlanetThreat)
    assert enemy.rect.left - scene.player.rect.right >= 120
    assert enemy.health == 130


def test_continuous_mapped_forward_input_still_produces_safe_arrival(game):
    scene = game.current_scene
    press(game, pygame.K_RIGHT)
    saw_warning = False
    for _ in range(300):
        step(game)
        saw_warning |= scene.forward_encounter.warning is not None
        if scene.enemy_manager.enemies:
            break
    press(game, pygame.K_RIGHT, False)
    assert saw_warning and scene.enemy_manager.enemies
    enemy = scene.enemy_manager.enemies[0]
    assert enemy.rect.left - scene.player.rect.right >= 120


def test_cap_and_high_water_never_spawn_more_than_authored(game):
    scene = place_at_first_trigger(game)
    director = scene.forward_encounter
    # Explicit positions exercise four distinct safe arrivals without changing
    # any save or permanent progress; enemy movement is deliberately paused.
    for position in (240, 500, 760, 1020):
        scene.player.x = position
        scene.player.rect.x = position
        for _ in range(65):
            director.update(1/60, scene.player)
    assert len(scene.enemy_manager.enemies) == 4
    scene.player.x = 3300
    scene.player.rect.x = 3300
    for _ in range(240):
        director.update(1/60, scene.player)
    assert director.next_trigger == 24
    assert len(director.entries) == 24
    assert len(scene.enemy_manager.enemies) <= 5
    assert len(director.pending) <= 24
    old_high = director.high_water
    scene.player.x = 0
    scene.player.rect.x = 0
    director.update(1/60, scene.player)
    assert director.high_water == old_high and director.next_trigger == 24


@pytest.mark.parametrize('world_id', ('alien_008', 'alien_009', 'alien_006', 'alien_002'))
def test_each_style_exposes_full_windup_before_attacking(game, world_id):
    scene = place_at_first_trigger(game)
    spec = world_config(world_id)
    threat = PlanetThreat('timing_fixture', 360, 216, spec)
    threat.update(1/60, scene.player, scene.room, scene.enemy_manager)
    assert threat.state == 'windup' and threat.telegraph_active
    assert threat.target_aim_pos == scene.player.rect.center
    for _ in range(45):
        threat.update(1/60, scene.player, scene.room, scene.enemy_manager)
    assert threat.state == 'windup' and threat.telegraph_active
    assert not scene.enemy_manager.projectiles
    for _ in range(20):
        threat.update(1/60, scene.player, scene.room, scene.enemy_manager)
    if spec['style'] in ('strafe', 'pulse'):
        assert scene.enemy_manager.projectiles
    else:
        assert threat.state in ('attack', 'recovery')


def _shoot(game, enemy):
    scene = game.current_scene
    x, y = scene.camera.world_to_screen(*enemy.rect.center)
    pos = (max(0, min(game.crt.win_w - 1, round(x * game.crt.win_w / 480))),
           max(0, min(game.crt.win_h - 1, round(y * game.crt.win_h / 270))))
    game.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=pos, rel=(0, 0), buttons=(0, 0, 0)))
    game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
    step(game, 2)
    game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=pos))
    step(game, 25)


def test_mapped_shots_require_multiple_hits_and_defeat_more_than_one_foe(game):
    scene = place_at_first_trigger(game)
    step(game, 75)
    first = scene.enemy_manager.enemies[0]
    press(game, pygame.K_RIGHT)
    for _ in range(120):
        step(game)
        if first.rect.left - scene.player.rect.right < 160:
            break
    press(game, pygame.K_RIGHT, False)
    step(game, 8)
    before = first.health
    _shoot(game, first)
    assert 0 < first.health < before, (before, first.health)
    for _ in range(5):
        if first.is_dead:
            break
        _shoot(game, first)
    assert first.is_dead and first.hit_count >= 3
    # The next real high-water spawn comes from continued mapped movement.
    press(game, pygame.K_RIGHT)
    for _ in range(240):
        step(game)
        others = [e for e in scene.enemy_manager.enemies if e is not first and not e.is_dead]
        if others and others[0].rect.left - scene.player.rect.right < 160:
            break
    press(game, pygame.K_RIGHT, False)
    step(game, 8)
    assert others
    second = others[0]
    for _ in range(6):
        if second.is_dead:
            break
        _shoot(game, second)
    assert second.is_dead and second.hit_count >= 3


def test_room_reentry_resets_visit_and_does_not_mutate_campaign(game):
    scene = place_at_first_trigger(game)
    before = dict(game.campaign.state.room_flags)
    step(game, 75)
    assert scene.enemy_manager.enemies and scene.forward_encounter.next_trigger
    game.change_state(config.STATE_BUNKER_HUB)
    game.change_state(config.STATE_FIELD_OPS, room='alien_worlds/alien_008_field.json',
                      spawn='default', journey_world='alien_008', campaign_route=True)
    assert game.current_scene.forward_encounter.next_trigger == 0
    assert not game.current_scene.enemy_manager.enemies
    assert game.campaign.state.room_flags == before


def test_assisted_player_survives_three_actual_enemy_hits(game):
    scene = place_at_first_trigger(game)
    step(game, 75)
    enemy = scene.enemy_manager.enemies[0]
    health = [scene.player.health]
    for _ in range(3):
        step(game, 60)  # Wait for knockback recovery, then approach normally.
        press(game, pygame.K_RIGHT)
        for _ in range(180):
            step(game)
            if enemy.rect.left - scene.player.rect.right < 100:
                break
        press(game, pygame.K_RIGHT, False)
        step(game, 10)
        for _ in range(600):
            step(game)
            if scene.player.health < health[-1]:
                break
        health.append(scene.player.health)
        assert health[-1] < health[-2]
        assert not scene.player.is_dead
    assert health == [100, 92, 84, 76]


def test_death_respawn_and_new_game_clear_visit_encounters(game):
    scene = place_at_first_trigger(game)
    step(game, 75)
    assert scene.enemy_manager.enemies
    # Explicit lethal fixture exercises the real automatic checkpoint respawn.
    scene.player.take_damage(10000, damage_source='hostile')
    assert scene.player.is_dead
    step(game, 2)
    assert not scene.player.is_dead and scene.player.health == 100
    assert not scene.enemy_manager.enemies and scene.forward_encounter.next_trigger == 0
    assert game.start_new_game(replace_existing=True)[0]
    game.change_state(config.STATE_FIELD_OPS, room='alien_worlds/alien_008_field.json',
                      spawn='default', journey_world='alien_008', campaign_route=True)
    assert not game.current_scene.enemy_manager.enemies
    assert game.current_scene.forward_encounter.next_trigger == 0


def test_active_hazard_keeps_moving_when_field_becomes_crowded(game, monkeypatch):
    scene = place_at_first_trigger(game)
    sprite = pygame.Surface((96, 72), pygame.SRCALPHA)
    pygame.draw.rect(sprite, (255, 180, 60, 255), (10, 12, 76, 50))
    monkeypatch.setattr('video_game.engine.world_hazards.load_planet_threat',
                        lambda root, ident: (sprite, (10, 12, 86, 62), (48, 64)))
    spec = world_config('alien_008')
    hazard = WorldHazards(game.assets.root, scene.room, spec['hazard'])
    assert hazard.enabled
    scene.world_hazards = hazard
    hazard.phase, hazard.x = 'active', 500.
    scene.enemy_manager.add_enemy(PlanetThreat('crowd_one', 650, 216, spec))
    scene.enemy_manager.add_enemy(PlanetThreat('crowd_two', 750, 216, spec))
    old_x = hazard.x
    step(game)
    assert hazard.phase == 'active' and hazard.x < old_x


def test_native_body_faces_enemy_direction_with_cached_mirrored_pivot_and_hit_alpha(game, monkeypatch):
    scene = game.current_scene
    body = pygame.Surface((96, 72), pygame.SRCALPHA)
    body.set_at((83, 20), (255, 80, 30, 191))  # Asymmetric right-facing tip.
    body.set_at((10, 30), (25, 220, 150, 83))
    director = PlanetEncounter(scene.room, scene.enemy_manager, 'alien_008', body=body)
    threat = PlanetThreat('direction_fixture', 400, 216, world_config('alien_008'), custom_body=True)
    scene.enemy_manager.add_enemy(threat)

    class Recorder:
        def __init__(self):
            self.layers = []
        def composite_native_effects(self, layers):
            self.layers.extend(layers)

    # Rendering must use the cached variants, not perform a per-frame flip.
    def unexpected_flip(*args, **kwargs):
        raise AssertionError('Per-frame flip')
    monkeypatch.setattr(pygame.transform, 'flip', unexpected_flip)
    x, y = scene.camera.world_to_screen(threat.rect.centerx, threat.rect.bottom)
    threat.facing = 'right'
    right = Recorder()
    director.render(right, scene.camera)
    image, dest, _ = right.layers[0]
    assert dest == (2*x - 48, 2*y - 64)
    assert image.get_at((83, 20)) == body.get_at((83, 20))

    threat.facing = 'left'
    left = Recorder()
    director.render(left, scene.camera)
    image, dest, _ = left.layers[0]
    assert dest == (2*x - 47, 2*y - 64)
    assert image.get_at((12, 20)) == body.get_at((83, 20))
    assert image.get_at((85, 30)) == body.get_at((10, 30))
    threat.state = 'hurt'
    hurt = Recorder()
    director.render(hurt, scene.camera)
    image, dest, _ = hurt.layers[0]
    assert dest == (2*x - 47, 2*y - 64)
    assert image.get_at((12, 20)).a == 191 and image.get_at((85, 30)).a == 83


@pytest.mark.parametrize('slug', ('pillar_approach', 'buried_archive', 'crust_waveguide'))
def test_archaeological_room_connects_effigy_and_warns(game, monkeypatch, slug):
    sprite = pygame.Surface((96, 72), pygame.SRCALPHA)
    pygame.draw.rect(sprite, (255, 180, 60, 255), (10, 12, 76, 50))
    monkeypatch.setattr('video_game.engine.world_hazards.load_planet_threat',
                        lambda root, ident: (sprite, (10, 12, 86, 62), (48, 64))
                        if ident == 'resonance_effigy' else None)
    game.change_state(config.STATE_FIELD_OPS, room=f'act_05/{slug}.json', spawn='default')
    scene = game.current_scene
    hazard = scene.world_hazards
    assert hazard and hazard.enabled and hazard.kind == 'stone_effigy'
    # Controlled scene fixture isolates the real field update from encounter pressure.
    scene.forward_encounter = None
    scene.enemy_manager.clear()
    scene.player.x = 240
    scene.player.rect.x = 240
    step(game, 485)
    assert hazard.phase == 'warning'
    assert scene.player.health == 100


def test_archaeological_arena_has_no_field_effigy(game):
    game.change_state(config.STATE_FIELD_OPS, room='act_05/core_prime_arena.json', spawn='default')
    assert game.current_scene.world_hazards is None


def test_swoop_hover_phase_freezes_during_pause_stun_and_hurt(game):
    scene=game.current_scene
    threat=PlanetThreat('hover_fixture',300,216,{**world_config('alien_009'), 'style': 'swoop'})
    threat.update(1/60,scene.player,scene.room,scene.enemy_manager)
    phase,y=threat.hover_phase,threat.y
    threat.update(.1,scene.player,scene.room,scene.enemy_manager,is_paused=True)
    assert (threat.hover_phase,threat.y)==(phase,y)
    threat.apply_status('stun',.3)
    threat.update(.05,scene.player,scene.room,scene.enemy_manager)
    assert (threat.hover_phase,threat.y)==(phase,y)
    threat.clear_statuses()
    assert threat.take_damage(1,hit_id='fixture').hit
    threat.update(.05,scene.player,scene.room,scene.enemy_manager)
    assert (threat.hover_phase,threat.y)==(phase,y)
    threat.reset_to_spawn()
    assert threat.hover_phase==0 and threat.y==216


@pytest.mark.parametrize('dt', [1/30,1/60])
def test_swoop_recovery_resumes_without_vertical_snap(game,dt):
    scene=game.current_scene
    scene.player.x=80;scene.player.rect.x=80
    threat=PlanetThreat('swoop_fixture',300,216,{**world_config('alien_009'), 'style': 'swoop'})
    states=set();previous_y=threat.y
    for i in range(round(8/dt)):
        previous_state=threat.state;previous_phase=threat.hover_phase
        threat.update(dt,scene.player,scene.room,scene.enemy_manager)
        states.add(previous_state)
        if previous_state!='patrol':
            assert threat.hover_phase==previous_phase
        if i:
            # The analytic hover derivative is bounded by 5*2 px/sec.
            assert abs(threat.y-previous_y) <= 10*dt + 1e-6
        previous_y=threat.y
    assert {'patrol','windup','attack','recovery'} <= states


def test_swoop_patrol_phase_is_frame_rate_independent(game):
    scene=game.current_scene
    scene.player.x=0;scene.player.rect.x=0
    a=PlanetThreat('swoop_30',1000,216,{**world_config('alien_009'), 'style': 'swoop'})
    b=PlanetThreat('swoop_60',1000,216,{**world_config('alien_009'), 'style': 'swoop'})
    for _ in range(60):a.update(1/30,scene.player,scene.room,scene.enemy_manager)
    for _ in range(120):b.update(1/60,scene.player,scene.room,scene.enemy_manager)
    assert a.hover_phase==pytest.approx(b.hover_phase,abs=1e-10)
    assert a.y==pytest.approx(b.y,abs=1e-10)


def test_ground_stride_follows_displacement_and_stops_for_pause_stun_and_walls(game, monkeypatch):
    scene = game.current_scene
    threat = PlanetThreat('stride_fixture', 1000, 216, world_config('alien_scan_h'))
    threat.cooldown_timer = 100
    start = threat.x
    threat.update(.1, scene.player, scene.room, scene.enemy_manager)
    assert threat.stride_distance == pytest.approx(abs(threat.x - start))
    assert threat.stride_distance > 0
    distance = threat.stride_distance
    threat.update(.1, scene.player, scene.room, scene.enemy_manager, is_paused=True)
    assert threat.stride_distance == distance
    threat.apply_status('stun', .5)
    threat.update(.1, scene.player, scene.room, scene.enemy_manager)
    assert threat.stride_distance == distance and threat.last_move_distance == 0
    threat.clear_statuses()
    monkeypatch.setattr(scene.room, 'check_rect_collision', lambda rect: {'solid': True, 'hazard': False})
    threat.update(.1, scene.player, scene.room, scene.enemy_manager)
    assert threat.stride_distance == distance and threat.last_move_distance == 0
    threat.reset_to_spawn()
    assert threat.stride_distance == threat.last_move_distance == 0


@pytest.mark.parametrize('world', ('alien_scan_h', 'alien_010', 'alien_007'))
def test_animated_creatures_have_cached_directional_leg_cycles(game, monkeypatch, world):
    from video_game.engine.planet_threat_assets import STRIDE_LENGTH
    game.change_state(config.STATE_FIELD_OPS, room=f'alien_worlds/{world}_field.json',
                      spawn='default', journey_world=world, campaign_route=True)
    scene = game.current_scene
    director = scene.forward_encounter
    assert len(director.run_frames) == 4
    assert len(scene.world_hazards.run_frames) == 4
    threat = PlanetThreat('run_fixture', 400, 216, world_config(world), custom_body=True)
    scene.enemy_manager.add_enemy(threat)
    def unexpected(*args, **kwargs):
        pytest.fail('Rendering should reuse cached poses')
    monkeypatch.setattr(pygame.image, 'load', unexpected)
    monkeypatch.setattr(pygame.transform, 'flip', unexpected)
    class Recorder:
        def __init__(self): self.layers = []
        def composite_native_effects(self, layers): self.layers.extend(layers)
    images = []
    for index in range(4):
        threat.stride_distance = index * STRIDE_LENGTH / 4
        threat.last_move_distance = 1
        threat.facing = 'left'
        result = Recorder()
        director.render(result, scene.camera)
        image, dest, _ = result.layers[0]
        assert image is director.run_frames_left[index]
        assert dest[1] == 2 * scene.camera.world_to_screen(0, threat.rect.bottom)[1] - 64
        images.append(pygame.image.tobytes(image.subsurface((0, 40, 96, 24)), 'RGBA'))
    assert len(set(images)) == 4
    threat.last_move_distance = 0
    result = Recorder()
    director.render(result, scene.camera)
    assert result.layers[0][0] is director.body_left
