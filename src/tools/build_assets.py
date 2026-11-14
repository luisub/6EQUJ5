"""
MODULE: src/tools/build_assets.py
PURPOSE: Production pixel-art pipeline for all 11 128x128 civilization portraits,
         environment plates, astronomical/survey charts, palette & comparison sheets.
CALLED BY: Run standalone (`python -m video_game.tools.build_assets`) or test suite.
HOW TO MODIFY:
  - To adjust material color ramps -> edit MATERIAL_RAMPS.
  - To adjust portrait/environment generation -> edit civ_art_builder.py.
"""

import argparse
import json
import math
import os
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw
from video_game.engine.asset_transactions import fcntl, promote_group, recover_pending
from video_game.tools.civ_art_builder import CONCEPT_FILES, build_civ_env_plate, build_civ_face_layer, resolve_concept_path
from video_game.tools import bunker_scene_builder, mateo_sprite_builder

REPO_ROOT_DIR = Path(__file__).resolve().parents[2]
CIV_DATA_DIR = REPO_ROOT_DIR / "src" / "art" / "source" / "civilizations"
ASSETS_DIR = REPO_ROOT_DIR / "src" / "assets"
OUT_CIV_DIR = ASSETS_DIR / "civilizations"
ART_SOURCE_DIR = REPO_ROOT_DIR / "src" / "art" / "source"
LEGACY_SOURCE_DIR = CIV_DATA_DIR / "legacy_ascii"

MATERIAL_RAMPS = {
    "BUNKER_CONCRETE": [(6, 8, 12), (16, 22, 28), (32, 42, 48), (58, 72, 78), (94, 112, 118), (148, 168, 176)],
    "OLIVE_CLOTH": [(12, 18, 10), (28, 38, 16), (52, 68, 26), (74, 93, 35), (108, 132, 56), (154, 178, 92)],
    "MATEO_SKIN_HAIR": [(14, 10, 10), (38, 24, 20), (82, 52, 38), (138, 92, 66), (184, 132, 98), (222, 174, 136)],
    "TUBE_AMBER_BRASS": [(20, 10, 4), (64, 28, 8), (128, 58, 14), (196, 102, 24), (255, 158, 44), (255, 224, 128)],
    "HYDROGEN_CRT": [(4, 16, 10), (12, 52, 28), (24, 112, 56), (51, 255, 102), (0, 240, 255), (210, 255, 235)],
    "PROXIMA_TWILIGHT": [(8, 12, 24), (24, 46, 82), (56, 96, 148), (168, 52, 28), (232, 116, 44), (255, 196, 92)],
    "OUMUAMUA_ALLOY": [(8, 6, 14), (28, 22, 38), (58, 46, 72), (96, 76, 112), (180, 130, 255), (235, 205, 255)],
}
CIV_MAP = {
    "FASR-001": ("fasr_001_sagittarius", (51, 255, 102), "SAGITTARIUS 19h25m", "DEC -27d // 1420MHz", [(18, 88), (38, 68), (56, 74), (72, 52), (94, 40), (108, 64), (84, 86)], (64, 58)),
    "FASR-002": ("fasr_002_sgr_a_star", (255, 158, 44), "SGR A* CORE 17h45m", "DEC -29d // HORIZON", [(20, 92), (44, 72), (64, 64), (88, 48), (106, 70)], (64, 64)),
    "FASR-003": ("fasr_003_tabbys_star", (0, 240, 255), "CYGNUS KIC 20h06m", "DEC +44d // DYSON", [(22, 64), (64, 64), (106, 64), (64, 26), (64, 102)], (82, 46)),
    "FASR-004": ("fasr_004_orion", (255, 80, 180), "ORION M42 05h35m", "DEC -05d // NEBULA", [(36, 28), (88, 32), (52, 64), (64, 62), (76, 60), (40, 98), (92, 96)], (64, 78)),
    "FASR-005": ("fasr_005_proxima", (255, 158, 44), "CENTAURUS 14h29m", "DEC -62d // 4.24 LY", [(22, 42), (48, 56), (74, 48), (98, 78), (62, 94), (34, 86)], (94, 80)),
    "FASR-006": ("fasr_006_crab_nebula", (192, 216, 240), "TAURUS M1 05h34m", "DEC +22d // PULSAR", [(24, 88), (58, 68), (96, 40), (92, 84)], (90, 44)),
    "FASR-007": ("fasr_007_lgm1", (245, 211, 0), "VULPECULA 19h19m", "DEC +21d // CP 1919", [(24, 70), (52, 58), (82, 64), (104, 52)], (68, 60)),
    "FASR-008": ("fasr_008_trappist1", (255, 110, 60), "AQUARIUS 23h06m", "DEC -05d // 7-WORLD", [(20, 48), (46, 38), (70, 56), (92, 52), (108, 78)], (70, 56)),
    "FASR-009": ("fasr_009_oumuamua", (180, 130, 255), "1I/2017 U1 03h50m", "DEC +23d // PROBE", [(18, 96), (48, 74), (78, 52), (104, 30)], (78, 52)),
    "FASR-010": ("fasr_010_gobekli_tepe", (229, 193, 88), "GOBEKLI TEPE 37.2N", "LON 38.9E // SURVEY", [], (64, 64)),
    "FASR-SCAN-H": ("fasr_scan_h_heptapod", (204, 34, 34), "MULTI-QUADRANT // H", "NON-LINEAR ANOMALY", [], (64, 64)),
}
AUTHORED_V2_IDS = set(CIV_MAP.keys())


