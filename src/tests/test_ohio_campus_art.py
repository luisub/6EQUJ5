"""MODULE: tests/test_ohio_campus_art.py
PURPOSE: Verify campus art registration, complete fallback and reproducible sources.
CALLED BY: pytest.
HOW TO MODIFY: Use temporary asset copies and preserve existing families and player saves.
"""

from video_game.engine import config
import hashlib
import json
import shutil
from pathlib import Path

import pygame
import pytest
from PIL import Image

from video_game.engine.native_room_assets import load_native_room_family
from video_game.engine.room_art_contracts import manifest_template
from video_game.engine.world import Camera
from video_game.tools.build_ohio_campus_art import FAR_HASH, FAR_MASTER, WORLD_HASH, build_far, build_world

ASSETS = config.ASSETS_DIR


@pytest.fixture
def family_copy(tmp_path):
    pygame.init()
    pygame.display.set_mode((960, 540))
    root = tmp_path / 'assets'
    shutil.copytree(ASSETS / 'environments/ohio_campus_v1', root / 'environments/ohio_campus_v1')
    yield root
    pygame.quit()


def test_campus_family_contract_coverage_and_rebuild(family_copy, tmp_path):
    contract = manifest_template('ohio_campus_v1')
    assert contract['room_id'] == 'act_01_ohio_campus'
    assert contract['world'] == [1280, 288]
    family = load_native_room_family(family_copy, 'act_01_ohio_campus', (1280, 288))
    assert family is not None
    camera = Camera(480, 270)
    camera.set_world_bounds(1280, 288)
    for x in (0, 400, 800):
        for y in (0, 18):
            camera.x, camera.y = x, y
            far, world = family.crops(camera)
            assert far.get_size() == world.get_size() == (960, 540)
    assert load_native_room_family(family_copy, 'act_01_ohio_campus', (1281, 288)) is None
    rebuilt = tmp_path / 'world.png'
    build_world(rebuilt)
    assert hashlib.sha256(rebuilt.read_bytes()).hexdigest() == WORLD_HASH
    rebuilt_far = tmp_path / 'far.png'
    build_far(rebuilt_far)
    assert hashlib.sha256(rebuilt_far.read_bytes()).hexdigest() == FAR_HASH
    assert hashlib.sha256((family_copy / 'environments/ohio_campus_v1/far_1152x544.png').read_bytes()).hexdigest() == FAR_HASH


def test_far_rebuild_rejects_unreviewed_master(tmp_path):
    changed = tmp_path / 'master.png'
    changed.write_bytes(FAR_MASTER.read_bytes() + b'changed')
    with pytest.raises(ValueError, match='far master hash'):
        build_far(tmp_path / 'far.png', master=changed)
    assert not (tmp_path / 'far.png').exists()


@pytest.mark.parametrize('defect', ['world_size', 'world_origin', 'far_repeat', 'world_hash', 'far_hash', 'far_alpha'])
def test_corrupt_family_falls_back_completely(family_copy, defect):
    base = family_copy / 'environments/ohio_campus_v1'
    manifest = base / 'manifest.json'
    doc = json.loads(manifest.read_text())
    if defect == 'world_size':
        doc['world'] = [1279, 288]
    elif defect == 'world_origin':
        doc['layers'][1]['origin'] = [1, 0]
    elif defect == 'far_repeat':
        doc['layers'][0]['repeat'] = True
    elif defect == 'world_hash':
        doc['layers'][1]['sha256'] = '0' * 64
    elif defect == 'far_hash':
        doc['layers'][0]['sha256'] = '0' * 64
    else:
        far_path = base / 'far_1152x544.png'
        with Image.open(far_path) as source:
            far = source.convert('RGBA')
        far.putpixel((0, 0), (0, 0, 0, 0))
        far.save(far_path)
        doc['layers'][0]['sha256'] = hashlib.sha256(far_path.read_bytes()).hexdigest()
    manifest.write_text(json.dumps(doc))
    assert load_native_room_family(family_copy, 'act_01_ohio_campus', (1280, 288)) is None
