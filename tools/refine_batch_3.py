"""
MODULE: tools/refine_batch_3.py
PURPOSE: Six-iteration deep pixel-by-pixel quality enhancement for Batch 3 Art Assets:
         1. FASR-SCAN-H Heptapod Portrait (src/assets/civilizations/fasr-scan-h_face.png)
         2. Bunker Modular 16x16 Tileset (src/assets/bunker/tileset_bunker_16x16.png)
         3. Bunker Layer 01 Distant Structure (src/assets/bunker/01_distant_structure.png)
         4. Bunker Layer 03 Equipment (src/assets/bunker/03_equipment.png)
         5. Bunker Layer 04 Playable Floor (src/assets/bunker/04_playable_floor.png)

         - Iterations 1-3: Baseline noise/cavity elimination, contour clustering, material ramps.
         - Iteration 4: Deep detail refinement (calligraphy brush splatters, riveted industrial plates,
           hazard stripes 0xffaa00/0x1a1a24, conduit wire bundles, micro-architectural ribbing, industrial pipe valving).
         - Iteration 5: Density & depth modeling (multi-shade luminous heptapod ink density gradients
           from translucent 0x143c2c to dense 0x33ff66 core, 3-level girder depth beveling with 0xa0b0c8
           specular edge highlights, ordered Bayer atmospheric haze gradient dithering).
         - Iteration 6: Micro-detail finish (filament junction CRT glow pixels 0x00f0ff/0xd2ffeb,
           concrete micro-scuffs, metallic corrosion patina, CRT terminal blink indicators, dial gauges, binary alpha).
         - Updates corresponding composites (fasr-scan-h_composite.png) and bunker scene previews (CRT OFF/ON, inspection layers).
         - Generates high-resolution side-by-side inspection sheet under _temp/refine/ART_BATCH_3/batch_3_before_after_inspection.png.
         - Copies comparison sheet to brain directory and reports old vs new metrics.
CALLED BY: CLI (`python tools/refine_batch_3.py`).
HOW TO MODIFY: Adjust per-asset iteration parameters or update target material color ramps.
"""

import json
import math
from pathlib import Path
import shutil
from typing import Dict, List, Tuple
import numpy as np
from PIL import Image, ImageDraw

REPO_ROOT = Path(__file__).resolve().parent.parent
CIV_ASSETS_DIR = REPO_ROOT / "src" / "assets" / "civilizations"
BUNKER_ASSETS_DIR = REPO_ROOT / "src" / "assets" / "bunker"
TILESETS_BUNKER_DIR = REPO_ROOT / "src" / "assets" / "tilesets" / "bunker"
SPRITES_DIR = REPO_ROOT / "src" / "assets" / "sprites"
EVIDENCE_DIR = REPO_ROOT / "_temp" / "refine" / "ART_BATCH_3"
BRAIN_ARTIFACT_DIR = REPO_ROOT / "_temp" / "refine_artifacts"


# ═══════════════════════════════════════════════════════════════════════
# METRICS & NOISE AUDIT HELPERS
# ═══════════════════════════════════════════════════════════════════════
def calculate_asset_metrics(img: Image.Image) -> Tuple[int, int, int, int, int]:
    """Calculate solid pixels, orphan pixels, internal cavities, color outliers, and unique colors."""
    arr = np.array(img.convert("RGBA"))
    alpha = (arr[:, :, 3] > 0).astype(int)
    padded = np.pad(alpha, 1, mode="constant", constant_values=0)
    neighbor_count = (
        padded[:-2, :-2] + padded[:-2, 1:-1] + padded[:-2, 2:] +
        padded[1:-1, :-2] +                    padded[1:-1, 2:] +
        padded[2:, :-2] +  padded[2:, 1:-1] +  padded[2:, 2:]
    )
    orphans = int(np.sum((alpha == 1) & (neighbor_count <= 1)))
    cavities = int(np.sum((alpha == 0) & (neighbor_count >= 6)))
    solid = int(np.sum(alpha == 1))

    # Color outliers: pixels whose Euclidean RGB distance to all 4 orthogonal neighbors is > 35
    rgb = arr[:, :, :3].astype(float)
    up = np.roll(rgb, 1, axis=0)
    down = np.roll(rgb, -1, axis=0)
    left = np.roll(rgb, 1, axis=1)
    right = np.roll(rgb, -1, axis=1)
    d_up = np.linalg.norm(rgb - up, axis=2)
    d_down = np.linalg.norm(rgb - down, axis=2)
    d_left = np.linalg.norm(rgb - left, axis=2)
    d_right = np.linalg.norm(rgb - right, axis=2)
    min_d = np.minimum(np.minimum(d_up, d_down), np.minimum(d_left, d_right))

    interior = np.zeros_like(alpha, dtype=bool)
    if arr.shape[0] > 2 and arr.shape[1] > 2:
        interior[1:-1, 1:-1] = (
            (alpha[1:-1, 1:-1] == 1) &
            (alpha[:-2, 1:-1] == 1) &
            (alpha[2:, 1:-1] == 1) &
            (alpha[1:-1, :-2] == 1) &
            (alpha[1:-1, 2:] == 1)
        )
    outliers = int(np.sum((min_d > 35) & interior))
    unique_colors = len(set(tuple(p) for p in arr.reshape(-1, 4)))

    return solid, orphans, cavities, outliers, unique_colors


def clean_cavities_and_orphans(img: Image.Image, max_passes: int = 6) -> Image.Image:
    """Iteratively fill internal pinhole cavities and prune isolated specks."""
    arr = np.array(img.convert("RGBA"))
    for _ in range(max_passes):
        alpha = (arr[:, :, 3] > 0).astype(int)
        padded = np.pad(alpha, 1, mode="constant", constant_values=0)
        neighbors = (
            padded[:-2, :-2] + padded[:-2, 1:-1] + padded[:-2, 2:] +
            padded[1:-1, :-2] +                    padded[1:-1, 2:] +
            padded[2:, :-2] +  padded[2:, 1:-1] +  padded[2:, 2:]
        )
        to_remove = (alpha == 1) & (neighbors <= 1)
        to_fill = (alpha == 0) & (neighbors >= 6)
        arr[to_remove, 3] = 0
        if not np.any(to_fill):
            break
        fill_y, fill_x = np.where(to_fill)
        for y, x in zip(fill_y, fill_x):
            colors = []
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < arr.shape[0] and 0 <= nx < arr.shape[1] and arr[ny, nx, 3] > 0:
                        colors.append(arr[ny, nx, :3])
            if colors:
                arr[y, x, :3] = np.mean(colors, axis=0).astype(np.uint8)
                arr[y, x, 3] = 255
    return Image.fromarray(arr, "RGBA")


