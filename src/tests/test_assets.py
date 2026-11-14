"""
MODULE: tests/test_assets.py
PURPOSE: Exercise locked asset groups, staged replacement and recovery.
CALLED BY: pytest (`python -m pytest tests -q`).
HOW TO MODIFY: Add focused cases for source, output or promotion failure modes.
"""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from PIL import Image
import pytest

from video_game.engine import asset_transactions
from video_game.tools import build_assets


@pytest.fixture
def asset_copy(tmp_path):
    assets = tmp_path / "assets"
    shutil.copytree(build_assets.ASSETS_DIR, assets)
    return assets


@pytest.fixture
def source_copy(tmp_path):
    source = tmp_path / "art" / "source"
    shutil.copytree(build_assets.ART_SOURCE_DIR, source)
    return source


def hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}


def test_default_and_dry_run_preserve_locked_groups(asset_copy, tmp_path):
    before = hashes(asset_copy)
    for dry_run in (True, False):
        assert build_assets.build_selected_groups(dry_run=dry_run, assets_dir=asset_copy,
                                                   archive_dir=tmp_path / "archive") == []
        assert hashes(asset_copy) == before
    assert not (tmp_path / "archive").exists()


def test_missing_related_output_and_missing_source_are_safe(asset_copy, source_copy, tmp_path):
    face = asset_copy / "civilizations/fasr-001_face.png"
    face.unlink()
    before = hashes(asset_copy)
    with pytest.raises(FileNotFoundError, match="incomplete"):
        build_assets.build_selected_groups(assets_dir=asset_copy, source_dir=source_copy, groups=["FASR-001"])
    assert hashes(asset_copy) == before
    (source_copy / "civilizations" / "FASR-001" / build_assets.CONCEPT_FILES["FASR-001"]).unlink()
    before = hashes(asset_copy)
    with pytest.raises(FileNotFoundError, match="Required source missing"):
        build_assets.build_selected_groups(["FASR-001"], assets_dir=asset_copy, source_dir=source_copy,
                                           archive_dir=tmp_path / "archive", groups=["FASR-001"])
    assert hashes(asset_copy) == before
    assert not (tmp_path / "archive").exists()


def test_selected_replacement_archives_only_group_and_is_stable(asset_copy, tmp_path):
    face = asset_copy / "civilizations/fasr-001_face.png"
    with Image.open(face) as image:
        changed = image.convert("RGBA")
    changed.putpixel((0, 0), (1, 2, 3, 4))
    changed.save(face)
    before = hashes(asset_copy)
    archives = tmp_path / "archive"
    build_assets.build_selected_groups(["FASR-001"], groups=["FASR-001"],
                                       assets_dir=asset_copy, archive_dir=archives)
    after = hashes(asset_copy)
    changed_paths = {path for path in before if before[path] != after[path]}
    assert "civilizations/fasr-001_face.png" in changed_paths
    assert changed_paths <= set(build_assets._group_paths("FASR-001", {})) | {"civilizations/manifest.json"}
    manifests = list(archives.glob("*/[0-9a-f]*/manifest.json"))
    assert len(manifests) == 1
    record = json.loads(manifests[0].read_text())
    entry = next(e for e in record["files"] if e["path"] == "civilizations/fasr-001_face.png")
    archived = manifests[0].parent / "video_game/assets" / entry["path"]
    assert hashlib.sha256(archived.read_bytes()).hexdigest() == entry["sha256"] == before[entry["path"]]
    assert (archives / "TRASH_LOG.md").is_file()
    build_assets.build_selected_groups(["FASR-001"], groups=["FASR-001"],
                                       assets_dir=asset_copy, archive_dir=archives)
    assert hashes(asset_copy) == after


def test_failure_during_promotion_restores_previous_group(asset_copy, tmp_path, monkeypatch):
    before = hashes(asset_copy)
    replace = asset_transactions.os.replace
    count = 0

    def fail_once(source, target):
        nonlocal count
        if str(target).startswith(str(asset_copy)):
            count += 1
            if count == 2:
                raise OSError("simulated promotion failure")
        return replace(source, target)

    monkeypatch.setattr(asset_transactions.os, "replace", fail_once)
    with pytest.raises(OSError, match="simulated"):
        build_assets.build_selected_groups(["FASR-001"], groups=["FASR-001"],
                                           assets_dir=asset_copy, archive_dir=tmp_path / "archive")
    assert hashes(asset_copy) == before
    assert not (tmp_path / ".assets-asset-build-pending.json").exists()


