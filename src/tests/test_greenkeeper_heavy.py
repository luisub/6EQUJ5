"""MODULE: tests/test_greenkeeper_heavy.py
PURPOSE: Verify Greenkeeper art-family integrity, geometry and combat-state contracts.
CALLED BY: pytest during focused and full game checks.
HOW TO MODIFY: Keep isolated asset roots and cover validation, fallback and reset.
"""

from . import REPO_ROOT
import shutil
from pathlib import Path

import pygame
import pytest

from video_game.engine import config
from video_game.engine.bosses.base import PHASE_2, STATE_IDLE, STATE_VULNERABLE
from video_game.engine.bosses.greenkeeper import Greenkeeper
from video_game.engine.bosses.greenkeeper_art import FAMILY, HASHES, load_family
from video_game.engine.world import Camera
from video_game.tools.build_greenkeeper_heavy import build

SOURCE = REPO_ROOT / 'src/art/source/visual_upgrade/candidates/greenkeeper_heavy_v01/exports'


def test_promotion_validates_and_uses_complete_family(tmp_path):
    assets = tmp_path / 'assets'; assets.mkdir()
    result = build(assets_dir=assets, source=SOURCE, archive_dir=tmp_path/'archive', promote=True)
    assert result['status'] == 'promoted'
    assert set(load_family(assets)) == set(HASHES)
    boss = Greenkeeper(asset_root=assets)
    assert tuple(boss.rect) == (428, 144, 128, 96)
    assert boss.mortar_muzzle == (467, 160)
    assert tuple(boss.weak_point_rect) == (490, 193, 23, 19)
    assert boss.health == boss.max_health
    # Explicit coordinates always specify the selected body's top-left.
    assert tuple(Greenkeeper(100, 90, asset_root=assets).rect) == (100, 90, 128, 96)


def test_incomplete_corrupt_and_pending_assets_fall_back_together(tmp_path):
    assets = tmp_path / 'assets'; assets.mkdir()
    build(assets_dir=assets, source=SOURCE, archive_dir=tmp_path/'archive', promote=True)
    frame = assets/FAMILY/'exposed.png'
    data = frame.read_bytes(); frame.unlink()
    boss = Greenkeeper(asset_root=assets)
    assert boss.heavy_sprites is None and tuple(boss.rect) == (460, 192, 64, 48)
    frame.write_bytes(data + b'corrupt')
    assert load_family(assets) is None
    frame.write_bytes(data)
    (tmp_path/'.assets-asset-build-pending.json').write_text('{}')
    assert load_family(assets) is None


def test_builder_rejects_bad_source_without_installing(tmp_path):
    source = tmp_path/'source'; shutil.copytree(SOURCE, source)
    (source/'attack_nearest_256x192.png').write_bytes(b'not a png')
    assets = tmp_path/'assets'; assets.mkdir()
    with pytest.raises(ValueError):
        build(assets_dir=assets, source=source, archive_dir=tmp_path/'archive', promote=True)
    assert not (assets/FAMILY/'manifest.json').exists()


def test_pose_selection_attacks_and_retry_are_registered(tmp_path):
    assets=tmp_path/'assets'; assets.mkdir()
    build(assets_dir=assets, source=SOURCE, archive_dir=tmp_path/'archive', promote=True)
    boss = Greenkeeper(asset_root=assets)
    boss.skip_intro()
    assert boss._heavy_pose() == 'idle'
    boss.current_attack_type = 'mortar'; boss.pending_mortar_targets = [(100,232)]
    boss._execute_telegraphed_attack()
    assert boss._heavy_pose() == 'attack' and boss.projectiles
    boss.phase_state = STATE_VULNERABLE; boss.weak_point_exposed = True
    assert boss._heavy_pose() == 'exposed'
    assert boss.take_damage(10, hit_pos=boss.weak_point_rect.center).damage_dealt == 20
    boss.current_phase = PHASE_2; boss.phase_state = STATE_IDLE; boss.weak_point_exposed = False
    boss.volley_count = 1; boss._schedule_next_attack((100,208))
    warning = boss.telegraphs[0]
    assert warning.attack_type == 'charge' and warning.target_rect.bottom == 240
    boss.charge_duration = 1; boss.charge_vx = -160; boss.x = 33; boss.update(0.1)
    assert boss.x == 32 and boss.rect.x == 32 and boss.weak_point_rect.x == 94
    boss.trigger_defeat(); assert boss._heavy_pose() == 'wreck'
    boss.reset_to_pristine()
    assert boss._heavy_pose() == 'idle' and tuple(boss.rect) == (428,144,128,96)
    assert not boss.projectiles and not boss.telegraphs and boss.health == boss.max_health


def test_native_render_uses_cached_frames_without_io(tmp_path, monkeypatch):
    assets=tmp_path/'assets'; assets.mkdir()
    build(assets_dir=assets, source=SOURCE, archive_dir=tmp_path/'archive', promote=True)
    boss=Greenkeeper(asset_root=assets)
    class CRT:
        def __init__(self): self.calls=[]
        def composite_native(self, sprite, pos, size): self.calls.append((sprite.get_size(), pos, size))
    crt=CRT(); camera=Camera(); surface=pygame.Surface((480,270),pygame.SRCALPHA)
    monkeypatch.setattr(pygame.image, 'load', lambda *args, **kwargs: pytest.fail('frame-time I/O'))
    boss.render(surface,camera,crt=crt); boss.render(surface,camera,crt=crt)
    assert crt.calls == [((256,192),(428,144),(128,96))]*2
