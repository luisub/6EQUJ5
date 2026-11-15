"""PURPOSE: Mapped intro/pickup lifecycle and combat/render regression coverage.
CALLED BY: pytest.
HOW TO MODIFY: Preserve normal input routing and explicitly disclose fixtures.
"""
import json
from pathlib import Path

import pygame
import pytest

from video_game.engine import config
from video_game.engine.alien_journey import journey_data
from video_game.engine.combat_feedback import CombatFeedback
from video_game.engine.opening_story import OpeningStory
from video_game.engine.temporary_weapons import PROFILES, WeaponPickups
from video_game.engine.weapons import CombatTarget, ProjectileManager
from video_game.engine.world import Room
from .test_opening_story import game, key, controller, click, title_start


def step(game, frames=1):
    for _ in range(frames):
        game.update(1 / 60)
        game.input.begin_frame()


def enter_field(game):
    title_start(game)
    key(game, pygame.K_RETURN, down=False)
    key(game, pygame.K_RETURN)  # Explicit Skip, then release before leaving.
    key(game, pygame.K_RETURN, down=False)
    key(game, pygame.K_RETURN)
    key(game, pygame.K_RETURN, down=False)
    assert game.current_state_name == config.STATE_FIELD_OPS
    return game.current_scene


@pytest.mark.parametrize('source', ['mouse', 'keyboard', 'controller'])
def test_next_reaches_map_inside_bunker_and_begin_does_not_exit(game, source, monkeypatch):
    title_start(game)
    key(game, pygame.K_RETURN, down=False)
    if source == 'controller':
        game.input._controller_state[37] = {'buttons': set(), 'axes': {}}
    for index in range(1, 5):
        if source == 'mouse':
            click(game, OpeningStory.NEXT_BUTTON.center)
            click(game, OpeningStory.NEXT_BUTTON.center, down=False)
        elif source == 'keyboard':
            key(game, pygame.K_n)
            key(game, pygame.K_n, down=False)
        else:
            controller(game, pygame.CONTROLLER_BUTTON_X)
            controller(game, pygame.CONTROLLER_BUTTON_X, down=False)
        assert game.current_state_name == config.STATE_BUNKER_HUB
        story = game.current_scene.opening_story
        if index < 4:
            assert story.index == index
            if index == 3:
                assert story.pages[index]['visual'] == 'galaxy_map'
                assert story.map_image is not None
                labels = []
                original = game.crt.draw_text
                def record(text, *args, **kwargs):
                    labels.append(text)
                    return original(text, *args, **kwargs)
                monkeypatch.setattr(game.crt, 'draw_text', record)
                game.render()
                assert {'EARTH', *(str(n) for n in range(1, len(journey_data()['worlds']) + 1))} <= set(labels)
        else:
            assert story is None


def test_walking_collects_weapon_and_focus_freezes_then_expiry_restores_maser(game):
    scene = enter_field(game)
    assert scene.weapon_pickups.items
    key(game, pygame.K_d)
    for _ in range(150):
        step(game)
        if scene.player.arsenal.temporary_id:
            break
    key(game, pygame.K_d, down=False)
    arsenal = scene.player.arsenal
    assert arsenal.temporary_id == 'arc_lance'
    assert scene.player.weapon.id == 'arc_lance'
    remaining = arsenal.temporary_remaining
    game.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
    step(game, 120)
    assert arsenal.temporary_remaining == remaining
    key(game, pygame.K_F2)
    assert not game.pause.active
    # The earned pickup is retained while a deterministic empty combat fixture
    # isolates expiry from enemy damage and automatic checkpoint respawn.
    scene.forward_encounter = None
    scene.enemy_manager.clear()
    scene.world_hazards = None
    step(game, 1090)
    assert arsenal.temporary_id is None
    assert scene.player.weapon is arsenal.weapons['starter_maser']
    assert not arsenal.weapons['starter_maser'].is_charging


