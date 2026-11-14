"""MODULE: tests/test_room_family_transaction.py
PURPOSE: Verify explicit multi-room asset contracts and recoverable family promotion.
CALLED BY: pytest tests/test_room_family_transaction.py.
HOW TO MODIFY: Use temporary asset roots and preserve installed approach-v1 fixtures.
"""

from . import REPO_ROOT
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from PIL import Image
from video_game.engine import asset_transactions
from video_game.engine.room_art_contracts import (
    OPAQUE_BACKDROP_FAMILIES, ROOM_ART_FAMILIES, backdrop_manifest_template, manifest_template,
)
from video_game.tools import build_room_family as builder


def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def png(path, size, opaque=False):
    image = Image.new('RGBA', size, (24, 48, 66, 255 if opaque else 128))
    if not opaque:
        image.putpixel((0, 0), (0, 0, 0, 0))
    image.save(path)


@pytest.fixture
def assets_and_sources(tmp_path):
    root = tmp_path / 'assets'
    root.mkdir()
    old = root / 'environments/ohio_approach_v1'
    old.mkdir(parents=True)
    (old / 'manifest.json').write_bytes(b'old-schema-1')
    (root / 'untouched').write_bytes(b'preserve')
    far = tmp_path / 'far.png'
    png(far, (1152, 544), True)
    inputs = {}
    for family in ROOM_ART_FAMILIES:
        template = manifest_template(family)
        world = tmp_path / f'{family}_world.png'
        png(world, tuple(template['layers'][1]['dimensions']))
        props = []
        for index, prop in enumerate(template['props']):
            source = tmp_path / f'{family}_prop_{index}.png'
            png(source, tuple(prop['dimensions']))
            props.append(source)
        inputs[family] = (far, world, props)
    return root, inputs, tmp_path / 'archive'


def test_templates_are_fresh_and_room_specific():
    expected = {'ohio_approach_v2': ('act_01_approach', [960, 288], [804, 208]),
                'ohio_salvage_v1': ('act_01_salvage_yard', [640, 288], [196, 202]),
                'ohio_dish_v1': ('act_01_dish_catwalk', [640, 288], None),
                'ohio_arena_v1': ('act_01_greenkeeper_arena', [640, 288], None)}
    for family, (room, size, origin) in expected.items():
        template = manifest_template(family)
        assert template['room_id'] == room and template['world'] == size
        assert template['schema_version'] == 2 and template['density'] == 2
        assert [x['id'] for x in template['layers']] == ['far', 'world']
        assert (template['props'][0]['origin_world'] if template['props'] else None) == origin
        template['world'][0] = -1
        assert manifest_template(family)['world'] == size
    with pytest.raises(ValueError, match='Unknown'):
        manifest_template('../untrusted')


@pytest.mark.parametrize('family', ROOM_ART_FAMILIES)
def test_explicit_promotion_isolated_and_manifest_last(assets_and_sources, monkeypatch, family):
    root, inputs, archive = assets_and_sources
    far, world, props = inputs[family]
    before = snapshot(root)
    assert builder.build_family(family, assets_dir=root, archive_dir=archive)['status'] == 'absent'
    assert builder.build_family(family, assets_dir=root, archive_dir=archive, far=far, world=world, props=props)['status'] == 'validated'
    assert snapshot(root) == before and not archive.exists()
    real = asset_transactions.os.replace
    order = []
    target_dir = root / 'environments' / family
    def track(src, dst):
        if Path(dst).parent == target_dir:
            order.append(Path(dst).name)
        return real(src, dst)
    monkeypatch.setattr(asset_transactions.os, 'replace', track)
    result = builder.build_family(family, assets_dir=root, archive_dir=archive, far=far, world=world, props=props, promote=True)
    assert result['status'] == 'promoted'
    template = manifest_template(family)
    assert order == [entry['file'] for entry in template['layers'] + template['props']] + ['manifest.json']
    manifest = json.loads((target_dir / 'manifest.json').read_text())
    assert manifest == result['manifest']
    for record, source in zip(manifest['layers'] + manifest['props'], [far, world, *props]):
        assert record['sha256'] == builder._sha(source)
        assert (target_dir / record['file']).read_bytes() == source.read_bytes()
    assert (root / 'environments/ohio_approach_v1/manifest.json').read_bytes() == b'old-schema-1'
    assert (root / 'untouched').read_bytes() == b'preserve'
    assert builder.build_family(family, assets_dir=root, archive_dir=archive)['integrity'] == 'not_inspected'


