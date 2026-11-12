"""PURPOSE: Inspect the actual field loader against a disposable promoted family.
CALLED BY: PYTHONPATH=. SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python capture.py --far FAR --world WORLD --output-dir NEW_PATH.
HOW TO MODIFY: Preserve temporary asset/save roots, actual field path and fixture disclosure.
"""
import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
import pygame
from video_game.engine import config
from video_game.engine.assets import AssetCache
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine
from video_game.tools.build_approach_family import build_family


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--far',type=Path,required=True);parser.add_argument('--world',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True);args=parser.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=False)
    with tempfile.TemporaryDirectory(prefix='6equj5-native-family-') as tmp:
        base=Path(tmp).resolve(); assets=base/'assets';shutil.copytree(config.ASSETS_DIR,assets)
        promoted=build_family(assets_dir=assets,archive_dir=base/'archive',far=args.far,world=args.world,promote=True)
        pygame.init();pygame.display.set_mode((960,540))
        game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(base/'save'),settings_store=SettingsStore(base/'save'))
        try:
            game.assets=AssetCache(assets);game.start_new_game()
            game.change_state(config.STATE_FIELD_OPS,room='act_01/approach.json',spawn='bunker_exit')
            scene=game.current_scene
            if scene.native_approach is None:raise RuntimeError('temporary promoted family was not loaded')
            for _ in range(30):game.update(1/60)
            records=[]
            for x,spawn in ((0,'bunker_exit'),(240,'approach_checkpoint'),(480,'dish_perimeter')):
                scene.reset_to_spawn(spawn)
                for _ in range(30):game.update(1/60)
                for y in (0,18):
                    scene.camera.x=float(x);scene.camera.y=float(y);game.render()
                    native=args.output_dir/f'camera_x{x}_y{y}_960.png';review=args.output_dir/f'camera_x{x}_y{y}_1920.png'
                    pygame.image.save(game.crt.render_surface,str(native))
                    pygame.image.save(pygame.transform.scale(game.crt.render_surface,(1920,1080)),str(review))
                    records.append({'camera':[x,y],'spawn':spawn,'player_rect':list(scene.player.rect),
                                    'native':native.name,'native_sha256':sha(native),'review':review.name,'review_sha256':sha(review)})
            data={'driver':pygame.display.get_driver(),'fixture':'copied legacy asset root, explicit temporary promotion and save; direct field entry; each spawn settled 30 ticks, camera positioned explicitly',
                  'sources':{'far':{'path':str(args.far),'sha256':sha(args.far)},'world':{'path':str(args.world),'sha256':sha(args.world)}},
                  'promotion_status':promoted['status'],'manifest':promoted['manifest'],'captures':records,
                  'limitations':'actual field render with fixture placement; no production promotion, human gameplay, native window, motion, visual gate or FPS claim'}
            (args.output_dir/'context.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(records,indent=2))
        finally:game.close();pygame.quit()


if __name__=='__main__':main()