def _build_constellation_plate(cid, pri_rgb, top_lbl, bot_lbl, stars, target_xy):
    """Render a 128x128 astronomical star chart, GPR survey (FASR-010), or anomaly radar (SCAN-H)."""
    img = Image.new("RGBA", (128, 128), (4, 10, 12, 255))
    draw = ImageDraw.Draw(img)
    for g_pos in range(16, 112, 16):
        draw.line((g_pos, 14, g_pos, 113), fill=(9, 26, 20, 255))
        draw.line((4, g_pos, 123, g_pos), fill=(9, 26, 20, 255))
    for s_idx in range(38):
        img.putpixel(((s_idx * 47 + 13) % 120 + 4, (s_idx * 31 + 19) % 94 + 16), (34, 78, 56, 255))
    if cid == "FASR-010":
        for sy in range(32, 98, 10):
            draw.line((12, sy, 116, sy), fill=(72, 54, 24, 255))
        for px_c in (34, 64, 94):
            draw.rectangle((px_c - 8, 42, px_c + 8, 52), fill=pri_rgb, outline=(120, 90, 30, 255))
            draw.rectangle((px_c - 4, 52, px_c + 4, 86), fill=(168, 134, 54, 255))
        for rad in (14, 26, 38):
            draw.arc((64 - rad, 70 - rad, 64 + rad, 70 + rad), 15, 165, fill=(51, 255, 102, 255))
    elif cid == "FASR-SCAN-H":
        for rad in (40, 28, 16):
            draw.ellipse((64 - rad, 64 - rad, 64 + rad, 64 + rad), outline=(110, 28, 32, 255))
        for k_idx in range(7):
            nx, ny = int(64 + 28 * math.cos(k_idx * 0.897)), int(64 + 28 * math.sin(k_idx * 0.897))
            draw.ellipse((nx - 4, ny - 4, nx + 4, ny + 4), fill=pri_rgb, outline=(255, 158, 44, 255))
    else:
        for idx in range(len(stars) - 1):
            draw.line((*stars[idx], *stars[idx + 1]), fill=(28, 110, 68, 255))
        for sx, sy in stars:
            draw.rectangle((sx - 1, sy - 1, sx + 1, sy + 1), fill=(210, 255, 230, 255))
        tx, ty = target_xy
        draw.ellipse((tx - 5, ty - 5, tx + 5, ty + 5), outline=(204, 34, 34, 255))
        draw.line((tx - 8, ty, tx + 8, ty), fill=(204, 34, 34, 255))
        draw.line((tx, ty - 8, tx, ty + 8), fill=(204, 34, 34, 255))
    draw.rectangle((0, 0, 127, 13), fill=(10, 28, 18, 255))
    draw.rectangle((0, 114, 127, 127), fill=(8, 22, 16, 255))
    draw.rectangle((0, 0, 127, 127), outline=(36, 128, 72, 255))
    draw.text((4, 1), top_lbl[:20], fill=(51, 255, 102, 255))
    draw.text((4, 115), bot_lbl[:20], fill=(255, 176, 0, 255))
    return img


