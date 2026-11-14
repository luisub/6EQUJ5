"""PURPOSE: Check warned, jumpable, context-bound local moving hazards.
CALLED BY: pytest tests/test_world_hazards.py.
HOW TO MODIFY: Preserve mapped jump, safe delay, collision, pause and missing-art cases.
"""
from pathlib import Path
from types import SimpleNamespace

from PIL import Image, ImageDraw
import pygame
import pytest

from video_game.engine.config import ASSETS_DIR
from video_game.engine.input import InputManager
from video_game.engine.player import Player, PlayerInput
from video_game.engine.world import Camera, Room
from video_game.engine.world_hazards import (ARCHAEOLOGICAL_EFFIGY_ROOMS, MODERN_WAGON_ACTS,
                                             MODERN_WAGON_ROOMS, WorldHazards)
from video_game.tools.build_planet_threat import build


@pytest.fixture
def display(monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER','dummy')
    pygame.init(); pygame.display.set_mode((1,1))
    yield
    pygame.quit()


@pytest.fixture
def source(tmp_path, display):
    root=tmp_path/'assets';root.mkdir();file=tmp_path/'body.png'
    image=Image.new('RGBA',(96,72),(0,0,0,0))
    ImageDraw.Draw(image).rectangle((12,10,83,63),fill=(230,180,140,253));image.save(file)
    build('carrier_wraith',file,{'source':'test fixture'},assets_dir=root,promote=True)
    return root


def config(kind='planet_charge', art_id='carrier_wraith'):
    return {'kind':kind,'art_id':art_id,'damage':12,'speed':100,
            'warning_seconds':1.25,'cooldown_seconds':7.0,'initial_delay':8.0}


def flat_room(room_id='alien_001_field'):
    grid=[[0]*240 for _ in range(18)]
    for row in range(15,18):grid[row]=[1]*240
    return Room({'schema_version':1,'room_id':room_id,'act_id':'act_05','title':'fixture',
                 'tile_size':16,'width_tiles':240,'height_tiles':18,'collision_layers':grid,
                 'background_layers':[],'spawns':{'default':{'x':200,'y':208,'facing':'right'}},
                 'checkpoints':[],'exits':[],'objects':[]})


def step(hazard,player,camera,count,dt=1/60,**flags):
    for _ in range(count):hazard.update(dt,player,camera,**flags)


def test_telegraph_full_warning_offscreen_entry_and_one_hit(source):
    room=flat_room();camera=Camera();camera.set_world_bounds(3840,288)
    player=Player(200,208);player.is_grounded=True
    hazard=WorldHazards(source,room,config())
    assert hazard.enabled and hazard.hit_bounds.height <= 35
    step(hazard,player,camera,480)
    assert hazard.phase=='warning' and hazard.timer==pytest.approx(1.25)
    step(hazard,player,camera,74)
    assert hazard.phase=='warning' and hazard.timer>0
    step(hazard,player,camera,1)
    assert hazard.phase=='active' and hazard._body(hazard.x).left > camera.rect.right
    old_health=player.health
    step(hazard,player,camera,240)
    assert player.health < old_health and hazard.hit_this_pass
    health=player.health
    step(hazard,player,camera,5)
    assert player.health == health  # one contact per pass even after invulnerability changes


def test_mapped_jump_dodges_real_collision_while_standing_player_is_hit(source):
    room=flat_room();camera=Camera();camera.set_world_bounds(3840,288)
    def trial(jump):
        p=Player(200,208);p.is_grounded=True;h=WorldHazards(source,room,config())
        keys=InputManager();did_jump=False;lowest_bottom=240
        for _ in range(1100):
            if jump and h.phase=='active' and not did_jump:
                gap=h._body(h.x).left-p.rect.right
                if gap < 34:
                    keys.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_SPACE))
                    keys.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_d))
                    did_jump=True
            p.update(1/60,PlayerInput.from_input_manager(keys),room)
            h.update(1/60,p,camera)
            keys.begin_frame();lowest_bottom=min(lowest_bottom,p.rect.bottom)
            if h.phase=='cooldown':break
        return p.health,did_jump,lowest_bottom
    standing,_,_=trial(False)
    jumped,did_jump,lowest=trial(True)
    assert standing < 100
    assert did_jump and lowest <= 205 and jumped == 100


