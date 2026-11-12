"""PURPOSE: Capture installed native room families through normal field routing.
CALLED BY: python capture.py --output-dir NEW_DIR using dummy SDL and disposable save.
HOW TO MODIFY: Preserve actual asset root, room entry and fixture disclosure.
"""
import argparse
import hashlib
import json
import tempfile
from pathlib import Path
import pygame
from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine

CASES=[('approach','bunker_exit',0),('approach','dish_perimeter',480),
       ('salvage_yard','yard_entrance',0),('salvage_yard','yard_midpoint',80),
       ('salvage_yard','yard_depot',160),('dish_catwalk','catwalk_start',0),
       ('dish_catwalk','catwalk_feedhorn',80),('dish_catwalk','catwalk_feedhorn',160)]


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();args.output_dir.mkdir(parents=True,exist_ok=False)
    pygame.init();pygame.display.set_mode((960,540))
    with tempfile.TemporaryDirectory(prefix='6equj5-installed-') as tmp:
        save=Path(tmp)/'save';game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(save),settings_store=SettingsStore(save));records=[]
        try:
            assert game.start_new_game()[0]
            for room,spawn,x in CASES:
                game.change_state(config.STATE_FIELD_OPS,room=f'act_01/{room}.json',spawn=spawn)
                scene=game.current_scene
                if scene.native_approach is None:raise RuntimeError(f'{room} native family missing')
                for _ in range(30):game.update(1/60)
                scene.camera.x=x;scene.camera.y=18;game.render()
                path=args.output_dir/f'{room}_x{x}_y18_960.png';pygame.image.save(game.crt.render_surface,str(path))
                pygame.image.save(pygame.transform.scale(game.crt.render_surface,(1920,1080)),str(path).replace('_960.png','_1920.png'))
                records.append({'room':room,'spawn':spawn,'camera':[x,18],'player_rect':list(scene.player.rect),'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
            game.change_state(config.STATE_BUNKER_HUB);assert game.save_checkpoint()
        finally:game.close()
        game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(save),settings_store=SettingsStore(save))
        try:
            assert game.continue_game().status=='ok'
            for room,spawn,_ in CASES[::2]:
                game.change_state(config.STATE_FIELD_OPS,room=f'act_01/{room}.json',spawn=spawn)
                assert game.current_scene.native_approach is not None
        finally:game.close();pygame.quit()
    (args.output_dir/'context.json').write_text(json.dumps({'asset_root':str(Path(config.ASSETS_DIR).resolve()),'driver':'dummy','captures':records,'continue':'temporary save, fresh machine, re-entry into sampled rooms','limitations':'fixed-camera settled fixture; no native playback, human gameplay, performance or art gate claim'},indent=2)+'\n')
    print(json.dumps(records,indent=2))


if __name__=='__main__':main()
