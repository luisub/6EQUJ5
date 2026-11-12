"""
MODULE: video_game/tools/generate_a08_evidence.py
PURPOSE: Generate visual evidence previews for Milestone 2 Task A08 (72-second dish defense).
CALLED BY: Manual execution or verification harness.
HOW TO MODIFY: Update evidence preview frames or telemetry curves; maintain 480x270 native resolution.
"""

import os
from pathlib import Path
import pygame

from video_game.engine import config
from video_game.engine.campaign import Campaign
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.enemies import CoreReconDrone, EnemyManager, StaticHound
from video_game.engine.objectives import (
    DEFENSE_WAVES,
    DishDefenseHoldout,
    Objective,
    ObjectiveTracker,
    SIGNAL_BINS,
)
from video_game.engine.player import Player
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.ui.hud import render_global_hud
from video_game.engine.world import Camera, Room

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

EVIDENCE_DIR = Path(__file__).resolve().parent.parent / "planning" / "evidence" / "A08" / "previews"
LEVELS_DIR = Path(__file__).resolve().parent.parent / "data" / "levels"


def ensure_evidence_dir():
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def generate_01_signal_bins_telemetry(crt: CRTRenderer):
    """Generate 6-bin Wow! signal telemetry chart showing 72s intensity curve."""
    crt.clear((6, 9, 12))

    panel_rect = (16, 16, 448, 238)
    crt.draw_panel(
        panel_rect,
        bg_color=(6, 12, 16),
        border_color=config.COLOR_CRT_GREEN,
        title="72-SECOND DISH DEFENSE // SIX 12-SECOND SIGNAL BINS (6EQUJ5)",
    )

    crt.draw_text("BIG EAR REFLECTOR OBSERVATION ENVELOPE (1420.4056 MHz)", 28, 36, color=config.COLOR_FIBO_GOLD, size="sm")

    # Draw 6 bins side by side
    bin_w = 64
    base_x = 36
    base_y = 190
    max_h = 110

    for idx, b_data in enumerate(SIGNAL_BINS):
        bx = base_x + idx * 70
        snr = b_data["snr"]
        code = b_data["code"]
        intensity = b_data["intensity"]

        bar_h = int(max_h * (snr / 30.0))
        by = base_y - bar_h

        # Bar fill
        color = config.COLOR_FIBO_GOLD if code in ("Q", "U") else config.COLOR_CRT_GREEN
        pygame.draw.rect(crt.canvas, (12, 28, 20), (bx, by, bin_w, bar_h))
        pygame.draw.rect(crt.canvas, color, (bx, by, bin_w, bar_h), 1)

        # Highlight strip
        if bar_h > 4:
            pygame.draw.rect(crt.canvas, color, (bx + 2, by + 2, bin_w - 4, 3))

        # Alphanumeric character (large)
        crt.draw_text(code, bx + 24, by - 16, color=color, size="md")

        # Bin details
        crt.draw_text(f"BIN {idx+1}", bx + 16, base_y + 6, color=config.COLOR_CRT_DIM, size="sm")
        crt.draw_text(f"{idx*12}-{(idx+1)*12}s", bx + 10, base_y + 16, color=config.COLOR_CRT_DIM, size="sm")
        crt.draw_text(f"{snr}σ", bx + 22, base_y + 26, color=color, size="sm")

    # Legend and timing summary
    crt.draw_text("TOTAL DURATION: 72.0s  |  BIN TIME: 12.0s  |  CARRIER: 1420.4056 MHz", 50, 234, color=config.COLOR_AMBER_1977, size="sm")

    out_path = EVIDENCE_DIR / "01_72s_wow_signal_bins_telemetry.png"
    pygame.image.save(crt.canvas, str(out_path))
    print(f"Saved {out_path.name}")


