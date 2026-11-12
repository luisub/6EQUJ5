"""PURPOSE: Inspect the actual bunker loader against a disposable staged family.
CALLED BY: python capture.py --output-dir NEW_DIR using dummy SDL.
HOW TO MODIFY: Retain temporary assets/saves, real scene routing, and fixture disclosures.
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
from video_game.engine.scenes.bunker import BUNKER_STATIONS
from video_game.tools.build_room_family import build_backdrop_family

SOURCE=Path('video_game/art/reviews/visual_upgrade/previews/bunker_registration_director_v01/capture_v01/bunker_background_960x540.png')
SHA='cc9749e5373fbf97122426daf7e418aa21f77655e14077e399112c1256b74e40'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',required=True,type=Path);args=parser.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=False)
    if sha(SOURCE)!=SHA:raise ValueError('reviewed source hash mismatch')
    pygame.init();pygame.display.set_mode((960,540))
    with tempfile.TemporaryDirectory(prefix='6equj5-bunker-staged-') as tmp:
        base=Path(tmp).resolve();root=base/'assets';shutil.copytree(config.ASSETS_DIR,root,ignore=shutil.ignore_patterns('ohio_bunker_v1'))
        result=build_backdrop_family('ohio_bunker_v1',assets_dir=root,archive_dir=base/'archive',backdrop=SOURCE,promote=True)
        game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(base/'save'),settings_store=SettingsStore(base/'save'))
        try:
            game.assets=AssetCache(root);assert game.start_new_game()[0]
            scene=game.current_scene;scene.on_enter()
            if game.current_state_name!=config.STATE_BUNKER_HUB or scene.native_backdrop is None:raise RuntimeError('native bunker not loaded')
            samples=[]
            def capture(name):
                game.render();native=args.output_dir/f'{name}_native_960.png';review=args.output_dir/f'{name}_review_1920.png'
                pygame.image.save(game.crt.render_surface,str(native));pygame.image.save(pygame.transform.scale(game.crt.render_surface,(1920,1080)),str(review))
                samples.append({'name':name,'mateo_x':scene.mateo_x,'station':scene.get_active_station(),'dossier_open':scene.dossier_open,'native':native.name,'native_sha256':sha(native),'review':review.name,'review_sha256':sha(review)})
            for name,station in BUNKER_STATIONS.items():scene.mateo_x=station['center_x'];capture(name)
            game.input.begin_frame();game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_TAB));game.handle_event(pygame.event.Event(pygame.KEYUP,key=pygame.K_TAB))
            assert scene.dossier_open;capture('dossier')
            game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_TAB));game.handle_event(pygame.event.Event(pygame.KEYUP,key=pygame.K_TAB))
            scene.mateo_x=BUNKER_STATIONS['lab']['center_x'];game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e));assert game.current_state_name==config.STATE_SCIENCE_LAB
            game.change_state(config.STATE_BUNKER_HUB);assert game.current_scene.native_backdrop is not None
            info={'source':str(SOURCE),'source_sha256':sha(SOURCE),'promotion_status':result['status'],'samples':samples,
                  'composition':'normal BunkerHubScene native family load replaces only layers 01–04; original actor/shadow, layers 05–06, prompts, HUD and dossier remain',
                  'fixture':'dummy SDL, copied temporary assets and saves, direct position at station centers, physical Tab to open/close dossier and E to enter lab; bunker re-entry reloads family',
                  'limitations':'temporary family only; no native window, normal movement, CRT presentation, full human gameplay, performance or art gate acceptance'}
            (args.output_dir/'context.json').write_text(json.dumps(info,indent=2)+'\n');print(json.dumps(samples,indent=2))
        finally:game.close();pygame.quit()

if __name__=='__main__':main()
