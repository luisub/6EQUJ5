"""
MODULE: video_game/engine/ui/hud.py
PURPOSE: Draw shared global HUD, player status, prediction-lock alerts, and dossier overlay.
CALLED BY: GameStateMachine, BunkerHubScene, FieldOpsScene.
HOW TO MODIFY: Keep layout disjoint with zero element overlap and maintain font scaling.
"""

import pygame
from .. import config


def _fit_label(font, text, width):
    """Fit a label into its allocated HUD column using the actual font."""
    if font.size(text)[0] <= width:
        return text
    while text and font.size(text + "...")[0] > width:
        text = text[:-1]
    return text + "..." if text else ""


def render_global_hud(
    crt,
    campaign,
    location_label: str = "",
    footer_text: str = None,
    player=None,
    objective=None,
    notification=None,
    threat_level: str = None,
):
    """
    Render standard scanline HUD with health gauge, active weapon, objective snippet,
    threat feedback, and failure notifications in mathematically disjoint bounding zones.
    """
    # 1. Top Bar (y: 0 - 16)
    pygame.draw.rect(crt.canvas, (5, 14, 9), (0, 0, config.INTERNAL_WIDTH, 16))
    pygame.draw.line(crt.canvas, config.COLOR_CRT_DIM, (0, 16), (config.INTERNAL_WIDTH, 16), 1)

    # Location label (x: 6)
    loc = location_label if location_label else "OHIO BIG EAR FACILITY"
    crt.draw_text(_fit_label(crt.font_sm, f"6EQUJ5 // {loc}", 216), 6, 3, color=config.COLOR_CRT_GREEN, size="sm")

    # Objective snippet in top bar center (x: 230 - 370)
    if objective is not None:
        obj_text = f"OBJ: {objective.title}"
        obj_text = _fit_label(crt.font_sm, obj_text, 153)
        crt.draw_text(obj_text, 230, 3, color=config.COLOR_FIBO_GOLD, size="sm")

    # Timeline mode indicator (x: 390 - 476)
    tl_mode = getattr(campaign, "timeline_mode", "2029_CORE")
    tl_color = config.COLOR_AMBER_1977 if tl_mode == "1977_ANALOG" else config.COLOR_CORE_STEEL
    crt.draw_text(f"[{tl_mode}]", 390, 3, color=tl_color, size="sm")

    # 2. Combat & Player Stats (when player is present, e.g. in FieldOpsScene)
    # Zone: x: 8 - 140, y: 19 - 34 (completely below top bar)
    if player is not None:
        # Health gauge
        cur_hp = max(0, getattr(player, "health", 100))
        max_hp = 100
        hp_ratio = min(1.0, max(0.0, cur_hp / max_hp))

        if hp_ratio > 0.50:
            hp_color = config.COLOR_CRT_GREEN
        elif hp_ratio > 0.25:
            hp_color = config.COLOR_AMBER_1977
        else:
            hp_color = (230, 40, 40)

        crt.draw_text(f"HP {cur_hp:3d}", 8, 19, color=hp_color, size="sm")

        # Gauge bar (x: 48, y: 21, w: 56, h: 6)
        pygame.draw.rect(crt.canvas, (10, 18, 14), (48, 21, 56, 6))
        fill_w = int(54 * hp_ratio)
        if fill_w > 0:
            pygame.draw.rect(crt.canvas, hp_color, (49, 22, fill_w, 4))
        pygame.draw.rect(crt.canvas, config.COLOR_CRT_DIM, (48, 21, 56, 6), 1)

        # Active Weapon info (x: 8, y: 27)
        wpn_name = "MASER 1420"
        if hasattr(player, "weapon") and player.weapon is not None:
            wpn_name = getattr(player.weapon, "name", "MASER 1420")[:14].upper()
        crt.draw_text(wpn_name, 8, 27, color=config.COLOR_CRT_DIM, size="sm")

        # Active Ability info (x: 8, y: 35)
        if hasattr(player, "abilities") and player.abilities is not None:
            ab = player.abilities.selected_ability
            if ab.is_unlocked:
                ab_state = f"{ab.name[:10].upper()}"
                ab_col = config.COLOR_ARC_CYAN
                if ab.is_active:
                    ab_state += f" [{ab.active_timer:.1f}s]"
                    ab_col = config.COLOR_CRT_GREEN
                elif ab.cooldown_timer > 0.0:
                    ab_state += f" ({ab.cooldown_timer:.1f}s)"
                    ab_col = config.COLOR_AMBER_1977
                crt.draw_text(_fit_label(crt.font_sm, ab_state, 106), 8, 35, color=ab_col, size="sm")

        # Charge progress indicator if charging
        charge_timer = getattr(player, "charge_timer", 0.0)
        charge_thresh = getattr(player, "charge_threshold", 0.60)
        if charge_timer > 0.0 and charge_thresh > 0.0:
            chg_ratio = min(1.0, charge_timer / charge_thresh)
            chg_w = int(36 * chg_ratio)
            pygame.draw.rect(crt.canvas, (14, 14, 8), (72, 28, 38, 5))
            if chg_w > 0:
                c_col = config.COLOR_FIBO_GOLD if chg_ratio >= 1.0 else (180, 160, 40)
                pygame.draw.rect(crt.canvas, c_col, (73, 29, chg_w, 3))
            pygame.draw.rect(crt.canvas, config.COLOR_CRT_DIM, (72, 28, 38, 5), 1)

    # 3. Threat Feedback / Prediction-Lock Alert
    # Zone: x: 155 - 325, y: 18 - 31 (centered, completely disjoint from player stats on left)
    if threat_level == "LOCKED":
        alert_box = (155, 18, 170, 13)
        pygame.draw.rect(crt.canvas, (40, 6, 6), alert_box)
        pygame.draw.rect(crt.canvas, (240, 50, 50), alert_box, 1)
        crt.draw_text("[!] LOCK-ON: EVADE NOW!", 162, 20, color=(255, 80, 80), size="sm")
    elif threat_level == "AIMING":
        alert_box = (155, 18, 170, 13)
        pygame.draw.rect(crt.canvas, (25, 20, 6), alert_box)
        pygame.draw.rect(crt.canvas, config.COLOR_AMBER_1977, alert_box, 1)
        crt.draw_text("[*] TARGETING DETECTED", 165, 20, color=config.COLOR_AMBER_1977, size="sm")

    # 4. Notification / Failure Reason Banner
    # Zone: x: 140 - 474, y: 34 - 47 (clear of the ability label at left)
    if notification is not None:
        title = getattr(notification, "title", "NOTICE")
        text = getattr(notification, "text", "")
        kind = getattr(notification, "kind", "info")

        if kind == "success":
            b_col = config.COLOR_CRT_GREEN
            bg_col = (4, 22, 10)
        elif kind == "warning":
            b_col = config.COLOR_AMBER_1977
            bg_col = (24, 18, 4)
        elif kind == "danger":
            b_col = (230, 50, 50)
            bg_col = (30, 6, 6)
        else:
            b_col = config.COLOR_FIBO_GOLD
            bg_col = (8, 16, 20)

        notif_rect = (140, 34, 334, 13)
        pygame.draw.rect(crt.canvas, bg_col, notif_rect)
        pygame.draw.rect(crt.canvas, b_col, notif_rect, 1)

        full_msg = f"[{title}] {text}"
        full_msg = _fit_label(crt.font_sm, full_msg, 322)
        crt.draw_text(full_msg, 146, 36, color=b_col, size="sm")

    # 5. Bottom Bar (y: 254 - 270)
    pygame.draw.rect(crt.canvas, (5, 12, 8), (0, 254, config.INTERNAL_WIDTH, 16))
    pygame.draw.line(crt.canvas, config.COLOR_CRT_DIM, (0, 254), (config.INTERNAL_WIDTH, 254), 1)
    if footer_text is None:
        footer_text = "[A/D] MOVE  [E] INTERACT  [TAB] DOSSIER  [F5] SAVE  [ESC] PAUSE"
    crt.draw_text(footer_text, 6, 257, color=config.COLOR_FIBO_GOLD, size="sm")