def generate_02_catwalk_level_blockout(crt: CRTRenderer):
    """Render full in-engine view of the act_01_dish_catwalk.json room."""
    crt.clear((4, 8, 12))
    level_path = LEVELS_DIR / "act_01" / "dish_catwalk.json"
    room = Room.load_from_file(level_path)

    camera = Camera(480, 270)
    camera.set_world_bounds(room.width_px, room.height_px)
    camera.x = 80.0
    camera.y = 0.0

    room.render_background(crt.canvas, camera)
    room.render_tiles(crt.canvas, camera)
    room.render_objects(crt.canvas, camera)

    # Annotate level zones
    crt.draw_text("UPPER CATWALK PLATFORM (ONE-WAY TILES)", 140, 78, color=config.COLOR_FIBO_GOLD, size="sm")
    crt.draw_text("MID LEVEL TRUSS", 190, 142, color=config.COLOR_CRT_DIM, size="sm")
    crt.draw_text("FEEDHORN ARRAY MAST (x=296)", 260, 115, color=config.COLOR_CRT_GREEN, size="sm")
    crt.draw_text("MAIN DECK WALKWAY", 40, 222, color=config.COLOR_AMBER_1977, size="sm")

    out_path = EVIDENCE_DIR / "02_dish_catwalk_level_blockout.png"
    pygame.image.save(crt.canvas, str(out_path))
    print(f"Saved {out_path.name}")


def generate_03_holdout_combat_preview(crt: CRTRenderer):
    """Render active combat scene with holdout HUD and Wow! signal telemetry."""
    level_path = LEVELS_DIR / "act_01" / "dish_catwalk.json"
    room = Room.load_from_file(level_path)

    camera = Camera(480, 270)
    camera.set_world_bounds(room.width_px, room.height_px)
    camera.x = 100.0
    camera.y = 0.0

    # Setup environment
    room.render_background(crt.canvas, camera)
    room.render_tiles(crt.canvas, camera)
    room.render_objects(crt.canvas, camera)

    # Setup enemies
    enemy_mgr = EnemyManager()
    drone = CoreReconDrone("drone_boss_catwalk", x=380.0, y=96.0, patrol_left=280.0, patrol_right=480.0)
    drone.state = "WINDUP"
    drone.telegraph_laser = True
    drone.aim_locked = True
    drone.target_point = (220.0, 224.0)

    hound = StaticHound("hound_boss_catwalk", x=440.0, y=220.0, patrol_left=360.0, patrol_right=520.0)
    hound.state = "PATROL"

    enemy_mgr.add_enemy(drone)
    enemy_mgr.add_enemy(hound)
    enemy_mgr.render(crt.canvas, camera)

    # Player position
    player = Player(x=208.0, y=208.0)
    player.health = 80
    sc_px, sc_py = camera.world_to_screen(player.x, player.y)
    pygame.draw.rect(crt.canvas, config.COLOR_FIBO_GOLD, (sc_px, sc_py, 16, 32), 2)
    pygame.draw.circle(crt.canvas, config.COLOR_FIBO_GOLD, (sc_px + 8, sc_py + 8), 5)

    # Holdout HUD
    holdout = DishDefenseHoldout(total_duration=72.0)
    holdout.start()
    holdout.update(34.0)  # Bin 3 ('Q', 26 sigma)

    campaign = Campaign(save_id="preview_defense")
    obj = Objective(
        id="defend_feedhorn",
        title="DEFEND DISH [34.0s / 72s]",
        description="Repel Core assault waves and prevent feedhorn collapse",
        hint="BIN 3/6 [Q] 26σ (PEAK)",
    )

    sig_disp = holdout.get_signal_display()
    footer = f"[BIN {sig_disp['bin']+1}/6: {sig_disp['code']} ({sig_disp['snr']}σ)]  DISH HP: {int(sig_disp['dish_integrity'])}%  TIME LEFT: {sig_disp['remaining']:.1f}s"

    render_global_hud(
        crt,
        campaign,
        location_label="DISH CATWALK // 72s HOLDOUT DEFENSE",
        footer_text=footer,
        player=player,
        objective=obj,
        threat_level="LOCKED",
    )

    out_path = EVIDENCE_DIR / "03_holdout_combat_encounter_preview.png"
    pygame.image.save(crt.canvas, str(out_path))
    print(f"Saved {out_path.name}")


