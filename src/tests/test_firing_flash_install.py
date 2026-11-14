"""PURPOSE: Verify explicit firing-flash transactions and complete runtime fallback.
CALLED BY: pytest.
HOW TO MODIFY: Use isolated asset roots and retain entry/re-entry and no-frame-I/O checks.
"""

from . import REPO_ROOT
import json
import shutil
from pathlib import Path

import pygame
import pytest

from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.firing_lighting import FLASH_FAMILY, FLASH_MANIFEST, FLASH_NAME
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine
from video_game.tools.build_firing_flash import build_flash

SOURCE = (REPO_ROOT / 'src/art/source/effects/firing_flash_v01'
          / 'export/firing_flash_64x32.png')


def test_transaction_is_explicit_and_manifest_last(tmp_path):
    root = tmp_path / 'assets'
    root.mkdir()
    archive = tmp_path / 'archive'
    assert build_flash(assets_dir=root, source=SOURCE)['status'] == 'validated'
    assert not (root / FLASH_FAMILY).exists()
    with pytest.raises(ValueError):
        build_flash(assets_dir=root, promote=True)
    result = build_flash(assets_dir=root, archive_dir=archive, source=SOURCE, promote=True)
    assert result['status'] == 'promoted'
    family = root / FLASH_FAMILY
    assert json.loads((family / 'manifest.json').read_text()) == FLASH_MANIFEST
    assert (family / FLASH_NAME).read_bytes() == SOURCE.read_bytes()
    assert not (tmp_path / '.assets-asset-build-pending.json').exists()
    assert Path(result['archive']).is_dir()


def test_actual_scene_entry_reentry_and_invalid_fallback(tmp_path, monkeypatch):
    root = tmp_path / 'assets'
    shutil.copytree(config.ASSETS_DIR, root)
    family = root / FLASH_FAMILY
    if family.exists():
        shutil.rmtree(family)
    pygame.init()
    pygame.display.set_mode((960, 540))
    machine = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(tmp_path / 'save'),
                               settings_store=SettingsStore(tmp_path / 'save'))
    try:
        machine.assets.root = root
        assert machine.start_new_game()[0]
        machine.change_state(config.STATE_FIELD_OPS, room='act_01/approach.json', spawn='approach_checkpoint')
        scene = machine.current_scene
        assert scene.firing_lighting is None
        machine.render()
        missing_frame = pygame.image.tobytes(machine.crt.render_surface, 'RGBA')
        build_flash(assets_dir=root, archive_dir=tmp_path / 'archive', source=SOURCE, promote=True)
        scene.load_room('act_01/approach.json', spawn_name='approach_checkpoint')
        assert scene.firing_lighting is not None
        assert scene.firing_lighting.world_source is scene.native_approach.world
        # Drawing the already loaded family must never read or decode the asset per frame.
        with monkeypatch.context() as patch:
            patch.setattr(Path, 'read_bytes', lambda *_: pytest.fail('unexpected frame file read'))
            patch.setattr(Path, 'read_text', lambda *_args, **_kw: pytest.fail('unexpected frame manifest read'))
            patch.setattr(pygame.image, 'load', lambda *_args, **_kw: pytest.fail('unexpected frame image load'))
            machine.render()
        scene.load_room('act_01/salvage_yard.json', spawn_name='yard_entrance')
        assert scene.firing_lighting is None
        scene.load_room('act_01/approach.json', spawn_name='approach_checkpoint')
        assert scene.firing_lighting is not None
        image = family / FLASH_NAME
        image.write_bytes(b'corrupt')
        scene.load_room('act_01/approach.json', spawn_name='approach_checkpoint')
        assert scene.firing_lighting is None
        machine.render()
        assert pygame.image.tobytes(machine.crt.render_surface, 'RGBA') == missing_frame
        image.write_bytes(SOURCE.read_bytes())
        manifest = family / 'manifest.json'
        bad = dict(FLASH_MANIFEST, pivot_right=[13, 16])
        manifest.write_text(json.dumps(bad))
        scene.load_room('act_01/approach.json', spawn_name='approach_checkpoint')
        assert scene.firing_lighting is None
        manifest.write_text(json.dumps(FLASH_MANIFEST))
        journal = root.parent / f'.{root.name}-asset-build-pending.json'
        journal.write_text('{}')
        scene.load_room('act_01/approach.json', spawn_name='approach_checkpoint')
        assert scene.firing_lighting is None
        journal.unlink()
        scene.load_room('act_01/approach.json', spawn_name='approach_checkpoint')
        assert scene.firing_lighting is not None
    finally:
        machine.close()
        pygame.quit()


def test_rejects_unreviewed_source_and_symlink_target(tmp_path):
    root = tmp_path / 'assets'
    root.mkdir()
    bad = tmp_path / 'bad.png'
    bad.write_bytes(b'bad')
    with pytest.raises(ValueError):
        build_flash(assets_dir=root, source=bad)
    (root / 'effects').symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError):
        build_flash(assets_dir=root, source=SOURCE, promote=True)
