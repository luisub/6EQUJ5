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
from .alien_journey import journey_data

LOGGER = logging.getLogger(__name__)
ART_IDS = {'act_02': 'neo_denver_v1', 'act_03': 'area_51_v1',
           'act_04': 'vla_rift_v1', 'act_05': 'gobekli_tepe_v1'}
ALIEN_CIV_IDS = tuple(w['boss_id'].removeprefix('guardian_fasr_') for w in journey_data()['worlds'])
ALIEN_BACKGROUND_IDS = frozenset(f'realm_fasr_{ident}_v1' for ident in ALIEN_CIV_IDS)
GUARDIAN_IDS = frozenset(f'guardian_fasr_{ident}' for ident in ALIEN_CIV_IDS)
BACKGROUND_IDS = (frozenset(ART_IDS.values()) | {'area_51_hangar_v1', 'gobekli_archive_v1', 'gobekli_tepe_v2',
                                              'core_network', 'denver_restored'}
                  | ALIEN_BACKGROUND_IDS)
_BACKGROUND_DIRECTORIES = {
    'core_network': 'earth_finale/core_network',
    'denver_restored': 'earth_finale/central_park',
    'neo_denver_v1': 'neo_denver',
    'area_51_v1': 'area_51/exterior',
    'area_51_hangar_v1': 'area_51/hangar',
    'vla_rift_v1': 'vla',
    'gobekli_tepe_v2': 'gobekli_tepe/surface',
    'gobekli_archive_v1': 'gobekli_tepe/archive',
    **{f'realm_fasr_{ident}_v1': f'alien_worlds/fasr_{ident}' for ident in ALIEN_CIV_IDS},
}
INTERIOR_BACKGROUND_IDS = frozenset({'area_51_hangar_v1', 'gobekli_archive_v1'})
# Modern traffic and the reused staff pose belong only in contemporary settings.
MODERN_ACTIVITY_ACTS = frozenset({'act_02', 'act_03', 'act_04'})
MODERN_ACTIVITY_ART_IDS = frozenset({'neo_denver_v1', 'area_51_v1', 'area_51_hangar_v1', 'vla_rift_v1'})
BOSS_IDS = frozenset({'synchronicity', 'amalgam', 'architect', 'core_prime',
                      'portal_warden', 'earth_core_ai'}) | GUARDIAN_IDS
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
    'core_enforcer', 'static_hound', 'precursor_guardian', 'temporal_phantom',
    'phase_watcher', 'temporal_phantom', 'shield_hound',
)))


def _journal_pending(root):
    journal = root.parent / f'.{root.name}-asset-build-pending.json'
    return journal.exists() or journal.is_symlink()


def background_directory(art_id):
    """Return the canonical directory for an installed background identity."""
    try:
        return Path('environments') / _BACKGROUND_DIRECTORIES[art_id]
    except (KeyError, TypeError) as exc:
        raise ValueError(f'Unknown installed background: {art_id}') from exc


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
        density = entry.get('density', 1)
        if density not in (1, 2):
            raise ValueError('invalid enemy fallback density')
        if density == 2:
            expected_hash = entry.get('frame_hashes', {}).get(relative.as_posix())
            if not isinstance(expected_hash, str) or not re.fullmatch('[a-f0-9]{64}', expected_hash):
                raise ValueError('invalid enemy fallback hash')
        if _digest(path) != expected_hash:
            raise ValueError('enemy fallback hash mismatch')
        image = pygame.image.load(str(path)).convert_alpha()
        if image.get_size() != (width * density, height * density):
            raise ValueError('enemy fallback dimensions mismatch')
        scale = min(224 / image.get_width(), 180 / image.get_height())
        image = pygame.transform.scale(image, (round(image.get_width() * scale), round(image.get_height() * scale)))
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
        relative = background_directory(art_id)
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
                source = pygame.image.load(str(root / 'environments/ohio/salvage_yard/wagon.png')).convert_alpha()
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
