"""PURPOSE: Install the reviewed bunker backdrop with a recoverable asset transaction.
CALLED BY: python promote.py --output-dir NEW_DIR after actual-scene review.
HOW TO MODIFY: Preserve source pin, pre-existing-family refusal, lock, archive and verification.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pygame
from video_game.engine import config
from video_game.engine.native_room_assets import load_native_opaque_backdrop
from video_game.tools.build_room_family import build_backdrop_family

SOURCE=Path('video_game/art/reviews/visual_upgrade/previews/bunker_registration_director_v01/capture_v01/bunker_background_960x540.png')
SHA='cc9749e5373fbf97122426daf7e418aa21f77655e14077e399112c1256b74e40'
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',required=True,type=Path);args=parser.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=False)
    root=Path(config.ASSETS_DIR).resolve();family=root/'environments/ohio_bunker_v1'
    if family.exists() or family.is_symlink():raise ValueError('target family already exists')
    if digest(SOURCE)!=SHA:raise ValueError('reviewed source hash mismatch')
    old_root=root/'bunker';original={str(p.relative_to(root)):digest(p) for p in old_root.rglob('*') if p.is_file()}
    result=build_backdrop_family('ohio_bunker_v1',assets_dir=root,archive_dir=args.output_dir/'archive',backdrop=SOURCE,promote=True)
    manifest=family/'manifest.json';doc=json.loads(manifest.read_text());backdrop=family/doc['backdrop']['file']
    if digest(backdrop)!=SHA or doc['backdrop']['sha256']!=SHA:raise ValueError('installed hash mismatch')
    after={str(p.relative_to(root)):digest(p) for p in old_root.rglob('*') if p.is_file()}
    if original!=after:raise ValueError('legacy bunker files changed')
    journal=root.parent/f'.{root.name}-asset-build-pending.json'
    if journal.exists() or journal.is_symlink():raise ValueError('pending asset journal')
    pygame.init();pygame.display.set_mode((960,540))
    try:
        if load_native_opaque_backdrop(root,'bunker_hub',(480,270)) is None:raise ValueError('installed backdrop rejected')
    finally:pygame.quit()
    info={'result':result,'manifest_sha256':digest(manifest),'backdrop_sha256':digest(backdrop),
          'legacy_bunker_sha256':original,'limits':'No live-reader guarantee; no human, normal gameplay, native-window or art gate acceptance.'}
    (args.output_dir/'context.json').write_text(json.dumps(info,indent=2)+'\n');print(json.dumps(info,indent=2))

if __name__=='__main__':main()