def _render_review_sheets(assets_dir, civ_dir, legacy_dir, manifest):
    """Generate palette_sheet.png (480x270), before_after_comparison.png, and all_civilizations_roster.png."""
    pal_img = Image.new("RGBA", (480, 270), (8, 10, 14, 255))
    p_draw = ImageDraw.Draw(pal_img)
    p_draw.text((12, 8), "6EQUJ5 MASTER MATERIAL PALETTE RAMPS (480x270 NATIVE)", fill=(51, 255, 102, 255))
    for r_idx, (r_name, colors) in enumerate(MATERIAL_RAMPS.items()):
        y_pos = 28 + r_idx * 34
        p_draw.text((14, y_pos), r_name, fill=(160, 200, 185, 255))
        for c_idx, rgb in enumerate(colors):
            x_pos = 180 + c_idx * 48
            p_draw.rectangle((x_pos, y_pos - 2, x_pos + 42, y_pos + 26), fill=(*rgb, 255), outline=(20, 36, 42, 255))
    pal_img.save(assets_dir / "palette_sheet.png")

    cmp_img = Image.new("RGBA", (620, 440), (6, 8, 12, 255))
    c_draw = ImageDraw.Draw(cmp_img)
    c_draw.text((12, 10), "6EQUJ5 MILESTONE 1: V1 ASCII vs V2 128x128 SCANLINE PIXEL-ART", fill=(51, 255, 102, 255))
    for idx, (cid, desc) in enumerate([
        ("FASR-001", "SAGITTARIUS // NARROWBAND HYDROGEN ANOMALY"),
        ("FASR-005", "PROXIMA CENTAURI // FLARE-STAR SHIFT"),
        ("FASR-009", "'OUMUAMUA 1I/2017 U1 // ANISOTROPIC ACCELERATION"),
    ]):
        y_base = 38 + idx * 132
        v1_p = legacy_dir / f"{cid.lower()}_face.png"
        if not v1_p.is_file():
            v1_p = legacy_dir / f"{cid.lower()}_legacy_face.png"
        v2_p = civ_dir / manifest[cid]["face_png"]
        if v1_p.is_file():
            cmp_img.paste(Image.open(v1_p).convert("RGBA").resize((128, 128), Image.Resampling.NEAREST), (20, y_base))
        if v2_p.is_file():
            cmp_img.paste(Image.open(v2_p).convert("RGBA"), (170, y_base))
        c_draw.text((310, y_base + 32), cid, fill=(51, 255, 102, 255))
        c_draw.text((310, y_base + 48), desc, fill=(255, 158, 44, 255))
    cmp_img.save(assets_dir / "before_after_comparison.png")

    roster = Image.new("RGBA", (560, 1500), (6, 10, 14, 255))
    r_draw = ImageDraw.Draw(roster)
    r_draw.text((14, 10), "6EQUJ5 // COMPLETE 11-CIVILIZATION SIGNAL ROSTER (128x128 SCANLINE COMPOSITES)", fill=(51, 255, 102, 255))
    for idx, (cid, c_data) in enumerate(manifest.items()):
        y_pos = 36 + idx * 132
        comp_p = civ_dir / c_data["composite_png"]
        if comp_p.is_file():
            roster.paste(Image.open(comp_p).convert("RGBA"), (14, y_pos))
        r_draw.text((156, y_pos + 4), f"{cid} // {c_data['folder'].upper()}", fill=(51, 255, 102, 255))
    roster.save(assets_dir / "all_civilizations_roster.png")


CIV_FIELDS = ("face_png", "env_png", "composite_png", "constellation_png")
REVIEW_FILES = ("palette_sheet.png", "before_after_comparison.png", "all_civilizations_roster.png")
BUNKER_INSPECTION_FILES = tuple(f"bunker/inspection/{name}" for name in bunker_scene_builder.INSPECTION_NAMES)
BUNKER_FILES = tuple(f"bunker/{name}" for name in bunker_scene_builder.LAYER_NAMES) + BUNKER_INSPECTION_FILES + (
    "bunker/tileset_bunker_16x16.png", "bunker/bunker_preview_crt_off.png",
    "bunker/bunker_preview_crt_on.png", "bunker/scene_manifest.json",
)
MATEO_FILES = tuple(
    ["sprites/mateo_portrait_128x128.png", "sprites/mateo_idle_48x64.png",
     "sprites/mateo_bunker_96x128.png", "mateo_character_sheet.png"]
    + [f"sprites/mateo_{outfit}_{pose}_96x128.png" for outfit in mateo_sprite_builder.OUTFIT_PALETTES for pose in mateo_sprite_builder.POSE_NAMES]
    + [f"sprites/mateo_{outfit}_{size}.png" for outfit in mateo_sprite_builder.OUTFIT_PALETTES for size in ("48x64", "96x128", "strip")]
)
ALL_GROUPS = tuple(CIV_MAP) + ("mateo", "bunker", "review")


