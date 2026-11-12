"""MODULE: video_game/tools/build_approach_family.py
PURPOSE: Stage and explicitly promote the reviewed Ohio approach environment family.
CALLED BY: python -m video_game.tools.build_approach_family or its transaction tests.
HOW TO MODIFY: Preserve explicit promotion, path checks, lock, recovery and manifest-last order.
"""

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

from PIL import Image
from video_game.engine.asset_transactions import fcntl, promote_group, recover_pending
from video_game.engine.config import ASSETS_DIR

FAMILY = Path('environments/ohio_approach_v1')
FAR = 'far_1152x544.png'
WORLD = 'world_architecture_1920x576.png'
MANIFEST = 'manifest.json'
OUTPUTS = tuple(FAMILY / name for name in (FAR, WORLD, MANIFEST))


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _no_symlinks(path):
    """Reject an existing symlink in an absolute path, including its leaf."""
    path = Path(os.path.abspath(path))
    for component in reversed((path, *path.parents)):
        if component.is_symlink():
            raise ValueError(f'Symlink component is not allowed: {component}')
    return path


def _relative(path):
    path = Path(path)
    if path.is_absolute() or not path.parts or any(p in ('..', '.') for p in path.parts):
        raise ValueError(f'Unsafe relative path: {path}')
    return path


def _check_outputs(root, paths):
    clean = [_relative(path) for path in paths]
    if len(set(clean)) != len(clean) or tuple(clean) != OUTPUTS:
        raise ValueError('Unexpected or duplicate family paths')
    for relative in clean:
        _no_symlinks(root / relative)
    return clean


def _check_pending(root):
    """Validate recovery paths before handing a trusted local journal to legacy recovery."""
    journal = root.parent / f'.{root.name}-asset-build-pending.json'
    _no_symlinks(journal)
    if not journal.exists():
        return False
    record = json.loads(journal.read_text(encoding='utf-8'))
    if Path(record['asset_root']) != root:
        raise ValueError('Pending journal has unexpected asset root')
    archive_input = Path(record['archive'])
    if not archive_input.is_absolute():
        raise ValueError('Recovery archive must be absolute')
    archive = _no_symlinks(archive_input)
    if archive == root or archive.is_relative_to(root):
        raise ValueError('Unsafe recovery archive')
    seen = set()
    for entry in record['files']:
        rel = _relative(entry['path'])
        if rel in seen or type(entry.get('existed')) is not bool:
            raise ValueError('Duplicate or malformed recovery entry')
        seen.add(rel)
        _no_symlinks(root / rel)
        if entry['existed']:
            _no_symlinks(archive / 'video_game' / 'assets' / rel)
    return True


def _validate_image(path, size, opaque):
    path = _no_symlinks(path)
    if not path.is_file():
        raise FileNotFoundError(f'Reviewed source is missing: {path}')
    with Image.open(path) as image:
        image.load()
        if image.format != 'PNG' or image.size != size or image.mode not in ('RGB', 'RGBA'):
            raise ValueError(f'Invalid PNG dimensions or mode: {path}')
        if opaque and image.mode == 'RGBA' and image.getchannel('A').getextrema() != (255, 255):
            raise ValueError(f'Far layer must be opaque: {path}')
        if not opaque:
            if image.mode != 'RGBA':
                raise ValueError(f'World layer must be straight-alpha RGBA: {path}')
            low, high = image.getchannel('A').getextrema()
            if low != 0 or high == 0:
                raise ValueError(f'World layer must contain transparent and visible pixels: {path}')
    return path


def _manifest(far, world):
    return {'schema_version': 1, 'room_id': 'act_01_approach', 'density': 2,
            'viewport': [480, 270], 'world': [960, 288], 'layers': [
                {'id': 'far', 'file': FAR, 'sha256': _sha(far), 'dimensions': [1152, 544],
                 'parallax': [0.1, 0.05], 'rounding': 'native_nearest', 'alpha': 'opaque',
                 'repeat': False, 'origin': [0, 0]},
                {'id': 'world', 'file': WORLD, 'sha256': _sha(world), 'dimensions': [1920, 576],
                 'parallax': [1, 1], 'rounding': 'logical_nearest', 'alpha': 'straight',
                 'repeat': False, 'origin': [0, 0]}]}


def build_family(*, assets_dir=ASSETS_DIR, archive_dir=None, far=None, world=None, promote=False):
    """Without sources report presence only; validate supplied sources or promote explicitly.

    Presence reports never validate installed bytes; use the loader for installed integrity.
    """
    root = _no_symlinks(assets_dir)
    if not root.is_dir():
        raise FileNotFoundError(f'Asset root does not exist: {root}')
    archive = _no_symlinks(archive_dir or root.parent / '_trash')
    if archive == root or archive.is_relative_to(root):
        raise ValueError('Archive must be outside asset root')
    if fcntl is None:
        raise RuntimeError('Approach family building requires fcntl locking')
    if (far is None) != (world is None):
        raise ValueError('Both reviewed sources must be provided together')
    if promote and far is None:
        raise ValueError('Explicit promotion requires both reviewed sources')
    descriptor = os.open(root, os.O_RDONLY)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError(f'Another asset build is active: {root}') from exc
        pending = _check_pending(root)
        if pending and not promote:
            raise RuntimeError('Pending asset transaction requires recovery before review')
        if pending:
            recover_pending(root)
        _check_outputs(root, OUTPUTS)
        if far is None:
            presence = {p.as_posix(): (root / p).is_file() for p in OUTPUTS}
            present_count = sum(presence.values())
            status = ('absent' if present_count == 0 else
                      'present_not_inspected' if present_count == len(OUTPUTS) else
                      'partial_not_inspected')
            return {'status': status, 'integrity': 'not_inspected', 'files': presence}
        far = _validate_image(far, (1152, 544), True)
        world = _validate_image(world, (1920, 576), False)
        manifest = _manifest(far, world)
        if not promote:
            return {'status': 'validated', 'manifest': manifest}
        with tempfile.TemporaryDirectory(prefix='approach-stage-', dir=root.parent) as tmp:
            stage = _no_symlinks(tmp)
            _check_outputs(stage, OUTPUTS)
            dest = stage / FAMILY
            dest.mkdir(parents=True)
            shutil.copyfile(far, dest / FAR)
            shutil.copyfile(world, dest / WORLD)
            _validate_image(dest / FAR, (1152, 544), True)
            _validate_image(dest / WORLD, (1920, 576), False)
            if _manifest(dest / FAR, dest / WORLD) != manifest:
                raise IOError('Staged image hash differs from reviewed source')
            (dest / MANIFEST).write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
            _check_outputs(stage, OUTPUTS)
            _check_outputs(root, OUTPUTS)
            archived = promote_group(root, stage, archive, 'ohio_approach_v1', OUTPUTS)
        return {'status': 'promoted', 'archive': str(archived), 'manifest': manifest}
    finally:
        os.close(descriptor)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets-dir', type=Path, default=ASSETS_DIR)
    parser.add_argument('--archive-dir', type=Path)
    parser.add_argument('--far', type=Path)
    parser.add_argument('--world', type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--promote', action='store_true', help='Explicitly replace the complete family')
    mode.add_argument('--dry-run', action='store_true', help='Without sources report presence only; with --far and --world validate reviewed source bytes without writes (installed integrity is not inspected)')
    args = parser.parse_args(argv)
    result = build_family(assets_dir=args.assets_dir, archive_dir=args.archive_dir,
                          far=args.far, world=args.world, promote=args.promote)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
