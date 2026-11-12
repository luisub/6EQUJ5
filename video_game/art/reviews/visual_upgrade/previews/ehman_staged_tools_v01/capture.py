"""PURPOSE: Inspect the 1977 room through actual native routing and key interactions.
CALLED BY: python capture.py --source PNG --source-sha HASH --output-dir NEW_DIR under dummy SDL.
HOW TO MODIFY: Preserve temporary assets/saves, physical input and fixture disclosures.
"""
import argparse,hashlib,json,shutil,tempfile
from pathlib import Path
import pygame
from video_game.engine import config
from video_game.engine.assets import AssetCache
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine
from video_game.tools.build_room_family import build_backdrop_family

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def key(game,code):
    game.input.begin_frame();game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=code));game.update(1/60);game.handle_event(pygame.event.Event(pygame.KEYUP,key=code))
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True);parser.add_argument('--source-sha',required=True);parser.add_argument('--output-dir',required=True,type=Path);args=parser.parse_args();args.output_dir.mkdir(parents=True,exist_ok=False)
    if sha(args.source)!=args.source_sha:raise ValueError('reviewed source mismatch')
    pygame.init();pygame.display.set_mode((960,540))
    with tempfile.TemporaryDirectory(prefix='6equj5-ehman-stage-') as tmp:
        base=Path(tmp).resolve();root=base/'assets';shutil.copytree(config.ASSETS_DIR,root,ignore=shutil.ignore_patterns('ehman_1977_v1'))
        result=build_backdrop_family('ehman_1977_v1',assets_dir=root,archive_dir=base/'archive',backdrop=args.source,promote=True)
        game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(base/'save'),settings_store=SettingsStore(base/'save'));samples=[]
        try:
            game.assets=AssetCache(root);assert game.start_new_game()[0];game.campaign.apply_event({'event_id':'fixture_boss','type':'defeat_greenkeeper'});key(game,pygame.K_m);key(game,pygame.K_F7)
            scene=game.current_scene;assert scene.room.room_id=='flashback_ehman_1977' and scene.flashback is not None and scene.native_opaque is not None
            def capture(name,y):
                scene.camera.x=0;scene.camera.y=y;game.render();native=args.output_dir/f'{name}_y{y}_native_960.png';review=args.output_dir/f'{name}_y{y}_review_1920.png'
                pygame.image.save(game.crt.render_surface,str(native));pygame.image.save(pygame.transform.scale(game.crt.render_surface,(1920,1080)),str(review))
                samples.append({'name':name,'camera':[0,y],'player_rect':list(scene.player.rect),'stage':str(scene.flashback.stage),'native':native.name,'sha256':sha(native)})
            for _ in range(30):game.input.begin_frame();game.update(1/60)
            for y in (0,18):capture('entry',y)
            scene.player.x=110;scene.player.y=208;key(game,pygame.K_e);capture('printout',18);key(game,pygame.K_e);capture('annotated',18)
            scene.player.x=375;key(game,pygame.K_e);capture('reel',18);key(game,pygame.K_e);assert game.current_scene.room.room_id=='act_01_mandela_test'
            data={'source':str(args.source),'source_sha256':sha(args.source),'promotion_status':result['status'],'samples':samples,
                  'fixture':'dummy SDL, copied temporary assets/save; injected Act I prerequisite, physical M/F7/E/E/E/E; 30 fixed updates, camera y0/18; teleported player to printout and vault',
                  'limits':'not an earned route, normal traversal, native window, human gameplay, performance or art gate.'}
            (args.output_dir/'context.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data,indent=2))
        finally:game.close();pygame.quit()
if __name__=='__main__':main()
