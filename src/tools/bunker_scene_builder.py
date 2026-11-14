"""
MODULE: src/tools/bunker_scene_builder.py
PURPOSE: Builds the 6 complete, uncropped 480x270 Ohio Big Ear bunker layers,
         authentic 16x16 pixel-art tileset, Mateo sprites, and CRT ON/OFF previews.
CALLED BY: Run standalone (`python -m video_game.tools.bunker_scene_builder`) or tests.
HOW TO MODIFY:
  - To adjust Mateo's outfits/poses -> edit src/tools/mateo_sprite_builder.py.
  - To adjust the 6 bunker layers -> edit build_bunker_layers().
"""

import json
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw
from video_game.tools.mateo_sprite_builder import BUNKER_SOURCE, resolve_source

REPO_ROOT_DIR = Path(__file__).resolve().parents[2]
ASSETS_DIR = REPO_ROOT_DIR / "src" / "assets"
BUNKER_DIR = ASSETS_DIR / "bunker"
SPRITES_DIR = ASSETS_DIR / "sprites"
CIV_DIR = ASSETS_DIR / "civilizations"
ART_SOURCE_DIR = REPO_ROOT_DIR / "src" / "art" / "source"
CONCEPTS_DIR = ART_SOURCE_DIR / "bunker"

LAYER_NAMES = [
    "01_distant_structure.png",
    "02_rear_wall.png",
    "03_equipment.png",
    "04_playable_floor.png",
    "05_foreground_props.png",
    "06_lighting_overlay.png",
]

INSPECTION_NAMES = [
    "01_distant_structure_inspect.png",
    "02_rear_wall_inspect.png",
    "03_equipment_inspect.png",
    "04_playable_floor_inspect.png",
    "05_foreground_props_inspect.png",
    "06_lighting_overlay_inspect.png",
]

LAYER_METADATA = [
    {
        "z_order": 0,
        "file": "01_distant_structure.png",
        "name": "distant_structure",
        "role": "deep_hull_and_steel_girders",
        "blend_mode": "alpha_composite",
        "alpha_type": "opaque_base",
        "description": "Deep background cavern hull and structural steel girders",
    },
    {
        "z_order": 1,
        "file": "02_rear_wall.png",
        "name": "rear_wall",
        "role": "acoustic_panels_and_conduits",
        "blend_mode": "alpha_composite",
        "alpha_type": "explicit_binary_mask",
        "description": "Rear wall acoustic baffling panels and high-voltage conduit runs",
    },
    {
        "z_order": 2,
        "file": "03_equipment.png",
        "name": "equipment",
        "role": "server_racks_desk_workbench_door",
        "blend_mode": "alpha_composite",
        "alpha_type": "explicit_binary_mask",
        "description": "Ohio Big Ear equipment consoles, tape drives, terminal desk, workbench, airlock frame",
    },
    {
        "z_order": 3,
        "file": "04_playable_floor.png",
        "name": "playable_floor",
        "role": "concrete_deck_tiles_and_cable_runs",
        "blend_mode": "alpha_composite",
        "alpha_type": "explicit_binary_mask",
        "description": "Playable concrete bunker deck with floor expansion seams and cable conduits",
    },
    {
        "z_order": 4,
        "file": "05_foreground_props.png",
        "name": "foreground_props",
        "role": "ceiling_ducts_hanging_cables_framing",
        "blend_mode": "alpha_composite",
        "alpha_type": "explicit_binary_mask",
        "description": "Foreground ceiling HVAC ducts, hanging sensor cables, and doorway vignette framing",
    },
    {
        "z_order": 5,
        "file": "06_lighting_overlay.png",
        "name": "lighting_overlay",
        "role": "phosphor_crt_tube_beacon_ambient_glows",
        "blend_mode": "alpha_composite",
        "alpha_type": "smooth_radial_falloff",
        "description": "Hydrogen CRT green phosphor bloom, amber vacuum tube glow, rack indicator, and red status beacon",
    },
]

TILE_COORDS = [
    (152, 48), (184, 48), (216, 48), (248, 48), (160, 8), (200, 8), (240, 8), (280, 8),
    (24, 42), (76, 42), (24, 90), (76, 90), (24, 148), (76, 148), (24, 196), (76, 196),
    (168, 128), (204, 128), (308, 110), (336, 110), (308, 148), (344, 148), (424, 48), (432, 142),
    (280, 236), (312, 236), (344, 236), (376, 236), (140, 248), (188, 248), (236, 248), (416, 244),
]


