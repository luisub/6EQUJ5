"""PURPOSE: Validate and safely promote a new galaxy transit bitmap family.
CALLED BY: python -m tools.build_galaxy_transit and focused tests.
HOW TO MODIFY: Preserve locking, source validation, staging and manifest-last promotion.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

from video_game.engine.asset_transactions import fcntl, promote_group
from video_game.engine.config import ASSETS_DIR
from video_game.engine.galaxy_transit_assets import FAMILY, IMAGES, validate_transit_image
from tools.build_approach_family import _check_pending, _no_symlinks


def build(galaxy_map, vortex, provenance, *, assets_dir=ASSETS_DIR, archive_dir=None, promote=False):
    """Validate two reviewed sources or atomically install an absent family."""
    if not isinstance(provenance, dict) or not provenance:
        raise ValueError('A nonempty provenance object is required')
    json.dumps(provenance, allow_nan=False)
    paths = {'galaxy_map': _no_symlinks(galaxy_map), 'vortex': _no_symlinks(vortex)}
    records = {}
    for name, (filename, dimensions, _) in IMAGES.items():
        data = paths[name].read_bytes()
        validate_transit_image(name, data)
        records[name] = {'file': filename, 'dimensions': list(dimensions),
                         'sha256': hashlib.sha256(data).hexdigest()}
    manifest = {'schema_version': 1, 'kind': 'galaxy_transit',
                'images': records, 'provenance': provenance}
    root = _no_symlinks(assets_dir)
    if not root.is_dir():
        raise FileNotFoundError(root)
    archive = _no_symlinks(archive_dir or (Path(__file__).resolve().parent.parent / '_trash' if root == ASSETS_DIR.resolve() else root.parent / '_trash'))
    if archive == root or archive.is_relative_to(root):
        raise ValueError('Archive must be outside the asset root')
    if fcntl is None:
        raise RuntimeError('Galaxy transit building requires fcntl locking')
    descriptor = os.open(root, os.O_RDONLY)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError('Another asset build is active') from exc
        if _check_pending(root):
            raise RuntimeError('Pending transaction requires recovery')
        target = _no_symlinks(root / FAMILY)
        if target.exists():
            raise FileExistsError(f'Galaxy transit family already exists: {target}')
        if not promote:
            return {'status': 'validated', 'manifest': manifest}
        with tempfile.TemporaryDirectory(prefix='galaxy-transit-stage-', dir=root.parent) as temporary:
            stage = Path(temporary)
            directory = stage / FAMILY
            directory.mkdir(parents=True)
            for name, (filename, _, _) in IMAGES.items():
                staged = directory / filename
                shutil.copyfile(paths[name], staged)
                data = staged.read_bytes()
                if hashlib.sha256(data).hexdigest() != records[name]['sha256']:
                    raise IOError('Staged image differs from reviewed source')
                validate_transit_image(name, data)
            (directory / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
            _no_symlinks(root / FAMILY)
            if (root / FAMILY).exists():
                raise FileExistsError('Galaxy transit family appeared during staging')
            members = tuple(FAMILY / info[0] for info in IMAGES.values()) + (FAMILY / 'manifest.json',)
            saved = promote_group(root, stage, archive, 'galaxy_transit_v1', members)
        return {'status': 'promoted', 'manifest': manifest, 'archive': str(saved)}
    finally:
        os.close(descriptor)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--galaxy-map', required=True, type=Path)
    parser.add_argument('--vortex', required=True, type=Path)
    parser.add_argument('--provenance', required=True, type=Path)
    parser.add_argument('--assets-dir', type=Path, default=ASSETS_DIR)
    parser.add_argument('--archive-dir', type=Path)
    parser.add_argument('--promote', action='store_true')
    args = parser.parse_args(argv)
    result = build(args.galaxy_map, args.vortex, json.loads(args.provenance.read_text(encoding='utf-8')),
                   assets_dir=args.assets_dir, archive_dir=args.archive_dir, promote=args.promote)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
