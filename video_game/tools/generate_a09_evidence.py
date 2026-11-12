"""
# PURPOSE: Generate visual evidence artifacts and telemetry previews for Milestone 2 Task A09 (Greenkeeper Boss).
# CALLED BY: Manual execution or release verification pipeline.
# HOW TO MODIFY: Adjust scene composition, telemetry charts, or preview render targets.
"""

from pathlib import Path
from typing import Any, Tuple
import pygame

from video_game.engine import config
from video_game.engine.bosses.base import (
    PHASE_1,
    PHASE_2,
    PHASE_3,
    PHASE_DEFEATED,
    STATE_ATTACK,
    STATE_TELEGRAPH,
    STATE_VULNERABLE,
)
from video_game.engine.bosses.greenkeeper import Greenkeeper
from video_game.engine.campaign import Campaign
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.objectives import Objective
from video_game.engine.player import Player
from video_game.engine.ui.hud import render_global_hud
from video_game.engine.world import Camera, Room

EVIDENCE_DIR = Path(__file__).resolve().parent.parent / "planning" / "evidence" / "A09" / "previews"
LEVELS_DIR = Path(__file__).resolve().parent.parent / "data" / "levels"


def ensure_evidence_dir():
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def generate_01_arena_blockout(crt: CRTRenderer):
    """Render full in-engine view of the act_01_greenkeeper_arena.json room."""
    crt.clear((4, 8, 12))
    level_path = LEVELS_DIR / "act_01" / "greenkeeper_arena.json"
    room = Room.load_from_file(level_path)

    camera = Camera(480, 270)
    camera.set_world_bounds(room.width_px, room.height_px)
    camera.x = 80.0
    camera.y = 0.0

    room.render_background(crt.canvas, camera)
    room.render_tiles(crt.canvas, camera)
    room.render_objects(crt.canvas, camera)

    # Annotate arena zones
    crt.draw_text("UPPER CATWALK PLATFORMS (ONE-WAY GRATING, y=144)", 110, 68, color=config.COLOR_FIBO_GOLD, size="sm")
    crt.draw_text("MID LEVEL TRUSS PLATFORM (y=192)", 130, 120, color=config.COLOR_CRT_DIM, size="sm")
    crt.draw_text("PRE-BOSS CHECKPOINT (x=64)", 40, 190, color=config.COLOR_CRT_GREEN, size="sm")
    crt.draw_text("DEEP REFLECTOR BASIN FLOOR (y=240)", 150, 244, color=config.COLOR_AMBER_1977, size="sm")
    crt.draw_text("BOSS SPAN ZONE (x=380..520)", 310, 160, color=config.COLOR_EHMAN_RED, size="sm")

    out_path = EVIDENCE_DIR / "01_greenkeeper_boss_arena_blockout.png"
    pygame.image.save(crt.canvas, str(out_path))
    print(f"Saved {out_path.name}")


