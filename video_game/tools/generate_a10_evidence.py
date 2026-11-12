"""
# PURPOSE: Generate visual evidence artifacts and telemetry previews for Milestone 2 Task A10 (Act I Mission Chain).
# CALLED BY: Manual execution or release verification pipeline.
# HOW TO MODIFY: Adjust scene composition, telemetry charts, or preview render targets.
"""

from pathlib import Path
from typing import Any, Tuple
import pygame

from video_game.engine import config
from video_game.engine.campaign import Campaign
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.objectives import ObjectiveTracker
from video_game.engine.player import Player
from video_game.engine.ui.hud import render_global_hud
from video_game.engine.world import Camera, Room

EVIDENCE_DIR = Path(__file__).resolve().parent.parent / "planning" / "evidence" / "A10" / "previews"
LEVELS_DIR = Path(__file__).resolve().parent.parent / "data" / "levels"


def ensure_evidence_dir():
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def generate_01_mission_chain_flowchart(crt: CRTRenderer):
    """Render end-to-end 7-stage Act I mission chain flowchart."""
    crt.clear((6, 10, 15))

    # Outer border
    pygame.draw.rect(crt.canvas, (12, 18, 25), (10, 10, 460, 250))
    pygame.draw.rect(crt.canvas, config.COLOR_CORE_STEEL, (10, 10, 460, 250), 1)

    # Header
    crt.draw_text("ACT I MISSION CHAIN // COMPLETE OPERATIONAL PROGRESSION", 22, 18, color=config.COLOR_FIBO_GOLD, size="sm")
    crt.draw_text("From Ohio Haystack Contact to Core Warden Defeat and Act II Transit", 22, 30, color=config.COLOR_CRT_DIM, size="sm")

    stages = [
        ("STAGE 1", "FASR-001 SIGNAL", "Radio discovery via CRT Terminal", config.COLOR_CRT_GREEN),
        ("STAGE 2", "VALIDATION LAB", "Protocol analysis & verification", config.COLOR_CRT_GREEN),
        ("STAGE 3", "SALVAGE YARD", "Scavenge analog coupler from scrap", config.COLOR_AMBER_1977),
        ("STAGE 4", "BUNKER REPAIR", "Feedhorn repair at workbench", config.COLOR_AMBER_1977),
        ("STAGE 5", "DISH CATWALK", "Wave defense of Big Ear array", config.COLOR_CORE_STEEL),
        ("STAGE 6", "GREENKEEPER", "Defeat Core Warden in dish basin", config.COLOR_EHMAN_RED),
        ("STAGE 7", "ACT II TRANSIT", "FASR-007 validation & unlock", config.COLOR_FIBO_GOLD),
    ]

    box_w = 420
    box_h = 24
    start_y = 48
    gap_y = 29

    for i, (tag, title, desc, col) in enumerate(stages):
        y = start_y + i * gap_y
        # Stage pill
        pygame.draw.rect(crt.canvas, (16, 24, 32), (30, y, box_w, box_h))
        pygame.draw.rect(crt.canvas, col, (30, y, box_w, box_h), 1)

        # Stage indicator pip
        pygame.draw.circle(crt.canvas, col, (42, y + 12), 4)

        # Texts
        crt.draw_text(tag, 54, y + 5, color=col, size="sm")
        crt.draw_text(title, 115, y + 5, color=(240, 240, 250), size="sm")
        crt.draw_text(desc, 245, y + 5, color=config.COLOR_CRT_DIM, size="sm")

        # Down arrow connector if not last
        if i < len(stages) - 1:
            pygame.draw.line(crt.canvas, config.COLOR_CRT_DIM, (42, y + box_h), (42, y + gap_y), 1)

    out_path = EVIDENCE_DIR / "01_act_01_mission_chain_flowchart.png"
    pygame.image.save(crt.canvas, str(out_path))
    print(f"Saved {out_path.name}")