@pytest.mark.parametrize('failure_index', [1, 2, 3, 4])
def test_interrupted_replacement_restores_mixed_existing_and_absent(assets_and_sources, monkeypatch, failure_index):
    root, inputs, archive = assets_and_sources
    family = 'ohio_approach_v2'
    far, world, props = inputs[family]
    target = root / 'environments' / family
    target.mkdir(parents=True)
    (target / 'far_1152x544.png').write_bytes(b'previous far')
    before = snapshot(root)
    real = asset_transactions.os.replace
    count = 0
    def fail(src, dst):
        nonlocal count
        if Path(dst).parent == target:
            count += 1
            if count == failure_index:
                raise OSError('injected failure')
        return real(src, dst)
    monkeypatch.setattr(asset_transactions.os, 'replace', fail)
    with pytest.raises(OSError, match='injected failure'):
        builder.build_family(family, assets_dir=root, archive_dir=archive, far=far, world=world, props=props, promote=True)
    assert snapshot(root) == before
    assert not (root.parent / '.assets-asset-build-pending.json').exists()


def test_source_validation_and_symlink_rejection_without_writes(assets_and_sources, tmp_path):
    root, inputs, archive = assets_and_sources
    far, world, props = inputs['ohio_salvage_v1']
    before = snapshot(root)
    with pytest.raises(ValueError, match='required together'):
        builder.build_family('ohio_salvage_v1', assets_dir=root, archive_dir=archive, far=far, world=world, promote=True)
    with pytest.raises(ValueError, match='required together'):
        builder.build_family('ohio_dish_v1', assets_dir=root, archive_dir=archive, far=far, world=world, props=props, promote=True)
    link = tmp_path / 'linked_prop.png'
    link.symlink_to(props[0])
    with pytest.raises(ValueError, match='Symlink'):
        builder.build_family('ohio_salvage_v1', assets_dir=root, archive_dir=archive, far=far, world=world, props=[link], promote=True)
    wrong = tmp_path / 'flattened.png'
    png(wrong, (168, 76), True)
    with pytest.raises(ValueError, match='transparent and visible'):
        builder.build_family('ohio_salvage_v1', assets_dir=root, archive_dir=archive, far=far, world=world, props=[wrong], promote=True)
    assert snapshot(root) == before and not archive.exists()


def test_target_symlink_and_lock_contention_fail_closed(assets_and_sources, tmp_path):
    root, inputs, archive = assets_and_sources
    family = 'ohio_dish_v1'
    far, world, props = inputs[family]
    target = root / 'environments' / family
    target.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match='Symlink'):
        builder.build_family(family, assets_dir=root, archive_dir=archive, far=far, world=world, props=props, promote=True)
    target.unlink()
    descriptor = os.open(root, os.O_RDONLY)
    try:
        builder.fcntl.flock(descriptor, builder.fcntl.LOCK_EX | builder.fcntl.LOCK_NB)
        with pytest.raises(RuntimeError, match='active'):
            builder.build_family(family, assets_dir=root, archive_dir=archive, far=far, world=world, props=props, promote=True)
    finally:
        os.close(descriptor)
    assert not archive.exists()