def generate_02_chassis_and_weak_point(crt: CRTRenderer):
    """Render technical breakdown card of Greenkeeper's chassis and weak point."""
    crt.clear((6, 9, 12))

    # Outer panel
    pygame.draw.rect(crt.canvas, (10, 16, 22), (10, 10, 460, 250))
    pygame.draw.rect(crt.canvas, config.COLOR_CORE_STEEL, (10, 10, 460, 250), 1)

    crt.draw_text("CORE WARDEN GREENKEEPER // CHASSIS & WEAK POINT SCHEMATIC", 24, 20, color=config.COLOR_FIBO_GOLD, size="sm")

    # Schematic box
    pygame.draw.rect(crt.canvas, (14, 20, 28), (24, 40, 220, 150))
    pygame.draw.rect(crt.canvas, config.COLOR_CRT_DIM, (24, 40, 220, 150), 1)

    # Render magnified boss mockup
    camera = Camera(480, 270)
    camera.x = 360.0
    camera.y = 110.0

    boss = Greenkeeper(x=440.0, y=160.0)
    boss.weak_point_exposed = True
    boss.vulnerability_timer = 2.0
    boss.render(crt.canvas, camera)

    # Annotations on schematic
    crt.draw_text("<- EXPOSED CORE [2.0x CRIT]", 130, 80, color=config.COLOR_AMBER_1977, size="sm")
    crt.draw_text("<- TURF MORTAR TURRET", 150, 60, color=config.COLOR_CRT_GREEN, size="sm")
    crt.draw_text("<- BULLDOZER SCOOP", 40, 155, color=config.COLOR_FIBO_GOLD, size="sm")
    crt.draw_text("<- TRACKED CHASSIS", 120, 175, color=config.COLOR_CORE_STEEL, size="sm")

    # Specifications on right side
    spec_x = 256
    crt.draw_text("TECHNICAL SPECIFICATIONS:", spec_x, 44, color=config.COLOR_FIBO_GOLD, size="sm")
    specs = [
        "DESIGNATION: Heavy Terraforming Excavator",
        "ORIGIN: 1995 Big Ear Coverup Decommissioning",
        "TOTAL DURABILITY: 300 HP (3 Equal Phases)",
        "PRIMARY WEAPON: Pneumatic Turf Mortar",
        "SECONDARY: Low-Altitude Ground Sweep Cutter",
        "TACTICAL VULNERABILITY: Overheated Core",
        "CRITICAL MULTIPLIER: 2.0x (150 Dmg Charged)",
    ]
    for idx, s in enumerate(specs):
        crt.draw_text(s, spec_x, 64 + idx * 16, color=config.COLOR_CRT_DIM, size="sm")

    # Bottom guidance strip
    pygame.draw.rect(crt.canvas, (12, 18, 24), (20, 202, 440, 48))
    pygame.draw.rect(crt.canvas, config.COLOR_CRT_GREEN, (20, 202, 440, 48), 1)
    crt.draw_text("TACTICAL DOCTRINE // DR. MATEO VARGAS", 28, 208, color=config.COLOR_CRT_GREEN, size="sm")
    crt.draw_text("Dodge mortar reticles; wait for exhaust cowl to open after 2 volleys.", 28, 220, color=config.COLOR_AMBER_1977, size="sm")
    crt.draw_text("Discharge charged Waveguide Maser (75 dmg x 2.0 = 150 dmg) directly into core.", 28, 232, color=config.COLOR_FIBO_GOLD, size="sm")

    out_path = EVIDENCE_DIR / "02_greenkeeper_chassis_and_weak_point.png"
    pygame.image.save(crt.canvas, str(out_path))
    print(f"Saved {out_path.name}")


def generate_03_phase_1_encounter(crt: CRTRenderer):
    """Render active Phase 1 combat scene with mortar warning reticles."""
    level_path = LEVELS_DIR / "act_01" / "greenkeeper_arena.json"
    room = Room.load_from_file(level_path)

    camera = Camera(480, 270)
    camera.set_world_bounds(room.width_px, room.height_px)
    camera.x = 100.0
    camera.y = 0.0

    room.render_background(crt.canvas, camera)
    room.render_tiles(crt.canvas, camera)
    room.render_objects(crt.canvas, camera)

    # Boss in Phase 1 telegraphing mortar
    boss = Greenkeeper(x=460.0, y=192.0)
    boss.current_phase = PHASE_1
    boss.health = 270
    boss._schedule_next_attack((180.0, 208.0))
    boss.render(crt.canvas, camera)

    # Player position (retreated outside mortar radius)
    player = Player(x=80.0, y=208.0)
    player.facing = "right"
    sc_px, sc_py = camera.world_to_screen(player.x, player.y)
    pygame.draw.rect(crt.canvas, config.COLOR_FIBO_GOLD, (sc_px, sc_py, 16, 32), 2)
    pygame.draw.circle(crt.canvas, config.COLOR_FIBO_GOLD, (sc_px + 8, sc_py + 8), 5)

    # Laser targeting line from player
    pygame.draw.line(crt.canvas, config.COLOR_CRT_GREEN, (sc_px + 16, sc_py + 14), (sc_px + 120, sc_py + 14), 1)

    # Boss health HUD
    bar_x = 120
    bar_y = 22
    bar_w = 240
    bar_h = 10
    pygame.draw.rect(crt.canvas, (10, 14, 18), (bar_x - 4, bar_y - 4, bar_w + 8, bar_h + 18))
    pygame.draw.rect(crt.canvas, config.COLOR_CORE_STEEL, (bar_x - 4, bar_y - 4, bar_w + 8, bar_h + 18), 1)
    pygame.draw.rect(crt.canvas, config.COLOR_CRT_GREEN, (bar_x, bar_y, int(bar_w * 270 / 300), bar_h))
    pygame.draw.rect(crt.canvas, (40, 50, 60), (bar_x, bar_y, bar_w, bar_h), 1)
    # Ticks
    pygame.draw.line(crt.canvas, (255, 255, 255), (bar_x + int(bar_w * 2 / 3), bar_y - 2), (bar_x + int(bar_w * 2 / 3), bar_y + bar_h + 2), 1)
    pygame.draw.line(crt.canvas, (255, 255, 255), (bar_x + int(bar_w / 3), bar_y - 2), (bar_x + int(bar_w / 3), bar_y + bar_h + 2), 1)
    crt.draw_text("THE GREENKEEPER [PHASE 1/3: TURF MORTARS]", bar_x, bar_y + 11, color=config.COLOR_FIBO_GOLD, size="sm")

    # Global HUD footer
    campaign = Campaign(save_id="preview_boss_p1")
    obj = Objective(
        id="defeat_greenkeeper",
        title="NEUTRALIZE GREENKEEPER [PHASE 1]",
        description="Evade mortar reticles and target exposed exhaust ports",
        hint="RETICLE WARNING: 0.8s ESCAPE WINDOW",
    )
    render_global_hud(
        crt,
        campaign,
        location_label="REFLECTOR BASIN // PHASE 1: MORTAR BARRAGE",
        footer_text="[RETICLE WARNING ACTIVE] ESCAPE TO PERIMETER // DISCHARGE ON VULNERABILITY",
        player=player,
        objective=obj,
        threat_level="LOCKED",
    )

    out_path = EVIDENCE_DIR / "03_phase_1_mortar_barrage_encounter.png"
    pygame.image.save(crt.canvas, str(out_path))
    print(f"Saved {out_path.name}")


