"""
═══════════════════════════════════════════════════════
MODULE: video_game/engine/config.py
PURPOSE: Single source of truth for all game constants, palettes, and paths.
CALLED BY: crt_renderer.py, state_machine.py, main.py, and all game scenes.
HOW TO MODIFY:
  - To change window size or scaling -> edit DEFAULT_SCALE.
  - To change any color -> edit COLOR_* RGB tuples below.
  - To change starting weapons or meters -> edit data/campaign.json.
═══════════════════════════════════════════════════════
"""

from pathlib import Path
from .campaign import Campaign

# ── Directory Paths (using pathlib.Path `/` operator) ──
GAME_ROOT_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT_DIR = GAME_ROOT_DIR.parent
ASSETS_DIR = GAME_ROOT_DIR / "assets"
DATA_DIR = GAME_ROOT_DIR / "data"
CIV_ASSETS_DIR = ASSETS_DIR / "civilizations"
AUDIO_ASSETS_DIR = ASSETS_DIR / "audio"
TRASH_DIR = GAME_ROOT_DIR / "_trash"

# ── Project resolution and timing ──
INTERNAL_WIDTH = 480
INTERNAL_HEIGHT = 270
RENDER_DENSITY = 2
RENDER_WIDTH = INTERNAL_WIDTH * RENDER_DENSITY
RENDER_HEIGHT = INTERNAL_HEIGHT * RENDER_DENSITY
DEFAULT_SCALE = 2  # 1920 x 1080 window; scale is in 960 x 540 units.
WINDOW_WIDTH = RENDER_WIDTH * DEFAULT_SCALE
WINDOW_HEIGHT = RENDER_HEIGHT * DEFAULT_SCALE
TARGET_FPS = 60

# ── Canonical Color Palette (RGB Tuples) ──
COLOR_VOID_BLACK = (2, 2, 6)          # #020206 — Deep space void
COLOR_BUNKER_DARK = (10, 26, 15)      # #0A1A0F — Bunker concrete shadow
COLOR_CRT_GREEN = (51, 255, 102)      # #33FF66 — Primary phosphor green
COLOR_CRT_DIM = (22, 105, 45)         # #16692D — Faded CRT burn-in
COLOR_CRT_DARK = (6, 20, 11)          # #06140B — CRT screen background
COLOR_EHMAN_RED = (204, 34, 34)       # #CC2222 — Red felt-tip "Wow!" ink
COLOR_BRIGHT_RED = (255, 45, 66)      # #FF2D42 — Core targeting laser
COLOR_AMBER_1977 = (255, 158, 44)     # #FF9E2C — 1977 Lab & vacuum tube glow
COLOR_LAB_BROWN = (61, 43, 31)        # #3D2B1F — 1977 Computer lab shadows
COLOR_CORE_STEEL = (192, 216, 240)    # #C0D8F0 — Cold blue-steel Core synths
COLOR_CORE_SHADOW = (6, 8, 12)        # #06080C — Blackout city shadow
COLOR_OLIVE_JACKET = (74, 93, 35)     # #4A5D23 — Mateo's military field jacket
COLOR_FIBO_GOLD = (229, 193, 88)      # #E5C158 — Fibonacci harmonic gold
COLOR_CYBER_MAGENTA = (255, 0, 85)    # #FF0055 — Scavenger neon magenta
COLOR_ARC_CYAN = (0, 240, 255)        # #00F0FF — Cherenkov / Dyson arc cyan
COLOR_PAPER_WHITE = (232, 240, 216)   # #E8F0D8 — Dot-matrix printout paper

# ── Game Scene Identifiers ──
STATE_TITLE_BOOT = "TITLE_BOOT"
STATE_BUNKER_HUB = "BUNKER_HUB"
STATE_CRT_TERMINAL = "CRT_TERMINAL"
STATE_SCIENCE_LAB = "SCIENCE_LAB"
STATE_FIELD_OPS = "FIELD_OPS"
STATE_BOSS_BOUNTY = "BOSS_BOUNTY"

# ── Scientific & Signal Constants ──
FIBONACCI_SEQ = (1, 1, 2, 3, 5, 8, 13, 21, 34)
HYDROGEN_LINE_MHZ = 1420.4056
OBSERVATION_WINDOW_SECONDS = 72


def default_campaign_state():
    """Create an authoritative, unseeded new-game campaign."""
    return Campaign()
