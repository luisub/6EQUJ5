"""
MODULE: video_game/tools/generate_a06_evidence.py
PURPOSE: Generate high-resolution visual evidence previews for A06 enemy AI,
         predictive laser targeting, hound pounce arcs, cover absorption, and in-game encounter.
CALLED BY: Python execution during A06 verification.
HOW TO MODIFY: Update layout geometries or visual themes for subsequent combat milestones.
"""

import math
import os
from pathlib import Path
import pygame

from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.enemies import (
    STATE_ATTACK,
    STATE_PATROL,
    STATE_WINDUP,
    CoreReconDrone,
    EnemyManager,
    StaticHound,
)
from video_game.engine.player import Player, PlayerConfig, PlayerInput
from video_game.engine.scenes.field import FieldOpsScene
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.weapons import ProjectileManager, StarterMaser
from video_game.engine.world import Camera, Room

EVIDENCE_DIR = Path("video_game/planning/evidence/A06/previews")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def generate_enemy_roster_preview():
    """Preview 01: Enemy roster contact sheet showing Core Recon Drone and Static Hound."""
    surf = pygame.Surface((480, 270))
    surf.fill((12, 16, 22))

    font_lg = pygame.font.Font(None, 20)
    font_sm = pygame.font.Font(None, 14)

    header = font_lg.render("ACT I ENEMY ROSTER // CORE RECON DRONE & STATIC HOUND", True, (255, 210, 80))
    surf.blit(header, (16, 12))

    # Load sprites
    drone_dir = Path("video_game/assets/sprites/enemies/core_recon_drone")
    hound_dir = Path("video_game/assets/sprites/enemies/static_hound")

    # Section A: Core Recon Drone (Faction: The Core)
    y_drone = 45
    card_drone = pygame.Rect(16, y_drone, 448, 90)
    pygame.draw.rect(surf, (18, 24, 32), card_drone)
    pygame.draw.rect(surf, (45, 55, 72), card_drone, 1)

    surf.blit(font_lg.render("CORE RECON DRONE // PREDICTIVE TARGETING AUTOMATON", True, (255, 80, 80)), (28, y_drone + 8))
    surf.blit(font_sm.render("HP: 50 | Speed: 40 px/s | 1.2s Predictive Aim Lock | 20 DMG Pulse | Faction: The Core", True, (160, 180, 200)), (28, y_drone + 24))

    drone_poses = [
        ("patrol_1.png", "Patrol"),
        ("windup_1.png", "Windup"),
        ("attack.png", "Attack"),
        ("recovery.png", "Recovery"),
        ("hurt.png", "Hurt"),
        ("death.png", "Death"),
    ]
    for i, (fn, lbl) in enumerate(drone_poses):
        px = 36 + i * 70
        py = y_drone + 44
        sp_path = drone_dir / fn
        if sp_path.exists():
            sp = pygame.image.load(str(sp_path)).convert_alpha()
            scaled = pygame.transform.scale(sp, (48, 40))
            surf.blit(scaled, (px, py - 6))
        surf.blit(font_sm.render(lbl, True, (200, 210, 225)), (px + 4, py + 34))

    # Section B: Static Hound (Faction: The Static Hounds)
    y_hound = 150
    card_hound = pygame.Rect(16, y_hound, 448, 105)
    pygame.draw.rect(surf, (24, 20, 18), card_hound)
    pygame.draw.rect(surf, (160, 110, 50), card_hound, 1)

    surf.blit(font_lg.render("STATIC HOUND // CASSETTE-PUNK MECHANICAL SCAVENGER", True, (255, 168, 38)), (28, y_hound + 8))
    surf.blit(font_sm.render("HP: 75 | Speed: 60 px/s | 0.6s Static Arc Telegraph | 240 px/s Pounce (30 DMG) | Counter: Slide-Kick", True, (200, 180, 160)), (28, y_hound + 24))

    hound_poses = [
        ("patrol_1.png", "Patrol"),
        ("windup.png", "Windup"),
        ("pounce.png", "Pounce"),
        ("recovery.png", "Recovery"),
        ("hurt.png", "Hurt"),
        ("death.png", "Death"),
    ]
    for i, (fn, lbl) in enumerate(hound_poses):
        px = 30 + i * 72
        py = y_hound + 44
        sp_path = hound_dir / fn
        if sp_path.exists():
            sp = pygame.image.load(str(sp_path)).convert_alpha()
            scaled = pygame.transform.scale(sp, (64, 40))
            surf.blit(scaled, (px, py - 6))
        surf.blit(font_sm.render(lbl, True, (220, 200, 180)), (px + 10, py + 36))

    pygame.image.save(surf, str(EVIDENCE_DIR / "01_enemy_roster_contact_sheet.png"))
    print("Saved 01_enemy_roster_contact_sheet.png")


