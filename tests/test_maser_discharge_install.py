"""PURPOSE: Exercise explicit maser asset transactions and validated fallback.
CALLED BY: pytest.
HOW TO MODIFY: Use temporary asset roots and never alter the installed family.
"""
import json
from pathlib import Path

import pygame
import pytest

from video_game.engine.effects import (MASER_FAMILY, MASER_MANIFEST, MASER_NAME,
                                       load_maser_presentation)
from tools.build_maser_discharge import build_discharge

SOURCE = (Path(__file__).resolve().parents[1] / 'art/source/visual_upgrade/candidates'
          / 'maser_discharge_v02/export/maser_discharge_v02_64x32.png')


def test_explicit_transaction_and_invalid_family_fallback(tmp_path):
    root = tmp_path / 'assets'
    root.mkdir()
    pygame.init()
    pygame.display.set_mode((1, 1))
    try:
        assert load_maser_presentation(root) is None
        assert build_discharge(assets_dir=root, source=SOURCE)['status'] == 'validated'
        assert not (root / MASER_FAMILY).exists()
        with pytest.raises(ValueError):
            build_discharge(assets_dir=root, promote=True)
        outcome = build_discharge(assets_dir=root, archive_dir=tmp_path / 'archive', source=SOURCE, promote=True)
        assert outcome['status'] == 'promoted'
        family = root / MASER_FAMILY
        assert json.loads((family / 'manifest.json').read_text()) == MASER_MANIFEST
        assert (family / MASER_NAME).read_bytes() == SOURCE.read_bytes()
        assert load_maser_presentation(root) is not None
        (family / MASER_NAME).write_bytes(b'broken')
        assert load_maser_presentation(root) is None
        (family / MASER_NAME).write_bytes(SOURCE.read_bytes())
        (family / 'manifest.json').write_text('{}')
        assert load_maser_presentation(root) is None
        (family / 'manifest.json').write_text(json.dumps(dict(MASER_MANIFEST, schema_version=True)))
        assert load_maser_presentation(root) is None
        (family / 'manifest.json').write_text(json.dumps(MASER_MANIFEST))
        journal = tmp_path / '.assets-asset-build-pending.json'
        journal.write_text('{}')
        assert load_maser_presentation(root) is None
    finally:
        pygame.quit()


def test_bad_source_and_symlink_are_rejected(tmp_path):
    root = tmp_path / 'assets'
    root.mkdir()
    bad = tmp_path / 'bad.png'
    bad.write_bytes(b'bad')
    with pytest.raises(ValueError):
        build_discharge(assets_dir=root, source=bad)
    (root / 'effects').symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError):
        build_discharge(assets_dir=root, source=SOURCE, promote=True)