def test_real_cli_requires_family_and_dry_run_does_not_write(assets_and_sources):
    root, inputs, archive = assets_and_sources
    far, world, props = inputs['ohio_dish_v1']
    before = snapshot(root)
    result = subprocess.run([sys.executable, '-m', 'video_game.tools.build_room_family',
                             '--family', 'ohio_dish_v1', '--assets-dir', str(root), '--archive-dir', str(archive),
                             '--far', str(far), '--world', str(world), '--dry-run'],
                            cwd=REPO_ROOT, env=os.environ.copy(),
                            text=True, capture_output=True, check=True)
    assert json.loads(result.stdout)['status'] == 'validated'
    assert snapshot(root) == before and not archive.exists()


def test_process_interruption_recovers_absent_family_before_new_attempt(assets_and_sources):
    root, inputs, archive = assets_and_sources
    family = 'ohio_salvage_v1'
    far, world, props = inputs[family]
    before = snapshot(root)
    script = '''
import os, sys
from pathlib import Path
from video_game.engine import asset_transactions
from video_game.tools.build_room_family import build_family
root, far, world, prop, archive = map(Path, sys.argv[1:])
real = asset_transactions.os.replace
def crash(source, target):
    result = real(source, target)
    if Path(target) == root / 'environments/ohio_salvage_v1/far_1152x544.png':
        os._exit(71)
    return result
asset_transactions.os.replace = crash
build_family('ohio_salvage_v1', assets_dir=root, far=far, world=world, props=[prop], archive_dir=archive, promote=True)
'''
    result = subprocess.run([sys.executable, '-c', script, str(root), str(far), str(world), str(props[0]), str(archive)],
                            cwd=REPO_ROOT, env=os.environ.copy(), check=False)
    assert result.returncode == 71
    journal = root.parent / '.assets-asset-build-pending.json'
    assert journal.exists()
    with pytest.raises(RuntimeError, match='Pending'):
        builder.build_family(family, assets_dir=root, archive_dir=archive)
    with pytest.raises(FileNotFoundError):
        builder.build_family(family, assets_dir=root, archive_dir=archive, far=root.parent / 'missing.png',
                             world=world, props=props, promote=True)
    assert snapshot(root) == before
    assert not journal.exists()


@pytest.fixture
def backdrop_sources(tmp_path):
    root = tmp_path / 'assets'
    root.mkdir()
    old = root / 'environments/ohio_approach_v1'
    old.mkdir(parents=True)
    (old / 'manifest.json').write_bytes(b'old-schema-1')
    source = tmp_path / 'bunker.png'
    png(source, (960, 540), True)
    return root, source, tmp_path / 'archive'


def test_backdrop_contract_is_exact_and_fresh():
    assert OPAQUE_BACKDROP_FAMILIES == ('ohio_bunker_v1', 'mandela_annex_v1',
                                        'dodleston_relay_v1', 'ehman_1977_v1')
    template = backdrop_manifest_template('ohio_bunker_v1')
    assert template == {'schema_version': 3, 'kind': 'opaque_backdrop', 'room_id': 'bunker_hub',
                        'density': 2, 'viewport': [480, 270], 'world': [480, 270],
                        'backdrop': {'id': 'backdrop', 'file': 'backdrop_960x540.png',
                                     'dimensions': [960, 540], 'alpha': 'opaque', 'origin': [0, 0],
                                     'rounding': 'logical_nearest', 'repeat': False}}
    template['backdrop']['dimensions'][0] = -1
    assert backdrop_manifest_template('ohio_bunker_v1')['backdrop']['dimensions'] == [960, 540]
    with pytest.raises(ValueError, match='Unknown'):
        backdrop_manifest_template('../untrusted')


