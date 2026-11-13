"""PURPOSE: Validate the optional compact energy-stream art family.
CALLED BY: Field and boss presentation at scene entry.
HOW TO MODIFY: Keep strict metadata, hash, RGBA validation and safe fallback.
"""
import hashlib
import io
import json
import logging
from pathlib import Path

from PIL import Image
import pygame

from .native_room_assets import _inside_without_symlinks

LOGGER = logging.getLogger(__name__)
FAMILY = Path('effects/energy_filament_v1')  # Retained v1 public contract.
FAMILY_V2 = Path('effects/energy_filament_v2')
FAMILIES = {1: FAMILY, 2: FAMILY_V2}
IMAGE_NAME = 'stream_96x24.png'
DIMENSIONS = (96, 24)
PIVOT = (4, 12)


def validate_stream_bytes(data):
    """Require transparency and at least four near-opaque core pixels."""
    with Image.open(io.BytesIO(data)) as image:
        if image.format != 'PNG' or image.mode != 'RGBA' or image.size != DIMENSIONS:
            raise ValueError('Energy stream must be a 96x24 RGBA PNG')
        image.load()
        alpha = image.getchannel('A')
        low, high = alpha.getextrema()
        if low != 0 or high < 240 or sum(alpha.histogram()[240:]) < 4:
            raise ValueError('Energy stream needs transparent pixels and a visible near-opaque core')


def _load_family(root, family):
    """Validate one allowlisted family, returning None on any invalid component."""
    try:
        path = _inside_without_symlinks(root, family / 'manifest.json')
        manifest = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(manifest, dict) or set(manifest) != {'schema_version', 'kind', 'density', 'pivot', 'image', 'provenance'}:
            raise ValueError('Unexpected energy-stream manifest fields')
        if (type(manifest['schema_version']) is not int or manifest['schema_version'] != 1
                or manifest['kind'] != 'energy_filament' or type(manifest['density']) is not int
                or manifest['density'] != 2 or not isinstance(manifest['pivot'], list)
                or len(manifest['pivot']) != 2 or any(type(v) is not int for v in manifest['pivot'])
                or tuple(manifest['pivot']) != PIVOT or not isinstance(manifest['provenance'], dict)
                or not manifest['provenance']):
            raise ValueError('Invalid energy-stream family contract')
        json.dumps(manifest['provenance'], allow_nan=False)
        item = manifest['image']
        if (not isinstance(item, dict) or set(item) != {'file', 'dimensions', 'sha256'}
                or item['file'] != IMAGE_NAME or not isinstance(item['dimensions'], list)
                or len(item['dimensions']) != 2 or any(type(v) is not int for v in item['dimensions'])
                or tuple(item['dimensions']) != DIMENSIONS):
            raise ValueError('Invalid energy-stream image metadata')
        digest = item['sha256']
        if (not isinstance(digest, str) or len(digest) != 64
                or any(c not in '0123456789abcdef' for c in digest)):
            raise ValueError('Invalid energy-stream hash')
        image_path = _inside_without_symlinks(root, family / IMAGE_NAME)
        data = image_path.read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError('Energy-stream hash mismatch')
        validate_stream_bytes(data)
        return pygame.image.load(io.BytesIO(data), IMAGE_NAME).convert_alpha()
    except (OSError, ValueError, TypeError, KeyError, AttributeError, pygame.error) as exc:
        LOGGER.info('Energy-stream family %s unavailable: %s', family, exc)
        return None


def load_energy_filament_with_family(asset_root):
    """Prefer validated v2, then validated v1; report the exact selected family."""
    if asset_root is None:
        return None, None
    root = Path(asset_root).resolve()
    journal = root.parent / f'.{root.name}-asset-build-pending.json'
    if journal.exists() or journal.is_symlink():
        return None, None
    for version in (2, 1):
        image = _load_family(root, FAMILIES[version])
        if image is not None:
            return image, FAMILIES[version]
    return None, None


def load_energy_filament(asset_root):
    """Load preferred validated art on scene entry, preserving the original API."""
    return load_energy_filament_with_family(asset_root)[0]
