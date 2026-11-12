"""PURPOSE: Inspect relay family through normal input and actual timeline layers.
CALLED BY: python capture.py --output-dir NEW_DIR under dummy SDL.
HOW TO MODIFY: Preserve temporary assets/saves, input actions and fixture disclosures.
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
SOURCE=Path('video_game/art/reviews/visual_upgrade/previews/relay_registration_director_v01/capture_v01/relay_shared_background_960x576.png')
SHA='9af9affb03ea68ace6b55293193a8a3ad80691b32b907421562ea17e75a1f447'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def key(game,code):
    game.input.begin_frame();game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=code));game.update(1/60);game.handle_event(pygame.event.Event(pygame.KEYUP,key=code))
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',required=True,type=Path);args=parser.parse_args();args.output_dir.mkdir(parents=True,exist_ok=False)
    if sha(SOURCE)!=SHA:raise ValueError('reviewed source mismatch')
    pygame.init();pygame.display.set_mode((960,540))
    with tempfile.TemporaryDirectory(prefix='6equj5-relay-stage-') as tmp:
        base=Path(tmp).resolve();root=base/'assets';shutil.copytree(config.ASSETS_DIR,root,ignore=shutil.ignore_patterns('dodleston_relay_v1'))
        result=build_backdrop_family('dodleston_relay_v1',assets_dir=root,archive_dir=base/'archive',backdrop=SOURCE,promote=True)
        game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(base/'save'),settings_store=SettingsStore(base/'save'));samples=[]
        try:
            game.assets=AssetCache(root);assert game.start_new_game()[0];game.campaign.apply_event({'event_id':'fixture_boss','type':'defeat_greenkeeper'})
            key(game,pygame.K_m);key(game,pygame.K_F6);scene=game.current_scene
            assert scene.room.room_id=='act_04_dodleston_relay' and scene.native_opaque is not None
            def capture(name,y=18):
                scene.camera.x=0;scene.camera.y=y;game.render();native=args.output_dir/f'{name}_y{y}_native_960.png';review=args.output_dir/f'{name}_y{y}_review_1920.png'
                pygame.image.save(game.crt.render_surface,str(native));pygame.image.save(pygame.transform.scale(game.crt.render_surface,(1920,1080)),str(review))
                samples.append({'name':name,'timeline':scene.room.active_timeline,'campaign':game.campaign.timeline_mode,'camera':[0,y],'player_rect':list(scene.player.rect),'panel_open':scene.reality.panel_open,'native':native.name,'sha256':sha(native)})
            for timeline in ('2029_CORE','1977_ANALOG'):
                if scene.reality.world.active_timeline!=timeline:key(game,pygame.K_t)
                assert scene.reality.world.active_timeline==scene.room.active_timeline==game.campaign.timeline_mode==timeline
                for _ in range(45):game.input.begin_frame();game.update(1/60)
                for y in (0,18):capture(timeline,y)
            key(game,pygame.K_t);assert scene.room.active_timeline=='2029_CORE'
            scene.player.x=96;scene.player.y=208;scene.player.vx=0;key(game,pygame.K_e);assert scene.reality.panel_open;capture('relay_panel')
            key(game,pygame.K_2);assert scene.reality.relay.puzzle_flags['pipe_ruptured'];capture('relay_failure')
            key(game,pygame.K_r);key(game,pygame.K_1);key(game,pygame.K_1);assert scene.reality.relay.puzzle_flags['dodleston_cassette_cached'];capture('relay_recovered')
            data={'source':str(SOURCE),'source_sha256':sha(SOURCE),'promotion_status':result['status'],'samples':samples,
                  'fixture':'temporary root/save; injected Act I completion, physical M/F6/T; 45 fixed updates, camera y0/18; teleport to relay and E/2/R/1/1 keys for failure/recovery',
                  'limits':'Staged static fixtures, injected prerequisite/position; not an earned route, human play, native window, performance or art gate.'}
            (args.output_dir/'context.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data,indent=2))
        finally:game.close();pygame.quit()
if __name__=='__main__':main()
