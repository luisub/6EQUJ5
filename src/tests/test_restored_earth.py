"""Earned liberation, recoverable dialogue and peaceful park controls."""
from copy import deepcopy

import pygame
from video_game.engine import config
from video_game.engine.alien_journey import dispatch, journey_data, ledger, save_ledger
from video_game.engine.audio import TRACK_RESTORED
from video_game.engine.campaign_scenery import load_campaign_background, load_campaign_boss
from video_game.engine.save_game import SaveError
from video_game.engine.scenes.restored_earth import load_families, NEXT
from .test_campaign_world_route import game, key


def completed_fixture(game):
    """Disclosed final-progress fixture; the routed fight is tested separately."""
    worlds = journey_data()['worlds']
    game.campaign.apply_event({'event_id': 'park_portal', 'type': 'defeat_portal_warden'})
    for world in worlds:
        game.campaign.apply_event({'event_id': 'park_' + world['id'], 'type': world['defeat_event']})
    game.campaign.apply_event({'event_id': 'park_final', 'type': 'defeat_earth_ai'})
    save_ledger(game.campaign, {'version': 1, 'world_id': None, 'stage': 'complete',
                              'checkpoint': None, 'receipts': [w['civ_id'] for w in worlds]})
    assert game.save_checkpoint()
    assert dispatch(game)
    return game.current_scene


def test_park_rejects_unearned_or_incomplete_progress(game):
    game.change_state(config.STATE_RESTORED_EARTH)
    assert game.current_state_name == config.STATE_BUNKER_HUB
    game.campaign.apply_event({'event_id': 'incomplete_park', 'type': 'defeat_earth_ai'})
    save_ledger(game.campaign, {'version': 1, 'world_id': None, 'stage': 'complete', 'receipts': []})
    game.change_state(config.STATE_RESTORED_EARTH)
    assert game.current_state_name == config.STATE_BUNKER_HUB


def test_park_pages_wait_and_continue_recovers_acknowledged_page(game):
    scene = completed_fixture(game)
    game.update(30)
    assert scene.page == 0
    key(game, pygame.K_RETURN)
    assert scene.page == 1 and ledger(game.campaign)['restoration_page'] == 1
    assert game.continue_game().status == 'ok'
    assert game.current_state_name == config.STATE_BUNKER_HUB
    key(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_RESTORED_EARTH
    assert game.current_scene.page == 1
    for _ in game.current_scene.pages[1:]:
        key(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_RESTORED_EARTH
    assert game.save_store.load().campaign.state.world_states['bunker_hub']['alien_journey']['stage'] == 'complete'


def test_failed_park_page_save_rolls_back_and_retries(game, monkeypatch):
    scene = completed_fixture(game)
    prior = deepcopy(ledger(game.campaign))
    save = game.save_store.save
    def fail(*args, **kwargs):
        raise SaveError('park fixture failure')
    monkeypatch.setattr(game.save_store, 'save', fail)
    key(game, pygame.K_RETURN)
    assert scene.page == 0 and scene.save_pending
    assert ledger(game.campaign) == prior
    monkeypatch.setattr(game.save_store, 'save', save)
    key(game, pygame.K_RETURN)
    assert scene.page == 1 and not scene.save_pending


def test_final_completion_save_failure_keeps_ending_recoverable(game, monkeypatch):
    completed_fixture(game)
    progress = dict(ledger(game.campaign), stage='final')
    save_ledger(game.campaign, progress)
    assert game.save_checkpoint()
    assert dispatch(game)
    finale = game.current_scene
    assert finale.journey_final and finale.is_defeated_sequence
    save = game.save_store.save

    def fail(*args, **kwargs):
        raise SaveError('final completion fixture failure')

    monkeypatch.setattr(game.save_store, 'save', fail)
    for _ in finale.story.pages:
        key(game, pygame.K_RETURN)
    assert game.current_scene is finale and finale.story_save_pending
    assert ledger(game.campaign)['stage'] == 'final'
    assert game.save_store.load().campaign.state.world_states['bunker_hub']['alien_journey']['stage'] == 'final'
    monkeypatch.setattr(game.save_store, 'save', save)
    key(game, pygame.K_RETURN)
    assert game.current_state_name == config.STATE_RESTORED_EARTH
    assert ledger(game.campaign)['stage'] == 'complete'


def test_walk_pause_focus_and_fresh_game_do_not_leak_input(game):
    scene = completed_fixture(game)
    start = scene.hero_x
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
    for _ in range(20):
        game.update(1/60)
    assert scene.hero_x > start and scene.animator.current_state == 'walk'
    assert scene.animator.current_frame_index > 0
    game.open_pause()
    snapshot = (scene.elapsed, scene.hero_x, scene.animator.time_accumulated)
    game.update(2)
    assert (scene.elapsed, scene.hero_x, scene.animator.time_accumulated) == snapshot
    game.pause.close()
    game.update(.1)
    assert scene.hero_x == snapshot[1] and scene.animator.current_state == 'idle'
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
    game.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
    game.pause.close()
    game.update(.1)
    assert scene.hero_x == snapshot[1]
    assert game.start_new_game(replace_existing=True)[0]
    assert not ledger(game.campaign)
    assert not game.campaign.state.room_flags.get('earth_ai_defeated')
    assert game.scenes[config.STATE_RESTORED_EARTH] is not scene


def test_controller_mouse_and_repeat_reading_controls(game):
    scene = completed_fixture(game)
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, repeat=True))
    assert scene.page == 0
    game.input._controller_state[42] = {'buttons': set(), 'axes': {}}
    game.handle_event(pygame.event.Event(pygame.CONTROLLERBUTTONDOWN, button=pygame.CONTROLLER_BUTTON_A, instance_id=42))
    game.handle_event(pygame.event.Event(pygame.CONTROLLERBUTTONUP, button=pygame.CONTROLLER_BUTTON_A, instance_id=42))
    assert scene.page == 1
    game.change_settings(scale=1)
    game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                        pos=(NEXT.centerx * 2, NEXT.centery * 2)))
    assert scene.page == 2
    x = scene.hero_x
    game.handle_event(pygame.event.Event(pygame.CONTROLLERBUTTONDOWN, button=pygame.CONTROLLER_BUTTON_DPAD_LEFT, instance_id=42))
    game.update(.1)
    game.handle_event(pygame.event.Event(pygame.CONTROLLERBUTTONUP, button=pygame.CONTROLLER_BUTTON_DPAD_LEFT, instance_id=42))
    assert scene.hero_x < x


def test_missing_optional_park_art_still_renders(game):
    scene = completed_fixture(game)
    scene.background = None
    scene.families = scene.families_left = ()
    game.update(.1)
    game.render()
    assert game.crt.render_surface.get_at((500, 350))[:3] != (0, 0, 0)


def test_finale_art_and_park_music_load_from_runtime_assets(game):
    root = game.assets.root
    for name in ('core_network', 'denver_restored'):
        background = load_campaign_background(root, name)
        assert background is not None and background.get_size() == (1920, 540)
    body = load_campaign_boss(root, 'earth_core_ai', allow_fallback=False)
    assert body is not None and body.get_size() == (256, 192)
    frames = load_families(root)
    assert len(frames) == 4
    assert len({pygame.image.tobytes(frame, 'RGBA') for frame in frames}) == 4
    for frame in frames:
        bounds = frame.get_bounding_rect(min_alpha=32)
        assert 86 <= bounds.bottom <= 90
    game.audio.stop_all()
    game.audio.enabled = False
    completed_fixture(game)
    assert game.audio.current_track == TRACK_RESTORED