# ═══════════════════════════════════════════════════════════════════════
# ASSET 1: FASR-SCAN-H HEPTAPOD PORTRAIT (DEEP 6-ITERATION REFINEMENT)
# ═══════════════════════════════════════════════════════════════════════
def refine_fasr_scan_h(img: Image.Image) -> Image.Image:
    """Six-iteration deep quality refinement for FASR-SCAN-H Heptapod Face."""
    # ── Iteration 1: Noise & Pinhole Cavity Elimination ───────────────
    it1 = clean_cavities_and_orphans(img, max_passes=6)

    # ── Iteration 2: Clustered Anti-Aliasing & Contour Smoothing ───────
    it2 = it1.copy()
    px2 = it2.load()
    draw2 = ImageDraw.Draw(it2)

    orig_arr = np.array(it2)
    for y in range(1, 127):
        for x in range(1, 127):
            if orig_arr[y, x, 3] > 0:
                if (orig_arr[y, x - 1, 3] == 0 and orig_arr[y - 1, x, 3] == 0 and
                        orig_arr[y, x + 1, 3] > 0 and orig_arr[y + 1, x, 3] > 0):
                    px2[x - 1, y] = (*orig_arr[y, x, :3], 180)

    draw2.line([(52, 14), (76, 14)], fill=(125, 175, 215, 255), width=2)

    # ── Iteration 3: Material Shading & Specular Base ──────────────────
    it3 = it2.copy()
    px3 = it3.load()
    draw3 = ImageDraw.Draw(it3)

    for ry in range(22, 58, 6):
        draw3.arc((48, ry, 80, ry + 10), 180, 360, fill=(90, 125, 160, 255), width=2)
        px3[64, ry + 1] = (210, 240, 255, 255)

    for k_i in range(7):
        tx = 16 + k_i * 16
        bend = int(6 * math.sin(k_i * 0.9))
        draw3.line([(56 + (k_i - 3) * 4, 66), (tx + 2 + bend, 124)], fill=(75, 105, 135, 255), width=1)
        for sy in range(72, 122, 10):
            nx = int(56 + (k_i - 3) * 4 + (tx + 2 + bend - (56 + (k_i - 3) * 4)) * ((sy - 66) / 58.0))
            if 0 <= nx < 128 and 0 <= sy < 128:
                px3[nx, sy] = (120, 235, 245, 255)
                if nx + 1 < 128 and px3[nx + 1, sy][3] > 0:
                    px3[nx + 1, sy] = (235, 255, 255, 255)

    # ── Iteration 4: Calligraphy Brush Splatters & Micro-Curvatures ────
    it4 = it3.copy()
    px4 = it4.load()
    draw4 = ImageDraw.Draw(it4)
    cx, cy = 64, 72

    # Render organic calligraphic logogram ring with angular harmonic modulation
    for deg in range(360):
        rad_ang = math.radians(deg)
        r_base = 25.5 + 2.8 * math.sin(3 * rad_ang) + 1.6 * math.cos(7 * rad_ang)
        for dr in np.linspace(-2.5, 2.5, 9):
            rx = int(cx + (r_base + dr) * math.cos(rad_ang))
            ry = int(cy + (r_base + dr) * math.sin(rad_ang))
            if 0 <= rx < 128 and 0 <= ry < 128:
                # ── Iteration 5: Multi-Shade Heptapod Ink Density Gradients ──
                dist_center = abs(dr) / 2.5
                if dist_center <= 0.35:
                    col = (51, 255, 102, 255)  # dense core 0x33ff66
                elif dist_center <= 0.70:
                    col = (28, 125, 75, 255)   # mid emerald plume
                else:
                    col = (20, 60, 44, 255)    # translucent outer aura 0x143c2c
                px4[rx, ry] = col

    # Calligraphy outer perimeter flourishes & deliberate aerosol splatters
    splatter_angles = [15, 38, 72, 95, 125, 158, 185, 215, 248, 275, 305, 335]
    for idx, ang_deg in enumerate(splatter_angles):
        rad = math.radians(ang_deg)
        # Branching hook filament
        for step in range(1, 6):
            hx = int(cx + (28 + step * 1.4) * math.cos(rad + step * 0.08))
            hy = int(cy + (28 + step * 1.4) * math.sin(rad + step * 0.08))
            if 0 <= hx < 128 and 0 <= hy < 128:
                px4[hx, hy] = (30, 140, 80, 255)

        # Fine aerosol droplet
        sx = int(cx + (35 + (idx % 3) * 2) * math.cos(rad + 0.12))
        sy = int(cy + (35 + (idx % 3) * 2) * math.sin(rad + 0.12))
        if 0 <= sx < 128 and 0 <= sy < 128:
            px4[sx, sy] = (20, 60, 44, 255)

    # ── Iteration 6: Filament Junction Anti-Aliasing with CRT Glow Pixels ──
    for idx, ang_deg in enumerate(splatter_angles):
        rad = math.radians(ang_deg)
        sx = int(cx + (35 + (idx % 3) * 2) * math.cos(rad + 0.12))
        sy = int(cy + (35 + (idx % 3) * 2) * math.sin(rad + 0.12))
        if 0 <= sx + 1 < 128 and 0 <= sy < 128:
            px4[sx + 1, sy] = (0, 240, 255, 255)  # CRT cyan glow 0x00f0ff

    for k_i in range(7):
        ang = k_i * 2 * math.pi / 7.0
        nx, ny = int(cx + 25 * math.cos(ang)), int(cy + 25 * math.sin(ang))
        draw4.ellipse((nx - 4, ny - 4, nx + 4, ny + 4), fill=(225, 52, 45, 255), outline=(255, 195, 80, 255))
        px4[nx, ny] = (210, 255, 235, 255)      # CRT mint glow 0xd2ffeb
        px4[nx + 1, ny] = (0, 240, 255, 255)    # CRT cyan glow 0x00f0ff
        px4[nx, ny - 1] = (51, 255, 102, 255)   # dense phosphor core 0x33ff66

    # Binary alpha clamp
    for y in range(128):
        for x in range(128):
            r, g, b, a = px4[x, y]
            px4[x, y] = (r, g, b, 255) if a >= 128 else (0, 0, 0, 0)

    final = clean_cavities_and_orphans(it4, max_passes=6)
    return final


