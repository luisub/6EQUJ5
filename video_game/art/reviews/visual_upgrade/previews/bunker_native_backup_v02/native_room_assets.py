"""MODULE: video_game/engine/native_room_assets.py
PURPOSE: Validate and render optional native room background families.
CALLED BY: FieldOpsScene for explicitly allowlisted rooms.
HOW TO MODIFY: Validate the complete family before drawing; keep legacy fallback safe.
"""
import hashlib
import json
import logging
from pathlib import Path
import pygame
from PIL import Image


LOGGER = logging.getLogger(__name__)
FAMILY = Path('environments/ohio_approach_v1')
LAYERS = (
    {'id':'far', 'file':'far_1152x544.png', 'dimensions':[1152,544],
     'parallax':[0.1,0.05], 'rounding':'native_nearest', 'alpha':'opaque',
     'repeat':False, 'origin':[0,0]},
    {'id':'world', 'file':'world_architecture_1920x576.png', 'dimensions':[1920,576],
     'parallax':[1,1], 'rounding':'logical_nearest', 'alpha':'straight',
     'repeat':False, 'origin':[0,0]},
)


def _inside_without_symlinks(root, relative):
    """Accept only files below the root with no symlink in their family path."""
    path = root
    for part in relative.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError(f'symlink not allowed: {relative}')
    if not path.resolve().is_relative_to(root):
        raise ValueError(f'asset escapes root: {relative}')
    return path


def _digest(path):
    hasher = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024 * 1024), b''):
            hasher.update(block)
    return hasher.hexdigest()


class NativeApproachFamily:
    """Two validated source surfaces; camera sampling never wraps."""

    def __init__(self, far, world):
        self.far = far
        self.world = world

    def crops(self, camera):
        far_x = round(2 * 0.1 * camera.x)
        far_y = round(2 * 0.05 * camera.y)
        # World geometry is rounded at the logical pixel grid before scaling.
        world_x = 2 * round(camera.x)
        world_y = 2 * round(camera.y)
        far_rect = pygame.Rect(far_x, far_y, 960, 540)
        world_rect = pygame.Rect(world_x, world_y, 960, 540)
        if not self.far.get_rect().contains(far_rect) or not self.world.get_rect().contains(world_rect):
            raise ValueError('camera exceeds native approach coverage')
        return self.far.subsurface(far_rect), self.world.subsurface(world_rect)

    def render(self, crt, camera, *, known_clean=False):
        """Validate both crop bounds before drawing either plane."""
        try:
            far, world = self.crops(camera)
        except ValueError as exc:
            LOGGER.warning('Native approach fallback: %s', exc)
            return False
        crt.composite_opaque_background(far, world, known_clean=known_clean)
        return True


def load_approach_family(asset_root, room_id, world_size):
    """Return a fully validated optional family, or None for complete legacy fallback.

    A pending transaction is never read through direct fixture/preview entry
    points; the normal game startup owns locked recovery. Reload per room entry
    instead of holding a process-wide stale image cache.
    """
    if room_id != 'act_01_approach' or tuple(world_size) != (960,288):
        return None
    root = Path(asset_root).resolve()
    journal = root.parent / f'.{root.name}-asset-build-pending.json'
    if journal.exists() or journal.is_symlink():
        LOGGER.warning('Native approach fallback: asset transaction pending')
        return None
    try:
        manifest_path = _inside_without_symlinks(root, FAMILY / 'manifest.json')
        if not manifest_path.exists():
            if manifest_path.parent.exists():
                LOGGER.warning('Native approach fallback: incomplete family has no manifest')
            else:
                LOGGER.info('Native approach family not installed; using legacy background')
            return None
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        if (not isinstance(manifest, dict) or type(manifest.get('schema_version')) is not int
                or manifest.get('schema_version') != 1 or type(manifest.get('density')) is not int):
            raise ValueError('invalid schema')
        if (manifest.get('room_id') != room_id or manifest.get('density') != 2
                or manifest.get('viewport') != [480,270] or manifest.get('world') != [960,288]):
            raise ValueError('room, density, viewport or world mismatch')
        entries = manifest.get('layers')
        if not isinstance(entries, list) or len(entries) != len(LAYERS):
            raise ValueError('expected exactly far and world layers')
        surfaces = []
        for entry, expected in zip(entries, LAYERS):
            if not isinstance(entry, dict) or set(entry) != set(expected) | {'sha256'}:
                raise ValueError('unexpected layer metadata')
            if any(type(entry[k]) is not type(v) or entry[k] != v for k,v in expected.items()):
                raise ValueError(f"invalid {expected['id']} layer contract")
            sha = entry['sha256']
            if not isinstance(sha,str) or len(sha)!=64 or any(ch not in '0123456789abcdef' for ch in sha):
                raise ValueError('invalid source hash')
            path = _inside_without_symlinks(root, FAMILY / expected['file'])
            if _digest(path) != sha:
                raise ValueError(f"hash mismatch: {expected['id']}")
            with path.open('rb') as stream:
                header = stream.read(26)
                if len(header) != 26 or header[:8] != b'\x89PNG\r\n\x1a\n' or header[12:16] != b'IHDR':
                    raise ValueError('layer is not a PNG')
                if header[25] not in ((2, 6) if expected['id'] == 'far' else (6,)):
                    raise ValueError('PNG color mode does not match layer contract')
            image = pygame.image.load(str(path)).convert_alpha()
            if list(image.get_size()) != expected['dimensions']:
                raise ValueError('image dimensions mismatch')
            visible = pygame.mask.from_surface(image, 0).count()
            total = image.get_width() * image.get_height()
            if expected['id'] == 'far':
                if pygame.mask.from_surface(image, 254).count() != total:
                    raise ValueError('far plane is not opaque')
                image = image.convert()  # validated opaque; avoid needless per-pixel alpha blending
            elif visible == 0 or visible == total:
                raise ValueError('world plane must have transparent and visible pixels')
            surfaces.append(image)
        return NativeApproachFamily(*surfaces)
    except (OSError, ValueError, TypeError, KeyError, pygame.error) as exc:
        LOGGER.warning('Native approach fallback: %s', exc)
        return None


