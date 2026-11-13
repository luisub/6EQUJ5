"""PURPOSE: Verify the new-game opening through the real title and input router.
CALLED BY: pytest.
HOW TO MODIFY: Keep normal input, temporary saves and release isolation under test.
"""
from copy import deepcopy
import json

import pygame
import pytest

from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.opening_story import OpeningStory, load_opening_pages
from video_game.engine.save_game import SaveError, SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.ui.text import wrap_text_pixels


@pytest.fixture
def game(tmp_path, monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER', 'dummy')
    monkeypatch.setenv('SDL_AUDIODRIVER', 'dummy')
    pygame.init(); pygame.display.set_mode((960,540))
    m=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(tmp_path/'save'),
                       settings_store=SettingsStore(tmp_path/'settings'))
    assert m.change_settings(scale=1,crt_effects=False)
    yield m
    m.close();pygame.quit()


def key(game, code, down=True, **attrs):
    game.handle_event(pygame.event.Event(pygame.KEYDOWN if down else pygame.KEYUP,key=code,**attrs))


def controller(game, button, down=True):
    game.handle_event(pygame.event.Event(pygame.CONTROLLERBUTTONDOWN if down else pygame.CONTROLLERBUTTONUP,
                                         button=button,instance_id=37))


def click(game, logical, down=True):
    x,y=logical
    game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN if down else pygame.MOUSEBUTTONUP,
                                         button=1,pos=(round(x*2),round(y*2))))


def title_start(game):
    assert game.current_state_name == config.STATE_TITLE_BOOT
    key(game,pygame.K_RETURN)
    assert game.current_state_name == config.STATE_BUNKER_HUB
    assert game.current_scene.opening_story is not None


def test_authored_pages_are_bounded_readable_and_fallback_is_safe(game,tmp_path):
    pages=load_opening_pages()
    assert len(pages)==4 and '6EQUJ5' in pages[1]['text']
    assert all(len(wrap_text_pixels(page['text'],game.crt.font_md,390)) <= 6 for page in pages)
    assert all(44 + game.crt.font_md.size(page['title'])[0] + 8 < 440 - game.crt.font_sm.size('3/3')[0]
               for page in pages)
    assert load_opening_pages(tmp_path/'missing.json') == []
    invalid=tmp_path/'bad.json';invalid.write_text(json.dumps({'schema_version':1,'pages':[{'title':'x','text':''}]}))
    assert load_opening_pages(invalid) == []


def test_normal_title_start_does_not_skip_and_timer_finishes_without_progress_mutation(game):
    title_start(game);scene=game.current_scene
    initial=deepcopy(game.campaign.state)
    key(game,pygame.K_RETURN,repeat=True)
    key(game,pygame.K_RETURN)  # Duplicate down cannot become a second action.
    assert scene.opening_story and scene.opening_story.index == 0
    game.update(13.9);assert scene.opening_story.index == 0
    game.update(.2);assert scene.opening_story.index == 1
    game.update(14.0);assert scene.opening_story.index == 2
    game.update(14.0);assert scene.opening_story.index == 3
    assert scene.opening_story.pages[3]['visual'] == 'galaxy_map'
    game.update(14.0);assert scene.opening_story is None
    assert game.current_state_name == config.STATE_BUNKER_HUB and game.campaign.state == initial
    # The original held Enter cannot leave even after the timer finishes.
    key(game,pygame.K_RETURN,repeat=True);assert game.current_state_name == config.STATE_BUNKER_HUB
    key(game,pygame.K_RETURN,down=False);key(game,pygame.K_RETURN)
    assert game.current_state_name == config.STATE_FIELD_OPS


@pytest.mark.parametrize('skip', [pygame.K_RETURN,pygame.K_KP_ENTER,pygame.K_SPACE,
                                  pygame.K_LEFT,pygame.K_RIGHT,pygame.K_UP,pygame.K_DOWN])
def test_one_fresh_key_skips_all_and_held_repeat_never_passes_through(game,skip):
    title_start(game)
    key(game,pygame.K_RETURN,down=False)
    scene=game.current_scene;x=scene.mateo_x
    key(game,skip)
    assert scene.opening_story is None and game.current_state_name == config.STATE_BUNKER_HUB
    key(game,skip,repeat=True);key(game,skip)
    game.update(.5)
    assert game.current_state_name == config.STATE_BUNKER_HUB and scene.mateo_x == x
    key(game,skip,down=False)
    key(game,pygame.K_RETURN)
    assert game.current_state_name == config.STATE_FIELD_OPS


