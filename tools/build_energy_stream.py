"""PURPOSE: Validate and safely promote one new compact energy-stream family.
CALLED BY: python -m tools.build_energy_stream and focused tests.
HOW TO MODIFY: Preserve allowlisted paths, lock/journal, staging and manifest-last order.
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
from video_game.engine.energy_stream_assets import DIMENSIONS, FAMILY, FAMILIES, IMAGE_NAME, PIVOT, validate_stream_bytes
from tools.build_approach_family import _check_pending, _no_symlinks


def build(source, provenance, *, assets_dir=ASSETS_DIR, archive_dir=None, promote=False, version=1):
    """Validate a complete reviewed source or promote it into an absent family."""
    if type(version) is not int or version not in FAMILIES:
        raise ValueError('Energy-stream version must be 1 or 2')
    family = FAMILIES[version]
    if not isinstance(provenance, dict) or not provenance:
        raise ValueError('A nonempty provenance object is required')
    json.dumps(provenance, allow_nan=False)
    source = _no_symlinks(source)
    data = source.read_bytes()
    validate_stream_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    manifest = {'schema_version': 1, 'kind': 'energy_filament', 'density': 2,
                'pivot': list(PIVOT),
                'image': {'file': IMAGE_NAME, 'dimensions': list(DIMENSIONS), 'sha256': digest},
                'provenance': provenance}
    root = _no_symlinks(assets_dir)
    if not root.is_dir():
        raise FileNotFoundError(root)
    archive = _no_symlinks(archive_dir or (Path(__file__).resolve().parent.parent / '_trash' if root == ASSETS_DIR.resolve() else root.parent / '_trash'))
    if archive == root or archive.is_relative_to(root):
        raise ValueError('Archive must be outside the asset root')
    if fcntl is None:
        raise RuntimeError('Energy-stream building requires fcntl locking')
    descriptor = os.open(root, os.O_RDONLY)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError('Another asset build is active') from exc
        if _check_pending(root):
            raise RuntimeError('Pending transaction requires recovery')
        target = _no_symlinks(root / family)
        if target.exists():
            raise FileExistsError(f'Energy-stream family already exists: {target}')
        if not promote:
            return {'status': 'validated', 'manifest': manifest}
        with tempfile.TemporaryDirectory(prefix='energy-stream-stage-', dir=root.parent) as temporary:
            stage = Path(temporary)
            directory = stage / family
            directory.mkdir(parents=True)
            staged = directory / IMAGE_NAME
            shutil.copyfile(source, staged)
            staged_data = staged.read_bytes()
            if hashlib.sha256(staged_data).hexdigest() != digest:
                raise IOError('Staged image differs from reviewed source')
            validate_stream_bytes(staged_data)
            (directory / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
            _no_symlinks(root / family)
            if (root / family).exists():
                raise FileExistsError('Energy-stream family appeared during staging')
            paths = (family / IMAGE_NAME, family / 'manifest.json')
            saved = promote_group(root, stage, archive, f'energy_filament_v{version}', paths)
        return {'status': 'promoted', 'manifest': manifest, 'archive': str(saved)}
    finally:
        os.close(descriptor)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--provenance', required=True, type=Path)
    parser.add_argument('--assets-dir', type=Path, default=ASSETS_DIR)
    parser.add_argument('--archive-dir', type=Path)
    parser.add_argument('--promote', action='store_true')
    parser.add_argument('--version', type=int, choices=(1, 2), default=1)
    args = parser.parse_args(argv)
    result = build(args.source, json.loads(args.provenance.read_text(encoding='utf-8')),
                   assets_dir=args.assets_dir, archive_dir=args.archive_dir, promote=args.promote, version=args.version)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