def _strict_equal(value, expected):
    """Compare JSON types as well as values (notably bool versus integer)."""
    if type(value) is not type(expected):
        return False
    if isinstance(expected, dict):
        return value.keys() == expected.keys() and all(_strict_equal(value[k], v) for k, v in expected.items())
    if isinstance(expected, list):
        return len(value) == len(expected) and all(_strict_equal(a, b) for a, b in zip(value, expected))
    return value == expected


def _load_room_family_v2(asset_root, family_id, room_id, world_size):
    """Validate every schema-2 component before producing any visible layer."""
    from video_game.engine.room_art_contracts import manifest_template

    root = Path(asset_root).resolve()
    journal = root.parent / f'.{root.name}-asset-build-pending.json'
    if journal.exists() or journal.is_symlink():
        LOGGER.warning('Native room fallback: asset transaction pending')
        return None
    try:
        template = manifest_template(family_id)
        if template['room_id'] != room_id or template['world'] != list(world_size):
            return None
        directory = Path('environments') / family_id
        manifest_path = _inside_without_symlinks(root, directory / 'manifest.json')
        if not manifest_path.exists():
            if manifest_path.parent.exists():
                LOGGER.warning('Native room fallback: incomplete %s family', family_id)
            return None
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        if not isinstance(manifest, dict) or set(manifest) != set(template):
            raise ValueError('unexpected manifest fields')
        for key in ('schema_version', 'room_id', 'density', 'viewport', 'world'):
            if not _strict_equal(manifest[key], template[key]):
                raise ValueError(f'invalid {key}')
        loaded = {}
        seen = set()
        for group in ('layers', 'props'):
            entries = manifest[group]
            expected_entries = template[group]
            if not isinstance(entries, list) or len(entries) != len(expected_entries):
                raise ValueError(f'invalid {group} count')
            for entry, expected in zip(entries, expected_entries):
                if not isinstance(entry, dict) or set(entry) != set(expected) | {'sha256'}:
                    raise ValueError('unexpected component metadata')
                if any(not _strict_equal(entry[key], value) for key, value in expected.items()):
                    raise ValueError(f"invalid {expected['id']} contract")
                filename = expected['file']
                if filename in seen:
                    raise ValueError('duplicate component filename')
                seen.add(filename)
                sha = entry['sha256']
                if not isinstance(sha, str) or len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
                    raise ValueError('invalid component hash')
                path = _inside_without_symlinks(root, directory / filename)
                if _digest(path) != sha:
                    raise ValueError(f"hash mismatch: {expected['id']}")
                with path.open('rb') as stream:
                    header = stream.read(26)
                if (len(header) != 26 or header[:8] != b'\x89PNG\r\n\x1a\n'
                        or header[12:16] != b'IHDR'
                        or header[25] not in ((2, 6) if expected['id'] == 'far' else (6,))):
                    raise ValueError('PNG color mode mismatch')
                image = pygame.image.load(str(path)).convert_alpha()
                if list(image.get_size()) != expected['dimensions']:
                    raise ValueError('image dimensions mismatch')
                total = image.get_width() * image.get_height()
                if expected['id'] == 'far':
                    if pygame.mask.from_surface(image, 254).count() != total:
                        raise ValueError('far plane must be opaque')
                    image = image.convert()
                else:
                    visible = pygame.mask.from_surface(image, 0).count()
                    if visible == 0 or visible == total:
                        raise ValueError('RGBA component must have transparent and visible pixels')
                loaded[expected['id']] = image
        # Straight-alpha composition must normalize color channels: pygame's
        # ordinary surface blit on a translucent destination does not do so.
        # Bake only after all validation and leave the source surfaces unchanged.
        world = loaded['world']
        if template['props']:
            combined = Image.frombytes('RGBA', world.get_size(), pygame.image.tobytes(world, 'RGBA'))
            for prop in template['props']:
                position = tuple(2 * value for value in prop['origin_world'])
                image = loaded[prop['id']]
                if not world.get_rect().contains(pygame.Rect(position, image.get_size())):
                    raise ValueError('prop outside world')
                overlay = Image.frombytes('RGBA', image.get_size(), pygame.image.tobytes(image, 'RGBA'))
                combined.alpha_composite(overlay, dest=position)
            world = pygame.image.frombytes(combined.tobytes(), world.get_size(), 'RGBA').convert_alpha()
        return NativeApproachFamily(loaded['far'], world)
    except (OSError, ValueError, TypeError, KeyError, pygame.error) as exc:
        LOGGER.warning('Native %s fallback: %s', family_id, exc)
        return None


