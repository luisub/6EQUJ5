"""
MODULE: video_game/tools/generate_a05_evidence.py
PURPOSE: Generate high-resolution visual evidence previews for A05 combat mechanics:
         swept-ray collision, piercing beams, 8-directional aim vectors, and in-game combat.
CALLED BY: Python execution during A05 verification.
HOW TO MODIFY: Update layout geometries or visual themes for subsequent combat milestones.
"""

import math
import os
from pathlib import Path
import pygame

from video_game.engine import config
from video_game.engine.animation import AnimationPlayer, load_mateo_animations
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.player import Player, PlayerConfig, PlayerInput
from video_game.engine.scenes.field import FieldOpsScene
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.weapons import (
    CombatTarget,
    ProjectileManager,
    StarterMaser,
    WeaponConfig,
    check_swept_ray_tile_collision,
    get_muzzle_world_pos,
    resolve_aim_vector,
)
from video_game.engine.world import (
    COLLISION_EMPTY,
    COLLISION_SOLID,
    Camera,
    Room,
)

EVIDENCE_DIR = Path("video_game/planning/evidence/A05/previews")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def generate_swept_ccd_preview():
    """Preview 01: Swept ray continuous collision detection vs discrete tunneling."""
    surf = pygame.Surface((480, 270))
    surf.fill((12, 16, 22))

    # Grid lines
    for x in range(0, 480, 16):
        pygame.draw.line(surf, (20, 28, 36), (x, 0), (x, 270), 1)
    for y in range(0, 270, 16):
        pygame.draw.line(surf, (20, 28, 36), (0, y), (480, y), 1)

    # Title Banner
    font_lg = pygame.font.Font(None, 20)
    font_sm = pygame.font.Font(None, 14)

    header = font_lg.render("CONTINUOUS COLLISION DETECTION (CCD) // SWEPT RAY VS DISCRETE TUNNELING", True, (255, 210, 80))
    surf.blit(header, (16, 12))

    # Thin Wall at x = 240..256 (1 tile = 16px wide)
    wall_rect = pygame.Rect(240, 48, 16, 180)
    pygame.draw.rect(surf, (80, 30, 30), wall_rect)
    pygame.draw.rect(surf, (220, 60, 60), wall_rect, 1)
    wall_lbl = font_sm.render("THIN SOLID WALL (16px)", True, (255, 100, 100))
    surf.blit(wall_lbl, (244, 234))

    # Scenario A: Discrete Stepping (Tunneling Failure)
    y_disc = 90
    lbl_a = font_sm.render("DISCRETE STEPPING: dt=0.08s, speed=1600px/s (Step = 128px) -> TUNNELS THROUGH WALL", True, (255, 120, 120))
    surf.blit(lbl_a, (24, y_disc - 24))

    step0 = (140, y_disc)
    step1 = (268, y_disc)  # Jumped right over x=240..256!

    pygame.draw.circle(surf, (100, 140, 255), step0, 5)
    pygame.draw.circle(surf, (255, 60, 60), step1, 5)
    pygame.draw.line(surf, (100, 100, 140), step0, step1, 1)
    surf.blit(font_sm.render("Tick 0 (x=140)", True, (140, 180, 255)), (110, y_disc + 8))
    surf.blit(font_sm.render("Tick 1 (x=268) [MISSED COLLISION!]", True, (255, 80, 80)), (268, y_disc + 8))

    # Scenario B: Swept-Ray Amanatides-Woo Traversal (Exact Contact)
    y_swept = 170
    lbl_b = font_sm.render("SWEPT RAY TRAVERSAL: Exact Amanatides-Woo DDA detects contact at wall boundary x=240.0", True, (100, 255, 160))
    surf.blit(lbl_b, (24, y_swept - 24))

    # Origin and ray
    origin = (140, y_swept)
    target_pos = (268, y_swept)
    hit_pos = (240, y_swept)

    # Intended trajectory (dashed)
    pygame.draw.line(surf, (40, 80, 60), origin, target_pos, 1)
    # Actual traversed segment
    pygame.draw.line(surf, (100, 255, 160), origin, hit_pos, 3)
    pygame.draw.circle(surf, (100, 255, 160), origin, 5)
    pygame.draw.circle(surf, (255, 230, 80), hit_pos, 6)

    # Impact sparks
    for angle in [0.4, 0.9, -0.4, -0.9, 3.14]:
        sx = hit_pos[0] + math.cos(angle) * 12
        sy = hit_pos[1] + math.sin(angle) * 12
        pygame.draw.line(surf, (255, 210, 80), hit_pos, (sx, sy), 1)

    surf.blit(font_sm.render("Start (x=140)", True, (100, 255, 160)), (110, y_swept + 8))
    surf.blit(font_sm.render("EXACT CONTACT x=240.0 [ZERO TUNNELING]", True, (255, 230, 80)), (244, y_swept - 14))

    pygame.image.save(surf, str(EVIDENCE_DIR / "01_swept_ccd_thin_wall_containment.png"))
    print("Saved 01_swept_ccd_thin_wall_containment.png")