def test_frame_rate_motion_is_independent_and_block_pause_reset_are_safe(source):
    room=flat_room();camera=Camera();camera.set_world_bounds(3840,288)
    p=Player(30,208);p.is_grounded=True
    a=WorldHazards(source,room,config());b=WorldHazards(source,room,config())
    step(a,p,camera,600,dt=1/60);step(b,p,camera,300,dt=1/30)
    assert a.phase == b.phase == 'active' and a.x==pytest.approx(b.x,abs=.01)
    x=a.x;a.update(.1,p,camera,paused=True);assert a.x==x
    a.update(.1,p,camera,blocking=True)
    assert a.phase=='delay' and a.timer==pytest.approx(8)
    a.update(.1,p,camera,alive=False);assert a.phase=='delay' and a.timer==pytest.approx(8)
    a.reset();assert a.phase=='delay' and not a.hit_this_pass


def test_safety_context_missing_art_and_ineligible_rooms_disable_hazard(source,display):
    assert not WorldHazards(source,flat_room(),config(art_id='shard_clipper')).enabled
    assert not WorldHazards(source,flat_room('alien_003_field'),config()).enabled
    assert not WorldHazards(source,flat_room('alien_001_arena'),config()).enabled
    assert not WorldHazards(source,flat_room(),config(art_id='not_installed')).enabled
    invalid=config();invalid['warning_seconds']=.5
    assert not WorldHazards(source,flat_room(),invalid).enabled
    wagon=config('earth_wagon','ohio_wagon')
    for room_id in ('act_05_pillar_approach','act_05_buried_archive','alien_001_field','act_03_s4_hangar'):
        assert not WorldHazards(ASSETS_DIR,flat_room(room_id),wagon).enabled
    for room_id in MODERN_WAGON_ROOMS:
        room=flat_room(room_id);room.act_id=MODERN_WAGON_ACTS[room_id]
        assert WorldHazards(ASSETS_DIR,room,wagon).enabled
        room.act_id='act_05'
        assert not WorldHazards(ASSETS_DIR,room,wagon).enabled


def test_cached_warning_and_sprite_draw_without_image_io(source,monkeypatch):
    room=flat_room();camera=Camera();camera.set_world_bounds(3840,288)
    p=Player(200,208);h=WorldHazards(source,room,config())
    class CRT:
        def __init__(self):self.canvas=pygame.Surface((480,270));self.text=[];self.images=[]
        def draw_text(self,*args,**kwargs):self.text.append(args)
        def composite_native(self,*args):self.images.append(args)
    crt=CRT();monkeypatch.setattr(pygame.image,'load',lambda *_a,**_kw:pytest.fail('render performed image IO'))
    step(h,p,camera,480);h.render(crt,camera);assert crt.text and crt.text[0][0]=='INCOMING'
    step(h,p,camera,75);h.render(crt,camera);assert len(crt.images)==1


def test_missing_correct_world_art_never_creates_invisible_hazard(tmp_path, display):
    root=tmp_path/'assets';root.mkdir();room=flat_room();camera=Camera();camera.set_world_bounds(3840,288)
    player=Player(200,208);hazard=WorldHazards(root,room,config())
    assert not hazard.enabled and hazard.image is None
    step(hazard,player,camera,1200)
    assert player.health==100 and hazard.phase=='disabled'


def test_offscreen_player_cannot_be_damaged_by_a_hidden_pass(source):
    room=flat_room();camera=Camera();camera.set_world_bounds(3840,288)
    player=Player(600,208);player.is_grounded=True;hazard=WorldHazards(source,room,config())
    # A queued object moving entirely outside the viewport cannot hit an offscreen player.
    hazard.phase='active';hazard.x=600
    step(hazard,player,camera,20)
    assert player.health==100 and not hazard.hit_this_pass


def test_real_hostile_damage_respects_assisted_and_existing_invulnerability(source):
    room=flat_room();camera=Camera();camera.set_world_bounds(3840,288)
    p=Player(200,208);p.is_grounded=True;p.combat_assisted=True
    hazard=WorldHazards(source,room,config());hazard.phase='active'
    hazard.x=p.rect.right-hazard.contact_bounds.left
    hazard.update(1/60,p,camera)
    assert p.health == 95
    assert p.invulnerable_timer>0
    next_hazard=WorldHazards(source,room,config());next_hazard.phase='active'
    next_hazard.x=p.rect.right-next_hazard.contact_bounds.left
    health=p.health;next_hazard.update(1/60,p,camera)
    assert p.health==health


def test_contact_core_stays_inside_full_visible_art_and_has_bounded_size(source):
    hazard=WorldHazards(source,flat_room(),config())
    assert hazard.hit_bounds.contains(hazard.contact_bounds)
    assert hazard.contact_bounds.width <= 16 and hazard.contact_bounds.height <= 18
    assert hazard.contact_bounds.bottom == hazard.hit_bounds.bottom
    assert abs(hazard.contact_bounds.centerx - hazard.hit_bounds.centerx) <= 1
    assert hazard.hit_bounds.width > hazard.contact_bounds.width


