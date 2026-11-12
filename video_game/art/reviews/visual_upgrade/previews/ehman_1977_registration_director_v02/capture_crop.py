"""PURPOSE: Register a 1977 background behind the real field and flashback overlay.
CALLED BY: From repo root with dummy SDL; provide --source and a new --output-dir.
HOW TO MODIFY: Preserve full source canvas, direct-spawn/teleport and key-event disclosure.
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
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=False)
    export=args.output_dir/'ehman_1977_background_960x576.png'
    with Image.open(args.source) as src:
        size=list(src.size)
        mode=src.mode
        if mode!='RGB':
            raise ValueError(f'Expected opaque RGB: {mode}')
        src.crop((30,0,1590,936)).resize((960,576),Image.Resampling.LANCZOS).save(export)
    pygame.init()
    pygame.display.set_mode((960,540))
    try:
        with tempfile.TemporaryDirectory(prefix='6equj5-1977-registration-') as tmp:
            game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(tmp),settings_store=SettingsStore(tmp))
            try:
                game.start_new_game()
                game.change_state(config.STATE_FIELD_OPS)
                scene=game.current_scene
                scene.load_room('flashback/ehman_1977.json',spawn_name='ehman_desk')
                for _ in range(30):
                    game.input.begin_frame()
                    game.update(1/60)
                plate=pygame.image.load(str(export)).convert()
                def background(_surface,camera):
                    game.crt.composite_native(plate.subsurface(pygame.Rect(0,round(2*camera.y),960,540)),(0,0),(480,270))
                scene.room.render_background=background
                samples=[]
                def capture(name,cy):
                    scene.camera.x,scene.camera.y=0,cy
                    game.render()
                    native=args.output_dir/f'{name}_y{cy}_native_960.png'
                    review=args.output_dir/f'{name}_y{cy}_review_1920.png'
                    pygame.image.save(game.crt.render_surface,str(native))
                    pygame.image.save(pygame.transform.scale(game.crt.render_surface,(1920,1080)),str(review))
                    samples.append({'name':name,'camera':[0,cy],'player_rect':list(scene.player.rect),'stage':scene.flashback.stage.value,'printout_open':scene.flashback.is_printout_open,'prompt':scene.prompt_text,'native':native.name,'native_sha256':sha(native),'review':review.name,'review_sha256':sha(review)})
                def press(key):
                    game.input.begin_frame()
                    game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=key))
                    game.handle_event(pygame.event.Event(pygame.KEYUP,key=key))
                    game.update(1/60)
                capture('desk_before',0)
                capture('desk_before',18)
                press(pygame.K_e)
                capture('printout_inspected',18)
                press(pygame.K_e)
                capture('printout_annotated',18)
                press(pygame.K_ESCAPE)
                scene.player.x=384
                game.input.begin_frame()
                game.update(1/60)
                capture('vault_before_retrieval',18)
                press(pygame.K_e)
                capture('vault_reel_retrieved',18)
                info={'source':str(args.source),'source_size':size,'source_mode':mode,'source_sha256':sha(args.source),'export':export.name,'export_sha256':sha(export),'transform':'Source crop (30,0,1590,936), 1560x936, then proportional 8/13 Lanczos resize to 960x576; trims left 30, right 29 and bottom 35 source pixels; no masks, painting or cleanup.','composition':'Fixture-local background callback behind actual field tile/objects, actor, flashback tint/printout and HUD.','fixture':'Dummy SDL with temporary save; direct desk spawn, 30 updates, synthetic E twice, Escape closes modal; direct x=384 reposition for vault then synthetic E. Camera forced y0/18. No normal-route progression.','limits':'Static direct-entry and teleport fixture; no real-window playthrough, final anchor return, CRT comparison, performance, human or art-gate acceptance.','samples':samples}
                (args.output_dir/'context.json').write_text(json.dumps(info,indent=2)+'\n')
                print(json.dumps(samples,indent=2))
            finally:
                game.close()
    finally:
        pygame.quit()

if __name__=='__main__':
    main()
