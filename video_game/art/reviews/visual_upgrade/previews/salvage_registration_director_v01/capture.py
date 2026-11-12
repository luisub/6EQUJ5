"""PURPOSE: Register one salvage candidate behind the real yard in disposable fixtures.
CALLED BY: PYTHONPATH=. SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python capture.py --output-dir NEW_PATH.
HOW TO MODIFY: Preserve source transform, explicit camera/spawn and temporary-save disclosure.
"""
import argparse
import hashlib
import json
import tempfile
from pathlib import Path
import pygame
from PIL import Image
from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore

SOURCE=Path('video_game/art/source/visual_upgrade/candidates/salvage_world_scene_v01/source/salvage_world_scene_generated_master.png')
FAR=Path('video_game/art/reviews/visual_upgrade/previews/approach_far_registration_v01/far_native_1152x544.png')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
a.output_dir.mkdir(parents=True,exist_ok=False)
with Image.open(SOURCE) as src:
    if src.mode!='RGBA': raise ValueError(f'Expected RGBA, got {src.mode}')
    source_size=src.size
    src.resize((1280,576), Image.Resampling.LANCZOS).save(a.output_dir/'yard_world_layer_1280x576.png')
pygame.init();pygame.display.set_mode((960,540))
try:
    with tempfile.TemporaryDirectory(prefix='6equj5-salvage-registration-') as tmp:
        game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(tmp),settings_store=SettingsStore(tmp))
        try:
            game.start_new_game();game.change_state(config.STATE_FIELD_OPS)
            scene=game.current_scene;scene.load_room('act_01/salvage_yard.json',spawn_name='yard_midpoint')
            for _ in range(30): game.input.begin_frame();game.update(1/60)
            far=pygame.image.load(str(FAR)).convert_alpha()
            layer=pygame.image.load(str(a.output_dir/'yard_world_layer_1280x576.png')).convert_alpha()
            def background(_surface,camera):
                f=(round(.2*camera.x),round(.1*camera.y))
                w=(round(2*camera.x),round(2*camera.y))
                game.crt.composite_native(far.subsurface(pygame.Rect(*f,960,540)),(0,0),(480,270))
                game.crt.composite_native(layer.subsurface(pygame.Rect(*w,960,540)),(0,0),(480,270))
            scene.room.render_background=background
            samples=[]
            for cx in (0,80,160):
                scene.camera.x,scene.camera.y=cx,18;game.render()
                native=a.output_dir/f'camera_x{cx}_y18_native_960.png'
                review=a.output_dir/f'camera_x{cx}_y18_review_1920.png'
                pygame.image.save(game.crt.render_surface,str(native))
                pygame.image.save(pygame.transform.scale(game.crt.render_surface,(1920,1080)),str(review))
                samples.append({'camera':[cx,18],'player_rect':list(scene.player.rect),'grounded':scene.player.is_grounded,
                    'coupler_collected':bool(game.campaign.state.room_flags.get('trench_coupler_collected',False)),
                    'native':native.name,'native_sha256':sha(native),'review':review.name,'review_sha256':sha(review)})
            info={'source':str(SOURCE),'source_size':list(source_size),'source_sha256':sha(SOURCE),
                'export':'yard_world_layer_1280x576.png','export_sha256':sha(a.output_dir/'yard_world_layer_1280x576.png'),
                'transform':'full-image Lanczos resize to 1280x576; no masks, alpha edits, painting or cleanup',
                'far_fixture':str(FAR),'far_sha256':sha(FAR),'far_use':'interim fixture, not approved yard sky',
                'composition':'fixture-local callback: far then world layer, then real yard tiles/objects/actors/effects/HUD',
                'fixture':'dummy display/audio, temporary saves, new game, direct field then yard_midpoint spawn, 30 updates at 1/60, force camera x0/80/160 y18 without updates between views',
                'samples':samples,'limits':'static scripted fixture; no normal-input traversal, native display, performance, readability, motion, alpha-cleanup or production acceptance'}
            (a.output_dir/'context.json').write_text(json.dumps(info,indent=2)+'\n')
            print(json.dumps(samples,indent=2))
        finally: game.close()
finally: pygame.quit()
