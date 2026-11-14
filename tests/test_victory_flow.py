"""Victory pacing, durable handoffs and readable dialogue, using isolated saves."""
import pygame
import pytest

from video_game.engine import config
from video_game.engine.alien_journey import journey_data, ledger, save_ledger
from video_game.engine.galaxy_transit import leg_position, leg_points, map_points, route_ids
from video_game.engine.save_game import SaveError
from video_game.engine.ui.dialogue import paginate
from video_game.engine.ui.text import wrap_text_pixels
from .test_campaign_world_route import game, key
from .test_alien_journey_runtime import enter_first_guardian


def test_guardian_destruction_waits_for_reading_and_survives_continue(game):
    world, scene = enter_first_guardian(game, acknowledge=False)
    assert ledger(game.campaign)['stage'] == 'guardian'
    assert scene.destruction and not scene.destruction.done
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, repeat=True))
    assert scene.story.index == 0 and game.current_scene is scene
    game.open_pause()
    elapsed = scene.destruction.elapsed
    game.update(30)
    assert scene.destruction.elapsed == elapsed
    game.pause.active = False
    game.update(30)
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, repeat=True))
    game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(10, 10)))
    assert scene.destruction.done and scene.story.index == 0
    assert ledger(game.campaign)['receipts'] == []
    assert game.continue_game().status == 'ok'
    key(game, pygame.K_RETURN)
    resumed = game.current_scene
    assert resumed.is_defeated_sequence and resumed.destruction is None
    key(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_ALIEN_CONTACT
    contact = game.current_scene
    game.update(90)
    assert contact.page == 0 and ledger(game.campaign)['receipts'] == []
    for _ in contact.pages:
        key(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_GALAXY_TRANSIT
    assert game.current_scene.pending == {'source': world['id'], 'destination': world['next_world']}
    assert ledger(game.campaign)['receipts'] == [world['civ_id']]


def test_victory_acknowledgement_rolls_back_failed_save(game, monkeypatch):
    world, scene = enter_first_guardian(game, acknowledge=False)
    game.update(3)
    original = game.save_store.save
    def fail(*args, **kwargs):
        raise SaveError('acknowledgement fixture')
    monkeypatch.setattr(game.save_store, 'save', fail)
    key(game, pygame.K_RETURN)
    assert scene.story_save_pending and game.current_scene is scene
    assert ledger(game.campaign)['stage'] == 'guardian'
    before = game.campaign.to_dict()
    key(game, pygame.K_RETURN)
    assert game.campaign.to_dict() == before
    game.render()  # The final page and retry button must remain visible.
    monkeypatch.setattr(game.save_store, 'save', original)
    key(game, pygame.K_F5)
    assert game.current_state_name == config.STATE_ALIEN_CONTACT
    assert ledger(game.campaign)['stage'] == 'contact'
    assert ledger(game.campaign)['receipts'] == []
    assert game.save_store.load().campaign.state.room_flags[world['defeat_flag']]


@pytest.mark.parametrize('index', range(11))
def test_every_guardian_requires_victory_then_message_before_travel(game, index):
    # Prior victories and lethal damage are fixtures, not a full playthrough.
    worlds = journey_data()['worlds']
    game.campaign.apply_event({'event_id':'fixture_portal', 'type':'defeat_portal_warden'})
    for i, prior in enumerate(worlds[:index]):
        game.campaign.apply_event({'event_id': f'fixture_{i}', 'type': prior['defeat_event']})
    world = worlds[index]
    save_ledger(game.campaign, {'version':1, 'world_id':world['id'], 'stage':'guardian',
                               'checkpoint':None, 'receipts':[w['civ_id'] for w in worlds[:index]]})
    game.change_state(config.STATE_BOSS_BOUNTY, room=world['arena_room'],
                      boss_id=world['boss_id'], journey_world=world['id'])
    game.update(1.6)
    scene = game.current_scene
    scene.boss.take_damage(10000, hit_pos=scene.boss.rect.center)
    game.update(1/60)
    assert scene.is_defeated_sequence and scene.destruction.shards
    game.update(20)
    assert game.current_scene is scene and ledger(game.campaign)['stage'] == 'guardian'
    key(game, pygame.K_RETURN)
    contact = game.current_scene
    assert game.current_state_name == config.STATE_ALIEN_CONTACT
    for _ in contact.pages:
        key(game, pygame.K_RETURN)
    assert ledger(game.campaign)['receipts'] == [w['civ_id'] for w in worlds[:index + 1]]
    assert game.current_scene.pending == {'source': world['id'], 'destination': world['next_world'] or 'earth'}


def test_portal_warden_does_not_inherit_greenkeeper_victory(game):
    game.campaign.apply_event({'event_id':'fixture_greenkeeper','type':'defeat_greenkeeper'})
    game.change_state(config.STATE_BOSS_BOUNTY, room='act_05/core_prime_arena.json', boss_id='portal_warden')
    assert not game.current_scene.is_defeated_sequence
    assert not game.current_scene.boss.is_defeated


def test_route_marker_follows_drawn_path_without_teleporting():
    area = (32, 68, 416, 132)
    points = map_points(area)
    route = route_ids()
    assert route[0] == route[-1] == 'earth'
    for source, destination in zip(route, route[1:]):
        path = leg_points(source, destination, area)
        assert path[0] == points[source] and path[-1] == points[destination]
        for i, point in enumerate(path):
            assert leg_position(source, destination, area, i / 24) == pytest.approx(point)
        # Nodes are adjacent on the itinerary, not arbitrary jumps across the map.
        assert all(pygame.Vector2(a).distance_to(b) < 5 for a, b in zip(path, path[1:]))


def test_dialogue_pagination_keeps_every_word_inside_the_panel(game):
    text = ' '.join(f'message{i}' for i in range(140))
    pages = paginate([{'title':'Recovered message', 'text':text}], game.crt.font_md, width=274)
    assert len(pages) > 1
    assert ' '.join(p['text'] for p in pages).split() == text.split()
    for page in pages:
        lines = wrap_text_pixels(page['text'], game.crt.font_md, 274)
        assert len(lines) <= 6
        assert all(game.crt.font_md.size(line)[0] <= 274 for line in lines)