def render_dossier_overlay(crt, campaign, objective=None):
    """
    Render full-screen authentic CRT dossier inspection overlay exposing
    all campaign meters, active mission objective, fragments, and inventory.
    """
    # Dim background
    overlay_dim = pygame.Surface((config.INTERNAL_WIDTH, config.INTERNAL_HEIGHT), pygame.SRCALPHA)
    overlay_dim.fill((4, 7, 10, 220))
    crt.canvas.blit(overlay_dim, (0, 0))

    panel_rect = (16, 20, 448, 226)
    crt.draw_panel(
        panel_rect,
        bg_color=(6, 12, 16),
        border_color=config.COLOR_CRT_GREEN,
        title="BIG EAR DOSSIER // CAMPAIGN METRICS & MISSION STATUS",
    )

    state = campaign.state

    # Left Column: Mission, Objective, and Inventory (x: 28 - 220)
    act_label = getattr(campaign, "current_act_label", "ACT I: OHIO BIG EAR")
    crt.draw_text(f"OPERATION: {act_label}", 28, 40, color=config.COLOR_FIBO_GOLD, size="sm")

    # Objective
    if objective is not None:
        crt.draw_text(f"ACTIVE OBJECTIVE: {objective.title}", 28, 54, color=config.COLOR_CRT_GREEN, size="sm")
        crt.draw_text(f"DETAILS: {objective.description}", 28, 66, color=config.COLOR_CRT_DIM, size="sm")
        crt.draw_text(f"HINT: {objective.hint}", 28, 78, color=config.COLOR_AMBER_1977, size="sm")
    else:
        crt.draw_text("OBJECTIVE: PROCEED THROUGH BUNKER", 28, 54, color=config.COLOR_CRT_GREEN, size="sm")

    # Horizontal divider
    pygame.draw.line(crt.canvas, config.COLOR_CRT_DIM, (28, 92), (220, 92), 1)

    # Inventory
    crt.draw_text("EQUIPMENT & INVENTORY:", 28, 98, color=config.COLOR_FIBO_GOLD, size="sm")
    inv = getattr(state, "inventory", {})
    y_inv = 110
    if "maser_1420" in inv:
        crt.draw_text("* 1420 MHz Waveguide Maser [READY]", 32, y_inv, color=config.COLOR_CRT_GREEN, size="sm")
        y_inv += 11
    if inv.get("analog_coupler", 0) > 0:
        crt.draw_text("* Analog Feedhorn Coupler [READY]", 32, y_inv, color=config.COLOR_AMBER_1977, size="sm")
        y_inv += 11
    if state.room_flags.get("feedhorn_repaired", False):
        crt.draw_text("* Dish Feedhorn Array: OPERATIONAL", 32, y_inv, color=config.COLOR_CRT_GREEN, size="sm")
        y_inv += 11

    # Signal Intelligence
    pygame.draw.line(crt.canvas, config.COLOR_CRT_DIM, (28, y_inv + 4), (220, y_inv + 4), 1)
    y_sig = y_inv + 10
    crt.draw_text("SIGNAL RECONNAISSANCE:", 28, y_sig, color=config.COLOR_FIBO_GOLD, size="sm")
    n_contacted = len(getattr(state, "contacted_civs", []))
    n_frags = len(getattr(state, "extracted_fragments", []))
    n_valid = len(getattr(state, "validation_records", []))
    crt.draw_text(f"* Contacts Established: {n_contacted} / 11", 32, y_sig + 12, color=config.COLOR_CRT_DIM, size="sm")
    crt.draw_text(f"* Extracted Fragments: {n_frags} / 11", 32, y_sig + 23, color=config.COLOR_CRT_DIM, size="sm")
    crt.draw_text(f"* Scientific Protocols: {n_valid} / 11", 32, y_sig + 34, color=config.COLOR_CRT_DIM, size="sm")

    # Vertical Column Divider (x: 232)
    pygame.draw.line(crt.canvas, config.COLOR_CRT_DIM, (232, 38), (232, 230), 1)

    # Right Column: Campaign Meters (x: 242 - 450)
    crt.draw_text("CAMPAIGN METERS (0 - 100%):", 242, 40, color=config.COLOR_FIBO_GOLD, size="sm")

    meter_labels = [
        ("scientific_certainty", "Scientific Certainty"),
        ("alignment_confidence", "Alignment Confidence"),
        ("coordination_capacity", "Coordination Capacity"),
        ("public_trust", "Public Trust"),
        ("human_agency", "Human Agency"),
        ("biosecurity_readiness", "Biosecurity Readiness"),
    ]

    meters = getattr(state, "meters", {})
    y_m = 54
    for key, label in meter_labels:
        val = meters.get(key, 50)
        crt.draw_text(f"{label}: {val:3d}%", 242, y_m, color=config.COLOR_CRT_GREEN, size="sm")

        # Bar gauge (x: 242, y: y_m + 11, w: 190, h: 6)
        pygame.draw.rect(crt.canvas, (10, 18, 14), (242, y_m + 11, 190, 6))
        fill_w = int(188 * (val / 100.0))
        if fill_w > 0:
            b_color = config.COLOR_CRT_GREEN if val >= 50 else config.COLOR_AMBER_1977
            pygame.draw.rect(crt.canvas, b_color, (243, y_m + 12, fill_w, 4))
        pygame.draw.rect(crt.canvas, config.COLOR_CRT_DIM, (242, y_m + 11, 190, 6), 1)

        y_m += 22

    # Dossier Footer inside panel
    crt.draw_text("[TAB / ESC] CLOSE DOSSIER VIEW", 140, 234, color=config.COLOR_FIBO_GOLD, size="sm")
