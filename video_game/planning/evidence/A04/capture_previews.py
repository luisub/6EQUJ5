"""
Capture visual evidence previews for Task A04 (Mateo animation clips).
Generates:
1. 01_action_poses_contact_sheet.png: 22 action poses across all 3 outfits.
2. 02_motion_run_cycle.png: 4-frame run cycle with foot contact verification.
3. 03_mirrored_facing_alignment.png: Pixel-calibrated facing right vs left pivot comparison.
4. 04_combat_scale_ingame_preview.png: Live FieldOpsScene render with animated Mateo.
5. 05_bunker_scale_preview.png: Native bunker presentation scale preview.
"""

import os
from pathlib import Path
import pygame
from PIL import Image, ImageDraw, ImageFont

# Set headless display driver if in CI/non-interactive
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
ASSETS_DIR = REPO_ROOT / "video_game" / "assets"
OUT_DIR = Path(__file__).resolve().parent / "previews"
OUT_DIR.mkdir(parents=True, exist_ok=True)

from video_game.engine import config
from video_game.engine.animation import AnimationPlayer, load_mateo_animations
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.scenes.field import FieldOpsScene
from video_game.engine.scenes.bunker import BunkerHubScene
from video_game.engine.state_machine import GameStateMachine
from video_game.tools.mateo_sprite_builder import ACTION_POSE_NAMES, OUTFIT_PALETTES


