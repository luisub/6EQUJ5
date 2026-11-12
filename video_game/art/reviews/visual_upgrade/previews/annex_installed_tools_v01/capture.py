"""PURPOSE: Capture configured-root annex after a normal-key timeline swap.
CALLED BY: python capture.py --output-dir NEW_DIR under dummy SDL.
HOW TO MODIFY: Preserve configured assets, temporary saves and prerequisite disclosure.
"""
import argparse,hashlib,json,tempfile
from pathlib import Path
import pygame
from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine

def key(game,code):
    game.input.begin_frame();game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=code));game.update(1/60);game.handle_event(pygame.event.Event(pygame.KEYUP,key=code))
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',required=True,type=Path);args=parser.parse_args();args.output_dir.mkdir(parents=True,exist_ok=False)
    pygame.init();pygame.display.set_mode((960,540));records=[]
    with tempfile.TemporaryDirectory(prefix='6equj5-annex-installed-') as tmp:
        save=Path(tmp)/'save';game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(save),settings_store=SettingsStore(save))
        try:
            assert game.start_new_game()[0];game.campaign.apply_event({'event_id':'fixture_boss','type':'defeat_greenkeeper'});key(game,pygame.K_m)
            scene=game.current_scene;assert scene.native_opaque is not None and scene.room.room_id=='act_01_mandela_test'
            for timeline in ('2029_CORE','1977_ANALOG'):
                if scene.reality.world.active_timeline!=timeline:key(game,pygame.K_t)
                assert scene.reality.world.active_timeline==scene.room.active_timeline==game.campaign.timeline_mode==timeline
                for _ in range(45):game.input.begin_frame();game.update(1/60)
                for y in (0,18):
                    scene.camera.x=0;scene.camera.y=y;game.render();path=args.output_dir/f'{timeline}_y{y}_native_960.png'
                    pygame.image.save(game.crt.render_surface,str(path));pygame.image.save(pygame.transform.scale(game.crt.render_surface,(1920,1080)),str(path).replace('_native_960','_review_1920'))
                    records.append({'timeline':timeline,'campaign':game.campaign.timeline_mode,'room':scene.room.active_timeline,'camera':[0,y],'image':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
            game.change_state(config.STATE_BUNKER_HUB);assert game.save_checkpoint()
        finally:game.close()
        game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(save),settings_store=SettingsStore(save))
        try:
            assert game.continue_game().status=='ok';key(game,pygame.K_m);assert game.current_scene.room.room_id=='act_01_mandela_test';assert game.current_scene.native_opaque is not None;game.render()
        finally:game.close();pygame.quit()
    data={'asset_root':str(config.ASSETS_DIR),'driver':'dummy','records':records,'continue':'fresh machine loaded temporary save, physical M re-entry into annex',
          'fixture':'Injected Act I completion; physical M and T; 45 fixed updates each, camera y0/18; actual configured asset root',
          'limits':'Not an earned route, native window, human gameplay, performance or art gate acceptance.'}
    (args.output_dir/'context.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data,indent=2))
if __name__=='__main__':main()
