"""Fresh campaigns can cross Ohio without item or laboratory prerequisites."""
import pygame
import pytest

from video_game.engine import config
from video_game.engine.scenes.lab import ScienceLabScene
from .test_campaign_world_route import game, key


@pytest.mark.parametrize('mode', ['classic', 'assisted'])
def test_fresh_next_crosses_all_ohio_boundaries_without_collection(game, mode):
    game.change_settings(combat_mode=mode)
    key(game, pygame.K_SPACE)
    assert game.current_state_name == config.STATE_FIELD_OPS
    rooms = ['act_01_approach', 'act_01_ohio_campus', 'act_01_salvage_yard',
             'act_01_dish_catwalk', 'act_01_greenkeeper_arena']
    field = game.current_scene
    for origin, destination in zip(rooms, rooms[1:]):
        assert field.room.room_id == origin
        # Isolate each boundary from combat and platforming; no progress is granted.
        exit = next(e for e in field.room.exits if e.target_room == destination)
        field.player.x, field.player.y = exit.x, 208
        field.player.rect.topleft = (exit.x, 208)
        field.player.vx = field.player.vy = 0
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
        game.update(1 / 60)
    assert game.current_state_name == config.STATE_BOSS_BOUNTY
    assert game.current_scene.room.room_id == rooms[-1]
    assert game.current_scene.boss.health > 0
    assert game.save_checkpoint()
    state = game.save_store.load().campaign.state
    assert not state.extracted_fragments and not state.validation_records
    assert not state.inventory.get('analog_coupler', 0)
    for flag in ('trench_coupler_collected', 'feedhorn_repaired',
                 'dish_defense_completed', 'greenkeeper_defeated'):
        assert not state.room_flags.get(flag, False)

    # A lethal hit isolates the normal victory/save transition from combat skill.
    game.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_RIGHT))
    boss = game.current_scene
    boss.boss.take_damage(1000, hit_pos=(boss.boss.x, boss.boss.y))
    game.update(1 / 60)
    assert game.campaign.state.room_flags['greenkeeper_defeated']
    key(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_FIELD_OPS
    assert game.current_scene.room.room_id == 'act_02_blackout_street'
    saved = game.save_store.load().campaign.state
    assert saved.room_flags['act_02_unlocked']
    assert not saved.validation_records and not saved.extracted_fragments


@pytest.mark.parametrize('manual', [False, True])
@pytest.mark.parametrize('method', ['keyboard', 'mouse', 'controller'])
def test_empty_lab_has_working_way_out_without_a_signal_sample(game, manual, method):
    game.change_state(config.STATE_SCIENCE_LAB)
    lab = game.current_scene
    assert isinstance(lab, ScienceLabScene)
    if manual:
        key(game, pygame.K_m)
        key(game, pygame.K_5)  # Reproduce the empty advanced bench in the report.
    assert lab.workbench.active_scenario is None
    game.render()
    button = game.crt.render_surface.subsurface((528, 404, 356, 48))
    pixels = pygame.surfarray.array3d(button)
    assert ((pixels == config.COLOR_FIBO_GOLD).all(axis=2)).sum() > 10
    if method == 'keyboard':
        key(game, pygame.K_RETURN)
    elif method == 'controller':
        game.input._controller_state[37] = {'buttons': set(), 'axes': {}}
        game.handle_event(pygame.event.Event(pygame.CONTROLLERBUTTONDOWN,
                                            instance_id=37, button=pygame.CONTROLLER_BUTTON_A))
    else:
        pygame.display.set_mode((game.crt.win_w, game.crt.win_h))
        pos = (round(353 * game.crt.win_w / 480), round(214 * game.crt.win_h / 270))
        game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
    assert game.current_state_name == config.STATE_FIELD_OPS
    assert game.current_scene.room.room_id == 'act_01_approach'
    assert not game.campaign.state.extracted_fragments
    assert not game.campaign.state.validation_records
    assert not game.input.held('auto_fire')
