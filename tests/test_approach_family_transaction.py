"""MODULE: tests/test_approach_family_transaction.py
PURPOSE: Verify explicit promotion, path safety and recoverable approach-family transactions.
CALLED BY: pytest tests/test_approach_family_transaction.py.
HOW TO MODIFY: Use temporary assets and failure injection; never write live game assets.
"""

from . import REPO_ROOT

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image, UnidentifiedImageError
from video_game.engine import asset_transactions
from video_game.tools import build_approach_family as builder


@pytest.fixture
def inputs(tmp_path):
    assets = tmp_path / 'assets'
    assets.mkdir()
    (assets / 'untouched.txt').write_text('original')
    far = tmp_path / 'reviewed_far.png'
    world = tmp_path / 'reviewed_world.png'
    Image.new('RGBA', (1152, 544), (10, 20, 30, 255)).save(far)
    image = Image.new('RGBA', (1920, 576), (50, 60, 70, 128))
    image.putpixel((0, 0), (0, 0, 0, 0))
    image.save(world)
    return assets, far, world, tmp_path / 'archive'


def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def test_default_and_dry_run_never_create_or_replace(inputs):
    assets, far, world, archive = inputs
    before = snapshot(assets)
    result = builder.build_family(assets_dir=assets, archive_dir=archive)
    assert result['status'] == 'absent' and result['integrity'] == 'not_inspected'
    result = builder.build_family(assets_dir=assets, archive_dir=archive, far=far, world=world)
    assert result['status'] == 'validated'
    assert snapshot(assets) == before
    assert not archive.exists()
    assert not (assets.parent / '.assets-asset-build-pending.json').exists()


def test_promotion_is_complete_manifest_last_and_preserves_others(inputs, monkeypatch):
    assets, far, world, archive = inputs
    real_replace = asset_transactions.os.replace
    order = []
    def record(source, target):
        target = Path(target)
        if target.parent == assets / builder.FAMILY:
            order.append(target.name)
        return real_replace(source, target)
    monkeypatch.setattr(asset_transactions.os, 'replace', record)
    result = builder.build_family(assets_dir=assets, archive_dir=archive, far=far, world=world, promote=True)
    assert result['status'] == 'promoted'
    assert order == [builder.FAR, builder.WORLD, builder.MANIFEST]
    manifest = json.loads((assets / builder.FAMILY / builder.MANIFEST).read_text())
    assert manifest == result['manifest']
    assert manifest['schema_version'] == 1 and manifest['room_id'] == 'act_01_approach'
    assert [layer['id'] for layer in manifest['layers']] == ['far', 'world']
    assert manifest['layers'][0]['sha256'] == builder._sha(far)
    assert manifest['layers'][1]['sha256'] == builder._sha(world)
    assert (assets / 'untouched.txt').read_text() == 'original'
    record_file = json.loads((Path(result['archive']) / 'manifest.json').read_text())
    assert all(not entry['existed'] for entry in record_file['files'])


@pytest.mark.parametrize('failure_index', [1, 2, 3])
def test_replacement_failure_restores_existing_and_removes_absent(inputs, monkeypatch, failure_index):
    assets, far, world, archive = inputs
    family = assets / builder.FAMILY
    family.mkdir(parents=True)
    (family / builder.FAR).write_bytes(b'old far')
    before = snapshot(assets)
    real_replace = asset_transactions.os.replace
    attempts = 0
    def fail_second(source, target):
        nonlocal attempts
        if Path(target).parent == family:
            attempts += 1
            if attempts == failure_index:
                raise OSError('simulated replacement failure')
        return real_replace(source, target)
    monkeypatch.setattr(asset_transactions.os, 'replace', fail_second)
    with pytest.raises(OSError, match='simulated'):
        builder.build_family(assets_dir=assets, archive_dir=archive, far=far, world=world, promote=True)
    assert snapshot(assets) == before
    assert not (assets.parent / '.assets-asset-build-pending.json').exists()