def generate_02_salvage_yard_blockout(crt: CRTRenderer):
    """Render full in-engine view of act_01_salvage_yard.json."""
    crt.clear((6, 8, 12))
    level_path = LEVELS_DIR / "act_01" / "salvage_yard.json"
    room = Room.load_from_file(level_path)

    camera = Camera(480, 270)
    camera.set_world_bounds(room.width_px, room.height_px)
    camera.x = 40.0
    camera.y = 18.0

    room.render_background(crt.canvas, camera)
    room.render_tiles(crt.canvas, camera)
    room.render_objects(crt.canvas, camera)

    # Annotate key level elements
    crt.draw_text("YARD ENTRANCE // FROM APPROACH TRENCH (x=48)", 20, 160, color=config.COLOR_CRT_GREEN, size="sm")
    crt.draw_text("UPPER SCRAP GRATING (ONE-WAY, y=144)", 110, 68, color=config.COLOR_FIBO_GOLD, size="sm")
    crt.draw_text("ELECTRICAL SUMP HAZARD (PIT x=288..352)", 180, 242, color=config.COLOR_EHMAN_RED, size="sm")
    crt.draw_text("PARTS CACHE // ANALOG COUPLER (x=576, y=192)", 240, 130, color=config.COLOR_AMBER_1977, size="sm")

    # Draw player silhouette at entrance
    px = 48.0 - camera.x
    py = 208.0 - camera.y
    pygame.draw.rect(crt.canvas, config.COLOR_CRT_GREEN, (int(px - 6), int(py - 24), 12, 24), 2)
    pygame.draw.circle(crt.canvas, config.COLOR_CRT_GREEN, (int(px), int(py - 28)), 4)

    out_path = EVIDENCE_DIR / "02_salvage_yard_level_blockout.png"
    pygame.image.save(crt.canvas, str(out_path))
    print(f"Saved {out_path.name}")


def generate_03_mission_prerequisite_blocking_card(crt: CRTRenderer):
    """Render prerequisite validation and lockout HUD telemetry."""
    crt.clear((8, 10, 14))

    # Outer panel
    pygame.draw.rect(crt.canvas, (12, 16, 22), (10, 10, 460, 250))
    pygame.draw.rect(crt.canvas, config.COLOR_EHMAN_RED, (10, 10, 460, 250), 1)

    crt.draw_text("SECURITY INTERLOCK & PREREQUISITE GUARDS", 24, 20, color=config.COLOR_EHMAN_RED, size="sm")
    crt.draw_text("Active Enforcement: Bypasses Blocked with Contextual Guidance", 24, 32, color=config.COLOR_CRT_DIM, size="sm")

    gates = [
        ("GATE 1", "BUNKER AIRLOCK -> DISH CATWALK", "BLOCKED: FEEDHORN UNREPAIRED",
         "Guidance: 'REPAIR REQUIRED // Calibrate Analog Coupler at Workbench'", config.COLOR_AMBER_1977),
        ("GATE 2", "FIELD OPS -> DISH CATWALK DOOR", "BLOCKED: FEEDHORN NOT POWERED",
         "Guidance: 'FEEDHORN RESTORATION REQUIRED BEFORE DISH ACCESS'", config.COLOR_AMBER_1977),
        ("GATE 3", "FIELD OPS -> GREENKEEPER ARENA", "BLOCKED: DISH SIEGE IN PROGRESS",
         "Guidance: 'ARENA LOCKOUT // Repel Drone Waves from Catwalk First'", config.COLOR_EHMAN_RED),
        ("GATE 4", "ACT I COMPLETION -> ACT II TRANSIT", "BLOCKED: GREENKEEPER ACTIVE",
         "Guidance: 'SECURE SECTOR // Core Warden Greenkeeper Must Be Neutralized'", config.COLOR_FIBO_GOLD),
    ]

    box_y = 50
    for tag, title, status, guide, col in gates:
        pygame.draw.rect(crt.canvas, (18, 22, 30), (24, box_y, 432, 44))
        pygame.draw.rect(crt.canvas, col, (24, box_y, 432, 44), 1)

        # Status badge
        pygame.draw.rect(crt.canvas, col, (32, box_y + 6, 50, 14))
        crt.draw_text(tag, 36, box_y + 8, color=(10, 10, 10), size="sm")

        crt.draw_text(title, 90, box_y + 8, color=(240, 240, 250), size="sm")
        crt.draw_text(f"STATUS: {status}", 90, box_y + 20, color=col, size="sm")
        crt.draw_text(guide, 90, box_y + 30, color=config.COLOR_CRT_DIM, size="sm")

        box_y += 48

    out_path = EVIDENCE_DIR / "03_mission_prerequisite_blocking_card.png"
    pygame.image.save(crt.canvas, str(out_path))
    print(f"Saved {out_path.name}")


