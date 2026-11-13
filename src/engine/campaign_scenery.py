"""PURPOSE: Validated campaign backgrounds and non-colliding ambient activity.
CALLED BY: FieldOpsScene and BossScene on room entry and rendering.
HOW TO MODIFY: Keep loading contained, hash-checked and outside render/update.

Scenery is cached at room entry. It never creates gameplay actors or collision.
"""
import json
import logging
import math
import re
from pathlib import Path

import pygame

from .native_room_assets import _digest, _inside_without_symlinks

LOGGER = logging.getLogger(__name__)
ART_IDS = {'act_02': 'neo_denver_v1', 'act_03': 'area_51_v1',
           'act_04': 'vla_rift_v1', 'act_05': 'gobekli_tepe_v1'}
ALIEN_CIV_IDS = tuple(f'{number:03d}' for number in range(1, 11)) + ('scan_h',)
ALIEN_BACKGROUND_IDS = frozenset(f'realm_fasr_{ident}_v1' for ident in ALIEN_CIV_IDS)
GUARDIAN_IDS = frozenset(f'guardian_fasr_{ident}' for ident in ALIEN_CIV_IDS)
BACKGROUND_IDS = (frozenset(ART_IDS.values()) | {'area_51_hangar_v1', 'gobekli_archive_v1', 'gobekli_tepe_v2'}
                  | ALIEN_BACKGROUND_IDS)
INTERIOR_BACKGROUND_IDS = frozenset({'area_51_hangar_v1', 'gobekli_archive_v1'})
# Modern traffic and the reused staff pose belong only in contemporary settings.
MODERN_ACTIVITY_ACTS = frozenset({'act_02', 'act_03', 'act_04'})
MODERN_ACTIVITY_ART_IDS = frozenset({'neo_denver_v1', 'area_51_v1', 'area_51_hangar_v1', 'vla_rift_v1'})
BOSS_IDS = frozenset({'synchronicity', 'amalgam', 'architect', 'core_prime',
                      'portal_warden', 'earth_core_ai'}) | GUARDIAN_IDS
# These are previously installed civilization profile images, not new realm art.
PROFILE_HASHES = {
    '001':'8c6f75d13f42639e7c5a0b635ea7b5fd8a6fea6a29d0d5d2d1696d5a08dc749a',
    '002':'0c622af3a2dd384bc50d12e1670a3948d5cb971d08d127d9e08597e20ee20635',
    '003':'1eba36dbcee2f8ec2307b36cbc2f927bf630b171386f986365e61a4a9e30691e',
    '004':'51eda698d404d000e8586fbd88d666f412b25b9add6ed308611f6fc1a64bf43a',
    '005':'1a202ca064084bf2de50cd02f823ef8670a5438337c2625ba2c20f9b1cf79d46',
    '006':'ecc0b6d2ddeeb74110447d4b8d8994c677c18420814e2be7db6fbb2ac8710c8e',
    '007':'f45973ede81969de7417ad75ef1201d5018ed2c26bc4e983c201adcc08573e64',
    '008':'e30dbde3c65210b3b7fc7789bae939b12f25878073a6adf90581e023ab14c5a9',
    '009':'6434381b3aeadacce3daae50fccb0b6d2852313510029d5612ba0ecc5221cc40',
    '010':'7cb802833cd65ba8657e0bc58187263b5992d8197f6b4dc89341b89a1dee5fd8',
    'scan_h':'04998748e07a1321f89ced38b1e338bc3203c8558592e961f361c3f195bcfb94',
}
# Existing patrol poses serve as temporary, recognizable combat silhouettes.
FALLBACK_ENEMIES = {
    'core_recon_drone': (24,20,'b758a58eb6d61a1265548b3adde9dc6a9c14dc116881d5dccd979fe3eaaeaea8'),
    'static_hound': (32,20,'32a7d4e5d1f65c7f7e764c305285dec9c0e2294d971aaf5d360e27892e6f020c'),
    'core_enforcer': (24,32,'6e74b2077a8803e5b8de70d463456b263b2d847a6cebeec62f308f3a25db6983'),
    'core_operative': (20,32,'be12eb4fdf8c5baa0b32953acd6eb519a12d1f791a4b6f0080a6b423bf26aeb1'),
    'shield_hound': (32,24,'878a321dfb95c19a23dbe8b8241db2d51a2ab376f3ada5cbb8b0d66e5bd7716a'),
    'phase_watcher': (20,36,'fdc3b42ce734251b0f3c6630b4caab25f63011d7f4a12b250f42e2f15a14b9c2'),
    'chrysalis_splicer': (28,24,'e62b3896cea9fb75d864e9bf1955c4461d020d80bf3b785468b815dac3d5feb3'),
    'precursor_guardian': (32,40,'40a7e56450768f8424f019a49bc36346d5658d4e4ed1341f8642f662bc3784c7'),
    'temporal_phantom': (24,32,'ad572261324264cd575174e568cad67551fd953bfafabd0464fbe187e8aa985c'),
}
GUARDIAN_FALLBACK = dict(zip(ALIEN_CIV_IDS, (
    'core_recon_drone', 'temporal_phantom', 'chrysalis_splicer', 'phase_watcher',
    'core_operative', 'precursor_guardian', 'shield_hound', 'core_enforcer',
    'static_hound', 'temporal_phantom', 'phase_watcher',
)))


