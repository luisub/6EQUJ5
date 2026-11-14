"""Shared containment, recovery and image checks for asset builders."""

import hashlib
import json
import os
from pathlib import Path

from PIL import Image


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


