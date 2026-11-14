"""PURPOSE: Verify the completed Ohio boundary through routed input and temporary saves.
CALLED BY: pytest.
HOW TO MODIFY: Preserve guarded exits, temporary saves and the earned Neo-Denver departure contract.
"""
import copy

import pygame
import pytest

from video_game.engine import config
from .test_simple_bunker_exit import game, key, setup_stage


@pytest.mark.parametrize('action', ['enter', 'up', 'button'])
def test_completed_boundary_exits_without_changing_campaign(game, action):
    setup_stage(game, 'complete')
    assert game.save_checkpoint()
    before = copy.deepcopy(game.campaign.to_dict())
    if action == 'button':
        rect = game.current_scene.EXPLORE_BUTTON
        pos = (round(rect.centerx * game.crt.win_w / 480),
               round(rect.centery * game.crt.win_h / 270))
        game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
    else:
        key(game, pygame.K_RETURN if action == 'enter' else pygame.K_UP)
    assert game.current_state_name == config.STATE_FIELD_OPS
    assert game.current_scene.room_path.name == 'blackout_street.json'
    assert game.campaign.to_dict() == before
    assert game.save_store.load().campaign.to_dict() == before


def test_boundary_labels_persist_and_fit(game, monkeypatch):
    setup_stage(game, 'complete')
    bunker = game.current_scene
    objective = bunker.objective_tracker.get_active_objective(game.campaign)
    assert (objective.id, objective.title, objective.is_completed) == (
        'obj_act_02', 'NEO-DENVER // BLACKOUT', False)
    labels = {}
    original = game.crt.draw_text
    def capture(text, *args, **kwargs):
        rect = original(text, *args, **kwargs)
        labels[text] = rect
        return rect
    monkeypatch.setattr(game.crt, 'draw_text', capture)
    for _ in range(2):
        labels.clear()
        game.render()
        panel = pygame.Rect(12, 36, 456, 60)
        for label in ('MISSION ROUTE AVAILABLE',
                      'CONTINUE TO THE LATEST UNLOCKED SECTOR',
                      'CONTINUE'):
            assert label in labels
            assert panel.contains(labels[label])
        assert bunker.EXPLORE_BUTTON.contains(labels['CONTINUE'])
        assert labels['ENTER / UP: CONTINUE MISSION'].right < bunker.DETAILS_BUTTON.left
        game.update(30.0)


def test_completed_boundary_dossier_and_pause_capture_actions(game):
    setup_stage(game, 'complete')
    bunker = game.current_scene
    pos = (round(bunker.EXPLORE_BUTTON.centerx * game.crt.win_w / 480),
           round(bunker.EXPLORE_BUTTON.centery * game.crt.win_h / 270))
    key(game, pygame.K_TAB)
    assert bunker.dossier_open
    game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
    key(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_BUNKER_HUB
    key(game, pygame.K_ESCAPE)
    key(game, pygame.K_ESCAPE)
    assert game.pause.active
    game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
    assert game.current_state_name == config.STATE_BUNKER_HUB


def test_incomplete_has_original_label_and_no_boundary(game, monkeypatch):
    labels = []
    original = game.crt.draw_text
    def capture(text, *args, **kwargs):
        labels.append(text)
        return original(text, *args, **kwargs)
    monkeypatch.setattr(game.crt, 'draw_text', capture)
    game.render()
    assert 'ENTER / UP: GO OUTSIDE' in labels
    assert 'MISSION ROUTE AVAILABLE' not in labels
    assert 'CONTINUE' not in labels


def test_unfinished_card_area_does_not_depart_and_airlock_label_is_unchanged(game):
    bunker = game.current_scene
    bunker.mateo_x = 348
    assert bunker.station_prompt(game.crt)[0] == 'E: USE AIRLOCK'
    pos = (round(bunker.EXPLORE_BUTTON.centerx * game.crt.win_w / 480),
           round(bunker.EXPLORE_BUTTON.centery * game.crt.win_h / 270))
    game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
    assert game.current_state_name == config.STATE_BUNKER_HUB


def test_completed_explore_button_obeys_failed_save_guard(game, monkeypatch):
    from video_game.engine.save_game import SaveError
    setup_stage(game, 'complete')
    before = copy.deepcopy(game.campaign.to_dict())
    def fail(*args, **kwargs):
        raise SaveError('fixture failure')
    monkeypatch.setattr(game.save_store, 'save', fail)
    button = game.current_scene.EXPLORE_BUTTON
    pos = (round(button.centerx * game.crt.win_w / 480),
           round(button.centery * game.crt.win_h / 270))
    game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
    assert game.current_state_name == config.STATE_BUNKER_HUB
    assert game.save_notice.startswith('SAVE FAILED')
    assert game.campaign.to_dict() == before
