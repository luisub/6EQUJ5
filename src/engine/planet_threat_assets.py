"""PURPOSE: Validate optional per-world threat artwork before use in a room.
CALLED BY: Planet encounters and world hazards on scene entry.
HOW TO MODIFY: Keep exact IDs, contained hash checks, sprite bounds and safe fallback.
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
WORLD_THREAT_IDS = {
    'alien_001': 'carrier_wraith', 'alien_003': 'shard_clipper',
    'alien_005': 'terminator_roller', 'alien_004': 'plasma_kite',
    'alien_008': 'sevenfold_interceptor', 'alien_009': 'archive_skimmer',
    'alien_006': 'memorial_sentinel', 'alien_002': 'lensing_orb',
    'alien_scan_h': 'rift_raptor', 'alien_010': 'resonance_effigy',
    'alien_007': 'beacon_mite',
}
THREAT_IDS = frozenset(WORLD_THREAT_IDS.values())
FAMILY_ROOT = Path('sprites/planet_threats')
IMAGE_NAME = 'body.png'
DIMENSIONS = (96, 72)
PIVOT = (48, 64)
RUN_IMAGE_NAME = 'run.png'
RUN_FRAME_COUNT = 4
RUN_DIMENSIONS = (DIMENSIONS[0] * RUN_FRAME_COUNT, DIMENSIONS[1])
STRIDE_LENGTH = 36.0


def validate_planet_threat_bytes(data):
    """Return exclusive visible alpha bounds after strict PNG/body checks."""
    with Image.open(io.BytesIO(data)) as image:
        if image.format != 'PNG' or image.mode != 'RGBA' or image.size != DIMENSIONS:
            raise ValueError('Planet threat must be a 96x72 RGBA PNG')
        image.load()
        alpha = image.getchannel('A')
        bounds = alpha.getbbox()
        if bounds is None or bounds[0] < 6 or bounds[1] < 8 or bounds[2] > 90 or bounds[3] > 64:
            raise ValueError('Planet threat visible body exceeds safe bounds')
        if sum(alpha.histogram()[240:]) < 16:
            raise ValueError('Planet threat requires a visible near-opaque core')
        return bounds


def validate_planet_threat_run_bytes(data):
    """Require four registered RGBA poses with the same bounds as the body."""
    with Image.open(io.BytesIO(data)) as sheet:
        if sheet.format != 'PNG' or sheet.mode != 'RGBA' or sheet.size != RUN_DIMENSIONS:
            raise ValueError('Planet threat run must be a 384x72 RGBA PNG')
        bounds = []
        for index in range(RUN_FRAME_COUNT):
            frame = sheet.crop((index * 96, 0, (index + 1) * 96, 72))
            stream = io.BytesIO()
            frame.save(stream, format='PNG')
            bounds.append(validate_planet_threat_bytes(stream.getvalue()))
        return bounds


def load_planet_threat(asset_root, art_id):
    """Return (96x72 image, alpha bounds, pivot) once per entry, or None."""
    if asset_root is None or not isinstance(art_id, str) or art_id not in THREAT_IDS:
        return None
    root = Path(asset_root).resolve()
    journal = root.parent / f'.{root.name}-asset-build-pending.json'
    try:
        if journal.exists() or journal.is_symlink():
            return None
        family = FAMILY_ROOT / art_id
        manifest = json.loads(_inside_without_symlinks(root, family / 'manifest.json').read_text(encoding='utf-8'))
        if (not isinstance(manifest, dict)
                or set(manifest) - {'run'} != {'schema_version', 'kind', 'art_id', 'pivot', 'image', 'provenance'}
                or type(manifest['schema_version']) is not int or manifest['schema_version'] != 1
                or manifest['kind'] != 'planet_threat' or manifest['art_id'] != art_id
                or not isinstance(manifest['pivot'], list) or manifest['pivot'] != list(PIVOT)
                or any(type(v) is not int for v in manifest['pivot'])
                or not isinstance(manifest['provenance'], dict) or not manifest['provenance']):
            raise ValueError('Invalid planet threat manifest')
        json.dumps(manifest['provenance'], allow_nan=False)
        item = manifest['image']
        if (not isinstance(item, dict) or set(item) != {'file', 'dimensions', 'sha256'}
                or item['file'] != IMAGE_NAME or item['dimensions'] != list(DIMENSIONS)
                or any(type(v) is not int for v in item['dimensions'])
                or not isinstance(item['sha256'], str) or re.fullmatch('[0-9a-f]{64}', item['sha256']) is None):
            raise ValueError('Invalid planet threat image metadata')
        path = _inside_without_symlinks(root, family / IMAGE_NAME)
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError('Planet threat image hash mismatch')
        bounds = validate_planet_threat_bytes(data)
        image = pygame.image.load(io.BytesIO(data), IMAGE_NAME).convert_alpha()
        return image, bounds, PIVOT
    except (OSError, ValueError, TypeError, KeyError, AttributeError, pygame.error) as exc:
        LOGGER.info('Planet threat %s unavailable: %s', art_id, exc)
        return None


def load_planet_threat_run(asset_root, art_id):
    """Load optional walking poses once at room entry; static art is the fallback."""
    if load_planet_threat(asset_root, art_id) is None:
        return ()
    root = Path(asset_root).resolve()
    family = FAMILY_ROOT / art_id
    try:
        manifest = json.loads(_inside_without_symlinks(root, family / 'manifest.json').read_text(encoding='utf-8'))
        item = manifest.get('run')
        if item is None:
            return ()
        if (not isinstance(item, dict) or set(item) != {'file', 'dimensions', 'sha256'}
                or item['file'] != RUN_IMAGE_NAME or item['dimensions'] != list(RUN_DIMENSIONS)
                or any(type(v) is not int for v in item['dimensions'])
                or not isinstance(item['sha256'], str) or re.fullmatch('[0-9a-f]{64}', item['sha256']) is None):
            raise ValueError('Invalid planet threat run metadata')
        data = _inside_without_symlinks(root, family / RUN_IMAGE_NAME).read_bytes()
        if hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError('Planet threat run hash mismatch')
        validate_planet_threat_run_bytes(data)
        sheet = pygame.image.load(io.BytesIO(data), RUN_IMAGE_NAME).convert_alpha()
        return tuple(sheet.subsurface((index * 96, 0, 96, 72)).copy() for index in range(RUN_FRAME_COUNT))
    except (OSError, ValueError, TypeError, KeyError, AttributeError, pygame.error) as exc:
        LOGGER.info('Planet threat %s run unavailable: %s', art_id, exc)
        return ()