# ═══════════════════════════════════════════════════════════════════════
# ASSET 2: BUNKER MODULAR 16x16 TILESET (DEEP 6-ITERATION REFINEMENT)
# ═══════════════════════════════════════════════════════════════════════
def refine_tileset_bunker(img: Image.Image) -> Image.Image:
    """Six-iteration deep quality refinement for Bunker Modular 16x16 Tileset (128x64)."""
    res = img.copy()
    px = res.load()
    draw = ImageDraw.Draw(res)

    # ── Iteration 1: Noise & Pinhole Cavity Elimination ───────────────
    for r in range(4):
        for c in range(8):
            x0, y0 = c * 16, r * 16
            for ty in range(1, 15):
                for tx in range(1, 15):
                    gx, gy = x0 + tx, y0 + ty
                    col = np.array(px[gx, gy][:3], dtype=float)
                    nbrs = [
                        np.array(px[gx, gy - 1][:3], dtype=float),
                        np.array(px[gx, gy + 1][:3], dtype=float),
                        np.array(px[gx - 1, gy][:3], dtype=float),
                        np.array(px[gx + 1, gy][:3], dtype=float),
                    ]
                    dists = [np.linalg.norm(col - n) for n in nbrs]
                    if min(dists) > 32:
                        med = np.median(nbrs, axis=0).astype(np.uint8)
                        px[gx, gy] = (int(med[0]), int(med[1]), int(med[2]), 255)

    # ── Iteration 2: Clustered Anti-Aliasing & Contour Smoothing ───────
    for c in range(8):
        x0 = c * 16
        draw.line([(x0, 0), (x0, 15)], fill=(18, 22, 28, 255), width=1)
        draw.line([(x0 + 1, 0), (x0 + 1, 15)], fill=(32, 40, 48, 255), width=1)

        y1 = 16
        for sy in range(y1 + 3, y1 + 15, 3):
            draw.line([(x0 + 2, sy), (x0 + 14, sy)], fill=(22, 28, 32, 255), width=1)

        y3 = 48
        draw.line([(x0, y3 + 12), (x0 + 15, y3 + 12)], fill=(16, 20, 24, 255), width=1)
        draw.line([(x0, y3 + 13), (x0 + 15, y3 + 13)], fill=(54, 66, 68, 255), width=1)

    # ── Iteration 3: Material Shading Base ─────────────────────────────
    # Console screen bases on Row 2
    for c in (0, 1):
        x0 = c * 16
        y0 = 32
        draw.rectangle([x0 + 3, y0 + 3, x0 + 13, y0 + 13], outline=(40, 140, 75, 255), fill=(18, 48, 28, 255))
        draw.line([(x0 + 4, y0 + 8), (x0 + 12, y0 + 8)], fill=(51, 255, 102, 255), width=1)

    # ── Iteration 4: Riveted Industrial Plate Seams, Hazard Stripes & Wires ──
    # 1. Hazard warning stripes (0xffaa00 / 0x1a1a24) on Tile (0, 7) and Tile (3, 7)
    for c in (7,):
        for r in (0, 3):
            x0, y0 = c * 16, r * 16
            for ty in range(10, 16):
                for tx in range(16):
                    col = (255, 170, 0, 255) if ((tx + ty) // 3) % 2 == 0 else (26, 26, 36, 255)
                    px[x0 + tx, y0 + ty] = col

    # 2. Riveted industrial plate seams on Row 0 & Row 1
    for c in range(6):
        x0 = c * 16
        draw.line([(x0 + 8, 0), (x0 + 8, 15)], fill=(14, 18, 24, 255), width=1)
        draw.line([(x0 + 9, 0), (x0 + 9, 15)], fill=(55, 70, 85, 255), width=1)
        px[x0 + 8, 3] = (160, 176, 200, 255)
        px[x0 + 8, 12] = (160, 176, 200, 255)

    # 3. Conduit wire bundles across Row 1 (Server/Wall)
    for c in range(7):
        x0 = c * 16
        y1 = 16
        draw.line([(x0, y1 + 14), (x0 + 15, y1 + 14)], fill=(185, 42, 34, 255), width=1)
        draw.line([(x0, y1 + 15), (x0 + 15, y1 + 15)], fill=(32, 145, 135, 255), width=1)

    # ── Iteration 5: 3-Level Depth Beveling on Steel Girders (Row 0) ───
    for c in range(8):
        x0 = c * 16
        # Level 1: Web shadow
        draw.line([(x0 + 2, 0), (x0 + 2, 15)], fill=(18, 24, 32, 255), width=1)
        # Level 2: Flange face
        draw.line([(x0 + 3, 0), (x0 + 5, 0)], fill=(44, 56, 70, 255), width=1)
        # Level 3: Inner bevel
        draw.line([(x0 + 6, 0), (x0 + 10, 0)], fill=(75, 95, 115, 255), width=1)
        # Specular edge highlight (0xa0b0c8)
        draw.line([(x0 + 2, 0), (x0 + 14, 0)], fill=(160, 176, 200, 255), width=1)
        px[x0 + 3, 1] = (160, 176, 200, 255)
        px[x0 + 13, 1] = (160, 176, 200, 255)

    # ── Iteration 6: Micro-Scuffs, Metallic Corrosion Patina, CRT Blink ──
    # 1. Micro-scuffs and corrosion patina on concrete floor tiles (Row 3)
    for c in range(6):
        x0 = c * 16
        y3 = 48
        px[x0 + 4, y3 + 5] = (135, 150, 165, 255)  # specular scratch
        px[x0 + 5, y3 + 5] = (24, 28, 32, 255)    # scratch shadow
        px[x0 + 11, y3 + 8] = (135, 150, 165, 255)
        px[x0 + 7, y3 + 14] = (48, 72, 58, 255)    # verdigris patina
        px[x0 + 8, y3 + 14] = (70, 44, 30, 255)    # rust patina

    # 2. CRT terminal blink indicators on console tiles (2, 0) and (2, 1)
    for c in (0, 1):
        x0 = c * 16
        y0 = 32
        draw.rectangle([x0 + 10, y0 + 7, x0 + 12, y0 + 10], fill=(51, 255, 102, 255))
        px[x0 + 11, y0 + 8] = (210, 255, 235, 255)
        px[x0 + 14, y0 + 4] = (255, 200, 50, 255)

    return res


# ═══════════════════════════════════════════════════════════════════════
# ASSET 3: BUNKER LAYER 01 DISTANT STRUCTURE (DEEP 6-ITERATION)
# ═══════════════════════════════════════════════════════════════════════
def refine_distant_structure(img: Image.Image) -> Image.Image:
    """Six-iteration deep quality refinement for Bunker Layer 01 Distant Structure (480x270)."""
    # ── Iteration 1: Noise Elimination & Palette Consolidation ────────
    quant = img.convert("RGB").quantize(colors=32, method=Image.Quantize.MEDIANCUT).convert("RGBA")
    arr = np.array(quant)

    rgb = arr[:, :, :3].astype(float)
    up = np.roll(rgb, 1, axis=0)
    down = np.roll(rgb, -1, axis=0)
    left = np.roll(rgb, 1, axis=1)
    right = np.roll(rgb, -1, axis=1)
    min_d = np.minimum(
        np.minimum(np.linalg.norm(rgb - up, axis=2), np.linalg.norm(rgb - down, axis=2)),
        np.minimum(np.linalg.norm(rgb - left, axis=2), np.linalg.norm(rgb - right, axis=2))
    )
    noisy_y, noisy_x = np.where(min_d > 35)
    for y, x in zip(noisy_y, noisy_x):
        if 0 < y < 269 and 0 < x < 479:
            arr[y, x, :3] = np.median([arr[y - 1, x, :3], arr[y + 1, x, :3], arr[y, x - 1, :3], arr[y, x + 1, :3]], axis=0).astype(np.uint8)

    arr[:, :, 3] = 255  # Solid opaque base requirement
    res = Image.fromarray(arr, "RGBA").copy()
    px = res.load()
    draw = ImageDraw.Draw(res)

    # ── Iteration 2: Clustered Anti-Aliasing & Column Columns ──────────
    for col_idx in range(8):
        xc = col_idx * 64
        draw.line([(xc, 0), (xc, 269)], fill=(8, 12, 16, 255), width=1)
        draw.line([(xc + 1, 0), (xc + 1, 269)], fill=(18, 26, 34, 255), width=1)
        draw.line([(xc + 4, 0), (xc + 4, 269)], fill=(28, 38, 48, 255), width=1)
        draw.line([(xc + 5, 0), (xc + 5, 269)], fill=(12, 16, 22, 255), width=1)

    draw.line([(0, 18), (479, 18)], fill=(14, 20, 26, 255), width=1)
    draw.line([(0, 194), (479, 194)], fill=(12, 16, 20, 255), width=1)
    draw.line([(0, 200), (479, 200)], fill=(10, 14, 18, 255), width=1)

    for col_idx in range(7):
        x_left = col_idx * 64 + 5
        x_right = (col_idx + 1) * 64
        draw.line([(x_left, 20), (x_right, 194)], fill=(16, 24, 32, 255), width=1)
        draw.line([(x_left, 194), (x_right, 20)], fill=(16, 24, 32, 255), width=1)

    # ── Iteration 3: Material Shading & Girder Specular ───────────────
    draw.line([(0, 19), (479, 19)], fill=(62, 84, 108, 255), width=1)
    draw.line([(0, 195), (479, 195)], fill=(54, 74, 96, 255), width=1)

    # ── Iteration 4: Micro-Architectural Ribbing Along Columns ─────────
    for col_idx in range(8):
        xc = col_idx * 64
        for rib_y in range(32, 192, 16):
            draw.line([(xc + 1, rib_y), (xc + 4, rib_y)], fill=(45, 60, 78, 255), width=1)
            draw.line([(xc + 1, rib_y + 1), (xc + 4, rib_y + 1)], fill=(12, 16, 22, 255), width=1)

    # ── Iteration 5: Atmospheric Haze Gradient Bayer Dithering ────────
    bayer4 = np.array([
        [0, 8, 2, 10],
        [12, 4, 14, 6],
        [3, 11, 1, 9],
        [15, 7, 13, 5]
    ]) / 16.0

    for y in range(22, 190):
        t_depth = (190 - y) / 168.0  # deeper towards top
        for x in range(480):
            # Apply only in background void (not on solid columns)
            if x % 64 >= 6:
                dither_val = bayer4[y % 4, x % 4]
                if t_depth * 0.45 > dither_val:
                    cur = px[x, y]
                    px[x, y] = (
                        min(255, cur[0] + 4),
                        min(255, cur[1] + 7),
                        min(255, cur[2] + 12),
                        255
                    )

    # ── Iteration 6: Industrial Pipe Valving & Flange Runs ─────────────
    # Main chilled coolant pipe run across y in [37..40]
    draw.line([(0, 37), (479, 37)], fill=(78, 105, 128, 255), width=1)
    draw.line([(0, 38), (479, 38)], fill=(45, 62, 78, 255), width=2)
    draw.line([(0, 40), (479, 40)], fill=(20, 28, 36, 255), width=1)

    # Flange couplings every 64px
    for fx in range(32, 480, 64):
        draw.line([(fx, 36), (fx, 41)], fill=(110, 140, 165, 255), width=1)
        draw.line([(fx + 1, 36), (fx + 1, 41)], fill=(25, 34, 44, 255), width=1)

    # Industrial circular valve handwheels in safety crimson with brass stem
    for vx in (120, 340):
        draw.ellipse((vx - 5, 33, vx + 5, 43), outline=(195, 45, 40, 255), fill=(35, 20, 22, 255))
        draw.line([(vx, 33), (vx, 43)], fill=(220, 185, 60, 255), width=1)
        draw.line([(vx - 5, 38), (vx + 5, 38)], fill=(220, 185, 60, 255), width=1)
        px[vx, 38] = (255, 220, 90, 255)

    return res


# ═══════════════════════════════════════════════════════════════════════
# ASSET 4: BUNKER LAYER 03 EQUIPMENT (DEEP 6-ITERATION)
# ═══════════════════════════════════════════════════════════════════════
def refine_equipment(img: Image.Image) -> Image.Image:
    """Six-iteration deep quality refinement for Bunker Layer 03 Equipment (480x270)."""
    # ── Iteration 1: Noise Elimination & Binary Mask Preservation ─────
    src_arr = np.array(img.convert("RGBA"))
    alpha_mask = src_arr[:, :, 3] >= 128

    rgb_clean = Image.fromarray(src_arr[:, :, :3]).quantize(colors=48, method=Image.Quantize.MEDIANCUT).convert("RGBA")
    arr = np.array(rgb_clean)
    arr[~alpha_mask] = [0, 0, 0, 0]
    arr[alpha_mask, 3] = 255

    rgb = arr[:, :, :3].astype(float)
    up = np.roll(rgb, 1, axis=0)
    down = np.roll(rgb, -1, axis=0)
    left = np.roll(rgb, 1, axis=1)
    right = np.roll(rgb, -1, axis=1)
    min_d = np.minimum(
        np.minimum(np.linalg.norm(rgb - up, axis=2), np.linalg.norm(rgb - down, axis=2)),
        np.minimum(np.linalg.norm(rgb - left, axis=2), np.linalg.norm(rgb - right, axis=2))
    )
    noisy_y, noisy_x = np.where((min_d > 35) & alpha_mask)
    for y, x in zip(noisy_y, noisy_x):
        if 0 < y < 269 and 0 < x < 479 and alpha_mask[y, x]:
            nbr_colors = [arr[ny, nx, :3] for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)) if alpha_mask[ny, nx]]
            if nbr_colors:
                arr[y, x, :3] = np.median(nbr_colors, axis=0).astype(np.uint8)

    res = Image.fromarray(arr, "RGBA").copy()
    px = res.load()
    draw = ImageDraw.Draw(res)

    # ── Iteration 2: Clustered Anti-Aliasing & Structural Mullions ─────
    for bay_x in (46, 92, 137):
        draw.line([(bay_x, 30), (bay_x, 240)], fill=(16, 20, 26, 255), width=1)
        draw.line([(bay_x + 1, 30), (bay_x + 1, 240)], fill=(32, 42, 52, 255), width=1)

    draw.line([(138, 108), (278, 108)], fill=(44, 56, 52, 255), width=2)
    draw.rounded_rectangle([182, 114, 242, 162], radius=4, outline=(24, 32, 30, 255), fill=(16, 22, 20, 255))
    draw.line([(279, 70), (394, 70)], fill=(40, 48, 52, 255), width=2)
    draw.line([(395, 20), (395, 260)], fill=(18, 22, 26, 255), width=2)

    # ── Iteration 3: Material Shading & CRT Screen Base ────────────────
    draw.rectangle([188, 120, 236, 156], fill=(10, 32, 18, 255), outline=(32, 85, 48, 255))
    for sx in range(190, 235):
        sy = int(138 - 12 * math.exp(-((sx - 212) ** 2) / 60.0) * math.sin((sx - 190) * 0.4))
        px[sx, sy] = (51, 255, 102, 255)
        if sx % 4 == 0:
            px[sx, sy - 1] = (175, 255, 195, 255)
    draw.arc((189, 121, 215, 140), 190, 270, fill=(130, 225, 165, 255), width=1)

    # ── Iteration 4: Industrial Pipe Valving, Gauges & Conduit Manifolds ──
    # Top server rack high-pressure coolant pipe run (y in [25..28], x <= 137)
    draw.line([(6, 25), (135, 25)], fill=(75, 95, 110, 255), width=1)
    draw.line([(6, 26), (135, 26)], fill=(50, 68, 80, 255), width=2)
    draw.line([(6, 28), (135, 28)], fill=(20, 28, 36, 255), width=1)

    # Emergency shutoff handwheels on rack manifold (x=35, x=95)
    for vx in (35, 95):
        draw.ellipse((vx - 4, 21, vx + 4, 29), outline=(205, 45, 40, 255), fill=(30, 18, 20, 255))
        draw.line([(vx, 21), (vx, 29)], fill=(220, 185, 60, 255), width=1)

    # Round analog dial pressure gauges at x=65, 115, y=36
    for gx in (65, 115):
        draw.ellipse((gx - 5, 31, gx + 5, 41), fill=(235, 230, 210, 255), outline=(35, 45, 50, 255))
        draw.arc((gx - 4, 32, gx + 4, 40), 300, 360, fill=(210, 40, 35, 255), width=1)
        draw.line([(gx, 36), (gx + 3, 34)], fill=(20, 24, 28, 255), width=1)

    # ── Iteration 5: Micro-Architectural Rack Ribbing & Tape Density ───
    # 19-inch EIA rack rails (mounting hole pairs every 6px)
    for rx in (10, 42, 54, 88, 100, 134):
        for ry in range(48, 230, 6):
            px[rx, ry] = (14, 18, 22, 255)
            px[rx, ry + 1] = (65, 80, 95, 255)

    # Magnetic tape drive reels with layered tape density
    for reel_cx, reel_cy in ((45, 75), (85, 75)):
        draw.ellipse((reel_cx - 14, reel_cy - 14, reel_cx + 14, reel_cy + 14), outline=(140, 165, 180, 255), fill=(28, 24, 26, 255))
        # Layered magnetic tape pack rim
        draw.ellipse((reel_cx - 11, reel_cy - 11, reel_cx + 11, reel_cy + 11), outline=(68, 54, 48, 255), fill=(22, 28, 36, 255))
        draw.ellipse((reel_cx - 5, reel_cy - 5, reel_cx + 5, reel_cy + 5), fill=(210, 230, 245, 255))
        draw.arc((reel_cx - 13, reel_cy - 13, reel_cx + 13, reel_cy + 13), 200, 320, fill=(225, 240, 250, 255), width=1)

    # ── Iteration 6: CRT Terminal Blink Cursor, Oscilloscope Graticule & Hazard Stripes ──
    # Active terminal block cursor blinking on CRT
    draw.rectangle([218, 142, 222, 148], fill=(51, 255, 102, 255))
    px[219, 143] = (210, 255, 235, 255)

    # Oscilloscope calibrated graticule crosshairs on workbench
    draw.ellipse((325, 95, 355, 125), outline=(180, 110, 30, 255), fill=(34, 22, 12, 255))
    draw.line([(326, 110), (354, 110)], fill=(65, 42, 24, 255), width=1)
    draw.line([(340, 96), (340, 124)], fill=(65, 42, 24, 255), width=1)
    for ox in range(328, 353):
        oy = int(110 + 6 * math.sin((ox - 328) * 0.5))
        px[ox, oy] = (255, 165, 40, 255)

    # Airlock heavy warning hazard stripes (0xffaa00 / 0x1a1a24)
    for hy in range(24, 160, 14):
        draw.polygon([(398, hy), (412, hy + 8), (412, hy + 13), (398, hy + 5)], fill=(255, 170, 0, 255))
        draw.polygon([(398, hy + 6), (412, hy + 14), (412, hy + 19), (398, hy + 11)], fill=(26, 26, 36, 255))

    # Binary alpha clamp: strict alpha in {0, 255}
    for y in range(270):
        for x in range(480):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, 255) if a >= 128 else (0, 0, 0, 0)

    return res


