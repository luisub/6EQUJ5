"""MODULE: video_game/engine/bosses/greenkeeper_art.py
PURPOSE: Validate and load the reviewed Greenkeeper key-pose family atomically.
CALLED BY: Greenkeeper and the Greenkeeper asset builder and tests.
HOW TO MODIFY: Preserve exact hashes, dimensions, anchors and procedural fallback.
"""
import hashlib
import io
import json
import logging
from pathlib import Path

import pygame
from PIL import Image

FAMILY = Path('sprites/bosses/greenkeeper')
HASHES = {
    'idle': 'e5aa98b55d761de1d1ea4959e025ff51b7ac310a434752da6eab537d4da0918c',
    'attack': '1e607d90a4c4a54bf386c0b24b1d4981a6d8f87e99ab8173958a81fc3fb0eddf',
    'exposed': 'f88ac427ed68d7321222d205ceb2f60b9a67f0b111c2707ff6ed0102a92cf1e7',
    'wreck': 'd54d7e427dfd3632e94522fac21bdced7d2bfd935600c9f0483bfdf483ca4f6f',
}
MANIFEST = {
    'schema_version': 1, 'boss_id': 'greenkeeper_act_01', 'density': 2,
    'native_size': [256, 192], 'world_size': [128, 96],
    'anchors': {'foot_y': 96, 'mortar_idle': [38, 15], 'mortar_attack': [39, 16],
                'mortar_wreck': [35, 40], 'sweep': [5, 80], 'reactor_rect': [62, 49, 23, 19]},
    'frames': {name: {'file': name + '.png', 'sha256': digest} for name, digest in HASHES.items()},
    'coverage': 'four key poses: idle, attack, exposed, wreck; not eleven new animation frames',
}


def validate_bytes(name, data):
    if hashlib.sha256(data).hexdigest() != HASHES[name]:
        raise ValueError('Greenkeeper asset hash mismatch: ' + name)
    with Image.open(io.BytesIO(data)) as im:
        im.load()
        if im.format != 'PNG' or im.mode != 'RGBA' or im.size != (256, 192):
            raise ValueError('Invalid Greenkeeper image format or dimensions')
        lo, hi = im.getchannel('A').getextrema()
        if lo != 0 or hi != 255:
            raise ValueError('Greenkeeper image requires transparent and opaque pixels')


def load_family(asset_root):
    """Load all four verified surfaces, or return None and use the procedural fallback."""
    root = Path(asset_root).resolve()
    journal = root.parent / f'.{root.name}-asset-build-pending.json'
    try:
        if journal.exists() or journal.is_symlink():
            return None
        paths = [root / 'sprites', root / 'sprites/bosses', root / FAMILY,
                 root / FAMILY / 'manifest.json'] + [root / FAMILY / (name + '.png') for name in HASHES]
        if any(path.is_symlink() for path in paths):
            raise ValueError('Symlink in Greenkeeper family')
        if json.loads((root / FAMILY / 'manifest.json').read_text(encoding='utf-8')) != MANIFEST:
            raise ValueError('Invalid Greenkeeper manifest')
        images = {}
        for name in HASHES:
            data = (root / FAMILY / (name + '.png')).read_bytes()
            validate_bytes(name, data)
            images[name] = pygame.image.load(io.BytesIO(data), name + '.png')
        return images
    except (OSError, ValueError, TypeError, pygame.error) as exc:
        logging.getLogger(__name__).info('Greenkeeper heavy art unavailable; using procedural fallback: %s', exc)
        return None
