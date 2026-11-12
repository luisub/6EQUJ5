"""
# PURPOSE: Build Act I Ohio environment pixel art assets (tileset, parallax backgrounds, weather).
# CALLED BY: Standalone execution (`python -m video_game.tools.ohio_environment_builder`) or release builder.
# HOW TO MODIFY: Adjust palette ramps, tile coordinate drawings, or parallax layer composition.
"""

import hashlib
import json
import math
from pathlib import Path
from typing import Dict, List, Tuple
from PIL import Image, ImageDraw

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ASSETS_DIR = REPO_ROOT / "video_game" / "assets"
ENV_DIR = ASSETS_DIR / "environments" / "ohio"
SOURCE_DIR = REPO_ROOT / "video_game" / "art" / "source" / "environments" / "ohio"


def ensure_directories():
    ENV_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)


def build_ohio_tileset() -> Image.Image:
    """
    Build 256x128 16x16 modular pixel art tileset for Act I Ohio environments.
    16 columns x 8 rows of 16x16 tiles.
    """
    img = Image.new("RGBA", (256, 128), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Palette definitions from materials.json
    C_CONC_DARK = (16, 22, 28, 255)
    C_CONC_MID = (32, 42, 48, 255)
    C_CONC_LIGHT = (58, 72, 78, 255)
    C_CONC_HILITE = (94, 112, 118, 255)

    C_MUD_DARK = (28, 34, 18, 255)
    C_MUD_MID = (46, 54, 28, 255)
    C_GRASS_MID = (72, 84, 43, 255)
    C_GRASS_LIGHT = (104, 118, 63, 255)

    C_STEEL_DARK = (22, 32, 44, 255)
    C_STEEL_MID = (40, 56, 74, 255)
    C_STEEL_LIGHT = (66, 90, 114, 255)
    C_STEEL_HILITE = (104, 134, 162, 255)

    C_RUST_DARK = (52, 24, 16, 255)
    C_RUST_MID = (94, 44, 28, 255)
    C_RUST_LIGHT = (140, 66, 42, 255)
    C_RUST_HILITE = (190, 100, 66, 255)

    C_HAZ_BG = (24, 8, 6, 255)
    C_HAZ_LIQ = (68, 20, 16, 255)
    C_HAZ_SPARK = (216, 66, 36, 255)
    C_HAZ_HILITE = (255, 222, 128, 255)

    C_BAG_DARK = (38, 32, 20, 255)
    C_BAG_MID = (66, 56, 36, 255)
    C_BAG_LIGHT = (102, 88, 58, 255)
    C_BAG_HILITE = (148, 130, 86, 255)

    C_CRT_GREEN = (51, 255, 102, 255)
    C_AMBER = (255, 158, 44, 255)

    def tile_rect(col, row):
        return col * 16, row * 16, col * 16 + 15, row * 16 + 15

    # -------------------------------------------------------------
    # ROW 0: SOLID CONCRETE FOUNDATIONS & WALLS
    # -------------------------------------------------------------
    # Col 0: Solid interior concrete fill
    x0, y0, x1, y1 = tile_rect(0, 0)
    draw.rectangle([x0, y0, x1, y1], fill=C_CONC_MID)
    draw.line([x0 + 3, y0 + 3, x1 - 3, y1 - 3], fill=C_CONC_DARK)
    draw.point([x0 + 5, y0 + 12], fill=C_CONC_LIGHT)
    draw.point([x0 + 11, y0 + 4], fill=C_CONC_LIGHT)

    # Col 1: Concrete top edge with bevel
    x0, y0, x1, y1 = tile_rect(1, 0)
    draw.rectangle([x0, y0, x1, y1], fill=C_CONC_MID)
    draw.line([x0, y0, x1, y0], fill=C_CONC_HILITE)
    draw.line([x0, y0 + 1, x1, y0 + 1], fill=C_CONC_LIGHT)
    draw.line([x0 + 2, y1, x1 - 2, y1], fill=C_CONC_DARK)

    # Col 2: Concrete left wall edge
    x0, y0, x1, y1 = tile_rect(2, 0)
    draw.rectangle([x0, y0, x1, y1], fill=C_CONC_MID)
    draw.line([x0, y0, x0, y1], fill=C_CONC_HILITE)
    draw.line([x0 + 1, y0, x0 + 1, y1], fill=C_CONC_LIGHT)

    # Col 3: Concrete right wall edge
    x0, y0, x1, y1 = tile_rect(3, 0)
    draw.rectangle([x0, y0, x1, y1], fill=C_CONC_MID)
    draw.line([x1, y0, x1, y1], fill=C_CONC_DARK)
    draw.line([x1 - 1, y0, x1 - 1, y1], fill=C_CONC_DARK)

    # Col 4: Top-left corner
    x0, y0, x1, y1 = tile_rect(4, 0)
    draw.rectangle([x0, y0, x1, y1], fill=C_CONC_MID)
    draw.line([x0, y0, x1, y0], fill=C_CONC_HILITE)
    draw.line([x0, y0, x0, y1], fill=C_CONC_HILITE)

    # Col 5: Top-right corner
    x0, y0, x1, y1 = tile_rect(5, 0)
    draw.rectangle([x0, y0, x1, y1], fill=C_CONC_MID)
    draw.line([x0, y0, x1, y0], fill=C_CONC_HILITE)
    draw.line([x1, y0, x1, y1], fill=C_CONC_DARK)

    # Col 6: Cracked concrete with exposed rebar
    x0, y0, x1, y1 = tile_rect(6, 0)
    draw.rectangle([x0, y0, x1, y1], fill=C_CONC_MID)
    draw.line([x0 + 4, y0 + 2, x0 + 7, y0 + 8], fill=C_CONC_DARK)
    draw.line([x0 + 7, y0 + 8, x0 + 12, y0 + 14], fill=C_CONC_DARK)
    draw.line([x0 + 5, y0 + 6, x0 + 9, y0 + 6], fill=C_RUST_LIGHT)  # exposed rebar

    # Col 7: Concrete drainage channel block
    x0, y0, x1, y1 = tile_rect(7, 0)
    draw.rectangle([x0, y0, x1, y1], fill=C_CONC_MID)
    draw.rectangle([x0 + 4, y0 + 4, x1 - 4, y1], fill=C_CONC_DARK)
    draw.line([x0 + 4, y0 + 4, x1 - 4, y0 + 4], fill=(8, 12, 16, 255))

    # -------------------------------------------------------------
    # ROW 1: SOLID TERRAIN & MUDDY SOIL
    # -------------------------------------------------------------
    # Col 0: Mud interior
    x0, y0, x1, y1 = tile_rect(0, 1)
    draw.rectangle([x0, y0, x1, y1], fill=C_MUD_MID)
    draw.point([x0 + 4, y0 + 5], fill=C_MUD_DARK)
    draw.point([x0 + 10, y0 + 11], fill=C_MUD_DARK)

    # Col 1: Autumn grass sod top edge
    x0, y0, x1, y1 = tile_rect(1, 1)
    draw.rectangle([x0, y0, x1, y1], fill=C_MUD_MID)
    draw.line([x0, y0, x1, y0], fill=C_GRASS_LIGHT)
    draw.line([x0, y0 + 1, x1, y0 + 1], fill=C_GRASS_MID)
    # Grass tufts
    for gx in range(x0 + 1, x1, 3):
        draw.line([gx, y0, gx, y0 + 3], fill=C_GRASS_LIGHT)

    # Col 2: Rocky soil with embedded stone
    x0, y0, x1, y1 = tile_rect(2, 1)
    draw.rectangle([x0, y0, x1, y1], fill=C_MUD_MID)
    draw.ellipse([x0 + 4, y0 + 6, x0 + 11, y0 + 11], fill=C_CONC_LIGHT, outline=C_CONC_DARK)

    # Col 3: Excavated mud trench wall
    x0, y0, x1, y1 = tile_rect(3, 1)
    draw.rectangle([x0, y0, x1, y1], fill=C_MUD_MID)
    draw.line([x0, y0, x0, y1], fill=C_MUD_DARK)
    draw.line([x0 + 1, y0, x0 + 1, y1], fill=C_MUD_DARK)

    # -------------------------------------------------------------
    # ROW 2: ONE_WAY CATWALK STEEL GRATING
    # -------------------------------------------------------------
    # Col 0: Catwalk steel grating (top 4px solid surface + brackets)
    x0, y0, x1, y1 = tile_rect(0, 2)
    # Top solid tread plate
    draw.line([x0, y0, x1, y0], fill=C_STEEL_HILITE)
    draw.line([x0, y0 + 1, x1, y0 + 1], fill=C_STEEL_LIGHT)
    draw.rectangle([x0, y0 + 2, x1, y0 + 4], fill=C_STEEL_DARK)
    # Grating vertical slats
    for gx in range(x0 + 1, x1, 3):
        draw.line([gx, y0 + 1, gx, y0 + 4], fill=C_STEEL_MID)
    # Under-truss bracket
    draw.line([x0 + 2, y0 + 5, x0 + 6, y0 + 10], fill=C_STEEL_MID)
    draw.line([x1 - 2, y0 + 5, x1 - 6, y0 + 10], fill=C_STEEL_MID)

    # Col 1: Catwalk left edge with stanchion
    x0, y0, x1, y1 = tile_rect(1, 2)
    draw.line([x0 + 2, y0, x1, y0], fill=C_STEEL_HILITE)
    draw.line([x0 + 2, y0 + 1, x1, y0 + 1], fill=C_STEEL_LIGHT)
    draw.rectangle([x0 + 2, y0 + 2, x1, y0 + 4], fill=C_STEEL_DARK)
    draw.line([x0 + 2, y0, x0 + 2, y1], fill=C_STEEL_LIGHT)
    draw.line([x0 + 3, y0, x0 + 3, y1], fill=C_STEEL_MID)

    # Col 2: Catwalk right edge with stanchion
    x0, y0, x1, y1 = tile_rect(2, 2)
    draw.line([x0, y0, x1 - 2, y0], fill=C_STEEL_HILITE)
    draw.line([x0, y0 + 1, x1 - 2, y0 + 1], fill=C_STEEL_LIGHT)
    draw.rectangle([x0, y0 + 2, x1 - 2, y0 + 4], fill=C_STEEL_DARK)
    draw.line([x1 - 2, y0, x1 - 2, y1], fill=C_STEEL_LIGHT)
    draw.line([x1 - 3, y0, x1 - 3, y1], fill=C_STEEL_MID)

    # Col 3: Catwalk cross-truss support
    x0, y0, x1, y1 = tile_rect(3, 2)
    draw.line([x0, y0, x1, y1], fill=C_STEEL_DARK)
    draw.line([x0, y1, x1, y0], fill=C_STEEL_DARK)
    draw.line([x0, y0, x1, y0], fill=C_STEEL_MID)
    draw.line([x0, y1, x1, y1], fill=C_STEEL_MID)

    # -------------------------------------------------------------
    # ROW 3: ONE_WAY / SOLID SCRAP YARD METAL
    # -------------------------------------------------------------
    # Col 0: Corrugated scrap metal sheet (one-way walkway)
    x0, y0, x1, y1 = tile_rect(0, 3)
    draw.line([x0, y0, x1, y0], fill=C_RUST_HILITE)
    draw.line([x0, y0 + 1, x1, y0 + 1], fill=C_RUST_LIGHT)
    draw.rectangle([x0, y0 + 2, x1, y0 + 5], fill=C_RUST_MID)
    # Corrugation ribs
    for rx in range(x0, x1, 4):
        draw.line([rx, y0, rx, y0 + 5], fill=C_RUST_HILITE)
        draw.line([rx + 2, y0, rx + 2, y0 + 5], fill=C_RUST_DARK)

    # Col 1: Solid riveted scrap iron wall
    x0, y0, x1, y1 = tile_rect(1, 3)
    draw.rectangle([x0, y0, x1, y1], fill=C_RUST_MID)
    draw.rectangle([x0, y0, x1, y1], outline=C_RUST_DARK)
    # Corner rivets
    for rx, ry in [(x0 + 2, y0 + 2), (x1 - 2, y0 + 2), (x0 + 2, y1 - 2), (x1 - 2, y1 - 2)]:
        draw.point([rx, ry], fill=C_RUST_HILITE)

    # -------------------------------------------------------------
    # ROW 4: HAZARD ELECTRICAL SUMP
    # -------------------------------------------------------------
    # Col 0: Sump pit liquid surface with conductive ripple
    x0, y0, x1, y1 = tile_rect(0, 4)
    # Sump fluid fills from y+6 to bottom
    draw.rectangle([x0, y0 + 6, x1, y1], fill=C_HAZ_LIQ)
    draw.line([x0, y0 + 6, x1, y0 + 6], fill=C_HAZ_SPARK)
    # Liquid wave ripples
    draw.line([x0 + 2, y0 + 9, x0 + 6, y0 + 9], fill=C_HAZ_HILITE)
    draw.line([x0 + 9, y0 + 11, x0 + 14, y0 + 11], fill=C_HAZ_HILITE)

    # Col 1: Sump deep liquid fill
    x0, y0, x1, y1 = tile_rect(1, 4)
    draw.rectangle([x0, y0, x1, y1], fill=C_HAZ_LIQ)
    draw.line([x0 + 4, y0 + 5, x0 + 12, y0 + 5], fill=C_HAZ_SPARK)
    draw.line([x0 + 2, y0 + 12, x0 + 8, y0 + 12], fill=C_HAZ_BG)

    # Col 2: Spark arc overlay
    x0, y0, x1, y1 = tile_rect(2, 4)
    draw.rectangle([x0, y0 + 6, x1, y1], fill=C_HAZ_LIQ)
    # Jagged electrical spark
    draw.line([x0 + 2, y0 + 8, x0 + 6, y0 + 4], fill=C_HAZ_HILITE)
    draw.line([x0 + 6, y0 + 4, x0 + 9, y0 + 9], fill=C_HAZ_HILITE)
    draw.line([x0 + 9, y0 + 9, x0 + 14, y0 + 3], fill=C_HAZ_HILITE)

    # -------------------------------------------------------------
    # ROW 5: COVER SANDBAGS & CRATES (LOW BARRIERS)
    # -------------------------------------------------------------
    # Col 0: Sandbag low cover block (16x10 low barrier, top at y+6)
    x0, y0, x1, y1 = tile_rect(0, 5)
    # Sandbag stack from y+6 to y1
    draw.rectangle([x0 + 1, y0 + 6, x1 - 1, y1], fill=C_BAG_MID)
    draw.rectangle([x0 + 1, y0 + 6, x1 - 1, y1], outline=C_BAG_DARK)
    # Individual bag contours
    draw.line([x0 + 2, y0 + 6, x1 - 2, y0 + 6], fill=C_BAG_HILITE)
    draw.line([x0 + 1, y0 + 10, x1 - 1, y0 + 10], fill=C_BAG_DARK)
    draw.line([x0 + 2, y0 + 11, x1 - 2, y0 + 11], fill=C_BAG_LIGHT)

    # Col 1: Military equipment crate (16x12 low cover crate)
    x0, y0, x1, y1 = tile_rect(1, 5)
    draw.rectangle([x0 + 1, y0 + 4, x1 - 1, y1], fill=C_MUD_DARK)
    draw.rectangle([x0 + 1, y0 + 4, x1 - 1, y1], outline=C_MUD_MID)
    draw.line([x0 + 2, y0 + 4, x1 - 2, y0 + 4], fill=C_GRASS_LIGHT)
    # Cross brace stencil
    draw.line([x0 + 3, y0 + 6, x1 - 3, y1 - 2], fill=C_MUD_MID)
    draw.line([x0 + 3, y1 - 2, x1 - 3, y0 + 6], fill=C_MUD_MID)

    # -------------------------------------------------------------
    # ROW 6: PROPS & STENCILS
    # -------------------------------------------------------------
    # Col 0: Parts cache / analog coupler box
    x0, y0, x1, y1 = tile_rect(0, 6)
    draw.rectangle([x0 + 2, y0 + 4, x1 - 2, y1 - 2], fill=C_STEEL_DARK, outline=C_AMBER)
    draw.ellipse([x0 + 5, y0 + 7, x1 - 5, y1 - 5], fill=C_AMBER)

    # Col 1: Terminal console block
    x0, y0, x1, y1 = tile_rect(1, 6)
    draw.rectangle([x0 + 1, y0 + 2, x1 - 1, y1], fill=C_STEEL_DARK, outline=C_STEEL_LIGHT)
    draw.rectangle([x0 + 3, y0 + 4, x1 - 3, y0 + 9], fill=(10, 28, 18, 255), outline=C_CRT_GREEN)
    draw.line([x0 + 4, y0 + 6, x1 - 5, y0 + 6], fill=C_CRT_GREEN)

    # -------------------------------------------------------------
    # ROW 7: AIRLOCK & BULKHEAD DOORS
    # -------------------------------------------------------------
    # Col 0: Heavy airlock door frame
    x0, y0, x1, y1 = tile_rect(0, 7)
    draw.rectangle([x0, y0, x1, y1], fill=C_STEEL_DARK)
    draw.rectangle([x0 + 2, y0 + 2, x1 - 2, y1 - 2], fill=C_CONC_MID, outline=C_CRT_GREEN)
    # Caution stripes
    for cy in range(y0, y1, 4):
        draw.line([x0, cy, x0 + 3, cy + 3], fill=C_AMBER)

    # =============================================================
    # COLUMNS 8..15: HIGH-DENSITY INDUSTRIAL ARTICULATED PROPS
    # =============================================================

    # -------------------------------------------------------------
    # 1. BIG EAR PARABOLIC DISH RELAY (3x3 TILES = 48x48: Cols 8..10, Rows 0..2)
    # -------------------------------------------------------------
    # (8, 0) Dish Top-Left
    x0, y0, x1, y1 = tile_rect(8, 0)
    draw.arc([x0 + 2, y0 + 4, x1 + 20, y1 + 24], 140, 220, fill=C_STEEL_HILITE, width=2)
    draw.line([x0 + 4, y0 + 10, x1, y1], fill=C_STEEL_MID, width=1)
    draw.point([x0 + 8, y0 + 6], fill=C_STEEL_HILITE)

    # (9, 0) Dish Top-Center & Feedhorn Stay
    x0, y0, x1, y1 = tile_rect(9, 0)
    draw.arc([x0 - 16, y0 + 4, x1 + 16, y1 + 24], 160, 200, fill=C_STEEL_HILITE, width=2)
    draw.line([x0 + 8, y0 + 6, x0 + 8, y1], fill=C_AMBER, width=1)
    draw.point([x0 + 8, y0 + 5], fill=(255, 240, 200, 255))

    # (10, 0) Dish Top-Right
    x0, y0, x1, y1 = tile_rect(10, 0)
    draw.arc([x0 - 20, y0 + 4, x1 - 2, y1 + 24], 320, 40, fill=C_STEEL_LIGHT, width=2)
    draw.line([x0, y1, x1 - 4, y0 + 10], fill=C_STEEL_MID, width=1)

    # (8, 1) Dish Mid-Left
    x0, y0, x1, y1 = tile_rect(8, 1)
    draw.arc([x0 + 2, y0 - 12, x1 + 20, y1 + 10], 140, 220, fill=C_STEEL_LIGHT, width=2)
    draw.line([x0 + 6, y0, x1, y1 - 4], fill=C_STEEL_DARK, width=2)

    # (9, 1) Dish Focal Receiver Horn Center
    x0, y0, x1, y1 = tile_rect(9, 1)
    draw.rectangle([x0 + 5, y0 + 4, x1 - 5, y1 - 4], fill=C_STEEL_DARK, outline=C_STEEL_LIGHT)
    draw.polygon([(x0 + 8, y0 + 2), (x0 + 5, y0 + 7), (x1 - 5, y0 + 7)], fill=C_AMBER)
    draw.line([x0 + 8, y1 - 4, x0 + 8, y1], fill=C_STEEL_HILITE, width=2)
    draw.point([x0 + 8, y0 + 1], fill=(255, 60, 60, 255))

    # (10, 1) Dish Mid-Right
    x0, y0, x1, y1 = tile_rect(10, 1)
    draw.arc([x0 - 20, y0 - 12, x1 - 2, y1 + 10], 320, 40, fill=C_STEEL_DARK, width=2)
    draw.line([x0, y1 - 4, x1 - 6, y0], fill=C_STEEL_DARK, width=2)

    # (8, 2) Dish Base Mount Left Anchor
    x0, y0, x1, y1 = tile_rect(8, 2)
    draw.line([x1, y0, x0 + 4, y1 - 2], fill=C_STEEL_LIGHT, width=2)
    draw.rectangle([x0 + 2, y1 - 3, x0 + 8, y1], fill=C_CONC_MID, outline=C_STEEL_DARK)

    # (9, 2) Dish Central Pedestal Mast & Elevation Ring
    x0, y0, x1, y1 = tile_rect(9, 2)
    draw.rectangle([x0 + 5, y0, x1 - 5, y1 - 2], fill=C_STEEL_DARK, outline=C_STEEL_LIGHT)
    draw.ellipse([x0 + 4, y0 + 2, x1 - 4, y0 + 8], fill=C_STEEL_MID, outline=C_STEEL_HILITE)
    draw.rectangle([x0 + 2, y1 - 3, x1 - 2, y1], fill=C_CONC_MID)

    # (10, 2) Dish Base Mount Right Anchor
    x0, y0, x1, y1 = tile_rect(10, 2)
    draw.line([x0, y0, x1 - 4, y1 - 2], fill=C_STEEL_DARK, width=2)
    draw.rectangle([x1 - 8, y1 - 3, x1 - 2, y1], fill=C_CONC_MID, outline=C_STEEL_DARK)

    # -------------------------------------------------------------
    # 2. HEAVY BUNKER AIRLOCK BULKHEAD (2x3 TILES = 32x48: Cols 8..9, Rows 3..5)
    # -------------------------------------------------------------
    # (8, 3) Bulkhead Door Top-Left
    x0, y0, x1, y1 = tile_rect(8, 3)
    draw.rectangle([x0, y0, x1, y1], fill=C_STEEL_DARK)
    draw.rectangle([x0 + 2, y0 + 2, x1, y1], fill=C_CONC_MID, outline=C_STEEL_LIGHT)
    draw.rectangle([x0 + 4, y0 + 4, x0 + 8, y0 + 8], fill=(12, 40, 24, 255), outline=C_CRT_GREEN)
    draw.point([x0 + 6, y0 + 6], fill=C_CRT_GREEN)

    # (9, 3) Bulkhead Door Top-Right
    x0, y0, x1, y1 = tile_rect(9, 3)
    draw.rectangle([x0, y0, x1, y1], fill=C_STEEL_DARK)
    draw.rectangle([x0, y0 + 2, x1 - 2, y1], fill=C_CONC_MID, outline=C_STEEL_LIGHT)
    # Stenciled caution warning stripes
    for cy in range(y0 + 3, y0 + 12, 3):
        draw.line([x0 + 2, cy, x0 + 6, cy + 2], fill=C_AMBER)

    # (8, 4) Bulkhead Door Center-Left (Locking Wheel)
    x0, y0, x1, y1 = tile_rect(8, 4)
    draw.rectangle([x0, y0, x1, y1], fill=C_STEEL_DARK)
    draw.rectangle([x0 + 2, y0, x1, y1], fill=C_CONC_MID, outline=C_STEEL_LIGHT)
    # Circular blast door wheel hub
    draw.ellipse([x0 + 6, y0 + 2, x1 + 6, y1 - 2], fill=C_STEEL_DARK, outline=C_STEEL_HILITE)
    draw.ellipse([x0 + 9, y0 + 5, x1 + 3, y1 - 5], fill=C_STEEL_MID)
    draw.line([x0 + 6, y0 + 7, x1, y0 + 7], fill=C_STEEL_HILITE, width=1)

    # (9, 4) Bulkhead Door Center-Right (Locking Hydraulic Latch)
    x0, y0, x1, y1 = tile_rect(9, 4)
    draw.rectangle([x0, y0, x1, y1], fill=C_STEEL_DARK)
    draw.rectangle([x0, y0, x1 - 2, y1], fill=C_CONC_MID, outline=C_STEEL_LIGHT)
    draw.ellipse([x0 - 6, y0 + 2, x0 + 6, y1 - 2], fill=C_STEEL_DARK, outline=C_STEEL_HILITE)
    # Hydraulic piston latch
    draw.rectangle([x0 + 8, y0 + 6, x1 - 3, y0 + 10], fill=C_STEEL_LIGHT, outline=C_STEEL_HILITE)

    # (8, 5) Bulkhead Door Base-Left
    x0, y0, x1, y1 = tile_rect(8, 5)
    draw.rectangle([x0, y0, x1, y1], fill=C_STEEL_DARK)
    draw.rectangle([x0 + 2, y0, x1, y1 - 2], fill=C_CONC_MID, outline=C_STEEL_LIGHT)
    draw.rectangle([x0, y1 - 3, x1, y1], fill=C_STEEL_MID)

    # (9, 5) Bulkhead Door Base-Right
    x0, y0, x1, y1 = tile_rect(9, 5)
    draw.rectangle([x0, y0, x1, y1], fill=C_STEEL_DARK)
    draw.rectangle([x0, y0, x1 - 2, y1 - 2], fill=C_CONC_MID, outline=C_STEEL_LIGHT)
    draw.rectangle([x0, y1 - 3, x1, y1], fill=C_STEEL_MID)

    # -------------------------------------------------------------
    # 3. HAZARD WARNING PLACARD (Col 10, Row 3: 16x16)
    # -------------------------------------------------------------
    x0, y0, x1, y1 = tile_rect(10, 3)
    # Steel pole
    draw.line([x0 + 7, y0 + 6, x0 + 7, y1], fill=C_STEEL_MID, width=2)
    # Diamond warning sign
    diamond = [(x0 + 7, y0), (x0 + 14, y0 + 7), (x0 + 7, y1 - 2), (x0, y0 + 7)]
    draw.polygon(diamond, fill=C_AMBER, outline=(24, 20, 10, 255))
    # Lightning bolt / exclamation symbol
    draw.line([x0 + 7, y0 + 3, x0 + 6, y0 + 7], fill=(18, 18, 20, 255), width=1)
    draw.line([x0 + 6, y0 + 7, x0 + 8, y0 + 7], fill=(18, 18, 20, 255), width=1)
    draw.line([x0 + 8, y0 + 7, x0 + 7, y0 + 11], fill=(18, 18, 20, 255), width=1)

    # -------------------------------------------------------------
    # 4. RADIO RELAY CHECKPOINT MAST (16x32: Col 10, Rows 4..5)
    # -------------------------------------------------------------
    # (10, 4) Transceiver Unit & Antenna
    x0, y0, x1, y1 = tile_rect(10, 4)
    # Whip antenna
    draw.line([x0 + 7, y0, x0 + 7, y0 + 6], fill=C_STEEL_HILITE, width=1)
    draw.point([x0 + 7, y0], fill=C_AMBER)
    # Transceiver housing
    draw.rectangle([x0 + 3, y0 + 6, x1 - 4, y1 - 2], fill=C_STEEL_DARK, outline=C_STEEL_LIGHT)
    draw.rectangle([x0 + 5, y0 + 8, x1 - 6, y0 + 11], fill=(10, 30, 20, 255), outline=C_CRT_GREEN)
    draw.point([x0 + 6, y0 + 9], fill=C_CRT_GREEN)
    draw.point([x1 - 7, y0 + 9], fill=C_CRT_GREEN)

    # (10, 5) Lattice Support Leg & Foot Flange
    x0, y0, x1, y1 = tile_rect(10, 5)
    draw.line([x0 + 7, y0, x0 + 7, y1 - 2], fill=C_STEEL_MID, width=2)
    # Lattice cross braces
    draw.line([x0 + 4, y0 + 2, x1 - 4, y0 + 7], fill=C_STEEL_LIGHT, width=1)
    draw.line([x1 - 4, y0 + 2, x0 + 4, y0 + 7], fill=C_STEEL_LIGHT, width=1)
    # Foundation base plate
    draw.rectangle([x0 + 2, y1 - 2, x1 - 2, y1], fill=C_CONC_MID, outline=C_STEEL_DARK)

    # -------------------------------------------------------------
    # 5. HIGH-VOLTAGE TRANSFORMER & CONDUITS (2x2: Cols 11..12, Rows 0..1)
    # -------------------------------------------------------------
    # (11, 0) Bushing Insulators
    x0, y0, x1, y1 = tile_rect(11, 0)
    for ix in [x0 + 3, x0 + 7, x0 + 11]:
        draw.line([ix, y0 + 2, ix, y1 - 2], fill=C_STEEL_HILITE, width=2)
        draw.point([ix, y0 + 1], fill=C_AMBER)
    draw.line([x0, y1 - 2, x1, y1 - 2], fill=C_STEEL_DARK, width=2)

    # (12, 0) Radiator Cooling Fins Top
    x0, y0, x1, y1 = tile_rect(12, 0)
    draw.rectangle([x0 + 1, y0 + 3, x1 - 1, y1], fill=C_STEEL_DARK, outline=C_STEEL_LIGHT)
    for fx in range(x0 + 3, x1 - 2, 3):
        draw.line([fx, y0 + 4, fx, y1], fill=C_STEEL_MID, width=1)

    # (11, 1) Transformer Main Box & Meter
    x0, y0, x1, y1 = tile_rect(11, 1)
    draw.rectangle([x0 + 1, y0, x1 - 1, y1 - 1], fill=C_STEEL_MID, outline=C_STEEL_DARK)
    draw.ellipse([x0 + 4, y0 + 3, x0 + 11, y0 + 10], fill=(16, 22, 28, 255), outline=C_STEEL_HILITE)
    draw.line([x0 + 7, y0 + 7, x0 + 9, y0 + 5], fill=C_AMBER)

    # (12, 1) Conduit Trunk Drop
    x0, y0, x1, y1 = tile_rect(12, 1)
    draw.rectangle([x0 + 1, y0, x1 - 1, y1 - 1], fill=C_STEEL_DARK, outline=C_STEEL_MID)
    draw.line([x0 + 5, y0, x0 + 5, y1], fill=C_RUST_LIGHT, width=2)
    draw.line([x0 + 10, y0, x0 + 10, y1], fill=C_STEEL_LIGHT, width=2)

    # -------------------------------------------------------------
    # 6. RUSTED INDUSTRIAL PIPES & COUPLERS (Cols 11..13, Row 2: 48x16)
    # -------------------------------------------------------------
    # (11, 2) Horizontal Pipe
    x0, y0, x1, y1 = tile_rect(11, 2)
    draw.rectangle([x0, y0 + 4, x1, y0 + 11], fill=C_RUST_MID)
    draw.line([x0, y0 + 4, x1, y0 + 4], fill=C_RUST_HILITE, width=1)
    draw.line([x0, y0 + 11, x1, y0 + 11], fill=C_RUST_DARK, width=1)

    # (12, 2) Flange Coupling Joint
    x0, y0, x1, y1 = tile_rect(12, 2)
    draw.rectangle([x0, y0 + 4, x1, y0 + 11], fill=C_RUST_MID)
    draw.line([x0, y0 + 4, x1, y0 + 4], fill=C_RUST_HILITE)
    draw.rectangle([x0 + 5, y0 + 2, x0 + 10, y0 + 13], fill=C_STEEL_DARK, outline=C_STEEL_HILITE)
    draw.point([x0 + 7, y0 + 4], fill=C_STEEL_CHROME if 'C_STEEL_CHROME' in dir() else C_STEEL_HILITE)
    draw.point([x0 + 7, y0 + 11], fill=C_STEEL_CHROME if 'C_STEEL_CHROME' in dir() else C_STEEL_HILITE)

    # (13, 2) Pipe 90-Degree Downward Elbow
    x0, y0, x1, y1 = tile_rect(13, 2)
    draw.rectangle([x0, y0 + 4, x0 + 8, y0 + 11], fill=C_RUST_MID)
    draw.rectangle([x0 + 3, y0 + 4, x0 + 10, y1], fill=C_RUST_MID)
    draw.line([x0, y0 + 4, x0 + 8, y0 + 4], fill=C_RUST_HILITE)
    draw.line([x0 + 10, y0 + 8, x0 + 10, y1], fill=C_RUST_DARK)

    # -------------------------------------------------------------
    # 7. HAZARD CHEMICAL & FUEL STORAGE DRUM (Col 14, Rows 0..1: 16x32)
    # -------------------------------------------------------------
    # (14, 0) Drum Top
    x0, y0, x1, y1 = tile_rect(14, 0)
    draw.ellipse([x0 + 2, y0 + 4, x1 - 2, y0 + 10], fill=C_RUST_LIGHT, outline=C_RUST_HILITE)
    draw.rectangle([x0 + 2, y0 + 7, x1 - 2, y1], fill=C_RUST_MID)
    draw.line([x0 + 2, y0 + 7, x0 + 2, y1], fill=C_RUST_HILITE)
    draw.line([x1 - 2, y0 + 7, x1 - 2, y1], fill=C_RUST_DARK)
    draw.point([x0 + 5, y0 + 6], fill=(240, 240, 240, 255))  # bung plug

    # (14, 1) Drum Bottom
    x0, y0, x1, y1 = tile_rect(14, 1)
    draw.rectangle([x0 + 2, y0, x1 - 2, y1 - 4], fill=C_RUST_MID)
    draw.ellipse([x0 + 2, y1 - 8, x1 - 2, y1 - 2], fill=C_RUST_DARK, outline=C_RUST_MID)
    draw.line([x0 + 2, y0, x0 + 2, y1 - 5], fill=C_RUST_HILITE)
    draw.line([x1 - 2, y0, x1 - 2, y1 - 5], fill=C_RUST_DARK)
    # Hazard stencil mark
    draw.polygon([(x0 + 8, y0 + 4), (x0 + 11, y0 + 8), (x0 + 5, y0 + 8)], fill=C_AMBER)

    # -------------------------------------------------------------
    # 8. ADVANCED ANALOG REEL-TO-REEL TAPE BANK (Col 15, Rows 0..1: 16x32)
    # -------------------------------------------------------------
    # (15, 0) Tape Reels Top
    x0, y0, x1, y1 = tile_rect(15, 0)
    draw.rectangle([x0 + 1, y0 + 1, x1 - 1, y1], fill=C_STEEL_DARK, outline=C_STEEL_LIGHT)
    # Two spinning magnetic tape reels
    draw.ellipse([x0 + 3, y0 + 4, x0 + 8, y0 + 9], fill=C_CONC_MID, outline=C_STEEL_HILITE)
    draw.ellipse([x0 + 8, y0 + 4, x0 + 13, y0 + 9], fill=C_CONC_MID, outline=C_STEEL_HILITE)
    draw.point([x0 + 5, y0 + 6], fill=(255, 255, 255, 255))
    draw.point([x0 + 10, y0 + 6], fill=(255, 255, 255, 255))

    # (15, 1) Tape Deck Controls Bottom
    x0, y0, x1, y1 = tile_rect(15, 1)
    draw.rectangle([x0 + 1, y0, x1 - 1, y1 - 2], fill=C_STEEL_DARK, outline=C_STEEL_LIGHT)
    # Status LEDs and switches
    for bx in range(x0 + 3, x1 - 3, 2):
        draw.point([bx, y0 + 3], fill=C_CRT_GREEN if bx % 4 == 0 else C_AMBER)
    draw.rectangle([x0 + 3, y0 + 7, x1 - 3, y0 + 11], fill=(12, 16, 20, 255), outline=C_STEEL_MID)

    # -------------------------------------------------------------
    # 9. FRACTURED RUBBLE & REBAR CRACK (Cols 13..14, Rows 3..4)
    # -------------------------------------------------------------
    x0, y0, x1, y1 = tile_rect(13, 3)
    draw.rectangle([x0, y0, x1, y1], fill=C_CONC_MID)
    draw.polygon([(x0 + 2, y0 + 14), (x0 + 8, y0 + 4), (x0 + 14, y0 + 12)], fill=C_CONC_LIGHT, outline=C_CONC_DARK)
    draw.line([x0 + 5, y0 + 8, x0 + 11, y0 + 3], fill=C_RUST_LIGHT, width=1)  # exposed rebar

    x0, y0, x1, y1 = tile_rect(14, 3)
    draw.rectangle([x0, y0, x1, y1], fill=C_CONC_MID)
    draw.line([x0 + 1, y0 + 3, x1 - 3, y1 - 2], fill=C_CONC_DARK, width=2)
    draw.line([x0 + 6, y0 + 8, x1 - 2, y0 + 5], fill=C_RUST_LIGHT, width=1)

    return img


def build_ohio_sky_twilight() -> Image.Image:
    """
    Build 960x270 seamless horizontal parallax sky background.
    Delaware County October dusk/twilight sky with radio mast beacons and distant treeline.
    """
    img = Image.new("RGBA", (960, 270), (8, 12, 20, 255))
    draw = ImageDraw.Draw(img)

    # 1. Dusk gradient
    for y in range(270):
        # Smooth interpolation from zenith indigo to horizon dusky slate
        t = y / 270.0
        r = int(8 + t * (38 - 8))
        g = int(12 + t * (54 - 12))
        b = int(20 + t * (86 - 20))
        draw.line([0, y, 959, y], fill=(r, g, b, 255))

    # 2. Distant cloud streaks (soft horizontal brush bands)
    cloud_color = (28, 42, 68, 80)
    for cx in range(0, 960, 160):
        draw.ellipse([cx, 70, cx + 180, 88], fill=cloud_color)
        draw.ellipse([cx + 60, 105, cx + 220, 118], fill=cloud_color)

    # 3. Distant radio mast silhouettes (Big Ear array towers)
    # Towers at x=120, x=380, x=640, x=860
    tower_x_positions = [120, 380, 640, 860]
    tower_color = (16, 24, 38, 255)
    beacon_color = (235, 45, 35, 255)

    for tx in tower_x_positions:
        # Lattice mast
        draw.line([tx, 30, tx, 240], fill=tower_color, width=2)
        draw.line([tx - 12, 240, tx, 30], fill=tower_color, width=1)
        draw.line([tx + 12, 240, tx, 30], fill=tower_color, width=1)
        # Cross braces
        for ty in range(60, 240, 30):
            draw.line([tx - 6, ty, tx + 6, ty], fill=tower_color, width=1)
        # Red obstruction beacon at mast apex
        draw.rectangle([tx - 1, 28, tx + 1, 30], fill=beacon_color)
        draw.point([tx, 27], fill=(255, 120, 100, 255))

    # 4. Distant treeline silhouette on the horizon (y=210..245)
    tree_color = (12, 18, 28, 255)
    for x in range(960):
        # Organic wave height
        h = int(18 + 10 * math.sin(x * 0.04) + 6 * math.sin(x * 0.11))
        draw.line([x, 240 - h, x, 270], fill=tree_color)

    return img


def build_ohio_treeline_fence() -> Image.Image:
    """
    Build 960x270 midground parallax layer with security perimeter chainlink fence
    and layered atmospheric Delaware County October autumn tree silhouettes.
    """
    img = Image.new("RGBA", (960, 270), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Distant layered tree crowns (Oaks and Maples canopy silhouettes)
    tree_back_col = (14, 20, 30, 240)
    tree_mid_col = (22, 32, 44, 255)
    tree_front_col = (30, 42, 56, 255)

    for x in range(960):
        # Multi-frequency organic undulating forest canopy
        h_back = int(32 + 14 * math.sin(x * 0.02) + 8 * math.sin(x * 0.07))
        draw.line([x, 210 - h_back, x, 210], fill=tree_back_col)

        h_mid = int(22 + 10 * math.sin(x * 0.035 + 1.2) + 6 * math.cos(x * 0.09))
        draw.line([x, 210 - h_mid, x, 210], fill=tree_mid_col)

        h_front = int(14 + 7 * math.sin(x * 0.05 + 2.5) + 4 * math.sin(x * 0.12))
        draw.line([x, 210 - h_front, x, 210], fill=tree_front_col)

    fence_y = 205
    fence_dark = (24, 34, 46, 220)
    fence_light = (58, 80, 102, 230)
    fence_hilite = (95, 125, 150, 255)
    post_dark = (32, 44, 56, 255)
    post_hilite = (74, 98, 122, 255)
    barbed_col = (68, 92, 114, 240)
    sign_yellow = (225, 170, 35, 255)

    # 2. Tubular line posts and barbed-wire top outriggers every 48px
    for px in range(0, 960, 48):
        # Post shadow and highlight
        draw.line([px, fence_y - 32, px, 270], fill=post_dark, width=2)
        draw.line([px + 1, fence_y - 32, px + 1, 270], fill=post_hilite, width=1)
        # 45-degree top outrigger bracket
        draw.line([px, fence_y - 32, px + 7, fence_y - 39], fill=post_hilite, width=1)
        draw.line([px - 1, fence_y - 32, px + 6, fence_y - 39], fill=post_dark, width=1)

        # Warning security sign mounted on alternate posts
        if px % 96 == 0:
            draw.rectangle([px - 5, fence_y - 20, px + 5, fence_y - 12], fill=sign_yellow, outline=(30, 24, 10, 255))
            draw.line([px - 3, fence_y - 16, px + 3, fence_y - 16], fill=(20, 20, 20, 255), width=1)

    # 3. Barbed wire strands (3 strands) with twisted razor barbs
    for by, strand_y in enumerate([fence_y - 38, fence_y - 35, fence_y - 32]):
        draw.line([0, strand_y, 959, strand_y], fill=barbed_col, width=1)
        # Razor barbs every 8 pixels
        for bx in range(by * 3, 960, 8):
            draw.line([bx - 1, strand_y - 2, bx + 1, strand_y + 2], fill=fence_hilite, width=1)
            draw.line([bx + 1, strand_y - 2, bx - 1, strand_y + 2], fill=post_dark, width=1)

    # 4. Galvanized chainlink diamond mesh grid with alternating highlight nodes
    for x in range(0, 960, 12):
        draw.line([x, fence_y - 30, x + 18, fence_y], fill=fence_dark, width=1)
        draw.line([x + 18, fence_y - 30, x, fence_y], fill=fence_light, width=1)
        # Interlock nodes
        for ny in range(fence_y - 25, fence_y, 6):
            draw.point([x + 9, ny], fill=fence_hilite)

    # 5. Bottom tension cable & top tubular rail
    draw.line([0, fence_y - 30, 959, fence_y - 30], fill=post_hilite, width=2)
    draw.line([0, fence_y - 1, 959, fence_y - 1], fill=post_dark, width=1)

    # 6. Concrete trench rim and aggregate wall base
    draw.rectangle([0, fence_y, 959, 270], fill=(16, 24, 32, 255))
    draw.line([0, fence_y, 959, fence_y], fill=(42, 58, 74, 255), width=2)
    draw.line([0, fence_y + 2, 959, fence_y + 2], fill=(26, 36, 48, 255), width=1)

    # Weed tufts and autumn debris along base of fence
    for wx in range(0, 960, 14):
        draw.line([wx, fence_y, wx + 2, fence_y - 4], fill=(62, 74, 40, 240))
        draw.line([wx + 3, fence_y, wx + 1, fence_y - 6], fill=(84, 98, 48, 240))

    return img


def build_ohio_dish_lattice() -> Image.Image:
    """
    Build 960x270 near-background parallax layer depicting Ohio Big Ear radio telescope's
    iconic 110-meter flat reflector mesh and structural steel triangular truss space-frame.
    """
    img = Image.new("RGBA", (960, 270), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    truss_dark = (26, 38, 52, 240)
    truss_mid = (42, 60, 80, 240)
    truss_light = (68, 92, 118, 255)
    truss_hilite = (110, 140, 172, 255)
    mesh_col = (30, 44, 60, 180)
    beacon_red = (255, 45, 45, 255)
    beacon_amber = (255, 180, 40, 255)

    # 1. Structural steel double-layered space-frame trusses
    for x in range(0, 960, 64):
        # Primary Warren truss diagonal members (I-beam profile)
        draw.line([x, 38, x + 32, 192], fill=truss_dark, width=3)
        draw.line([x, 38, x + 32, 192], fill=truss_mid, width=2)
        draw.line([x, 37, x + 31, 191], fill=truss_light, width=1)

        draw.line([x + 32, 192, x + 64, 38], fill=truss_dark, width=3)
        draw.line([x + 32, 192, x + 64, 38], fill=truss_mid, width=2)
        draw.line([x + 33, 192, x + 65, 38], fill=truss_light, width=1)

        # Gusset connection plates at triangular apex nodes
        for gx, gy in [(x, 38), (x + 32, 192), (x + 64, 38)]:
            draw.rectangle([gx - 4, gy - 4, gx + 4, gy + 4], fill=truss_mid, outline=truss_light)
            draw.point([gx, gy], fill=truss_hilite)

        # Horizontal chord I-beams
        draw.line([x, 38, x + 64, 38], fill=truss_dark, width=3)
        draw.line([x, 37, x + 64, 37], fill=truss_hilite, width=1)

        draw.line([x, 115, x + 64, 115], fill=truss_mid, width=2)
        draw.line([x, 114, x + 64, 114], fill=truss_light, width=1)

        draw.line([x, 192, x + 64, 192], fill=truss_dark, width=3)
        draw.line([x, 191, x + 64, 191], fill=truss_light, width=1)

    # 2. Precision parabolic bowed reflector mesh grid
    for y in range(48, 186, 8):
        # Subtle parabolic sag in reflector wires
        for x in range(0, 960, 4):
            sag = int(3 * math.sin((x % 320) / 320.0 * math.pi))
            draw.point([x, y + sag], fill=mesh_col)
            draw.point([x + 1, y + sag], fill=mesh_col)

    # Vertical antenna grid reflector stays
    for x in range(0, 960, 16):
        draw.line([x, 38, x, 192], fill=mesh_col, width=1)

    # 3. High-Fidelity Feedhorn Collector Mast Arrays at x=280 and x=760
    for hx in [280, 760]:
        # Heavy lattice mast trunk
        draw.line([hx - 2, 12, hx - 2, 192], fill=truss_dark, width=2)
        draw.line([hx + 2, 12, hx + 2, 192], fill=truss_light, width=2)
        draw.line([hx, 12, hx, 192], fill=truss_mid, width=2)

        # Ladder climbing rungs
        for ly in range(25, 190, 8):
            draw.line([hx - 3, ly, hx + 3, ly], fill=truss_hilite, width=1)

        # Pyramidal electromagnetic feedhorn collector
        horn_pts = [(hx, 12), (hx - 16, 42), (hx + 16, 42)]
        draw.polygon(horn_pts, fill=truss_dark, outline=truss_light)
        draw.polygon([(hx, 15), (hx - 12, 40), (hx + 12, 40)], fill=truss_mid)
        draw.ellipse([hx - 10, 36, hx + 10, 44], fill=(18, 24, 32, 255), outline=truss_hilite)

        # High-voltage coaxial feedline running down mast
        draw.line([hx + 4, 40, hx + 4, 192], fill=beacon_amber, width=1)

        # Guy wires with tension turnbuckles
        draw.line([hx, 24, hx - 64, 192], fill=truss_light, width=1)
        draw.line([hx, 24, hx + 64, 192], fill=truss_light, width=1)
        draw.ellipse([hx - 32, 108, hx - 28, 114], fill=truss_hilite)
        draw.ellipse([hx + 28, 108, hx + 32, 114], fill=truss_hilite)

        # Red obstruction beacon at mast summit
        draw.rectangle([hx - 2, 8, hx + 2, 12], fill=beacon_red)
        draw.point([hx, 7], fill=(255, 180, 180, 255))

    return img


def build_weather_mist() -> Image.Image:
    """
    Build 480x270 atmospheric autumn mist weather overlay.
    Low opacity (alpha 15..35) ensuring 100% combat readability.
    """
    img = Image.new("RGBA", (480, 270), (0, 0, 0, 0))
    px = img.load()

    for y in range(270):
        # Ground fog denser near lower elevations
        base_a = int(10 + (y / 270.0) * 22)
        for x in range(480):
            # Gentle sinusoidal density variation
            wave = math.sin(x * 0.03 + y * 0.02) * math.cos(y * 0.05)
            a = max(0, min(38, int(base_a + wave * 6)))
            px[x, y] = (160, 180, 205, a)

    return img


def main():
    ensure_directories()
    print("Building Act I Ohio Environment Art Suite...")

    # 1. Tileset
    tileset_img = build_ohio_tileset()
    tileset_path = ENV_DIR / "tileset_ohio_16x16.png"
    tileset_img.save(tileset_path)
    print(f"Saved tileset: {tileset_path.name} ({tileset_img.size[0]}x{tileset_img.size[1]})")

    # 2. Parallax background plates
    sky_img = build_ohio_sky_twilight()
    sky_path = ENV_DIR / "bg_ohio_sky_twilight.png"
    sky_img.save(sky_path)
    print(f"Saved sky: {sky_path.name} ({sky_img.size[0]}x{sky_img.size[1]})")

    fence_img = build_ohio_treeline_fence()
    fence_path = ENV_DIR / "bg_ohio_treeline_fence.png"
    fence_img.save(fence_path)
    print(f"Saved fence: {fence_path.name} ({fence_img.size[0]}x{fence_img.size[1]})")

    dish_img = build_ohio_dish_lattice()
    dish_path = ENV_DIR / "bg_ohio_dish_lattice.png"
    dish_img.save(dish_path)
    print(f"Saved dish lattice: {dish_path.name} ({dish_img.size[0]}x{dish_img.size[1]})")

    # 3. Weather overlay
    mist_img = build_weather_mist()
    mist_path = ENV_DIR / "weather_ohio_mist.png"
    mist_img.save(mist_path)
    print(f"Saved weather mist: {mist_path.name} ({mist_img.size[0]}x{mist_img.size[1]})")

    # 4. Generate manifest
    manifest_data = {
        "schema_version": 1,
        "environment_id": "act_01_ohio",
        "description": "Act I Ohio outdoor environment visual assets (Big Ear Observatory, approach trench, salvage yard, catwalk, arena)",
        "tile_size": 16,
        "assets": {
            "tileset_ohio": {
                "file": tileset_path.name,
                "dimensions": list(tileset_img.size),
                "sha256": hashlib.sha256(tileset_path.read_bytes()).hexdigest(),
                "alpha_mode": "RGBA",
                "tile_rows": {
                    "0": "SOLID_CONCRETE",
                    "1": "SOLID_TERRAIN_MUD",
                    "2": "ONE_WAY_CATWALK_GRATING",
                    "3": "ONE_WAY_SCRAP_PLATES",
                    "4": "HAZARD_SUMP_LIQUID",
                    "5": "COVER_SANDBAGS_CRATES",
                    "6": "PROPS_FIXTURES",
                    "7": "AIRLOCK_BULKHEAD_DOORS"
                }
            },
            "bg_ohio_sky": {
                "file": sky_path.name,
                "dimensions": list(sky_img.size),
                "sha256": hashlib.sha256(sky_path.read_bytes()).hexdigest(),
                "parallax_ratio_x": 0.10,
                "parallax_ratio_y": 0.05
            },
            "bg_ohio_fence": {
                "file": fence_path.name,
                "dimensions": list(fence_img.size),
                "sha256": hashlib.sha256(fence_path.read_bytes()).hexdigest(),
                "parallax_ratio_x": 0.35,
                "parallax_ratio_y": 0.15
            },
            "bg_ohio_dish": {
                "file": dish_path.name,
                "dimensions": list(dish_img.size),
                "sha256": hashlib.sha256(dish_path.read_bytes()).hexdigest(),
                "parallax_ratio_x": 0.65,
                "parallax_ratio_y": 0.25
            },
            "weather_ohio_mist": {
                "file": mist_path.name,
                "dimensions": list(mist_img.size),
                "sha256": hashlib.sha256(mist_path.read_bytes()).hexdigest(),
                "blend_mode": "alpha",
                "max_alpha": 38
            }
        }
    }

    manifest_path = ENV_DIR / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
    print(f"Saved environment manifest: {manifest_path.name}")
    print("Ohio environment art suite built successfully.")


if __name__ == "__main__":
    main()

