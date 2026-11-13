"""
MODULE: tools/civ_art_builder.py
PURPOSE: Builds complete, defect-free 128x128 RGBA foreground portraits (*_face.png)
         and standalone 128x128 environment plates (*_env.png) for all 11 civilizations.
CALLED BY: tools/build_assets.py.
HOW TO MODIFY:
  - To tune a civilization's environment plate -> edit build_civ_env_plate().
  - To tune a civilization's foreground cutout -> edit build_civ_face_layer().
"""

import math
from pathlib import Path
from PIL import Image, ImageDraw

REPO_ROOT_DIR = Path(__file__).resolve().parent.parent
ART_SOURCE_DIR = REPO_ROOT_DIR / "art" / "source"
CIV_CONCEPTS_DIR = ART_SOURCE_DIR / "civilizations"
CONCEPTS_DIR = CIV_CONCEPTS_DIR
CONCEPT_FILES = {
    "FASR-001": "concept_fasr_001_1794333404634.jpg",
    "FASR-002": "concept_fasr_002.jpg",
    "FASR-003": "concept_fasr_003.jpg",
    "FASR-004": "concept_fasr_004.jpg",
    "FASR-005": "concept_fasr_005_1794333420891.jpg",
    "FASR-006": "concept_fasr_006.jpg",
    "FASR-007": "concept_fasr_007.jpg",
    "FASR-008": "concept_fasr_008.jpg",
    "FASR-009": "concept_fasr_009_1794333439876.jpg",
    "FASR-010": "concept_fasr_010.jpg",
}


def resolve_concept_path(cid, concepts_dir=None):
    """Resolve concept image path across art/source/civilizations/<cid>, flat dir or legacy."""
    fname = CONCEPT_FILES[cid]
    if concepts_dir is not None:
        p = Path(concepts_dir)
        if (p / fname).is_file():
            return p / fname
        if (p / cid / fname).is_file():
            return p / cid / fname
        if (p / "civilizations" / cid / fname).is_file():
            return p / "civilizations" / cid / fname
        return (p / "civilizations" / cid / fname) if (p / "civilizations").is_dir() else (p / cid / fname if (p / cid).is_dir() else p / fname)
    source_p = CIV_CONCEPTS_DIR / cid / fname
    if source_p.is_file():
        return source_p
    legacy_p = REPO_ROOT_DIR / "src" / "assets" / "concepts" / fname
    if legacy_p.is_file():
        return legacy_p
    return CIV_CONCEPTS_DIR / cid / fname


def quantize_rgba_clean(img, num_colors=32):
    """Quantize RGBA image while preserving alpha and preventing background color bleed."""
    src_px = img.load()
    rgb_clean = Image.new("RGB", img.size, (6, 8, 14))
    clean_px = rgb_clean.load()
    for py in range(img.height):
        for px in range(img.width):
            if src_px[px, py][3] > 96:
                clean_px[px, py] = src_px[px, py][:3]
    quant_rgb = rgb_clean.quantize(colors=num_colors, method=Image.Quantize.MEDIANCUT).convert("RGBA")
    q_px = quant_rgb.load()
    for py in range(img.height):
        for px in range(img.width):
            q_px[px, py] = (*q_px[px, py][:3], 255) if src_px[px, py][3] > 96 else (0, 0, 0, 0)
    return quant_rgb


def _add_starfield(env_img, seed_val, count=70, base_col=(130, 155, 185)):
    """Render deterministic pixel-art starfield across a 128x128 environment plate."""
    px_map = env_img.load()
    for idx in range(count):
        sx, sy = (idx * 53 + seed_val * 17 + 11) % 126 + 1, (idx * 37 + seed_val * 29 + 7) % 126 + 1
        brt = 0.55 + 0.45 * ((idx * 19) % 5) / 4.0
        px_map[sx, sy] = (int(base_col[0] * brt), int(base_col[1] * brt), int(base_col[2] * brt), 255)


