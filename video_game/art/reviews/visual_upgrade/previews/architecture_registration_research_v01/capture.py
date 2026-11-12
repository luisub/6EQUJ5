"""PURPOSE: Capture a disposable two-plane registration fixture without modifying runtime assets.
CALLED BY: Run from the repository root with dummy SDL and --output-dir NEW_DIR.
HOW TO MODIFY: Preserve the fixed layer mapping, temporary saves, hashes and fresh-output guard.
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

ROOT = Path('video_game/art')
MASTER = ROOT / 'source/visual_upgrade/candidates/approach_world_architecture_v01/source/approach_world_architecture_generated_master.png'
FAR = ROOT / 'reviews/visual_upgrade/previews/approach_far_registration_v01/far_native_1152x544.png'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    with Image.open(MASTER) as src:
        if src.mode != 'RGBA' or src.size != (2172, 724):
            raise ValueError('Architecture master must be original 2172x724 RGBA')
        architecture = src.resize((1920, 576), Image.Resampling.LANCZOS)
    with Image.open(FAR) as far:
        if far.size != (1152, 544):
            raise ValueError('Far layer must be 1152x544')
    args.output_dir.mkdir(parents=True, exist_ok=False)
    arch_path = args.output_dir / 'architecture_full_rgba_1920x576.png'
    architecture.save(arch_path)
    results = []
    with tempfile.TemporaryDirectory(prefix='6equj5-architecture-fixture-') as tmp:
        pygame.init()
        pygame.display.set_mode((960, 540))
        game = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(tmp), settings_store=SettingsStore(tmp))
        try:
            game.start_new_game()
            game.change_state(config.STATE_FIELD_OPS)
            scene = game.current_scene
            for _ in range(30):
                game.update(1 / 60)
            far_surf = pygame.image.load(str(FAR)).convert_alpha()
            arch_surf = pygame.image.load(str(arch_path)).convert_alpha()
            def fixture_background(surface, camera):
                far_origin = (round(2 * 0.10 * camera.x), round(2 * 0.05 * camera.y))
                arch_origin = (round(2 * camera.x), round(2 * camera.y))
                far_crop = far_surf.subsurface(pygame.Rect(*far_origin, 960, 540))
                arch_crop = arch_surf.subsurface(pygame.Rect(*arch_origin, 960, 540))
                game.crt.composite_native(far_crop, (0, 0), (480, 270))
                game.crt.composite_native(arch_crop, (0, 0), (480, 270))
            scene.room.render_background = fixture_background
            for cx, spawn in ((0, 'bunker_exit'), (240, 'approach_checkpoint'), (480, 'dish_perimeter')):
                point = scene.room.spawns[spawn]
                scene.player.x, scene.player.y = point.x, point.y
                scene.player.facing = point.facing
                scene.camera.x, scene.camera.y = cx, 18
                game.render()
                native = args.output_dir / f'camera_x{cx}_y18_native_960.png'
                review = args.output_dir / f'camera_x{cx}_y18_review_1920.png'
                pygame.image.save(game.crt.render_surface, str(native))
                pygame.image.save(pygame.transform.scale(game.crt.render_surface, (1920, 1080)), str(review))
                results.append({'camera':[cx,18], 'far_crop_native':[round(0.2*cx),2,960,540],
                                'architecture_crop_native':[2*cx,36,960,540],
                                'fixture_player_spawn':spawn,'player_rect':list(scene.player.rect),
                                'native':native.name,'native_sha256':sha(native),
                                'review':review.name,'review_sha256':sha(review)})
            info = {'architecture_source':str(MASTER),'architecture_source_sha256':sha(MASTER),
                    'architecture_source_size':[2172,724],'architecture_source_mode':'RGBA',
                    'architecture_export':arch_path.name,'architecture_export_sha256':sha(arch_path),
                    'architecture_export_size':[1920,576],'architecture_export_mode':'RGBA',
                    'transform':'full-image Lanczos resize, no masks, crop, painting, cleanup or manual alpha changes; width/height ratio 3.0 to 3.3333 (+11.11%)',
                    'far_source':str(FAR),'far_source_sha256':sha(FAR),'far_source_size':[1152,544],
                    'mapping':'far native crop round(2*.1*camera_x), round(2*.05*camera_y); architecture crop round(2*camera_x), round(2*camera_y); each 960x540',
                    'composition':'fixture-local room.render_background callback composites both native layers behind actual room tiles and objects, actors, effects, weather and HUD; original runtime Mateo animator; no replacement or promotion',
                    'fixture':'dummy display and audio; temporary saves; new game, direct field entry, 30 updates at 1/60; manually set camera and authored spawn for each still; no update between stills',
                    'outputs':results,'limitations':'static fixtures; teleported actor/camera are not normal-input play, motion, alignment acceptance, performance, native-window or art-gate evidence'}
            (args.output_dir / 'context.json').write_text(json.dumps(info, indent=2)+'\n')
            print(json.dumps(info, indent=2))
        finally:
            game.close()
            pygame.quit()


if __name__ == '__main__':
    main()
