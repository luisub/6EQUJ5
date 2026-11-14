"""PURPOSE: Verify energy-stream manifest validation and safe family promotion.
CALLED BY: pytest tests/test_energy_stream_install.py.
HOW TO MODIFY: Keep temporary assets, rollback, corruption and fallback checks.
"""
import hashlib
import json
import os
import shutil
from pathlib import Path

from PIL import Image, ImageDraw
import pygame
import pytest

from video_game.engine import asset_transactions
from video_game.engine.energy_stream_assets import FAMILY, IMAGE_NAME, load_energy_filament
from video_game.tools import build_energy_stream


@pytest.fixture
def display(monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER', 'dummy')
    pygame.display.init(); pygame.display.set_mode((1, 1))
    yield
    pygame.display.quit()


@pytest.fixture
def setup(tmp_path):
    root = tmp_path / 'assets'; root.mkdir()
    source = tmp_path / 'source.png'
    image = Image.new('RGBA', (96, 24), (0, 0, 0, 0))
    painter = ImageDraw.Draw(image)
    painter.line((4, 12, 88, 12), fill=(95, 180, 255, 90), width=8)
    painter.line((4, 12, 88, 12), fill=(220, 250, 255, 255), width=2)
    image.save(source)
    return root, source


def install_fixture(root, source):
    result = build_energy_stream.build(source, {'source':'test fixture'}, assets_dir=root)
    directory = root / FAMILY; directory.mkdir(parents=True)
    (directory / IMAGE_NAME).write_bytes(source.read_bytes())
    (directory / 'manifest.json').write_text(json.dumps(result['manifest']))
    return directory, result['manifest']


def test_temp_promotion_roundtrip_and_manifest_last(setup, display, monkeypatch):
    root, source = setup
    paths_seen = []
    original = build_energy_stream.promote_group
    def observe(asset_root, stage, archive, group, paths):
        paths_seen.extend(paths)
        assert all((stage / path).is_file() for path in paths)
        return original(asset_root, stage, archive, group, paths)
    monkeypatch.setattr(build_energy_stream, 'promote_group', observe)
    result = build_energy_stream.build(source, {'source':'test fixture'}, assets_dir=root, promote=True)
    assert result['status'] == 'promoted'
    assert paths_seen == [FAMILY / IMAGE_NAME, FAMILY / 'manifest.json']
    manifest = json.loads((root / FAMILY / 'manifest.json').read_text())
    assert manifest == result['manifest']
    assert manifest['pivot'] == [4, 12] and manifest['density'] == 2
    assert manifest['image']['sha256'] == hashlib.sha256(source.read_bytes()).hexdigest()
    image = load_energy_filament(root)
    assert image is not None and image.get_size() == (96, 24)
    assert image.get_at((4, 12)).a == 255 and image.get_at((0, 0)).a == 0
    assert not (root.parent / '.assets-asset-build-pending.json').exists()
    with pytest.raises(FileExistsError):
        build_energy_stream.build(source, {'source':'test fixture'}, assets_dir=root, promote=True)


@pytest.mark.parametrize('mutation', ['pivot', 'density', 'dimensions', 'kind', 'extra', 'provenance', 'hash', 'bool_version'])
def test_loader_rejects_invalid_metadata(setup, display, mutation):
    root, source = setup; directory, manifest = install_fixture(root, source)
    if mutation == 'pivot': manifest['pivot'] = [5, 12]
    elif mutation == 'density': manifest['density'] = 1
    elif mutation == 'dimensions': manifest['image']['dimensions'] = [97, 24]
    elif mutation == 'kind': manifest['kind'] = 'unknown'
    elif mutation == 'extra': manifest['unexpected'] = True
    elif mutation == 'provenance': manifest['provenance'] = {}
    elif mutation == 'hash': manifest['image']['sha256'] = '0' * 64
    else: manifest['schema_version'] = True
    (directory / 'manifest.json').write_text(json.dumps(manifest))
    assert load_energy_filament(root) is None


def test_missing_corrupt_symlink_and_journal_fallback(setup, display):
    root, source = setup
    assert load_energy_filament(root) is None
    directory, manifest = install_fixture(root, source)
    (directory / IMAGE_NAME).write_bytes(b'corrupted')
    assert load_energy_filament(root) is None
    (directory / IMAGE_NAME).unlink()
    (directory / IMAGE_NAME).symlink_to(source)
    assert load_energy_filament(root) is None
    (directory / IMAGE_NAME).unlink(); (directory / IMAGE_NAME).write_bytes(source.read_bytes())
    journal = root.parent / '.assets-asset-build-pending.json'
    journal.write_text(json.dumps({'asset_root':str(root.resolve()), 'archive':str(root.parent/'archive'), 'files':[]}))
    assert load_energy_filament(root) is None
    with pytest.raises(RuntimeError, match='Pending'):
        build_energy_stream.build(source, {'source':'test fixture'}, assets_dir=root)


@pytest.mark.parametrize('mode,size,alpha', [
    ('RGB', (96,24), None), ('RGBA', (95,24), (0,255)),
    ('RGBA', (96,24), (0,128)), ('RGBA', (96,24), (255,255)),
    ('RGBA', (96,24), (0,0)), ('RGBA', (96,24), (0,239)),
    ('RGBA', (96,24), (0,240)),
])
def test_builder_rejects_invalid_source_contract(tmp_path, mode, size, alpha):
    root = tmp_path / 'assets'; root.mkdir(); source=tmp_path/'wrong.png'
    image = Image.new(mode, size, (0,0,0) if mode == 'RGB' else (0,0,0,alpha[0]))
    if alpha is not None:
        image.putpixel((0,0), (255,255,255,alpha[1]))
    image.save(source)
    with pytest.raises(ValueError):
        build_energy_stream.build(source, {'source':'test fixture'}, assets_dir=root)
    assert not (root / FAMILY).exists()


def test_near_opaque_emissive_core_is_accepted(setup, display):
    root, source = setup
    image = Image.new('RGBA', (96,24), (0,0,0,0))
    ImageDraw.Draw(image).line((4,12,80,12), fill=(220,245,255,253), width=2)
    image.save(source)
    directory, _ = install_fixture(root, source)
    loaded = load_energy_filament(root)
    assert loaded is not None and loaded.get_at((20,12)).a == 253
    assert (directory / IMAGE_NAME).read_bytes() == source.read_bytes()


def test_temp_transaction_rolls_back_when_manifest_promotion_fails(setup, monkeypatch):
    root, source = setup
    original = asset_transactions.os.replace
    def fail_manifest(src, dst):
        if Path(dst) == root / FAMILY / 'manifest.json':
            raise OSError('injected manifest replacement failure')
        return original(src, dst)
    monkeypatch.setattr(asset_transactions.os, 'replace', fail_manifest)
    with pytest.raises(OSError, match='injected'):
        build_energy_stream.build(source, {'source':'test fixture'}, assets_dir=root, promote=True)
    assert not (root / FAMILY / IMAGE_NAME).exists()
    assert not (root / FAMILY / 'manifest.json').exists()
    assert not (root.parent / '.assets-asset-build-pending.json').exists()


def test_symlink_target_and_archive_inside_root_are_rejected(setup):
    root, source = setup
    outside = root.parent / 'outside'; outside.mkdir()
    (root / 'effects').mkdir(); (root / FAMILY).symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match='[Ss]ymlink'):
        build_energy_stream.build(source, {'source':'test fixture'}, assets_dir=root)
    (root / FAMILY).unlink()
    with pytest.raises(ValueError, match='outside'):
        build_energy_stream.build(source, {'source':'test fixture'}, assets_dir=root, archive_dir=root/'archive')


