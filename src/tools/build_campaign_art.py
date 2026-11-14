"""PURPOSE: Validate and safely promote one new campaign art family.
CALLED BY: python -m video_game.tools.build_campaign_art and focused tests.
HOW TO MODIFY: Keep allowlists, validated sources, lock, journal and manifest-last promotion.

Examples: python -m video_game.tools.build_campaign_art --kind background
  --id neo_denver_v1 --source reviewed.png --provenance provenance.json
Add --promote only after review. Existing families cannot be replaced.
"""
import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

from PIL import Image
from video_game.engine.asset_transactions import fcntl, promote_group
from video_game.engine.campaign_scenery import BACKGROUND_IDS, BOSS_IDS, background_directory
from video_game.engine.config import ASSETS_DIR
from video_game.tools.asset_build_common import _check_pending, _no_symlinks

def build(kind, art_id, source, provenance, *, assets_dir=ASSETS_DIR, archive_dir=None, promote=False):
    if kind == 'background' and art_id in BACKGROUND_IDS:
        relative = background_directory(art_id)
        filename, dimensions, mode = 'background.png', (1920, 540), 'RGB'
        manifest = {'schema_version': 1, 'kind': 'campaign_world_background', 'art_id': art_id,
                    'viewport': [480, 270], 'density': 2}
    elif kind == 'boss' and art_id in BOSS_IDS:
        relative = Path('sprites/bosses/campaign') / art_id
        filename, dimensions, mode = 'body.png', (256, 192), 'RGBA'
        manifest = {'schema_version': 1, 'kind': 'campaign_boss', 'boss_id': art_id}
    else:
        raise ValueError('Unknown kind or family ID')
    if not isinstance(provenance, dict) or not provenance:
        raise ValueError('A nonempty provenance object is required')
    source = _no_symlinks(source)
    with Image.open(source) as image:
        image.load()
        if image.format != 'PNG' or image.size != dimensions or image.mode not in ({'RGB', 'RGBA'} if mode == 'RGB' else {'RGBA'}):
            raise ValueError(f'Source must be {mode} PNG at {dimensions}')
        if kind == 'background' and image.mode == 'RGBA' and image.getchannel('A').getextrema() != (255, 255):
            raise ValueError('Background must be opaque')
        if kind == 'boss':
            low, high = image.getchannel('A').getextrema()
            if low != 0 or high == 0:
                raise ValueError('Boss body requires transparent and visible pixels')
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    manifest['image'] = {'file': filename, 'dimensions': list(dimensions), 'sha256': digest}
    manifest['provenance'] = provenance
    root = _no_symlinks(assets_dir)
    if not root.is_dir():
        raise FileNotFoundError(root)
    archive = _no_symlinks(archive_dir or (Path(__file__).resolve().parents[2] / '_trash' if root == ASSETS_DIR.resolve() else root.parent / '_trash'))
    if archive == root or archive.is_relative_to(root):
        raise ValueError('Archive must be outside asset root')
    if fcntl is None:
        raise RuntimeError('Asset builder requires fcntl locking')
    descriptor = os.open(root, os.O_RDONLY)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError('Another asset build is active') from exc
        if _check_pending(root):
            raise RuntimeError('Pending transaction requires recovery')
        target = _no_symlinks(root / relative)
        if target.exists():
            raise FileExistsError(f'Campaign family already exists: {target}')
        if not promote:
            return {'status': 'validated', 'manifest': manifest}
        with tempfile.TemporaryDirectory(prefix='campaign-art-stage-', dir=root.parent) as temp:
            stage = Path(temp)
            directory = stage / relative
            directory.mkdir(parents=True)
            shutil.copyfile(source, directory / filename)
            if hashlib.sha256((directory / filename).read_bytes()).hexdigest() != digest:
                raise IOError('Staged image differs from reviewed source')
            (directory / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
            paths = (relative / filename, relative / 'manifest.json')
            _no_symlinks(root / relative)
            if (root / relative).exists():
                raise FileExistsError('Campaign family appeared during staging')
            saved = promote_group(root, stage, archive, f'campaign_{kind}_{art_id}', paths)
        return {'status': 'promoted', 'manifest': manifest, 'archive': str(saved)}
    finally:
        os.close(descriptor)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind', choices=('background', 'boss'), required=True)
    parser.add_argument('--id', required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--provenance', type=Path, required=True)
    parser.add_argument('--assets-dir', type=Path, default=ASSETS_DIR)
    parser.add_argument('--archive-dir', type=Path)
    parser.add_argument('--promote', action='store_true')
    args = parser.parse_args(argv)
    result = build(args.kind, args.id, args.source, json.loads(args.provenance.read_text()),
                   assets_dir=args.assets_dir, archive_dir=args.archive_dir, promote=args.promote)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
