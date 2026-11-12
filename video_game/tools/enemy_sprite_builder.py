"""
MODULE: video_game/tools/enemy_sprite_builder.py
PURPOSE: Generate authentic 16-bit pixel art sprite sheets and animation manifests
         for Core Recon Drones and Static Hounds.
CALLED BY: Asset generation scripts and tests.
HOW TO MODIFY: Update color palettes, chassis geometries, or frame definitions.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
import pygame

ENEMY_ASSETS_DIR = Path("video_game/assets/sprites/enemies")
DRONE_DIR = ENEMY_ASSETS_DIR / "core_recon_drone"
HOUND_DIR = ENEMY_ASSETS_DIR / "static_hound"

DRONE_DIR.mkdir(parents=True, exist_ok=True)
HOUND_DIR.mkdir(parents=True, exist_ok=True)


def create_drone_surface(state: str, frame_num: int = 1) -> pygame.Surface:
    """Generate 24x20 pixel art surface for Core Recon Drone."""
    surf = pygame.Surface((24, 20), pygame.SRCALPHA)

    # Color Palette
    CHASSIS_DARK = (24, 30, 40)
    CHASSIS_MID = (45, 55, 72)
    CHASSIS_LIGHT = (113, 128, 150)
    CHASSIS_HIGHLIGHT = (203, 213, 225)
    THRUSTER_CYAN = (56, 178, 172)
    EYE_CORE = (255, 230, 230)
    EYE_RED = (255, 30, 66)
    EYE_GLOW = (229, 62, 62)

    bob_y = 1 if frame_num % 2 == 0 else 0

    if state == "death":
        # Fractured debris / exploded drone
        pygame.draw.rect(surf, CHASSIS_MID, (4, 4 + bob_y, 6, 4))
        pygame.draw.rect(surf, CHASSIS_DARK, (14, 2 + bob_y, 7, 5))
        pygame.draw.rect(surf, CHASSIS_LIGHT, (8, 12 + bob_y, 8, 4))
        pygame.draw.rect(surf, (255, 200, 50), (10, 8 + bob_y, 4, 4))
        surf.set_at((6, 2), (255, 120, 50))
        surf.set_at((18, 14), (255, 60, 60))
        return surf

    if state == "hurt":
        # Glitched / flashing white-red
        surf.fill((0, 0, 0, 0))
        pygame.draw.ellipse(surf, (255, 255, 255), (2, 3 + bob_y, 20, 12))
        pygame.draw.rect(surf, EYE_RED, (8, 7 + bob_y, 8, 4))
        return surf

    # 1. Main Dish Chassis (20 x 10 oval)
    pygame.draw.ellipse(surf, CHASSIS_DARK, (2, 3 + bob_y, 20, 11))
    pygame.draw.ellipse(surf, CHASSIS_MID, (3, 4 + bob_y, 18, 9))
    pygame.draw.ellipse(surf, CHASSIS_LIGHT, (4, 4 + bob_y, 16, 6))
    pygame.draw.line(surf, CHASSIS_HIGHLIGHT, (7, 4 + bob_y), (16, 4 + bob_y), 1)

    # 2. Stabilizer Thrusters (lateral pods)
    # Left pod
    pygame.draw.rect(surf, CHASSIS_DARK, (1, 6 + bob_y, 3, 5))
    pygame.draw.rect(surf, CHASSIS_MID, (1, 7 + bob_y, 2, 3))
    # Right pod
    pygame.draw.rect(surf, CHASSIS_DARK, (20, 6 + bob_y, 3, 5))
    pygame.draw.rect(surf, CHASSIS_MID, (21, 7 + bob_y, 2, 3))

    # Thruster exhaust flame
    thruster_col = THRUSTER_CYAN if state != "recovery" else (30, 60, 60)
    surf.set_at((2, 11 + bob_y), thruster_col)
    surf.set_at((21, 11 + bob_y), thruster_col)
    if frame_num == 2 and state != "recovery":
        surf.set_at((2, 12 + bob_y), (129, 230, 217))
        surf.set_at((21, 12 + bob_y), (129, 230, 217))

    # 3. Optical Sensor Eye & Emitter (Center)
    if state in ("windup", "attack"):
        # Dilated / flaring red eye
        pygame.draw.circle(surf, EYE_GLOW, (12, 8 + bob_y), 4)
        pygame.draw.circle(surf, EYE_RED, (12, 8 + bob_y), 3)
        pygame.draw.circle(surf, EYE_CORE, (12, 8 + bob_y), 1)
        # Laser emitter barrel tip
        pygame.draw.rect(surf, (255, 100, 100), (11, 12 + bob_y, 2, 3))
        if state == "attack":
            # Muzzle flash spark
            pygame.draw.line(surf, (255, 255, 255), (12, 14 + bob_y), (12, 17 + bob_y), 2)
    elif state == "recovery":
        # Dimmed optic
        pygame.draw.rect(surf, (120, 30, 30), (10, 7 + bob_y, 4, 3))
        surf.set_at((12, 8 + bob_y), (180, 50, 50))
    else:
        # Standard patrol optic
        pygame.draw.rect(surf, EYE_GLOW, (10, 7 + bob_y, 4, 3))
        pygame.draw.rect(surf, EYE_RED, (11, 7 + bob_y, 2, 3))
        surf.set_at((12, 8 + bob_y), EYE_CORE)

    # Undercarriage antenna / probe
    pygame.draw.line(surf, CHASSIS_DARK, (12, 12 + bob_y), (12, 15 + bob_y), 1)

    return surf


def create_hound_surface(state: str, frame_num: int = 1) -> pygame.Surface:
    """Generate 32x20 pixel art surface for Static Hound."""
    surf = pygame.Surface((32, 20), pygame.SRCALPHA)

    # Color Palette
    METAL_DARK = (30, 35, 42)
    METAL_MID = (55, 65, 81)
    METAL_LIGHT = (107, 114, 128)
    RUST_BRONZE = (139, 90, 43)
    AMBER_EYE = (255, 168, 38)
    EYE_CORE = (255, 235, 180)
    ELECTRIC_BLUE = (96, 165, 250)

    if state == "death":
        # Collapsed scrap chassis
        pygame.draw.rect(surf, METAL_DARK, (4, 14, 24, 5))
        pygame.draw.rect(surf, METAL_MID, (8, 12, 14, 4))
        pygame.draw.rect(surf, RUST_BRONZE, (10, 10, 8, 3))
        surf.set_at((26, 13), (60, 60, 60))  # Dead eye
        return surf

    if state == "hurt":
        # Recoil flash
        surf.fill((0, 0, 0, 0))
        pygame.draw.rect(surf, (255, 255, 255), (4, 4, 24, 12))
        pygame.draw.rect(surf, AMBER_EYE, (22, 6, 6, 4))
        return surf

    if state == "pounce":
        # Elongated airborne leaping posture
        # Head / Jaw extended forward
        pygame.draw.rect(surf, METAL_DARK, (22, 4, 8, 7))
        pygame.draw.rect(surf, METAL_MID, (24, 5, 6, 4))
        # Spiked scrap collar
        pygame.draw.rect(surf, RUST_BRONZE, (20, 4, 3, 8))
        surf.set_at((21, 3), (200, 160, 100))
        # Eye visor
        pygame.draw.rect(surf, (255, 60, 60), (26, 5, 4, 2))
        surf.set_at((28, 5), EYE_CORE)
        # Jaws open
        surf.set_at((29, 9), (220, 220, 220))
        surf.set_at((30, 10), (220, 220, 220))

        # Torso / Tape-deck Battery
        pygame.draw.rect(surf, METAL_DARK, (10, 6, 12, 7))
        pygame.draw.rect(surf, RUST_BRONZE, (12, 4, 7, 3))
        surf.set_at((14, 5), (40, 40, 40))  # Cassette spool

        # Outstretched front legs
        pygame.draw.line(surf, METAL_LIGHT, (19, 12), (26, 17), 2)
        # Trailing hind legs
        pygame.draw.line(surf, METAL_LIGHT, (11, 11), (3, 16), 2)
        # Spines / Static spark
        surf.set_at((15, 3), ELECTRIC_BLUE)
        surf.set_at((17, 2), (255, 255, 255))
        return surf

    if state == "windup":
        # Crouched / coiled ready to pounce
        # Lowered body
        pygame.draw.rect(surf, METAL_DARK, (8, 7, 14, 8))
        pygame.draw.rect(surf, METAL_MID, (9, 8, 12, 6))
        # Battery on back
        pygame.draw.rect(surf, RUST_BRONZE, (10, 5, 8, 3))
        # Lowered Head
        pygame.draw.rect(surf, METAL_DARK, (20, 8, 7, 7))
        pygame.draw.rect(surf, METAL_MID, (21, 9, 5, 4))
        # Flaring red-amber eye
        pygame.draw.rect(surf, (255, 80, 40), (23, 9, 4, 3))
        surf.set_at((25, 10), (255, 255, 200))
        # Spines / Electric telegraph arcs
        pygame.draw.line(surf, ELECTRIC_BLUE, (12, 3), (14, 5), 1)
        pygame.draw.line(surf, ELECTRIC_BLUE, (16, 2), (18, 5), 1)
        surf.set_at((15, 2), (255, 255, 255))

        # Coiled limbs
        pygame.draw.line(surf, METAL_LIGHT, (10, 14), (6, 18), 2)
        pygame.draw.line(surf, METAL_LIGHT, (18, 14), (16, 18), 2)
        return surf

    # Standard Patrol / Recovery
    leg_offset = 2 if frame_num == 2 else 0

    # 1. Torso & Scavenged Battery Pack
    pygame.draw.rect(surf, METAL_DARK, (7, 6, 14, 7))
    pygame.draw.rect(surf, METAL_MID, (8, 7, 12, 5))
    # Walkman / Tape deck pack on back
    pygame.draw.rect(surf, RUST_BRONZE, (9, 4, 8, 3))
    surf.set_at((11, 5), (30, 30, 30))
    surf.set_at((14, 5), (30, 30, 30))

    # 2. Spiked Scrap Collar
    pygame.draw.rect(surf, RUST_BRONZE, (19, 5, 2, 7))
    surf.set_at((20, 4), (200, 160, 100))

    # 3. Head & Optic Visor
    pygame.draw.rect(surf, METAL_DARK, (20, 5, 8, 6))
    pygame.draw.rect(surf, METAL_MID, (21, 6, 6, 4))
    eye_col = AMBER_EYE if state != "recovery" else (140, 90, 20)
    pygame.draw.rect(surf, eye_col, (24, 6, 3, 2))
    surf.set_at((25, 6), EYE_CORE)

    # 4. Articulated Piston Legs
    # Front leg
    fx = 18 - leg_offset
    pygame.draw.line(surf, METAL_LIGHT, (19, 12), (fx, 18), 2)
    # Hind leg
    hx = 8 + leg_offset
    pygame.draw.line(surf, METAL_LIGHT, (9, 12), (hx, 18), 2)

    # Tail antenna wire
    pygame.draw.line(surf, METAL_DARK, (7, 8), (3, 5), 1)
    surf.set_at((3, 4), (200, 100, 50))

    return surf


def build_all_enemy_sprites():
    """Render and export all individual sprite PNGs and build manifest.json."""
    drone_frames = {
        "patrol_1": create_drone_surface("patrol", 1),
        "patrol_2": create_drone_surface("patrol", 2),
        "windup_1": create_drone_surface("windup", 1),
        "windup_2": create_drone_surface("windup", 2),
        "attack": create_drone_surface("attack", 1),
        "recovery": create_drone_surface("recovery", 1),
        "hurt": create_drone_surface("hurt", 1),
        "death": create_drone_surface("death", 1),
    }

    for name, surf in drone_frames.items():
        out_path = DRONE_DIR / f"{name}.png"
        pygame.image.save(surf, str(out_path))
        print(f"Exported {out_path}")

    hound_frames = {
        "patrol_1": create_hound_surface("patrol", 1),
        "patrol_2": create_hound_surface("patrol", 2),
        "windup": create_hound_surface("windup", 1),
        "pounce": create_hound_surface("pounce", 1),
        "recovery": create_hound_surface("recovery", 1),
        "hurt": create_hound_surface("hurt", 1),
        "death": create_hound_surface("death", 1),
    }

    for name, surf in hound_frames.items():
        out_path = HOUND_DIR / f"{name}.png"
        pygame.image.save(surf, str(out_path))
        print(f"Exported {out_path}")

    # Build manifest.json
    manifest = {
        "schema_version": 1,
        "enemies": {
            "core_recon_drone": {
                "name": "Core Recon Drone",
                "width": 24,
                "height": 20,
                "origin": [12, 10],
                "attachment_points": {
                    "laser_emitter": [12, 14],
                    "sensor_eye": [12, 8]
                },
                "animations": {
                    "patrol": {
                        "frames": ["sprites/enemies/core_recon_drone/patrol_1.png", "sprites/enemies/core_recon_drone/patrol_2.png"],
                        "frame_duration_ms": 250,
                        "loop": True
                    },
                    "windup": {
                        "frames": ["sprites/enemies/core_recon_drone/windup_1.png", "sprites/enemies/core_recon_drone/windup_2.png"],
                        "frame_duration_ms": 150,
                        "loop": True
                    },
                    "attack": {
                        "frames": ["sprites/enemies/core_recon_drone/attack.png"],
                        "frame_duration_ms": 200,
                        "loop": False
                    },
                    "recovery": {
                        "frames": ["sprites/enemies/core_recon_drone/recovery.png"],
                        "frame_duration_ms": 400,
                        "loop": False
                    },
                    "hurt": {
                        "frames": ["sprites/enemies/core_recon_drone/hurt.png"],
                        "frame_duration_ms": 120,
                        "loop": False
                    },
                    "death": {
                        "frames": ["sprites/enemies/core_recon_drone/death.png"],
                        "frame_duration_ms": 500,
                        "loop": False
                    }
                }
            },
            "static_hound": {
                "name": "Static Hound",
                "width": 32,
                "height": 20,
                "origin": [16, 18],
                "attachment_points": {
                    "jaw": [28, 9],
                    "optic_visor": [25, 6],
                    "spine_pack": [13, 5]
                },
                "animations": {
                    "patrol": {
                        "frames": ["sprites/enemies/static_hound/patrol_1.png", "sprites/enemies/static_hound/patrol_2.png"],
                        "frame_duration_ms": 200,
                        "loop": True
                    },
                    "windup": {
                        "frames": ["sprites/enemies/static_hound/windup.png"],
                        "frame_duration_ms": 300,
                        "loop": True
                    },
                    "attack": {
                        "frames": ["sprites/enemies/static_hound/pounce.png"],
                        "frame_duration_ms": 400,
                        "loop": False
                    },
                    "recovery": {
                        "frames": ["sprites/enemies/static_hound/recovery.png"],
                        "frame_duration_ms": 500,
                        "loop": False
                    },
                    "hurt": {
                        "frames": ["sprites/enemies/static_hound/hurt.png"],
                        "frame_duration_ms": 120,
                        "loop": False
                    },
                    "death": {
                        "frames": ["sprites/enemies/static_hound/death.png"],
                        "frame_duration_ms": 500,
                        "loop": False
                    }
                }
            }
        }
    }

    manifest_path = ENEMY_ASSETS_DIR / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Exported {manifest_path}")


if __name__ == "__main__":
    pygame.init()
    build_all_enemy_sprites()
    print("Enemy sprites built successfully.")

