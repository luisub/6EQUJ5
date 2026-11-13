"""MODULE: tools/build_maser_discharge.py
PURPOSE: Validate or explicitly install the reviewed maser discharge family.
CALLED BY: python -m tools.build_maser_discharge and transaction tests.
HOW TO MODIFY: Preserve explicit promotion, asset-root lock, recovery and manifest-last order.
"""
import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path

from video_game.engine.asset_transactions import fcntl, promote_group, recover_pending
from video_game.engine.config import ASSETS_DIR
from video_game.engine.effects import MASER_FAMILY, MASER_MANIFEST, MASER_NAME, validate_maser_bytes
from tools.build_approach_family import _check_pending, _no_symlinks

OUTPUTS = (MASER_FAMILY / MASER_NAME, MASER_FAMILY / 'manifest.json')


def build_discharge(*, assets_dir=ASSETS_DIR, archive_dir=None, source=None, promote=False):
    """Inspect presence, validate the reviewed source, or explicitly promote it."""
    root = _no_symlinks(assets_dir)
    if not root.is_dir():
        raise FileNotFoundError(root)
    archive = _no_symlinks(archive_dir or (Path(__file__).resolve().parent.parent / '_trash' if root == ASSETS_DIR.resolve() else root.parent / '_trash'))
    if archive == root or archive.is_relative_to(root):
        raise ValueError('Archive must be outside asset root')
    if fcntl is None:
        raise RuntimeError('Asset build requires fcntl locking')
    if promote and source is None:
        raise ValueError('Explicit promotion requires the reviewed source')
    descriptor = os.open(root, os.O_RDONLY)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError('Another asset build is active') from exc
        pending = _check_pending(root)
        if pending and not promote:
            raise RuntimeError('Pending transaction requires recovery')
        if pending:
            recover_pending(root)
        for path in OUTPUTS:
            _no_symlinks(root / path)
        if source is None:
            return {'status': 'presence_only', 'integrity': 'not_inspected',
                    'files': {str(path): (root / path).is_file() for path in OUTPUTS}}
        source = _no_symlinks(source)
        validate_maser_bytes(source.read_bytes())
        if not promote:
            return {'status': 'validated', 'manifest': MASER_MANIFEST}
        with tempfile.TemporaryDirectory(prefix='maser-discharge-stage-', dir=root.parent) as tmp:
            stage = _no_symlinks(tmp)
            for path in OUTPUTS:
                _no_symlinks(stage / path)
            (stage / MASER_FAMILY).mkdir(parents=True)
            shutil.copyfile(source, stage / OUTPUTS[0])
            validate_maser_bytes((stage / OUTPUTS[0]).read_bytes())
            (stage / OUTPUTS[1]).write_text(json.dumps(MASER_MANIFEST, indent=2) + '\n', encoding='utf-8')
            for path in OUTPUTS:
                _no_symlinks(root / path)
                _no_symlinks(stage / path)
            saved = promote_group(root, stage, archive, 'maser_discharge_v2', OUTPUTS)
        return {'status': 'promoted', 'archive': str(saved), 'manifest': MASER_MANIFEST}
    finally:
        os.close(descriptor)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets-dir', type=Path, default=ASSETS_DIR)
    parser.add_argument('--archive-dir', type=Path)
    parser.add_argument('--source', type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--promote', action='store_true')
    mode.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)
    print(json.dumps(build_discharge(assets_dir=args.assets_dir, archive_dir=args.archive_dir,
                                 source=args.source, promote=args.promote), indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
