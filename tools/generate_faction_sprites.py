"""
MODULE: tools/generate_faction_sprites.py
PURPOSE: Procedurally synthesize native pixel-art sprite frames and manifests for all S09 hostile factions.
CALLED BY: CLI execution during build or asset verification.
HOW TO MODIFY: Adjust palettes or pixel clusters; maintain zero wildcard imports.
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw

SPRITES_DIR = Path(__file__).resolve().parent.parent / "src" / "assets" / "sprites" / "enemies"


def create_frame(w: int, h: int, draw_fn) -> Image.Image:
    """Create a new transparent RGBA image and invoke drawing callback."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw_fn(draw, w, h)
    return img


def generate_core_enforcer():
    out_dir = SPRITES_DIR / "core_enforcer"
    out_dir.mkdir(parents=True, exist_ok=True)
    w, h = 24, 32

    # Colors
    c_armor = (192, 216, 240, 255)
    c_armor_dark = (120, 145, 175, 255)
    c_metal = (35, 45, 55, 255)
    c_eye = (0, 240, 255, 255)
    c_red = (255, 30, 66, 255)

    def draw_base(draw, leg_offset=0, arm_up=False, hurt=False):
        # Legs
        draw.rectangle([6, 20, 9, 30 + leg_offset], fill=c_metal)
        draw.rectangle([14, 20, 17, 30 - leg_offset], fill=c_metal)
        draw.rectangle([5, 30 + leg_offset, 10, 31], fill=c_armor_dark)
        draw.rectangle([13, 30 - leg_offset, 18, 31], fill=c_armor_dark)

        # Torso & Heavy Armor Plate
        draw.rectangle([5, 10, 18, 20], fill=c_metal)
        draw.rectangle([6, 11, 17, 19], fill=c_armor)
        draw.line([(6, 15), (17, 15)], fill=c_armor_dark)

        # Head / Optic Visor
        draw.rectangle([7, 3, 16, 9], fill=c_armor)
        if hurt:
            draw.line([(8, 6), (15, 6)], fill=(255, 200, 50, 255))
        else:
            draw.line([(8, 6), (15, 6)], fill=c_eye)

        # Arms & Heavy Weapon
        if arm_up:
            draw.rectangle([17, 8, 23, 14], fill=c_metal)
            draw.rectangle([19, 10, 24, 12], fill=c_armor_dark)
            draw.point((23, 9), fill=c_red)
        else:
            draw.rectangle([17, 12, 21, 20], fill=c_metal)
            draw.rectangle([18, 14, 22, 18], fill=c_armor_dark)

    create_frame(w, h, lambda d, w, h: draw_base(d, 0, False)).save(out_dir / "patrol_1.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, 1, False)).save(out_dir / "patrol_2.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, 0, True)).save(out_dir / "windup.png")
    create_frame(w, h, lambda d, w, h: (draw_base(d, 0, True), d.line([(23, 11), (24, 11)], fill=c_eye))).save(out_dir / "attack.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, 0, False)).save(out_dir / "recovery.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, -1, False, hurt=True)).save(out_dir / "hurt.png")
    create_frame(w, h, lambda d, w, h: d.rectangle([4, 24, 20, 31], fill=c_armor_dark)).save(out_dir / "death.png")