def build_civ_env_plate(cid, concepts_dir=None):
    """Build a complete, uninterrupted 128x128 pixel-art environment plate with zero holes."""
    env = Image.new("RGBA", (128, 128), (5, 7, 14, 255))
    draw, epx = ImageDraw.Draw(env), env.load()
    if cid == "FASR-001":
        for py in range(128):
            for px in range(128):
                neb = int(14 * math.sin((px + py) * 0.06) + 10 * math.cos((px - py) * 0.08))
                epx[px, py] = (max(4, 14 + neb // 2), max(8, 22 + neb), max(14, 30 + neb), 255)
        _add_starfield(env, 1, 85, (180, 220, 210))
        for rad in (58, 44, 30, 16):
            draw.ellipse((64 - rad, 64 - rad, 64 + rad, 64 + rad), outline=(18, 58, 46, 255))
        draw.line((0, 64, 127, 64), fill=(14, 44, 36, 255))
        draw.line((64, 0, 64, 127), fill=(14, 44, 36, 255))
    elif cid == "FASR-002":
        for py in range(128):
            for px in range(128):
                d_v, band = math.hypot(px - 64, py - 64), max(0, 28 - abs(int((px - 64) * 0.5 + (py - 64) - 4)))
                epx[px, py] = (min(75, int(10 + band * 1.4 + max(0, 50 - d_v) * 0.5)), int(8 + band * 0.5), int(16 + band * 0.7), 255)
        _add_starfield(env, 2, 90, (240, 195, 150))
        for rad in (54, 40):
            draw.ellipse((64 - rad, 64 - rad, 64 + rad, 64 + rad), outline=(56, 32, 22, 255))
    elif cid == "FASR-003":
        _add_starfield(env, 3, 75, (160, 225, 240))
        for rad in range(52, 0, -1):
            col = (210, 252, 255, 255) if rad < 34 else (int(12 + (52 - rad) * 9), int(65 + (52 - rad) * 10), int(95 + (52 - rad) * 8), 255)
            draw.ellipse((60 - rad, 64 - rad, 60 + rad, 64 + rad), fill=col)
    elif cid == "FASR-004":
        for py in range(128):
            for px in range(128):
                pillar = 1 if (26 <= px <= 54 and py > 14) or (72 <= px <= 104 and py > 26) else 0
                epx[px, py] = (28 + (py // 6), 14, 34 + (py // 5), 255) if pillar else (10, 6, 18, 255)
        _add_starfield(env, 4, 80, (235, 175, 245))
    elif cid == "FASR-005":
        src = Image.open(resolve_concept_path(cid, concepts_dir)).convert("RGBA").resize((128, 128), Image.Resampling.NEAREST)
        spx = src.load()
        for py in range(128):
            for px in range(128):
                if px < 64:
                    d_sun = math.hypot(px - 12, py - 68)
                    proc = (76 + (py % 4) * 8, 30 + (py % 3) * 4, 18, 255) if py >= 96 else (max(26, int(215 - d_sun * 2.5)), max(12, int(92 - d_sun * 1.2)), 22, 255)
                    w_s = max(0.0, min(1.0, (32 - px) / 14.0)) * max(0.0, min(1.0, (94 - py) / 10.0))
                else:
                    proc = (18, 34, 58, 255) if py >= 96 else (6, 10, 20, 255)
                    w_s = max(0.0, min(1.0, (px - 95) / 12.0)) * max(0.0, min(1.0, (94 - py) / 10.0))
                sr, sg, sb, _ = spx[px, py]
                epx[px, py] = (int(sr * w_s + proc[0] * (1 - w_s)), int(sg * w_s + proc[1] * (1 - w_s)), int(sb * w_s + proc[2] * (1 - w_s)), 255)
        for bx, top_y, bw in [(66, 68, 10), (76, 48, 12), (86, 36, 12), (96, 22, 14)]:
            draw.polygon([(bx, 96), (bx + bw // 2, top_y), (bx + bw, 96)], fill=(38, 72, 118, 255), outline=(74, 126, 184, 255))
        draw.line((63, 0, 63, 127), fill=(184, 96, 44, 255))
    elif cid == "FASR-006":
        _add_starfield(env, 6, 80, (200, 220, 250))
        # Relativistic magnetic field lines and pulsar jet emission cones
        for py in range(128):
            for px in range(128):
                d = math.hypot(px - 64, py - 64)
                ang = math.atan2(py - 64, px - 64)
                beam = math.exp(-((ang - 0.785) ** 2) / 0.08) + math.exp(-((ang + 2.356) ** 2) / 0.08)
                if d < 55 and beam > 0.05:
                    r = int(180 * beam + 20)
                    g = int(45 * beam + 15)
                    b = int(70 * beam + 25)
                    epx[px, py] = (min(255, r), min(255, g), min(255, b), 255)
        # Pulsar core and magnetic dipole arcs
        for r_dipole in (20, 32, 44):
            draw.arc((64 - r_dipole, 64 - r_dipole * 2, 64 + r_dipole, 64 + r_dipole * 2), 40, 140, fill=(38, 168, 196, 255), width=2)
            draw.arc((64 - r_dipole, 64 - r_dipole * 2, 64 + r_dipole, 64 + r_dipole * 2), 220, 320, fill=(38, 168, 196, 255), width=2)
        draw.ellipse((60, 60, 68, 68), fill=(255, 240, 240, 255), outline=(220, 40, 60, 255))
    elif cid == "FASR-007":
        # The 1420.405 MHz Hydrogen Line Transmission: Deep celestial nebula and spectrogram
        for py in range(128):
            for px in range(128):
                d1 = math.hypot(px - 40, py - 48)
                d2 = math.hypot(px - 88, py - 80)
                neb1 = max(0, int(60 - d1 * 0.9 + 12 * math.sin(px * 0.15) * math.cos(py * 0.12)))
                neb2 = max(0, int(50 - d2 * 0.8 + 10 * math.cos(px * 0.18) * math.sin(py * 0.14)))
                r = 10 + neb1 // 2 + neb2 // 4
                g = 22 + neb1 + neb2 // 2
                b = 32 + neb1 // 2 + neb2
                epx[px, py] = (r, g, b, 255)
        _add_starfield(env, 7, 75, (180, 245, 230))
        # Radio spectral carrier waterfall grid
        for g_pos in range(8, 128, 16):
            draw.line((g_pos, 0, g_pos, 127), fill=(18, 48, 56, 180))
            draw.line((0, g_pos, 127, g_pos), fill=(18, 48, 56, 180))
        # The 6EQUJ5 signal intensity profile waveform across frequency channels
        for px in range(128):
            env_val = math.exp(-((px - 64) ** 2) / 320.0)
            osc = math.sin(px * 0.6) * 12.0 * env_val
            draw.line((px, int(64 - osc), px, int(64 + osc)), fill=(36, 188, 165, 255))
            draw.point((px, int(64 - osc)), fill=(255, 220, 90, 255))
        # Foreground interferometer dish lattice silhouette
        draw.arc((16, 75, 112, 135), 180, 360, fill=(14, 28, 36, 255), width=3)
        draw.line([(64, 105), (64, 127)], fill=(20, 42, 54, 255), width=4)
        draw.line([(64, 75), (64, 95)], fill=(210, 160, 40, 255), width=2)
    elif cid == "FASR-008":
        # Stellar chromosphere and coronal mass ejection loops
        for py in range(128):
            for px in range(128):
                d = math.hypot(px - 64, py - 64)
                turb = math.sin(px * 0.2) * math.cos(py * 0.2) * 8
                if d < 48:
                    intensity = max(0, min(255, int(255 - (d + turb) * 3.8)))
                    epx[px, py] = (min(255, intensity + 80), max(0, min(255, int(intensity * 0.55))), 20, 255)
                else:
                    epx[px, py] = (12, 8, 16, 255)
        _add_starfield(env, 8, 65, (230, 195, 180))
        # Magnetic coronal plasma prominence loops
        for rad, width, col in [(54, 2, (196, 48, 22, 255)), (46, 2, (245, 118, 32, 255)), (38, 2, (255, 210, 60, 255))]:
            draw.arc((64 - rad, 64 - rad, 64 + rad, 64 + rad), 200, 340, fill=col, width=width)
            draw.arc((64 - rad, 64 - rad, 64 + rad, 64 + rad), 20, 160, fill=col, width=width)
    elif cid == "FASR-009":
        for py in range(128):
            for px in range(128):
                band = max(0, 18 - abs((px + py) - 128) // 4)
                epx[px, py] = (6 + band // 2, 8 + band // 2, 16 + band, 255)
        _add_starfield(env, 9, 80, (170, 185, 220))
        draw.arc((-14, 14, 142, 150), 198, 264, fill=(108, 76, 158, 255))
        draw.arc((4, 2, 154, 138), 192, 256, fill=(56, 96, 124, 255))
    elif cid == "FASR-010":
        # Göbekli Tepe Megalithic Sanctuary: Sirius astronomical alignment & T-shaped monoliths
        for py in range(128):
            for px in range(128):
                sky_t = py / 128.0
                epx[px, py] = (int(10 + sky_t * 18), int(14 + sky_t * 24), int(22 + sky_t * 30), 255)
        _add_starfield(env, 10, 85, (220, 230, 255))
        # Prominent Sirius / Cygnus alignment ray
        draw.line([(64, 0), (64, 60)], fill=(180, 210, 255, 180), width=1)
        draw.ellipse((61, 22, 67, 28), fill=(255, 255, 255, 255), outline=(140, 180, 255, 255))
        # Ceremonial circular stone megalith enclosure wall
        for r_stone in range(48, 128, 16):
            for c_stone in range(0, 128, 22):
                draw.rectangle((c_stone, r_stone, c_stone + 20, r_stone + 14), fill=(34, 46, 52, 255), outline=(18, 24, 28, 255))
                # Stone chisel relief markings
                draw.point((c_stone + 6, r_stone + 5), fill=(65, 85, 95, 255))
                draw.point((c_stone + 14, r_stone + 9), fill=(65, 85, 95, 255))
        # Central twin T-shaped Göbekli Tepe monolith pillars
        # Left Pillar
        draw.polygon([(26, 44), (54, 44), (54, 56), (44, 56), (44, 127), (36, 127), (36, 56), (26, 56)], fill=(52, 68, 76, 255), outline=(22, 30, 36, 255))
        draw.line([(37, 46), (53, 46)], fill=(95, 122, 134, 255), width=2)
        draw.ellipse((38, 72, 42, 80), fill=(80, 105, 116, 255))
        # Right Pillar
        draw.polygon([(74, 48), (102, 48), (102, 60), (92, 60), (92, 127), (84, 127), (84, 60), (74, 60)], fill=(46, 60, 68, 255), outline=(20, 26, 32, 255))
        draw.line([(85, 50), (101, 50)], fill=(88, 114, 126, 255), width=2)
        draw.ellipse((86, 76, 90, 84), fill=(72, 95, 106, 255))
    elif cid == "FASR-SCAN-H":
        for py in range(128):
            for px in range(128):
                fog = max(0, int(112 - math.hypot(px - 64, py - 64) * 0.95 + 10 * math.sin(px * 0.12) * math.cos(py * 0.1)))
                epx[px, py] = (34 + fog, 24 + int(fog * 0.78), 22 + int(fog * 0.62), 255) if 7 < px < 120 else (18, 20, 26, 255)
    return quantize_rgba_clean(env, 24)


def build_civ_face_layer(cid, concepts_dir=None):
    """Build a clean, complete 128x128 RGBA foreground portrait cutout with solid internal silhouettes."""
    face = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    fpx = face.load()
    if cid == "FASR-SCAN-H":
        draw = ImageDraw.Draw(face)
        # 1. Cephalic mantle dorsal shell
        mantle_pts = [(48, 12), (80, 12), (90, 44), (82, 68), (46, 68), (38, 44)]
        draw.polygon(mantle_pts, fill=(32, 40, 52, 255), outline=(16, 20, 28, 255))
        draw.polygon([(52, 16), (76, 16), (84, 42), (76, 64), (52, 64), (44, 42)], fill=(48, 62, 80, 255))
        # Epidermal translucent highlights
        draw.line([(54, 18), (74, 18)], fill=(110, 142, 176, 255), width=2)
        draw.line([(46, 36), (48, 54)], fill=(82, 108, 138, 255), width=1)
        draw.line([(82, 36), (80, 54)], fill=(82, 108, 138, 255), width=1)
        # Epidermal chromatophores on mantle
        for mx in range(50, 78, 5):
            for my in range(24, 58, 7):
                draw.point((mx, my), fill=(95, 130, 165, 255))
                draw.point((mx + 1, my), fill=(140, 180, 220, 255))

        # 2. Respiration fissures / bio-acoustic slits
        for ry in range(22, 58, 6):
            draw.arc((48, ry, 80, ry + 10), 180, 360, fill=(75, 98, 128, 255), width=2)
            draw.point((64, ry + 1), fill=(145, 185, 225, 255))

        # 3. 7 Articulated muscular tentacles with suction apertures & chromatophores
        for k_i in range(7):
            tx = 16 + k_i * 16
            bend = int(6 * math.sin(k_i * 0.9))
            draw.polygon([
                (52 + (k_i - 3) * 4, 62),
                (60 + (k_i - 3) * 4, 62),
                (tx + 6 + bend, 126),
                (tx - 2 + bend, 126)
            ], fill=(28, 36, 48, 255), outline=(48, 62, 82, 255))
            # Inner limb highlight
            draw.line([(56 + (k_i - 3) * 4, 66), (tx + 2 + bend, 124)], fill=(68, 88, 114, 255), width=1)
            # Bioluminescent suction nodes
            for sy in range(74, 122, 12):
                nx = int(56 + (k_i - 3) * 4 + (tx + 2 + bend - (56 + (k_i - 3) * 4)) * ((sy - 66) / 58.0))
                draw.point((nx, sy), fill=(110, 215, 225, 255))

        # 4. Circular Heptapod Bio-Ink Logogram Emission Mist
        for rad in range(22, 28):
            draw.ellipse((64 - rad, 72 - rad, 64 + rad, 72 + rad), outline=(40, 20, 25, 255))
        for k_i in range(7):
            ang = k_i * 2 * math.pi / 7.0
            nx, ny = int(64 + 25 * math.cos(ang)), int(72 + 25 * math.sin(ang))
            # Logogram ink node burst
            draw.ellipse((nx - 5, ny - 5, nx + 5, ny + 5), fill=(210, 48, 42, 255), outline=(255, 180, 70, 255))
            draw.point((nx, ny), fill=(255, 240, 180, 255))
            draw.arc((nx - 9, ny - 9, nx + 9, ny + 9), int(k_i * 51), int(k_i * 51 + 160), fill=(160, 36, 32, 255), width=2)

        return quantize_rgba_clean(face, 24)
    src = Image.open(resolve_concept_path(cid, concepts_dir)).convert("RGBA")
    if cid == "FASR-009":
        sub = src.resize((112, 112), Image.Resampling.NEAREST)
        src = Image.new("RGBA", (128, 128), (0, 0, 0, 255))
        src.paste(sub, (4, 12))
    else:
        src = src.resize((128, 128), Image.Resampling.NEAREST)
    spx = src.load()
    if cid == "FASR-009":
        queue = [(x, y) for x in range(128) for y in (0, 127)] + [(x, y) for x in (0, 127) for y in range(128)]
        bg_vis = set(queue)
        while queue:
            cx, cy = queue.pop()
            for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                if 0 <= nx < 128 and 0 <= ny < 128 and (nx, ny) not in bg_vis and (sum(spx[nx, ny][:3]) <= 56 or (nx < 46 and ny < 50) or (nx > 92 and ny > 92) or (nx - ny >= 90) or (nx + (128 - ny) >= 212)):
                    bg_vis.add((nx, ny))
                    queue.append((nx, ny))
        for py in range(128):
            for px in range(128):
                if (px, py) not in bg_vis and sum(1 for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)) if (px + dx, py + dy) not in bg_vis) >= 2:
                    fpx[px, py] = (min(165, spx[px, py][0]), min(160, spx[px, py][1]), min(175, spx[px, py][2]), 255)
    elif cid in ("FASR-007", "FASR-010"):
        for py in range(128):
            if cid == "FASR-007":
                pts = [x for x in range(14, 112) if (6 <= py < 26 and 28 <= x <= 100 and (spx[x, py][0] > spx[x, py][2] + 8 or sum(spx[x, py][:3]) > 95)) or (26 <= py <= 62 and 40 <= x <= 88 and sum(spx[x, py][:3]) > 28) or (py > 62 and sum(spx[x, py][:3]) > 38 and not (x > 92 and py < 98))]
            else:
                pts = [x for x in range(28, 101) if (4 <= py <= 52 and (spx[x, py][0] > spx[x, py][2] or spx[x, py][1] > 140 or sum(spx[x, py][:3]) > 65)) or (py > 52 and 32 <= x <= 96 and (spx[x, py][0] > spx[x, py][2] or sum(spx[x, py][:3]) > 42))]
            span = range(min(pts), max(pts) + 1) if (len(pts) >= 2 and (cid != "FASR-007" or py >= 26)) else pts
            for px in span:
                fpx[px, py] = (*spx[px, py][:3], 255)
    else:
        for py in range(128):
            for px in range(128):
                r_v, g_v, b_v, _ = spx[px, py]
                tot, d_c = r_v + g_v + b_v, math.hypot(px - 64, py - 64)
                if cid == "FASR-001":
                    if 56 <= py <= 67 and (20 <= px <= 46 or 82 <= px <= 108):
                        r_v, g_v, b_v, _ = spx[px, 128 - py]
                    elif 92 <= py <= 104 and 64 <= px <= 84:
                        r_v, g_v, b_v, _ = spx[128 - px, py]
                    if d_c <= 23 or (d_c <= 51 and (g_v > 42 or b_v > 48 or r_v > 56)):
                        fpx[px, py] = (r_v, g_v, b_v, 255)
                elif cid == "FASR-002" and (d_c <= 19 or (tot > 85 and (r_v > b_v + 15 or d_c <= 36) and 4 <= px <= 123 and 16 <= py <= 112)):
                    fpx[px, py] = (r_v, g_v, b_v, 255)
                elif cid == "FASR-003" and not (r_v > 205 and g_v > 235 and b_v > 235) and ((tot > 42 and 12 <= px <= 118 and 8 <= py <= 120 and d_c <= 48) or d_c < 34):
                    fpx[px, py] = (r_v, g_v, b_v, 255)
                elif cid == "FASR-004" and ((r_v > 85 and b_v > 75 and r_v + b_v > g_v * 2 + 40) or (d_c < 22 and tot > 180)):
                    fpx[px, py] = (r_v, g_v, b_v, 255)
                elif cid == "FASR-005":
                    hw = 24.5 * math.sqrt(max(0.0, 1.0 - ((py - 31.0) / 25.0) ** 2)) if 6 <= py <= 46 else 0.0
                    bl = int(63.5 - hw) if py <= 46 else (int(39 + (py - 47) * 0.28) if py <= 63 else (int(42 - (py - 64) * 0.8) if py <= 74 else (34 if py <= 90 else int(34 - (py - 90) * 0.92))))
                    br = int(63.5 + hw) if py <= 46 else (int(88 - (py - 47) * 0.28) if py <= 63 else (int(85 + (py - 64) * 0.8) if py <= 74 else (93 if py <= 90 else int(93 + (py - 90) * 0.92))))
                    if py >= 6 and bl <= px <= br:
                        fpx[px, py] = (r_v, g_v, b_v, 255)
                elif cid == "FASR-006" and (d_c <= 25 or (abs((px - 64) + (py - 56)) < 14 and b_v > 140) or ((26 <= d_c <= 46 or (py > 80 and 68 <= px <= 108)) and (r_v > b_v or tot > 75))):
                    fpx[px, py] = (r_v, g_v, b_v, 255)
                elif cid == "FASR-008" and 23 <= d_c <= 56 and (r_v > 75 or (b_v > 95 and px > 80)):
                    fpx[px, py] = (r_v, g_v, b_v, 255)
    quant = quantize_rgba_clean(face, 28)
    if cid == "FASR-009":
        qpx = quant.load()
        for px, py, col in [(61, 78, (180, 130, 255, 255)), (64, 76, (180, 130, 255, 255)), (70, 72, (255, 158, 44, 255))]:
            qpx[px, py] = qpx[px + 1, py] = col
    return quant
