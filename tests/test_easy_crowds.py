"""PURPOSE: Exercise Assisted crowd fire, earned recovery, and bounded input handoff.
CALLED BY: pytest tests/test_easy_crowds.py.
HOW TO MODIFY: Use real mapped events and enemy collision; retain Classic and reset checks.
"""
import pygame
import pytest

from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.enemies import CoreReconDrone, EnemyManager
from video_game.engine.input import InputManager
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine


@pytest.fixture
def game(tmp_path, monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    pygame.display.set_mode((960, 540))
    machine = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(tmp_path),
                               settings_store=SettingsStore(tmp_path))
    machine.start_new_game()
    machine.change_settings(combat_mode="assisted")
    machine.change_state(config.STATE_FIELD_OPS)
    yield machine
    machine.close()
    pygame.quit()


def test_mapped_mouse_fire_defeats_enemy_and_rewards_once(game):
    scene = game.current_scene
    scene.forward_encounter = None
    player = scene.player
    player.health = 70
    # Fixture places a real enemy in the projectile path; firing and damage use
    # normal events, field updates, swept collision and the enemy manager.
    enemy = CoreReconDrone("reward_test", player.x + 70, player.y + 4)
    scene.enemy_manager.add_enemy(enemy)
    target = (round((enemy.rect.centerx - scene.camera.x) * game.crt.win_w / config.INTERNAL_WIDTH),
              round((enemy.rect.centery - scene.camera.y) * game.crt.win_h / config.INTERNAL_HEIGHT))
    game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=target))
    for _ in range(45):
        game.update(1 / 60)
        game.input.begin_frame()
        if enemy.is_dead:
            break
    assert enemy.is_dead and player.health == 75
    for _ in range(5):
        game.update(1 / 60)
    assert player.health == 75
    game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=target))
    assert not game.input.held("auto_fire")
    enemy.reset_to_spawn()
    enemy.take_damage(1000, hit_id="fixture_after_reset")
    scene.enemy_manager.update(1 / 60, player, scene.room)
    assert player.health == 75


def test_recovery_caps_and_rejects_classic_dead_or_living_enemy(game):
    scene = game.current_scene
    manager = EnemyManager()
    player = scene.player
    player.set_combat_assisted(True)
    player.health = 98
    alive = CoreReconDrone("alive", 200, 100)
    manager.add_enemy(alive)
    manager.update(1 / 60, player, scene.room)
    assert player.health == 98
    alive.take_damage(1000, hit_id="kill")
    manager.update(1 / 60, player, scene.room)
    assert player.health == 100
    player.health = 40
    player.set_combat_assisted(False)
    classic = CoreReconDrone("classic", 200, 100)
    manager.add_enemy(classic)
    classic.take_damage(1000, hit_id="kill")
    manager.update(1 / 60, player, scene.room)
    player.set_combat_assisted(True)
    manager.update(1 / 60, player, scene.room)
    assert player.health == 40
    player.health, player.is_dead = 0, True
    dead = CoreReconDrone("dead_player", 200, 100)
    manager.add_enemy(dead)
    dead.take_damage(1000, hit_id="kill")
    manager.update(1 / 60, player, scene.room)
    assert player.health == 0 and player.is_dead


def test_forward_handoff_masks_overlapping_remaps_and_normal_release():
    mapper = InputManager(bindings={"move_right": (pygame.K_d,), "fire": (pygame.K_d,),
                                    "dash": (pygame.K_d,), "auto_fire": (pygame.K_f,)})
    mapper.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_d))
    mapper.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_f))
    mapper.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(240, 90)))
    mapper.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=3, pos=(240, 90)))
    snapshot = mapper.snapshot_forward_handoff()
    mapper.release_all()
    mapper.restore_forward_handoff(snapshot)
    assert mapper.held("move_right") and mapper.held("auto_fire")
    assert not mapper.held("fire") and not mapper.held("dash")
    assert mapper.mouse_position == (240, 90) and mapper.aim_source == "mouse"
    assert not mapper.pressed("move_right") and not mapper.released("fire")
    mapper.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_d))
    assert not mapper.held("move_right") and not mapper.released("fire")
    mapper.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_d))
    assert mapper.pressed("fire") and mapper.pressed("dash")
    mapper.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_f))
    assert mapper.held("auto_fire")
    mapper.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(241, 90)))
    assert not mapper.held("auto_fire") and mapper.released("auto_fire")
    mapper.release_all()
    assert not any(mapper.held(action) for action in ("move_right", "auto_fire", "fire", "dash"))
    assert mapper.aim_source is None