def _safe_civ_paths(cid, entry):
    names = [entry.get(field, f"{cid.lower()}_{field.removesuffix('_png')}.png") for field in CIV_FIELDS]
    for name in names:
        if not isinstance(name, str) or Path(name).name != name or not name.endswith(".png"):
            raise ValueError(f"Invalid manifest path for {cid}: {name}")
    if len(set(names)) != len(names):
        raise ValueError(f"Duplicate manifest output paths for {cid}")
    return [f"civilizations/{name}" for name in names]


def _group_paths(group, manifest):
    if group in CIV_MAP:
        return _safe_civ_paths(group, manifest.get(group, {}))
    return list({"mateo": MATEO_FILES, "bunker": BUNKER_FILES, "review": REVIEW_FILES}[group])


def _validate_source(path, min_size=None):
    if not path.is_file():
        raise FileNotFoundError(f"Required source missing: {path}")
    with Image.open(path) as img:
        img.load()
        if min_size and (img.width < min_size[0] or img.height < min_size[1]):
            raise ValueError(f"Source image too small: {path} ({img.size}); need {min_size}")


def _validate_inputs(group, assets_dir, manifest, legacy_dir, source_dir=None):
    if source_dir is not None:
        concepts_dir = Path(source_dir)
    elif (assets_dir / "concepts").is_dir():
        concepts_dir = assets_dir / "concepts"
    elif (assets_dir.parent / "art/source").is_dir():
        concepts_dir = assets_dir.parent / "art/source"
    else:
        concepts_dir = ART_SOURCE_DIR

    if group in CONCEPT_FILES:
        _validate_source(resolve_concept_path(group, concepts_dir))
    elif group == "mateo":
        _validate_source(mateo_sprite_builder.resolve_source(mateo_sprite_builder.MATEO_SOURCE, "mateo", concepts_dir), (1024, 1024))
        _validate_source(mateo_sprite_builder.resolve_source(mateo_sprite_builder.BUNKER_SOURCE, "bunker", concepts_dir), (620, 580))
    elif group == "bunker":
        _validate_source(bunker_scene_builder.resolve_source(mateo_sprite_builder.BUNKER_SOURCE, "bunker", concepts_dir))
        _validate_source(assets_dir / "sprites/mateo_bunker_96x128.png", (96, 128))
    if group == "review":
        for cid in CIV_MAP:
            for relative in _group_paths(cid, manifest):
                _validate_source(assets_dir / relative, (128, 128))
        for cid in ("FASR-001", "FASR-005", "FASR-009"):
            path = legacy_dir / f"{cid.lower()}_face.png"
            if not path.is_file():
                path = legacy_dir / f"{cid.lower()}_legacy_face.png"
            _validate_source(path)


def _render_group(group, stage, assets_dir, manifest, legacy_dir, source_dir=None):
    if source_dir is not None:
        concepts_dir = Path(source_dir)
    elif (assets_dir / "concepts").is_dir():
        concepts_dir = assets_dir / "concepts"
    elif (assets_dir.parent / "art/source").is_dir():
        concepts_dir = assets_dir.parent / "art/source"
    else:
        concepts_dir = ART_SOURCE_DIR
    if group in CIV_MAP:
        folder, color, top, bottom, stars, target = CIV_MAP[group]
        paths = _group_paths(group, manifest)
        face = build_civ_face_layer(group, concepts_dir)
        env = build_civ_env_plate(group, concepts_dir)
        values = (face, env, Image.alpha_composite(env.convert("RGBA"), face.convert("RGBA")),
                  _build_constellation_plate(group, color, top, bottom, stars, target))
        for relative, image in zip(paths, values):
            dest = stage / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            image.save(dest)
        entry = dict(manifest.get(group, {}))
        if not entry:
            info = CIV_DATA_DIR / folder / "info.txt"
            if not info.is_file():
                raise FileNotFoundError(f"Required civilization information missing: {info}")
            entry = {"folder": folder, "status": "production_v2", "authored_lock": True,
                     "native_size": [128, 128], "primary_color": f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}",
                     "info_text": info.read_text(encoding="utf-8")}
            entry.update({key: Path(path).name for key, path in zip(CIV_FIELDS, paths)})
        manifest[group] = entry
        manifest_path = stage / "civilizations/manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return paths + ["civilizations/manifest.json"]
    if group == "mateo":
        mateo_sprite_builder._render_mateo_assets(stage, concepts_dir)
    elif group == "bunker":
        bunker_scene_builder._render_bunker_previews(stage, concepts_dir, assets_dir / "sprites/mateo_bunker_96x128.png")
    else:
        _render_review_sheets(stage, assets_dir / "civilizations", legacy_dir, manifest)
    return _group_paths(group, manifest)