def generate_predictive_targeting_preview():
    """Preview 02: Predictive laser targeting, aim lock window, and dodge escape."""
    surf = pygame.Surface((480, 270))
    surf.fill((10, 14, 20))

    font_lg = pygame.font.Font(None, 20)
    font_sm = pygame.font.Font(None, 14)

    header = font_lg.render("PREDICTIVE LASER TARGETING // 0.3s AIM LOCK & DODGE ESCAPE WINDOW", True, (255, 210, 80))
    surf.blit(header, (16, 12))

    # Drone at x=380, y=70
    dx, dy = 380, 70
    pygame.draw.ellipse(surf, (45, 55, 72), (dx - 24, dy - 15, 48, 30))
    pygame.draw.circle(surf, (255, 30, 66), (dx, dy), 6)
    surf.blit(font_sm.render("Core Recon Drone", True, (255, 120, 120)), (dx - 40, dy - 28))

    # Phase 1: Tracking phase (t=0.0..0.9s)
    # Player at Tick 0 moving right
    p0 = (140, 160)
    pygame.draw.circle(surf, (100, 140, 255), p0, 6)
    surf.blit(font_sm.render("Mateo (t=0s)", True, (140, 180, 255)), (p0[0] - 25, p0[1] + 10))

    # Lead prediction vector
    p_pred = (220, 160)
    pygame.draw.line(surf, (100, 140, 255), p0, p_pred, 1)
    pygame.draw.circle(surf, (255, 210, 80), p_pred, 4)
    surf.blit(font_sm.render("Velocity Lead Vector (vx * 0.3s)", True, (255, 210, 80)), (130, 144))

    # Tracking laser (dashed/thin red)
    pygame.draw.line(surf, (255, 30, 66), (dx, dy), p_pred, 1)

    # Phase 2: Lock Window (t=0.9..1.2s, 0.3s duration)
    # Aim locks onto predicted spot p_pred
    crosshair_pos = p_pred
    pygame.draw.circle(surf, (255, 30, 66), crosshair_pos, 8, 1)
    pygame.draw.line(surf, (255, 255, 255), (crosshair_pos[0] - 12, crosshair_pos[1]), (crosshair_pos[0] + 12, crosshair_pos[1]), 1)
    pygame.draw.line(surf, (255, 255, 255), (crosshair_pos[0], crosshair_pos[1] - 12), (crosshair_pos[0], crosshair_pos[1] + 12), 1)

    # Solid intense red lock line
    pygame.draw.line(surf, (255, 30, 66), (dx, dy), (80, 185), 3)
    pygame.draw.line(surf, (255, 230, 230), (dx, dy), (80, 185), 1)

    # Phase 3: Player Dodge!
    # Player jumped or slid down to (220, 210)
    p_dodge = (220, 215)
    pygame.draw.circle(surf, (100, 255, 140), p_dodge, 8)
    pygame.draw.line(surf, (100, 255, 140), p_pred, p_dodge, 2)
    surf.blit(font_sm.render("DODGED POSITION [SAFE // 0 DMG]", True, (100, 255, 140)), (p_dodge[0] + 14, p_dodge[1] - 6))

    # Notes
    surf.blit(font_sm.render("1. TRACKING (0.9s): Drone predicts trajectory based on Mateo velocity", True, (180, 190, 200)), (24, 215))
    surf.blit(font_sm.render("2. AIM LOCK (0.3s): Laser locks in place with chime; dodge window active!", True, (255, 210, 80)), (24, 230))
    surf.blit(font_sm.render("3. DISCHARGE (t=1.2s): High-speed pulse fires along locked vector, missing dodged player", True, (100, 255, 140)), (24, 245))

    pygame.image.save(surf, str(EVIDENCE_DIR / "02_predictive_targeting_telegraph.png"))
    print("Saved 02_predictive_targeting_telegraph.png")


