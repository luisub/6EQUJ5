"""PURPOSE: Verify opt-in firing light composition without changing gameplay.
CALLED BY: pytest.
HOW TO MODIFY: Preserve real input timing, HUD order and unchanged disabled/other scenes.
"""
from copy import deepcopy
from dataclasses import asdict
from types import SimpleNamespace
import pygame
import pytest
from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.firing_lighting import FiringLighting, FADE_LEVELS, LIGHT_SIZE, AMBIENT_RGB, LAMP_POOLS
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.weapons import ProjectileManager


@pytest.fixture
def game(tmp_path):
    pygame.init()
    pygame.display.set_mode((960,540))
    machine=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(tmp_path/'save'),settings_store=SettingsStore(tmp_path/'save'))
    try:
        assert machine.change_settings(combat_mode='classic')  # Historical single-ray lighting contract.
        assert machine.start_new_game()[0]
        machine.change_state(config.STATE_FIELD_OPS,room='act_01/approach.json',spawn='approach_checkpoint')
        machine.current_scene.firing_lighting=None  # Explicit legacy control for these paired tests.
        machine.current_scene.maser_presentation=None  # Exercise this historical approach path independently.
        machine.current_scene.energy_filament=None  # Exercise fallback rather than the new tap visual.
        machine.current_scene.enemy_manager.clear()
        for _ in range(30):
            machine.input.begin_frame()
            machine.update(1/60)
        yield machine
    finally:
        machine.close()
        pygame.quit()


def burst():
    image=pygame.Surface((64,32),pygame.SRCALPHA)
    pygame.draw.circle(image,(255,245,230,255),(12,16),3)
    return image


def test_disabled_baseline_and_other_room_are_unchanged(game):
    scene=game.current_scene
    assert scene.firing_lighting is None
    game.render()
    before=pygame.image.tobytes(game.crt.render_surface,'RGBA')
    game.render()
    assert pygame.image.tobytes(game.crt.render_surface,'RGBA')==before
    lighting=FiringLighting(burst(),scene.native_approach.world)
    scene.load_room('act_01/salvage_yard.json',spawn_name='yard_entrance')
    game.render()
    legacy=pygame.image.tobytes(game.crt.render_surface,'RGBA')
    scene.firing_lighting=lighting
    game.render()
    assert pygame.image.tobytes(game.crt.render_surface,'RGBA')==legacy


def test_world_lamps_actor_alpha_and_finite_cache(game):
    world=pygame.Surface((1920,576),pygame.SRCALPHA)
    world.fill((255,255,255,255))
    light=FiringLighting(burst(), world)
    assert len(light.world_glows)==len(light.actor_glows)==FADE_LEVELS+1
    assert all(surface.get_size()==LIGHT_SIZE for surface in light.world_glows)
    scene=game.current_scene
    scene.camera.x=0
    scene.camera.y=0
    game.crt.clear((100,100,100))
    assert light.render_ambient(game.crt,scene.camera)
    output=game.crt.render_surface
    assert output.get_at((600,200))[:3]==(71,73,78)
    # Center of each authored world lamp pool is nearly original brightness.
    assert min(output.get_at((257,389))[:3])>=97
    assert min(output.get_at((288,490))[:3])>=97
    assert min(output.get_at((1104-480,510))[:3])<97  # second lamp remains off-screen at camera x=0
    scene.camera.x=240
    game.crt.clear((100,100,100))
    assert light.render_ambient(game.crt,scene.camera)
    assert min(game.crt.render_surface.get_at((1082-480,441))[:3])>=97
    scene.camera.x=0
    sprite=pygame.Surface((48,64),pygame.SRCALPHA)
    sprite.fill((20,30,40,0))
    pygame.draw.rect(sprite,(20,30,40,180),(10,10,20,30))
    f={'x':200,'y':200,'life':.04,'max_life':.08,'lighting_token':1,'is_charged':False}
    camera=scene.camera
    result=light.light_actor(sprite,(380,370),camera,[f])
    assert pygame.image.tobytes(result,'RGBA')[3::4]==pygame.image.tobytes(sprite,'RGBA')[3::4]
    assert pygame.image.tobytes(result,'RGB')!=pygame.image.tobytes(sprite,'RGB')


