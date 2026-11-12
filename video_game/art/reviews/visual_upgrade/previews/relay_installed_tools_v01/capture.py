"""PURPOSE: Verify installed relay art with real input, state and temporary saves.
CALLED BY: python capture.py --output-dir NEW_DIR under dummy SDL.
HOW TO MODIFY: Preserve configured asset root, physical actions and fixture disclosure.
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
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',type=Path,required=True);args=parser.parse_args();args.output_dir.mkdir(parents=True,exist_ok=False)
    pygame.init();pygame.display.set_mode((960,540));records=[]
    with tempfile.TemporaryDirectory(prefix='6equj5-relay-installed-') as tmp:
        save=Path(tmp)/'save';game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(save),settings_store=SettingsStore(save))
        try:
            assert game.start_new_game()[0];game.campaign.apply_event({'event_id':'fixture_boss','type':'defeat_greenkeeper'});key(game,pygame.K_m);key(game,pygame.K_F6)
            scene=game.current_scene;assert scene.room.room_id=='act_04_dodleston_relay' and scene.native_opaque is not None
            def capture(name):
                scene.camera.x=0;scene.camera.y=18;game.render();path=args.output_dir/f'{name}_native_960.png';pygame.image.save(game.crt.render_surface,str(path));pygame.image.save(pygame.transform.scale(game.crt.render_surface,(1920,1080)),str(path).replace('_native_960','_review_1920'));records.append({'name':name,'room_timeline':scene.room.active_timeline,'campaign_timeline':game.campaign.timeline_mode,'image':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
            capture('2029');key(game,pygame.K_t);assert game.campaign.timeline_mode==scene.room.active_timeline=='1977_ANALOG';capture('1977');key(game,pygame.K_t)
            scene.player.x=104;scene.player.y=208;key(game,pygame.K_e);assert scene.reality.panel_open;capture('panel')
            key(game,pygame.K_2);assert scene.reality.relay.puzzle_flags['pipe_ruptured'];key(game,pygame.K_r);key(game,pygame.K_1);key(game,pygame.K_1)
            assert scene.reality.relay.puzzle_flags['dodleston_cassette_cached'];capture('recovered');key(game,pygame.K_ESCAPE);game.change_state(config.STATE_BUNKER_HUB);assert game.save_checkpoint()
        finally:game.close()
        game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(save),settings_store=SettingsStore(save))
        try:
            assert game.continue_game().status=='ok';key(game,pygame.K_m);key(game,pygame.K_F6)
            scene=game.current_scene;assert scene.native_opaque is not None and scene.reality.relay.puzzle_flags['dodleston_cassette_cached'];game.render()
        finally:game.close();pygame.quit()
    data={'asset_root':str(config.ASSETS_DIR),'records':records,'fixture':'Injected Act I prerequisite and player position; physical M/F6/T/E/2/R/1/1/ESC; fresh-machine Continue and M/F6 reload from temporary save.',
          'control_placement':'decorative control lies inside existing E activation range but differs from requested object rectangle; no trigger or physics change',
          'limits':'not an earned route, native window, human gameplay, performance or art gate.'}
    (args.output_dir/'context.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data,indent=2))
if __name__=='__main__':main()
