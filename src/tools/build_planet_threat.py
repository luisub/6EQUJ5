"""PURPOSE: Validate and safely promote one new per-world threat sprite family.
CALLED BY: python -m video_game.tools.build_planet_threat and focused tests.
HOW TO MODIFY: Keep exact IDs, staged validation, transaction lock and manifest last.
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
from video_game.engine.planet_threat_assets import (THREAT_IDS, FAMILY_ROOT, IMAGE_NAME,
                                                   DIMENSIONS, PIVOT, validate_planet_threat_bytes)
from video_game.tools.build_approach_family import _check_pending, _no_symlinks


def build(art_id, source, provenance, *, assets_dir=ASSETS_DIR, archive_dir=None, promote=False):
    """Validate reviewed source or promote it into its absent allowlisted family."""
    if not isinstance(art_id, str) or art_id not in THREAT_IDS:
        raise ValueError('Unknown planet threat ID')
    if not isinstance(provenance, dict) or not provenance:
        raise ValueError('A nonempty provenance object is required')
    json.dumps(provenance, allow_nan=False)
    source = _no_symlinks(source)
    data = source.read_bytes(); validate_planet_threat_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    manifest = {'schema_version': 1, 'kind': 'planet_threat', 'art_id': art_id,
                'pivot': list(PIVOT),
                'image': {'file': IMAGE_NAME, 'dimensions': list(DIMENSIONS), 'sha256': digest},
                'provenance': provenance}
    root = _no_symlinks(assets_dir)
    if not root.is_dir():
        raise FileNotFoundError(root)
    archive = _no_symlinks(archive_dir or (Path(__file__).resolve().parents[2] / '_trash' if root == ASSETS_DIR.resolve() else root.parent / '_trash'))
    if archive == root or archive.is_relative_to(root):
        raise ValueError('Archive must be outside the asset root')
    if fcntl is None:
        raise RuntimeError('Planet threat building requires fcntl locking')
    descriptor = os.open(root, os.O_RDONLY)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError('Another asset build is active') from exc
        if _check_pending(root):
            raise RuntimeError('Pending transaction requires recovery')
        family = FAMILY_ROOT / art_id
        target = _no_symlinks(root / family)
        if target.exists():
            raise FileExistsError(f'Planet threat family already exists: {target}')
        if not promote:
            return {'status': 'validated', 'manifest': manifest}
        with tempfile.TemporaryDirectory(prefix='planet-threat-stage-', dir=root.parent) as temporary:
            stage = Path(temporary); directory = stage / family; directory.mkdir(parents=True)
            staged = directory / IMAGE_NAME; shutil.copyfile(source, staged)
            staged_data = staged.read_bytes()
            if hashlib.sha256(staged_data).hexdigest() != digest:
                raise IOError('Staged image differs from reviewed source')
            validate_planet_threat_bytes(staged_data)
            (directory / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
            _no_symlinks(root / family)
            if (root / family).exists():
                raise FileExistsError('Planet threat family appeared during staging')
            saved = promote_group(root, stage, archive, f'planet_threat_{art_id}',
                                  (family / IMAGE_NAME, family / 'manifest.json'))
        return {'status':'promoted', 'manifest':manifest, 'archive':str(saved)}
    finally:
        os.close(descriptor)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--art-id', choices=sorted(THREAT_IDS), required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--provenance', type=Path, required=True)
    parser.add_argument('--assets-dir', type=Path, default=ASSETS_DIR)
    parser.add_argument('--archive-dir', type=Path)
    parser.add_argument('--promote', action='store_true')
    args = parser.parse_args(argv)
    result = build(args.art_id, args.source, json.loads(args.provenance.read_text(encoding='utf-8')),
                   assets_dir=args.assets_dir, archive_dir=args.archive_dir, promote=args.promote)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
