"""
MODULE: video_game/engine/assets.py
PURPOSE: Validate existing manifests and cache required Pygame asset surfaces.
CALLED BY: GameStateMachine and its scenes.
HOW TO MODIFY: Resolve manifest paths within the asset root and retain current
  alpha-mask behavior until the bunker layer migration in C02.
"""

import json
from pathlib import Path

import pygame


class AssetLoadError(RuntimeError):
    """A required game asset or its manifest cannot be loaded safely."""


class AssetCache:
    """Cache each validated image and its masked variants for a game session."""

    def __init__(self, asset_root):
        self.root = Path(asset_root).resolve()
        self._surfaces = {}
        self.master_manifest = self._manifest("manifest.json") if (self.root / "manifest.json").is_file() else {}
        self.bunker_manifest = self._manifest("bunker/scene_manifest.json")
        self.civilizations = self._manifest("civilizations/manifest.json")
        self.mateo_manifest = self._manifest("sprites/mateo/manifest.json") if (self.root / "sprites/mateo/manifest.json").is_file() else {}
        layers = self.bunker_manifest.get("layers")
        if (self.bunker_manifest.get("canvas_size") != [480, 270] or not isinstance(layers, list)
                or len(layers) != 6 or any(not isinstance(name, str) for name in layers)
                or len(set(layers)) != 6):
            raise AssetLoadError("Invalid bunker manifest: expected six 480x270 layers")
        for name in layers:
            self._resolve(Path("bunker") / name)
        if not isinstance(self.civilizations, dict) or not self.civilizations:
            raise AssetLoadError("Invalid civilization manifest: expected civilization entries")

    def _resolve(self, relative):
        relative = Path(relative)
        if relative.is_absolute() or ".." in relative.parts:
            raise AssetLoadError(f"Asset path must stay inside {self.root}: {relative}")
        path = (self.root / relative).resolve()
        if not path.is_relative_to(self.root):
            raise AssetLoadError(f"Asset path escapes {self.root}: {relative}")
        return path

    def _manifest(self, relative):
        path = self._resolve(relative)
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise AssetLoadError(f"Cannot read required asset manifest {path}: {exc}") from exc
        if not isinstance(value, dict):
            raise AssetLoadError(f"Asset manifest must contain an object: {path}")
        return value

    def image(self, relative, size, mode=None):
        key = (str(relative), tuple(size), mode)
        if key not in self._surfaces:
            path = self._resolve(relative)
            if not path.is_file():
                rel_str = str(relative)
                if rel_str.startswith("sprites/mateo_") and rel_str.endswith("_strip.png"):
                    outfit = rel_str.removeprefix("sprites/mateo_").removesuffix("_strip.png")
                    candidate = self.root / "sprites" / "mateo" / outfit / "strip.png"
                    if candidate.is_file():
                        path = candidate
                elif rel_str == "sprites/mateo_portrait_128x128.png":
                    candidate = self.root / "sprites" / "mateo" / "portrait_128x128.png"
                    if candidate.is_file():
                        path = candidate
                elif rel_str == "sprites/mateo_bunker_96x128.png":
                    candidate = self.root / "sprites" / "mateo" / "bunker_96x128.png"
                    if candidate.is_file():
                        path = candidate
            try:
                surface = pygame.image.load(str(path)).convert_alpha()
            except (pygame.error, OSError, FileNotFoundError) as exc:
                raise AssetLoadError(f"Cannot load required image {path}: {exc}") from exc
            if surface.get_size() != tuple(size):
                raise AssetLoadError(f"Invalid size for {path}: expected {tuple(size)}, got {surface.get_size()}")
            self._surfaces[key] = surface
        return self._surfaces[key]

    def bunker_layers(self):
        return [self.image(Path("bunker") / name, (480, 270))
                for name in self.bunker_manifest["layers"]]

    def bunker_sprite(self, name, size):
        try:
            entry = self.bunker_manifest[name]
            path = entry["file"]
            if not isinstance(path, str) or entry["size"] != list(size):
                raise ValueError(f"expected a relative path and size {tuple(size)}")
        except (KeyError, TypeError, ValueError) as exc:
            raise AssetLoadError(f"Invalid bunker sprite {name}: {exc}") from exc
        return self.image(path, size)

    def civilization(self, civ_id, field):
        try:
            entry = self.civilizations[civ_id]
            filename = entry[f"{field}_png"]
            if entry["native_size"] != [128, 128] or not isinstance(filename, str):
                raise ValueError("expected a 128x128 image and relative filename")
            path = Path("civilizations") / filename
            if Path(filename).is_absolute() or ".." in Path(filename).parts:
                raise ValueError("path must stay inside the civilization directory")
        except (KeyError, TypeError, ValueError) as exc:
            raise AssetLoadError(f"Invalid civilization asset {civ_id}/{field}: {exc}") from exc
        return self.image(path, (128, 128))