def test_interrupted_process_recovers_before_game_load(asset_copy, tmp_path):
    face = asset_copy / "civilizations/fasr-001_face.png"
    with Image.open(face) as image:
        marked = image.convert("RGBA")
    marked.putpixel((0, 0), (1, 2, 3, 4))
    marked.save(face)
    before = hashes(asset_copy)
    script = '''
import os
from pathlib import Path
from video_game.engine import asset_transactions
from video_game.tools import build_assets
assets, archive = map(Path, __import__("sys").argv[1:])
replace = asset_transactions.os.replace
def crash(source, target):
    result = replace(source, target)
    if str(target).startswith(str(assets)):
        os._exit(71)
    return result
asset_transactions.os.replace = crash
build_assets.build_selected_groups(["FASR-001"], groups=["FASR-001"], assets_dir=assets, archive_dir=archive)
'''
    result = subprocess.run([sys.executable, "-c", script, str(asset_copy), str(tmp_path / "archive")],
                            cwd=build_assets.REPO_ROOT_DIR, env=os.environ.copy(), check=False)
    assert result.returncode == 71
    assert (tmp_path / ".assets-asset-build-pending.json").exists()
    assert hashes(asset_copy) != before
    load_script = '''
import sys
from pathlib import Path
from video_game.engine import config
from video_game.main import run_game
config.ASSETS_DIR = Path(sys.argv[1])
config.CIV_ASSETS_DIR = config.ASSETS_DIR / "civilizations"
assert run_game(max_frames=1) == 1
'''
    environment = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    subprocess.run([sys.executable, "-c", load_script, str(asset_copy)], cwd=build_assets.REPO_ROOT_DIR,
                   env=environment, check=True)
    assert hashes(asset_copy) == before
    assert not (tmp_path / ".assets-asset-build-pending.json").exists()


def test_explicit_mateo_and_bunker_groups_are_separate_and_stable(asset_copy, tmp_path):
    archive = tmp_path / "archive"
    before = hashes(asset_copy)
    for group, allowed in (("mateo", set(build_assets.MATEO_FILES)), ("bunker", set(build_assets.BUNKER_FILES))):
        build_assets.build_selected_groups([group], groups=[group], assets_dir=asset_copy, archive_dir=archive)
        after = hashes(asset_copy)
        assert {path for path in before if before[path] != after[path]} <= allowed
        build_assets.build_selected_groups([group], groups=[group], assets_dir=asset_copy, archive_dir=archive)
        assert hashes(asset_copy) == after
        before = after


def test_selected_replacement_repairs_missing_related_output(asset_copy, tmp_path):
    missing = asset_copy / "civilizations/fasr-001_constellation.png"
    missing.unlink()
    before = hashes(asset_copy)
    archive = tmp_path / "archive"
    build_assets.build_selected_groups(["FASR-001"], groups=["FASR-001"],
                                       assets_dir=asset_copy, archive_dir=archive)
    after = hashes(asset_copy)
    assert missing.is_file()
    assert {key for key in before if before[key] != after[key]} <= set(build_assets._group_paths("FASR-001", {})) | {"civilizations/manifest.json"}
    record = json.loads(next(archive.glob("*/[0-9a-f]*/manifest.json")).read_text())
    assert next(entry for entry in record["files"] if entry["path"].endswith("fasr-001_constellation.png"))["existed"] is False


def test_palette_rebuild_preserves_other_assets_and_is_stable(asset_copy, tmp_path):
    before = hashes(asset_copy)
    archive = tmp_path / "archive"
    for _ in range(2):
        build_assets.build_selected_groups(["palette"], groups=["palette"],
                                           assets_dir=asset_copy, archive_dir=archive)
        after = hashes(asset_copy)
        assert {path for path in before if before[path] != after[path]} <= {"ui/palette_sheet.png"}
        if _ == 0:
            first = after
    assert after == first


def test_preflight_checks_all_selected_sources_before_writing(asset_copy, source_copy, tmp_path):
    missing = source_copy / "civilizations" / "FASR-002" / build_assets.CONCEPT_FILES["FASR-002"]
    missing.unlink()
    before = hashes(asset_copy)
    with pytest.raises(FileNotFoundError, match="Required source missing"):
        build_assets.build_selected_groups(["FASR-001", "FASR-002"], groups=["FASR-001", "FASR-002"],
                                           assets_dir=asset_copy, source_dir=source_copy, archive_dir=tmp_path / "archive")
    assert hashes(asset_copy) == before
    assert not (tmp_path / "archive").exists()


def test_unsupported_lock_host_can_load_only_without_pending_recovery(asset_copy, tmp_path, monkeypatch):
    monkeypatch.setattr(asset_transactions, "fcntl", None)
    assert asset_transactions.recover_before_load(asset_copy) is False
    (tmp_path / ".assets-asset-build-pending.json").write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeError, match="supported builder host"):
        asset_transactions.recover_before_load(asset_copy)