@pytest.mark.parametrize('weapon_id', list(PROFILES))
@pytest.mark.parametrize('source', ['mouse', 'keyboard', 'controller'])
def test_pickup_fires_with_mapped_input_and_cannot_unlock_permanently(game, weapon_id, source):
    scene = enter_field(game)
    item = next(item for item in scene.weapon_pickups.items if item['weapon_id'] == weapon_id)
    # Position is a declared fixture; collection still runs the real scene loop.
    scene.player.x = item['rect'].x
    scene.player.y = item['rect'].bottom - scene.player.height
    scene.player.rect.topleft = (scene.player.x, scene.player.y)
    step(game)
    arsenal = scene.player.arsenal
    assert arsenal.temporary_id == weapon_id
    x, y = scene.player.get_muzzle_world_pos()
    target = CombatTarget('pickup_target', pygame.Rect(round(x + 45), round(y - 14), 22, 28), 1000, 1000)
    scene.camera.snap_to(scene.player.rect.centerx, scene.player.rect.centery)
    scene.enemy_manager.clear()
    scene.forward_encounter = None
    scene.world_hazards = None
    if source == 'mouse':
        pos = (round((target.rect.centerx - scene.camera.x) * game.crt.win_w / 480),
               round((target.rect.centery - scene.camera.y) * game.crt.win_h / 270))
        game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
    elif source == 'keyboard':
        key(game, pygame.K_x)
    else:
        game.input._controller_state[37] = {'buttons': set(), 'axes': {}}
        game.handle_event(pygame.event.Event(pygame.CONTROLLERAXISMOTION, instance_id=37,
                                             axis=pygame.CONTROLLER_AXIS_TRIGGERRIGHT, value=32767))
    step(game)
    shots = list(scene.projectile_manager.projectiles)
    assert shots and all(shot.weapon_type == weapon_id for shot in shots)
    # Keep the actual fired trajectories, move a target onto their central ray.
    primary = next(shot for shot in shots if shot.is_primary_discharge)
    target.rect.center = (round(primary.x + primary.dir_x * 35), round(primary.y + primary.dir_y * 35))
    hits = scene.projectile_manager.update(.10, scene.room, [target])
    assert any(hit.damage_dealt > 50 for hit in hits)
    assert target.health < 950
    game.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
    before = scene.projectile_manager._next_id
    key(game, pygame.K_F2)
    step(game, 30)
    assert scene.projectile_manager._next_id == before
    assert game.save_checkpoint()
    serialized = json.dumps(game.campaign.state.to_dict()) if hasattr(game.campaign.state, 'to_dict') else json.dumps(game.campaign.to_dict())
    assert weapon_id not in serialized
    game.change_state(config.STATE_BUNKER_HUB)
    assert arsenal.temporary_id is None
    assert arsenal.active_weapon.id == 'starter_maser'
    assert weapon_id not in arsenal.to_dict()['unlocked_weapons']


def test_retry_and_new_game_reset_pickups_and_effects(game):
    scene = enter_field(game)
    scene.player.arsenal.equip_temporary('nova_scatter')
    scene.feedback.emit(90, 200, 'destroy')
    scene.player.take_damage(10000, ignore_invulnerable=True)
    step(game, 2)
    assert scene.player.arsenal.temporary_id is None
    assert scene.player.weapon.id == 'starter_maser'
    assert all(not item['collected'] for item in scene.weapon_pickups.items)
    assert all(event['kind'] == 'checkpoint' for event in scene.feedback.events)
    game.change_state(config.STATE_BOSS_BOUNTY)
    boss = game.current_scene
    boss.player.arsenal.equip_temporary('arc_lance')
    boss.weapon_pickups.items[0]['collected'] = True
    boss.retry_from_checkpoint()
    assert boss.player.weapon.id == 'starter_maser'
    assert all(not item['collected'] for item in boss.weapon_pickups.items)
    game.start_new_game()
    assert scene.player.arsenal.temporary_id is None


def test_all_authored_field_pickups_are_supported_and_clear(game):
    root = config.DATA_DIR / 'levels'
    total = 0
    for path in root.rglob('*.json'):
        room = Room.load_from_file(path)
        for item in WeaponPickups(room).items:
            collision = room.check_rect_collision(item['rect'])
            assert not collision['solid'] and not collision['hazard'], path
            assert 0 <= item['rect'].left < room.width_px
            total += 1
    assert total > 70


def test_feedback_pool_and_caches_are_bounded_and_pause_frozen(game):
    feedback = CombatFeedback()
    scene = enter_field(game)
    for index in range(200):
        feedback.emit(100 + index % 8, 160, 'destroy', '-90')
    assert len(feedback.events) == feedback.MAX_EVENTS
    remaining = feedback.events[0]['life']
    feedback.update(1, paused=True)
    assert feedback.events[0]['life'] == remaining
    for _ in range(40):
        game.crt.clear()
        feedback.render(game.crt, scene.camera)
        feedback.update(1 / 60)
    assert not feedback.events
    assert len(feedback.glows) <= 64 and len(feedback.stamps) <= 256
