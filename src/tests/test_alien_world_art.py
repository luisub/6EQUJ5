"""Verify every journey world uses its own complete runtime art families."""
import hashlib
import json
import shutil

import pygame
import pytest

from video_game.engine.alien_journey import journey_data
from video_game.engine.campaign_scenery import (
    CampaignScenery, load_campaign_background, load_campaign_boss,
)
from video_game.engine.config import ASSETS_DIR
from video_game.engine.world import Room


@pytest.fixture
def display(monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER', 'dummy')
    pygame.display.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.display.quit()


@pytest.mark.parametrize('world', journey_data()['worlds'], ids=lambda world: world['civ_id'])
def test_installed_world_has_native_landscape_and_guardian(display, world):
    rooms = journey_data()['rooms']
    field_id = world['id'] + '_field'
    art_id = rooms[field_id]['art_id']
    landscape = load_campaign_background(ASSETS_DIR, art_id)
    guardian = load_campaign_boss(ASSETS_DIR, world['boss_id'], allow_fallback=False)
    assert landscape is not None, f'{art_id} must not use a tiled profile fallback'
    assert guardian is not None, f"{world['boss_id']} must not use an enlarged patrol pose"
    assert landscape.get_size() == (1920, 540)
    assert guardian.get_size() == (256, 192)
    visible = pygame.mask.from_surface(guardian, 0)
    assert 0 < visible.count() < 256 * 192

    # The previous fallback repeated the same 540px tile across the landscape.
    left = pygame.image.tobytes(landscape.subsurface((0, 0, 540, 540)), 'RGB')
    next_tile = pygame.image.tobytes(landscape.subsurface((540, 0, 540, 540)), 'RGB')
    assert left != next_tile
    for room_id, relative_path in ((field_id, world['field_room']),
                                   (world['id'] + '_arena', world['arena_room'])):
        room = Room.load_from_file(ASSETS_DIR.parent / 'data/levels' / relative_path)
        scenery = CampaignScenery(ASSETS_DIR, room, rooms[room_id])
        assert scenery.background_source == {'kind': 'native', 'art_id': art_id}
        assert scenery.vehicle is None and scenery.person is None


def test_all_installed_world_families_have_distinct_images_and_provenance(display):
    backgrounds, guardians = set(), set()
    for world in journey_data()['worlds']:
        art_id = journey_data()['rooms'][world['id'] + '_field']['art_id']
        for relative, hashes in (
            (f'environments/campaign_worlds/{art_id}', backgrounds),
            (f"sprites/bosses/campaign/{world['boss_id']}", guardians),
        ):
            directory = ASSETS_DIR / relative
            manifest = json.loads((directory / 'manifest.json').read_text())
            image = directory / manifest['image']['file']
            assert manifest['provenance']
            digest = hashlib.sha256(image.read_bytes()).hexdigest()
            assert digest == manifest['image']['sha256']
            hashes.add(digest)
    assert len(backgrounds) == len(guardians) == 11


def test_new_world_corruption_is_not_accepted_as_native_art(tmp_path, display):
    root = tmp_path / 'assets'
    for relative in ('environments/campaign_worlds/realm_fasr_005_v1',
                     'sprites/bosses/campaign/guardian_fasr_005'):
        directory = root / relative
        shutil.copytree(ASSETS_DIR / relative, directory)
        manifest = json.loads((directory / 'manifest.json').read_text())
        (directory / manifest['image']['file']).write_bytes(b'corrupt fixture')
    assert load_campaign_background(root, 'realm_fasr_005_v1') is None
    assert load_campaign_boss(root, 'guardian_fasr_005', allow_fallback=False) is None


def test_proxima_guardian_feet_meet_its_collision_floor(display):
    body = load_campaign_boss(ASSETS_DIR, 'guardian_fasr_005', allow_fallback=False)
    assert body is not None
    # Nearly invisible export halos must not create empty space below the feet.
    opaque_body = pygame.mask.from_surface(body, 64)
    bounds = opaque_body.get_bounding_rects()
    assert bounds
    assert max(rect.bottom for rect in bounds) >= body.get_height() - 1
