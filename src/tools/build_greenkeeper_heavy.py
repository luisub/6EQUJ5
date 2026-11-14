"""MODULE: src/tools/build_greenkeeper_heavy.py
PURPOSE: Validate and transactionally promote the reviewed Greenkeeper heavy family.
CALLED BY: python -m video_game.tools.build_greenkeeper_heavy and focused asset tests.
HOW TO MODIFY: Retain the shared lock, recovery, staged validation and manifest-last promotion.
"""
import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path

from video_game.engine.asset_transactions import fcntl, promote_group, recover_pending
from video_game.engine.bosses.greenkeeper_art import FAMILY, HASHES, MANIFEST, validate_bytes
from video_game.engine.config import ASSETS_DIR
from video_game.tools.asset_build_common import _check_pending, _no_symlinks


def build(*, assets_dir=ASSETS_DIR, source, archive_dir=None, promote=False):
    root = _no_symlinks(assets_dir)
    source = _no_symlinks(source)
    archive = _no_symlinks(archive_dir or (Path(__file__).resolve().parents[2] / '_trash' if root == ASSETS_DIR.resolve() else root.parent / '_trash'))
    if not root.is_dir() or archive == root or archive.is_relative_to(root):
        raise ValueError('Invalid asset root or archive')
    if fcntl is None:
        raise RuntimeError('Asset build requires fcntl locking')
    paths = [FAMILY / (name + '.png') for name in HASHES] + [FAMILY / 'manifest.json']
    fd = os.open(root, os.O_RDONLY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        pending = _check_pending(root)
        if pending and not promote:
            raise RuntimeError('Pending asset transaction requires recovery')
        if pending:
            recover_pending(root)
        for name in HASHES:
            p = _no_symlinks(source / (name + '_nearest_256x192.png'))
            validate_bytes(name, p.read_bytes())
        for path in paths:
            _no_symlinks(root / path)
        if not promote:
            return {'status': 'validated', 'manifest': MANIFEST}
        with tempfile.TemporaryDirectory(prefix='greenkeeper-heavy-stage-', dir=root.parent) as tmp:
            stage = _no_symlinks(tmp)
            (stage / FAMILY).mkdir(parents=True)
            for name in HASHES:
                dst = stage / FAMILY / (name + '.png')
                shutil.copyfile(source / (name + '_nearest_256x192.png'), dst)
                validate_bytes(name, dst.read_bytes())
            (stage / FAMILY / 'manifest.json').write_text(json.dumps(MANIFEST, indent=2) + '\n', encoding='utf-8')
            for path in paths:
                _no_symlinks(root / path); _no_symlinks(stage / path)
            saved = promote_group(root, stage, archive, 'greenkeeper', paths)
        return {'status': 'promoted', 'archive': str(saved), 'manifest': MANIFEST}
    finally:
        os.close(fd)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', required=True, type=Path)
    p.add_argument('--assets-dir', default=ASSETS_DIR, type=Path)
    p.add_argument('--archive-dir', type=Path)
    p.add_argument('--promote', action='store_true')
    args = p.parse_args()
    print(json.dumps(build(assets_dir=args.assets_dir, source=args.source, archive_dir=args.archive_dir, promote=args.promote), indent=2))


if __name__ == '__main__':
    main()