@pytest.mark.parametrize('button', [pygame.CONTROLLER_BUTTON_A,pygame.CONTROLLER_BUTTON_DPAD_LEFT,
                                    pygame.CONTROLLER_BUTTON_DPAD_RIGHT,pygame.CONTROLLER_BUTTON_DPAD_UP,
                                    pygame.CONTROLLER_BUTTON_DPAD_DOWN])
def test_controller_a_or_any_dpad_skips_without_handoff(game,button):
    title_start(game);key(game,pygame.K_RETURN,down=False)
    game.input._controller_state[37] = {'buttons':set(),'axes':{}}
    scene=game.current_scene;x=scene.mateo_x
    controller(game,button);assert scene.opening_story is None
    controller(game,button);game.update(.5)
    assert game.current_state_name == config.STATE_BUNKER_HUB and scene.mateo_x == x
    controller(game,button,down=False)


def test_controller_start_press_must_release_before_it_can_skip(game):
    game.input._controller_state[37] = {'buttons':set(),'axes':{}}
    controller(game,pygame.CONTROLLER_BUTTON_A)
    assert game.current_scene.opening_story is not None
    controller(game,pygame.CONTROLLER_BUTTON_A)
    assert game.current_scene.opening_story is not None
    controller(game,pygame.CONTROLLER_BUTTON_A,down=False)
    controller(game,pygame.CONTROLLER_BUTTON_A)
    assert game.current_scene.opening_story is None and game.current_state_name == config.STATE_BUNKER_HUB


def test_held_controller_axis_waits_for_neutral_after_skip(game):
    title_start(game);key(game,pygame.K_RETURN,down=False)
    game.input._controller_state[37] = {'buttons':set(),'axes':{}}
    def axis(value):
        game.handle_event(pygame.event.Event(pygame.CONTROLLERAXISMOTION,instance_id=37,
                                             axis=pygame.CONTROLLER_AXIS_LEFTX,value=value))
    scene=game.current_scene;x=scene.mateo_x
    axis(32767)
    key(game,pygame.K_DOWN);assert scene.opening_story is None
    axis(32767);game.update(.5)
    assert scene.mateo_x == x
    axis(0);axis(32767);game.update(.5)
    assert scene.mateo_x > x


@pytest.mark.parametrize('kind', [pygame.CONTROLLERDEVICEREMOVED,pygame.CONTROLLERDEVICEREMAPPED])
def test_removed_or_remapped_controller_clears_only_its_opening_guards(game,kind):
    title_start(game);key(game,pygame.K_RETURN,down=False)
    for instance in (37,38):
        game.input._controller_state[instance]={'buttons':set(),'axes':{}}
        game.handle_event(pygame.event.Event(pygame.CONTROLLERAXISMOTION,instance_id=instance,
                                             axis=pygame.CONTROLLER_AXIS_LEFTX,value=32767))
    controller(game,pygame.CONTROLLER_BUTTON_A)
    scene=game.current_scene;assert scene.opening_story is None
    assert ('controller',37,pygame.CONTROLLER_BUTTON_A) in scene._opening_guarded
    game.handle_event(pygame.event.Event(kind,instance_id=37,which=37))
    assert all(not (token[0] in ('controller','axis') and token[1]==37) for token in scene._opening_guarded)
    assert ('axis',38,pygame.CONTROLLER_AXIS_LEFTX) in scene._opening_guarded


def test_mouse_arrow_skips_and_other_clicks_do_not_activate_stations(game):
    click(game,game.current_scene.PRIMARY.center)
    scene=game.current_scene;assert scene.opening_story is not None
    click(game,(140,100),down=False)
    click(game,(145,100));click(game,(145,100),down=False)
    assert scene.opening_story is not None and game.current_state_name == config.STATE_BUNKER_HUB
    click(game,OpeningStory.SKIP_BUTTON.center)
    assert scene.opening_story is None and game.current_state_name == config.STATE_BUNKER_HUB
    click(game,OpeningStory.SKIP_BUTTON.center,down=False)


