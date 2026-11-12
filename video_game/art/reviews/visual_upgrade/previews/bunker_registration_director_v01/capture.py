"""PURPOSE: Register one native bunker backdrop with the actual actor, overlays and station UI.
CALLED BY: PYTHONPATH=. SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python capture.py --output-dir NEW_DIR.
HOW TO MODIFY: Retain temporary-save fixture, native/legacy z-order and transform disclosures.
"""
import argparse, hashlib, json, tempfile
from pathlib import Path
import pygame
from PIL import Image
from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.scenes.bunker import BUNKER_STATIONS
SOURCE=Path('video_game/art/source/visual_upgrade/candidates/bunker_background_v01/source/bunker_background_generated_master.png')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();a.output_dir.mkdir(parents=True,exist_ok=False)
with Image.open(SOURCE) as src:
    if src.mode not in ('RGB','RGBA'):raise ValueError(f'Unexpected source mode {src.mode}')
    if src.mode=='RGBA' and src.getchannel('A').getextrema()!=(255,255):raise ValueError('Backdrop must be opaque')
    size=src.size;mode=src.mode;src.convert('RGB').resize((960,540),Image.Resampling.LANCZOS).save(a.output_dir/'bunker_background_960x540.png')
pygame.init();pygame.display.set_mode((960,540))
try:
  with tempfile.TemporaryDirectory(prefix='6equj5-bunker-register-') as tmp:
    game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(tmp),settings_store=SettingsStore(tmp))
    try:
      game.start_new_game();scene=game.current_scene
      if game.current_state_name!=config.STATE_BUNKER_HUB:raise RuntimeError('Expected bunker on new game')
      backdrop=pygame.image.load(str(a.output_dir/'bunker_background_960x540.png')).convert()
      original_layers=scene.layers[:];scene.layers[:4]=[None]*4
      original_clear=game.crt.clear
      def clear_and_background(*args,**kwargs):
        original_clear(*args,**kwargs);game.crt.composite_native(backdrop,(0,0),(480,270))
      game.crt.clear=clear_and_background
      samples=[]
      def capture(name):
        game.render();native=a.output_dir/f'{name}_native_960.png';review=a.output_dir/f'{name}_review_1920.png'
        pygame.image.save(game.crt.render_surface,str(native));pygame.image.save(pygame.transform.scale(game.crt.render_surface,(1920,1080)),str(review))
        samples.append({'name':name,'mateo_x':scene.mateo_x,'active_station':scene.get_active_station(),
          'dossier_open':scene.dossier_open,'native':native.name,'native_sha256':sha(native),'review':review.name,'review_sha256':sha(review)})
      for name,station in BUNKER_STATIONS.items():scene.mateo_x=station['center_x'];capture(name)
      game.input.begin_frame();game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_TAB));game.handle_event(pygame.event.Event(pygame.KEYUP,key=pygame.K_TAB))
      if not scene.dossier_open:raise RuntimeError('Dossier did not open')
      capture('dossier')
      game.crt.clear=original_clear;scene.layers[:]=original_layers
      info={'source':str(SOURCE),'source_size':list(size),'source_mode':mode,'source_sha256':sha(SOURCE),
        'export':'bunker_background_960x540.png','export_sha256':sha(a.output_dir/'bunker_background_960x540.png'),
        'transform':'full-image Lanczos resize to 960x540; no masks, painting, alpha editing or cleanup',
        'composition':'fixture-only clear wrapper inserts native background, disables original layers 01–04; original player/shadow, layers 05–06, station prompts, HUD and dossier remain in scene order',
        'fixture':'dummy SDL, temporary save, direct placement of mateo_x at each station center; physical Tab event opens dossier; no normal movement/progression',
        'samples':samples,'limits':'temporary fixture callback, not runtime promotion; no real window, motion, station interaction, CRT-on, performance, human or art-gate acceptance'}
      (a.output_dir/'context.json').write_text(json.dumps(info,indent=2)+'\n');print(json.dumps(samples,indent=2))
    finally:game.close()
finally:pygame.quit()