def _validate_outputs(group, stage, paths):
    for relative in paths:
        path = stage / relative
        if not path.is_file():
            raise FileNotFoundError(f"Generated group is incomplete: {path}")
        if path.suffix == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
            if group == "bunker":
                if data.get("canvas_size") != [480, 270] or data.get("layers") != bunker_scene_builder.LAYER_NAMES:
                    raise ValueError(f"Invalid bunker manifest: {path}")
                if data.get("mateo_idle", {}).get("file") != "sprites/mateo_idle_48x64.png" or data.get("mateo_bunker", {}).get("file") != "sprites/mateo_bunker_96x128.png":
                    raise ValueError(f"Invalid bunker sprite references: {path}")
            elif group in CIV_MAP and _group_paths(group, data) != paths[:-1]:
                raise ValueError(f"Invalid civilization manifest references: {path}")
            continue
        with Image.open(path) as image:
            image.load()
            if group in CIV_MAP and image.size != (128, 128):
                raise ValueError(f"Invalid civilization image size: {path}: {image.size}")
            if relative in BUNKER_FILES and path.name in bunker_scene_builder.LAYER_NAMES and image.size != (480, 270):
                raise ValueError(f"Invalid bunker layer size: {path}: {image.size}")
            if group == "bunker":
                sizes = {"tileset_bunker_16x16.png": (128, 64), "bunker_preview_crt_off.png": (480, 270), "bunker_preview_crt_on.png": (1440, 810)}
                if image.size != sizes.get(path.name, (480, 270)):
                    raise ValueError(f"Invalid bunker image size: {path}: {image.size}")
            if group == "review":
                sizes = {"palette_sheet.png": (480, 270), "before_after_comparison.png": (620, 440), "all_civilizations_roster.png": (560, 1500)}
                if image.size != sizes[path.name]:
                    raise ValueError(f"Invalid review image size: {path}: {image.size}")
            if group == "mateo":
                expected = (1180, 520) if path.name == "mateo_character_sheet.png" else ((1056, 128) if path.name.endswith("_strip.png") else ((128, 128) if "portrait" in path.name else ((48, 64) if "48x64" in path.name else (96, 128))))
                if image.size != expected:
                    raise ValueError(f"Invalid Mateo image size: {path}: {image.size}")