def _build_modular_tileset(bunker_dir, concepts_dir=None):
    """Extract 32 authentic 16x16 pixel-art bunker material tiles from the master bunker scene."""
    bunker_dir.mkdir(parents=True, exist_ok=True)
    sheet = Image.new("RGBA", (128, 64), (10, 14, 18, 255))
    bunker_src = resolve_source(BUNKER_SOURCE, "bunker", concepts_dir)
    if bunker_src.is_file():
        raw_b = Image.open(bunker_src).convert("RGB").resize((480, 270), Image.Resampling.NEAREST)
        quant_b = raw_b.quantize(colors=48, method=Image.Quantize.MEDIANCUT).convert("RGBA")
        for idx, (sx, sy) in enumerate(TILE_COORDS):
            tx, ty = (idx % 8) * 16, (idx // 8) * 16
            tile = quant_b.crop((sx, sy, sx + 16, sy + 16))
            sheet.paste(tile, (tx, ty))
    sheet.save(bunker_dir / "tileset_bunker_16x16.png")
    return sheet


def _draw_soft_glow(layer_img, cx, cy, rx, ry, rgb, peak_alpha=64):
    """Draw a soft light pool with smooth radial alpha falloff."""
    px = layer_img.load()
    for py in range(max(0, cy - ry), min(270, cy + ry + 1)):
        for x in range(max(0, cx - rx), min(480, cx + rx + 1)):
            dist = ((x - cx) / float(rx)) ** 2 + ((py - cy) / float(ry)) ** 2
            if dist <= 1.0:
                w = 1.0 - dist
                a1 = int(peak_alpha * w)
                if a1 > 0:
                    r0, g0, b0, a0 = px[x, py]
                    if a0 == 0:
                        px[x, py] = (rgb[0], rgb[1], rgb[2], a1)
                    else:
                        new_a = min(255, a0 + a1)
                        new_r = min(255, int((r0 * a0 + rgb[0] * a1) / new_a))
                        new_g = min(255, int((g0 * a0 + rgb[1] * a1) / new_a))
                        new_b = min(255, int((b0 * a0 + rgb[2] * a1) / new_a))
                        px[x, py] = (new_r, new_g, new_b, new_a)


def _build_bunker_layers(bunker_dir, concepts_dir=None):
    """Build 6 complete 480x270 bunker layers with clean explicit alpha masks and inspection previews."""
    bunker_dir.mkdir(parents=True, exist_ok=True)
    inspect_dir = bunker_dir / "inspection"
    inspect_dir.mkdir(parents=True, exist_ok=True)

    layers = {
        "01_distant_structure.png": Image.new("RGBA", (480, 270), (8, 12, 16, 255)),
        "02_rear_wall.png": Image.new("RGBA", (480, 270), (0, 0, 0, 0)),
        "03_equipment.png": Image.new("RGBA", (480, 270), (0, 0, 0, 0)),
        "04_playable_floor.png": Image.new("RGBA", (480, 270), (0, 0, 0, 0)),
        "05_foreground_props.png": Image.new("RGBA", (480, 270), (0, 0, 0, 0)),
        "06_lighting_overlay.png": Image.new("RGBA", (480, 270), (0, 0, 0, 0)),
    }
    bunker_src = resolve_source(BUNKER_SOURCE, "bunker", concepts_dir)
    raw_b = Image.open(bunker_src).convert("RGB").resize((480, 270), Image.Resampling.NEAREST)
    quant_b = raw_b.quantize(colors=48, method=Image.Quantize.MEDIANCUT).convert("RGBA")
    r_px, q_px = raw_b.load(), quant_b.load()

    p01 = layers["01_distant_structure.png"].load()
    p02 = layers["02_rear_wall.png"].load()
    p03 = layers["03_equipment.png"].load()
    p04 = layers["04_playable_floor.png"].load()
    p05 = layers["05_foreground_props.png"].load()

    for py in range(270):
        for px in range(480):
            rr, rg, rb = r_px[px, py]
            col = (rr, rg, rb, 255) if (rr > rg + 22 or rg > rr + 18) else q_px[px, py]

            # 01: Distant structure - full opaque cavern hull background
            is_girder = (px % 64 < 6) or (py < 20) or (194 <= py <= 200)
            b_scale = 0.62 if is_girder else 0.42
            p01[px, py] = (int(col[0] * b_scale), int(col[1] * b_scale), int(col[2] * b_scale), 255)

            # Segmentation boundaries
            is_rack = px <= 137
            is_desk = 138 <= px <= 278 and py >= 108
            is_bench = 279 <= px <= 394 and py >= 70
            is_door = px >= 395
            is_equip = is_rack or is_desk or is_bench or is_door
            is_wall = (not is_equip) and (py < 196)
            is_floor = py >= 196
            is_fg = py < 24 or py >= 248 or px < 8 or px >= 472

            # Explicit alpha masks: full opacity where active, (0, 0, 0, 0) elsewhere
            if is_wall:
                p02[px, py] = (col[0], col[1], col[2], 255)
            if is_equip:
                p03[px, py] = (col[0], col[1], col[2], 255)
            if is_floor:
                p04[px, py] = (col[0], col[1], col[2], 255)
            if is_fg:
                p05[px, py] = (col[0], col[1], col[2], 255)

    # 06: Lighting overlay with soft radial alpha pools
    _draw_soft_glow(layers["06_lighting_overlay.png"], 208, 148, 72, 54, (51, 255, 102), 48)
    _draw_soft_glow(layers["06_lighting_overlay.png"], 324, 126, 58, 46, (255, 158, 44), 54)
    _draw_soft_glow(layers["06_lighting_overlay.png"], 70, 56, 64, 36, (255, 184, 76), 42)
    _draw_soft_glow(layers["06_lighting_overlay.png"], 235, 14, 96, 22, (160, 235, 195), 38)
    _draw_soft_glow(layers["06_lighting_overlay.png"], 444, 56, 28, 22, (220, 38, 38), 58)

    # Save layers to disk
    for name, img in layers.items():
        img.save(bunker_dir / name)

    # Generate flattened inspection previews over 35% dimmed/desaturated background
    rgb_b = quant_b.convert("RGB")
    gray_b = rgb_b.convert("L").convert("RGB")
    dimmed_bg = Image.blend(rgb_b, gray_b, 0.70).point(lambda c: int(c * 0.35)).convert("RGBA")

    for name in LAYER_NAMES:
        inspect_img = Image.alpha_composite(dimmed_bg.copy(), layers[name])
        inspect_name = name.replace(".png", "_inspect.png")
        inspect_img.save(inspect_dir / inspect_name)

    return layers


def _active_mask_copy(layer_img, is_light=False):
    """Legacy helper: returns a copy of the layer."""
    return layer_img.copy()


def _render_bunker_previews(assets_dir, concepts_dir=None, sprite_path=None):
    """Assemble all 6 bunker layers + proportional Mateo sprite and export CRT OFF/ON previews."""
    bunker_dir = assets_dir / "bunker"
    if sprite_path is None:
        sprite_path = assets_dir / "sprites/mateo_bunker_96x128.png"
    mateo_bunker = Image.open(sprite_path).convert("RGBA")
    _build_modular_tileset(bunker_dir, concepts_dir)
    layers = _build_bunker_layers(bunker_dir, concepts_dir)

    # Standard alpha composite in exact intended z-order
    comp = layers["01_distant_structure.png"].copy()
    comp = Image.alpha_composite(comp, layers["02_rear_wall.png"])
    comp = Image.alpha_composite(comp, layers["03_equipment.png"])
    comp = Image.alpha_composite(comp, layers["04_playable_floor.png"])

    shadow = Image.new("RGBA", (480, 270), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse((202, 238, 268, 252), fill=(0, 0, 0, 145))
    comp = Image.alpha_composite(comp, shadow)
    comp.paste(mateo_bunker, (186, 122), mateo_bunker)

    comp = Image.alpha_composite(comp, layers["05_foreground_props.png"])
    comp = Image.alpha_composite(comp, layers["06_lighting_overlay.png"])
    comp.save(bunker_dir / "bunker_preview_crt_off.png")

    crt_on = comp.resize((1440, 810), Image.Resampling.NEAREST)
    overlay = Image.new("RGBA", (1440, 810), (0, 0, 0, 0))
    c_draw = ImageDraw.Draw(overlay)
    for sy in range(2, 810, 3):
        c_draw.line((0, sy, 1440, sy), fill=(0, 0, 0, 58))
    c_draw.rectangle((0, 0, 1439, 809), outline=(36, 140, 72, 200), width=4)
    Image.alpha_composite(crt_on, overlay).convert("RGB").save(bunker_dir / "bunker_preview_crt_on.png")

    meta = {
        "canvas_size": [480, 270],
        "tile_grid": [16, 16],
        "layers": LAYER_NAMES,
        "layer_metadata": LAYER_METADATA,
        "mateo_idle": {"file": "sprites/mateo_idle_48x64.png", "size": [48, 64], "foot_pivot": [24, 62]},
        "mateo_bunker": {"file": "sprites/mateo_bunker_96x128.png", "size": [96, 128], "foot_pivot": [48, 124]},
    }
    (bunker_dir / "scene_manifest.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def build_mateo_idle_sprite():
    """Return the current protected idle sprite, building only a missing new group."""
    from video_game.tools.mateo_sprite_builder import build_all_mateo_assets
    build_all_mateo_assets()
    return Image.open(SPRITES_DIR / "mateo_idle_48x64.png").convert("RGBA")


def build_modular_tileset():
    """Render a tileset for callers without writing into the protected assets."""
    with tempfile.TemporaryDirectory(prefix="bunker-tiles-") as temporary:
        return _build_modular_tileset(Path(temporary), CONCEPTS_DIR)


def build_bunker_layers(active_civ_id="FASR-001"):
    """Render layers for callers without writing into the protected assets."""
    with tempfile.TemporaryDirectory(prefix="bunker-layers-") as temporary:
        return _build_bunker_layers(Path(temporary), CONCEPTS_DIR)


def build_bunker_previews(*, replace=False, dry_run=False):
    """Safely preserve or explicitly rebuild the bunker group."""
    from video_game.tools.build_assets import build_selected_groups
    build_selected_groups(["bunker"] if replace else [], dry_run=dry_run, groups=["bunker"])


if __name__ == "__main__":
    from video_game.tools.build_assets import main
    main(default_groups=["bunker"])

