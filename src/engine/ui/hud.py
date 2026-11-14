"""
MODULE: video_game/engine/ui/hud.py
PURPOSE: Draw shared global HUD, player status, prediction-lock alerts, and dossier overlay.
CALLED BY: GameStateMachine, BunkerHubScene, FieldOpsScene.
HOW TO MODIFY: Keep layout disjoint with zero element overlap and maintain font scaling.
"""

import pygame
from .. import config
from ..temporary_weapons import WEAPON_TIMER_RECT
from .text import wrap_text_pixels


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
    threat_y: int = 18,
    staging_cleared: bool = False,
):
    """Draw only the current goal, health, and time-sensitive alerts.

    Full mission and equipment details remain available in the dossier.  The
    legacy location and footer arguments are accepted for existing callers.
    """
    labels = []
    hud_bottom = 48
    if player is not None:
        hp = max(0, getattr(player, "health", 100))
        ratio = min(1.0, hp / 100.0)
        color = (config.COLOR_CRT_GREEN if ratio > 0.5 else
                 config.COLOR_AMBER_1977 if ratio > 0.25 else (230, 40, 40))
        pygame.draw.rect(crt.canvas, (5, 14, 9), (5, 4, 105, 12))
        pygame.draw.rect(crt.canvas, config.COLOR_CRT_DIM, (48, 7, 58, 6), 1)
        if ratio > 0:
            pygame.draw.rect(crt.canvas, color, (49, 8, int(56 * ratio), 4))
        labels.append((f"HP {hp:3d}", 8, 5, color))

        charge = getattr(player, "charge_timer", 0.0)
        threshold = getattr(player, "charge_threshold", 0.60)
        if charge > 0 and threshold > 0:
            pygame.draw.rect(crt.canvas, (5, 14, 9), (48, 17, 58, 5))
            pygame.draw.rect(crt.canvas, config.COLOR_FIBO_GOLD,
                             (49, 18, int(56 * min(1.0, charge / threshold)), 3))

    if objective is not None:
        x = 120 if player is not None else 6
        title = _fit_label(crt.font_sm, objective.title, config.INTERNAL_WIDTH - x - 14)
        width = crt.font_sm.size(title)[0] + 15
        pygame.draw.rect(crt.canvas, (5, 14, 9), (x, 3, width, 14))
        pygame.draw.circle(crt.canvas, config.COLOR_FIBO_GOLD, (x + 5, 10), 2)
        labels.append((title, x + 11, 5, config.COLOR_FIBO_GOLD))

    # Alerts stay at the top, away from the character and interaction button.
    if notification is not None:
        kind = getattr(notification, "kind", "info")
        color = {"success": config.COLOR_CRT_GREEN, "warning": config.COLOR_AMBER_1977,
                 "danger": (230, 50, 50)}.get(kind, config.COLOR_FIBO_GOLD)
        message = getattr(notification, 'title', 'NOTICE')
        if getattr(notification, 'text', ''):
            message += ': ' + notification.text
        arsenal = getattr(player, 'arsenal', None)
        # Leave the right-hand countdown visible alongside long notifications.
        right = WEAPON_TIMER_RECT.left - 6 if getattr(arsenal, 'temporary_id', None) else 478
        message = _fit_label(crt.font_sm, message, right - 120 - 12)
        width = crt.font_sm.size(message)[0] + 12
        pygame.draw.rect(crt.canvas, (5, 14, 9), (120, 19, width, 13))
        pygame.draw.rect(crt.canvas, color, (120, 19, width, 13), 1)
        labels.append((message, 126, 21, color))

    if threat_level in ("LOCKED", "AIMING"):
        color = (255, 80, 80) if threat_level == "LOCKED" else config.COLOR_AMBER_1977
        message = "[!] LOCK-ON: EVADE NOW!" if threat_level == "LOCKED" else "TARGETED"
        y = max(threat_y, 34 if notification is not None else 19)
        hud_bottom = max(hud_bottom, int(y) + 14)
        width = crt.font_sm.size(message)[0] + 12
        pygame.draw.rect(crt.canvas, (20, 7, 6), (120, y, width, 13))
        pygame.draw.rect(crt.canvas, color, (120, y, width, 13), 1)
        labels.append((message, 126, y + 2, color))

    # All four HUD sections occupy disjoint areas. Flush their staged
    # backgrounds together before drawing their native-density text. A caller
    # that has just flushed the scene can restrict this to HUD-owned pixels.
    if labels:
        region = (0, 0, config.INTERNAL_WIDTH, hud_bottom) if staging_cleared is True else None
        with crt.text_batch(dirty_region=region):
            for text, x, y, color in labels:
                crt.draw_text(text, x, y, color=color, size="sm")


def dossier_lines(crt, campaign, objective=None):
    """Wrap complete left-column contents into individually scrollable rows."""
    state = campaign.state
    entries = []
    if objective is not None:
        entries.extend([(f"OBJECTIVE: {objective.title}", config.COLOR_CRT_GREEN),
                        (f"DETAILS: {objective.description}", config.COLOR_CRT_DIM),
                        (f"HINT: {objective.hint}", config.COLOR_AMBER_1977)])
    else:
        entries.append(("OBJECTIVE: PROCEED THROUGH BUNKER", config.COLOR_CRT_GREEN))
    entries.append(("EQUIPMENT & INVENTORY:", config.COLOR_FIBO_GOLD))
    inv = getattr(state, 'inventory', {})
    if 'maser_1420' in inv:
        entries.append(("* 1420 MHz Waveguide Maser [READY]", config.COLOR_CRT_GREEN))
    if inv.get('analog_coupler', 0) > 0:
        entries.append(("* Analog Feedhorn Coupler [READY]", config.COLOR_AMBER_1977))
    if state.room_flags.get('feedhorn_repaired', False):
        entries.append(("* Dish Feedhorn Array: OPERATIONAL", config.COLOR_CRT_GREEN))
    entries.extend([("SIGNAL RECONNAISSANCE:", config.COLOR_FIBO_GOLD),
                    (f"* Contacts Established: {len(getattr(state, 'contacted_civs', []))} / 11", config.COLOR_CRT_DIM),
                    (f"* Extracted Fragments: {len(getattr(state, 'extracted_fragments', []))} / 11", config.COLOR_CRT_DIM),
                    (f"* Scientific Protocols: {len(getattr(state, 'validation_records', []))} / 11", config.COLOR_CRT_DIM)])
    return [(line, color) for text, color in entries for line in wrap_text_pixels(text, crt.font_sm, 190)]


def render_dossier_overlay(crt, campaign, objective=None, scroll_offset=0):
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

    lines = dossier_lines(crt, campaign, objective)
    start = max(0, min(scroll_offset, max(0, len(lines) - 15)))
    with crt.text_batch():
        for index, (line, color) in enumerate(lines[start:start + 15]):
            crt.draw_text(line, 28, 54 + index * 11, color=color, size="sm")

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
    crt.draw_text("[UP/DOWN] SCROLL  [TAB/ESC] CLOSE", 120, 234, color=config.COLOR_FIBO_GOLD, size="sm")