def _build_selected_groups(replace_groups=(), *, dry_run=False, groups=None, assets_dir=ASSETS_DIR,
                           archive_dir=None, legacy_dir=LEGACY_SOURCE_DIR, source_dir=None):
    """Preserve locked groups; explicitly selected groups are staged and archived."""
    assets_dir = Path(assets_dir).resolve()
    archive_dir = Path(archive_dir or (REPO_ROOT_DIR / "_trash" if assets_dir == ASSETS_DIR.resolve() else assets_dir.parent / "_trash")).resolve()
    if archive_dir == assets_dir or archive_dir.is_relative_to(assets_dir):
        raise ValueError("Recovery archives must be outside the active assets directory")
    groups = list(ALL_GROUPS if groups is None else groups)
    replacements = set(replace_groups)
    if not set(groups) <= set(ALL_GROUPS) or not replacements <= set(groups) or len(groups) != len(set(groups)):
        raise ValueError("Unknown, duplicate or unselected asset group")
    journal = assets_dir.parent / f".{assets_dir.name}-asset-build-pending.json"
    if dry_run and journal.exists():
        raise RuntimeError(f"Pending transaction requires recovery before dry-run: {journal}")
    if not dry_run:
        recover_pending(assets_dir)
    manifest_path = assets_dir / "civilizations/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    all_civ_paths = [path for cid in CIV_MAP if cid in manifest for path in _group_paths(cid, manifest)]
    if len(all_civ_paths) != len(set(all_civ_paths)):
        raise ValueError("Civilization groups share an output path")
    plans = []
    for group in groups:
        paths = _group_paths(group, manifest)
        present = [(assets_dir / path).is_file() for path in paths]
        locked = manifest.get(group, {}).get("authored_lock", False) if group in CIV_MAP else any(present)
        selected = group in replacements
        if locked and not selected:
            if not all(present):
                raise FileNotFoundError(f"Locked group {group} is incomplete; explicitly replace it to repair")
            print(f"Preserved locked group: {group}")
            continue
        if any(present) and not selected and not locked:
            raise RuntimeError(f"Existing unprotected outputs for {group}; explicitly select replacement")
        _validate_inputs(group, assets_dir, manifest, Path(legacy_dir), source_dir=source_dir)
        if group in CIV_MAP and group not in manifest:
            info = CIV_DATA_DIR / CIV_MAP[group][0] / "info.txt"
            if not info.is_file():
                raise FileNotFoundError(f"Required civilization information missing: {info}")
        plans.append(group)
    if dry_run:
        for group in plans:
            print(f"Would stage and promote: {group}")
        return plans
    for group in plans:
        with tempfile.TemporaryDirectory(prefix="asset-stage-", dir=assets_dir.parent) as temporary:
            stage = Path(temporary)
            paths = _render_group(group, stage, assets_dir, manifest, Path(legacy_dir), source_dir=source_dir)
            _validate_outputs(group, stage, paths)
            archive = promote_group(assets_dir, stage, archive_dir, group, paths)
            print(f"Promoted {group}; recovery archive: {archive}")
    return plans


def build_selected_groups(replace_groups=(), *, dry_run=False, groups=None, assets_dir=ASSETS_DIR,
                          archive_dir=None, legacy_dir=LEGACY_SOURCE_DIR, source_dir=None):
    """Serialize builds on the asset directory, including recovery and preflight."""
    assets_dir = Path(assets_dir).resolve()
    if fcntl is None:
        raise RuntimeError("Asset building requires a host with fcntl directory locking; use macOS for now")
    descriptor = os.open(assets_dir, os.O_RDONLY)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError(f"Another asset build is active: {assets_dir}") from exc
        return _build_selected_groups(replace_groups, dry_run=dry_run, groups=groups, assets_dir=assets_dir,
                                      archive_dir=archive_dir, legacy_dir=legacy_dir, source_dir=source_dir)
    finally:
        os.close(descriptor)


def build_civilization_assets(force_overwrite=False, *, replace_groups=(), dry_run=False, source_dir=None):
    """Preserve existing civilizations unless an individual group is selected."""
    if force_overwrite:
        raise ValueError("Bulk overwrite is unsafe; explicitly select each group with --replace")
    build_selected_groups(replace_groups, dry_run=dry_run, groups=list(CIV_MAP), source_dir=source_dir)
    path = OUT_CIV_DIR / "manifest.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def build_palette_and_comparison_sheets(*, replace=False, dry_run=False):
    """Preserve review sheets unless explicitly replaced as one group."""
    return build_selected_groups(["review"] if replace else [], dry_run=dry_run, groups=["review"])


def main(default_groups=None):
    parser = argparse.ArgumentParser(description="Safely build selected asset groups.")
    parser.add_argument("--replace", action="append", choices=ALL_GROUPS, default=[], help="Explicit group to replace; repeat for multiple groups")
    parser.add_argument("--dry-run", action="store_true", help="Validate and report changes without writing")
    parser.add_argument("--assets-dir", type=Path, default=ASSETS_DIR)
    parser.add_argument("--source-dir", type=Path, default=None, help="Directory containing art sources")
    parser.add_argument("--archive-dir", type=Path, default=None)
    args = parser.parse_args()
    groups = args.replace or default_groups
    if default_groups and not set(args.replace) <= set(default_groups):
        parser.error("This entry point only builds its own group")
    build_selected_groups(args.replace, dry_run=args.dry_run, groups=groups,
                          assets_dir=args.assets_dir, archive_dir=args.archive_dir,
                          source_dir=args.source_dir)


if __name__ == "__main__":
    main()