def test_concurrent_builder_or_startup_is_rejected(asset_copy):
    descriptor = os.open(asset_copy, os.O_RDONLY)
    try:
        asset_transactions.fcntl.flock(descriptor, asset_transactions.fcntl.LOCK_EX | asset_transactions.fcntl.LOCK_NB)
        with pytest.raises(RuntimeError, match="Another asset build is active"):
            build_assets.build_selected_groups(assets_dir=asset_copy, dry_run=True)
        with pytest.raises(RuntimeError, match="while a build is active"):
            asset_transactions.recover_before_load(asset_copy)
    finally:
        os.close(descriptor)



def test_bunker_overlays_preserve_alpha_and_runtime_canvas():
    bunker_dir = build_assets.ASSETS_DIR / "environments/ohio/bunker"
    for name in ("foreground.png", "lighting.png"):
        with Image.open(bunker_dir / name) as image:
            assert image.size == (480, 270) and image.mode == "RGBA"
            values = {value for value, count in enumerate(image.getchannel("A").histogram()) if count}
            assert 254 not in values
            if name == "foreground.png":
                assert values == {0, 255}
            else:
                assert 0 in values and max(values) <= 128 and len(values) > 20


def test_bunker_scene_manifest_has_only_active_overlays_and_canonical_sprites():
    directory = build_assets.ASSETS_DIR / "environments/ohio/bunker"
    manifest = json.loads((directory / "scene.json").read_text())
    assert manifest["canvas_size"] == [480, 270]
    assert manifest["layers"] == ["foreground.png", "lighting.png"]
    for key, size in (("mateo_idle", [48, 64]), ("mateo_bunker", [96, 128])):
        entry = manifest[key]
        assert entry["size"] == size
        assert entry["file"].startswith("sprites/mateo/")
        with Image.open(build_assets.ASSETS_DIR / entry["file"]) as image:
            assert list(image.size) == size

def test_mateo_sprite_manifest_validates_bounds_and_attachments():
    manifest_path = build_assets.ASSETS_DIR / "sprites/mateo/manifest.json"
    assert manifest_path.is_file(), "Mateo manifest must exist"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest.get("schema_version") in (1, 2)
    assert "outfits" in manifest
    assert len(manifest["outfits"]) == 3
    required_anims = {
        "idle", "walk", "run", "jump", "fall", "land", "crouch",
        "slide", "cover_low", "cover_background", "shoot", "recoil",
        "tune", "hurt", "death",
    }

    for outfit_key, outfit_data in manifest["outfits"].items():
        assert "label" in outfit_data
        cell_size = outfit_data.get("cell_size", [96, 128])
        assert cell_size == [96, 128]
        anims = outfit_data.get("animations", {})
        assert required_anims <= set(anims.keys()), f"{outfit_key} missing required animation clips"

        for anim_name, anim_data in anims.items():
            assert "frames" in anim_data and len(anim_data["frames"]) > 0
            assert "frame_duration_ms" in anim_data
            assert "loop" in anim_data
            assert "foot_pivot" in anim_data
            assert "hurtbox" in anim_data
            assert "attachment_points" in anim_data
            assert anim_data.get("review_status") == "reviewed"

            # Validate foot pivot
            px, py = anim_data["foot_pivot"]
            assert 0 <= px <= cell_size[0]
            assert 0 <= py <= cell_size[1]

            # Validate hurtbox
            hx, hy, hw, hh = anim_data["hurtbox"]
            assert hx >= 0 and hy >= 0
            assert hx + hw <= cell_size[0]
            assert hy + hh <= cell_size[1]

            # Validate attachment points
            for att_name, pt in anim_data["attachment_points"].items():
                assert len(pt) == 2
                assert 0 <= pt[0] <= cell_size[0] + 16  # Weapon barrel can extend slightly past base cell
                assert 0 <= pt[1] <= cell_size[1]

            # Validate all frame files exist with correct size and RGBA mode
            for fr_rel in anim_data["frames"]:
                fr_path = build_assets.ASSETS_DIR / fr_rel
                assert fr_path.is_file(), f"Missing frame file: {fr_path}"
                with Image.open(fr_path) as img:
                    assert img.size == tuple(cell_size), f"{fr_path} size {img.size} != {cell_size}"
                    assert img.mode == "RGBA", f"{fr_path} mode {img.mode} != RGBA"


def test_mateo_action_rig_provenance():
    rig_path = build_assets.ART_SOURCE_DIR / "mateo/mateo_action_rig.json"
    assert rig_path.is_file(), "Mateo action rig manifest must exist in art/source/mateo"
    data = json.loads(rig_path.read_text(encoding="utf-8"))
    assert data.get("schema_version") == 1
    assert "source_concept" in data
    assert (build_assets.ART_SOURCE_DIR / "mateo" / data["source_concept"]).is_file()
    assert len(data.get("anatomical_pivots", {})) == 6
    assert len(data.get("action_poses", {})) >= 22

