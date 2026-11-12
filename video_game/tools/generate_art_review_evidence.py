"""
MODULE: video_game/tools/generate_art_review_evidence.py
PURPOSE: Generate comprehensive visual evidence, composite sheets, and preview renders
         for the art review and remediation milestone.
CALLED BY: Manual verification and evidence documentation.
HOW TO MODIFY: Add additional preview capture scenes or asset panels.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import pygame

from video_game.engine import config
from video_game.engine.bosses.greenkeeper import Greenkeeper
from video_game.engine.world import Camera, Room

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EVIDENCE_DIR = REPO_ROOT / "video_game" / "planning" / "evidence" / "art_review" / "previews"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def capture_greenkeeper_showcase():
    """Generate 640x360 montage showcasing all Greenkeeper boss animations and arena render."""
    pygame.init()
    surf = pygame.Surface((640, 360))
    surf.fill((16, 20, 26))

    # Title Banner
    font = pygame.font.Font(None, 24)
    font_sm = pygame.font.Font(None, 18)
    title_lbl = font.render("CORE WARDEN GREENKEEPER // 16-BIT PIXEL ART SHOWCASE", True, config.COLOR_AMBER_1977)
    sub_lbl = font_sm.render("Native 64x48 Pixel Art Sprites with Dynamic States & Weak-Point Reticles", True, config.COLOR_CORE_STEEL)
    surf.blit(title_lbl, (20, 16))
    surf.blit(sub_lbl, (20, 42))

    # Render Sprite States Grid (2x scaled for clear preview)
    boss = Greenkeeper(x=460.0, y=192.0)
    sprite_states = [
        ("idle_1", "IDLE (TRACK LINK 1)"),
        ("idle_2", "IDLE (TRACK LINK 2)"),
        ("charge_1", "CHARGE (RAM TILT)"),
        ("charge_2", "CHARGE (DIRT EJECT)"),
        ("mortar_aim", "MORTAR (ELEVATION)"),
        ("mortar_fire", "MORTAR (MUZZLE FLASH)"),
        ("sweep_charge", "SWEEP (PLASMA APERTURE)"),
        ("vulnerable_1", "VULNERABLE (CORE VENT 1)"),
        ("vulnerable_2", "VULNERABLE (CORE VENT 2)"),
        ("hurt", "DAMAGE FLASH"),
        ("defeated", "WRECKED HULL"),
    ]

    for idx, (s_name, desc) in enumerate(sprite_states):
        sp = boss.sprites.get(s_name)
        if sp is not None:
            col = idx % 4
            row = idx // 4
            pos_x = 24 + col * 152
            pos_y = 70 + row * 92

            # Background panel
            pygame.draw.rect(surf, (24, 30, 40), (pos_x, pos_y, 144, 84), border_radius=4)
            pygame.draw.rect(surf, (45, 55, 72), (pos_x, pos_y, 144, 84), 1, border_radius=4)

            # 2x scaled sprite
            scaled_sp = pygame.transform.scale(sp, (128, 96))
            # Blit center
            surf.blit(scaled_sp, (pos_x + 8, pos_y + 4), pygame.Rect(0, 0, 128, 64))

            # Description label
            d_lbl = font_sm.render(desc, True, (180, 200, 220))
            surf.blit(d_lbl, (pos_x + 8, pos_y + 68))

    out_path = EVIDENCE_DIR / "01_greenkeeper_pixel_art_states.png"
    pygame.image.save(surf, str(out_path))
    print(f"Exported Greenkeeper preview: {out_path}")


def capture_ohio_environment_showcase():
    """Generate 640x360 montage showcasing enriched tileset and parallax background layers."""
    img = Image.new("RGBA", (640, 360), (12, 16, 22, 255))
    draw = ImageDraw.Draw(img)

    draw.text((20, 14), "ACT I OHIO ENVIRONMENT ART // REMEDIATION SCORECARD", fill=(255, 175, 40, 255))
    draw.text((20, 36), "Enriched 256x128 Tileset (Cols 8-15 Populated) & Multi-Toned Parallax Layers", fill=(140, 165, 190, 255))

    # Tileset Preview (Scaled 2x)
    ts_path = REPO_ROOT / "video_game" / "assets" / "environments" / "ohio" / "tileset_ohio_16x16.png"
    if ts_path.exists():
        ts_img = Image.open(ts_path).convert("RGBA")
        ts_scaled = ts_img.resize((512, 128), Image.Resampling.NEAREST)
        draw.rectangle([18, 62, 534, 194], fill=(20, 26, 34, 255), outline=(60, 80, 100, 255))
        img.paste(ts_scaled, (20, 64), ts_scaled)
        draw.text((20, 198), "Full 16x8 Tileset: Concrete, Mud, Catwalk, Hazard Sump, Sandbags, Dish Mast, Bulkhead Door, Checkpoint", fill=(180, 200, 220, 255))

    # Parallax Background Strip
    fence_path = REPO_ROOT / "video_game" / "assets" / "environments" / "ohio" / "bg_ohio_treeline_fence.png"
    dish_path = REPO_ROOT / "video_game" / "assets" / "environments" / "ohio" / "bg_ohio_dish_lattice.png"
    if fence_path.exists() and dish_path.exists():
        fence = Image.open(fence_path).convert("RGBA").crop((0, 0, 480, 270)).resize((280, 110), Image.Resampling.NEAREST)
        dish = Image.open(dish_path).convert("RGBA").crop((0, 0, 480, 270)).resize((280, 110), Image.Resampling.NEAREST)
        # Dish frame
        draw.rectangle([18, 220, 302, 334], fill=(16, 22, 30, 255), outline=(50, 70, 90, 255))
        img.paste(dish, (20, 222), dish)
        draw.text((20, 338), "Big Ear Parabolic Lattice (Truss Depth)", fill=(160, 185, 210, 255))

        # Fence frame
        draw.rectangle([328, 220, 612, 334], fill=(16, 22, 30, 255), outline=(50, 70, 90, 255))
        img.paste(fence, (330, 222), fence)
        draw.text((330, 338), "Chainlink Perimeter & Autumn Treeline", fill=(160, 185, 210, 255))

    out_path = EVIDENCE_DIR / "02_ohio_environment_remediation.png"
    img.save(out_path)
    print(f"Exported Ohio environment preview: {out_path}")


def capture_civilization_remaster_showcase():
    """Generate 640x360 montage showcasing the 5 remediated civilizations."""
    img = Image.new("RGBA", (640, 360), (14, 18, 24, 255))
    draw = ImageDraw.Draw(img)

    draw.text((20, 14), "CIVILIZATION ART REMEDIATION // FULL PALETTE PARITY", fill=(255, 175, 40, 255))
    draw.text((20, 36), "Elevated FASR-006, 007, 008, 010 & FASR-SCAN-H from procedural sketches to authentic 24-color pixel art", fill=(140, 165, 190, 255))

    civ_dir = REPO_ROOT / "video_game" / "assets" / "civilizations"
    civs = [
        ("FASR-006", "fasr-006_composite.png", "PULSAR MAGNETAR"),
        ("FASR-007", "fasr-007_composite.png", "1420 MHz WOW! NEBULA"),
        ("FASR-008", "fasr-008_composite.png", "CORONAL DYSON RING"),
        ("FASR-010", "fasr-010_composite.png", "GÖBEKLI TEPE SIRIUS"),
        ("FASR-SCAN-H", "fasr-scan-h_composite.png", "HEPTAPOD BIO-ACOUSTIC"),
    ]

    for idx, (cid, fname, label) in enumerate(civs):
        p = civ_dir / fname
        if p.exists():
            c_img = Image.open(p).convert("RGBA").resize((104, 104), Image.Resampling.NEAREST)
            pos_x = 20 + idx * 122
            pos_y = 75

            # Border card
            draw.rectangle([pos_x - 4, pos_y - 4, pos_x + 107, pos_y + 145], fill=(22, 28, 38, 255), outline=(55, 75, 95, 255))
            img.paste(c_img, (pos_x, pos_y), c_img)

            draw.text((pos_x, pos_y + 110), cid, fill=(255, 200, 60, 255))
            draw.text((pos_x, pos_y + 126), label, fill=(160, 180, 205, 255))

    out_path = EVIDENCE_DIR / "03_civilization_art_remaster.png"
    img.save(out_path)
    print(f"Exported civilization remaster preview: {out_path}")


def main():
    capture_greenkeeper_showcase()
    capture_ohio_environment_showcase()
    capture_civilization_remaster_showcase()


if __name__ == "__main__":
    main()