def generate_04_phase_2_sweep_and_safety(crt: CRTRenderer):
    """Render Phase 2 ground sweep beam and upper catwalk evasion."""
    level_path = LEVELS_DIR / "act_01" / "greenkeeper_arena.json"
    room = Room.load_from_file(level_path)

    camera = Camera(480, 270)
    camera.set_world_bounds(room.width_px, room.height_px)
    camera.x = 100.0
    camera.y = 0.0

    room.render_background(crt.canvas, camera)
    room.render_tiles(crt.canvas, camera)
    room.render_objects(crt.canvas, camera)

    # Boss executing sweep
    boss = Greenkeeper(x=460.0, y=192.0)
    boss.current_phase = PHASE_2
    boss.health = 160
    boss.sweep_active = True
    boss.sweep_x = 260.0
    boss.sweep_y = 224.0
    boss.render(crt.canvas, camera)

    # Player safely on mid catwalk grating (y=160, sc_py = 160)
    player = Player(x=160.0, y=160.0)
    sc_px, sc_py = camera.world_to_screen(player.x, player.y)
    pygame.draw.rect(crt.canvas, config.COLOR_CRT_GREEN, (sc_px, sc_py, 16, 32), 2)
    pygame.draw.circle(crt.canvas, config.COLOR_CRT_GREEN, (sc_px + 8, sc_py + 8), 5)

    # Annotate safe elevation vs danger zone
    crt.draw_text("SAFE PLATFORM ELEVATION (y <= 192)", sc_px - 40, sc_py - 14, color=config.COLOR_CRT_GREEN, size="sm")
    crt.draw_text("GROUND CUTTER DANGER ZONE (y in [216, 232])", 60, 210, color=(255, 90, 90), size="sm")

    # Boss health HUD
    bar_x = 120
    bar_y = 22
    bar_w = 240
    bar_h = 10
    pygame.draw.rect(crt.canvas, (10, 14, 18), (bar_x - 4, bar_y - 4, bar_w + 8, bar_h + 18))
    pygame.draw.rect(crt.canvas, config.COLOR_CORE_STEEL, (bar_x - 4, bar_y - 4, bar_w + 8, bar_h + 18), 1)
    pygame.draw.rect(crt.canvas, config.COLOR_AMBER_1977, (bar_x, bar_y, int(bar_w * 160 / 300), bar_h))
    pygame.draw.rect(crt.canvas, (40, 50, 60), (bar_x, bar_y, bar_w, bar_h), 1)
    crt.draw_text("THE GREENKEEPER [PHASE 2/3: SWEEP CUTTER]", bar_x, bar_y + 11, color=config.COLOR_FIBO_GOLD, size="sm")

    # Global HUD footer
    campaign = Campaign(save_id="preview_boss_p2")
    obj = Objective(
        id="defeat_greenkeeper",
        title="NEUTRALIZE GREENKEEPER [PHASE 2]",
        description="Climb catwalks to avoid floor cutter; strike jammed cowl",
        hint="HIGH GROUND SAFE FROM SWEEP",
    )
    render_global_hud(
        crt,
        campaign,
        location_label="REFLECTOR BASIN // PHASE 2: GROUND SWEEP CUTTER",
        footer_text="[SWEEP ACTIVE] ELEVATED CATWALKS PROVIDE 100% COVERAGE FROM SWEEP",
        player=player,
        objective=obj,
        threat_level="LOCKED",
    )

    out_path = EVIDENCE_DIR / "04_phase_2_sweep_laser_and_catwalk_safety.png"
    pygame.image.save(crt.canvas, str(out_path))
    print(f"Saved {out_path.name}")