def generate_core_operative():
    out_dir = SPRITES_DIR / "core_operative"
    out_dir.mkdir(parents=True, exist_ok=True)
    w, h = 20, 32

    c_suit = (40, 48, 56, 255)
    c_suit_light = (70, 85, 100, 255)
    c_visor = (255, 30, 66, 255)
    c_glow = (65, 195, 245, 255)

    def draw_base(draw, step=0, aim=False, hurt=False):
        # Legs
        draw.rectangle([4, 19, 7, 30 + step], fill=c_suit)
        draw.rectangle([11, 19, 14, 30 - step], fill=c_suit)

        # Torso
        draw.rectangle([4, 9, 14, 19], fill=c_suit)
        draw.line([(5, 12), (13, 12)], fill=c_suit_light)
        draw.point((9, 15), fill=c_glow)

        # Head / Monocular
        draw.rectangle([6, 3, 13, 8], fill=c_suit_light)
        draw.point((10, 5), fill=c_visor if not hurt else (255, 220, 50, 255))

        # Weapon / Arm
        if aim:
            draw.rectangle([13, 10, 19, 14], fill=(20, 25, 30, 255))
            draw.point((19, 11), fill=c_visor)
        else:
            draw.rectangle([12, 12, 16, 18], fill=(20, 25, 30, 255))

    create_frame(w, h, lambda d, w, h: draw_base(d, 0, False)).save(out_dir / "patrol_1.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, 1, False)).save(out_dir / "patrol_2.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, 0, True)).save(out_dir / "windup.png")
    create_frame(w, h, lambda d, w, h: (draw_base(d, 0, True), d.point((19, 11), fill=c_glow))).save(out_dir / "attack.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, 0, False)).save(out_dir / "recovery.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, 0, False, hurt=True)).save(out_dir / "hurt.png")
    create_frame(w, h, lambda d, w, h: d.rectangle([2, 26, 17, 31], fill=c_suit)).save(out_dir / "death.png")


