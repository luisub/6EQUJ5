"""Player-controlled pacing, using disposable saves and explicit progress fixtures."""
import pygame
import pytest

from video_game.engine import config
from video_game.engine.alien_journey import ledger, journey_data
from video_game.engine.ui.dialogue import NEXT_BUTTON, paginate
from .test_campaign_world_route import game, key, ohio_fixture
from .test_alien_journey_runtime import enter_first_guardian


def activate(game, method, rect=NEXT_BUTTON, button=pygame.CONTROLLER_BUTTON_A):
    if method == 'keyboard':
        key(game, pygame.K_RETURN)
    elif method == 'controller':
        game.handle_event(pygame.event.Event(pygame.CONTROLLERBUTTONDOWN,
                                            button=button))
        game.handle_event(pygame.event.Event(pygame.CONTROLLERBUTTONUP,
                                            button=button))
    else:
        pygame.display.set_mode((game.crt.win_w, game.crt.win_h))
        pos = (round(rect.centerx * game.crt.win_w / 480), round(rect.centery * game.crt.win_h / 270))
        game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
        game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=pos))


@pytest.mark.parametrize('phase', ['active', 'jammed', 'failed'])
@pytest.mark.parametrize('method', ['keyboard', 'controller', 'mouse'])
def test_repair_opens_gate_without_waiting_or_granting_defense_reward(game, phase, method):
    from video_game.engine.scenes.field import CONTEXT_BUTTON
    # Prior discoveries are fixtures; the repair and exit use actual mapped input.
    assert game.campaign.apply_event({'event_id': 'fixture_contact', 'type': 'record_contact',
                                      'payload': {'civilization_id': 'FASR-001'}})
    for event in ('grant_fragment_fasr_001', 'validate_fasr_001_deploy', 'collect_analog_coupler'):
        assert game.campaign.apply_event({'event_id': 'fixture_' + event, 'type': event})
    game.change_state(config.STATE_FIELD_OPS, room='act_01/dish_catwalk.json')
    field = game.current_scene
    field.player.x, field.player.y = 288, 208
    field.player.rect.topleft = (288, 208)
    key(game, pygame.K_e)
    assert field.holdout.is_active and field.holdout.elapsed_time < 1
    if phase == 'jammed':
        field.holdout.is_jammed = True
    elif phase == 'failed':
        field.holdout.fail('fixture failure')
    gate = next(e for e in field.room.exits if e.target_room == 'act_01_greenkeeper_arena')
    field.player.x, field.player.y = gate.x, 208
    field.player.rect.topleft = (gate.x, 208)
    assert field._context_label() == 'UP / CLICK: ENTER'
    activate(game, method, CONTEXT_BUTTON, pygame.CONTROLLER_BUTTON_X)
    assert game.current_state_name == config.STATE_BOSS_BOUNTY
    assert field.holdout.elapsed_time < 1
    assert not game.campaign.state.room_flags.get('dish_defense_completed', False)
    assert game.save_checkpoint()
    saved = game.save_store.load().campaign.state
    assert saved.room_flags['feedhorn_repaired']
    assert not saved.room_flags.get('dish_defense_completed', False)


@pytest.mark.parametrize('method', ['keyboard', 'controller', 'mouse'])
def test_victory_and_travel_can_be_advanced_without_animation_waits(game, method):
    world, boss = enter_first_guardian(game, acknowledge=False)
    assert boss.destruction and not boss.destruction.done
    assert boss.destruction.elapsed < .1
    activate(game, method)
    assert game.current_state_name == config.STATE_ALIEN_CONTACT
    assert len(game.current_scene.pages) == 1
    activate(game, method)
    assert game.current_state_name == config.STATE_GALAXY_TRANSIT
    assert game.current_scene.elapsed < .1
    activate(game, method)
    assert game.current_state_name == config.STATE_FIELD_OPS
    assert ledger(game.campaign)['world_id'] == world['next_world']
    assert ledger(game.campaign)['receipts'] == [world['civ_id']]
    assert game.save_store.load().campaign.state.world_states['bunker_hub']['alien_journey']['receipts'] == [world['civ_id']]


def test_new_area_has_no_modal_briefing_and_accepts_movement(game):
    ohio_fixture(game)
    game.change_state(config.STATE_FIELD_OPS, room='act_02/blackout_street.json',
                      campaign_route=True, show_intro=True)
    field = game.current_scene
    assert field.route_story is None
    x = field.player.x
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
    game.update(1 / 60)
    assert field.player.x > x


def test_every_contact_fits_one_short_page_with_portrait(game):
    for world in journey_data()['worlds']:
        assert len(paginate(world['contact_pages'], game.crt.font_md, width=274)) == 1