def test_corrupt_or_unsafe_inputs_do_not_write(inputs, tmp_path):
    assets, far, world, archive = inputs
    before = snapshot(assets)
    bad = tmp_path / 'bad.png'
    bad.write_bytes(b'not an image')
    with pytest.raises(UnidentifiedImageError):
        builder.build_family(assets_dir=assets, archive_dir=archive, far=bad, world=world, promote=True)
    link = tmp_path / 'link.png'
    link.symlink_to(far)
    with pytest.raises(ValueError, match='Symlink'):
        builder.build_family(assets_dir=assets, archive_dir=archive, far=link, world=world, promote=True)
    with pytest.raises(ValueError, match='duplicate'):
        builder._check_outputs(assets, [builder.OUTPUTS[0]] * 3)
    with pytest.raises(ValueError, match='Unsafe'):
        builder._relative('../outside')
    assert snapshot(assets) == before
    assert not archive.exists()


def test_target_and_stage_symlink_components_rejected(inputs, tmp_path):
    assets, far, world, archive = inputs
    (assets / 'environments').symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match='Symlink'):
        builder.build_family(assets_dir=assets, archive_dir=archive, far=far, world=world, promote=True)
    stage = tmp_path / 'stage'
    stage.mkdir()
    (stage / 'environments').symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match='Symlink'):
        builder._check_outputs(stage, builder.OUTPUTS)
    assert not archive.exists()


def test_lock_contention_is_rejected_without_writes(inputs):
    assets, far, world, archive = inputs
    descriptor = os.open(assets, os.O_RDONLY)
    try:
        builder.fcntl.flock(descriptor, builder.fcntl.LOCK_EX | builder.fcntl.LOCK_NB)
        with pytest.raises(RuntimeError, match='active'):
            builder.build_family(assets_dir=assets, archive_dir=archive, far=far, world=world, promote=True)
    finally:
        os.close(descriptor)
    assert not archive.exists()
    assert not (assets / builder.FAMILY).exists()


def test_interrupted_child_recovers_before_next_explicit_attempt(inputs):
    assets, far, world, archive = inputs
    before = snapshot(assets)
    script = '''
import os, sys
from pathlib import Path
from video_game.engine import asset_transactions
from video_game.tools.build_approach_family import build_family
root, far, world, archive = map(Path, sys.argv[1:])
real = asset_transactions.os.replace
def crash(source, target):
    result = real(source, target)
    if Path(target) == root / 'environments/ohio_approach_v1/far_1152x544.png':
        os._exit(71)
    return result
asset_transactions.os.replace = crash
build_family(assets_dir=root, far=far, world=world, archive_dir=archive, promote=True)
'''
    result = subprocess.run([sys.executable, '-c', script, str(assets), str(far), str(world), str(archive)],
                            cwd=REPO_ROOT, env=os.environ.copy(), check=False)
    assert result.returncode == 71
    journal = assets.parent / '.assets-asset-build-pending.json'
    assert journal.exists()
    with pytest.raises(RuntimeError, match='Pending'):
        builder.build_family(assets_dir=assets, archive_dir=archive)
    # An explicit attempt first restores the interrupted family, then rejects this bad input.
    with pytest.raises(FileNotFoundError):
        builder.build_family(assets_dir=assets, archive_dir=archive, far=assets.parent / 'missing.png', world=world, promote=True)
    assert snapshot(assets) == before
    assert not journal.exists()


def test_invalid_size_and_nonopaque_far_never_write(inputs, tmp_path):
    assets, far, world, archive = inputs
    before = snapshot(assets)
    wrong = tmp_path / 'wrong.png'
    Image.new('RGBA', (12, 12), (1, 2, 3, 255)).save(wrong)
    with pytest.raises(ValueError, match='dimensions or mode'):
        builder.build_family(assets_dir=assets, archive_dir=archive, far=far, world=wrong, promote=True)
    Image.new('RGBA', (1152, 544), (1, 2, 3, 254)).save(wrong)
    with pytest.raises(ValueError, match='opaque'):
        builder.build_family(assets_dir=assets, archive_dir=archive, far=wrong, world=world, promote=True)
    assert snapshot(assets) == before
    assert not archive.exists()