def generate_shield_hound():
    out_dir = SPRITES_DIR / "shield_hound"
    out_dir.mkdir(parents=True, exist_ok=True)
    w, h = 32, 24

    c_beast = (85, 55, 40, 255)
    c_iron = (55, 60, 65, 255)
    c_shield = (60, 110, 130, 255)
    c_phosphor = (65, 245, 155, 255)
    c_pack = (215, 135, 35, 255)

    def draw_base(draw, charge=False, pounce=False, hurt=False):
        # Body
        draw.rectangle([6, 8, 24, 16], fill=c_beast)
        # Cassette Walkman battery pack on rear
        draw.rectangle([7, 4, 13, 8], fill=c_pack)
        draw.point((10, 6), fill=(255, 230, 120, 255))

        # Legs
        draw.rectangle([7, 16, 10, 22], fill=c_iron)
        draw.rectangle([19, 16, 22, 22], fill=c_iron)

        # Head
        draw.rectangle([22, 7, 28, 14], fill=c_beast)
        draw.point((26, 9), fill=(255, 60, 40, 255))

        # Welded CRT Glass Riot Shield (Frontal Barrier)
        draw.rectangle([27, 2, 31, 20], fill=c_shield)
        draw.line([(28, 5), (30, 5)], fill=c_phosphor)
        draw.line([(28, 15), (30, 15)], fill=c_phosphor)

    create_frame(w, h, lambda d, w, h: draw_base(d, False, False)).save(out_dir / "patrol_1.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, False, False)).save(out_dir / "patrol_2.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, True, False)).save(out_dir / "windup.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, True, True)).save(out_dir / "pounce.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, False, False)).save(out_dir / "recovery.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, False, False, hurt=True)).save(out_dir / "hurt.png")
    create_frame(w, h, lambda d, w, h: d.rectangle([4, 18, 28, 23], fill=c_beast)).save(out_dir / "death.png")


def generate_phase_watcher():
    out_dir = SPRITES_DIR / "phase_watcher"
    out_dir.mkdir(parents=True, exist_ok=True)
    w, h = 20, 36

    c_grey = (160, 170, 185, 255)
    c_aura = (185, 115, 250, 180)
    c_eye = (8, 8, 12, 255)

    def draw_base(draw, drain=False, hurt=False):
        # Glitch / Aura halo
        draw.rectangle([2, 2, 17, 33], outline=c_aura, width=1)
        # Tall slender body
        draw.rectangle([6, 12, 13, 28], fill=c_grey)
        draw.rectangle([7, 28, 9, 35], fill=c_grey)
        draw.rectangle([10, 28, 12, 35], fill=c_grey)

        # Head & almond eyes
        draw.ellipse([4, 3, 15, 13], fill=c_grey)
        draw.polygon([(6, 7), (8, 6), (9, 9)], fill=c_eye)
        draw.polygon([(10, 6), (12, 7), (11, 9)], fill=c_eye)

        if drain:
            # Psychic drain beam emitter focus
            draw.ellipse([8, 16, 11, 19], fill=(220, 160, 255, 255))

    create_frame(w, h, lambda d, w, h: draw_base(d, False)).save(out_dir / "patrol_1.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, False)).save(out_dir / "patrol_2.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, False)).save(out_dir / "windup.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, True)).save(out_dir / "attack.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, False)).save(out_dir / "recovery.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, False, hurt=True)).save(out_dir / "hurt.png")
    create_frame(w, h, lambda d, w, h: d.ellipse([4, 28, 15, 35], fill=c_aura)).save(out_dir / "death.png")


def generate_chrysalis_splicer():
    out_dir = SPRITES_DIR / "chrysalis_splicer"
    out_dir.mkdir(parents=True, exist_ok=True)
    w, h = 28, 24

    c_chitin = (60, 70, 50, 255)
    c_tube = (230, 160, 30, 255)
    c_acid = (60, 220, 130, 255)

    def draw_base(draw, spit=False, hurt=False):
        # Low carapace body
        draw.ellipse([4, 6, 23, 18], fill=c_chitin)
        # Radio receiver vacuum tubes on back
        draw.rectangle([7, 2, 11, 6], fill=c_tube)
        draw.rectangle([13, 2, 17, 6], fill=c_tube)
        draw.point((9, 4), fill=c_acid)
        draw.point((15, 4), fill=c_acid)

        # Skittering insectoid legs
        draw.line([(5, 14), (2, 22)], fill=c_chitin, width=1)
        draw.line([(10, 15), (8, 22)], fill=c_chitin, width=1)
        draw.line([(17, 15), (19, 22)], fill=c_chitin, width=1)
        draw.line([(22, 14), (25, 22)], fill=c_chitin, width=1)

        # Mandibles
        draw.line([(22, 10), (27, 8)], fill=c_acid if spit else c_chitin, width=1)
        draw.line([(22, 13), (27, 14)], fill=c_acid if spit else c_chitin, width=1)

    create_frame(w, h, lambda d, w, h: draw_base(d, False)).save(out_dir / "patrol_1.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, False)).save(out_dir / "patrol_2.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, False)).save(out_dir / "windup.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, True)).save(out_dir / "attack.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, False)).save(out_dir / "recovery.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, False, hurt=True)).save(out_dir / "hurt.png")
    create_frame(w, h, lambda d, w, h: d.ellipse([4, 16, 23, 22], fill=c_chitin)).save(out_dir / "death.png")


def generate_precursor_guardian():
    out_dir = SPRITES_DIR / "precursor_guardian"
    out_dir.mkdir(parents=True, exist_ok=True)
    w, h = 32, 40

    c_stone = (70, 75, 80, 255)
    c_stone_dark = (45, 50, 55, 255)
    c_brass = (210, 160, 50, 255)
    c_rune = (245, 205, 65, 255)

    def draw_base(draw, slam=False, hurt=False):
        # Heavy stone legs
        draw.rectangle([6, 26, 12, 38], fill=c_stone_dark)
        draw.rectangle([20, 26, 26, 38], fill=c_stone_dark)

        # Monolithic torso
        draw.rectangle([5, 12, 27, 26], fill=c_stone)
        draw.rectangle([8, 14, 24, 24], fill=c_stone_dark)
        # Glowing runic glyphs
        draw.line([(12, 17), (20, 17)], fill=c_rune)
        draw.line([(16, 15), (16, 21)], fill=c_rune)

        # Broad stone head
        draw.rectangle([9, 4, 23, 12], fill=c_stone)
        draw.point((12, 7), fill=c_rune)
        draw.point((20, 7), fill=c_rune)

        # Brass Gauntlets
        if slam:
            draw.rectangle([2, 24, 8, 36], fill=c_brass)
            draw.rectangle([24, 24, 30, 36], fill=c_brass)
        else:
            draw.rectangle([1, 14, 6, 26], fill=c_brass)
            draw.rectangle([26, 14, 31, 26], fill=c_brass)

    create_frame(w, h, lambda d, w, h: draw_base(d, False)).save(out_dir / "patrol_1.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, False)).save(out_dir / "patrol_2.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, False)).save(out_dir / "windup.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, True)).save(out_dir / "attack.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, False)).save(out_dir / "recovery.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, False, hurt=True)).save(out_dir / "hurt.png")
    create_frame(w, h, lambda d, w, h: d.rectangle([4, 30, 28, 38], fill=c_stone_dark)).save(out_dir / "death.png")


def generate_temporal_phantom():
    out_dir = SPRITES_DIR / "temporal_phantom"
    out_dir.mkdir(parents=True, exist_ok=True)
    w, h = 24, 32

    c_amber = (230, 160, 40, 220)
    c_green = (50, 220, 100, 220)

    def draw_base(draw, pulse=False, hurt=False):
        # Wireframe vector lines
        draw.rectangle([5, 8, 18, 26], outline=c_amber, width=1)
        draw.line([(5, 8), (18, 26)], fill=c_green)
        draw.line([(5, 26), (18, 8)], fill=c_green)

        # Wireframe head
        draw.ellipse([7, 2, 16, 9], outline=c_amber, width=1)
        draw.point((10, 5), fill=(255, 255, 255, 255))
        draw.point((13, 5), fill=(255, 255, 255, 255))

        # Vector limbs
        draw.line([(7, 26), (6, 31)], fill=c_amber)
        draw.line([(16, 26), (17, 31)], fill=c_amber)

    create_frame(w, h, lambda d, w, h: draw_base(d, False)).save(out_dir / "patrol_1.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, False)).save(out_dir / "patrol_2.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, False)).save(out_dir / "windup.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, True)).save(out_dir / "attack.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, False)).save(out_dir / "recovery.png")
    create_frame(w, h, lambda d, w, h: draw_base(d, False, hurt=True)).save(out_dir / "hurt.png")
    create_frame(w, h, lambda d, w, h: d.rectangle([6, 28, 17, 31], outline=c_amber)).save(out_dir / "death.png")