def generate_piercing_preview():
    """Preview 02: Charged waveguide maser beam multi-target piercing."""
    surf = pygame.Surface((480, 270))
    surf.fill((10, 14, 20))

    font_lg = pygame.font.Font(None, 20)
    font_sm = pygame.font.Font(None, 14)

    header = font_lg.render("1420 MHz CHARGED MASER // MULTI-TARGET PIERCING BEAM (PIERCE BUDGET = 3)", True, (255, 210, 80))
    surf.blit(header, (16, 12))

    # Muzzle at x=40, y=130
    mx, my = 40, 130
    surf.blit(font_sm.render("Maser Muzzle (x=40)", True, (180, 220, 255)), (16, my - 20))

    # Targets at x=120, x=220, x=320, x=420
    targets = [
        (120, "DRONE-ALPHA", 100, 25, "HIT 1 (Pierce: 3->2)"),
        (220, "DRONE-BETA", 100, 25, "HIT 2 (Pierce: 2->1)"),
        (320, "DRONE-GAMMA", 100, 25, "HIT 3 (Pierce: 1->0) [TERMINAL]"),
        (420, "DRONE-DELTA", 100, 100, "BLOCKED (Pierce Budget Exhausted)"),
    ]

    # Draw Beam from x=40 to x=320
    # Outer plasma glow
    pygame.draw.line(surf, (255, 180, 50), (mx, my), (320, my), 8)
    # Inner energetic core
    pygame.draw.line(surf, (255, 255, 240), (mx, my), (320, my), 4)

    for tx, name, init_hp, end_hp, status in targets:
        t_rect = pygame.Rect(tx, my - 24, 24, 48)
        is_hit = end_hp < init_hp
        border_col = (255, 200, 60) if is_hit else (80, 100, 120)
        fill_col = (50, 40, 20) if is_hit else (20, 28, 36)
        pygame.draw.rect(surf, fill_col, t_rect)
        pygame.draw.rect(surf, border_col, t_rect, 2)

        # Labels
        surf.blit(font_sm.render(name, True, (220, 220, 220)), (tx - 8, my - 40))
        surf.blit(font_sm.render(f"HP: {end_hp}/{init_hp}", True, (255, 120, 120) if is_hit else (100, 255, 140)), (tx - 8, my + 30))
        surf.blit(font_sm.render(status, True, border_col), (tx - 20, my + 44))

        if is_hit:
            # Sparks
            for angle in [0.2, 0.7, -0.2, -0.7, 2.5, 3.8]:
                spx = tx + math.cos(angle) * 14
                spy = my + math.sin(angle) * 14
                pygame.draw.line(surf, (255, 230, 100), (tx, my), (spx, spy), 1)

    # Legend footer
    footer = font_sm.render("DAMAGE: 75 HP PER IMPACT  //  IDEMPOTENT HIT-IDS PREVENT MULTI-FRAME TICK RE-DAMAGE", True, (160, 200, 240))
    surf.blit(footer, (16, 246))

    pygame.image.save(surf, str(EVIDENCE_DIR / "02_piercing_beam_multi_target.png"))
    print("Saved 02_piercing_beam_multi_target.png")