@pytest.mark.parametrize('x,y', [(0,0), (240,18), (480,18), (128.5,.5), (160.75,17.5)])
def test_cached_ambient_exactly_matches_per_frame_reference(game,x,y):
    scene=game.current_scene
    light=FiringLighting(burst(),scene.native_approach.world)
    crop=pygame.Rect(2*round(x),2*round(y),960,540)
    # Reference is the original per-frame composition, including clipping.
    expected=pygame.Surface((960,540)).convert()
    expected.fill(AMBIENT_RGB)
    recovery=pygame.Surface((960,540)).convert()
    recovery.fill((0,0,0))
    for (wx,wy,_,_),mask in zip(LAMP_POOLS,light.lamp_masks):
        recovery.blit(mask,(wx-crop.x,wy-crop.y),special_flags=pygame.BLEND_RGB_ADD)
    recovery.blit(light.material_mask,(0,0),area=crop,special_flags=pygame.BLEND_RGB_MULT)
    expected.blit(recovery,(0,0),special_flags=pygame.BLEND_RGB_ADD)
    assert pygame.image.tobytes(light.ambient_world.subsurface(crop),'RGB')==pygame.image.tobytes(expected,'RGB')
    scene.camera.x,scene.camera.y=x,y
    game.crt.clear((137,89,61))
    assert light.render_ambient(game.crt,scene.camera)
    reference=pygame.Surface((960,540),pygame.SRCALPHA).convert_alpha()
    reference.fill((137,89,61,255))
    reference.blit(expected,(0,0),special_flags=pygame.BLEND_RGB_MULT)
    assert pygame.image.tobytes(game.crt.render_surface,'RGBA')==pygame.image.tobytes(reference,'RGBA')


def test_actual_fire_origin_lifetime_and_hud_are_preserved(game):
    scene=game.current_scene
    scene.camera.x=240
    scene.camera.y=18
    baseline_campaign=deepcopy(game.campaign.to_dict())
    scene.firing_lighting=FiringLighting(burst(), scene.native_approach.world)
    spawns=[]
    original=scene.projectile_manager.spawn
    def record_spawn(*args,**kwargs):
        spawns.append((kwargs['x'],kwargs['y'],scene.player.animator.current_state))
        return original(*args,**kwargs)
    scene.projectile_manager.spawn=record_spawn
    expected=scene.player.get_muzzle_world_pos()
    game.input.begin_frame()
    game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_j))
    game.update(1/60)
    game.handle_event(pygame.event.Event(pygame.KEYUP,key=pygame.K_j))
    assert len(spawns)==1 and spawns[0][:2]==expected
    assert spawns[0][2]=='idle' and scene.player.animator.current_state=='recoil'
    flash=scene.effects.flashes[0]
    assert (flash['x'],flash['y'])==expected and flash['life']==pytest.approx(.08-1/60)
    assert scene.projectile_manager.projectiles[0].id in scene._firing_light_projectile_ids
    assert game.campaign.to_dict()==baseline_campaign
    game.render()
    lit=game.crt.render_surface.copy()
    scene.firing_lighting=None
    game.render()
    unlit=game.crt.render_surface.copy()
    objective=scene.objective_tracker.get_active_objective(game.campaign)
    goal_width=game.crt.font_sm.size(objective.title)[0]+15
    # These are the opaque logical HP and goal backgrounds at 2x density.
    for rect in ((10,8,210,24),(240,6,goal_width*2,28)):
        assert pygame.image.tobytes(lit.subsurface(rect),'RGBA') == pygame.image.tobytes(unlit.subsurface(rect),'RGBA')
    # The uncovered background remains visible and responds to lighting.
    exposed=(700,0,260,34)
    assert pygame.image.tobytes(lit.subsurface(exposed),'RGBA') != pygame.image.tobytes(unlit.subsurface(exposed),'RGBA')
    for _ in range(4):
        game.input.begin_frame()
        game.update(1/60)
    assert not scene.effects.flashes