def update_manifest():
    manifest_path = SPRITES_DIR / "manifest.json"
    data = {}
    if manifest_path.exists():
        data = json.loads(manifest_path.read_text(encoding="utf-8"))

    enemies = data.get("enemies", {})

    archetypes = [
        ("core_enforcer", "Core Chassis Enforcer", 24, 32, [12, 16]),
        ("core_operative", "Core Assimilated Operative", 20, 32, [10, 16]),
        ("shield_hound", "Static Shield Hound", 32, 24, [16, 20]),
        ("phase_watcher", "Phase Watcher", 20, 36, [10, 18]),
        ("chrysalis_splicer", "Chrysalis Splicer", 28, 24, [14, 20]),
        ("precursor_guardian", "Precursor Hominid Guardian", 32, 40, [16, 36]),
        ("temporal_phantom", "Temporal Wireframe Phantom", 24, 32, [12, 16]),
    ]

    for key, name, w, h, origin in archetypes:
        enemies[key] = {
            "name": name,
            "width": w,
            "height": h,
            "origin": origin,
            "animations": {
                "patrol": {
                    "frames": [f"sprites/enemies/{key}/patrol_1.png", f"sprites/enemies/{key}/patrol_2.png"],
                    "frame_duration_ms": 250,
                    "loop": True
                },
                "windup": {
                    "frames": [f"sprites/enemies/{key}/windup.png"],
                    "frame_duration_ms": 200,
                    "loop": True
                },
                "attack": {
                    "frames": [f"sprites/enemies/{key}/attack.png" if key != "shield_hound" else f"sprites/enemies/{key}/pounce.png"],
                    "frame_duration_ms": 200,
                    "loop": False
                },
                "recovery": {
                    "frames": [f"sprites/enemies/{key}/recovery.png"],
                    "frame_duration_ms": 400,
                    "loop": False
                },
                "hurt": {
                    "frames": [f"sprites/enemies/{key}/hurt.png"],
                    "frame_duration_ms": 120,
                    "loop": False
                },
                "death": {
                    "frames": [f"sprites/enemies/{key}/death.png"],
                    "frame_duration_ms": 500,
                    "loop": False
                }
            }
        }

    data["enemies"] = enemies
    manifest_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main():
    print("Synthesizing S09 hostile faction sprite sheets...")
    generate_core_enforcer()
    generate_core_operative()
    generate_shield_hound()
    generate_phase_watcher()
    generate_chrysalis_splicer()
    generate_precursor_guardian()
    generate_temporal_phantom()
    update_manifest()
    print("SUCCESS: All 7 faction sprite assets generated and manifest updated.")


if __name__ == "__main__":
    main()