def _journal_pending(root):
    journal = root.parent / f'.{root.name}-asset-build-pending.json'
    return journal.exists() or journal.is_symlink()


def load_profile_blockout(asset_root, art_id):
    """Reuse one verified civilization environment as a temporary backdrop."""
    if asset_root is None or not isinstance(art_id, str) or art_id not in ALIEN_BACKGROUND_IDS:
        return None
    ident = art_id.removeprefix('realm_fasr_').removesuffix('_v1')
    civ_id = 'FASR-' + ('SCAN-H' if ident == 'scan_h' else ident)
    filename = f'fasr-{ident.replace("_", "-")}_env.png'
    root = Path(asset_root).resolve()
    try:
        if _journal_pending(root):
            return None
        manifest = json.loads(_inside_without_symlinks(root, Path('civilizations/manifest.json')).read_text())
        entry = manifest[civ_id]
        if entry.get('env_png') != filename or entry.get('native_size') != [128,128]:
            raise ValueError('invalid civilization environment mapping')
        path = _inside_without_symlinks(root, Path('civilizations') / filename)
        if _digest(path) != PROFILE_HASHES[ident]:
            raise ValueError('civilization environment hash mismatch')
        image = pygame.image.load(str(path)).convert_alpha()
        if image.get_size() != (128,128) or pygame.mask.from_surface(image,254).count() != 128*128:
            raise ValueError('civilization environment must be opaque 128x128')
        tile = pygame.transform.scale(image, (540,540)).convert()
        background = pygame.Surface((1920,540)).convert()
        for x in range(0,1920,540):
            background.blit(tile, (x,0))
        return background
    except (OSError, ValueError, TypeError, KeyError, AttributeError, pygame.error) as exc:
        LOGGER.info('Civilization blockout unavailable for %s: %s', civ_id, exc)
        return None