def test_active_asset_lock_blocks_builder_without_writing(setup):
    root, source = setup
    if asset_transactions.fcntl is None:
        pytest.skip('Asset builder requires fcntl')
    descriptor = os.open(root, os.O_RDONLY)
    try:
        asset_transactions.fcntl.flock(descriptor, asset_transactions.fcntl.LOCK_EX | asset_transactions.fcntl.LOCK_NB)
        with pytest.raises(RuntimeError, match='Another asset build'):
            build_energy_stream.build(source, {'source':'test fixture'}, assets_dir=root, promote=True)
    finally:
        os.close(descriptor)
    assert not (root / FAMILY).exists()


def test_invalid_provenance_never_stages_files(setup):
    root, source = setup
    with pytest.raises((ValueError, TypeError)):
        build_energy_stream.build(source, {'bad':float('nan')}, assets_dir=root, promote=True)
    assert not (root / FAMILY).exists()



@pytest.mark.parametrize("retired_name", ["energy_filament_v1", "energy_filament_v2"])
@pytest.mark.parametrize("defect", ["missing", "corrupt"])
def test_only_canonical_family_is_loaded(setup, display, retired_name, defect):
    from video_game.engine.energy_stream_assets import load_energy_filament_with_family
    root, source = setup
    build_energy_stream.build(source, {"source": "canonical fixture"}, assets_dir=root, promote=True)
    image, family = load_energy_filament_with_family(root)
    assert image is not None and family == FAMILY
    assert family == Path("effects/energy_filament")
    retired = root / "effects" / retired_name
    shutil.copytree(root / FAMILY, retired)
    active = root / FAMILY / IMAGE_NAME
    if defect == "missing":
        active.unlink()
    else:
        active.write_bytes(b"corrupt")
    assert load_energy_filament_with_family(root) == (None, None)
    assert (retired / IMAGE_NAME).read_bytes() == source.read_bytes()
