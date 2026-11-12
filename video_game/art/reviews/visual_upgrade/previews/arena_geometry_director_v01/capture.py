"""PURPOSE: Capture Greenkeeper arena geometry and disposable boss-entry stills.
CALLED BY: PYTHONPATH=. SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python capture.py --output-dir NEW_PATH.
HOW TO MODIFY: Keep actual boss initialization, temporary saves and direct-entry fixture disclosure.
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

parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',type=Path,required=True);out=parser.parse_args().output_dir
out.mkdir(parents=True,exist_ok=False)
pygame.init();pygame.display.set_mode((960,540))
try:
    level=Path('video_game/data/levels/act_01/greenkeeper_arena.json')
    room=Room.load_from_file(level);camera=Camera(room.width_px,room.height_px);camera.set_world_bounds(room.width_px,room.height_px)
    surface=pygame.Surface((room.width_px,room.height_px),pygame.SRCALPHA);surface.fill((10,16,24,255))
    room.render_tiles(surface,camera);room.render_objects(surface,camera)
    pygame.image.save(pygame.transform.scale(surface,(room.width_px*2,room.height_px*2)),out/'actual_room_geometry_1280x576.png')
    samples=[]
    with tempfile.TemporaryDirectory(prefix='6equj5-arena-guide-') as tmp:
        machine=GameStateMachine(CRTRenderer(scale=2),save_store=SaveStore(tmp),settings_store=SettingsStore(tmp))
        try:
            machine.start_new_game();machine.change_state(config.STATE_BOSS_BOUNTY)
            scene=machine.current_scene
            for _ in range(30):machine.input.begin_frame();machine.update(1/60)
            for cx in (0,160):
                scene.camera.x,scene.camera.y=cx,18;machine.render()
                path=out/f'camera_x{cx}_native_960.png';pygame.image.save(machine.crt.render_surface,path)
                samples.append({'camera':[cx,18],'player_rect':list(scene.player.rect),'grounded':scene.player.is_grounded,
                                'boss_rect':list(scene.boss.rect),'boss_phase':scene.boss.current_phase,'image':path.name})
        finally:machine.close()
    context={'driver':pygame.display.get_driver(),'room':str(level),'world_size':[room.width_px,room.height_px],
             'guide':'room.render_tiles + room.render_objects on opaque diagnostic background, nearest-scaled 2x; no boss, player, effects or HUD',
             'fixture':'new game, direct boss scene entry bypassing progression, temporary saves, 30 updates at 1/60 then force camera x0/160 y18; no updates between stills',
             'samples':samples,'limits':'static dummy fixtures; no earned route, all phases, motion, fairness, native display or performance acceptance'}
    (out/'context.json').write_text(json.dumps(context,indent=2)+'\n');print(json.dumps(samples,indent=2))
finally:pygame.quit()