@pytest.mark.parametrize('name,path,scene_options', [
    ('carrier','alien_worlds/alien_001_field.json',{'campaign_route':True,'journey_world':'alien_001'}),
    ('stone','act_05/pillar_approach.json',{}),
    ('wagon','act_01/perimeter_road.json',{}),
])
@pytest.mark.parametrize('moving', [False,True], ids=['stationary','moving-right'])
@pytest.mark.parametrize('reaction_frames', [0,6,12], ids=['0s','0.1s','0.2s'])
def test_field_first_actionable_cue_dodges_with_normal_mapped_hold(tmp_path,display,name,path,scene_options,moving,reaction_frames):
    """Use actual input and field collision; no artificial cue or player movement."""
    from video_game.engine import config as game_config
    from video_game.engine.crt_renderer import CRTRenderer
    from video_game.engine.save_game import SaveStore
    from video_game.engine.settings import SettingsStore
    from video_game.engine.state_machine import GameStateMachine

    machine=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(tmp_path/'save'),
                             settings_store=SettingsStore(tmp_path/'settings'))
    try:
        assert machine.change_settings(scale=1,combat_mode='assisted',crt_effects=False)
        assert machine.start_new_game()[0]
        machine.change_state(game_config.STATE_FIELD_OPS,room=path,spawn='default',**scene_options)
        scene=machine.current_scene;scene.forward_encounter=None;scene.enemy_manager.clear()
        x=64 if moving else min(1000, scene.room.width_px // 2)
        scene.player.x=float(x);scene.player.y=208.;scene.player.rect.topleft=(x,208)
        scene.player.vx=scene.player.vy=0;scene.camera.snap_to(x+8,224)
        hazard=scene.world_hazards
        assert hazard and hazard.enabled, name
        # Isolate the full warning/reaction window from the entry delay. Short
        # Earth rooms can now be crossed before that eight-second delay ends.
        hazard.phase='warning'
        hazard.timer=hazard.warning_seconds
        if moving:machine.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RIGHT))
        cue_frame=None;press_frame=None;warning_frames=0
        for frame in range(1100):
            if moving and scene.player.x >= scene.room.width_px - 128:
                machine.handle_event(pygame.event.Event(pygame.KEYUP,key=pygame.K_RIGHT))
            if hazard.phase=='warning':
                warning_frames+=1
                assert not hazard.action_cue
            if hazard.action_cue and cue_frame is None:
                cue_frame=frame
            if cue_frame is not None and press_frame is None and frame>=cue_frame+reaction_frames:
                machine.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_SPACE))
                press_frame=frame
            machine.update(1/60);machine.input.begin_frame()
            assert scene.player.health==100, (name,moving,reaction_frames,frame,cue_frame,press_frame)
            if hazard.phase=='cooldown':break
        assert warning_frames>=75
        assert cue_frame is not None and press_frame==cue_frame+reaction_frames
        assert hazard.phase=='cooldown'
    finally:
        machine.close()


def test_no_actionable_cue_while_retreating_airborne_paused_or_after_hit(source):
    room=flat_room();camera=Camera();camera.set_world_bounds(3840,288)
    player=Player(200,208);player.is_grounded=True
    h=WorldHazards(source,room,config());h.phase='active'
    h.x=player.rect.right-h.contact_bounds.left+30
    player.vx=-140;h.update(1/60,player,camera);assert not h.action_cue
    player.vx=0;player.is_grounded=False;h.update(1/60,player,camera);assert not h.action_cue
    player.is_grounded=True;h.update(1/60,player,camera,paused=True);assert not h.action_cue
    h.hit_this_pass=True;h.update(1/60,player,camera);assert not h.action_cue


