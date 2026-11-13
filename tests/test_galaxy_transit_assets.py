"""PURPOSE: Verify safe galaxy transit asset loading and transactional promotion.
CALLED BY: pytest tests/test_galaxy_transit_assets.py.
HOW TO MODIFY: Keep strict mode/hash, staging, fallback and rollback coverage.
"""
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw
import pygame
import pytest

from video_game.engine import asset_transactions
from video_game.engine.galaxy_transit_assets import FAMILY, IMAGES, load_galaxy_transit
from tools import build_galaxy_transit


@pytest.fixture
def display(monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER', 'dummy')
    pygame.display.init(); pygame.display.set_mode((1, 1))
    yield
    pygame.display.quit()


@pytest.fixture
def sources(tmp_path):
    root = tmp_path / 'assets'; root.mkdir()
    galaxy = tmp_path / 'galaxy.png'; vortex = tmp_path / 'vortex.png'
    Image.new('RGB', (960, 540), (3, 9, 22)).save(galaxy)
    image = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
    ImageDraw.Draw(image).ellipse((80, 80, 432, 432), outline=(50, 180, 255, 200), width=5)
    image.save(vortex)
    return root, galaxy, vortex


def test_new_family_promotion_preserves_bytes_and_manifest_is_last(sources, display, monkeypatch):
    root, galaxy, vortex = sources
    paths_seen = []
    original = build_galaxy_transit.promote_group
    def observe(root, stage, archive, group, paths):
        paths_seen.extend(paths)
        assert all((stage / path).is_file() for path in paths)
        return original(root, stage, archive, group, paths)
    monkeypatch.setattr(build_galaxy_transit, 'promote_group', observe)
    outcome = build_galaxy_transit.build(galaxy, vortex, {'source':'test'}, assets_dir=root, promote=True)
    assert paths_seen == [FAMILY / IMAGES['galaxy_map'][0], FAMILY / IMAGES['vortex'][0], FAMILY / 'manifest.json']
    family = root / FAMILY
    for name, source in [('galaxy_map', galaxy), ('vortex', vortex)]:
        record = outcome['manifest']['images'][name]
        assert record['sha256'] == hashlib.sha256(source.read_bytes()).hexdigest()
        assert (family / record['file']).read_bytes() == source.read_bytes()
    result = load_galaxy_transit(root)
    assert result['galaxy_map'].get_size() == (960, 540)
    assert result['vortex'].get_size() == (512, 512)
    assert result['vortex'].get_at((0, 0)).a == 0
    assert not (root.parent / '.assets-asset-build-pending.json').exists()
    with pytest.raises(FileExistsError):
        build_galaxy_transit.build(galaxy, vortex, {'source':'test'}, assets_dir=root, promote=True)


@pytest.mark.parametrize('mutation', ['schema', 'kind', 'extra', 'provenance', 'name', 'dimension', 'hash', 'missing'])
def test_loader_rejects_invalid_manifest(sources, display, mutation):
    root, galaxy, vortex = sources
    result = build_galaxy_transit.build(galaxy, vortex, {'source':'test'}, assets_dir=root, promote=True)
    manifest = result['manifest']; directory = root / FAMILY
    if mutation == 'schema': manifest['schema_version'] = True
    elif mutation == 'kind': manifest['kind'] = 'unknown'
    elif mutation == 'extra': manifest['other'] = True
    elif mutation == 'provenance': manifest['provenance'] = {}
    elif mutation == 'name': manifest['images']['vortex']['file'] = '../outside.png'
    elif mutation == 'dimension': manifest['images']['galaxy_map']['dimensions'] = [960, 539]
    elif mutation == 'hash': manifest['images']['galaxy_map']['sha256'] = '0' * 64
    else: del manifest['images']['vortex']
    (directory / 'manifest.json').write_text(json.dumps(manifest))
    assert load_galaxy_transit(root) is None


@pytest.mark.parametrize('which,mode,size,alpha', [
    ('galaxy', 'RGBA', (960, 540), 255), ('galaxy', 'RGB', (959, 540), None),
    ('vortex', 'RGB', (512, 512), None), ('vortex', 'RGBA', (511, 512), 0),
    ('vortex', 'RGBA', (512, 512), 0), ('vortex', 'RGBA', (512, 512), 255),
])
def test_invalid_source_is_never_promoted(sources, which, mode, size, alpha):
    root, galaxy, vortex = sources
    target = galaxy if which == 'galaxy' else vortex
    Image.new(mode, size, (10,20,30) if mode == 'RGB' else (10,20,30,alpha)).save(target)
    with pytest.raises(ValueError):
        build_galaxy_transit.build(galaxy, vortex, {'source':'test'}, assets_dir=root, promote=True)
    assert not (root / FAMILY).exists()


def test_missing_corrupt_symlink_and_pending_journal_return_none(sources, display):
    root, galaxy, vortex = sources
    assert load_galaxy_transit(root) is None
    build_galaxy_transit.build(galaxy, vortex, {'source':'test'}, assets_dir=root, promote=True)
    file = root / FAMILY / IMAGES['vortex'][0]
    file.write_bytes(b'corrupted'); assert load_galaxy_transit(root) is None
    file.unlink(); file.symlink_to(vortex); assert load_galaxy_transit(root) is None
    file.unlink(); file.write_bytes(vortex.read_bytes())
    journal = root.parent / '.assets-asset-build-pending.json'
    journal.write_text(json.dumps({'asset_root':str(root.resolve()), 'archive':str(root.parent/'archive'), 'files':[]}))
    assert load_galaxy_transit(root) is None
    with pytest.raises(RuntimeError, match='Pending'):
        build_galaxy_transit.build(galaxy, vortex, {'source':'test'}, assets_dir=root)


def test_rollback_removes_both_images_on_manifest_failure(sources, monkeypatch):
    root, galaxy, vortex = sources
    original = asset_transactions.os.replace
    def fail_manifest(src, dst):
        if Path(dst) == root / FAMILY / 'manifest.json':
            raise OSError('injected manifest failure')
        return original(src, dst)
    monkeypatch.setattr(asset_transactions.os, 'replace', fail_manifest)
    with pytest.raises(OSError, match='injected'):
        build_galaxy_transit.build(galaxy, vortex, {'source':'test'}, assets_dir=root, promote=True)
    assert all(not (root / FAMILY / info[0]).exists() for info in IMAGES.values())
    assert not (root / FAMILY / 'manifest.json').exists()
    assert not (root.parent / '.assets-asset-build-pending.json').exists()


def test_builder_rejects_symlink_target_and_archive_inside_assets(sources):
    root, galaxy, vortex = sources
    outside = root.parent / 'outside'; outside.mkdir()
    (root / 'effects').mkdir(); (root / FAMILY).symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match='[Ss]ymlink'):
        build_galaxy_transit.build(galaxy, vortex, {'source':'test'}, assets_dir=root)
    (root / FAMILY).unlink()
    with pytest.raises(ValueError, match='outside'):
        build_galaxy_transit.build(galaxy, vortex, {'source':'test'}, assets_dir=root, archive_dir=root/'archive')


