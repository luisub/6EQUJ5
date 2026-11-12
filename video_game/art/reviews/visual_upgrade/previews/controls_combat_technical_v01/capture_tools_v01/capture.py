"""PURPOSE: Capture initial integrated pointer fire and the accessible settings selector.
CALLED BY: python capture.py --output-dir NEW_DIRECTORY.
HOW TO MODIFY: Keep physical mouse events, isolated saves and explicit fixture limitations.
"""
import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
import pygame
from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    pygame.init()
    pygame.display.set_mode((1920,1080))
    records = []
    with tempfile.TemporaryDirectory(prefix='6equj5-control-capture-') as tmp:
        for legacy in (False, True):
            root = Path(tmp) / ('legacy' if legacy else 'fresh')
            root.mkdir()
            if legacy:
                (root / 'settings.json').write_text(json.dumps({'schema_version':2, 'volume':70, 'crt_effects':True, 'scale':2}))
            machine = GameStateMachine(CRTRenderer(scale=2), save_store=SaveStore(root), settings_store=SettingsStore(root))
            try:
                assert machine.start_new_game()[0]
                machine.change_state(config.STATE_FIELD_OPS, room='act_01/approach.json', spawn='approach_checkpoint')
                scene = machine.current_scene
                scene.enemy_manager.clear()
                scene.player.x, scene.player.y = 400, 208
                for _ in range(30):
                    machine.input.begin_frame()
                    machine.update(1/60)
                scene.camera.x, scene.camera.y = 160, 18
                assert scene.player.is_grounded
                # Cursor points upward and forward in the actual 1920×1080 viewport.
                target = (int(345 * machine.crt.win_w / config.INTERNAL_WIDTH),
                          int(125 * machine.crt.win_h / config.INTERNAL_HEIGHT))
                spawns = []
                original = scene.projectile_manager.spawn
                def record(*a, **kw):
                    projectile = original(*a, **kw)
                    spawns.append({'id':projectile.id, 'x':projectile.x, 'y':projectile.y,
                                   'dir_x':projectile.dir_x, 'dir_y':projectile.dir_y,
                                   'damage':projectile.damage, 'primary':projectile.is_primary_discharge})
                    return projectile
                scene.projectile_manager.spawn = record
                machine.input.begin_frame()
                machine.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=target, rel=(0,0), buttons=(0,0,0)))
                machine.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=target, button=1))
                machine.update(1/60)
                scene.camera.x, scene.camera.y = 160, 18
                machine.render()
                name = 'legacy_classic' if legacy else 'fresh_assisted'
                image = args.output_dir / f'{name}_angled_fire_960.png'
                pygame.image.save(machine.crt.render_surface, str(image))
                pygame.image.save(pygame.transform.scale(machine.crt.render_surface,(1920,1080)), str(args.output_dir / f'{name}_angled_fire_1920.png'))
                assert len(spawns) == (1 if legacy else 3)
                assert spawns[0]['dir_y'] < 0 and spawns[0]['primary']
                machine.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP,pos=target,button=1))
                machine.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F2))
                machine.render()
                pause = args.output_dir / f'{name}_pause_960.png'
                pygame.image.save(machine.crt.render_surface,str(pause))
                records.append({'mode':machine.settings.combat_mode, 'legacy_settings':legacy,
                                'target_window':target, 'camera':[160,18], 'spawns':spawns,
                                'image':image.name, 'sha256':hashlib.sha256(image.read_bytes()).hexdigest(),
                                'pause':pause.name})
            finally:
                machine.close()
        report = {'argv':sys.argv, 'cwd':os.getcwd(), 'temporary_save_root':tmp,
                  'environment':{k:os.environ.get(k) for k in ('SDL_VIDEODRIVER','SDL_AUDIODRIVER','PYTHONPATH')},
                  'records':records,
                  'limitations':'Dummy SDL and direct x=400 fixture, enemies cleared; mouse events route through the actual GameStateMachine. Static captures are not human gameplay or physical-controller review.'}
        (args.output_dir/'context.json').write_text(json.dumps(report,indent=2)+'\n')
    pygame.quit()


if __name__ == '__main__':
    main()