def _load_existing_guardian(asset_root, boss_id):
    """Build a temporary body from a hash-checked, manifest-backed patrol pose."""
    if boss_id not in GUARDIAN_IDS:
        return None
    ident = boss_id.removeprefix('guardian_fasr_')
    enemy = GUARDIAN_FALLBACK[ident]
    width, height, expected_hash = FALLBACK_ENEMIES[enemy]
    relative = Path('sprites/enemies') / enemy / 'patrol_1.png'
    root = Path(asset_root).resolve()
    try:
        if _journal_pending(root):
            return None
        manifest = json.loads(_inside_without_symlinks(root,Path('sprites/enemies/manifest.json')).read_text())
        entry = manifest['enemies'][enemy]
        if (entry['width'] != width or entry['height'] != height
                or entry['animations']['patrol']['frames'][0] != relative.as_posix()):
            raise ValueError('invalid enemy fallback manifest')
        path = _inside_without_symlinks(root, relative)
        if _digest(path) != expected_hash:
            raise ValueError('enemy fallback hash mismatch')
        image = pygame.image.load(str(path)).convert_alpha()
        if image.get_size() != (width,height):
            raise ValueError('enemy fallback dimensions mismatch')
        scale = min(224 / width, 180 / height)
        image = pygame.transform.scale(image, (round(width * scale), round(height * scale)))
        body = pygame.Surface((256,192),pygame.SRCALPHA).convert_alpha()
        body.blit(image, ((256-image.get_width())//2, 192-image.get_height()))
        return body
    except (OSError, ValueError, TypeError, KeyError, IndexError, pygame.error) as exc:
        LOGGER.info('Guardian blockout unavailable for %s: %s', boss_id, exc)
        return None


def load_campaign_background(asset_root, art_id):
    """Load one complete, contained, opaque, hash-validated background family."""
    if asset_root is None or not isinstance(art_id, str) or art_id not in BACKGROUND_IDS:
        return None
    root = Path(asset_root).resolve()
    journal = root.parent / f'.{root.name}-asset-build-pending.json'
    try:
        if journal.exists() or journal.is_symlink():
            return None
        relative = Path('environments/campaign_worlds') / art_id
        manifest_path = _inside_without_symlinks(root, relative / 'manifest.json')
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        if not isinstance(manifest, dict) or set(manifest) != {'schema_version', 'kind', 'art_id', 'viewport', 'density', 'image', 'provenance'}:
            raise ValueError('unexpected background manifest fields')
        if (type(manifest['schema_version']) is not int or manifest['schema_version'] != 1
                or manifest['kind'] != 'campaign_world_background' or manifest['art_id'] != art_id
                or manifest['viewport'] != [480, 270] or type(manifest['density']) is not int
                or manifest['density'] != 2 or not isinstance(manifest['provenance'], dict)):
            raise ValueError('invalid background manifest')
        item = manifest['image']
        if (not isinstance(item, dict) or set(item) != {'file', 'dimensions', 'sha256'}
                or item['file'] != 'background.png' or item['dimensions'] != [1920, 540]
                or not isinstance(item['sha256'], str) or not re.fullmatch('[a-f0-9]{64}', item['sha256'])):
            raise ValueError('invalid image metadata')
        path = _inside_without_symlinks(root, relative / item['file'])
        if _digest(path) != item['sha256']:
            raise ValueError('background hash mismatch')
        with path.open('rb') as stream:
            header = stream.read(26)
        if (len(header) != 26 or header[:8] != b'\x89PNG\r\n\x1a\n'
                or header[12:16] != b'IHDR' or header[25] not in (2, 6)):
            raise ValueError('background is not an RGB or RGBA PNG')
        image = pygame.image.load(str(path)).convert_alpha()
        if image.get_size() != (1920, 540) or pygame.mask.from_surface(image, 254).count() != 1920 * 540:
            raise ValueError('background must be an opaque 1920x540 image')
        return image.convert()
    except (OSError, ValueError, TypeError, KeyError, pygame.error) as exc:
        LOGGER.info('Campaign background unavailable for %s: %s', art_id, exc)
        return None


def load_campaign_boss(asset_root, boss_id, *, allow_fallback=True):
    """Load a verified boss pose, optionally reusing validated existing art."""
    if asset_root is None or not isinstance(boss_id, str) or boss_id not in BOSS_IDS:
        return None
    root = Path(asset_root).resolve()
    journal = root.parent / f'.{root.name}-asset-build-pending.json'
    try:
        if journal.exists() or journal.is_symlink():
            return None
        relative = Path('sprites/bosses/campaign') / boss_id
        manifest = json.loads(_inside_without_symlinks(root, relative / 'manifest.json').read_text(encoding='utf-8'))
        if not isinstance(manifest, dict) or set(manifest) != {'schema_version', 'kind', 'boss_id', 'image', 'provenance'}:
            raise ValueError('unexpected boss manifest fields')
        if (type(manifest['schema_version']) is not int or manifest['schema_version'] != 1
                or manifest['kind'] != 'campaign_boss' or manifest['boss_id'] != boss_id
                or not isinstance(manifest['provenance'], dict)):
            raise ValueError('invalid boss manifest')
        item = manifest['image']
        if (not isinstance(item, dict) or set(item) != {'file', 'dimensions', 'sha256'}
                or item['file'] != 'body.png' or item['dimensions'] != [256, 192]
                or not isinstance(item['sha256'], str) or not re.fullmatch('[a-f0-9]{64}', item['sha256'])):
            raise ValueError('invalid boss image metadata')
        path = _inside_without_symlinks(root, relative / 'body.png')
        if _digest(path) != item['sha256']:
            raise ValueError('boss image hash mismatch')
        with path.open('rb') as stream:
            header = stream.read(26)
        if (len(header) != 26 or header[:8] != b'\x89PNG\r\n\x1a\n'
                or header[12:16] != b'IHDR' or header[25] != 6):
            raise ValueError('boss body must be an RGBA PNG')
        image = pygame.image.load(str(path)).convert_alpha()
        if image.get_size() != (256, 192):
            raise ValueError('invalid boss image dimensions')
        count = pygame.mask.from_surface(image, 0).count()
        if count == 0 or count == image.get_width() * image.get_height():
            raise ValueError('boss image requires visible and transparent pixels')
        return image
    except (OSError, ValueError, TypeError, KeyError, pygame.error) as exc:
        LOGGER.info('Campaign boss body unavailable for %s: %s', boss_id, exc)
        if allow_fallback and not _journal_pending(root):
            if boss_id in GUARDIAN_IDS:
                body = _load_existing_guardian(root, boss_id)
                if body is not None:
                    return body
            if boss_id == 'earth_core_ai':
                from .bosses.greenkeeper_art import load_family
                existing = load_family(root)
                if existing is not None:
                    return existing['idle']
            if boss_id != 'synchronicity':
                # Reuse the approved Core machine pose when available.
                body = load_campaign_boss(root, 'synchronicity', allow_fallback=False)
                if body is not None:
                    return body
            from .bosses.greenkeeper_art import load_family
            existing = load_family(root)
            if existing is not None:
                return existing['idle']
        return None


class CampaignScenery:
    """Background plate and quiet, decorative people and traffic."""

    def __init__(self, asset_root, room, route_room_meta=None):
        self.room = room
        self.elapsed = 0.0
        self.background = None
        self.background_source = {'kind': 'unavailable'}
        self._background_view = None
        meta = route_room_meta if isinstance(route_room_meta, dict) else {}
        alien_room = isinstance(room.room_id, str) and room.room_id.startswith('alien_')
        view = meta.get('art_view')
        if (isinstance(view, (tuple, list)) and len(view) == 2
                and all(type(v) in (int, float) and math.isfinite(v) for v in view)
                and 0 <= view[0] <= view[1] <= 1):
            self.art_view = tuple(view)
        else:
            self.art_view = (0.0, 1.0)
        art_id = meta.get('art_id') if alien_room else meta.get('art_id', ART_IDS.get(room.act_id))
        # Preserve route metadata and v1 source while avoiding its baked vehicle.
        # A missing or corrupt v2 uses the scene's generic fallback, never v1.
        if not alien_room and room.act_id == 'act_05' and art_id == 'gobekli_tepe_v1':
            art_id = 'gobekli_tepe_v2'
        allowed = art_id in ALIEN_BACKGROUND_IDS if alien_room and isinstance(art_id, str) else not alien_room
        if allowed and room.act_id in ART_IDS and room.room_id != 'act_04_dodleston_relay':
            self.background = load_campaign_background(asset_root, art_id)
            if self.background is not None:
                self.background_source = {'kind': 'native', 'art_id': art_id}
            elif alien_room:
                self.background = load_profile_blockout(asset_root, art_id)
                if self.background is not None:
                    self.background_source = {'kind': 'profile_blockout', 'art_id': art_id}
            if self.background is not None:
                self._background_view = pygame.Surface((960, 540)).convert()
        self.vehicle = self.person = None
        modern_activity = (room.act_id in MODERN_ACTIVITY_ACTS and isinstance(art_id, str)
                           and art_id in MODERN_ACTIVITY_ART_IDS)
        ohio_activity = room.act_id == 'act_01' and art_id is None
        if asset_root is None or alien_room or not (modern_activity or ohio_activity):
            return
        root = Path(asset_root)
        # Ohio has its own traffic controller; avoid two overlapping vehicles.
        if room.act_id in MODERN_ACTIVITY_ACTS and art_id not in INTERIOR_BACKGROUND_IDS:
            try:
                source = pygame.image.load(str(root / 'environments/ohio_salvage_v1/wagon_168x76_rgba.png')).convert_alpha()
                self.vehicle = pygame.transform.scale(source, (72, 33))
            except (OSError, pygame.error):
                pass
        try:
            source = pygame.image.load(str(root / 'sprites/mateo/navy_chore/idle_1.png')).convert_alpha()
            self.person = pygame.transform.scale(source, (21, 28))
        except (OSError, pygame.error):
            pass

    def update(self, dt, paused=False):
        if not paused and math.isfinite(dt) and dt > 0:
            self.elapsed = (self.elapsed + min(dt, 0.1)) % 10000

    def render_background(self, crt, camera):
        if self.background is None:
            return False
        if (not math.isfinite(camera.x) or not math.isfinite(camera.y)
                or camera.x < 0 or camera.y < 0 or camera.y > 18):
            return False
        extent = max(1, self.room.width_px - camera.viewport_w)
        progress = min(1.0, camera.x / extent)
        start, end = self.art_view
        # Earth passages join consecutive slices of the same panorama. Keep
        # the slower far plane for arenas and alien worlds.
        travel = 960 * (end - start)
        if (self.room.act_id not in ('act_02', 'act_03', 'act_04', 'act_05')
                or self.room.room_id.endswith('_arena')):
            travel = min(travel, 0.2 * extent)
        x = min(960, max(0, round(960 * start + travel * progress)))
        y = 2 * round(camera.y)
        # Artwork ground is anchored at world y=240. Shift with the camera,
        # filling only the uncovered strip below the foreground floor.
        self._background_view.fill((7, 11, 16))
        self._background_view.blit(self.background, (0, 0), pygame.Rect(x, y, 960, 540 - y))
        crt.composite_opaque_background(self._background_view, known_clean=True)
        return True

    def render_activity(self, crt, camera):
        """Draw ground-anchored background activity without collision or combat."""
        if self.vehicle is None and self.person is None:
            return
        start = max(0, int(camera.x // 640) - 1)
        end = min((self.room.width_px // 640) + 1, int((camera.x + camera.viewport_w) // 640) + 2)
        for segment in range(start, end):
            base = segment * 640
            if self.vehicle is not None:
                x = base + 250 + ((self.elapsed * 12 + segment * 97) % 250)
                sx, sy = camera.world_to_screen(x, 207)
                if -self.vehicle.get_width() < sx < camera.viewport_w:
                    crt.canvas.blit(self.vehicle, (sx, sy))
            if self.person is not None:
                x = base + 470 + math.sin(self.elapsed * 0.4 + segment) * 12
                sx, sy = camera.world_to_screen(x, 212)
                if -self.person.get_width() < sx < camera.viewport_w:
                    crt.canvas.blit(self.person, (sx, sy))
