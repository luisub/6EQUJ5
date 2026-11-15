"""PURPOSE: Load the optional, validated galaxy map and transit vortex family.
CALLED BY: Transit presentation on scene entry; no image I/O during rendering.
HOW TO MODIFY: Preserve strict metadata, SHA validation and safe missing-art fallback.
"""
import hashlib
import io
import json
import logging
import math
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


def render_constellation(crt, area, *, leg=None, progress=0.0, visited=(), time=0.0, compact=False):
    """Shared signal chart: named stars, earned links and one moving ship."""
    from .galaxy_transit import map_points, leg_points, leg_position, route_ids, locations_by_id
    area = pygame.Rect(area)
    route, locations = route_ids(), locations_by_id()
    points = map_points(area)
    visited = set(visited)
    # Stable background stars, without consuming gameplay randomness.
    for i in range(66):
        x = area.x + (i * 137 + 31) % max(1, area.width)
        y = area.y + (i * i * 17 + 19) % max(1, area.height)
        light = 28 + round(12 * (1 + math.sin(time * .8 + i)))
        pygame.draw.rect(crt.canvas, (light, light + 8, light + 17), (x, y, 1, 1))
    for origin, target in zip(route, route[1:]):
        path = leg_points(origin, target, area)
        complete = origin in visited and target in visited and target != 'earth'
        pygame.draw.lines(crt.canvas, (4, 11, 22), False, path, 3)
        color = (65, 134, 148) if complete else (42, 62, 86)
        if complete or compact:
            pygame.draw.lines(crt.canvas, color, False, path, 1)
        else:
            for i in range(0, len(path) - 1, 2):
                pygame.draw.line(crt.canvas, color, path[i], path[i + 1])
    if leg:
        source, destination = leg
        path = leg_points(source, destination, area, progress)
        pygame.draw.lines(crt.canvas, (105, 89, 59), False, leg_points(source, destination, area), 1)
        pygame.draw.lines(crt.canvas, (161, 124, 66), False, path, 3)
        pygame.draw.lines(crt.canvas, (255, 220, 147), False, path, 1)
        ship = pygame.Vector2(leg_position(source, destination, area, progress))
        ahead = pygame.Vector2(leg_position(source, destination, area, min(1, progress + .01)))
        behind = pygame.Vector2(leg_position(source, destination, area, max(0, progress - .01)))
        direction = ahead - behind
        if direction.length_squared() > .001:
            direction.normalize_ip()
            normal = pygame.Vector2(-direction.y, direction.x)
            pygame.draw.polygon(crt.canvas, (255, 242, 201),
                                (ship + direction * 5, ship - direction * 3 + normal * 3,
                                 ship - direction, ship - direction * 3 - normal * 3))
    labels = []
    for index, loc_id in enumerate(route[:-1]):
        if loc_id not in points:
            continue
        x, y = points[loc_id]
        current = leg and loc_id in leg
        color = ((255, 215, 137) if index == 0 or (leg and loc_id == leg[0]) else
                 (132, 238, 245) if current else (100, 163, 174) if loc_id in visited else (109, 127, 152))
        pygame.draw.circle(crt.canvas, (4, 12, 23), (x, y), 7)
        pygame.draw.circle(crt.canvas, color, (x, y), 3 if current else 2)
        if current or index == 0:
            pygame.draw.circle(crt.canvas, color, (x, y), 6, 1)
        if leg and loc_id == leg[1]:
            radius = 8 + round(2 * math.sin(time * 5))
            pygame.draw.circle(crt.canvas, (50, 102, 125), (x, y), radius, 1)
        label = ('EARTH' if index == 0 else str(index)) if compact else locations[loc_id]['label']
        width = crt.font_sm.size(label)[0]
        lx = x + 10
        if lx + width > area.right:
            lx = x - width - 10
        ly = y - 5 if not compact else y + 6
        labels.append((label, max(area.left, lx), ly, color))
    with crt.text_batch():
        for label, x, y, color in labels:
            crt.draw_text(label, x, y, color=color, size='sm', has_shadow=True)


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