def test_scene_token_blocks_old_or_charged_flashes(game):
    scene=game.current_scene
    light=FiringLighting(burst(), scene.native_approach.world)
    scene.firing_lighting=light
    token=scene._firing_light_token
    scene.effects.add_muzzle_flash(120,180,lighting_token=token)
    scene.effects.add_muzzle_flash(120,180,is_charged=True,lighting_token=token)
    assert len(light.active_flashes(scene.effects.flashes,token))==1
    scene.load_room('act_01/salvage_yard.json',spawn_name='yard_entrance')
    scene.load_room('act_01/approach.json',spawn_name='bunker_exit')
    assert not light.active_flashes(scene.effects.flashes,scene._firing_light_token)


def test_direct_reset_and_automatic_respawn_invalidate_old_lighting(game):
    scene=game.current_scene
    light=FiringLighting(burst(),scene.native_approach.world)
    scene.firing_lighting=light
    token=scene._firing_light_token
    scene.effects.add_muzzle_flash(120,180,lighting_token=token)
    assert light.active_flashes(scene.effects.flashes,token)
    scene.reset_to_spawn('approach_checkpoint')
    assert not light.active_flashes(scene.effects.flashes,scene._firing_light_token)
    token=scene._firing_light_token
    scene.effects.add_muzzle_flash(120,180,lighting_token=token)
    scene.player.is_dead=True
    game.input.begin_frame()
    game.update(1/60)
    assert scene._firing_light_token!=token
    assert not light.active_flashes(scene.effects.flashes,scene._firing_light_token)


def test_upward_starter_uses_rotated_burst_other_weapon_keeps_legacy(game):
    scene=game.current_scene
    scene.firing_lighting=FiringLighting(burst(),scene.native_approach.world)
    game.input.begin_frame()
    game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_UP))
    game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_j))
    game.update(1/60)
    assert scene.projectile_manager.projectiles[-1].dir_y < 0
    assert scene.effects.flashes[-1]['lighting_token'] == scene._firing_light_token
    assert scene.projectile_manager.projectiles[-1].id in scene._firing_light_projectile_ids
    game.render()
    assert any(key[1] == -90 for key in scene.firing_lighting.rotated_bursts)
    game.handle_event(pygame.event.Event(pygame.KEYUP,key=pygame.K_j))
    game.handle_event(pygame.event.Event(pygame.KEYUP,key=pygame.K_UP))
    scene.projectile_manager.clear()
    scene.effects.clear()
    scene.player.weapon=scene.player.arsenal.weapons['scattergun']
    scene.player.weapon.is_unlocked=True  # Explicit isolated weapon precondition.
    game.input.begin_frame()
    game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_j))
    game.update(1/60)
    assert scene.projectile_manager.projectiles[-1].weapon_type=='scattergun'
    assert scene.effects.flashes[-1]['lighting_token'] is None
    assert scene.projectile_manager.projectiles[-1].id not in scene._firing_light_projectile_ids
    assert not scene.firing_lighting.active_flashes(scene.effects.flashes,scene._firing_light_token)


def test_hazard_and_telegraph_stay_above_background_lighting(game,monkeypatch):
    scene=game.current_scene
    scene.camera.x=80
    scene.camera.y=18
    def telegraph(surface,camera, *, crt=None):
        pygame.draw.line(surface,(255,30,30),(100,180),(140,180),2)
    monkeypatch.setattr(scene.enemy_manager,'render',telegraph)
    game.render()
    baseline=game.crt.render_surface.copy()
    scene.firing_lighting=FiringLighting(burst(),scene.native_approach.world)
    scene.effects.add_muzzle_flash(330,220,lighting_token=scene._firing_light_token)
    game.render()
    lit=game.crt.render_surface
    # Compare actual opaque tile pixels, excluding transparent gaps which
    # intentionally reveal the dimmed backdrop behind the gameplay art.
    tile_layer=pygame.Surface((480,270),pygame.SRCALPHA)
    scene.room.render_tiles(tile_layer,scene.camera)
    native_tiles=pygame.transform.scale(tile_layer,(960,540))
    opaque_points=[(x,y) for x in range(480,608) for y in range(476,506)
                   if native_tiles.get_at((x,y)).a==255]
    assert opaque_points
    assert all(baseline.get_at(point)==lit.get_at(point) for point in opaque_points)
    assert lit.get_at((220,360))==baseline.get_at((220,360))
    assert lit.get_at((220,360)).r>200


