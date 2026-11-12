"""PURPOSE: Install reviewed room families with independent archived transactions.
CALLED BY: python promote.py --output-dir NEW_DIR with dummy SDL and no active game.
HOW TO MODIFY: Keep source pins, absence checks, manifest-last builder and postvalidation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pygame
from video_game.engine import config
from video_game.engine.native_room_assets import load_native_room_family
from video_game.tools.build_room_family import build_family

P = Path('video_game/art/reviews/visual_upgrade/previews')
FAR = (P/'approach_far_registration_v01/far_native_1152x544.png', 'f57b938219cb4d228ad3f6339a854b2cc770bf15b97bdb36f83a1df31997718e')
CASES = [
 ('ohio_approach_v2', 'act_01_approach', (960,288),
  (P/'architecture_registration_research_v02/crop_top_left_v01/architecture_rgba_1920x576.png','cffef0606db604f55a5821a3a8cce467dbd32b2efda80cfb22183d167398e4e3'),
  [(P/'approach_equipment_registration_v01/render_v01/equipment_112x64_rgba.png','0c8431ad457f575f50288811b1468d5c3b26f6f31668cea510eab2d67aee3476')]),
 ('ohio_salvage_v1', 'act_01_salvage_yard', (640,288),
  (P/'salvage_registration_director_v02/capture_v01/yard_world_layer_1280x576.png','023b441b8c784b78277722926b6c242243a8f195d8ad6cc2f76937cdae8f50c6'),
  [(P/'salvage_wagon_registration_v01/render_v01/wagon_168x76_rgba.png','ac8fce6cdd8edc41fca57a180c4faed0cbf1524b9fef6aea74d1d288a8e0d3ee')]),
 ('ohio_dish_v1', 'act_01_dish_catwalk', (640,288),
  (P/'dish_registration_director_v01/capture_v01/dish_world_layer_1280x576.png','1bd2262000bf17f87da1c13b1c865796416b061006b82c673b9beadc3303b8cc'), []),
]


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True); args=parser.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=False)
    root=Path(config.ASSETS_DIR).resolve()
    original=root/'environments/ohio_approach_v1'
    before={p.name:digest(p) for p in original.iterdir() if p.is_file()}
    for family,_,_,world,props in CASES:
        if (root/'environments'/family).exists(): raise RuntimeError(f'family already exists: {family}')
        for path,expected in [FAR,world,*props]:
            if digest(path)!=expected: raise RuntimeError(f'source hash mismatch: {path}')
    pygame.init();pygame.display.set_mode((960,540)); records=[]
    try:
        for family,room,size,world,props in CASES:
            result=build_family(family,assets_dir=root,archive_dir=args.output_dir/'archive',far=FAR[0],world=world[0],props=[p[0] for p in props],promote=True)
            manifest=root/'environments'/family/'manifest.json'; data=json.loads(manifest.read_text())
            for entry in data['layers']+data['props']:
                if digest(manifest.parent/entry['file'])!=entry['sha256']: raise RuntimeError('installed hash mismatch')
            if load_native_room_family(root,room,size) is None: raise RuntimeError('installed loader rejected family')
            journal=root.parent/f'.{root.name}-asset-build-pending.json'
            if journal.exists() or journal.is_symlink():raise RuntimeError('pending journal remains')
            records.append({'family':family,'result':result,'manifest_sha256':digest(manifest),
                            'file_sha256':{entry['file']:entry['sha256'] for entry in data['layers']+data['props']}})
            (args.output_dir/'progress.json').write_text(json.dumps(records,indent=2)+'\n')
        after={p.name:digest(p) for p in original.iterdir() if p.is_file()}
        if before!=after:raise RuntimeError('installed approach v1 changed')
        (args.output_dir/'context.json').write_text(json.dumps({'records':records,'approach_v1_unchanged_sha256':before,
          'limitations':'Independent locked transactions, not atomic across all three families. No live-reader guarantee or normal-play acceptance. Approved far reused as interim room sky.'},indent=2)+'\n')
        print(json.dumps(records,indent=2))
    finally:pygame.quit()


if __name__=='__main__':main()
