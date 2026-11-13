"""
MODULE: tests/test_checkpoint_audit.py
PURPOSE: Check readable module conventions and the current asset contracts.
CALLED BY: pytest (`python -m pytest tests -q`).
HOW TO MODIFY: Add focused checks when a contract changes; review unused files
  through their actual callers and dynamic references before retiring them.
"""

from video_game.engine import config

import ast
import json
from pathlib import Path

from PIL import Image
import pytest

GAME_ROOT_DIR = Path(__file__).resolve().parent.parent
EXCLUDED_DIRECTORIES = {"_trash", "_temp", "__pycache__", ".pytest_cache", ".venv", "build", "dist", "evidence", "art"}


def _active_python_files(root=GAME_ROOT_DIR):
    """Find active modules without keeping a second inventory of the project."""
    return sorted(
        path for path in root.rglob("*.py")
        if not EXCLUDED_DIRECTORIES.intersection(path.relative_to(root).parts)
    )


def _check_module(path):
    """Parse a module and check its documentation and explicit imports."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    if path.name != "__init__.py":
        assert ast.get_docstring(tree), f"{path} needs a module docstring"
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert all(alias.name != "*" for alias in node.names), (
                f"{path}:{node.lineno} uses a wildcard import"
            )


def test_active_modules_have_valid_syntax_documentation_and_explicit_imports():
    for path in _active_python_files():
        _check_module(path)


def test_new_scene_needs_no_registry_or_line_budget(tmp_path):
    scene = tmp_path / "engine" / "scenes" / "new_scene.py"
    scene.parent.mkdir(parents=True)
    scene.write_text(
        '"""Draw the example scene."""\n'
        + '\n'.join(f'value_{number} = {number}' for number in range(230)) + '\n',
        encoding="utf-8",
    )
    assert _active_python_files(tmp_path) == [scene]
    _check_module(scene)
    scene.write_text(scene.read_text(encoding="utf-8") + 'from math import *\n', encoding="utf-8")
    with pytest.raises(AssertionError, match="wildcard import"):
        _check_module(scene)
    scene.write_text('value = 1\n', encoding='utf-8')
    with pytest.raises(AssertionError, match='module docstring'):
        _check_module(scene)


def test_art_milestone_1_asset_dimensions_and_locks():
    """Check the actual manifest references and current required artwork sizes."""
    assets = config.ASSETS_DIR
    civ_dir = assets / "civilizations"
    manifest = json.loads((civ_dir / "manifest.json").read_text(encoding="utf-8"))
    assert len(manifest) == 11
    for cid, entry in manifest.items():
        assert entry["authored_lock"] is True
        assert entry["status"] == "production_v2"
        assert entry["native_size"] == [128, 128]
        for field in ("face_png", "env_png", "composite_png", "constellation_png"):
            path = civ_dir / entry[field]
            assert path.resolve().is_relative_to(civ_dir.resolve()), f"Invalid path for {cid}: {path}"
            with Image.open(path) as image:
                assert image.size == (128, 128), f"{cid} {field} must be 128x128"

    bunker_dir = assets / "bunker"
    bunker = json.loads((bunker_dir / "scene_manifest.json").read_text(encoding="utf-8"))
    assert bunker["canvas_size"] == [480, 270]
    assert len(bunker["layers"]) == 6
    for layer in bunker["layers"]:
        path = bunker_dir / layer
        assert path.resolve().is_relative_to(bunker_dir.resolve()), f"Invalid layer path: {path}"
        with Image.open(path) as image:
            assert image.size == (480, 270)
    for key, size in (("mateo_idle", (48, 64)), ("mateo_bunker", (96, 128))):
        entry = bunker[key]
        path = assets / entry["file"]
        assert path.resolve().is_relative_to(assets.resolve()), f"Invalid sprite path: {path}"
        assert entry["size"] == list(size)
        with Image.open(path) as image:
            assert image.size == size
    for relative, size in (
        ("sprites/mateo_portrait_128x128.png", (128, 128)),
        ("mateo_character_sheet.png", (1180, 520)),
        ("palette_sheet.png", (480, 270)),
    ):
        with Image.open(assets / relative) as image:
            assert image.size == size
    assert (assets / "before_after_comparison.png").exists()
