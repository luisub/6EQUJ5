"""PURPOSE: Register dish scene art behind actual active/jammed defense fixtures.
CALLED BY: PYTHONPATH=. SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python capture.py --output-dir NEW_DIR.
HOW TO MODIFY: Preserve exact source transforms, temporary saves and all progression/time shortcuts in metadata.
"""
import argparse
import hashlib
import json
import tempfile
from pathlib import Path
import pygame
from PIL import Image
from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore

SOURCE=Path('video_game/art/source/visual_upgrade/candidates/dish_world_scene_v01/source/dish_world_scene_generated_master.png')
FAR=Path('video_game/art/reviews/visual_upgrade/previews/approach_far_registration_v01/far_native_1152x544.png')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
a.output_dir.mkdir(parents=True,exist_ok=False)
with Image.open(SOURCE) as src:
    if src.mode!='RGBA': raise ValueError(f'Expected RGBA, got {src.mode}')
    source_size=src.size
    src.resize((1280,576), Image.Resampling.LANCZOS).save(a.output_dir/'dish_world_layer_1280x576.png')
pygame.init();pygame.display.set_mode((960,540))
try:
    with tempfile.TemporaryDirectory(prefix='6equj5-dish-registration-') as tmp:
        game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(tmp),settings_store=SettingsStore(tmp))
        try:
            game.start_new_game()
            assert game.campaign.apply_event({'event_id':'fixture_collect','type':'collect_analog_coupler'})
            assert game.campaign.apply_event({'event_id':'fixture_repair','type':'repair_dish_feedhorn'})
            game.change_state(config.STATE_FIELD_OPS)
            scene=game.current_scene;scene.load_room('act_01/dish_catwalk.json',spawn_name='catwalk_feedhorn')
            assert scene.holdout and scene.holdout.is_active
            scene.player.x=312;scene.player.y=208;scene.player.vx=scene.player.vy=0
            for _ in range(30): game.input.begin_frame();game.update(1/60)
            far=pygame.image.load(str(FAR)).convert_alpha()
            layer=pygame.image.load(str(a.output_dir/'dish_world_layer_1280x576.png')).convert_alpha()
            def background(_surface,camera):
                f=(round(.2*camera.x),round(.1*camera.y));w=(round(2*camera.x),round(2*camera.y))
                game.crt.composite_native(far.subsurface(pygame.Rect(*f,960,540)),(0,0),(480,270))
                game.crt.composite_native(layer.subsurface(pygame.Rect(*w,960,540)),(0,0),(480,270))
            scene.room.render_background=background
            samples=[]
            def capture(name,cx):
                scene.camera.x,scene.camera.y=cx,18;game.render()
                native=a.output_dir/f'{name}_x{cx}_native_960.png';review=a.output_dir/f'{name}_x{cx}_review_1920.png'
                pygame.image.save(game.crt.render_surface,str(native))
                pygame.image.save(pygame.transform.scale(game.crt.render_surface,(1920,1080)),str(review))
                samples.append({'name':name,'camera':[cx,18],'player_rect':list(scene.player.rect),
                  'grounded':scene.player.is_grounded,'active':scene.holdout.is_active,'jammed':scene.holdout.is_jammed,
                  'elapsed':scene.holdout.elapsed_time,'native':native.name,'native_sha256':sha(native),'review':review.name,'review_sha256':sha(review)})
            for cx in (0,80,160):capture('active',cx)
            scene.holdout.elapsed_time=23.99
            game.input.begin_frame();game.update(1/60)
            if not scene.holdout.is_jammed: raise RuntimeError('Scheduled jam was not reached')
            capture('jammed',80)
            if abs(scene.player.rect.centerx-320)>56: raise RuntimeError('Player outside E-clear range')
            game.input.begin_frame();game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e));game.update(1/60)
            game.handle_event(pygame.event.Event(pygame.KEYUP,key=pygame.K_e))
            if scene.holdout.is_jammed: raise RuntimeError('Physical E event did not clear jam')
            capture('cleared',80)
            game.input.begin_frame();game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_x));game.update(1/60)
            projectile_count=len(scene.projectile_manager.projectiles)
            capture('fire_attempt',80)
            game.handle_event(pygame.event.Event(pygame.KEYUP,key=pygame.K_x))
            info={'source':str(SOURCE),'source_size':list(source_size),'source_sha256':sha(SOURCE),
              'export':'dish_world_layer_1280x576.png','export_sha256':sha(a.output_dir/'dish_world_layer_1280x576.png'),
              'transform':'full-image Lanczos resize to 1280x576; no masks, alpha edits, painting or cleanup',
              'far_fixture':str(FAR),'far_sha256':sha(FAR),'far_use':'interim fixture, not approved dish far',
              'composition':'fixture-local callback: far then world layer, then real dish tiles/objects/actors/effects/HUD',
              'fixture':'dummy SDL, temporary saves, new game; directly apply collect and repair campaign events; direct field then dish room, teleport player x312/y208, settle 30 ticks; cameras forced x0/80/160 y18; directly set elapsed=23.99 then one 1/60 update to scheduled jam; dispatch physical KEYDOWN E to clear; fire attempt via KEYDOWN X',
              'fire_attempt_projectile_count':projectile_count,'samples':samples,
              'limits':'synthetic prerequisite/time/position fixture, not earned route or normal full holdout; static views, no human/native display/motion/fairness/performance or art-gate acceptance'}
            (a.output_dir/'context.json').write_text(json.dumps(info,indent=2)+'\n')
            print(json.dumps({'projectiles':projectile_count,'samples':samples},indent=2))
        finally: game.close()
finally: pygame.quit()