@pytest.mark.parametrize(('family', 'room'), [
    ('mandela_annex_v1', 'act_01_mandela_test'),
    ('dodleston_relay_v1', 'act_04_dodleston_relay'),
    ('ehman_1977_v1', 'flashback_ehman_1977'),
])
def test_prototype_backdrop_contract_and_isolated_transaction(tmp_path, family, room):
    template = backdrop_manifest_template(family)
    assert template == {'schema_version': 3, 'kind': 'opaque_backdrop', 'room_id': room,
                        'density': 2, 'viewport': [480, 270], 'world': [480, 288],
                        'backdrop': {'id': 'backdrop', 'file': 'backdrop_960x576.png',
                                     'dimensions': [960, 576], 'alpha': 'opaque', 'origin': [0, 0],
                                     'rounding': 'logical_nearest', 'repeat': False}}
    template['world'][1] = 0
    assert backdrop_manifest_template(family)['world'] == [480, 288]
    root = tmp_path / 'assets'
    root.mkdir()
    (root / 'preserve').write_bytes(b'unchanged')
    source = tmp_path / 'prototype.png'
    png(source, (960, 576), True)
    archive = tmp_path / 'archive'
    before = snapshot(root)
    dry_run = builder.build_backdrop_family(family, assets_dir=root, archive_dir=archive, backdrop=source)
    assert dry_run['status'] == 'validated' and snapshot(root) == before and not archive.exists()
    installed = builder.build_backdrop_family(family, assets_dir=root, archive_dir=archive,
                                              backdrop=source, promote=True)
    target = root / 'environments' / family
    assert installed['status'] == 'promoted'
    assert (target / 'backdrop_960x576.png').read_bytes() == source.read_bytes()
    assert json.loads((target / 'manifest.json').read_text()) == installed['manifest']
    assert (root / 'preserve').read_bytes() == b'unchanged'


def test_backdrop_validation_and_promotion_are_isolated_and_manifest_last(backdrop_sources, monkeypatch):
    root, source, archive = backdrop_sources
    before = snapshot(root)
    assert builder.build_backdrop_family('ohio_bunker_v1', assets_dir=root, archive_dir=archive)['status'] == 'absent'
    result = builder.build_backdrop_family('ohio_bunker_v1', assets_dir=root, archive_dir=archive, backdrop=source)
    assert result['status'] == 'validated'
    assert result['manifest']['backdrop']['sha256'] == builder._sha(source)
    assert snapshot(root) == before and not archive.exists()
    real = asset_transactions.os.replace
    target = root / 'environments/ohio_bunker_v1'
    order = []
    def track(src, dst):
        if Path(dst).parent == target:
            order.append(Path(dst).name)
        return real(src, dst)
    monkeypatch.setattr(asset_transactions.os, 'replace', track)
    result = builder.build_backdrop_family('ohio_bunker_v1', assets_dir=root, archive_dir=archive,
                                           backdrop=source, promote=True)
    assert result['status'] == 'promoted'
    assert order == ['backdrop_960x540.png', 'manifest.json']
    assert (target / 'backdrop_960x540.png').read_bytes() == source.read_bytes()
    assert json.loads((target / 'manifest.json').read_text()) == result['manifest']
    assert (root / 'environments/ohio_approach_v1/manifest.json').read_bytes() == b'old-schema-1'
    assert builder.build_backdrop_family('ohio_bunker_v1', assets_dir=root, archive_dir=archive)['integrity'] == 'not_inspected'


@pytest.mark.parametrize('failure_index', [1, 2])
@pytest.mark.parametrize('existing', [False, True])
def test_backdrop_replacement_failure_restores_originals(backdrop_sources, monkeypatch, failure_index, existing):
    root, source, archive = backdrop_sources
    target = root / 'environments/ohio_bunker_v1'
    if existing:
        target.mkdir(parents=True)
        (target / 'backdrop_960x540.png').write_bytes(b'previous image')
        (target / 'manifest.json').write_bytes(b'previous manifest')
    before = snapshot(root)
    real = asset_transactions.os.replace
    count = 0
    def fail(src, dst):
        nonlocal count
        if Path(dst).parent == target:
            count += 1
            if count == failure_index:
                raise OSError('injected failure')
        return real(src, dst)
    monkeypatch.setattr(asset_transactions.os, 'replace', fail)
    with pytest.raises(OSError, match='injected failure'):
        builder.build_backdrop_family('ohio_bunker_v1', assets_dir=root, archive_dir=archive,
                                      backdrop=source, promote=True)
    assert snapshot(root) == before
    assert not (root.parent / '.assets-asset-build-pending.json').exists()