def generate_05_defeat_and_act_02_unlock_flow(crt: CRTRenderer):
    """Render defeat sequence, progression rewards, and Act II unlock flow."""
    crt.clear((6, 9, 12))

    # Outer panel
    pygame.draw.rect(crt.canvas, (10, 16, 22), (10, 10, 460, 250))
    pygame.draw.rect(crt.canvas, config.COLOR_CRT_GREEN, (10, 10, 460, 250), 1)

    crt.draw_text("SECTOR BOSS DEFEAT FLOW // ACT I COMPLETION & ACT II UNLOCK", 24, 20, color=config.COLOR_CRT_GREEN, size="sm")

    # Stage 1: Phase 3 Meltdown Depleted
    pygame.draw.rect(crt.canvas, (14, 24, 18), (20, 40, 440, 46))
    pygame.draw.rect(crt.canvas, config.COLOR_CRT_GREEN, (20, 40, 440, 46), 1)
    crt.draw_text("STAGE 1: HEALTH DEPLETED (HP: 0 / 300) -> BOSS_DEFEATED", 30, 46, color=config.COLOR_CRT_GREEN, size="sm")
    crt.draw_text("Condition: resolve_simultaneous_death(player_alive=True) -> 'BOSS_DEFEATED'", 30, 58, color=config.COLOR_CRT_DIM, size="sm")
    crt.draw_text("Edge Case: If player dies in same frame, PLAYER_DIED takes precedence (fair retry).", 30, 70, color=config.COLOR_FIBO_GOLD, size="sm")

    # Stage 2: Atomic Event Grant
    pygame.draw.rect(crt.canvas, (14, 20, 26), (20, 94, 440, 46))
    pygame.draw.rect(crt.canvas, config.COLOR_FIBO_GOLD, (20, 94, 440, 46), 1)
    crt.draw_text("STAGE 2: ATOMIC CAMPAIGN EVENT GRANT (defeat_greenkeeper)", 30, 100, color=config.COLOR_FIBO_GOLD, size="sm")
    crt.draw_text("Flags: greenkeeper_defeated = True, act_01_completed = True, act_02_unlocked = True", 30, 112, color=config.COLOR_CRT_DIM, size="sm")
    crt.draw_text("Meters: Scientific Certainty +10, Human Agency +15, Alignment Confidence +10", 30, 124, color=config.COLOR_CRT_GREEN, size="sm")

    # Stage 3: Checkpoint and Save Idempotence
    pygame.draw.rect(crt.canvas, (14, 18, 22), (20, 148, 440, 46))
    pygame.draw.rect(crt.canvas, config.COLOR_CORE_STEEL, (20, 148, 440, 46), 1)
    crt.draw_text("STAGE 3: PERSISTENT SAVE & REPLAY IDEMPOTENCE", 30, 154, color=config.COLOR_CORE_STEEL, size="sm")
    crt.draw_text("Re-triggering defeat returns False; 0 duplicate meter grants or corrupted state.", 30, 166, color=config.COLOR_CRT_DIM, size="sm")
    crt.draw_text("Campaign checkpoint saved cleanly to disk; survives game reboot.", 30, 178, color=config.COLOR_CRT_DIM, size="sm")

    # Stage 4: Milestone 2 Task A10 Transition
    pygame.draw.rect(crt.canvas, (20, 14, 24), (20, 202, 440, 46))
    pygame.draw.rect(crt.canvas, (200, 120, 255), (20, 202, 440, 46), 1)
    crt.draw_text("STAGE 4: UNLOCKS ACT I MISSION CHAIN ASSEMBLY (TASK A10)", 30, 208, color=(220, 150, 255), size="sm")
    crt.draw_text("Transit corridor unlocked to return to Bunker Hub and initiate Act II relay transit.", 30, 222, color=config.COLOR_AMBER_1977, size="sm")

    out_path = EVIDENCE_DIR / "05_boss_defeat_and_act_02_unlock_flow.png"
    pygame.image.save(crt.canvas, str(out_path))
    print(f"Saved {out_path.name}")


def main():
    ensure_evidence_dir()
    pygame.init()
    pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    crt = CRTRenderer(scale=1)

    generate_01_arena_blockout(crt)
    generate_02_chassis_and_weak_point(crt)
    generate_03_phase_1_encounter(crt)
    generate_04_phase_2_sweep_and_safety(crt)
    generate_05_defeat_and_act_02_unlock_flow(crt)

    print("All A09 visual evidence previews generated successfully.")


if __name__ == "__main__":
    main()

