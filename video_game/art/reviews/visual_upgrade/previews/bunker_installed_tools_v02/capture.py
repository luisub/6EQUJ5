"""PURPOSE: Verify installed bunker backdrop via normal machine entry and presentation.
CALLED BY: python capture.py --output-dir NEW_DIR under dummy SDL.
HOW TO MODIFY: Keep configured assets, disposable saves, key events and fixture limits.
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
from video_game.engine.scenes.bunker import BUNKER_STATIONS

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',required=True,type=Path);args=parser.parse_args();args.output_dir.mkdir(parents=True,exist_ok=False)
    pygame.init();pygame.display.set_mode((960,540));records=[]
    with tempfile.TemporaryDirectory(prefix='6equj5-bunker-installed-') as tmp:
        root=Path(tmp).resolve();save=root/'save';game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(save),settings_store=SettingsStore(save))
        try:
            assert game.start_new_game()[0];scene=game.current_scene;assert scene.native_backdrop is not None
            for name,station in BUNKER_STATIONS.items():
                scene.mateo_x=station['center_x'];game.render();path=args.output_dir/f'{name}_native_960.png';pygame.image.save(game.crt.render_surface,str(path));pygame.image.save(pygame.transform.scale(game.crt.render_surface,(1920,1080)),str(path).replace('_native_960','_review_1920'));records.append({'station':name,'x':scene.mateo_x,'image':path.name,'sha256':sha(path)})
            game.crt.glitch_timer_ms=0
            for enabled in (False,True):
                game.crt.is_crt_enabled=enabled;window=pygame.Surface((game.crt.win_w,game.crt.win_h));game.crt.present(window);path=args.output_dir/f'crt_{"on" if enabled else "off"}_1920.png';pygame.image.save(window,str(path))
            game.input.begin_frame();game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_TAB));game.handle_event(pygame.event.Event(pygame.KEYUP,key=pygame.K_TAB));assert scene.dossier_open
            game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_TAB));game.handle_event(pygame.event.Event(pygame.KEYUP,key=pygame.K_TAB));assert not scene.dossier_open
            scene.mateo_x=BUNKER_STATIONS['lab']['center_x'];game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e));assert game.current_state_name==config.STATE_SCIENCE_LAB
            game.change_state(config.STATE_BUNKER_HUB);assert game.current_scene.native_backdrop is not None;assert game.save_checkpoint()
        finally:game.close()
        game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(save),settings_store=SettingsStore(save))
        try:
            assert game.continue_game().status=='ok';assert game.current_scene.native_backdrop is not None;game.render()
        finally:game.close();pygame.quit()
    info={'asset_root':str(config.ASSETS_DIR),'driver':'dummy','captures':records,'continuation':'fresh machine loaded temporary save in bunker',
          'fixture':'New game; direct station-center positions; physical Tab/E and lab→bunker transition; CRT on/off actual present',
          'limits':'Static dummy SDL fixture; no real window, motion playback, normal play, audible or art gate acceptance'}
    (args.output_dir/'context.json').write_text(json.dumps(info,indent=2)+'\n');print(json.dumps(info,indent=2))
if __name__=='__main__':main()
