"""PURPOSE: Reproduce a registered Ohio background and optional pose study.
CALLED BY: PYTHONPATH=. SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python compose_registered_v01.py --background MASTER --output-dir NEW_PATH [--sprite CELL]
HOW TO MODIFY: Retain source hashes, temporary saves, explicit fixture and refusal to overwrite.
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


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--background', type=Path, required=True)
    parser.add_argument('--sprite', type=Path, help='Optional transparent RGBA 48x64 registered idle cell')
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    background = Image.open(args.background).convert('RGB')
    background_size = background.size
    sprite_hash = None
    if args.sprite:
        with Image.open(args.sprite) as pose:
            if pose.size != (48, 64) or pose.mode != 'RGBA':
                parser.error('sprite must be a 48x64 RGBA cell')
        sprite_hash = digest(args.sprite)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    plate_path = args.output_dir / 'background_960.png'
    background.resize((960, 540), Image.Resampling.LANCZOS).save(plate_path)
    with tempfile.TemporaryDirectory(prefix='6equj5-bg-study-') as tmp:
        pygame.init(); pygame.display.set_mode((960, 540))
        game = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(tmp), settings_store=SettingsStore(tmp))
        try:
            game.start_new_game(); game.change_state(config.STATE_FIELD_OPS)
            scene = game.current_scene
            for _ in range(30): game.update(1 / 60)
            plate = pygame.image.load(str(plate_path)).convert()
            # Fixture-local insertion: all actual scene layers retain their order.
            scene.room.render_background = lambda surface, camera: game.crt.composite_native(plate, (0, 0), (480, 270))
            if args.sprite:
                sprite = pygame.image.load(str(args.sprite)).convert_alpha()
                scene.player.animator.surface_for_density = lambda density: pygame.transform.scale(sprite, (24 * density, 32 * density))
            game.render()
            native = args.output_dir / 'study_native_960.png'
            scaled = args.output_dir / 'study_review_1920.png'
            pygame.image.save(game.crt.render_surface, str(native))
            pygame.image.save(pygame.transform.scale(game.crt.render_surface, (1920, 1080)), str(scaled))
            player = scene.player
            info = {'background_source':str(args.background), 'background_sha256':digest(args.background),
                    'background_source_size':background_size, 'background_export_sha256':digest(plate_path),
                    'background_transform':'full image Lanczos resize to 960x540; small aspect adjustment; no crop or painting',
                    'sprite_source':str(args.sprite) if args.sprite else None, 'sprite_sha256':sprite_hash,
                    'sprite_placement':'48x64 cell at native (88,382); world foot (56,240), nominal pivot (24,62)' if args.sprite else 'existing Mateo 96x128 source sampled directly to 48x64',
                    'fixture':'dummy driver; new game, direct field entry, 30 updates at 1/60, temporary save',
                    'camera':[scene.camera.x,scene.camera.y], 'world_view':[scene.camera.x,scene.camera.y,480,270],
                    'player_rect':list(player.rect), 'native_sha256':digest(native), 'review_sha256':digest(scaled),
                    'composition':'native background before actual runtime room tiles, objects, enemies, Mateo, effects, weather and HUD',
                    'limitations':'static fixture only; no art promotion, native window, playback, parallax, seamlessness or gate verdict'}
            (args.output_dir/'context.json').write_text(json.dumps(info, indent=2)+'\n')
            print(json.dumps(info, indent=2))
        finally:
            game.close(); pygame.quit()


if __name__ == '__main__':
    main()