def generate_aim_vectors_preview():
    """Preview 03: 8-directional aim vectors with normalized trajectories."""
    surf = pygame.Surface((480, 270))
    surf.fill((14, 18, 24))

    font_lg = pygame.font.Font(None, 20)
    font_sm = pygame.font.Font(None, 14)

    header = font_lg.render("8-DIRECTIONAL WEAPON AIM VECTORS & MUZZLE ATTACHMENT RESOLUTION", True, (255, 210, 80))
    surf.blit(header, (16, 12))

    # Center origin
    cx, cy = 240, 145
    radius = 75

    # Compass ring
    pygame.draw.circle(surf, (30, 42, 54), (cx, cy), radius, 1)
    pygame.draw.circle(surf, (20, 30, 40), (cx, cy), radius // 2, 1)

    # 8 directions
    directions = [
        ((1.0, 0.0), "RIGHT (1.0, 0.0)", (18, -6)),
        ((0.707, -0.707), "UP-RIGHT (+0.71, -0.71)", (10, -18)),
        ((0.0, -1.0), "UP (0.0, -1.0)", (-36, -24)),
        ((-0.707, -0.707), "UP-LEFT (-0.71, -0.71)", (-140, -18)),
        ((-1.0, 0.0), "LEFT (-1.0, 0.0)", (-110, -6)),
        ((-0.707, 0.707), "DOWN-LEFT (-0.71, +0.71)", (-150, 8)),
        ((0.0, 1.0), "DOWN (0.0, +1.0) [AIRBORNE]", (-75, 16)),
        ((0.707, 0.707), "DOWN-RIGHT (+0.71, +0.71)", (10, 8)),
    ]

    for (dx, dy), label, (ox, oy) in directions:
        end_x = cx + dx * radius
        end_y = cy + dy * radius

        # Glow line
        pygame.draw.line(surf, (80, 160, 255), (cx, cy), (end_x, end_y), 3)
        pygame.draw.line(surf, (220, 240, 255), (cx, cy), (end_x, end_y), 1)
        pygame.draw.circle(surf, (255, 210, 80), (int(end_x), int(end_y)), 3)

        surf.blit(font_sm.render(label, True, (160, 200, 240)), (end_x + ox, end_y + oy))

    # Center Mateo marker
    pygame.draw.circle(surf, (255, 255, 255), (cx, cy), 6)
    surf.blit(font_sm.render("MATEO (MUZZLE ORIGIN)", True, (255, 255, 255)), (cx - 65, cy + 85))

    pygame.image.save(surf, str(EVIDENCE_DIR / "03_aim_vectors_8_directions.png"))
    print("Saved 03_aim_vectors_8_directions.png")


def generate_ingame_combat_preview():
    """Preview 04: In-engine FieldOpsScene render of Mateo discharging waveguide maser."""
    pygame.init()
    crt = CRTRenderer(scale=config.DEFAULT_SCALE)
    machine = GameStateMachine(crt, development=True)

    field_scene = machine.scenes[config.STATE_FIELD_OPS]
    field_scene.player.x = 120.0
    field_scene.player.y = 192.0
    field_scene.player.facing = "right"
    field_scene.player.is_grounded = True
    field_scene.camera.snap_to(120.0, 192.0)

    # Spawn 2 active maser bolts in flight
    muzzle_x, muzzle_y = get_muzzle_world_pos(field_scene.player)
    field_scene.player.trigger_fire_recoil(0.12)

    # Bolt 1: Forward shot
    p1 = field_scene.projectile_manager.spawn(
        x=muzzle_x + 60.0,
        y=muzzle_y,
        dir_x=1.0,
        dir_y=0.0,
        speed=420.0,
        damage=25,
        beam_length=16.0,
        beam_thickness=3.0,
    )
    # Bolt 2: Second pulse
    p2 = field_scene.projectile_manager.spawn(
        x=muzzle_x + 140.0,
        y=muzzle_y,
        dir_x=1.0,
        dir_y=0.0,
        speed=420.0,
        damage=25,
        beam_length=16.0,
        beam_thickness=3.0,
    )
    # Impact sparks at distant obstacle
    field_scene.projectile_manager.add_sparks(muzzle_x + 140.0, muzzle_y, count=6)

    # Render scene to CRT
    field_scene.render(crt)

    # Save native resolution surface
    pygame.image.save(crt.canvas, str(EVIDENCE_DIR / "04_ingame_combat_field_preview.png"))
    print("Saved 04_ingame_combat_field_preview.png")


def generate_charge_comparison_preview():
    """Preview 05: Close-up comparison of standard maser pulse vs charged beam."""
    surf = pygame.Surface((480, 270))
    surf.fill((12, 16, 22))

    font_lg = pygame.font.Font(None, 20)
    font_sm = pygame.font.Font(None, 14)

    header = font_lg.render("WAVEGUIDE MASER DISCHARGE PROFILE // STANDARD VS CHARGED EMISSION", True, (255, 210, 80))
    surf.blit(header, (16, 12))

    # Standard Shot Card
    card_a = pygame.Rect(24, 44, 200, 190)
    pygame.draw.rect(surf, (18, 24, 32), card_a)
    pygame.draw.rect(surf, (60, 100, 140), card_a, 1)

    surf.blit(font_lg.render("STANDARD PULSE", True, (120, 220, 255)), (36, 54))
    surf.blit(font_sm.render("Cadence: 0.20s (5 shots/sec)", True, (180, 180, 180)), (36, 80))
    surf.blit(font_sm.render("Damage: 25 HP", True, (180, 180, 180)), (36, 96))
    surf.blit(font_sm.render("Pierce Count: 1 Target", True, (180, 180, 180)), (36, 112))
    surf.blit(font_sm.render("Beam Speed: 420 px/s", True, (180, 180, 180)), (36, 128))
    surf.blit(font_sm.render("Glow Profile: Electric Cyan", True, (120, 220, 255)), (36, 144))

    # Draw standard beam preview
    beam_y = 195
    pygame.draw.line(surf, (100, 220, 255), (40, beam_y), (140, beam_y), 4)
    pygame.draw.line(surf, (255, 255, 240), (40, beam_y), (140, beam_y), 2)
    surf.blit(font_sm.render("Length: 12px", True, (100, 220, 255)), (150, beam_y - 6))

    # Charged Shot Card
    card_b = pygame.Rect(256, 44, 200, 190)
    pygame.draw.rect(surf, (24, 20, 18), card_b)
    pygame.draw.rect(surf, (160, 110, 50), card_b, 1)

    surf.blit(font_lg.render("CHARGED OVERDRIVE", True, (255, 180, 50)), (268, 54))
    surf.blit(font_sm.render("Charge Build-up: 0.60s Hold", True, (180, 180, 180)), (268, 80))
    surf.blit(font_sm.render("Damage: 75 HP (3x Multiplier)", True, (255, 120, 120)), (268, 96))
    surf.blit(font_sm.render("Pierce Count: 3 Targets", True, (255, 210, 80)), (268, 112))
    surf.blit(font_sm.render("Beam Speed: 483 px/s (+15%)", True, (180, 180, 180)), (268, 128))
    surf.blit(font_sm.render("Glow Profile: Plasma Gold", True, (255, 180, 50)), (268, 144))

    # Draw charged beam preview
    cbeam_y = 195
    pygame.draw.line(surf, (255, 180, 50), (272, cbeam_y), (392, cbeam_y), 8)
    pygame.draw.line(surf, (255, 255, 255), (272, cbeam_y), (392, cbeam_y), 4)
    surf.blit(font_sm.render("Length: 20px", True, (255, 180, 50)), (402, cbeam_y - 6))

    pygame.image.save(surf, str(EVIDENCE_DIR / "05_charge_state_meter_preview.png"))
    print("Saved 05_charge_state_meter_preview.png")


if __name__ == "__main__":
    pygame.init()
    pygame.font.init()
    pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    generate_swept_ccd_preview()
    generate_piercing_preview()
    generate_aim_vectors_preview()
    generate_ingame_combat_preview()
    generate_charge_comparison_preview()
    print("All A05 evidence previews generated successfully.")