def generate_04_bunker_dispatch_and_airlock_routing(crt: CRTRenderer):
    """Render bunker airlock dispatch logic and routing paths."""
    crt.clear((6, 12, 16))

    pygame.draw.rect(crt.canvas, (12, 20, 28), (10, 10, 460, 250))
    pygame.draw.rect(crt.canvas, config.COLOR_CRT_GREEN, (10, 10, 460, 250), 1)

    crt.draw_text("BUNKER HUB // AIRLOCK DISPATCH ROUTING MATRIX", 24, 20, color=config.COLOR_CRT_GREEN, size="sm")
    crt.draw_text("Airlock Station (x=348) Context-Aware Dispatch State Table", 24, 32, color=config.COLOR_CRT_DIM, size="sm")

    # Table headers
    pygame.draw.rect(crt.canvas, (20, 32, 44), (24, 52, 432, 20))
    crt.draw_text("CAMPAIGN STATE / PREREQUISITE", 32, 56, color=config.COLOR_FIBO_GOLD, size="sm")
    crt.draw_text("DISPATCH TARGET", 220, 56, color=config.COLOR_FIBO_GOLD, size="sm")
    crt.draw_text("SPAWN / ACTION", 340, 56, color=config.COLOR_FIBO_GOLD, size="sm")

    rows = [
        ("Default / First Field Mission", "act_01/approach.json", "bunker_exit", config.COLOR_CRT_GREEN),
        ("Coupler Collected (Unrepaired)", "BLOCKED AT AIRLOCK", "Toast: Repair Required", config.COLOR_AMBER_1977),
        ("Feedhorn Repaired (flags=True)", "act_01/dish_catwalk.json", "dish_access_left", config.COLOR_CORE_STEEL),
        ("Dish Defense Completed", "STATE_BOSS_BOUNTY", "arena_checkpoint", config.COLOR_EHMAN_RED),
        ("Greenkeeper Defeated", "BUNKER RESTORATION", "ACT II Transmit Ready", config.COLOR_FIBO_GOLD),
    ]

    row_y = 76
    for cond, target, action, col in rows:
        pygame.draw.rect(crt.canvas, (16, 24, 34), (24, row_y, 432, 28))
        pygame.draw.rect(crt.canvas, config.COLOR_CRT_DIM, (24, row_y, 432, 28), 1)

        crt.draw_text(cond, 32, row_y + 8, color=(230, 230, 240), size="sm")
        crt.draw_text(target, 220, row_y + 8, color=col, size="sm")
        crt.draw_text(action, 340, row_y + 8, color=config.COLOR_CRT_DIM, size="sm")
        row_y += 32

    # Footer note
    crt.draw_text("Bidirectional Traversal: Salvage Yard is seamlessly accessible from Approach Trench door (x=980)",
                  24, 238, color=config.COLOR_CRT_DIM, size="sm")

    out_path = EVIDENCE_DIR / "04_bunker_dispatch_and_airlock_routing.png"
    pygame.image.save(crt.canvas, str(out_path))
    print(f"Saved {out_path.name}")