def generate_cover_occlusion_preview():
    """Preview 03: Wall occlusion, background concealment, and low sandbag absorption."""
    surf = pygame.Surface((480, 270))
    surf.fill((12, 16, 22))

    font_lg = pygame.font.Font(None, 20)
    font_sm = pygame.font.Font(None, 14)

    header = font_lg.render("TACTICAL COVER MECHANICS // WALL OCCLUSION & SANDBAG ABSORPTION", True, (255, 210, 80))
    surf.blit(header, (16, 12))

    # Ground line
    pygame.draw.line(surf, (60, 70, 80), (0, 220), (480, 220), 2)

    # Scenario 1: Solid Concrete Wall Occlusion (Left)
    wall_rect = pygame.Rect(110, 80, 24, 140)
    pygame.draw.rect(surf, (40, 48, 56), wall_rect)
    pygame.draw.rect(surf, (70, 85, 100), wall_rect, 1)
    surf.blit(font_sm.render("CONCRETE PIER", True, (160, 170, 180)), (90, 64))

    # Player behind wall at x=60
    pygame.draw.rect(surf, (100, 140, 255), (60, 188, 16, 32))
    surf.blit(font_sm.render("Mateo", True, (100, 140, 255)), (54, 172))

    # Occluded Ray
    pygame.draw.line(surf, (255, 60, 60), (200, 130), (134, 145), 1)
    pygame.draw.circle(surf, (255, 60, 60), (134, 145), 3)
    surf.blit(font_sm.render("LINE OF SIGHT BLOCKED", True, (255, 100, 100)), (36, 110))

    # Scenario 2: Background Doorway Recess (Center)
    alcove_rect = pygame.Rect(210, 160, 32, 60)
    pygame.draw.rect(surf, (18, 14, 24), alcove_rect)
    pygame.draw.rect(surf, (120, 80, 160), alcove_rect, 1)
    surf.blit(font_sm.render("ALCOVE RECESS", True, (200, 160, 255)), (190, 144))
    surf.blit(font_sm.render("[UP: CONCEAL]", True, (160, 130, 200)), (200, 226))

    # Scenario 3: Sandbag Low Cover (Right)
    sandbag_rect = pygame.Rect(320, 196, 28, 24)
    pygame.draw.rect(surf, (64, 52, 34), sandbag_rect)
    pygame.draw.rect(surf, (120, 100, 65), sandbag_rect, 1)
    surf.blit(font_sm.render("SANDBAG", True, (200, 180, 130)), (314, 180))

    # Crouched Mateo behind sandbag
    pygame.draw.rect(surf, (100, 140, 255), (298, 200, 16, 20))
    surf.blit(font_sm.render("Crouched", True, (100, 140, 255)), (286, 184))

    # Enemy Drone firing from right at x=440
    pygame.draw.circle(surf, (255, 30, 66), (430, 190), 6)
    surf.blit(font_sm.render("Core Drone", True, (255, 100, 100)), (400, 172))

    # Laser absorbed by sandbag
    pygame.draw.line(surf, (255, 30, 66), (430, 190), (348, 204), 3)
    pygame.draw.line(surf, (255, 230, 230), (430, 190), (348, 204), 1)

    # Sparks on sandbag
    for ang in [2.8, 3.2, 3.6, -2.8]:
        sx = 348 + math.cos(ang) * 8
        sy = 204 + math.sin(ang) * 8
        pygame.draw.line(surf, (255, 200, 80), (348, 204), (sx, sy), 1)

    surf.blit(font_sm.render("INCOMING LASER ABSORBED BY COVER", True, (255, 210, 80)), (270, 245))

    pygame.image.save(surf, str(EVIDENCE_DIR / "03_cover_and_line_of_sight_occlusion.png"))
    print("Saved 03_cover_and_line_of_sight_occlusion.png")


