"""PURPOSE: Install a reviewed prototype interior with an archived transaction.
CALLED BY: python promote.py --family ID --master PNG --master-sha HASH --source PNG --source-sha HASH --output-dir NEW_DIR.
HOW TO MODIFY: Preserve exact pins, explicit target, archive, loader and existing-file checks.
"""
import argparse,hashlib,json
from pathlib import Path
import pygame
from video_game.engine import config
from video_game.engine.native_room_assets import load_native_opaque_backdrop
from video_game.engine.room_art_contracts import backdrop_manifest_template
from video_game.tools.build_room_family import build_backdrop_family

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--family',choices=('dodleston_relay_v1','ehman_1977_v1'),required=True)
    parser.add_argument('--master',type=Path,required=True);parser.add_argument('--master-sha',required=True)
    parser.add_argument('--source',type=Path,required=True);parser.add_argument('--source-sha',required=True)
    parser.add_argument('--output-dir',type=Path,required=True);args=parser.parse_args();args.output_dir.mkdir(parents=True,exist_ok=False)
    if sha(args.master)!=args.master_sha or sha(args.source)!=args.source_sha:raise ValueError('reviewed provenance mismatch')
    root=Path(config.ASSETS_DIR).resolve();env=root/'environments';target=env/args.family
    if target.exists() or target.is_symlink():raise ValueError('target family exists')
    originals={str(p.relative_to(root)):sha(p) for p in env.rglob('*') if p.is_file()}
    result=build_backdrop_family(args.family,assets_dir=root,archive_dir=args.output_dir/'archive',backdrop=args.source,promote=True)
    path=target/'manifest.json';doc=json.loads(path.read_text());asset=target/doc['backdrop']['file']
    if sha(asset)!=args.source_sha or doc['backdrop']['sha256']!=args.source_sha:raise ValueError('installed bytes mismatch')
    for name,digest in originals.items():
        if sha(root/name)!=digest:raise ValueError(f'existing environment changed: {name}')
    journal=root.parent/f'.{root.name}-asset-build-pending.json'
    if journal.exists() or journal.is_symlink():raise ValueError('pending journal')
    template=backdrop_manifest_template(args.family);pygame.init();pygame.display.set_mode((960,540))
    try:
        if load_native_opaque_backdrop(root,template['room_id'],template['world']) is None:raise ValueError('installed family invalid')
    finally:pygame.quit()
    result={'result':result,'master':str(args.master),'master_sha256':sha(args.master),'source':str(args.source),'source_sha256':sha(args.source),
            'manifest_sha256':sha(path),'existing_environment_sha256':originals,
            'limits':'No live-reader guarantee, human play, native-window or art-gate acceptance.'}
    (args.output_dir/'context.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