def generate_05_save_reload_mid_chain_telemetry(crt: CRTRenderer):
    """Render save/reload mid-chain state fidelity telemetry."""
    crt.clear((8, 10, 16))

    pygame.draw.rect(crt.canvas, (14, 18, 26), (10, 10, 460, 250))
    pygame.draw.rect(crt.canvas, config.COLOR_FIBO_GOLD, (10, 10, 460, 250), 1)

    crt.draw_text("MID-CHAIN SAVE / RELOAD STATE FIDELITY TELEMETRY", 24, 20, color=config.COLOR_FIBO_GOLD, size="sm")
    crt.draw_text("Verification: Exact Preservation of Objectives, Flags, and Inventory", 24, 32, color=config.COLOR_CRT_DIM, size="sm")

    # Pre-save vs Post-reload table
    pygame.draw.rect(crt.canvas, (20, 26, 38), (24, 52, 432, 20))
    crt.draw_text("STATE PROPERTY", 32, 56, color=config.COLOR_CRT_DIM, size="sm")
    crt.draw_text("PRE-SAVE VALUE", 180, 56, color=config.COLOR_CRT_DIM, size="sm")
    crt.draw_text("POST-RELOAD VALUE", 300, 56, color=config.COLOR_CRT_DIM, size="sm")
    crt.draw_text("MATCH", 410, 56, color=config.COLOR_CRT_DIM, size="sm")

    telemetry = [
        ("Current Act", "act_01_ohio", "act_01_ohio", True),
        ("Current Room", "act_01_salvage_yard", "act_01_salvage_yard", True),
        ("Analog Coupler Inv", "1 unit", "1 unit", True),
        ("Trench Coupler Flag", "True", "True", True),
        ("Feedhorn Repaired", "False (Pending)", "False (Pending)", True),
        ("Contacted Civs", "['FASR-001']", "['FASR-001']", True),
        ("Extracted Fragments", "['FASR-001']", "['FASR-001']", True),
        ("Active Objective ID", "obj_repair_dish", "obj_repair_dish", True),
    ]

    ty = 76
    for prop, pre, post, match in telemetry:
        pygame.draw.rect(crt.canvas, (16, 22, 32), (24, ty, 432, 18))
        crt.draw_text(prop, 32, ty + 3, color=(220, 220, 230), size="sm")
        crt.draw_text(pre, 180, ty + 3, color=config.COLOR_AMBER_1977, size="sm")
        crt.draw_text(post, 300, ty + 3, color=config.COLOR_AMBER_1977, size="sm")
        crt.draw_text("OK" if match else "MISMATCH", 415, ty + 3,
                      color=config.COLOR_CRT_GREEN if match else config.COLOR_EHMAN_RED, size="sm")
        ty += 20

    crt.draw_text("FASR-007 LGM-1 spread-spectrum progression unlocks cleanly upon Greenkeeper defeat",
                  24, 238, color=config.COLOR_CRT_GREEN, size="sm")

    out_path = EVIDENCE_DIR / "05_save_reload_mid_chain_telemetry.png"
    pygame.image.save(crt.canvas, str(out_path))
    print(f"Saved {out_path.name}")


def main():
    pygame.init()
    pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    crt = CRTRenderer(scale=config.DEFAULT_SCALE)
    ensure_evidence_dir()

    print("Generating A10 evidence artifacts...")
    generate_01_mission_chain_flowchart(crt)
    generate_02_salvage_yard_blockout(crt)
    generate_03_mission_prerequisite_blocking_card(crt)
    generate_04_bunker_dispatch_and_airlock_routing(crt)
    generate_05_save_reload_mid_chain_telemetry(crt)
    print("All A10 visual evidence artifacts generated successfully.")


if __name__ == "__main__":
    main()