def test_bad_recovery_paths_fail_closed_without_touching_assets(inputs, tmp_path):
    assets, far, world, archive = inputs
    journal = assets.parent / '.assets-asset-build-pending.json'
    journal.write_text(json.dumps({'asset_root': str(assets), 'archive': str(archive),
                                   'files': [{'path': '../outside', 'existed': False}]}))
    outside = tmp_path / 'outside'
    outside.write_text('preserve')
    with pytest.raises(ValueError, match='Unsafe'):
        builder.build_family(assets_dir=assets, archive_dir=archive, far=far, world=world, promote=True)
    assert journal.exists()
    assert outside.read_text() == 'preserve'
    assert not (assets / builder.FAMILY).exists()


def test_real_cli_dry_run_without_writes(inputs):
    assets, far, world, archive = inputs
    before = snapshot(assets)
    result = subprocess.run([sys.executable, '-m', 'video_game.tools.build_approach_family',
                             '--assets-dir', str(assets), '--archive-dir', str(archive),
                             '--far', str(far), '--world', str(world), '--dry-run'],
                            cwd=REPO_ROOT, env=os.environ.copy(),
                            capture_output=True, text=True, check=True)
    assert json.loads(result.stdout)['status'] == 'validated'
    assert snapshot(assets) == before
    assert not archive.exists()


@pytest.mark.parametrize('alpha', [0, 255])
def test_blank_or_flattened_world_is_rejected(inputs, tmp_path, alpha):
    assets, far, world, archive = inputs
    bad = tmp_path / 'world_bad.png'
    Image.new('RGBA', (1920, 576), (1, 2, 3, alpha)).save(bad)
    before = snapshot(assets)
    with pytest.raises(ValueError, match='transparent and visible'):
        builder.build_family(assets_dir=assets, archive_dir=archive, far=far, world=bad, promote=True)
    assert snapshot(assets) == before
    assert not archive.exists()


def test_corrupt_recovery_backup_keeps_journal_and_current_file(inputs):
    assets, far, world, archive_root = inputs
    family = assets / builder.FAMILY
    family.mkdir(parents=True)
    target = family / builder.FAR
    target.write_bytes(b'new partial family')
    archive = archive_root / 'interrupted'
    backup = archive / 'video_game' / 'assets' / builder.OUTPUTS[0]
    backup.parent.mkdir(parents=True)
    backup.write_bytes(b'corrupt backup')
    journal = assets.parent / '.assets-asset-build-pending.json'
    journal.write_text(json.dumps({'asset_root': str(assets), 'archive': str(archive),
                                   'files': [{'path': builder.OUTPUTS[0].as_posix(), 'existed': True,
                                              'sha256': '0' * 64}]}))
    with pytest.raises(RuntimeError, match='Backup hash mismatch'):
        builder.build_family(assets_dir=assets, archive_dir=archive_root, far=far, world=world, promote=True)
    assert journal.exists()
    assert target.read_bytes() == b'new partial family'


def test_no_source_reports_partial_and_present_without_claiming_integrity(inputs):
    assets, far, world, archive = inputs
    family = assets / builder.FAMILY
    family.mkdir(parents=True)
    (family / builder.FAR).write_bytes(b'invalid')
    partial = builder.build_family(assets_dir=assets, archive_dir=archive)
    assert partial['status'] == 'partial_not_inspected'
    assert partial['integrity'] == 'not_inspected'
    (family / builder.WORLD).write_bytes(b'invalid')
    (family / builder.MANIFEST).write_bytes(b'invalid')
    before = snapshot(assets)
    present = builder.build_family(assets_dir=assets, archive_dir=archive)
    assert present['status'] == 'present_not_inspected'
    assert present['integrity'] == 'not_inspected'
    assert snapshot(assets) == before
    assert not archive.exists()