def test_action_cue_is_hidden_when_too_late_or_pause_overlay_is_active(source):
    room=flat_room();camera=Camera();camera.set_world_bounds(3840,288)
    player=Player(200,208);player.is_grounded=True
    h=WorldHazards(source,room,config());h.phase='active'
    h.x=player.rect.right-h.contact_bounds.left+3
    h.update(1/60,player,camera)
    assert not h.action_cue  # Too close for even an immediate jump.
    class CRT:
        def __init__(self):self.canvas=pygame.Surface((480,270));self.text=[]
        def draw_text(self,*args,**kwargs):self.text.append(args)
        def composite_native(self,*args):pass
    player.combat_context=SimpleNamespace(machine=SimpleNamespace(pause=SimpleNamespace(active=False)),
                                          route_story=None,reality=SimpleNamespace(panel_open=False))
    h.action_cue=True;h._cue_player=player
    crt=CRT();h.render(crt,camera);assert crt.text[0][0]=='HOLD JUMP'
    _, cue_x, cue_y = crt.text[0]
    center=(player.rect.centerx+h._contact_body(h.x).centerx)/2
    assert abs(cue_x+55//2-center) <= 1
    assert 4 <= cue_x <= camera.viewport_w-59 and cue_y+16 <= player.rect.top
    player.combat_context.machine.pause.active=True
    crt=CRT();h.render(crt,camera);assert not crt.text


def test_crowding_delays_new_pass_but_preserves_visible_active_motion(source):
    room=flat_room();camera=Camera();camera.set_world_bounds(3840,288)
    player=Player(200,208);player.is_grounded=True;hazard=WorldHazards(source,room,config())
    step(hazard,player,camera,600,crowded=True)
    assert hazard.phase=='delay' and hazard.timer==pytest.approx(8)
    step(hazard,player,camera,480)
    assert hazard.phase=='warning'
    hazard.update(1/60,player,camera,crowded=True)
    assert hazard.phase=='cooldown' and hazard.timer==pytest.approx(7)
    step(hazard,player,camera,420)
    assert hazard.phase=='warning'
    step(hazard,player,camera,75)
    assert hazard.phase=='active'
    x=hazard.x
    hazard.update(1/60,player,camera,crowded=True)
    assert hazard.phase=='active' and hazard.x < x


def test_planet_image_and_asymmetric_collision_bounds_mirror_for_leftward_pass(tmp_path, display):
    root=tmp_path/'assets';root.mkdir();file=tmp_path/'asymmetric.png'
    image=Image.new('RGBA',(96,72),(0,0,0,0))
    ImageDraw.Draw(image).rectangle((8,12,59,63),fill=(250,200,90,253))
    image.save(file)
    build('carrier_wraith',file,{'source':'asymmetric fixture'},assets_dir=root,promote=True)
    hazard=WorldHazards(root,flat_room(),config())
    source=pygame.image.load(str(file)).convert_alpha()
    expected=pygame.transform.scale(pygame.transform.flip(source,True,False),(120,90))
    assert pygame.image.tobytes(hazard.image,'RGBA')==pygame.image.tobytes(expected,'RGBA')
    # Exclusive source bounds x=[8,60) become x=[36,88); at 0.625 logical scale.
    assert hazard.hit_bounds.left==22 and hazard.hit_bounds.right==55
    assert hazard.hit_bounds.top==7 and hazard.hit_bounds.bottom==40


def test_wagon_remains_in_original_left_facing_orientation(display):
    room=flat_room('act_01_perimeter_road');room.act_id='act_01'
    hazard=WorldHazards(ASSETS_DIR,room,config('earth_wagon','ohio_wagon'))
    source=pygame.image.load(str(ASSETS_DIR/'environments/ohio/salvage_yard/wagon.png')).convert_alpha()
    expected=pygame.transform.scale(source,(144,66))
    assert pygame.image.tobytes(hazard.image,'RGBA')==pygame.image.tobytes(expected,'RGBA')


def test_stone_effigy_only_in_archaeological_fields_without_car_fallback(source, tmp_path):
    source_body = tmp_path / 'body.png'
    assert source_body.is_file()
    build('resonance_effigy',source_body,{'source':'test'},assets_dir=source,promote=True)
    stone=config('stone_effigy','resonance_effigy')
    for room_id in ARCHAEOLOGICAL_EFFIGY_ROOMS:
        h=WorldHazards(source,flat_room(room_id),stone)
        assert h.enabled and h.kind=='stone_effigy' and h.hit_bounds.height<=35
    for room_id in ('act_05_core_prime_arena','earth_finale_core_prime_arena',
                    'act_02_blackout_street','alien_010_field'):
        assert not WorldHazards(source,flat_room(room_id),stone).enabled
    wrong_act=flat_room('act_05_pillar_approach');wrong_act.act_id='act_02'
    assert not WorldHazards(source,wrong_act,stone).enabled
    empty=tmp_path/'empty-assets';empty.mkdir()
    assert not WorldHazards(empty,flat_room('act_05_pillar_approach'),stone).enabled
    assert not WorldHazards(source,flat_room('act_05_pillar_approach'),config('earth_wagon','ohio_wagon')).enabled