def test_charged_release_preserves_legacy_flash(game):
    scene=game.current_scene
    scene.firing_lighting=FiringLighting(burst(),scene.native_approach.world)
    game.input.begin_frame()
    game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_j))
    game.update(1/60)
    for _ in range(48):
        game.input.begin_frame()
        game.update(1/60)
    game.input.begin_frame()
    game.handle_event(pygame.event.Event(pygame.KEYUP,key=pygame.K_j))
    game.update(1/60)
    assert scene.effects.flashes[-1]['is_charged']
    assert scene.effects.flashes[-1]['lighting_token'] is None
    assert scene.projectile_manager.projectiles[-1].id not in scene._firing_light_projectile_ids
    assert not scene.firing_lighting.active_flashes(scene.effects.flashes,scene._firing_light_token)


def test_narrow_beam_changes_only_selected_visual_stroke():
    pygame.init()
    try:
        projectiles=ProjectileManager()
        selected=projectiles.spawn(80,30,1,0,180,7)
        other=projectiles.spawn(80,60,1,0,180,9,is_charged=True)
        original=[asdict(selected),asdict(other)]
        camera=SimpleNamespace(world_to_screen=lambda x,y:(round(x),round(y)))
        baseline=pygame.Surface((120,90))
        narrowed=pygame.Surface((120,90))
        projectiles.render(baseline,camera)
        projectiles.render(narrowed,camera,narrow_projectile_ids={selected.id})
        # The same world-space endpoints remain lit; only the selected stroke narrows.
        assert baseline.get_at((68,30))[:3]!=(0,0,0)
        assert narrowed.get_at((68,30))[:3]!=(0,0,0)
        assert narrowed.get_at((80,30))[:3]!=(0,0,0)
        assert sum(baseline.get_at((75,y))[:3]!=(0,0,0) for y in range(20,41))==5
        assert sum(narrowed.get_at((75,y))[:3]!=(0,0,0) for y in range(20,41))==3
        assert pygame.image.tobytes(baseline.subsurface((0,50,120,20)),'RGB')==pygame.image.tobytes(narrowed.subsurface((0,50,120,20)),'RGB')
        assert [asdict(selected),asdict(other)]==original
    finally:
        pygame.quit()


def test_repeated_actual_taps_leave_gameplay_identical_with_light(tmp_path):
    pygame.init()
    pygame.display.set_mode((960,540))
    traces=[]
    try:
        for enabled in (False,True):
            save=tmp_path/str(enabled)
            game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(save),settings_store=SettingsStore(save))
            try:
                assert game.start_new_game()[0]
                game.change_state(config.STATE_FIELD_OPS,room='act_01/approach.json',spawn='approach_checkpoint')
                scene=game.current_scene
                assert game.change_settings(combat_mode='classic')  # Compare the original tap contract.
                scene.enemy_manager.clear()
                for _ in range(30):
                    game.input.begin_frame()
                    game.update(1/60)
                scene.firing_lighting=(FiringLighting(burst(),scene.native_approach.world)
                                       if enabled else None)
                shots=[]
                original=scene.projectile_manager.spawn
                def record_spawn(*args,**kwargs):
                    shots.append({k:kwargs[k] for k in ('x','y','dir_x','dir_y','speed','damage','is_charged','weapon_type')})
                    return original(*args,**kwargs)
                scene.projectile_manager.spawn=record_spawn
                for frame in range(60):
                    game.input.begin_frame()
                    if frame in (0,15,30,45):
                        game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_j))
                    if frame in (1,16,31,46):
                        game.handle_event(pygame.event.Event(pygame.KEYUP,key=pygame.K_j))
                    game.update(1/60)
                    game.render()
                campaign=game.campaign.to_dict()
                campaign.pop('save_id')  # Each isolated save intentionally has a unique identity.
                traces.append({'shots':shots,'rect':list(scene.player.rect),'health':scene.player.health,
                               'cooldown':scene.player.weapon.cooldown_timer,'campaign':campaign})
            finally:
                game.close()
        assert len(traces[0]['shots'])==4
        assert traces[0]==traces[1]
    finally:
        pygame.quit()
