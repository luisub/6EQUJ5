"""PURPOSE: Capture a disposable dish-catwalk room geometry guide and camera fixtures.
CALLED BY: PYTHONPATH=. SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python capture.py --output-dir NEW_PATH from repository root.
HOW TO MODIFY: Keep temporary saves, explicit fixture disclosures and fresh output paths.
"""
import argparse
import json
import tempfile
from pathlib import Path
import pygame
from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.world import Room, Camera

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir', type=Path, required=True)
out = parser.parse_args().output_dir
out.mkdir(parents=True, exist_ok=False)
pygame.init()
pygame.display.set_mode((960, 540))
try:
    level = Path('video_game/data/levels/act_01/dish_catwalk.json')
    room = Room.load_from_file(level)
    camera = Camera(room.width_px, room.height_px)
    camera.set_world_bounds(room.width_px, room.height_px)
    logical = pygame.Surface((room.width_px, room.height_px), pygame.SRCALPHA)
    logical.fill((10, 16, 24, 255))
    room.render_tiles(logical, camera)
    room.render_objects(logical, camera)
    pygame.image.save(pygame.transform.scale(logical, (room.width_px * 2, room.height_px * 2)), out / 'actual_room_geometry_1280x576.png')
    samples = []
    with tempfile.TemporaryDirectory(prefix='6equj5-dish-guide-') as temp:
        machine = GameStateMachine(CRTRenderer(scale=2), save_store=SaveStore(temp), settings_store=SettingsStore(temp))
        try:
            machine.start_new_game()
            machine.change_state(config.STATE_FIELD_OPS)
            scene = machine.current_scene
            scene.load_room('act_01/dish_catwalk.json', spawn_name='catwalk_start')
            for spawn, cam_x in [('catwalk_start', 0), ('catwalk_feedhorn', 160)]:
                scene.reset_to_spawn(spawn)
                for _ in range(30):
                    machine.input.begin_frame()
                    machine.update(1 / 60)
                scene.camera.x = cam_x
                scene.camera.y = 18
                machine.render()
                filename = f'{spawn}_camera_x{cam_x}_native_960.png'
                pygame.image.save(machine.crt.render_surface, out / filename)
                samples.append({'spawn': spawn, 'camera': [scene.camera.x, scene.camera.y],
                                'player_rect': list(scene.player.rect), 'grounded': scene.player.is_grounded,
                                'image': filename, 'defense_active': bool(scene.holdout and scene.holdout.is_active)})
        finally:
            machine.close()
    context = {'driver': pygame.display.get_driver(), 'room': str(level), 'room_world_size': [room.width_px, room.height_px],
               'guide': 'room.render_tiles + room.render_objects at world origin on an opaque diagnostic backing, nearest-scaled 2x; no background, actor, HUD or scene-drawn pickup/effects',
               'fixtures': 'new game, direct field then direct dish-catwalk load; temporary saves; reset named spawn and 30 updates at 1/60; camera explicitly positioned; scripted fixture, not a played route; fresh game lacks repaired feedhorn, so defense does not start',
               'samples': samples,
               'limits': 'guide is not artwork or a normal route; real interactive/conditional cues, motion, native window, performance, audio and human play remain unverified'}
    (out / 'context.json').write_text(json.dumps(context, indent=2) + '\n')
    print(json.dumps(samples, indent=2))
finally:
    pygame.quit()
