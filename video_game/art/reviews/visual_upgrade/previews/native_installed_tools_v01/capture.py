"""PURPOSE: Inspect installed approach family through normal configured-root scene paths.
CALLED BY: PYTHONPATH=. SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python capture.py --output-dir NEW_DIR.
HOW TO MODIFY: Keep temporary saves, actual asset root, event/placement disclosure and no overwrites.
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
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True);args=p.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=False)
    pygame.init();pygame.display.set_mode((960,540))
    with tempfile.TemporaryDirectory(prefix='6equj5-installed-review-') as tmp:
        def make_game():return GameStateMachine(CRTRenderer(scale=2),save_store=SaveStore(tmp),settings_store=SettingsStore(tmp))
        game=make_game()
        try:
            assert game.start_new_game()[0]
            game.change_state(config.STATE_FIELD_OPS,room='act_01/approach.json',spawn='bunker_exit')
            scene=game.current_scene;assert scene.native_approach is not None
            for _ in range(30):game.update(1/60)
            def capture(name):
                game.render();surface=game.crt.render_surface
                pygame.image.save(surface,str(args.output_dir/f'{name}_960.png'))
                pygame.image.save(pygame.transform.scale(surface,(1920,1080)),str(args.output_dir/f'{name}_1920.png'))
            samples=[]
            for x,spawn in ((0,'bunker_exit'),(240,'approach_checkpoint'),(480,'dish_perimeter')):
                scene.reset_to_spawn(spawn)
                for _ in range(30):game.update(1/60)
                scene.camera.x=float(x);scene.camera.y=18.0;capture(f'camera_x{x}_y18')
                samples.append({'camera':[x,18],'spawn':spawn,'player_rect':list(scene.player.rect)})
            scene.reset_to_spawn('bunker_exit')
            for _ in range(30):game.update(1/60)
            game.render();window=pygame.Surface((1920,1080))
            game.crt.is_crt_enabled=False;game.crt.present(window);pygame.image.save(window,str(args.output_dir/'present_crt_off_1920.png'))
            game.crt.is_crt_enabled=True;game.crt.present(window);pygame.image.save(window,str(args.output_dir/'present_crt_on_1920.png'))
            actions={8:[(pygame.KEYDOWN,pygame.K_d)],45:[(pygame.KEYDOWN,pygame.K_x)],70:[(pygame.KEYUP,pygame.K_x)],75:[(pygame.KEYDOWN,pygame.K_SPACE)],100:[(pygame.KEYUP,pygame.K_SPACE)],125:[(pygame.KEYDOWN,pygame.K_c)],145:[(pygame.KEYUP,pygame.K_c)],165:[(pygame.KEYDOWN,pygame.K_F2)],166:[(pygame.KEYUP,pygame.K_F2)],190:[(pygame.KEYDOWN,pygame.K_F2)],191:[(pygame.KEYUP,pygame.K_F2)],192:[(pygame.KEYDOWN,pygame.K_d)],235:[(pygame.KEYDOWN,pygame.K_SPACE)],255:[(pygame.KEYUP,pygame.K_SPACE)],290:[(pygame.KEYUP,pygame.K_d)]}
            frames=[];trace=[]
            for frame in range(300):
                game.input.begin_frame()
                for kind,key in actions.get(frame,[]):game.handle_event(pygame.event.Event(kind,key=key))
                game.update(1/60);game.render()
                if frame%5==0:
                    image=game.crt.render_surface
                    frames.append(Image.frombytes('RGB',image.get_size(),pygame.image.tobytes(image,'RGB')))
                    trace.append({'frame':frame,'player':[round(scene.player.x,2),round(scene.player.y,2)],'camera':[round(scene.camera.x,2),round(scene.camera.y,2)],'paused':game.pause.active,'animation':scene.player.animation_state,'health':scene.player.health})
            frames[0].save(args.output_dir/'scripted_motion_960.gif',save_all=True,append_images=frames[1:],duration=83,loop=0,optimize=False)
            game.change_state(config.STATE_BUNKER_HUB);assert game.save_checkpoint()
        finally:game.close()
        continued=make_game()
        try:
            result=continued.continue_game();assert result.status=='ok'
            continued.change_state(config.STATE_FIELD_OPS,room='act_01/approach.json',spawn='bunker_exit')
            assert continued.current_scene.native_approach is not None
            for _ in range(30):continued.update(1/60)
            continued.render();pygame.image.save(continued.crt.render_surface,str(args.output_dir/'continued_approach_960.png'))
            family=config.ASSETS_DIR/'environments/ohio_approach_v1'
            data={'driver':pygame.display.get_driver(),'asset_root':'normal configured game assets','save':'temporary',
                  'fixture':'direct field entry and three room-spawn/camera placements, synthetic KEYDOWN/KEYUP via state machine, bunker save and fresh-machine Continue, direct field reentry',
                  'actions':{str(k):[(pygame.event.event_name(kind),pygame.key.name(key)) for kind,key in v] for k,v in actions.items()},'samples':samples,'trace':trace,'continue_status':result.status,
                  'hashes':{name:sha(family/name) for name in ('manifest.json','far_1152x544.png','world_architecture_1920x576.png')},
                  'limits':'static and scripted dummy-driver fixtures; no human playthrough, actual playback inspection, native window, graphical performance, collision/fairness or art-gate acceptance'}
            (args.output_dir/'context.json').write_text(json.dumps(data,indent=2)+'\n')
            print('installed source hashes',data['hashes'],'Continue',result.status,'samples',samples)
        finally:continued.close();pygame.quit()


if __name__=='__main__':main()
