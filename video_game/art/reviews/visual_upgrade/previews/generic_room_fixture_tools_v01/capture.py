"""PURPOSE: Capture real field routing against a disposable reviewed room family.
CALLED BY: python capture.py --family ID --far PNG --world PNG [--prop PNG] --output-dir NEW_DIR.
HOW TO MODIFY: Retain the actual room renderer, temporary asset/save roots and source hashes.
"""
import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
import pygame
from video_game.engine import config
from video_game.engine.assets import AssetCache
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine
from video_game.tools.build_room_family import build_family

CASES = {
    'ohio_approach_v2': ('approach', ((0, 'bunker_exit'), (240, 'approach_checkpoint'), (480, 'dish_perimeter'))),
    'ohio_salvage_v1': ('salvage_yard', ((0, 'yard_entrance'), (80, 'yard_midpoint'), (160, 'yard_depot'))),
    'ohio_dish_v1': ('dish_catwalk', ((0, 'catwalk_start'), (80, 'catwalk_feedhorn'), (160, 'catwalk_feedhorn'))),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--family', choices=CASES, required=True)
    parser.add_argument('--far', type=Path, required=True)
    parser.add_argument('--world', type=Path, required=True)
    parser.add_argument('--prop', type=Path, action='append', default=[])
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix='6equj5-room-family-') as tmp:
        base = Path(tmp).resolve(); assets = base / 'assets'
        shutil.copytree(config.ASSETS_DIR, assets)
        result = build_family(args.family, assets_dir=assets, archive_dir=base/'archive',
                              far=args.far, world=args.world, props=args.prop, promote=True)
        pygame.init(); pygame.display.set_mode((960, 540))
        game = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(base/'save'),
                                settings_store=SettingsStore(base/'save'))
        try:
            game.assets = AssetCache(assets); game.start_new_game()
            name, cameras = CASES[args.family]
            game.change_state(config.STATE_FIELD_OPS, room=f'act_01/{name}.json', spawn=cameras[0][1])
            scene = game.current_scene
            if scene.native_approach is None:
                raise RuntimeError('family did not load')
            records = []
            for x, spawn in cameras:
                scene.reset_to_spawn(spawn)
                for _ in range(30): game.update(1/60)
                for y in (0, 18):
                    scene.camera.x = float(x); scene.camera.y = float(y); game.render()
                    native = args.output_dir/f'camera_x{x}_y{y}_960.png'
                    review = args.output_dir/f'camera_x{x}_y{y}_1920.png'
                    pygame.image.save(game.crt.render_surface, str(native))
                    pygame.image.save(pygame.transform.scale(game.crt.render_surface, (1920,1080)), str(review))
                    records.append({'camera':[x,y], 'spawn':spawn, 'player_rect':list(scene.player.rect),
                                    'native':native.name, 'sha256':sha(native), 'review':review.name})
            data = {'family':args.family, 'driver':pygame.display.get_driver(),
                    'fixture':'copied asset root; staged family and saves in temporary directory; direct entry, 30 ticks at each spawn and fixed camera',
                    'sources':[{'path':str(p), 'sha256':sha(p)} for p in [args.far,args.world,*args.prop]],
                    'promotion_status':result['status'], 'captures':records,
                    'limitations':'static dummy SDL captures only; no production promotion, native playback, normal-play, performance or art gate claim'}
            (args.output_dir/'context.json').write_text(json.dumps(data,indent=2)+'\n')
            print(json.dumps(data,indent=2))
        finally:
            game.close(); pygame.quit()


if __name__ == '__main__':
    main()
