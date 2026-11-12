"""PURPOSE: Register corrected annex backdrop in actual timeline geometry fixtures.
CALLED BY: From repo root with dummy SDL and --output-dir NEW_DIR.
HOW TO MODIFY: Preserve full source, temporary saves and explicit injected platform endpoints.
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

SOURCE = Path('video_game/art/source/visual_upgrade/candidates/annex_shared_background_v02/source/annex_shared_background_generated_master.png')
EXPECTED_SHA = '6541fdaf3974dd7630ad7a44c1073c9c67a2f02cb5fab27572ac11dcb9d9a282'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir', type=Path, required=True)
    args = p.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    if sha(SOURCE) != EXPECTED_SHA:
        raise ValueError('Unexpected source hash')
    export = args.output_dir / 'annex_shared_background_960x576.png'
    with Image.open(SOURCE) as src:
        if src.mode != 'RGB' or src.size != (1619, 971):
            raise ValueError(f'Unexpected source {src.mode} {src.size}')
        src.resize((960, 576), Image.Resampling.LANCZOS).save(export)
    pygame.init()
    pygame.display.set_mode((960, 540))
    try:
        with tempfile.TemporaryDirectory(prefix='6equj5-annex-v02-') as tmp:
            game = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(tmp), settings_store=SettingsStore(tmp))
            try:
                game.start_new_game()
                game.change_state(config.STATE_FIELD_OPS)
                scene = game.current_scene
                samples = []
                for timeline in ('2029_CORE', '1977_ANALOG'):
                    scene.load_room('act_01/mandela_test.json', spawn_name='default')
                    if not scene.room.set_active_timeline(timeline):
                        raise ValueError(timeline)
                    scene.reality.world.active_timeline = timeline
                    for _ in range(30):
                        game.input.begin_frame()
                        game.update(1 / 60)
                    platforms = list(scene.reality.world.moving_platforms.values())
                    if len(platforms) != 1 or len(platforms[0].waypoints) != 2:
                        raise ValueError('Unexpected platform inventory')
                    platform = platforms[0]
                    plate = pygame.image.load(str(export)).convert()
                    def background(_surface, camera):
                        source_y = round(2 * camera.y)
                        game.crt.composite_native(plate.subsurface(pygame.Rect(0, source_y, 960, 540)), (0, 0), (480, 270))
                    scene.room.render_background = background
                    for endpoint, (px, py) in enumerate(platform.waypoints):
                        platform.x, platform.y = px, py
                        for cy in (0, 18):
                            scene.camera.x, scene.camera.y = 0, cy
                            game.render()
                            stem = f'{timeline}_endpoint{endpoint}_y{cy}'
                            native = args.output_dir / f'{stem}_native_960.png'
                            review = args.output_dir / f'{stem}_review_1920.png'
                            pygame.image.save(game.crt.render_surface, str(native))
                            pygame.image.save(pygame.transform.scale(game.crt.render_surface, (1920, 1080)), str(review))
                            samples.append({'timeline': timeline, 'camera': [0, cy], 'player_rect': list(scene.player.rect),
                                            'grounded': scene.player.is_grounded, 'platform_id': platform.id,
                                            'injected_platform_world': [px, py], 'native': native.name,
                                            'native_sha256': sha(native), 'review': review.name, 'review_sha256': sha(review)})
                info = {'source': str(SOURCE), 'source_size': [1619, 971], 'source_sha256': sha(SOURCE),
                        'export': export.name, 'export_sha256': sha(export),
                        'transform': 'Full 1619x971 image Lanczos-resized to 960x576; full canvas retained; near-matching aspect, no masks, painting or cleanup.',
                        'composition': 'Fixture-local room callback draws source crop at y=2*camera.y, then actual MandelaWorld tiles, platforms, active objects, weather/transition and normal field actor/HUD.',
                        'fixture': 'Dummy SDL, temporary saves, direct annex spawn and timeline; 30 updates at 1/60, then manually set platform to each authored waypoint and force camera y=0/18 without additional updates.',
                        'limits': 'Static injected endpoints only; no movement, real timeline swap, collected/open state, native window, playthrough, performance or art-gate acceptance.',
                        'samples': samples}
                (args.output_dir / 'context.json').write_text(json.dumps(info, indent=2) + '\n')
                print(json.dumps(samples, indent=2))
            finally:
                game.close()
    finally:
        pygame.quit()

if __name__ == '__main__':
    main()