def test_locked_builder_and_bad_provenance_never_write(sources):
    root, galaxy, vortex = sources
    with pytest.raises((ValueError, TypeError)):
        build_galaxy_transit.build(galaxy, vortex, {'bad':float('nan')}, assets_dir=root, promote=True)
    if asset_transactions.fcntl is None:
        pytest.skip('Asset builder requires fcntl')
    fd = os.open(root, os.O_RDONLY)
    try:
        asset_transactions.fcntl.flock(fd, asset_transactions.fcntl.LOCK_EX | asset_transactions.fcntl.LOCK_NB)
        with pytest.raises(RuntimeError, match='Another asset build'):
            build_galaxy_transit.build(galaxy, vortex, {'source':'test'}, assets_dir=root, promote=True)
    finally:
        os.close(fd)
    assert not (root / FAMILY).exists()


def test_loader_rejects_rehashed_wrong_image_mode(sources, display):
    root, galaxy, vortex = sources
    result = build_galaxy_transit.build(galaxy, vortex, {'source':'test'}, assets_dir=root, promote=True)
    manifest = result['manifest']; directory = root / FAMILY
    image = directory / IMAGES['galaxy_map'][0]
    Image.new('RGBA', (960, 540), (1, 2, 3, 255)).save(image)
    manifest['images']['galaxy_map']['sha256'] = hashlib.sha256(image.read_bytes()).hexdigest()
    (directory / 'manifest.json').write_text(json.dumps(manifest))
    assert load_galaxy_transit(root) is None


def test_staging_tamper_and_symlink_sources_are_rejected(sources, monkeypatch):
    root, galaxy, vortex = sources
    link = root.parent / 'linked.png'; link.symlink_to(galaxy)
    with pytest.raises(ValueError, match='[Ss]ymlink'):
        build_galaxy_transit.build(link, vortex, {'source':'test'}, assets_dir=root, promote=True)
    original = build_galaxy_transit.shutil.copyfile
    def tamper(source, dest):
        original(source, dest)
        if Path(dest).name == IMAGES['vortex'][0]:
            Path(dest).write_bytes(b'tampered')
    monkeypatch.setattr(build_galaxy_transit.shutil, 'copyfile', tamper)
    with pytest.raises(IOError, match='Staged image differs'):
        build_galaxy_transit.build(galaxy, vortex, {'source':'test'}, assets_dir=root, promote=True)
    assert not (root / FAMILY).exists()