def generate_04_jammed_feedhorn_card(crt: CRTRenderer):
    """Generate jammed feedhorn alert card and unjam interaction breakdown."""
    crt.clear((6, 9, 12))

    # Outer panel
    pygame.draw.rect(crt.canvas, (10, 16, 22), (10, 10, 460, 250))
    pygame.draw.rect(crt.canvas, (230, 60, 60), (10, 10, 460, 250), 1)

    font_title = "FEEDHORN JAMMING INTERACTION // CRITICAL INTEGRITY DECAY"
    crt.draw_text(font_title, 24, 20, color=(240, 80, 80), size="sm")

    # Alarm banner
    pygame.draw.rect(crt.canvas, (36, 10, 10), (20, 38, 440, 28))
    pygame.draw.rect(crt.canvas, (240, 60, 60), (20, 38, 440, 28), 1)
    crt.draw_text("[!] WARNING: FEEDHORN ARRAY JAMMED BY CORE ELECTRONIC WARFARE", 30, 46, color=(255, 100, 100), size="sm")

    # Integrity gauge visualization
    crt.draw_text("DISH INTEGRITY COLLAPSE DYNAMICS:", 28, 76, color=config.COLOR_FIBO_GOLD, size="sm")
    # Health bar showing 65% remaining with decay rate
    pygame.draw.rect(crt.canvas, (14, 18, 14), (28, 92, 280, 14))
    pygame.draw.rect(crt.canvas, config.COLOR_AMBER_1977, (29, 93, 180, 12))
    pygame.draw.rect(crt.canvas, config.COLOR_CRT_DIM, (28, 92, 280, 14), 1)
    crt.draw_text("65% [ACTIVE DECAY: -1.0 HP/s]", 316, 94, color=config.COLOR_AMBER_1977, size="sm")

    # Step 1: Cause
    pygame.draw.rect(crt.canvas, (12, 18, 22), (20, 116, 440, 38))
    pygame.draw.rect(crt.canvas, config.COLOR_CRT_DIM, (20, 116, 440, 38), 1)
    crt.draw_text("TRIGGER: Scheduled Wave 2 (t=24.0s, Bin 'Q') activates Core jammer mast.", 28, 124, color=config.COLOR_CRT_DIM, size="sm")
    crt.draw_text("EFFECT: Dish integrity drains continuously; hits 0% = MISSION FAILED.", 28, 136, color=(240, 120, 120), size="sm")

    # Step 2: Unjam Counterplay
    pygame.draw.rect(crt.canvas, (12, 24, 16), (20, 162, 440, 44))
    pygame.draw.rect(crt.canvas, config.COLOR_CRT_GREEN, (20, 162, 440, 44), 1)
    crt.draw_text("COUNTERPLAY: Move to Central Feedhorn Mast (x=296) and press [E].", 28, 170, color=config.COLOR_CRT_GREEN, size="sm")
    crt.draw_text("ACTION: holdout.unjam() clears jammer, arrests decay, restores telemetry.", 28, 184, color=config.COLOR_FIBO_GOLD, size="sm")

    # Step 3: Geometry & Checkpoint Recovery
    pygame.draw.rect(crt.canvas, (12, 16, 24), (20, 214, 440, 36))
    pygame.draw.rect(crt.canvas, config.COLOR_CORE_STEEL, (20, 214, 440, 36), 1)
    crt.draw_text("RECOVERY: Failure resets holdout to IDLE, clears waves, respawns at ladder.", 28, 224, color=config.COLOR_CORE_STEEL, size="sm")

    out_path = EVIDENCE_DIR / "04_jammed_feedhorn_and_unjam_interaction.png"
    pygame.image.save(crt.canvas, str(out_path))
    print(f"Saved {out_path.name}")


