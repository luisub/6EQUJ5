"""PURPOSE: Record a disposable headless runtime motion inspection.
CALLED BY: python capture.py --output-dir NEW_PATH from repository root with dummy SDL.
HOW TO MODIFY: Preserve event timings and fixture disclosure in the context JSON.
"""
import argparse
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

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir', type=Path, required=True)
out = parser.parse_args().output_dir
out.mkdir(parents=True, exist_ok=False)
actions = {
    8: [(pygame.KEYDOWN, pygame.K_d)],
    45: [(pygame.KEYDOWN, pygame.K_x)],
    70: [(pygame.KEYUP, pygame.K_x)],
    75: [(pygame.KEYDOWN, pygame.K_SPACE)],
    100: [(pygame.KEYUP, pygame.K_SPACE)],
    125: [(pygame.KEYDOWN, pygame.K_c)],
    145: [(pygame.KEYUP, pygame.K_c)],
    165: [(pygame.KEYDOWN, pygame.K_F2)],
    166: [(pygame.KEYUP, pygame.K_F2)],
    190: [(pygame.KEYDOWN, pygame.K_F2)],
    191: [(pygame.KEYUP, pygame.K_F2)],
    192: [(pygame.KEYDOWN, pygame.K_d)],
    235: [(pygame.KEYDOWN, pygame.K_SPACE)],
    255: [(pygame.KEYUP, pygame.K_SPACE)],
    290: [(pygame.KEYUP, pygame.K_d)],
}
with tempfile.TemporaryDirectory(prefix='6equj5-motion-') as tmp:
    pygame.init()
    pygame.display.set_mode((960, 540))
    machine = GameStateMachine(CRTRenderer(scale=2), save_store=SaveStore(tmp), settings_store=SettingsStore(tmp))
    try:
        machine.start_new_game()
        machine.change_state(config.STATE_FIELD_OPS)  # explicit entry fixture
        field = machine.current_scene
        frames, trace = [], []
        for frame in range(300):
            machine.input.begin_frame()
            for kind, key in actions.get(frame, []):
                machine.handle_event(pygame.event.Event(kind, key=key))
            machine.update(1/60)
            machine.render()
            if frame % 5 == 0:
                s = machine.crt.render_surface
                frames.append(Image.frombytes('RGB', s.get_size(), pygame.image.tobytes(s, 'RGB')))
                trace.append({'frame':frame, 'player':[round(field.player.x, 2),round(field.player.y, 2)],
                              'camera':[round(field.camera.x, 2),round(field.camera.y, 2)],
                              'animation':field.player.animation_state,'health':field.player.health,
                              'paused':machine.pause.active})
            if frame == 30:
                window = pygame.Surface((1920,1080))
                machine.crt.is_crt_enabled = False; machine.crt.present(window)
                pygame.image.save(window, out/'present_crt_off_1920.png')
                machine.crt.is_crt_enabled = True; machine.crt.present(window)
                pygame.image.save(window, out/'present_crt_on_1920.png')
        frames[0].save(out/'actual_motion_960.gif', save_all=True, append_images=frames[1:], duration=83, loop=0, optimize=False)
        metadata = {'driver':pygame.display.get_driver(), 'fixture':'new game; direct field entry, no campaign progression, temporary save',
                    'timestep':'1/60 s; 300 updates; synthetic KEYDOWN/KEYUP events through GameStateMachine input mapping',
                    'sampling':'one native frame every 5 updates; GIF requested delay 83 ms; encoder quantizes and may coalesce duplicate frames',
                    'crt_stills':'same rendered frame via actual present(), CRT off/on, 2x display',
                    'events':{str(k):[(pygame.event.event_name(kind),pygame.key.name(key)) for kind,key in v] for k,v in actions.items()},
                    'trace':trace,'limitations':'headless scripted motion and static effect evidence only, no native display, human play, fairness, audio, or FPS claim'}
        (out/'context.json').write_text(json.dumps(metadata,indent=2)+'\n')
        print('saved',len(frames),'frames; player and camera samples:',trace[0],trace[-1])
    finally:
        machine.close(); pygame.quit()
