"""PURPOSE: Capture actual scene entry using an isolated installed flash family.
CALLED BY: python capture.py --output-dir NEW_DIRECTORY.
HOW TO MODIFY: Preserve temporary asset/save roots, physical fire and exact context.
"""
import argparse
import hashlib
import json
import os
import random
import shutil
import sys
import tempfile
from pathlib import Path

import pygame
from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.firing_lighting import FLASH_FAMILY, FLASH_NAME
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine
from video_game.tools.build_firing_flash import build_flash

SOURCE = Path('video_game/art/reviews/visual_upgrade/previews/firing_flash_registration_v01/cell_v01/firing_flash_64x32.png')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    random.seed(17)
    pygame.init()
    pygame.display.set_mode((960, 540))
    records = []
    with tempfile.TemporaryDirectory(prefix='6equj5-flash-staged-', dir=Path(tempfile.gettempdir()).resolve()) as tmp:
        root = Path(tmp) / 'assets'
        shutil.copytree(config.ASSETS_DIR, root)
        if (root / FLASH_FAMILY).exists():
            shutil.rmtree(root / FLASH_FAMILY)
        result = build_flash(assets_dir=root, archive_dir=Path(tmp) / 'archive', source=SOURCE, promote=True)
        for facing in ('right', 'left'):
            save = Path(tmp) / ('save_' + facing)
            machine = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(save),
                                       settings_store=SettingsStore(save))
            try:
                machine.assets.root = root
                assert machine.start_new_game()[0]
                machine.change_state(config.STATE_FIELD_OPS, room='act_01/approach.json', spawn='approach_checkpoint')
                scene = machine.current_scene
                assert scene.firing_lighting is not None
                scene.enemy_manager.clear()
                scene.player.x, scene.player.y = 400, 208
                for _ in range(30):
                    machine.input.begin_frame()
                    machine.update(1 / 60)
                key = pygame.K_d if facing == 'right' else pygame.K_a
                machine.input.begin_frame()
                machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))
                machine.update(1 / 60)
                machine.handle_event(pygame.event.Event(pygame.KEYUP, key=key))
                for _ in range(20):
                    machine.input.begin_frame()
                    machine.update(1 / 60)
                assert scene.player.facing == facing and scene.player.is_grounded
                for label in ('before', 'shot'):
                    if label == 'shot':
                        machine.input.begin_frame()
                        machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_j))
                        machine.update(1 / 60)
                        machine.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_j))
                    scene.camera.x, scene.camera.y = 160, 18
                    machine.render()
                    image = args.output_dir / f'{facing}_{label}_native_960.png'
                    pygame.image.save(machine.crt.render_surface, str(image))
                    pygame.image.save(pygame.transform.scale(machine.crt.render_surface, (1920, 1080)),
                                      str(args.output_dir / f'{facing}_{label}_review_1920.png'))
                    records.append({'facing': facing, 'phase': label, 'file': image.name,
                                    'sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
                                    'flash_positions': [[f['x'], f['y']] for f in scene.effects.flashes]})
            finally:
                machine.close()
        context = {'argv': sys.argv, 'cwd': os.getcwd(), 'temporary_root': tmp,
                   'environment': {k: os.environ.get(k) for k in ('SDL_VIDEODRIVER', 'SDL_AUDIODRIVER', 'PYTHONPATH')},
                   'transaction': result, 'source': str(SOURCE),
                   'installed_sha256': hashlib.sha256((root / FLASH_FAMILY / FLASH_NAME).read_bytes()).hexdigest(),
                   'records': records, 'limitations': 'Dummy SDL, direct x=400 placement, camera (160,18), enemies removed, physical turn and J tap; not playback or native-window acceptance.'}
        (args.output_dir / 'context.json').write_text(json.dumps(context, indent=2) + '\n')
    pygame.quit()


if __name__ == '__main__':
    main()
