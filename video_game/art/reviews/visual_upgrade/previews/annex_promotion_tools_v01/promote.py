"""PURPOSE: Install the reviewed annex backdrop in a recoverable transaction.
CALLED BY: python promote.py --output-dir NEW_DIR after staged review.
HOW TO MODIFY: Preserve master/export pins, explicit target, archive and existing-file checks.
"""
import argparse,hashlib,json
from pathlib import Path
import pygame
from video_game.engine import config
from video_game.engine.native_room_assets import load_native_opaque_backdrop
from video_game.tools.build_room_family import build_backdrop_family

MASTER=Path('video_game/art/source/visual_upgrade/candidates/annex_shared_background_v02/source/annex_shared_background_generated_master.png')
SOURCE=Path('video_game/art/reviews/visual_upgrade/previews/annex_registration_director_v02/capture_v01/annex_shared_background_960x576.png')
MASTER_SHA='6541fdaf3974dd7630ad7a44c1073c9c67a2f02cb5fab27572ac11dcb9d9a282'
SOURCE_SHA='b12ba8f554e5cdb9f237a9f1266ed3bae06c10c480272a3c605decf50269dd4a'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',type=Path,required=True);args=parser.parse_args();args.output_dir.mkdir(parents=True,exist_ok=False)
    if sha(MASTER)!=MASTER_SHA or sha(SOURCE)!=SOURCE_SHA:raise ValueError('reviewed provenance hash mismatch')
    root=Path(config.ASSETS_DIR).resolve();env=root/'environments';target=env/'mandela_annex_v1'
    if target.exists() or target.is_symlink():raise ValueError('target already exists')
    originals={str(p.relative_to(root)):sha(p) for p in env.rglob('*') if p.is_file()}
    result=build_backdrop_family('mandela_annex_v1',assets_dir=root,archive_dir=args.output_dir/'archive',backdrop=SOURCE,promote=True)
    manifest=target/'manifest.json';doc=json.loads(manifest.read_text());asset=target/doc['backdrop']['file']
    if sha(asset)!=SOURCE_SHA or doc['backdrop']['sha256']!=SOURCE_SHA:raise ValueError('installed bytes mismatch')
    for name,digest in originals.items():
        if sha(root/name)!=digest:raise ValueError(f'existing environment changed: {name}')
    journal=root.parent/f'.{root.name}-asset-build-pending.json'
    if journal.exists() or journal.is_symlink():raise ValueError('pending journal')
    pygame.init();pygame.display.set_mode((960,540))
    try:
        if load_native_opaque_backdrop(root,'act_01_mandela_test',(480,288)) is None:raise ValueError('installed family invalid')
    finally:pygame.quit()
    context={'result':result,'master_path':str(MASTER),'master_sha256':sha(MASTER),'source_path':str(SOURCE),'source_sha256':sha(SOURCE),
             'manifest_sha256':sha(manifest),'existing_environment_sha256':originals,
             'limits':'No live-reader guarantee, human play, native-window or art-gate acceptance.'}
    (args.output_dir/'context.json').write_text(json.dumps(context,indent=2)+'\n');print(json.dumps(context,indent=2))
if __name__=='__main__':main()