def test_controller_handoff_retains_only_forward_repeat_and_aim():
    mapper = InputManager()
    mapper._controller_state[4] = {"buttons": set(), "axes": {}}
    def axis(name, value):
        mapper.handle_event(pygame.event.Event(pygame.CONTROLLERAXISMOTION, instance_id=4,
                                              axis=name, value=value))
    axis(pygame.CONTROLLER_AXIS_LEFTX, 30000)
    axis(pygame.CONTROLLER_AXIS_RIGHTX, 20000)
    axis(pygame.CONTROLLER_AXIS_TRIGGERRIGHT, 30000)
    axis(pygame.CONTROLLER_AXIS_TRIGGERLEFT, 30000)
    mapper.handle_event(pygame.event.Event(pygame.CONTROLLERBUTTONDOWN, instance_id=4,
                                          button=pygame.CONTROLLER_BUTTON_B))
    snapshot = mapper.snapshot_forward_handoff()
    mapper.release_all()
    mapper.restore_forward_handoff(snapshot)
    assert mapper.held("move_right") and mapper.held("auto_fire")
    assert not mapper.held("fire") and not mapper.held("dash")
    assert mapper.controller_aim == (1.0, 0.0)
    assert not mapper.pressed("auto_fire")
    axis(pygame.CONTROLLER_AXIS_TRIGGERRIGHT, 0)
    axis(pygame.CONTROLLER_AXIS_LEFTX, 0)
    assert not mapper.held("auto_fire") and not mapper.held("move_right")
    mapper.release_all()
    assert mapper.aim_source is None


def test_paused_enemy_defeat_and_living_retreat_do_not_heal(game):
    scene = game.current_scene
    player = scene.player
    player.set_combat_assisted(True)
    player.health = 60
    defeated = CoreReconDrone("paused", 224, 116)
    scene.enemy_manager.add_enemy(defeated)
    defeated.take_damage(1000, hit_id="fixture")
    scene.enemy_manager.update(1 / 60, player, scene.room, is_paused=True)
    assert player.health == 60
    scene.enemy_manager.update(1 / 60, player, scene.room)
    assert player.health == 65
    scene.enemy_manager.clear()
    retreat = CoreReconDrone("retreat", 20, 116)
    scene.enemy_manager.add_enemy(retreat)
    player.x = 500
    player.rect.x = 500
    scene.camera.x = 300
    scene.forward_encounter.update(1 / 60, player, camera=scene.camera)
    assert retreat not in scene.enemy_manager.enemies and not retreat.is_dead
    scene.enemy_manager.update(1 / 60, player, scene.room)
    assert player.health == 65


def test_boss_defeat_does_not_award_enemy_recovery(game):
    from video_game.engine.bosses.base import STATE_VULNERABLE
    game.change_state(config.STATE_BOSS_BOUNTY)
    scene = game.current_scene
    scene.player.set_combat_assisted(True)
    scene.player.health = 60
    scene.boss.skip_intro()
    scene.boss.phase_state = STATE_VULNERABLE
    scene.boss.weak_point_exposed = True
    scene.boss.health = 1
    scene.boss.take_damage(1000, hit_id="boss_fixture", hit_pos=scene.boss.weak_point_rect.center)
    assert scene.boss.is_dead
    game.update(1 / 60)
    assert scene.player.health == 60