def test_backdrop_rejects_nonopaque_wrong_size_symlinks_and_lock(backdrop_sources, tmp_path):
    root, source, archive = backdrop_sources
    before = snapshot(root)
    bad_alpha = tmp_path / 'alpha.png'
    png(bad_alpha, (960, 540))
    wrong_size = tmp_path / 'size.png'
    png(wrong_size, (959, 540), True)
    symlink = tmp_path / 'link.png'
    symlink.symlink_to(source)
    for invalid in (bad_alpha, wrong_size, symlink):
        with pytest.raises(ValueError):
            builder.build_backdrop_family('ohio_bunker_v1', assets_dir=root, archive_dir=archive,
                                          backdrop=invalid, promote=True)
    target = root / 'environments/ohio_bunker_v1'
    target.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match='Symlink'):
        builder.build_backdrop_family('ohio_bunker_v1', assets_dir=root, archive_dir=archive,
                                      backdrop=source, promote=True)
    target.unlink()
    descriptor = os.open(root, os.O_RDONLY)
    try:
        builder.fcntl.flock(descriptor, builder.fcntl.LOCK_EX | builder.fcntl.LOCK_NB)
        with pytest.raises(RuntimeError, match='active'):
            builder.build_backdrop_family('ohio_bunker_v1', assets_dir=root, archive_dir=archive,
                                          backdrop=source, promote=True)
    finally:
        os.close(descriptor)
    assert snapshot(root) == before and not archive.exists()


def test_backdrop_cli_requires_correct_arguments_and_does_not_write(backdrop_sources):
    root, source, archive = backdrop_sources
    before = snapshot(root)
    command = [sys.executable, '-m', 'video_game.tools.build_room_family', '--family', 'ohio_bunker_v1',
               '--assets-dir', str(root), '--archive-dir', str(archive)]
    options = dict(cwd=REPO_ROOT, env=os.environ.copy(), text=True, capture_output=True)
    result = subprocess.run([*command, '--backdrop', str(source), '--dry-run'], **options, check=True)
    assert json.loads(result.stdout)['status'] == 'validated'
    invalid = subprocess.run([*command, '--far', str(source)], **options, check=False)
    assert invalid.returncode != 0 and 'accept only --backdrop' in invalid.stderr
    assert snapshot(root) == before and not archive.exists()


def test_backdrop_process_interruption_recovers_absent_family(backdrop_sources):
    root, source, archive = backdrop_sources
    before = snapshot(root)
    script = '''
import os, sys
from pathlib import Path
from video_game.engine import asset_transactions
from video_game.tools.build_room_family import build_backdrop_family
root, source, archive = map(Path, sys.argv[1:])
real = asset_transactions.os.replace
def crash(src, dst):
    result = real(src, dst)
    if Path(dst) == root / 'environments/ohio_bunker_v1/backdrop_960x540.png':
        os._exit(71)
    return result
asset_transactions.os.replace = crash
build_backdrop_family('ohio_bunker_v1', assets_dir=root, archive_dir=archive, backdrop=source, promote=True)
'''
    result = subprocess.run([sys.executable, '-c', script, str(root), str(source), str(archive)],
                            cwd=REPO_ROOT, env=os.environ.copy(), check=False)
    assert result.returncode == 71
    journal = root.parent / '.assets-asset-build-pending.json'
    assert journal.exists()
    with pytest.raises(RuntimeError, match='Pending'):
        builder.build_backdrop_family('ohio_bunker_v1', assets_dir=root, archive_dir=archive)
    with pytest.raises(FileNotFoundError):
        builder.build_backdrop_family('ohio_bunker_v1', assets_dir=root, archive_dir=archive,
                                      backdrop=root.parent / 'missing.png', promote=True)
    assert snapshot(root) == before
    assert not journal.exists()
