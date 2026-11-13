"""
MODULE: tools/boss_sprite_builder.py
PURPOSE: Generate authentic 16-bit pixel art sprite frames and animation manifests
         for Act I Culminating Boss Core Warden Greenkeeper.
CALLED BY: Asset generation scripts, game engine startup, and unit tests.
HOW TO MODIFY: Update color palettes, chassis geometries, or frame definitions.
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Tuple
import pygame

REPO_ROOT = Path(__file__).resolve().parent.parent
BOSS_ASSETS_DIR = REPO_ROOT / "src" / "assets" / "sprites" / "bosses" / "greenkeeper"
BOSS_ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def create_greenkeeper_surface(state: str, frame_num: int = 1) -> pygame.Surface:
    """
    Generate 64x48 pixel art surface for Core Warden Greenkeeper.
    Features heavy excavator treads, riveted armor, scoop blade, mortar turret, and reactor core.
    """
    surf = pygame.Surface((64, 48), pygame.SRCALPHA)

    # 16-bit Color Palette
    # Tread & Iron
    TREAD_BLACK = (14, 18, 22)
    TREAD_DARK = (24, 30, 36)
    TREAD_MID = (44, 56, 68)
    TREAD_LIGHT = (82, 100, 118)
    TREAD_PIN = (130, 150, 170)

    # Chassis Armored Steel (Weathered Industrial Olive/Slate)
    ARMOR_DARK = (22, 32, 30)
    ARMOR_MID = (38, 52, 48)
    ARMOR_LIGHT = (62, 84, 76)
    ARMOR_HILITE = (98, 128, 116)
    ARMOR_RIVET = (145, 175, 160)

    # Hydraulic Cylinders & Steel Trim
    STEEL_DARK = (30, 36, 44)
    STEEL_MID = (65, 78, 92)
    STEEL_LIGHT = (120, 140, 160)
    STEEL_CHROME = (200, 220, 235)

    # Hazard & Optical Sensors
    HAZARD_YELLOW = (235, 170, 35)
    HAZARD_DARK = (80, 55, 10)
    SENSOR_RED = (245, 42, 42)
    SENSOR_GLOW = (255, 120, 120)

    # Molten Core / Weak Point
    CORE_DEEP = (160, 28, 18)
    CORE_AMBER = (255, 130, 24)
    CORE_HOT = (255, 215, 75)
    CORE_WHITE = (255, 250, 220)

    bob_y = 1 if (frame_num % 2 == 0 and state in ("idle", "charge")) else 0

    if state == "defeated":
        # Wrecked, smoking excavator carcass with shattered plating
        # Crushed treads
        pygame.draw.rect(surf, TREAD_BLACK, (2, 38, 60, 10))
        pygame.draw.rect(surf, TREAD_DARK, (4, 40, 56, 6))
        # Buckled hull
        pygame.draw.polygon(surf, ARMOR_DARK, [(6, 38), (14, 24), (58, 28), (62, 38)])
        pygame.draw.polygon(surf, ARMOR_MID, [(12, 34), (16, 26), (54, 30), (58, 36)])
        # Detached hanging plow blade
        pygame.draw.polygon(surf, STEEL_MID, [(-2, 40), (8, 32), (10, 46), (0, 46)])
        # Ruptured smoking core
        pygame.draw.circle(surf, (40, 20, 15), (36, 26), 6)
        surf.set_at((36, 26), (255, 100, 30))
        surf.set_at((35, 25), (255, 200, 80))
        surf.set_at((37, 24), (120, 120, 130))  # smoke
        surf.set_at((38, 22), (90, 90, 100))
        return surf

    if state == "hurt":
        # Electrical damage flash strobe
        pygame.draw.rect(surf, (255, 255, 255), (2, 10, 60, 38))
        pygame.draw.rect(surf, SENSOR_RED, (6, 14, 52, 28))
        pygame.draw.rect(surf, (255, 240, 200), (22, 18, 22, 16))
        return surf

    # -----------------------------------------------------------------
    # 1. Tank Treads (Bottom 12px: y=36..47)
    # -----------------------------------------------------------------
    tread_y = 36 + bob_y
    # Outer rubber/steel tread housing
    pygame.draw.rect(surf, TREAD_BLACK, (2, tread_y, 60, 11), border_radius=3)
    pygame.draw.rect(surf, TREAD_DARK, (3, tread_y + 1, 58, 9), border_radius=2)

    # Road wheels / guide idler sprockets (5 large wheels)
    wheel_x_positions = [8, 20, 32, 44, 56]
    wheel_offset = (frame_num * 2) if state == "charge" else (frame_num % 2)
    for wx in wheel_x_positions:
        # Outer rim
        pygame.draw.circle(surf, TREAD_MID, (wx, tread_y + 5), 4)
        pygame.draw.circle(surf, TREAD_BLACK, (wx, tread_y + 5), 3)
        # Center axle hub
        pygame.draw.circle(surf, STEEL_CHROME, (wx, tread_y + 5), 1)
        # Rotating tread tooth / spoke marker
        spoke_angle = wheel_offset * 1.57
        sx = int(wx + 2.5 * math.cos(spoke_angle))
        sy = int(tread_y + 5 + 2.5 * math.sin(spoke_angle))
        surf.set_at((sx, sy), TREAD_LIGHT)

    # Track links top/bottom treads
    track_shift = (frame_num * 3) % 4 if state == "charge" else (frame_num % 2)
    for tx in range(3, 60, 4):
        px = (tx + track_shift) % 57 + 3
        # Upper track link
        surf.set_at((px, tread_y), TREAD_LIGHT)
        surf.set_at((px, tread_y + 1), TREAD_MID)
        # Lower track contact tooth
        surf.set_at((px, tread_y + 10), TREAD_PIN)

    # Mud skirt / tread armor guard plate
    pygame.draw.rect(surf, ARMOR_DARK, (2, tread_y - 1, 60, 3))
    pygame.draw.line(surf, ARMOR_LIGHT, (2, tread_y - 1), (61, tread_y - 1), 1)

    # -----------------------------------------------------------------
    # 2. Main Armored Hull / Excavator Chassis (y=16..35)
    # -----------------------------------------------------------------
    body_y = 16 + bob_y
    # Heavy angled sloped armor plate
    pygame.draw.polygon(surf, ARMOR_DARK, [
        (8, body_y + 19),
        (12, body_y + 4),
        (22, body_y),
        (58, body_y),
        (62, body_y + 8),
        (62, body_y + 19),
    ])
    pygame.draw.polygon(surf, ARMOR_MID, [
        (9, body_y + 18),
        (13, body_y + 5),
        (22, body_y + 1),
        (57, body_y + 1),
        (61, body_y + 8),
        (61, body_y + 18),
    ])

    # Top highlight bevel
    pygame.draw.line(surf, ARMOR_HILITE, (22, body_y + 1), (57, body_y + 1), 1)
    pygame.draw.line(surf, ARMOR_HILITE, (13, body_y + 5), (22, body_y + 1), 1)

    # Armor plating seams and structural rivets
    pygame.draw.line(surf, ARMOR_DARK, (36, body_y + 2), (36, body_y + 18), 1)
    pygame.draw.line(surf, ARMOR_HILITE, (37, body_y + 2), (37, body_y + 18), 1)
    for ry in [body_y + 4, body_y + 10, body_y + 16]:
        surf.set_at((14, ry), ARMOR_RIVET)
        surf.set_at((59, ry), ARMOR_RIVET)

    # Hazard caution stripes on lower hull flank
    for hx in range(16, 34, 4):
        pygame.draw.line(surf, HAZARD_YELLOW, (hx, body_y + 14), (hx + 2, body_y + 18), 1)
        pygame.draw.line(surf, HAZARD_DARK, (hx + 2, body_y + 14), (hx + 4, body_y + 18), 1)

    # -----------------------------------------------------------------
    # 3. Heavy Excavator Scoop / Cowcatcher Plow (Left facing: x=-4..14)
    # -----------------------------------------------------------------
    scoop_y = 18 + (2 if state == "charge" else bob_y)
    # Triangular hardened blade
    scoop_points = [
        (0, scoop_y + 6),
        (12, scoop_y),
        (14, scoop_y + 24),
        (-2, scoop_y + 24),
    ]
    pygame.draw.polygon(surf, STEEL_DARK, scoop_points)
    pygame.draw.polygon(surf, STEEL_MID, [
        (1, scoop_y + 7),
        (11, scoop_y + 1),
        (13, scoop_y + 23),
        (-1, scoop_y + 23),
    ])
    # Beveled cutting edge
    pygame.draw.line(surf, STEEL_CHROME, (0, scoop_y + 6), (-2, scoop_y + 24), 2)
    # Serrated plow teeth at base
    for tooth_x in [-2, 2, 6, 10]:
        pygame.draw.polygon(surf, STEEL_CHROME, [
            (tooth_x, scoop_y + 24),
            (tooth_x + 2, scoop_y + 27),
            (tooth_x + 4, scoop_y + 24),
        ])
    # Heavy hydraulic ram connecting scoop to chassis
    pygame.draw.line(surf, STEEL_DARK, (10, scoop_y + 8), (20, body_y + 12), 3)
    pygame.draw.line(surf, STEEL_CHROME, (12, scoop_y + 9), (18, body_y + 11), 1)

    # -----------------------------------------------------------------
    # 4. Top Parabolic Mortar Turret Assembly (x=20..56, y=0..16)
    # -----------------------------------------------------------------
    turret_y = 3 + bob_y
    # Turret base pedestal
    pygame.draw.rect(surf, STEEL_DARK, (38, turret_y + 9, 18, 5))
    pygame.draw.rect(surf, STEEL_MID, (39, turret_y + 10, 16, 3))

    if state in ("mortar", "mortar_fire"):
        # Elevated high-angle artillery position
        # Recoil displacement
        recoil = 3 if state == "mortar_fire" else 0
        barrel_start = (48 + recoil, turret_y + 10)
        barrel_end = (32 + recoil, turret_y - 2)
        # Heavy rifled barrel tube
        pygame.draw.line(surf, STEEL_DARK, (barrel_start[0], barrel_start[1] + 1), (barrel_end[0], barrel_end[1] + 1), 6)
        pygame.draw.line(surf, STEEL_MID, barrel_start, barrel_end, 4)
        pygame.draw.line(surf, STEEL_CHROME, (barrel_start[0] - 1, barrel_start[1] - 1), (barrel_end[0] - 1, barrel_end[1] - 1), 1)
        # Muzzle brake
        pygame.draw.circle(surf, STEEL_DARK, barrel_end, 4)
        pygame.draw.circle(surf, STEEL_LIGHT, barrel_end, 2)
        if state == "mortar_fire":
            # Fiery blast muzzle flash
            pygame.draw.circle(surf, CORE_WHITE, (barrel_end[0] - 3, barrel_end[1] - 3), 4)
            pygame.draw.circle(surf, CORE_AMBER, (barrel_end[0] - 5, barrel_end[1] - 5), 7)
            pygame.draw.circle(surf, SENSOR_RED, (barrel_end[0] - 7, barrel_end[1] - 7), 9)
    else:
        # Standard travel / low-angle mortar turret position
        barrel_start = (48, turret_y + 9)
        barrel_end = (30, turret_y + 1)
        pygame.draw.line(surf, STEEL_DARK, (barrel_start[0], barrel_start[1] + 1), (barrel_end[0], barrel_end[1] + 1), 5)
        pygame.draw.line(surf, STEEL_MID, barrel_start, barrel_end, 3)
        pygame.draw.line(surf, STEEL_CHROME, barrel_start, barrel_end, 1)
        # Muzzle collar
        pygame.draw.circle(surf, STEEL_DARK, barrel_end, 3)
        pygame.draw.circle(surf, STEEL_LIGHT, barrel_end, 1)

    # Targeting sensor eye / optics turret (Left side of mortar)
    pygame.draw.rect(surf, ARMOR_DARK, (26, turret_y + 8, 8, 6), border_radius=1)
    pygame.draw.rect(surf, ARMOR_MID, (27, turret_y + 9, 6, 4))
    eye_col = SENSOR_RED if (frame_num % 2 == 0 or state == "charge") else SENSOR_GLOW
    surf.set_at((29, turret_y + 10), eye_col)
    surf.set_at((30, turret_y + 10), SENSOR_RED)

    # Dual diesel exhaust manifolds on rear deck (x=54..60)
    for ex in [54, 58]:
        pygame.draw.rect(surf, STEEL_DARK, (ex, turret_y + 2, 3, 9))
        pygame.draw.rect(surf, STEEL_MID, (ex, turret_y + 2, 2, 8))
        surf.set_at((ex + 1, turret_y + 1), STEEL_CHROME)
        if state == "charge":
            # Dark soot particulate
            surf.set_at((ex + 1, turret_y - 1), (40, 40, 45))
            surf.set_at((ex + 2, turret_y - 2), (60, 60, 70))

    # -----------------------------------------------------------------
    # 5. Core Weak Point (Reactor Housing at x=22..46, y=14..32)
    # -----------------------------------------------------------------
    core_rect = (24, body_y + 2, 20, 16)
    if state in ("vulnerable", "vulnerable_open"):
        # Cowl raised open - superheated pulsing reactor core exposed!
        # Prop rod / open hatch flap
        pygame.draw.line(surf, ARMOR_DARK, (24, body_y + 2), (20, body_y - 6), 3)
        pygame.draw.line(surf, ARMOR_LIGHT, (24, body_y + 1), (20, body_y - 5), 1)
        pygame.draw.line(surf, STEEL_CHROME, (22, body_y + 4), (22, body_y - 2), 1)

        # Core chamber cavity
        pygame.draw.rect(surf, (20, 10, 8), core_rect)
        # Pulsing molten core layers
        pulse = 1 if frame_num % 2 == 0 else 0
        pygame.draw.ellipse(surf, CORE_DEEP, (26 - pulse, body_y + 4, 16 + pulse * 2, 12))
        pygame.draw.ellipse(surf, CORE_AMBER, (28, body_y + 6, 12, 8))
        pygame.draw.ellipse(surf, CORE_HOT, (30, body_y + 7, 8, 6))
        pygame.draw.circle(surf, CORE_WHITE, (34, body_y + 10), 2)

        # Cooling manifold lattice / thermal venting sparks
        for gx in [27, 31, 35, 39]:
            pygame.draw.line(surf, CORE_HOT, (gx, body_y + 3), (gx, body_y + 16), 1)
        # Thermal glow bleed
        surf.set_at((33, body_y + 1), CORE_AMBER)
        surf.set_at((35, body_y + 1), CORE_HOT)
    else:
        # Armored Cowl closed - reinforced shielding with warning chevrons
        pygame.draw.rect(surf, ARMOR_DARK, core_rect)
        pygame.draw.rect(surf, ARMOR_MID, (25, body_y + 3, 18, 14))
        pygame.draw.rect(surf, ARMOR_LIGHT, (26, body_y + 4, 16, 12))
        # Central lock clamp
        pygame.draw.rect(surf, STEEL_DARK, (31, body_y + 7, 6, 6))
        pygame.draw.rect(surf, STEEL_CHROME, (32, body_y + 8, 4, 4))
        # Warning radiation emblem stencil
        surf.set_at((34, body_y + 10), HAZARD_YELLOW)

    # -----------------------------------------------------------------
    # 6. Lower Sweep Beam Emitter (x=8..18, y=30..36)
    # -----------------------------------------------------------------
    if state in ("sweep", "sweep_charge"):
        # Plasma cutter aperture open and glowing intensely
        pygame.draw.rect(surf, STEEL_CHROME, (8, body_y + 14, 8, 4))
        pygame.draw.rect(surf, SENSOR_RED, (10, body_y + 15, 6, 2))
        surf.set_at((12, body_y + 16), CORE_WHITE)
        surf.set_at((13, body_y + 16), CORE_WHITE)

    return surf


def build_all_greenkeeper_sprites():
    """Render and export all individual sprite PNGs and write manifest.json."""
    frames = {
        "idle_1": create_greenkeeper_surface("idle", 1),
        "idle_2": create_greenkeeper_surface("idle", 2),
        "charge_1": create_greenkeeper_surface("charge", 1),
        "charge_2": create_greenkeeper_surface("charge", 2),
        "mortar_aim": create_greenkeeper_surface("mortar", 1),
        "mortar_fire": create_greenkeeper_surface("mortar_fire", 1),
        "sweep_charge": create_greenkeeper_surface("sweep_charge", 1),
        "vulnerable_1": create_greenkeeper_surface("vulnerable", 1),
        "vulnerable_2": create_greenkeeper_surface("vulnerable", 2),
        "hurt": create_greenkeeper_surface("hurt", 1),
        "defeated": create_greenkeeper_surface("defeated", 1),
    }

    manifest = {
        "schema_version": 1,
        "boss_id": "greenkeeper_act_01",
        "name": "Core Warden Greenkeeper",
        "native_size": [64, 48],
        "frames": {},
        "animations": {
            "idle": ["idle_1", "idle_2"],
            "charge": ["charge_1", "charge_2"],
            "mortar": ["mortar_aim", "mortar_fire"],
            "sweep": ["sweep_charge"],
            "vulnerable": ["vulnerable_1", "vulnerable_2"],
            "hurt": ["hurt"],
            "defeated": ["defeated"],
        },
    }

    for name, surf in frames.items():
        out_path = BOSS_ASSETS_DIR / f"{name}.png"
        pygame.image.save(surf, str(out_path))
        manifest["frames"][name] = f"{name}.png"
        print(f"Exported Greenkeeper boss frame: {out_path.name}")

    manifest_path = BOSS_ASSETS_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote boss manifest: {manifest_path}")


if __name__ == "__main__":
    pygame.init()
    build_all_greenkeeper_sprites()