@pytest.mark.parametrize("kind", ["space", "click", "legacy_r"])
def test_boss_retry_uses_fresh_input_without_carrying_controls(game, kind):
    game.change_state(config.STATE_BOSS_BOUNTY)
    scene = game.current_scene
    key = lambda event_type, code: game.handle_event(pygame.event.Event(event_type, key=code))
    click = lambda event_type: game.handle_event(pygame.event.Event(event_type, button=1, pos=(250, 120)))
    key(pygame.KEYDOWN, pygame.K_d)
    key(pygame.KEYDOWN, pygame.K_x)
    if kind == "space":
        key(pygame.KEYDOWN, pygame.K_SPACE)
    elif kind == "click":
        click(pygame.MOUSEBUTTONDOWN)
    assert not scene.player.is_dead  # The same inputs cannot retry a live encounter.
    for _ in range(5):
        game.update(1 / 60)  # Combat starts immediately; held controls retain physical freshness.
    assert scene.encounter_intro_remaining == 0
    scene.player.take_damage(10000, ignore_invulnerable=True)
    assert scene.player.is_dead
    if kind == "space":
        key(pygame.KEYDOWN, pygame.K_SPACE)  # OS repeat is not a fresh press.
        assert scene.player.is_dead
        key(pygame.KEYUP, pygame.K_SPACE)
        key(pygame.KEYDOWN, pygame.K_SPACE)
    elif kind == "click":
        click(pygame.MOUSEBUTTONDOWN)  # A still-held mouse button is not a fresh click.
        assert scene.player.is_dead
        click(pygame.MOUSEBUTTONUP)
        click(pygame.MOUSEBUTTONDOWN)
    else:
        key(pygame.KEYDOWN, pygame.K_r)
    assert not scene.player.is_dead
    assert scene.encounter_intro_remaining == 0
    assert not any(game.input.held(action) for action in ("move_right", "fire", "auto_fire", "jump"))
    game.update(1 / 60)
    assert not scene.proj_mgr.projectiles and not scene.player.weapon.is_charging


def test_boss_retry_input_does_not_activate_while_paused_or_in_victory(game):
    game.change_state(config.STATE_BOSS_BOUNTY)
    scene = game.current_scene
    scene.player.take_damage(10000, ignore_invulnerable=True)
    game.open_pause()
    game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(250, 120)))
    assert scene.player.is_dead
    game.pause.close()
    scene.is_defeated_sequence = True
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
    assert scene.player.is_dead and scene.is_defeated_sequence


def test_supporting_ray_render_is_quiet_and_selected_override_wins():
    from dataclasses import asdict
    from video_game.engine.weapons import ProjectileManager

    manager = ProjectileManager()
    def beam(y, **kwargs):
        return manager.spawn(110, y, 1, 0, 420, 25, beam_length=60, **kwargs)
    center = beam(20)
    flank = beam(40, is_primary_discharge=False)
    selected = beam(60, is_primary_discharge=False)
    charged = beam(80, is_charged=True, is_primary_discharge=False)
    other = beam(100, weapon_type="scattergun", is_primary_discharge=False)
    before = [asdict(p) for p in manager.projectiles]
    surface = pygame.Surface((140, 120))
    surface.fill((0, 0, 0))
    camera = type("Camera", (), {"world_to_screen": staticmethod(lambda x, y: (round(x), round(y)))})()
    manager.render(surface, camera, narrow_projectile_ids={selected.id})
    def pixels(y):
        return [surface.get_at((80, row))[:3] for row in range(y - 5, y + 6)
                if surface.get_at((80, row))[:3] != (0, 0, 0)]
    assert len(pixels(20)) == 5 and (255, 255, 240) in pixels(20)
    assert len(pixels(40)) == 2 and set(pixels(40)) == {(90, 160, 170), (190, 225, 210)}
    assert len(pixels(60)) == 3 and set(pixels(60)) == {(145, 220, 195), (240, 255, 239)}
    assert len(pixels(80)) == 5 and (255, 180, 50) in pixels(80)
    assert len(pixels(100)) == 5 and (100, 220, 255) in pixels(100)
    for shot in (center, flank, selected, charged, other):
        assert surface.get_at((50, int(shot.y)))[:3] != (0, 0, 0)
        assert surface.get_at((110, int(shot.y)))[:3] != (0, 0, 0)
    assert [asdict(p) for p in manager.projectiles] == before
