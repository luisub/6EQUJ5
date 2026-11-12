"""PURPOSE: Isolate actor and architecture response in one unchanged physical-shot state.
CALLED BY: python measure.py --output-dir NEW_DIRECTORY.
HOW TO MODIFY: Keep the same scene state and separately suppress only the measured light pass.
"""
import argparse
import json
import os
import random
import sys
import tempfile
from pathlib import Path

import pygame
from PIL import Image, ImageChops, ImageStat
from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine


def stats(lit, muted):
    diff = ImageChops.difference(lit, muted)
    pixels = [pixel for pixel in diff.getdata() if pixel != (0, 0, 0)]
    return {'changed_pixels': len(pixels), 'maximum_rgb_delta': [max((p[c] for p in pixels), default=0) for c in range(3)],
            'mean_rgb_delta_over_changed_pixels': [round(sum(p[c] for p in pixels) / len(pixels), 2) if pixels else 0 for c in range(3)],
            'bounding_box': diff.getbbox()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    random.seed(17)
    pygame.init()
    pygame.display.set_mode((960, 540))
    results = {}
    with tempfile.TemporaryDirectory(prefix='6equj5-light-delta-') as tmp:
        for facing in ('right', 'left'):
            save = Path(tmp) / facing
            machine = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(save), settings_store=SettingsStore(save))
            try:
                assert machine.start_new_game()[0]
                machine.change_state(config.STATE_FIELD_OPS, room='act_01/approach.json', spawn='approach_checkpoint')
                scene = machine.current_scene
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
                assert scene.firing_lighting and scene.player.facing == facing
                machine.input.begin_frame()
                machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_j))
                machine.update(1 / 60)
                machine.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_j))
                scene.camera.x, scene.camera.y = 160, 18
                light = scene.firing_lighting
                original_world, original_actor = light.render_world_bounce, light.light_actor

                def capture():
                    machine.render()
                    return Image.frombytes('RGB', (960, 540), pygame.image.tobytes(machine.crt.render_surface, 'RGB'))

                full = capture()
                light.render_world_bounce = lambda *_: None
                muted_world = capture()
                light.render_world_bounce = original_world
                light.light_actor = lambda sprite, *_: sprite
                muted_actor = capture()
                light.light_actor = original_actor
                results[facing] = {'architecture_response': stats(full, muted_world),
                                   'actor_response': stats(full, muted_actor),
                                   'flash_world': [scene.effects.flashes[-1]['x'], scene.effects.flashes[-1]['y']]}
            finally:
                machine.close()
        report = {'argv': sys.argv, 'cwd': os.getcwd(), 'temporary_save_root': tmp,
                  'environment': {k: os.environ.get(k) for k in ('SDL_VIDEODRIVER', 'SDL_AUDIODRIVER', 'PYTHONPATH')},
                  'results': results,
                  'method': 'Same actual rendered shot state and camera; temporarily suppress just one render pass without advancing time. Other effects, burst and HUD remain present. RGB deltas are absolute 8-bit channel values over changed final-frame pixels.',
                  'limitations': 'Dummy SDL, direct x=400 setup, enemies cleared, one physical tap per facing; no motion or native performance claim.'}
        (args.output_dir / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(results, indent=2))
    pygame.quit()


if __name__ == '__main__':
    main()
