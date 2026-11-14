"""Capture the earned final fight and restored park using isolated progress fixtures."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import tempfile

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pygame
from PIL import Image

from video_game.engine import config
from video_game.engine.alien_journey import dispatch, journey_data, save_ledger
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine


def capture(output):
    output.mkdir(parents=True, exist_ok=False)
    pygame.init()
    pygame.display.set_mode((960, 540))
    random.seed(1977)
    records = []
    with tempfile.TemporaryDirectory(prefix='6equj5-finale-') as temporary:
        game = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(Path(temporary)/'save'),
                                settings_store=SettingsStore(Path(temporary)/'settings'))
        game.change_settings(scale=1, crt_effects=False)
        def key(code, down=True):
            game.handle_event(pygame.event.Event(pygame.KEYDOWN if down else pygame.KEYUP, key=code))
        def tap(code):
            key(code); key(code, False)
        def step(count=1):
            for _ in range(count):
                game.update(1/60)
                game.input.begin_frame()
        def frame():
            game.render()
            s = game.crt.render_surface
            return Image.frombytes('RGB', s.get_size(), pygame.image.tobytes(s, 'RGB'))
        def still(name, setup):
            frame().save(output / (name + '.png'))
            records.append({'file':name+'.png', 'size':[960,540], 'setup':setup})
        try:
            assert game.start_new_game(replace_existing=True)[0]
            worlds = journey_data()['worlds']
            game.campaign.apply_event({'event_id':'capture_portal','type':'defeat_portal_warden'})
            for world in worlds:
                game.campaign.apply_event({'event_id':'capture_'+world['id'],'type':world['defeat_event']})
            save_ledger(game.campaign, {'version':1,'world_id':None,'stage':'final','checkpoint':None,
                                       'receipts':[w['civ_id'] for w in worlds]})
            dispatch(game)
            scene = game.current_scene
            step(100)
            still('core-network', 'Eleven prior victories and receipts staged; final arena after 100 normal updates.')
            scene.player.x, scene.player.y = 250, 208
            key(pygame.K_x)
            second = False
            for tick in range(4000):
                step()
                if scene.boss.final_stage == 2 and not second:
                    second = True
                    still('core-second-form', 'Second health stage reached with mapped fire; player x=250 fixture.')
                if scene.is_defeated_sequence or scene.player.is_dead:
                    break
            key(pygame.K_x, False)
            assert second and scene.is_defeated_sequence and not scene.player.is_dead
            step(170)
            still('core-disconnected', 'Both full health stages defeated by mapped fire; first earned ending page.')
            for _ in scene.story.pages:
                tap(pygame.K_RETURN)
            assert game.current_state_name == config.STATE_RESTORED_EARTH
            park = game.current_scene
            step(60)
            still('central-park-dialogue', 'Restored Earth entered through the earned final dialogue; first park page.')
            for _ in park.pages:
                tap(pygame.K_RETURN)
            step(45)
            still('central-park', 'All ending pages acknowledged; native peaceful park with families, birds, water and Mateo.')
            frames = []
            key(pygame.K_RIGHT)
            for tick in range(300):
                step()
                if tick % 6 == 0:
                    frames.append(frame())
            key(pygame.K_RIGHT, False)
            palette = frames[25].quantize(colors=256, dither=Image.Dither.NONE)
            indexed = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
            indexed[0].save(output/'central-park-walk.gif', save_all=True, append_images=indexed[1:],
                            duration=100, loop=0, optimize=True, disposal=1)
            records.append({'file':'central-park-walk.gif','size':[960,540],'frames':len(frames),
                            'frame_duration_ms':100,'setup':'Five seconds of mapped Right movement; actual park animation, no composited art.'})
            for record in records:
                path = output/record['file']
                record['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
                record['bytes'] = path.stat().st_size
            (output/'capture.json').write_text(json.dumps({'purpose':'Staged final-progress renderer review, not a full campaign playthrough',
                'isolated_saves':True,'crt':False,'drivers':'dummy','captures':records},indent=2)+'\n')
        finally:
            game.close();pygame.quit()
    print(f'Captured {len(records)} finale previews in {output}')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    capture(parser.parse_args().output)
