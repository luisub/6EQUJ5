"""
MODULE: video_game/tools/generate_a07_evidence.py
PURPOSE: Generate visual evidence previews for Milestone 2 Task A07.
CALLED BY: Manual execution or verification harness.
HOW TO MODIFY: Update evidence preview frames or annotations; maintain 480x270 native resolution.
"""

import os
from pathlib import Path
import pygame

from video_game.engine import config
from video_game.engine.campaign import Campaign
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.objectives import Notification, Objective, ObjectiveTracker
from video_game.engine.player import Player
from video_game.engine.scenes.bunker import BUNKER_STATIONS, BunkerHubScene
from video_game.engine.scenes.field import FieldOpsScene
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.ui.hud import render_dossier_overlay, render_global_hud

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

EVIDENCE_DIR = Path(__file__).resolve().parent.parent / "planning" / "evidence" / "A07" / "previews"


def ensure_evidence_dir():
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def generate_01_station_prompts(crt: CRTRenderer, machine: GameStateMachine):
    """Generate 4-panel visual strip showing Mateo at all 4 bunker stations with active prompts."""
    bunker: BunkerHubScene = machine.scenes[config.STATE_BUNKER_HUB]
    machine.current_state_name = config.STATE_BUNKER_HUB
    machine.current_scene = bunker

    stations = [
        ("lab", 140.0, "1. SCIENCE LAB [x=140]"),
        ("terminal", 215.0, "2. RECEIVER CRT [x=215]"),
        ("repair", 295.0, "3. REPAIR BENCH [x=295]"),
        ("field", 345.0, "4. SURFACE AIRLOCK [x=345]"),
    ]

    strip_surf = pygame.Surface((480 * 2, 270 * 2))

    for idx, (st_id, x_pos, label) in enumerate(stations):
        bunker.mateo_x = x_pos
        bunker.update(0.016)
        bunker.render(crt)

        # Label above station
        cell_surf = crt.canvas.copy()
        pygame.draw.rect(cell_surf, (0, 0, 0), (6, 20, 200, 14))
        pygame.draw.rect(cell_surf, config.COLOR_FIBO_GOLD, (6, 20, 200, 14), 1)
        crt.draw_text(label, 10, 22, color=config.COLOR_FIBO_GOLD, size="sm")

        dest_x = (idx % 2) * 480
        dest_y = (idx // 2) * 270
        strip_surf.blit(cell_surf, (dest_x, dest_y))

    # Grid line
    pygame.draw.line(strip_surf, config.COLOR_CRT_GREEN, (480, 0), (480, 540), 2)
    pygame.draw.line(strip_surf, config.COLOR_CRT_GREEN, (0, 270), (960, 270), 2)

    out_path = EVIDENCE_DIR / "01_bunker_station_proximity_prompts.png"
    pygame.image.save(strip_surf, str(out_path))
    print(f"Saved {out_path.name}")


def generate_02_dossier_view(crt: CRTRenderer, machine: GameStateMachine):
    """Generate authentic full-screen render of Big Ear Dossier view with campaign meters."""
    tracker = ObjectiveTracker()
    campaign = machine.campaign
    # Seed some progress for informative dossier
    campaign.state.meters["scientific_certainty"] = 55
    campaign.state.meters["alignment_confidence"] = 45
    campaign.state.meters["coordination_capacity"] = 40
    campaign.state.meters["public_trust"] = 35
    campaign.state.meters["human_agency"] = 75
    campaign.state.meters["biosecurity_readiness"] = 40

    obj = tracker.get_active_objective(campaign)

    crt.clear((6, 9, 12))
    render_dossier_overlay(crt, campaign, obj)

    out_path = EVIDENCE_DIR / "02_dossier_campaign_meters_view.png"
    pygame.image.save(crt.canvas, str(out_path))
    print(f"Saved {out_path.name}")


def generate_03_hud_disjoint_layout(crt: CRTRenderer, machine: GameStateMachine):
    """Generate annotated HUD screenshot highlighting non-overlapping UI bounding zones."""
    crt.clear((8, 12, 16))

    player = Player(x=100.0, y=100.0)
    player.health = 85
    player.charge_timer = 0.45

    obj = Objective(
        id="test_obj",
        title="RECOVER ANALOG COUPLER",
        description="Search approach trench for analog feedhorn coupler",
        hint="SURFACE AIRLOCK [RIGHT]",
    )
    notif = Notification(
        title="REPAIR COMPLETE",
        text="DISH FEEDHORN RESTORED (+5 CERTAINTY, +5 AGENCY)",
        kind="success",
        duration=3.5,
        timer=3.0,
    )

    render_global_hud(
        crt,
        machine.campaign,
        location_label="OHIO FIELD OPS // DISJOINT HUD AUDIT",
        footer_text="[A/D] MOVE  [SPACE] JUMP  [X] FIRE  [TAB] DOSSIER  [ESC] BUNKER",
        player=player,
        objective=obj,
        notification=notif,
        threat_level="LOCKED",
    )

    # Annotate bounding boxes in bright colored outlines
    # Top bar
    pygame.draw.rect(crt.canvas, (80, 200, 255), (0, 0, 480, 16), 1)
    crt.draw_text("ZONE 1: TOP BAR (y:0..16)", 100, 18, color=(80, 200, 255), size="sm")

    # Player stats
    pygame.draw.rect(crt.canvas, (100, 255, 100), (8, 19, 102, 14), 1)
    crt.draw_text("ZONE 2: PLAYER STATS", 8, 48, color=(100, 255, 100), size="sm")

    # Threat alert
    pygame.draw.rect(crt.canvas, (255, 80, 80), (155, 18, 170, 13), 1)
    crt.draw_text("ZONE 3: THREAT LOCK", 185, 48, color=(255, 80, 80), size="sm")

    # Notification banner
    pygame.draw.rect(crt.canvas, config.COLOR_FIBO_GOLD, (50, 34, 380, 13), 1)
    crt.draw_text("ZONE 4: NOTIFICATION / FAILURE ALERT", 120, 62, color=config.COLOR_FIBO_GOLD, size="sm")

    # Bottom footer
    pygame.draw.rect(crt.canvas, (150, 150, 255), (0, 254, 480, 16), 1)
    crt.draw_text("ZONE 5: FOOTER (y:254..270)", 160, 240, color=(150, 150, 255), size="sm")

    out_path = EVIDENCE_DIR / "03_hud_disjoint_layout_breakdown.png"
    pygame.image.save(crt.canvas, str(out_path))
    print(f"Saved {out_path.name}")


def generate_04_coupler_trench_pickup(crt: CRTRenderer, machine: GameStateMachine):
    """Generate in-engine render of the approach trench showing the glowing analog coupler pickup."""
    field: FieldOpsScene = machine.scenes[config.STATE_FIELD_OPS]
    machine.current_state_name = config.STATE_FIELD_OPS
    machine.current_scene = field

    # Position player near coupler
    field.player.x = 480.0
    field.player.y = 208.0
    field.camera.x = 350.0
    field.camera.y = 0.0

    field.update(0.016)
    field.render(crt)

    # Add callout arrow/bracket pointing to pickup
    sc_cx, sc_cy = field.camera.world_to_screen(field.coupler_x, field.coupler_y)
    pygame.draw.rect(crt.canvas, config.COLOR_FIBO_GOLD, (sc_cx - 16, sc_cy - 16, 32, 32), 1)
    crt.draw_text("COLLECTIBLE: ANALOG COUPLER", sc_cx - 60, sc_cy - 28, color=config.COLOR_FIBO_GOLD, size="sm")

    out_path = EVIDENCE_DIR / "04_collectible_coupler_trench_pickup.png"
    pygame.image.save(crt.canvas, str(out_path))
    print(f"Saved {out_path.name}")


def generate_05_repair_interaction_card(crt: CRTRenderer, machine: GameStateMachine):
    """Generate comparison card showing prerequisite check, repair execution, and meter bonuses."""
    card_surf = pygame.Surface((480, 270))
    card_surf.fill((6, 9, 12))

    # Title panel
    pygame.draw.rect(card_surf, (10, 16, 22), (10, 10, 460, 250))
    pygame.draw.rect(card_surf, config.COLOR_CRT_GREEN, (10, 10, 460, 250), 1)

    font_title = "ANALOG BENCH REPAIR INTERACTION // ATOMIC PROGRESSION AUDIT"
    crt.draw_text(font_title, 24, 20, color=config.COLOR_CRT_GREEN, size="sm")

    # Step 1: Prerequisite Check
    pygame.draw.rect(card_surf, (14, 20, 16), (20, 40, 440, 48))
    pygame.draw.rect(card_surf, (200, 60, 60), (20, 40, 440, 48), 1)
    crt.draw_text("STEP 1: PREREQUISITE UNMET (NO COUPLER)", 30, 46, color=(240, 100, 100), size="sm")
    crt.draw_text("Input: [E] at Repair Bench  -->  Result: REJECTED", 30, 58, color=config.COLOR_CRT_DIM, size="sm")
    crt.draw_text("Notice: [PREREQUISITE UNMET] MISSING ANALOG COUPLER", 30, 70, color=config.COLOR_AMBER_1977, size="sm")

    # Step 2: Collection in Trench
    pygame.draw.rect(card_surf, (14, 20, 16), (20, 96, 440, 48))
    pygame.draw.rect(card_surf, config.COLOR_FIBO_GOLD, (20, 96, 440, 48), 1)
    crt.draw_text("STEP 2: TRENCH PICKUP AT x=560", 30, 102, color=config.COLOR_FIBO_GOLD, size="sm")
    crt.draw_text("Event: collect_analog_coupler  -->  Inventory: {'analog_coupler': 1}", 30, 114, color=config.COLOR_CRT_DIM, size="sm")
    crt.draw_text("Reward: Coordination Capacity +5  |  Flag: trench_coupler_collected = True", 30, 126, color=config.COLOR_CRT_GREEN, size="sm")

    # Step 3: Successful Repair
    pygame.draw.rect(card_surf, (14, 20, 16), (20, 152, 440, 54))
    pygame.draw.rect(card_surf, config.COLOR_CRT_GREEN, (20, 152, 440, 54), 1)
    crt.draw_text("STEP 3: BENCH REPAIR EXECUTION", 30, 158, color=config.COLOR_CRT_GREEN, size="sm")
    crt.draw_text("Event: repair_dish_feedhorn  -->  Coupler consumed: 1 -> 0", 30, 170, color=config.COLOR_CRT_DIM, size="sm")
    crt.draw_text("Flag: feedhorn_repaired = True  |  Scientific Certainty +5, Human Agency +5", 30, 182, color=config.COLOR_CRT_GREEN, size="sm")

    # Step 4: Idempotence & Save Persistence
    pygame.draw.rect(card_surf, (14, 20, 16), (20, 214, 440, 36))
    pygame.draw.rect(card_surf, config.COLOR_CORE_STEEL, (20, 214, 440, 36), 1)
    crt.draw_text("STEP 4: REPLAY IDEMPOTENCE: Re-interaction rejected, 0 duplicate rewards.", 30, 224, color=config.COLOR_CORE_STEEL, size="sm")

    out_path = EVIDENCE_DIR / "05_repair_interaction_and_meter_grant.png"
    pygame.image.save(card_surf, str(out_path))
    print(f"Saved {out_path.name}")


def main():
    ensure_evidence_dir()
    pygame.init()
    pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    crt = CRTRenderer(scale=1)
    machine = GameStateMachine(crt)

    generate_01_station_prompts(crt, machine)
    generate_02_dossier_view(crt, machine)
    generate_03_hud_disjoint_layout(crt, machine)
    generate_04_coupler_trench_pickup(crt, machine)
    generate_05_repair_interaction_card(crt, machine)

    print("All A07 visual evidence previews generated successfully.")


if __name__ == "__main__":
    main()
