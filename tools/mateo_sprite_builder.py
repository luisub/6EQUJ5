"""
MODULE: tools/mateo_sprite_builder.py
PURPOSE: Builds Huntdown-grade 16-bit pixel-art portrait, 3 outfits, and 11
         articulated action poses for Dr. Mateo 'Six' Vargas from the master rig.
CALLED BY: bunker_scene_builder.py and build_assets.py.
HOW TO MODIFY:
  - To adjust hair/face/eye sculpture -> edit _extract_base_mateo_128().
  - To add or tune outfit material ramps -> edit _recolor_outfit().
  - To adjust limb articulation angles/offsets -> edit POSE_TABLE in _build_pose().
"""

from pathlib import Path
import tempfile
from PIL import Image, ImageDraw

REPO_ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = REPO_ROOT_DIR / "src" / "assets"
SPRITES_DIR = ASSETS_DIR / "sprites"
ART_SOURCE_DIR = REPO_ROOT_DIR / "art" / "source"
MATEO_SOURCE = "concept_mateo_idle_1794333616733.jpg"
BUNKER_SOURCE = "concept_bunker_clean_1794333595362.jpg"
CONCEPTS_DIR = ART_SOURCE_DIR / "mateo"

OUTFIT_PALETTES = {
    "navy_chore": {"label": "NAVY CHORE COAT (PI / CHIEF SCIENTIST)"},
    "olive_field": {"label": "1977 OLIVE M-65 FIELD JACKET"},
    "faraday_rig": {"label": "2029 FARADAY TACTICAL LAB SUIT"},
}
POSE_NAMES = ("idle_1", "idle_2", "run_1", "run_2", "run_3", "run_4", "jump", "crouch", "slide", "shoot", "tune")
ACTION_POSE_NAMES = (
    "idle_1", "idle_2", "idle_3", "idle_4",
    "walk_1", "walk_2",
    "run_1", "run_2", "run_3", "run_4",
    "jump", "fall", "land",
    "crouch", "slide",
    "cover_low", "cover_background",
    "shoot", "recoil", "tune",
    "hurt", "death",
)
POSE_TABLE = {
    "idle_1": (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    "idle_2": (0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 0, 1, -2, 0, 1, 0, 0, 1),
    "idle_3": (0, 0, 0, 0, 0, 0, 0, 0, 2, 3, 0, 2, -3, 0, 2, 0, 0, 2),
    "idle_4": (0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, -1, 0, 1, 0, 0, 1),
    "walk_1": (-14, -1, -1, 12, 1, -1, -2, 1, 1, 14, 1, 1, -12, -1, 1, -1, 1, 1),
    "walk_2": (12, 2, -1, -14, -1, -1, -2, 1, 1, -12, 1, 1, 14, 0, 1, -1, 1, 1),
    "run_1": (-24, -2, -2, 22, 2, -2, -4, 1, 1, 24, 1, 1, -22, -1, 1, -2, 1, 1),
    "run_2": (-10, 0, -1, 10, 0, 0, -2, 0, 2, 10, 1, 2, -10, 0, 2, -1, 0, 2),
    "run_3": (22, 4, -2, -24, -2, -2, -4, 1, 1, -20, 2, 1, 24, 0, 1, -2, 1, 1),
    "run_4": (10, 1, 0, -10, -1, -1, -2, 0, 2, -10, 1, 2, 10, 0, 2, -1, 0, 2),
    "jump": (-26, -2, -9, 30, 2, -11, -5, 1, -8, -22, 2, -8, 34, -1, -8, -3, 1, -8),
    "fall": (-14, -1, -3, 16, 1, -4, 3, 0, -3, -28, 1, -5, 22, -1, -4, 4, 0, -3),
    "land": (-8, -1, -2, 10, 1, -2, -3, 1, 4, 6, 1, 4, 20, -1, 3, -1, 1, 4),
    "crouch": (-16, -1, -7, 20, 3, -7, -6, 2, 9, 12, 1, 9, 38, -1, 7, -3, 2, 9),
    "slide": (46, -2, 10, 54, 2, 12, 20, -16, 26, -15, -14, 25, 32, -14, 24, 10, -14, 26),
    "cover_low": (-18, -1, -8, 22, 3, -8, -8, 2, 10, 14, 1, 10, 42, -1, 8, -4, 2, 10),
    "cover_background": (0, 0, 0, 0, 0, 0, 0, 0, 0, 12, -2, 0, 24, -4, 0, 0, 0, 0),
    "shoot": (-6, -1, 0, 8, 1, 0, -2, 0, 0, 6, 0, 0, 68, -2, 1, 0, 0, 0),
    "recoil": (-6, -1, 0, 8, 1, 0, -5, -2, 0, 14, -2, 0, 80, -3, -2, -2, -2, 0),
    "tune": (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 52, -2, 1, -2, 0, 0),
    "hurt": (-16, -3, 2, 22, 3, 2, -14, -5, -2, -32, -4, -2, -24, -4, -2, -12, -5, -3),
    "death": (-55, -12, 22, -45, -10, 24, -75, -24, 28, -75, -22, 26, -65, -26, 28, -75, -28, 30),
}
FACE_ROWS = {
    16: [(165, 96, 66), (204, 130, 92), (232, 160, 120), (232, 160, 120), (222, 152, 112), (210, 140, 100), (194, 122, 84), (168, 100, 68)], 17: [(158, 90, 62), (22, 18, 24), (18, 14, 20), (28, 22, 28), (216, 144, 104), (224, 152, 112), (22, 18, 24), (28, 22, 28)],
    18: [(176, 104, 72), (236, 224, 212), (24, 12, 8), (136, 78, 54), (198, 124, 86), (232, 162, 120), (228, 214, 200), (24, 12, 8)], 19: [(196, 120, 82), (224, 152, 112), (218, 144, 104), (192, 116, 80), (208, 134, 94), (236, 168, 126), (198, 124, 86), (168, 98, 66)],
    20: [(188, 114, 78), (220, 148, 108), (226, 156, 116), (142, 78, 52), (196, 120, 82), (214, 140, 100), (192, 118, 82), (164, 96, 66)], 21: [(154, 88, 60), (128, 64, 44), (198, 126, 88), (212, 140, 100), (204, 132, 92), (194, 122, 84), (136, 70, 48), (176, 108, 76)],
    22: [(178, 106, 72), (188, 114, 78), (116, 56, 38), (108, 50, 34), (108, 50, 34), (122, 60, 42), (184, 112, 78), (158, 92, 64)], 23: [(176, 106, 74), (194, 122, 86), (216, 144, 104), (224, 152, 112), (218, 146, 106), (202, 130, 92), (182, 112, 78), (142, 80, 56)],
    24: [(158, 92, 64), (182, 110, 76), (204, 132, 94), (216, 144, 104), (212, 140, 100), (196, 124, 88), (168, 100, 68), (118, 66, 46)], 25: [(118, 66, 46), (142, 82, 56), (164, 96, 66), (176, 106, 74), (168, 100, 68), (144, 84, 58), (98, 54, 38), (14, 16, 20)],
}


def resolve_source(filename, domain="mateo", concepts_dir=None):
    """Locate source concept image across art/source/<domain>, flat dir or legacy."""
    if concepts_dir is not None:
        base = Path(concepts_dir)
        if (base / filename).is_file():
            return base / filename
        if (base / domain / filename).is_file():
            return base / domain / filename
        return (base / domain / filename) if (base / domain).is_dir() else (base / filename)
    art_path = ART_SOURCE_DIR / domain / filename
    if art_path.is_file():
        return art_path
    legacy = ASSETS_DIR / "concepts" / filename
    if legacy.is_file():
        return legacy
    return ART_SOURCE_DIR / domain / filename


def _scale2x_epx(src):
    """Apply Eric's Pixel Expansion (Scale2x) for crisp 1x1 diagonal pixel clusters."""
    w, h = src.size
    dst = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    sp, dp = src.load(), dst.load()
    for y in range(h):
        for x in range(w):
            p, a, b, c, d = sp[x, y], sp[x, max(0, y - 1)], sp[min(w - 1, x + 1), y], sp[max(0, x - 1), y], sp[x, min(h - 1, y + 1)]
            dp[x * 2, y * 2], dp[x * 2 + 1, y * 2] = (c if (c == a and c != d and a != b) else p), (a if (a == b and a != c and b != d) else p)
            dp[x * 2, y * 2 + 1], dp[x * 2 + 1, y * 2 + 1] = (d if (d == c and d != b and c != a) else p), (b if (b == d and b != a and d != c) else p)
    return dst


def _extract_base_mateo_128(concepts_dir):
    """Extract the native 128x128 pixel grid from concept_mateo_idle and sculpt hair, eyes & jaw."""
    raw = Image.open(resolve_source(MATEO_SOURCE, "mateo", concepts_dir)).convert("RGBA")
    r_px, nat = raw.load(), Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    n_px = nat.load()
    for y in range(128):
        for x in range(128):
            rv, gv, bv, _ = r_px[x * 8 + 4, y * 8 + 4]
            if not ((rv > 130 and bv > 120 and gv < 115) or (rv + bv - 2 * gv > 85)):
                n_px[x, y] = (14, 16, 20, 255) if (bv > gv + 14 and rv > gv + 14) else (rv, gv, bv, 255)
    for y in range(12, 33):
        for x in range(38, 57):
            rv, gv, bv, av = n_px[x, y]
            if av > 0 and (y <= 26 or (y <= 28 and x <= 53) or (y <= 30 and x <= 49) or (abs(rv - gv) < 18 and bv >= gv - 6 and rv > 65)):
                n_px[x, y] = (0, 0, 0, 0)
    for hy, x0, cols in [
        (8, 63, [(12, 12, 16), (20, 18, 26), (28, 26, 36), (36, 32, 46), (28, 26, 36), (38, 34, 48), (28, 26, 36), (20, 18, 26), (12, 12, 16)]),
        (9, 62, [(14, 14, 20), (28, 26, 36), (42, 38, 52), (28, 26, 36), (46, 42, 58), (34, 30, 44), (48, 44, 60), (34, 30, 44), (44, 40, 56), (26, 24, 34), (14, 14, 18)]),
        (10, 62, [(14, 14, 20), (36, 32, 46), (24, 22, 30), (38, 34, 48), (26, 24, 34), (42, 38, 52), (28, 26, 36), (44, 40, 56), (30, 28, 38), (22, 20, 28), (16, 14, 22), (10, 10, 14)]),
    ]:
        for idx, col in enumerate(cols):
            n_px[x0 + idx, hy] = (*col, 255)
    n_px[73, 11] = (14, 14, 18, 255)
    for y in range(11, 17):
        for x in range(60, 74):
            rv, gv, bv, av = n_px[x, y]
            if av > 0 and (y <= 12 or x <= 65 or (y == 13 and x >= 72)):
                lum = (rv + gv + bv) // 3
                n_px[x, y] = (10, 10, 14, 255) if lum < 30 else ((22, 20, 28, 255) if lum < 55 else ((34, 30, 42, 255) if lum < 75 else (48, 42, 58, 255)))
    for fy, cols in FACE_ROWS.items():
        for idx, rgb in enumerate(cols):
            n_px[66 + idx, fy] = (*rgb, 255)
    n_px[65, 23], n_px[65, 24], n_px[65, 25] = (146, 84, 58, 255), (124, 68, 46, 255), (38, 24, 18, 255)
    return nat


def _recolor_outfit(base_img, outfit_key):
    """Apply luminance-preserving pixel-art material ramps without any neon boxes."""
    im = base_img.copy()
    px = im.load()
    for y in range(24, 115):
        for x in range(35, 92):
            r, g, b, a = px[x, y]
            if a == 0 or (r > g + 26 and r > 90 and (y >= 52 or (y <= 28 and 62 <= x <= 73))) or (27 <= y <= 34 and 61 <= x <= 65 and r > g and g > b + 8):
                continue
            lum = int(0.299 * r + 0.587 * g + 0.114 * b)
            if y <= 71:
                is_olive = g >= r - 12 and g > b + 4 and lum > 18
                if outfit_key == "navy_chore":
                    if 28 <= y <= 35 and 66 <= x <= 69 and lum > 35: px[x, y] = (232, 240, 250, 255) if lum > 70 else (180, 196, 218, 255)
                    elif x == 68 and y in (38, 45, 52, 59): px[x, y] = (224, 162, 68, 255)
                    elif is_olive: px[x, y] = (14, 22, 38, 255) if lum < 35 else ((22, 36, 62, 255) if lum < 55 else ((34, 54, 88, 255) if lum < 75 else ((48, 74, 116, 255) if lum < 98 else (68, 98, 146, 255))))
                elif outfit_key == "faraday_rig":
                    if (44 <= x <= 50 and 35 <= y <= 43 and lum > 30) or (x - y == 25 and 32 <= y <= 52 and lum > 35): px[x, y] = (232, 136, 44, 255) if lum > 65 else (164, 88, 28, 255)
                    elif is_olive: px[x, y] = (18, 22, 30, 255) if lum < 35 else ((30, 38, 50, 255) if lum < 55 else ((46, 56, 72, 255) if lum < 75 else ((66, 78, 98, 255) if lum < 98 else (90, 106, 128, 255))))
            elif 72 <= y <= 108 and outfit_key == "navy_chore" and lum > 22:
                px[x, y] = (20, 28, 42, 255) if lum < 45 else ((30, 42, 62, 255) if lum < 68 else (44, 58, 82, 255))
    return im


def _slice_parts(im):
    """Segment the 128x128 sprite into 6 clean anatomical pixel-art limb layers."""
    px = im.load()
    parts = {k: Image.new("RGBA", (128, 128), (0, 0, 0, 0)) for k in ("head", "torso", "b_arm", "f_arm", "r_leg", "l_leg")}
    p_px = {k: v.load() for k, v in parts.items()}
    for y in range(128):
        for x in range(128):
            c = px[x, y]
            if c[3] == 0:
                continue
            is_b_arm = 29 <= y <= 76 and ((y <= 51 and x <= 53) or (52 <= y <= 57 and x <= 52) or (y >= 58 and x <= 55))
            is_f_arm = 30 <= y <= 76 and x >= 75
            if y <= 25 and x >= 56: p_px["head"][x, y] = c
            elif is_b_arm and not (y >= 55 and c[1] > c[0] and c[1] > 40): p_px["b_arm"][x, y] = c
            elif is_f_arm: p_px["f_arm"][x, y] = c
            elif 24 <= y <= 70 and 56 <= x <= 74: p_px["torso"][x, y] = c
            elif 69 <= y <= 126 and (y >= 77 or 56 <= x <= 74):
                if x <= 64: p_px["r_leg"][x, y] = c
                if x >= 64: p_px["l_leg"][x, y] = c
    return parts


def _build_pose(parts, pose_name):
    """Articulate the 6 Huntdown pixel-art body parts into a 96x128 cell."""
    canvas = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    rl_d, rl_x, rl_y, ll_d, ll_x, ll_y, t_d, t_x, t_y, ba_d, ba_x, ba_y, fa_d, fa_x, fa_y, h_d, h_x, h_y = POSE_TABLE[pose_name]
    for key, piv, deg, dx, dy in [
        ("r_leg", (57, 72), rl_d, rl_x, rl_y), ("l_leg", (70, 72), ll_d, ll_x, ll_y),
        ("f_arm", (76, 36), fa_d, fa_x, fa_y), ("torso", (64, 50), t_d, t_x, t_y),
        ("head", (66, 22), h_d, h_x, h_y), ("b_arm", (51, 35), ba_d, ba_x, ba_y),
    ]:
        rot = parts[key].rotate(deg, resample=Image.Resampling.NEAREST, center=piv) if deg != 0 else parts[key]
        tmp = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
        tmp.paste(rot, (int(dx), int(dy)), rot)
        canvas.alpha_composite(tmp)
    if pose_name == "shoot":
        d = ImageDraw.Draw(canvas)
        d.rectangle((92, 41, 108, 46), fill=(42, 50, 60, 255), outline=(12, 14, 18, 255))
        d.line((93, 42, 106, 42), fill=(112, 126, 142, 255))
        d.rectangle((96, 43, 102, 45), fill=(198, 142, 54, 255))
        d.point([(107, 43), (107, 44)], fill=(238, 182, 84, 255))
    elif pose_name == "recoil":
        d = ImageDraw.Draw(canvas)
        d.rectangle((90, 32, 104, 38), fill=(42, 50, 60, 255), outline=(12, 14, 18, 255))
        d.line((91, 33, 103, 33), fill=(112, 126, 142, 255))
        d.rectangle((94, 34, 100, 37), fill=(198, 142, 54, 255))
    elif pose_name == "tune":
        d = ImageDraw.Draw(canvas)
        d.rectangle((90, 49, 98, 54), fill=(42, 50, 60, 255), outline=(12, 14, 18, 255))
        d.rectangle((92, 50, 96, 52), fill=(198, 142, 54, 255))
    return canvas.crop((16, 0, 112, 128))


def _build_mateo_portrait_128(navy_128, concepts_dir, sprites_dir):
    """Build 128x128 Mateo portrait matching the exact style of all_civilizations_roster.png."""
    env = Image.new("RGBA", (128, 128), (6, 10, 16, 255))
    bunker_src = resolve_source(BUNKER_SOURCE, "bunker", concepts_dir)
    if bunker_src.is_file():
        b_raw = Image.open(bunker_src).convert("RGB").crop((180, 140, 620, 580)).resize((128, 128), Image.Resampling.NEAREST)
        bp, ep = b_raw.quantize(colors=24, method=Image.Quantize.MEDIANCUT).convert("RGB").load(), env.load()
        for py in range(128):
            for px in range(128):
                r, g, b = bp[px, py]
                ep[px, py] = (int(r * 0.42), int(g * 0.46), int(b * 0.50), 255)
    bust_112 = _scale2x_epx(navy_128.crop((36, 4, 92, 60)))
    env.paste(bust_112, (8, 16), bust_112)
    ImageDraw.Draw(env).rectangle((0, 0, 127, 127), outline=(42, 88, 68, 255))
    env.save(sprites_dir / "mateo_portrait_128x128.png")
    return env


def _render_mateo_assets(assets_dir, concepts_dir=None):
    """Generate 128x128 portrait, 48x64 & 96x128 sprites for 3 outfits and 11 poses, plus master sheet."""
    sprites_dir = assets_dir / "sprites"
    sprites_dir.mkdir(parents=True, exist_ok=True)
    mateo_dir = sprites_dir / "mateo"
    mateo_dir.mkdir(parents=True, exist_ok=True)
    base_128 = _extract_base_mateo_128(concepts_dir)
    navy_128 = _recolor_outfit(base_128, "navy_chore")
    port_128, sheet = _build_mateo_portrait_128(navy_128, concepts_dir, sprites_dir), Image.new("RGBA", (1180, 520), (6, 9, 14, 255))
    port_128.save(mateo_dir / "portrait_128x128.png")
    s_draw = ImageDraw.Draw(sheet)
    s_draw.text((16, 10), "6EQUJ5: THE FERMI OVERRIDE - DR. MATEO 'SIX' VARGAS (HUNTDOWN 16-BIT RIG: 3 OUTFITS x 11 ACTIONS)", fill=(51, 255, 102, 255))
    sheet.paste(port_128, (16, 42))
    s_draw.text((18, 176), "128x128 BUST PORTRAIT", fill=(255, 158, 44, 255))
    for o_idx, (o_key, o_meta) in enumerate(OUTFIT_PALETTES.items()):
        outfit_128 = navy_128 if o_key == "navy_chore" else _recolor_outfit(base_128, o_key)
        parts, ry, strip = _slice_parts(outfit_128), 42 + o_idx * 156, Image.new("RGBA", (1056, 128), (0, 0, 0, 0))
        s_draw.text((160, ry - 13), o_meta["label"], fill=(255, 158, 44, 255))
        outfit_dir = mateo_dir / o_key
        outfit_dir.mkdir(parents=True, exist_ok=True)
        for p_idx, p_name in enumerate(POSE_NAMES):
            cell_96 = _build_pose(parts, p_name)
            cell_48 = cell_96.resize((48, 64), Image.Resampling.NEAREST)
            cell_96.save(sprites_dir / f"mateo_{o_key}_{p_name}_96x128.png")
            cell_96.save(outfit_dir / f"{p_name}.png")
            strip.paste(cell_96, (p_idx * 96, 0), cell_96)
            if p_name == "idle_1":
                cell_48.save(sprites_dir / f"mateo_{o_key}_48x64.png")
                cell_96.save(sprites_dir / f"mateo_{o_key}_96x128.png")
                cell_48.save(outfit_dir / "48x64.png")
                cell_96.save(outfit_dir / "96x128.png")
                if o_key == "navy_chore":
                    cell_48.save(sprites_dir / "mateo_idle_48x64.png")
                    cell_96.save(sprites_dir / "mateo_bunker_96x128.png")
                    cell_96.save(mateo_dir / "bunker_96x128.png")
            px, thumb = 160 + p_idx * 91, cell_96.crop((4, 0, 92, 126))
            s_draw.rectangle((px, ry, px + 88, ry + 126), fill=(10, 16, 22, 255), outline=(34, 62, 52, 255))
            sheet.paste(thumb, (px, ry), thumb)
            if o_idx == 0: s_draw.text((px + 18, ry + 128), p_name.upper(), fill=(170, 215, 195, 255))
        strip.save(sprites_dir / f"mateo_{o_key}_strip.png")
        strip.save(outfit_dir / "strip.png")
    sheet.save(assets_dir / "mateo_character_sheet.png")
    return sheet


def build_mateo_portrait_128(navy_128):
    """Render a portrait for existing callers without replacing protected files."""
    with tempfile.TemporaryDirectory(prefix="mateo-portrait-") as temporary:
        return _build_mateo_portrait_128(navy_128, CONCEPTS_DIR, Path(temporary))


def build_all_mateo_assets(*, replace=False, dry_run=False):
    """Safely preserve or explicitly rebuild the complete Mateo group."""
    from .build_assets import build_selected_groups
    result = build_selected_groups(["mateo"] if replace else [], dry_run=dry_run, groups=["mateo"])
    if dry_run:
        return result
    with Image.open(ASSETS_DIR / "mateo_character_sheet.png") as sheet:
        return sheet.copy()


def build_all_action_poses(assets_dir=ASSETS_DIR, concepts_dir=None):
    """Generate all 22 reviewed Huntdown action poses for all 3 outfits."""
    assets_dir = Path(assets_dir)
    mateo_dir = assets_dir / "sprites" / "mateo"
    base_128 = _extract_base_mateo_128(concepts_dir)
    navy_128 = _recolor_outfit(base_128, "navy_chore")
    for o_key in OUTFIT_PALETTES:
        outfit_128 = navy_128 if o_key == "navy_chore" else _recolor_outfit(base_128, o_key)
        parts = _slice_parts(outfit_128)
        outfit_dir = mateo_dir / o_key
        outfit_dir.mkdir(parents=True, exist_ok=True)
        for p_name in ACTION_POSE_NAMES:
            cell_96 = _build_pose(parts, p_name)
            cell_96.save(outfit_dir / f"{p_name}.png")


if __name__ == "__main__":
    from .build_assets import main
    main(default_groups=["mateo"])