def test_continue_and_later_bunker_return_do_not_replay(game):
    title_start(game);key(game,pygame.K_RETURN,down=False);key(game,pygame.K_RIGHT)
    key(game,pygame.K_RIGHT,down=False)
    game.change_state(config.STATE_TITLE_BOOT)
    key(game,pygame.K_RETURN)
    assert game.current_state_name == config.STATE_BUNKER_HUB and game.current_scene.opening_story is None
    game.change_state(config.STATE_FIELD_OPS)
    game.change_state(config.STATE_BUNKER_HUB)
    assert game.current_scene.opening_story is None


def test_existing_save_explicit_new_game_restarts_opening(game):
    assert game.start_new_game()[0]
    game.change_state(config.STATE_TITLE_BOOT)
    key(game,pygame.K_n);assert game.current_scene.confirm_new
    key(game,pygame.K_y)
    assert game.current_state_name == config.STATE_BUNKER_HUB and game.current_scene.opening_story is not None


def test_failed_new_game_save_does_not_open_story(game,monkeypatch):
    def fail(*args,**kwargs):raise SaveError('fixture failure')
    monkeypatch.setattr(game.save_store,'save',fail)
    key(game,pygame.K_RETURN)
    assert game.current_state_name == config.STATE_TITLE_BOOT and not game.session_active
    assert 'SAVE FAILED' in game.current_scene.status


def test_pause_and_focus_loss_freeze_opening_without_input_leak(game):
    title_start(game);key(game,pygame.K_RETURN,down=False)
    scene=game.current_scene;remaining=scene.opening_story.remaining
    key(game,pygame.K_F2);assert game.pause.active
    game.update(30);assert scene.opening_story.remaining == remaining
    key(game,pygame.K_F2);assert not game.pause.active
    game.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST));assert game.pause.active
    game.update(30);assert scene.opening_story.remaining == remaining
    key(game,pygame.K_F2);assert not game.pause.active
    key(game,pygame.K_UP);assert scene.opening_story is None
    key(game,pygame.K_UP,repeat=True);assert game.current_state_name == config.STATE_BUNKER_HUB


def test_crt_hotkey_and_controller_device_events_pass_through_without_skipping(game,monkeypatch):
    title_start(game);key(game,pygame.K_RETURN,down=False)
    story=game.current_scene.opening_story
    previous=game.settings.crt_effects
    key(game,pygame.K_F1)
    assert game.settings.crt_effects != previous and game.current_scene.opening_story is story
    seen=[]
    original=game.input.handle_event
    def observe(event):
        seen.append(event.type)
        original(event)
    monkeypatch.setattr(game.input,'handle_event',observe)
    for kind in (pygame.CONTROLLERDEVICEADDED,pygame.CONTROLLERDEVICEREMOVED,pygame.CONTROLLERDEVICEREMAPPED):
        game.handle_event(pygame.event.Event(kind,which=987654,instance_id=987654,device_index=0))
    assert seen == [pygame.CONTROLLERDEVICEADDED,pygame.CONTROLLERDEVICEREMOVED,pygame.CONTROLLERDEVICEREMAPPED]
    assert game.current_scene.opening_story is story


def test_starting_key_release_while_paused_allows_fresh_skip(game):
    title_start(game)
    key(game,pygame.K_F2);assert game.pause.active
    key(game,pygame.K_RETURN,down=False)  # Release is still consumed while paused.
    key(game,pygame.K_F2);assert not game.pause.active
    key(game,pygame.K_RETURN)
    assert game.current_scene.opening_story is None and game.current_state_name == config.STATE_BUNKER_HUB


def test_non_skip_key_held_through_skip_cannot_activate_station(game):
    title_start(game);key(game,pygame.K_RETURN,down=False)
    key(game,pygame.K_e)  # Other actions are blocked while the story is active.
    key(game,pygame.K_DOWN);assert game.current_scene.opening_story is None
    key(game,pygame.K_e,repeat=True);key(game,pygame.K_e)
    assert game.current_state_name == config.STATE_BUNKER_HUB
    key(game,pygame.K_e,down=False);key(game,pygame.K_e)
    assert game.current_state_name == config.STATE_CRT_TERMINAL