def generate_05_completion_reward_flow(crt: CRTRenderer):
    """Generate completion reward flow and boss arena progression card."""
    crt.clear((6, 9, 12))

    # Outer panel
    pygame.draw.rect(crt.canvas, (10, 16, 22), (10, 10, 460, 250))
    pygame.draw.rect(crt.canvas, config.COLOR_CRT_GREEN, (10, 10, 460, 250), 1)

    font_title = "72-SECOND DEFENSE COMPLETION // ACT I PROGRESSION REWARDS"
    crt.draw_text(font_title, 24, 20, color=config.COLOR_CRT_GREEN, size="sm")

    # Step 1: Exactly 72.0s
    pygame.draw.rect(crt.canvas, (14, 24, 18), (20, 40, 440, 46))
    pygame.draw.rect(crt.canvas, config.COLOR_CRT_GREEN, (20, 40, 440, 46), 1)
    crt.draw_text("STAGE 1: 72.0 SECONDS OF ACCUMULATED ACTIVE SIMULATION TIME", 30, 46, color=config.COLOR_CRT_GREEN, size="sm")
    crt.draw_text("Condition: elapsed_time >= 72.0s and dish_integrity > 0.0%", 30, 58, color=config.COLOR_CRT_DIM, size="sm")
    crt.draw_text("State Transition: HOLDOUT_ACTIVE -> HOLDOUT_COMPLETED", 30, 70, color=config.COLOR_FIBO_GOLD, size="sm")

    # Step 2: Campaign Event
    pygame.draw.rect(crt.canvas, (14, 20, 26), (20, 94, 440, 46))
    pygame.draw.rect(crt.canvas, config.COLOR_FIBO_GOLD, (20, 94, 440, 46), 1)
    crt.draw_text("STAGE 2: ATOMIC CAMPAIGN EVENT GRANT", 30, 100, color=config.COLOR_FIBO_GOLD, size="sm")
    crt.draw_text("Event: complete_dish_defense  |  Flag: dish_defense_completed = True", 30, 112, color=config.COLOR_CRT_DIM, size="sm")
    crt.draw_text("Meters: Scientific Certainty +10, Alignment Confidence +5, Human Agency +5", 30, 124, color=config.COLOR_CRT_GREEN, size="sm")

    # Step 3: Replay Idempotence
    pygame.draw.rect(crt.canvas, (14, 18, 22), (20, 148, 440, 46))
    pygame.draw.rect(crt.canvas, config.COLOR_CORE_STEEL, (20, 148, 440, 46), 1)
    crt.draw_text("STAGE 3: REPLAY IDEMPOTENCE & PERSISTENCE", 30, 154, color=config.COLOR_CORE_STEEL, size="sm")
    crt.draw_text("Re-defense replay returns False (0 duplicate rewards, 0 corrupted state).", 30, 166, color=config.COLOR_CRT_DIM, size="sm")
    crt.draw_text("Disk save preserves completion flag permanently across sessions.", 30, 178, color=config.COLOR_CRT_DIM, size="sm")

    # Step 4: Next Milestone
    pygame.draw.rect(crt.canvas, (20, 14, 24), (20, 202, 440, 46))
    pygame.draw.rect(crt.canvas, (200, 120, 255), (20, 202, 440, 46), 1)
    crt.draw_text("STAGE 4: UNLOCKS MILESTONE 2 TASK A09 (GREENKEEPER BOSS ARENA)", 30, 208, color=(220, 150, 255), size="sm")
    crt.draw_text("Objective: Infiltrate deep reflector basin and confront Core Warden Greenkeeper.", 30, 222, color=config.COLOR_AMBER_1977, size="sm")

    out_path = EVIDENCE_DIR / "05_mission_completion_reward_flow.png"
    pygame.image.save(crt.canvas, str(out_path))
    print(f"Saved {out_path.name}")


def main():
    ensure_evidence_dir()
    pygame.init()
    pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    crt = CRTRenderer(scale=1)

    generate_01_signal_bins_telemetry(crt)
    generate_02_catwalk_level_blockout(crt)
    generate_03_holdout_combat_preview(crt)
    generate_04_jammed_feedhorn_card(crt)
    generate_05_completion_reward_flow(crt)

    print("All A08 visual evidence previews generated successfully.")


if __name__ == "__main__":
    main()
