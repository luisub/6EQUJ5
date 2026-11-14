"""Export the approved bunker foreground and lighting without changing their pixels."""
import json
import shutil
from pathlib import Path

from PIL import Image


BUNKER_RELATIVE = Path("environments/ohio/bunker")
OVERLAY_NAMES = ("foreground.png", "lighting.png")
SOURCE_DIR = Path(__file__).resolve().parents[1] / "art/source/bunker/overlays"


def scene_manifest():
    return {
        "canvas_size": [480, 270],
        "layers": list(OVERLAY_NAMES),
        "mateo_idle": {"file": "sprites/mateo/navy_chore/48x64.png", "size": [48, 64], "foot_pivot": [24, 62]},
        "mateo_bunker": {"file": "sprites/mateo/navy_chore/idle_1.png", "size": [96, 128], "foot_pivot": [48, 124]},
    }


def validate_sources(source_dir=None):
    """Require the two approved 480 × 270 transparent compositing inputs."""
    directory = Path(source_dir) / "bunker/overlays" if source_dir is not None else SOURCE_DIR
    paths = [directory / name for name in OVERLAY_NAMES]
    for path in paths:
        with Image.open(path) as image:
            image.load()
            if image.mode != "RGBA" or image.size != (480, 270):
                raise ValueError(f"Invalid bunker overlay dimensions or mode: {path}")
            alpha = image.getchannel("A")
            low, high = alpha.getextrema()
            if high == 0 or low == 255:
                raise ValueError(f"Bunker overlay must include visible and transparent pixels: {path}")
    return paths


def _render_bunker_assets(assets_dir, source_dir=None):
    paths = validate_sources(source_dir)
    destination = Path(assets_dir) / BUNKER_RELATIVE
    destination.mkdir(parents=True, exist_ok=True)
    for source, name in zip(paths, OVERLAY_NAMES):
        shutil.copyfile(source, destination / name)
    (destination / "scene.json").write_text(json.dumps(scene_manifest(), indent=2) + "\n")


def build_bunker_overlays(*, replace=False, dry_run=False):
    """Preserve or explicitly promote the protected bunker overlay group."""
    from video_game.tools.build_assets import build_selected_groups
    return build_selected_groups(["bunker"] if replace else [], dry_run=dry_run, groups=["bunker"])


if __name__ == "__main__":
    from video_game.tools.build_assets import main
    main(default_groups=["bunker"])