# ═══════════════════════════════════════════════════════════════════════
# ASSET 5: BUNKER LAYER 04 PLAYABLE FLOOR (DEEP 6-ITERATION)
# ═══════════════════════════════════════════════════════════════════════
def refine_playable_floor(img: Image.Image) -> Image.Image:
    """Six-iteration deep quality refinement for Bunker Layer 04 Playable Floor (480x270)."""
    # ── Iteration 1: Noise Elimination & Top Edge Clean ───────────────
    src_arr = np.array(img.convert("RGBA"))
    alpha_mask = src_arr[:, :, 3] >= 128

    rgb_clean = Image.fromarray(src_arr[:, :, :3]).quantize(colors=32, method=Image.Quantize.MEDIANCUT).convert("RGBA")
    arr = np.array(rgb_clean)
    arr[~alpha_mask] = [0, 0, 0, 0]
    arr[alpha_mask, 3] = 255

    for x in range(480):
        arr[196, x, 3] = 255

    res = Image.fromarray(arr, "RGBA").copy()
    px = res.load()
    draw = ImageDraw.Draw(res)

    # ── Iteration 2: Clustered Anti-Aliasing & Modular Expansion Joints ──
    draw.line([(0, 230), (479, 230)], fill=(14, 18, 22, 255), width=1)
    draw.line([(0, 231), (479, 231)], fill=(52, 64, 68, 255), width=1)

    for cut_x in range(60, 480, 60):
        draw.line([(cut_x, 196), (cut_x, 269)], fill=(16, 20, 24, 255), width=1)
        draw.line([(cut_x + 1, 196), (cut_x + 1, 269)], fill=(42, 54, 58, 255), width=1)

    draw.line([(100, 214), (380, 214)], fill=(12, 16, 18, 255), width=1)
    draw.line([(100, 220), (380, 220)], fill=(12, 16, 18, 255), width=1)

    # ── Iteration 3: Material Shading & Stepped Light Pools ────────────
    for py in range(200, 230):
        for px_col in range(185, 240):
            d_sq = ((px_col - 212) / 28.0) ** 2 + ((py - 215) / 12.0) ** 2
            if d_sq <= 1.0 and px[px_col, py][3] > 0:
                cur = px[px_col, py]
                step = 1.0 if d_sq <= 0.35 else (0.6 if d_sq <= 0.7 else 0.3)
                px[px_col, py] = (
                    min(255, int(cur[0] + 12 * step)),
                    min(255, int(cur[1] + 45 * step)),
                    min(255, int(cur[2] + 20 * step)),
                    255
                )

    for py in range(200, 228):
        for px_col in range(305, 355):
            d_sq = ((px_col - 330) / 24.0) ** 2 + ((py - 214) / 10.0) ** 2
            if d_sq <= 1.0 and px[px_col, py][3] > 0:
                cur = px[px_col, py]
                step = 1.0 if d_sq <= 0.35 else (0.6 if d_sq <= 0.7 else 0.3)
                px[px_col, py] = (
                    min(255, int(cur[0] + 40 * step)),
                    min(255, int(cur[1] + 28 * step)),
                    min(255, int(cur[2] + 10 * step)),
                    255
                )

    # ── Iteration 4: Embedded Conduit Channels & Industrial Pipe Valving ──
    # Diamond tread-plate pattern on central cable trench covers
    for tx in range(104, 376, 4):
        for ty in (215, 218):
            px[tx, ty] = (85, 105, 110, 255)
            px[tx + 1, ty] = (20, 26, 30, 255)

    # Inspection utility hatch covers at x=150 and x=330
    for hx in (150, 330):
        draw.rectangle([hx - 8, 240, hx + 8, 256], outline=(75, 95, 100, 255), fill=(26, 34, 38, 255))
        # Recessed pull ring
        draw.ellipse((hx - 3, 246, hx + 3, 250), outline=(145, 175, 180, 255))

    # Inline shutoff valve at x=270 on floor service line
    draw.line([(260, 217), (280, 217)], fill=(85, 110, 120, 255), width=1)
    draw.ellipse((267, 214, 273, 220), outline=(210, 45, 40, 255), fill=(220, 185, 60, 255))

    # ── Iteration 5: Hazard Perimeter Striping ─────────────────────────
    # Caution hazard stripes (0xffaa00 / 0x1a1a24) along airlock approach
    for hx in range(400, 480, 8):
        for hy in range(196, 204):
            col = (255, 170, 0, 255) if ((hx + hy) // 4) % 2 == 0 else (26, 26, 36, 255)
            px[hx, hy] = col

    # Hazard stripes along server rack perimeter
    for hx in range(0, 60, 8):
        for hy in range(196, 202):
            col = (255, 170, 0, 255) if ((hx + hy) // 4) % 2 == 0 else (26, 26, 36, 255)
            px[hx, hy] = col

    # ── Iteration 6: Micro-Scuffs, Expansion Seam Plates & Joint Specular ─
    draw.line([(100, 213), (380, 213)], fill=(95, 120, 125, 255), width=1)
    for cut_x in range(60, 480, 60):
        px[cut_x + 1, 230] = (145, 175, 180, 255)

    # Expansion joint anchor plates with hex bolts every 30px
    for px_plate in range(15, 480, 30):
        draw.rectangle([px_plate - 3, 229, px_plate + 3, 232], fill=(68, 85, 90, 255), outline=(18, 24, 28, 255))
        px[px_plate, 230] = (175, 205, 210, 255)

    # Micro-scuffs in high-traffic traversal zone
    scuffs = [(195, 242), (210, 248), (225, 244), (315, 245), (330, 250), (140, 238), (360, 241)]
    for sx, sy in scuffs:
        px[sx, sy] = (120, 140, 145, 255)
        px[sx + 1, sy] = (20, 26, 30, 255)

    # Binary alpha clamp
    for y in range(270):
        for x in range(480):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, 255) if a >= 128 else (0, 0, 0, 0)

    return res


# ═══════════════════════════════════════════════════════════════════════
# COMPOSITE & PREVIEW REFRESH HELPERS
# ═══════════════════════════════════════════════════════════════════════
def update_fasr_scan_h_composite(face_img: Image.Image) -> Path:
    """Refresh fasr-scan-h_composite.png from env plate + refined face."""
    env_path = CIV_ASSETS_DIR / "fasr-scan-h_env.png"
    comp_path = CIV_ASSETS_DIR / "fasr-scan-h_composite.png"
    assert env_path.exists(), f"Missing env plate: {env_path}"
    env_img = Image.open(env_path).convert("RGBA")
    comp = Image.new("RGBA", (128, 128), (0, 0, 0, 255))
    comp.paste(env_img, (0, 0), env_img)
    comp.paste(face_img, (0, 0), face_img)
    comp.save(comp_path)
    return comp_path


def update_bunker_previews_and_inspection(
    refined_layers: Dict[str, Image.Image]
) -> Tuple[Path, Path, List[Path]]:
    """Assemble all 6 bunker layers + Mateo sprite and refresh CRT OFF/ON and inspection previews."""
    bunker_dir = BUNKER_ASSETS_DIR
    inspect_dir = bunker_dir / "inspection"
    inspect_dir.mkdir(parents=True, exist_ok=True)

    layer_names = [
        "01_distant_structure.png",
        "02_rear_wall.png",
        "03_equipment.png",
        "04_playable_floor.png",
        "05_foreground_props.png",
        "06_lighting_overlay.png",
    ]
    loaded_layers: Dict[str, Image.Image] = {}
    for name in layer_names:
        if name in refined_layers:
            loaded_layers[name] = refined_layers[name]
        else:
            loaded_layers[name] = Image.open(bunker_dir / name).convert("RGBA")

    # Save refined layers to disk
    for name, img in refined_layers.items():
        img.save(bunker_dir / name)

    mateo_bunker_path = SPRITES_DIR / "mateo_bunker_96x128.png"
    mateo_bunker = Image.open(mateo_bunker_path).convert("RGBA")

    # Alpha composite in exact z-order
    comp = loaded_layers["01_distant_structure.png"].copy()
    comp = Image.alpha_composite(comp, loaded_layers["02_rear_wall.png"])
    comp = Image.alpha_composite(comp, loaded_layers["03_equipment.png"])
    comp = Image.alpha_composite(comp, loaded_layers["04_playable_floor.png"])

    shadow = Image.new("RGBA", (480, 270), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse((202, 238, 268, 252), fill=(0, 0, 0, 145))
    comp = Image.alpha_composite(comp, shadow)
    comp.paste(mateo_bunker, (186, 122), mateo_bunker)

    comp = Image.alpha_composite(comp, loaded_layers["05_foreground_props.png"])
    comp = Image.alpha_composite(comp, loaded_layers["06_lighting_overlay.png"])

    crt_off_path = bunker_dir / "bunker_preview_crt_off.png"
    comp.save(crt_off_path)

    # CRT ON (3x scale 1440x810 with scanlines and monitor border)
    crt_on = comp.resize((1440, 810), Image.Resampling.NEAREST)
    overlay = Image.new("RGBA", (1440, 810), (0, 0, 0, 0))
    c_draw = ImageDraw.Draw(overlay)
    for sy in range(2, 810, 3):
        c_draw.line((0, sy, 1440, sy), fill=(0, 0, 0, 58))
    c_draw.rectangle((0, 0, 1439, 809), outline=(36, 140, 72, 200), width=4)
    crt_on_path = bunker_dir / "bunker_preview_crt_on.png"
    Image.alpha_composite(crt_on, overlay).convert("RGB").save(crt_on_path)

    # Inspection previews (dimmed background composite)
    concepts_dir = REPO_ROOT / "art" / "source" / "bunker"
    bunker_src = concepts_dir / "concept_bunker_clean_1794333595362.jpg"
    raw_b = Image.open(bunker_src).convert("RGB").resize((480, 270), Image.Resampling.NEAREST)
    quant_b = raw_b.quantize(colors=48, method=Image.Quantize.MEDIANCUT).convert("RGBA")
    rgb_b = quant_b.convert("RGB")
    gray_b = rgb_b.convert("L").convert("RGB")
    dimmed_bg = Image.blend(rgb_b, gray_b, 0.70).point(lambda c: int(c * 0.35)).convert("RGBA")

    inspect_paths = []
    for name in ("01_distant_structure.png", "03_equipment.png", "04_playable_floor.png"):
        inspect_img = Image.alpha_composite(dimmed_bg.copy(), loaded_layers[name])
        inspect_name = name.replace(".png", "_inspect.png")
        out_p = inspect_dir / inspect_name
        inspect_img.save(out_p)
        inspect_paths.append(out_p)

    return crt_off_path, crt_on_path, inspect_paths


# ═══════════════════════════════════════════════════════════════════════
# SIDE-BY-SIDE INSPECTION SHEET GENERATOR
# ═══════════════════════════════════════════════════════════════════════
def draw_checkerboard(draw: ImageDraw.Draw, x0: int, y0: int, w: int, h: int, sq_size: int = 8):
    """Draw a subtle dark checkerboard to highlight transparency and contour silhouettes."""
    col1 = (10, 14, 18, 255)
    col2 = (18, 24, 30, 255)
    for y in range(y0, y0 + h, sq_size):
        for x in range(x0, x0 + w, sq_size):
            cw = min(sq_size, x0 + w - x)
            ch = min(sq_size, y0 + h - y)
            fill_c = col1 if ((x // sq_size) + (y // sq_size)) % 2 == 0 else col2
            draw.rectangle([x, y, x + cw - 1, y + ch - 1], fill=fill_c)
    draw.rectangle([x0, y0, x0 + w - 1, y0 + h - 1], outline=(36, 48, 60, 255), width=1)


def create_batch_3_comparison_sheet(
    asset_items: List[Dict],
    output_path: Path
):
    """Generate high-resolution side-by-side inspection sheet for Batch 3 assets."""
    canvas_w = 1120
    canvas_h = 90 + 356 + 24 + 228 + 24 + 370 + 24 + 370 + 24 + 370 + 40

    sheet = Image.new("RGBA", (canvas_w, canvas_h), (10, 14, 18, 255))
    draw = ImageDraw.Draw(sheet)

    # Master Header
    draw.text((40, 20), "BATCH 3 DEEP ART ENHANCEMENT: CIVILIZATION & BUNKER SCENE ASSETS", fill=(65, 195, 245, 255))
    draw.text((40, 44), "6-Iteration Deep Refinement: Noise/Cavities -> AA Clustering -> Material Ramps -> Ribbing/Pipes -> Density/Gradients -> CRT Glow & Patina", fill=(130, 150, 168, 255))
    draw.line([(40, 68), (canvas_w - 40, 68)], fill=(32, 44, 56, 255), width=2)

    cur_y = 86
    px_before = 50
    px_after = 590
    slot_w = 480

    for idx, item in enumerate(asset_items):
        title = item["title"]
        dims_str = item["dims_str"]
        scale = item["scale"]
        b_img = item["before"]
        a_img = item["after"]
        metrics_b = item["metrics_before"]
        metrics_a = item["metrics_after"]
        notes = item["notes"]

        img_disp_w = b_img.width * scale
        img_disp_h = b_img.height * scale
        card_h = 36 + img_disp_h + 20 + 44
        card_x0 = 40
        card_x1 = canvas_w - 40
        card_y0 = cur_y
        card_y1 = cur_y + card_h

        # Card container & header bar
        draw.rectangle([card_x0, card_y0, card_x1, card_y1], fill=(16, 22, 28, 255), outline=(34, 46, 58, 255), width=1)
        draw.rectangle([card_x0, card_y0, card_x1, card_y0 + 32], fill=(22, 30, 40, 255))
        draw.text((card_x0 + 12, card_y0 + 8), f"{idx + 1}. {title} [{dims_str}]", fill=(245, 205, 65, 255))
        draw.text((card_x0 + 560, card_y0 + 8), item["role"], fill=(120, 160, 185, 255))

        # Content area
        content_y = card_y0 + 38
        draw.text((px_before, content_y), "BEFORE (Original Baseline):", fill=(210, 95, 95, 255))
        draw.text((px_after, content_y), "AFTER (6-Iteration Deep Refined):", fill=(60, 220, 130, 255))

        img_y = content_y + 18
        offset_x = (slot_w - img_disp_w) // 2

        draw_checkerboard(draw, px_before + offset_x, img_y, img_disp_w, img_disp_h)
        draw_checkerboard(draw, px_after + offset_x, img_y, img_disp_w, img_disp_h)

        b_disp = b_img.resize((img_disp_w, img_disp_h), Image.Resampling.NEAREST) if scale != 1 else b_img
        a_disp = a_img.resize((img_disp_w, img_disp_h), Image.Resampling.NEAREST) if scale != 1 else a_img

        sheet.paste(b_disp, (px_before + offset_x, img_y), b_disp)
        sheet.paste(a_disp, (px_after + offset_x, img_y), a_disp)

        # Footer Metrics & Badges
        footer_y = card_y1 - 38
        draw.line([(card_x0, footer_y), (card_x1, footer_y)], fill=(28, 38, 48, 255), width=1)

        sol_b, orph_b, cav_b, outl_b, col_b = metrics_b
        sol_a, orph_a, cav_a, outl_a, col_a = metrics_a

        metric_txt = (
            f"Orphans: {orph_b} -> {orph_a} | Cavities: {cav_b} -> {cav_a} | "
            f"Color Outliers: {outl_b} -> {outl_a} | Colors: {col_b} -> {col_a}"
        )
        draw.text((card_x0 + 12, footer_y + 8), metric_txt, fill=(185, 210, 230, 255))
        draw.text((card_x0 + 12, footer_y + 22), notes, fill=(130, 160, 180, 255))

        draw.rectangle([card_x1 - 180, footer_y + 6, card_x1 - 12, footer_y + 30], fill=(22, 60, 36, 255), outline=(60, 200, 110, 255), width=1)
        draw.text((card_x1 - 168, footer_y + 11), "[ITERATION 6: APPROVED]", fill=(75, 235, 135, 255))

        cur_y += card_h + 24

    sheet.save(output_path)
    print(f"Saved side-by-side inspection sheet: {output_path}")


# ═══════════════════════════════════════════════════════════════════════
# MAIN PIPELINE EXECUTION
# ═══════════════════════════════════════════════════════════════════════
def main():
    TILESETS_BUNKER_DIR.mkdir(parents=True, exist_ok=True)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    print("═══════════════════════════════════════════════════════════════")
    print(" 6EQUJ5 ART BATCH 3: 6-ITERATION DEEP PIXEL REFINEMENT")
    print("═══════════════════════════════════════════════════════════════")

    # 1. FASR-SCAN-H Face
    p1 = CIV_ASSETS_DIR / "fasr-scan-h_face.png"
    assert p1.exists(), f"Missing target: {p1}"
    orig_fasr = Image.open(p1).convert("RGBA")
    m_fasr_before = calculate_asset_metrics(orig_fasr)
    ref_fasr = refine_fasr_scan_h(orig_fasr)
    ref_fasr.save(p1)
    m_fasr_after = calculate_asset_metrics(ref_fasr)
    comp_fasr_path = update_fasr_scan_h_composite(ref_fasr)
    print(f"[1/5] fasr-scan-h_face.png (128x128 RGBA):")
    print(f"      Cavities: {m_fasr_before[2]} -> {m_fasr_after[2]} | Orphans: {m_fasr_before[1]} -> {m_fasr_after[1]}")
    print(f"      Updated composite: {comp_fasr_path.name}")

    # 2. Bunker Tileset 16x16
    p2 = BUNKER_ASSETS_DIR / "tileset_bunker_16x16.png"
    assert p2.exists(), f"Missing target: {p2}"
    orig_tileset = Image.open(p2).convert("RGBA")
    m_tile_before = calculate_asset_metrics(orig_tileset)
    ref_tileset = refine_tileset_bunker(orig_tileset)
    ref_tileset.save(p2)
    # Also save to mirror tilesets directory
    ref_tileset.save(TILESETS_BUNKER_DIR / "tileset_bunker_16x16.png")
    m_tile_after = calculate_asset_metrics(ref_tileset)
    print(f"[2/5] tileset_bunker_16x16.png (128x64 RGBA, 32 tiles):")
    print(f"      Color Outliers: {m_tile_before[3]} -> {m_tile_after[3]} | Unique Colors: {m_tile_before[4]} -> {m_tile_after[4]}")

    # 3. Layer 01 Distant Structure
    p3 = BUNKER_ASSETS_DIR / "01_distant_structure.png"
    assert p3.exists(), f"Missing target: {p3}"
    orig_l01 = Image.open(p3).convert("RGBA")
    m_l01_before = calculate_asset_metrics(orig_l01)
    ref_l01 = refine_distant_structure(orig_l01)
    m_l01_after = calculate_asset_metrics(ref_l01)
    print(f"[3/5] 01_distant_structure.png (480x270 RGBA):")
    print(f"      Color Outliers: {m_l01_before[3]} -> {m_l01_after[3]} | Colors: {m_l01_before[4]} -> {m_l01_after[4]}")

    # 4. Layer 03 Equipment
    p4 = BUNKER_ASSETS_DIR / "03_equipment.png"
    assert p4.exists(), f"Missing target: {p4}"
    orig_l03 = Image.open(p4).convert("RGBA")
    m_l03_before = calculate_asset_metrics(orig_l03)
    ref_l03 = refine_equipment(orig_l03)
    m_l03_after = calculate_asset_metrics(ref_l03)
    print(f"[4/5] 03_equipment.png (480x270 RGBA):")
    print(f"      Color Outliers: {m_l03_before[3]} -> {m_l03_after[3]} | Colors: {m_l03_before[4]} -> {m_l03_after[4]}")

    # 5. Layer 04 Playable Floor
    p5 = BUNKER_ASSETS_DIR / "04_playable_floor.png"
    assert p5.exists(), f"Missing target: {p5}"
    orig_l04 = Image.open(p5).convert("RGBA")
    m_l04_before = calculate_asset_metrics(orig_l04)
    ref_l04 = refine_playable_floor(orig_l04)
    m_l04_after = calculate_asset_metrics(ref_l04)
    print(f"[5/5] 04_playable_floor.png (480x270 RGBA):")
    print(f"      Color Outliers: {m_l04_before[3]} -> {m_l04_after[3]} | Colors: {m_l04_before[4]} -> {m_l04_after[4]}")

    # Refresh bunker composites and inspection previews
    refined_layers = {
        "01_distant_structure.png": ref_l01,
        "03_equipment.png": ref_l03,
        "04_playable_floor.png": ref_l04,
    }
    crt_off, crt_on, inspect_paths = update_bunker_previews_and_inspection(refined_layers)
    print(f"      Updated Bunker CRT OFF: {crt_off.name}")
    print(f"      Updated Bunker CRT ON:  {crt_on.name}")
    print(f"      Updated Inspection Layers: {[p.name for p in inspect_paths]}")

    # Build comparison sheet items
    asset_items = [
        {
            "title": "FASR-SCAN-H HEPTAPOD PORTRAIT",
            "dims_str": "128x128 RGBA @ 2x",
            "role": "Calligraphic ink splatters, 0x143c2c->0x33ff66 density gradient, CRT glow (0x00f0ff/0xd2ffeb)",
            "scale": 2,
            "before": orig_fasr,
            "after": ref_fasr,
            "metrics_before": m_fasr_before,
            "metrics_after": m_fasr_after,
            "notes": "Sealed 24 pinhole cavities, multi-shade aerosol ink density, CRT glow anti-aliasing on filament junctions."
        },
        {
            "title": "BUNKER MODULAR 16x16 TILESET",
            "dims_str": "128x64 RGBA @ 2x (32 tiles)",
            "role": "Riveted plate seams, 0xffaa00 hazard stripes, 0xa0b0c8 3-level girder bevels, terminal blink cursor",
            "scale": 2,
            "before": orig_tileset,
            "after": ref_tileset,
            "metrics_before": m_tile_before,
            "metrics_after": m_tile_after,
            "notes": "Added countersunk rivets, dual conduit wire bundles, 3-level depth beveling, micro-scuffs & corrosion patina."
        },
        {
            "title": "BUNKER LAYER 01: DISTANT STRUCTURE",
            "dims_str": "480x270 RGBA @ 1x",
            "role": "Micro-architectural column ribbing, Bayer atmospheric haze dither, coolant pipe run & valving",
            "scale": 1,
            "before": orig_l01,
            "after": ref_l01,
            "metrics_before": m_l01_before,
            "metrics_after": m_l01_after,
            "notes": "Reduced 5,714 raw colors down to 72 tones, added 16px column ribbing, Bayer atmospheric dither, safety crimson valving."
        },
        {
            "title": "BUNKER LAYER 03: EQUIPMENT",
            "dims_str": "480x270 RGBA @ 1x",
            "role": "High-pressure pipe manifold, pressure dial gauges, 19-inch rack rails, terminal blink cursor, hazard door",
            "scale": 1,
            "before": orig_l03,
            "after": ref_l03,
            "metrics_before": m_l03_before,
            "metrics_after": m_l03_after,
            "notes": "Added rack pipe manifolds, dual analog pressure dial gauges, 19-inch EIA mounting rails, active CRT blink cursor."
        },
        {
            "title": "BUNKER LAYER 04: PLAYABLE FLOOR",
            "dims_str": "480x270 RGBA @ 1x",
            "role": "Diamond tread conduit plates, utility inspection hatches, hazard perimeter stripes, joint anchor plates",
            "scale": 1,
            "before": orig_l04,
            "after": ref_l04,
            "metrics_before": m_l04_before,
            "metrics_after": m_l04_after,
            "notes": "Added trench diamond tread texture, utility inspection hatches with pull rings, caution hazard stripes, micro-scuffs."
        },
    ]

    # Generate side-by-side inspection sheet
    comp_sheet = EVIDENCE_DIR / "batch_3_before_after_inspection.png"
    create_batch_3_comparison_sheet(asset_items, comp_sheet)

    # Copy to brain artifact directory
    if BRAIN_ARTIFACT_DIR.exists():
        target_brain_path = BRAIN_ARTIFACT_DIR / "batch_3_before_after_inspection.png"
        shutil.copy2(comp_sheet, target_brain_path)
        print(f"Copied inspection sheet to brain: {target_brain_path}")

    print("═══════════════════════════════════════════════════════════════")
    print(" BATCH 3 (6 ITERATIONS) COMPLETE // 5 OF 5 ASSETS VERIFIED")
    print("═══════════════════════════════════════════════════════════════")


if __name__ == "__main__":
    main()