def generate_contact_sheet():
    """Build high-resolution inspection contact sheet of all 22 poses across 3 outfits."""
    cell_w, cell_h = 96, 128
    pad_x, pad_y = 12, 28
    cols = 11
    rows = 6  # 2 rows per outfit
    total_w = cols * (cell_w + pad_x) + pad_x
    total_h = rows * (cell_h + pad_y) + 50

    sheet = Image.new("RGBA", (total_w, total_h), (8, 12, 16, 255))
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 12), "6EQUJ5 // DR. MATEO 'SIX' VARGAS: 22 ACTION POSES x 3 OUTFITS (A04 REVIEW)", fill=(51, 255, 102, 255))

    outfit_list = list(OUTFIT_PALETTES.keys())
    for o_idx, o_key in enumerate(outfit_list):
        outfit_dir = ASSETS_DIR / "sprites" / "mateo" / o_key
        row_base = o_idx * 2
        draw.text((16, 36 + row_base * (cell_h + pad_y)), f"OUTFIT: {OUTFIT_PALETTES[o_key]['label']}", fill=(255, 176, 0, 255))

        for p_idx, p_name in enumerate(ACTION_POSE_NAMES):
            col = p_idx % cols
            row = row_base + (p_idx // cols)
            px = pad_x + col * (cell_w + pad_x)
            py = 52 + row * (cell_h + pad_y)

            # Cell background card
            draw.rectangle((px, py, px + cell_w, py + cell_h), fill=(14, 20, 26, 255), outline=(32, 54, 46, 255))

            # Load frame
            frame_path = outfit_dir / f"{p_name}.png"
            if frame_path.is_file():
                with Image.open(frame_path) as fr:
                    sheet.alpha_composite(fr.convert("RGBA"), (px, py))

            # Foot pivot crosshair at (48, 124)
            piv_x = px + 48
            piv_y = py + 124
            draw.line((piv_x - 3, piv_y, piv_x + 3, piv_y), fill=(255, 60, 60, 255))
            draw.line((piv_x, piv_y - 3, piv_x, piv_y + 3), fill=(255, 60, 60, 255))

            # Label
            draw.text((px + 4, py + cell_h + 4), p_name.upper()[:12], fill=(160, 200, 185, 255))

    sheet.save(OUT_DIR / "01_action_poses_contact_sheet.png")
    print(f"Exported: {OUT_DIR / '01_action_poses_contact_sheet.png'}")


def generate_run_cycle_inspection():
    """Build detailed run cycle strip with ground contact registration lines."""
    width = 480
    height = 200
    img = Image.new("RGBA", (width, height), (10, 14, 18, 255))
    draw = ImageDraw.Draw(img)
    draw.text((14, 10), "MATEO RUN CYCLE STRIDE INSPECTION (110ms / FRAME // 440ms CYCLE)", fill=(51, 255, 102, 255))

    outfit_dir = ASSETS_DIR / "sprites" / "mateo" / "olive_field"
    ground_y = 160
    draw.line((10, ground_y, width - 10, ground_y), fill=(40, 180, 100, 255), width=2)
    draw.text((14, ground_y + 6), "GROUND PLANE ANCHOR (Y = 124 PIXEL PIVOT)", fill=(40, 180, 100, 255))

    run_frames = ["run_1", "run_2", "run_3", "run_4"]
    for idx, fname in enumerate(run_frames):
        p_path = outfit_dir / f"{fname}.png"
        if p_path.is_file():
            with Image.open(p_path) as fr:
                x_pos = 30 + idx * 110
                # Align foot pivot (48, 124) with ground_y
                y_pos = ground_y - 124
                # Card box
                draw.rectangle((x_pos, y_pos, x_pos + 96, y_pos + 128), fill=(16, 24, 30, 200), outline=(32, 60, 50, 255))
                img.alpha_composite(fr.convert("RGBA"), (x_pos, y_pos))

                # Foot pivot marker
                draw.ellipse((x_pos + 46, ground_y - 2, x_pos + 50, ground_y + 2), fill=(255, 60, 60, 255))
                draw.text((x_pos + 20, y_pos + 6), f"FRAME {idx+1}", fill=(255, 176, 0, 255))

    img.save(OUT_DIR / "02_motion_run_cycle.png")
    print(f"Exported: {OUT_DIR / '02_motion_run_cycle.png'}")


def generate_facing_alignment_comparison():
    """Verify mirrored pivot registration on calibrated pixel grid."""
    width = 480
    height = 240
    img = Image.new("RGBA", (width, height), (8, 10, 14, 255))
    draw = ImageDraw.Draw(img)
    draw.text((14, 10), "MIRRORED PIVOT REGISTRATION (FACING RIGHT vs FACING LEFT)", fill=(51, 255, 102, 255))

    # Grid background
    for gy in range(30, height, 16):
        draw.line((0, gy, width, gy), fill=(16, 26, 32, 255))
    for gx in range(0, width, 16):
        draw.line((gx, 30, gx, height), fill=(16, 26, 32, 255))

    # Load idle frame
    idle_path = ASSETS_DIR / "sprites" / "mateo" / "olive_field" / "idle_1.png"
    if idle_path.is_file():
        with Image.open(idle_path) as fr:
            # RIGHT
            anchor_rx = 140
            anchor_ry = 180
            # Pivot at (48, 124) -> blit at (anchor_rx - 48, anchor_ry - 124)
            img.alpha_composite(fr, (anchor_rx - 48, anchor_ry - 124))
            draw.line((anchor_rx, 40, anchor_rx, 220), fill=(0, 240, 255, 255), width=1)
            draw.line((anchor_rx - 10, anchor_ry, anchor_rx + 10, anchor_ry), fill=(0, 240, 255, 255), width=1)
            draw.text((anchor_rx - 38, 222), "FACING RIGHT", fill=(0, 240, 255, 255))

            # LEFT (Mirrored)
            fr_left = fr.transpose(Image.FLIP_LEFT_RIGHT)
            anchor_lx = 340
            anchor_ly = 180
            # Mirrored pivot: W - 1 - 48 = 96 - 1 - 48 = 47
            img.alpha_composite(fr_left, (anchor_lx - 47, anchor_ly - 124))
            draw.line((anchor_lx, 40, anchor_lx, 220), fill=(255, 128, 0, 255), width=1)
            draw.line((anchor_lx - 10, anchor_ly, anchor_lx + 10, anchor_ly), fill=(255, 128, 0, 255), width=1)
            draw.text((anchor_lx - 34, 222), "FACING LEFT", fill=(255, 128, 0, 255))

    img.save(OUT_DIR / "03_mirrored_facing_alignment.png")
    print(f"Exported: {OUT_DIR / '03_mirrored_facing_alignment.png'}")


def generate_combat_scale_preview():
    """Render live FieldOpsScene with animated Mateo in access trench."""
    pygame.init()
    pygame.display.set_mode((480, 270))
    crt = CRTRenderer(scale=1)
    machine = GameStateMachine(crt, development=True)

    field_scene = FieldOpsScene(machine, "act_01/approach.json")
    field_scene.on_enter(None)

    # Position player near sandbag cover
    field_scene.player.x = 360.0
    field_scene.player.y = 192.0
    field_scene.player.vx = 40.0
    field_scene.player.facing = "right"
    field_scene.camera.snap_to(field_scene.player.x, field_scene.player.y)

    # Step simulation
    for _ in range(10):
        field_scene.update(0.016)

    field_scene.render(crt)
    pygame.image.save(crt.canvas, str(OUT_DIR / "04_combat_scale_ingame_preview.png"))
    print(f"Exported: {OUT_DIR / '04_combat_scale_ingame_preview.png'}")
    pygame.quit()


def generate_bunker_scale_preview():
    """Render live BunkerHubScene with Mateo in bunker scale."""
    pygame.init()
    pygame.display.set_mode((480, 270))
    crt = CRTRenderer(scale=1)
    machine = GameStateMachine(crt, development=True)

    bunker_scene = BunkerHubScene(machine)
    bunker_scene.on_enter()
    bunker_scene.outfit_idx = 1  # 1977 Olive Field Jacket

    for _ in range(5):
        bunker_scene.update(0.016)

    bunker_scene.render(crt)
    pygame.image.save(crt.canvas, str(OUT_DIR / "05_bunker_scale_preview.png"))
    print(f"Exported: {OUT_DIR / '05_bunker_scale_preview.png'}")
    pygame.quit()


def main():
    generate_contact_sheet()
    generate_run_cycle_inspection()
    generate_facing_alignment_comparison()
    generate_combat_scale_preview()
    generate_bunker_scale_preview()
    print("All A04 previews generated successfully!")


if __name__ == "__main__":
    main()
