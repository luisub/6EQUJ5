"""PURPOSE: Capture actual approach shots and no-fire frames at a fixed camera.
CALLED BY: python capture.py --output-dir NEW_DIR under dummy SDL.
HOW TO MODIFY: Preserve real input, temporary saves, context and unchanged gameplay.
"""
import argparse
import hashlib
import json
import os
import random
import sys
import tempfile
from pathlib import Path
import pygame
from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=False)
    random.seed(17)
    pygame.init()
    pygame.display.set_mode((960,540))
    samples=[]
    with tempfile.TemporaryDirectory(prefix='6equj5-light-capture-') as tmp:
        try:
            for facing in ('right','left'):
                save=Path(tmp)/facing
                game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(save),settings_store=SettingsStore(save))
                try:
                    assert game.start_new_game()[0]
                    game.change_state(config.STATE_FIELD_OPS,room='act_01/approach.json',spawn='approach_checkpoint')
                    scene=game.current_scene
                    scene.enemy_manager.clear()
                    for _ in range(30):
                        game.input.begin_frame()
                        game.update(1/60)
                    direction=pygame.K_d if facing=='right' else pygame.K_a
                    game.input.begin_frame()
                    game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=direction))
                    game.update(1/60)
                    game.handle_event(pygame.event.Event(pygame.KEYUP,key=direction))
                    for _ in range(20):
                        game.input.begin_frame()
                        game.update(1/60)
                    assert scene.player.facing==facing and scene.player.is_grounded
                    camera=(240,18)
                    prior={'clip':scene.player.animator.current_state,'muzzle_world':list(scene.player.get_muzzle_world_pos()),
                           'player_rect':list(scene.player.rect),'facing':scene.player.facing}
                    def capture(name):
                        scene.camera.x,scene.camera.y=camera
                        game.render()
                        native=args.output_dir/f'{facing}_{name}_native_960.png'
                        review=args.output_dir/f'{facing}_{name}_review_1920.png'
                        pygame.image.save(game.crt.render_surface,str(native))
                        pygame.image.save(pygame.transform.scale(game.crt.render_surface,(1920,1080)),str(review))
                        game.crt.glitch_timer_ms=0
                        for enabled in (False,True):
                            game.crt.is_crt_enabled=enabled
                            window=pygame.Surface((game.crt.win_w,game.crt.win_h))
                            game.crt.present(window)
                            pygame.image.save(window,str(args.output_dir/f'{facing}_{name}_crt_{"on" if enabled else "off"}_1920.png'))
                        samples.append({'facing':facing,'name':name,'camera':list(camera),'clip':scene.player.animator.current_state,
                            'player_rect':list(scene.player.rect),'flashes':[dict(f) for f in scene.effects.flashes],
                            'projectiles':[[p.x,p.y,p.active] for p in scene.projectile_manager.projectiles],
                            'native':native.name,'native_sha256':sha(native),'review':review.name,'review_sha256':sha(review)})
                    capture('nofire')
                    game.input.begin_frame()
                    game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_j))
                    game.update(1/60)
                    game.handle_event(pygame.event.Event(pygame.KEYUP,key=pygame.K_j))
                    capture('fire0')
                    for frame in (1,2,3,4,5):
                        game.input.begin_frame()
                        game.update(1/60)
                        capture(f'fire{frame}')
                    samples.append({'facing':facing,'pre_fire':prior})
                finally:
                    game.close()
        finally:
            pygame.quit()
    context={'argv':sys.argv,'cwd':str(Path.cwd()),'temp_save_root':tmp,'environment':{k:os.environ.get(k) for k in ('SDL_VIDEODRIVER','SDL_AUDIODRIVER','PYTHONPATH')},
        'fixture':'dummy SDL; installed approach; direct checkpoint entry; enemy list cleared; physical directional turn and J fire; fixed camera (240,18); sequential fixed 1/60 updates; unchanged runtime sprite and geometry',
        'samples':samples,'limits':'static frame samples, not native window, full gameplay, perceptual motion, real-time performance or art gate'}
    (args.output_dir/'context.json').write_text(json.dumps(context,indent=2)+'\n')
    print(json.dumps({'samples':len(samples),'output':str(args.output_dir)},indent=2))

if __name__=='__main__':
    main()
