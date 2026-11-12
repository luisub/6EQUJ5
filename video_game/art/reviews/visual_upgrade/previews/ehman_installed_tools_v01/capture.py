"""PURPOSE: Verify installed 1977 backdrop and physical interaction in a temporary save.
CALLED BY: python capture.py --output-dir NEW_DIR under dummy SDL.
HOW TO MODIFY: Preserve configured assets, disclosed input/position fixtures and no art-gate claims.
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
    with tempfile.TemporaryDirectory(prefix='6equj5-ehman-installed-') as tmp:
        save=Path(tmp)/'save';game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(save),settings_store=SettingsStore(save))
        try:
            assert game.start_new_game()[0];game.campaign.apply_event({'event_id':'fixture_boss','type':'defeat_greenkeeper'});key(game,pygame.K_m);key(game,pygame.K_F7)
            scene=game.current_scene;assert scene.room.room_id=='flashback_ehman_1977' and scene.native_opaque is not None
            def capture(name,y=18):
                scene.camera.x=0;scene.camera.y=y;game.render();path=args.output_dir/f'{name}_y{y}_native_960.png';pygame.image.save(game.crt.render_surface,str(path));pygame.image.save(pygame.transform.scale(game.crt.render_surface,(1920,1080)),str(path).replace('_native_960','_review_1920'));records.append({'name':name,'camera':[0,y],'stage':str(scene.flashback.stage),'campaign_timeline':game.campaign.timeline_mode,'image':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
            for _ in range(30):game.input.begin_frame();game.update(1/60)
            capture('entry',0);capture('entry',18);scene.player.x=110;scene.player.y=208;key(game,pygame.K_e);capture('printout');key(game,pygame.K_e);capture('annotated');scene.player.x=375;key(game,pygame.K_e);capture('reel');key(game,pygame.K_e)
            assert game.current_scene.room.room_id=='act_01_mandela_test';assert game.campaign.state.inventory.get('reality_anchor_1977')==1
            game.change_state(config.STATE_BUNKER_HUB);assert game.save_checkpoint()
        finally:game.close()
        game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(save),settings_store=SettingsStore(save))
        try:
            assert game.continue_game().status=='ok';assert game.campaign.state.inventory.get('reality_anchor_1977')==1
        finally:game.close();pygame.quit()
    data={'asset_root':str(config.ASSETS_DIR),'records':records,'fixture':'Injected Act I prerequisite and printout/vault positions; physical M/F7/E/E/E/E; temporary save and fresh-machine Continue.',
          'timeline_note':'1977 flashback leaves the campaign timeline at 2029_CORE; badge reflects campaign state, not flashback date.',
          'limits':'Not an earned route, native window, human gameplay, performance or art gate.'}
    (args.output_dir/'context.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data,indent=2))
if __name__=='__main__':main()