def load_native_room_family(asset_root, room_id, world_size):
    """Select an allowlisted complete family, falling back to approach v1 or legacy."""
    from video_game.engine.room_art_contracts import ROOM_ART_FAMILIES, manifest_template

    family_id = next((candidate for candidate in ROOM_ART_FAMILIES
                      if manifest_template(candidate)['room_id'] == room_id), None)
    if family_id is None:
        return None
    family = _load_room_family_v2(asset_root, family_id, room_id, world_size)
    if family is not None:
        return family
    if room_id == 'act_01_approach':
        return load_approach_family(asset_root, room_id, world_size)
    return None


class NativeOpaqueBackdrop:
    """A validated opaque native world surface, sampled on the logical camera grid."""

    def __init__(self, surface):
        self.surface = surface

    def render(self, crt, camera_x=0, camera_y=0, *, known_clean=False):
        rect = pygame.Rect(2 * round(camera_x), 2 * round(camera_y), 960, 540)
        if not self.surface.get_rect().contains(rect):
            LOGGER.warning('Native backdrop fallback: camera exceeds coverage')
            return False
        crt.composite_opaque_background(self.surface.subsurface(rect), known_clean=known_clean)
        return True


def load_native_opaque_backdrop(asset_root, room_id, world_size):
    """Load an allowlisted whole opaque family, or return None for legacy fallback."""
    from video_game.engine.room_art_contracts import OPAQUE_BACKDROP_FAMILIES, backdrop_manifest_template

    family_id = next((candidate for candidate in OPAQUE_BACKDROP_FAMILIES
                      if backdrop_manifest_template(candidate)['room_id'] == room_id), None)
    if family_id is None:
        return None
    root = Path(asset_root).resolve()
    journal = root.parent / f'.{root.name}-asset-build-pending.json'
    if journal.exists() or journal.is_symlink():
        LOGGER.warning('Native backdrop fallback: asset transaction pending')
        return None
    try:
        template = backdrop_manifest_template(family_id)
        if template['world'] != list(world_size):
            return None
        directory = Path('environments') / family_id
        path = _inside_without_symlinks(root, directory / 'manifest.json')
        if not path.exists():
            if path.parent.exists():
                LOGGER.warning('Native backdrop fallback: incomplete %s family', family_id)
            return None
        manifest = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(manifest, dict) or set(manifest) != set(template):
            raise ValueError('unexpected manifest fields')
        for key in template:
            if key != 'backdrop' and not _strict_equal(manifest[key], template[key]):
                raise ValueError(f'invalid {key}')
        expected = template['backdrop']
        entry = manifest['backdrop']
        if not isinstance(entry, dict) or set(entry) != set(expected) | {'sha256'}:
            raise ValueError('unexpected backdrop fields')
        if any(not _strict_equal(entry[key], value) for key, value in expected.items()):
            raise ValueError('invalid backdrop metadata')
        digest = entry['sha256']
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError('invalid backdrop hash')
        image_path = _inside_without_symlinks(root, directory / expected['file'])
        if _digest(image_path) != digest:
            raise ValueError('backdrop hash mismatch')
        with image_path.open('rb') as stream:
            header = stream.read(26)
        if (len(header) != 26 or header[:8] != b'\x89PNG\r\n\x1a\n'
                or header[12:16] != b'IHDR' or header[25] not in (2, 6)):
            raise ValueError('backdrop must be RGB or RGBA PNG')
        image = pygame.image.load(str(image_path)).convert_alpha()
        if list(image.get_size()) != expected['dimensions']:
            raise ValueError('backdrop dimensions mismatch')
        if pygame.mask.from_surface(image, 254).count() != image.get_width() * image.get_height():
            raise ValueError('backdrop must be fully opaque')
        return NativeOpaqueBackdrop(image.convert())
    except (OSError, ValueError, TypeError, KeyError, pygame.error) as exc:
        LOGGER.warning('Native backdrop %s fallback: %s', family_id, exc)
        return None