def generate_hound_pounce_preview():
    """Preview 04: Static Hound pounce arc vs Mateo slide-kick counter."""
    surf = pygame.Surface((480, 270))
    surf.fill((14, 18, 24))

    font_lg = pygame.font.Font(None, 20)
    font_sm = pygame.font.Font(None, 14)

    header = font_lg.render("TACTICAL COUNTER // STATIC HOUND POUNCE VS SLIDE-KICK BREACH", True, (255, 210, 80))
    surf.blit(header, (16, 12))

    # Ground plane
    pygame.draw.line(surf, (50, 60, 70), (0, 210), (480, 210), 2)

    # Hound Pounce Trajectory Arc (from x=360 down to x=180)
    arc_points = []
    for t_step in range(21):
        progress = t_step / 20.0
        hx = 360 - progress * 180
        # Parabolic leap: peak height at center
        hy = 190 - math.sin(progress * math.pi) * 45
        arc_points.append((hx, hy))

    pygame.draw.lines(surf, (255, 140, 40), False, arc_points, 2)
    surf.blit(font_sm.render("Hound Pounce Arc (240 px/s, 30 DMG)", True, (255, 168, 38)), (230, 120))

    # Hound in mid-leap at x=250, y=148
    hound_sp_path = Path("video_game/assets/sprites/enemies/static_hound/pounce.png")
    if hound_sp_path.exists():
        hsp = pygame.image.load(str(hound_sp_path)).convert_alpha()
        hsp_scaled = pygame.transform.scale(hsp, (64, 40))
        surf.blit(hsp_scaled, (218, 128))

    # Mateo Sliding underneath at x=200, y=196 (height = 14px)
    mateo_slide_rect = pygame.Rect(180, 196, 24, 14)
    pygame.draw.rect(surf, (100, 140, 255), mateo_slide_rect)
    surf.blit(font_sm.render("Mateo Tactical Slide (14px Height)", True, (140, 180, 255)), (110, 222))

    # Slide-kick hitbox extending forward
    kick_rect = pygame.Rect(204, 196, 16, 14)
    pygame.draw.rect(surf, (255, 210, 80), kick_rect, 1)

    # Hit sparks at connection point
    hit_pos = (212, 196)
    for ang in [0.2, 0.8, -0.4, 2.4, 3.1]:
        spx = hit_pos[0] + math.cos(ang) * 12
        spy = hit_pos[1] + math.sin(ang) * 12
        pygame.draw.line(surf, (255, 220, 80), hit_pos, (spx, spy), 1)

    surf.blit(font_sm.render("SLIDE-KICK CONNECTS (+35 DAMAGE TO HOUND)", True, (255, 210, 80)), (230, 185))
    surf.blit(font_sm.render("Hound leap clears over Mateo's low 14px profile -> Zero contact damage taken", True, (100, 255, 140)), (40, 248))

    pygame.image.save(surf, str(EVIDENCE_DIR / "04_hound_pounce_vs_slidekick.png"))
    print("Saved 04_hound_pounce_vs_slidekick.png")


def generate_ingame_encounter_preview():
    """Preview 05: In-engine CRT render of FieldOpsScene with active combat encounter."""
    pygame.init()
    crt = CRTRenderer(scale=config.DEFAULT_SCALE)
    machine = GameStateMachine(crt, development=True)

    field_scene = machine.scenes[config.STATE_FIELD_OPS]
    field_scene.player.x = 240.0
    field_scene.player.y = 192.0
    field_scene.player.facing = "right"
    field_scene.camera.snap_to(300.0, 180.0)

    # Position Drone in windup with aim lock
    if hasattr(field_scene, "enemy_manager") and field_scene.enemy_manager.enemies:
        for enemy in field_scene.enemy_manager.enemies:
            if isinstance(enemy, CoreReconDrone):
                enemy.x = 420.0
                enemy.y = 110.0
                enemy.state = STATE_WINDUP
                enemy.state_timer = 0.20  # Inside aim lock window
                enemy.telegraph_active = True
                enemy.telegraph_locked = True
                enemy.target_aim_pos = (248.0, 208.0)
                enemy.locked_aim_vector = (-0.88, 0.47)
            elif isinstance(enemy, StaticHound):
                enemy.x = 520.0
                enemy.y = 192.0
                enemy.state = STATE_PATROL

    # Render scene to CRT
    field_scene.render(crt)

    # Save native resolution surface
    pygame.image.save(crt.canvas, str(EVIDENCE_DIR / "05_ingame_encounter_preview.png"))
    print("Saved 05_ingame_encounter_preview.png")


if __name__ == "__main__":
    pygame.init()
    pygame.font.init()
    pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))

    generate_enemy_roster_preview()
    generate_predictive_targeting_preview()
    generate_cover_occlusion_preview()
    generate_hound_pounce_preview()
    generate_ingame_encounter_preview()
    print("All A06 evidence previews generated successfully.")

