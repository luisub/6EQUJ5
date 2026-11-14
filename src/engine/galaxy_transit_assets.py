"""PURPOSE: Load the optional, validated galaxy map and transit vortex family.
CALLED BY: Transit presentation on scene entry; no image I/O during rendering.
HOW TO MODIFY: Preserve strict metadata, SHA validation and safe missing-art fallback.
"""
import hashlib
import io
import json
import logging
import re
from pathlib import Path

from PIL import Image
import pygame

from .native_room_assets import _inside_without_symlinks

LOGGER = logging.getLogger(__name__)
FAMILY = Path('effects/galaxy_transit')
IMAGES = {
    'galaxy_map': ('galaxy_map_960x540.png', (960, 540), 'RGB'),
    'vortex': ('vortex_512x512.png', (512, 512), 'RGBA'),
}


def validate_transit_image(name, data):
    """Check the exact PNG mode and size, plus a usable transparent vortex."""
    if name not in IMAGES:
        raise ValueError('Unknown galaxy transit image')
    _, dimensions, mode = IMAGES[name]
    with Image.open(io.BytesIO(data)) as image:
        if image.format != 'PNG' or image.mode != mode or image.size != dimensions:
            raise ValueError(f'Invalid {name} PNG mode or dimensions')
        image.load()
        if name == 'vortex':
            low, high = image.getchannel('A').getextrema()
            if low != 0 or high == 0:
                raise ValueError('Vortex requires transparent and visible pixels')


def load_galaxy_transit(asset_root):
    """Return both validated cached-at-entry surfaces, or None for plain fallback."""
    if asset_root is None:
        return None
    root = Path(asset_root).resolve()
    journal = root.parent / f'.{root.name}-asset-build-pending.json'
    try:
        if journal.exists() or journal.is_symlink():
            return None
        manifest_path = _inside_without_symlinks(root, FAMILY / 'manifest.json')
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        if (not isinstance(manifest, dict)
                or set(manifest) != {'schema_version', 'kind', 'images', 'provenance'}
                or type(manifest['schema_version']) is not int or manifest['schema_version'] != 1
                or manifest['kind'] != 'galaxy_transit'
                or not isinstance(manifest['provenance'], dict) or not manifest['provenance']):
            raise ValueError('Invalid galaxy transit manifest')
        json.dumps(manifest['provenance'], allow_nan=False)
        items = manifest['images']
        if not isinstance(items, dict) or set(items) != set(IMAGES):
            raise ValueError('Invalid galaxy transit image list')
        result = {}
        for name, (filename, dimensions, _) in IMAGES.items():
            record = items[name]
            if (not isinstance(record, dict) or set(record) != {'file', 'dimensions', 'sha256'}
                    or record['file'] != filename or record['dimensions'] != list(dimensions)
                    or any(type(v) is not int for v in record['dimensions'])
                    or not isinstance(record['sha256'], str)
                    or re.fullmatch(r'[0-9a-f]{64}', record['sha256']) is None):
                raise ValueError(f'Invalid {name} metadata')
            path = _inside_without_symlinks(root, FAMILY / filename)
            data = path.read_bytes()
            if hashlib.sha256(data).hexdigest() != record['sha256']:
                raise ValueError(f'{name} image hash mismatch')
            validate_transit_image(name, data)
            surface = pygame.image.load(io.BytesIO(data), filename)
            result[name] = surface.convert() if name == 'galaxy_map' else surface.convert_alpha()
        return result
    except (OSError, ValueError, TypeError, KeyError, AttributeError, pygame.error) as exc:
        LOGGER.info('Galaxy transit art unavailable; using plain presentation: %s', exc)
        return None
