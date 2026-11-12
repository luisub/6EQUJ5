"""PURPOSE: Compare actual approach shots with the disabled and opt-in lighting paths.
CALLED BY: python capture.py --mode baseline|candidate --player-x X --camera-x X --output-dir NEW_DIR.
HOW TO MODIFY: Preserve physical keys, fixed same-view pairs, temporary saves and disclosures.
"""
import argparse,hashlib,json,os,random,sys,tempfile
from pathlib import Path
import pygame
from PIL import Image
from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.firing_lighting import FiringLighting
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine

BURST=Path('video_game/art/reviews/visual_upgrade/previews/firing_flash_registration_v01/cell_v01/firing_flash_64x32.png')
BURST_SHA='027df21d8bb8d6d21f1421ad7bb50845e941a6907de2af430571fd95374ef7e5'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=('baseline','candidate'),required=True)
    parser.add_argument('--player-x',type=float,required=True);parser.add_argument('--camera-x',type=float,required=True)
    parser.add_argument('--output-dir',type=Path,required=True);args=parser.parse_args();args.output_dir.mkdir(parents=True,exist_ok=False)
    if sha(BURST)!=BURST_SHA:raise ValueError('experimental burst hash mismatch')
    random.seed(17);pygame.init();pygame.display.set_mode((960,540));records=[]
    with tempfile.TemporaryDirectory(prefix='6equj5-light-compare-') as tmp:
        try:
            for facing in ('right','left'):
                save=Path(tmp)/facing;game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(save),settings_store=SettingsStore(save))
                try:
                    assert game.start_new_game()[0];game.change_state(config.STATE_FIELD_OPS,room='act_01/approach.json',spawn='approach_checkpoint')
                    scene=game.current_scene;scene.enemy_manager.clear();scene.player.x=args.player_x;scene.player.y=208
                    for _ in range(30):game.input.begin_frame();game.update(1/60)
                    direction=pygame.K_d if facing=='right' else pygame.K_a
                    game.input.begin_frame();game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=direction));game.update(1/60);game.handle_event(pygame.event.Event(pygame.KEYUP,key=direction))
                    for _ in range(20):game.input.begin_frame();game.update(1/60)
                    assert scene.player.facing==facing and scene.player.is_grounded and not scene.player.in_cover
                    if args.mode=='candidate':
                        scene.firing_lighting=FiringLighting(pygame.image.load(str(BURST)).convert_alpha(),scene.native_approach.world)
                    camera=(args.camera_x,18);frames=[];durations=[];spawned=[];original_spawn=scene.projectile_manager.spawn
                    def record_spawn(*a,**kw):
                        spawned.append({'clip':scene.player.animator.current_state,'facing':scene.player.animator.facing,'muzzle_world':[kw['x'],kw['y']]})
                        return original_spawn(*a,**kw)
                    scene.projectile_manager.spawn=record_spawn
                    def capture(name,duration,crt=False):
                        scene.camera.x,scene.camera.y=camera;game.render()
                        native=args.output_dir/f'{facing}_{name}_native_960.png';review=args.output_dir/f'{facing}_{name}_review_1920.png'
                        pygame.image.save(game.crt.render_surface,str(native));pygame.image.save(pygame.transform.scale(game.crt.render_surface,(1920,1080)),str(review))
                        if crt:
                            game.crt.glitch_timer_ms=0
                            for enabled in (False,True):
                                game.crt.is_crt_enabled=enabled;window=pygame.Surface((game.crt.win_w,game.crt.win_h));game.crt.present(window)
                                pygame.image.save(window,str(args.output_dir/f'{facing}_{name}_crt_{"on" if enabled else "off"}_1920.png'))
                        frames.append(Image.open(native).convert('RGB'));durations.append(duration)
                        records.append({'facing':facing,'name':name,'camera':list(camera),'player_rect':list(scene.player.rect),
                           'clip':scene.player.animator.current_state,'flashes':[dict(f) for f in scene.effects.flashes],
                           'projectiles':[[p.x,p.y,p.active] for p in scene.projectile_manager.projectiles],
                           'native':native.name,'sha256':sha(native)})
                    capture('off_before',200,True)
                    for shot in (1,2):
                        game.input.begin_frame();game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_j));game.update(1/60);game.handle_event(pygame.event.Event(pygame.KEYUP,key=pygame.K_j))
                        capture(f'shot{shot}_frame0',20,shot==1)
                        for frame in range(1,6):
                            game.input.begin_frame();game.update(1/60);capture(f'shot{shot}_frame{frame}',20)
                        for _ in range(18):game.input.begin_frame();game.update(1/60)
                        capture(f'off_after{shot}',200)
                    assert len(spawned)==2
                    gif=args.output_dir/f'{facing}_two_shots_960.gif';frames[0].save(gif,save_all=True,append_images=frames[1:],duration=durations,loop=0,optimize=False)
                    for frame in frames:frame.close()
                    records.append({'facing':facing,'spawned':spawned,'gif':gif.name,'gif_sha256':sha(gif),'gif_requested_durations_ms':durations})
                finally:game.close()
        finally:pygame.quit()
    context={'argv':sys.argv,'cwd':str(Path.cwd()),'temp_save_root':tmp,'environment':{k:os.environ.get(k) for k in ('SDL_VIDEODRIVER','SDL_AUDIODRIVER','PYTHONPATH')},
      'mode':args.mode,'experimental_burst':str(BURST),'burst_sha256':sha(BURST),'records':records,
      'fixture':'actual installed approach and actor, temporary saves; direct x placement, enemy list cleared; physical directional turn and two separate J taps, fixed 1/60 simulation updates, fixed camera; candidate uses explicit noninstalled source and in-memory opt-in only',
      'limits':'GIF frame durations quantized to 20ms versus 16.67ms updates; no native window, human gameplay, playback, performance or art gate claim'}
    (args.output_dir/'context.json').write_text(json.dumps(context,indent=2)+'\n');print(json.dumps({'records':len(records),'output':str(args.output_dir)},indent=2))
if __name__=='__main__':main()
