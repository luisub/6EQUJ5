"""PURPOSE: Check relay workstation context and E panel over the registered candidate.
CALLED BY: From repo root with dummy SDL and --output-dir NEW_DIR.
HOW TO MODIFY: Preserve direct-placement and synthetic-key disclosure and temporary saves.
"""
import argparse
import hashlib
import json
import tempfile
from pathlib import Path
import pygame
from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine

PLATE = Path('video_game/art/reviews/visual_upgrade/previews/relay_registration_director_v01/capture_v01/relay_shared_background_960x576.png')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args()
    a.output_dir.mkdir(parents=True,exist_ok=False)
    pygame.init()
    pygame.display.set_mode((960,540))
    try:
        with tempfile.TemporaryDirectory(prefix='6equj5-relay-panel-') as tmp:
            game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(tmp),settings_store=SettingsStore(tmp))
            try:
                game.start_new_game()
                game.change_state(config.STATE_FIELD_OPS)
                scene=game.current_scene
                scene.load_room('act_04/dodleston_relay.json',spawn_name='relay_terminal_post')
                for _ in range(30):
                    game.input.begin_frame()
                    game.update(1/60)
                plate=pygame.image.load(str(PLATE)).convert()
                def background(_surface,camera):
                    game.crt.composite_native(plate.subsurface(pygame.Rect(0,round(2*camera.y),960,540)),(0,0),(480,270))
                scene.room.render_background=background
                scene.camera.x,scene.camera.y=0,18
                samples=[]
                for name in ('terminal_before_e','terminal_panel_e'):
                    if name=='terminal_panel_e':
                        game.input.begin_frame()
                        game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e))
                        game.handle_event(pygame.event.Event(pygame.KEYUP,key=pygame.K_e))
                    game.render()
                    path=a.output_dir/f'{name}_native_960.png'
                    pygame.image.save(game.crt.render_surface,str(path))
                    samples.append({'file':path.name,'sha256':sha(path),'panel_open':scene.reality.panel_open,'player_rect':list(scene.player.rect)})
                (a.output_dir/'context.json').write_text(json.dumps({'plate':str(PLATE),'plate_sha256':sha(PLATE),'fixture':'dummy SDL, temporary save, direct relay_terminal_post spawn, 30 updates, fixed camera (0,18), synthetic E KEYDOWN/UP; no progression or human play claim','samples':samples},indent=2)+'\n')
                print(json.dumps(samples,indent=2))
            finally:
                game.close()
    finally:
        pygame.quit()

if __name__=='__main__':
    main()
