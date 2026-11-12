"""PURPOSE: Inspect the actual annex backdrop route in both real swapped timelines.
CALLED BY: python capture.py --output-dir NEW_DIR under dummy SDL.
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

SOURCE=Path('video_game/art/reviews/visual_upgrade/previews/annex_registration_director_v02/capture_v01/annex_shared_background_960x576.png')
SHA='b12ba8f554e5cdb9f237a9f1266ed3bae06c10c480272a3c605decf50269dd4a'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def key(game,code):
    game.input.begin_frame();game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=code));game.update(1/60);game.handle_event(pygame.event.Event(pygame.KEYUP,key=code))
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',required=True,type=Path);args=parser.parse_args();args.output_dir.mkdir(parents=True,exist_ok=False)
    if sha(SOURCE)!=SHA:raise ValueError('source mismatch')
    pygame.init();pygame.display.set_mode((960,540))
    with tempfile.TemporaryDirectory(prefix='6equj5-annex-stage-') as tmp:
        base=Path(tmp).resolve();root=base/'assets';shutil.copytree(config.ASSETS_DIR,root,ignore=shutil.ignore_patterns('mandela_annex_v1'))
        result=build_backdrop_family('mandela_annex_v1',assets_dir=root,archive_dir=base/'archive',backdrop=SOURCE,promote=True)
        game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(base/'save'),settings_store=SettingsStore(base/'save'));samples=[]
        try:
            game.assets=AssetCache(root);assert game.start_new_game()[0]
            game.campaign.apply_event({'event_id':'fixture_boss','type':'defeat_greenkeeper'});key(game,pygame.K_m)
            scene=game.current_scene;assert scene.room.room_id=='act_01_mandela_test' and scene.native_opaque is not None
            for timeline in ('2029_CORE','1977_ANALOG'):
                if scene.reality.world.active_timeline!=timeline:key(game,pygame.K_t)
                assert scene.reality.world.active_timeline==scene.room.active_timeline==game.campaign.timeline_mode==timeline
                for _ in range(45):game.input.begin_frame();game.update(1/60)
                for y in (0,18):
                    scene.camera.x=0;scene.camera.y=y;game.render();stem=f'{timeline}_y{y}'
                    native=args.output_dir/f'{stem}_native_960.png';review=args.output_dir/f'{stem}_review_1920.png'
                    pygame.image.save(game.crt.render_surface,str(native));pygame.image.save(pygame.transform.scale(game.crt.render_surface,(1920,1080)),str(review))
                    samples.append({'timeline':timeline,'campaign_timeline':game.campaign.timeline_mode,'room_timeline':scene.room.active_timeline,'camera':[0,y],'player_rect':list(scene.player.rect),'platforms':[[p.x,p.y] for p in scene.reality.world.moving_platforms.values()],'native':native.name,'native_sha256':sha(native)})
            info={'source':str(SOURCE),'sha256':sha(SOURCE),'promotion_status':result['status'],'samples':samples,
              'fixture':'dummy SDL and copied temporary assets/save; injected Act I completion prerequisite, physical M annex entry and T timeline swap, 45 fixed updates after each; forced camera y0/18; platform moves normally',
              'limits':'Not an earned Act I route, full playthrough, native window, performance, human or art gate acceptance'}
            (args.output_dir/'context.json').write_text(json.dumps(info,indent=2)+'\n');print(json.dumps(info,indent=2))
        finally:game.close();pygame.quit()
if __name__=='__main__':main()
