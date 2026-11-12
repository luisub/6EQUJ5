"""
MODULE: video_game/engine/flashback.py
PURPOSE: Manage the playable August 1977 Big Ear Dr. Jerry Ehman flashback state machine, research interactions, printout annotations, and reality anchor return snapshot rules.
CALLED BY: video_game.engine.scenes.field, video_game.tests.test_flashback.
HOW TO MODIFY: Define new interaction stages, printout telemetry lines, or return inventory rules; maintain zero wildcard imports.
"""

from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import pygame

from video_game.engine import config
from video_game.engine.ui.text import wrap_text_pixels


class FlashbackStage(str, Enum):
    """Progressive narrative and mechanical stages of the 1977 flashback."""
    ENTERED = "ENTERED"
    PRINTOUT_INSPECTED = "PRINTOUT_INSPECTED"
    ANNOTATION_APPLIED = "ANNOTATION_APPLIED"
    REEL_RETRIEVED = "REEL_RETRIEVED"
    ANCHOR_LOCKED = "ANCHOR_LOCKED"
    COMPLETED = "COMPLETED"


@dataclass
class FlashbackSnapshot:
    """
    Preserved state snapshot of present-day (2029) player and equipment.
    Restored cleanly upon completing or exiting the 1977 historical flashback.
    """
    origin_room: str = "bunker_hub"
    origin_spawn: str = "bunker_start"
    saved_health: int = 100
    saved_inventory: Dict[str, int] = field(default_factory=dict)
    saved_unlocked_weapons: List[str] = field(default_factory=list)
    saved_active_weapon: str = "maser_1420"
    saved_unlocked_abilities: List[str] = field(default_factory=list)
    saved_timeline: str = "2029_CORE"

    @classmethod
    def capture(
        cls,
        player: Any,
        campaign: Any,
        origin_room: str = "bunker_hub",
        origin_spawn: str = "bunker_start",
    ) -> "FlashbackSnapshot":
        """Capture present-day player and campaign state before transitioning to 1977."""
        inv = deepcopy(campaign.state.inventory) if hasattr(campaign, "state") else {}
        weps = list(campaign.state.unlocked_weapons) if hasattr(campaign, "state") else ["maser_1420"]
        active_wep = getattr(getattr(player, "arsenal", None), "active_weapon_id", None)
        if not active_wep:
            active_wep = campaign.state.active_weapon if hasattr(campaign, "state") else "starter_maser"
        abils = list(campaign.state.unlocked_abilities) if hasattr(campaign, "state") else []
        timeline = campaign.state.timeline_mode if hasattr(campaign, "state") else "2029_CORE"

        return cls(
            origin_room=origin_room,
            origin_spawn=origin_spawn,
            saved_health=int(getattr(player, "health", 100)),
            saved_inventory=inv,
            saved_unlocked_weapons=weps,
            saved_active_weapon=str(active_wep),
            saved_unlocked_abilities=abils,
            saved_timeline=timeline,
        )

    def apply_return(self, player: Any, campaign: Any) -> None:
        """
        Restore player and equipment upon returning to the present day.
        Enforces explicit health preservation rules: player returns with
        saved health (minimum 50 HP baseline safety threshold).
        """
        # 1. Restore weapons and equipment to player
        if hasattr(player, "arsenal") and player.arsenal:
            player.arsenal.sync_unlocks(campaign)
            if hasattr(player.arsenal, "select_weapon"):
                player.arsenal.select_weapon(self.saved_active_weapon)
            player.weapon = player.arsenal.active_weapon

        # 2. Restore abilities
        if hasattr(player, "abilities") and player.abilities:
            player.abilities.sync_unlocks(campaign)

        # 3. Explicit health return rule
        player.health = max(self.saved_health, 50)
        player.is_dead = False
        setattr(player, "is_flashback", False)


class FlashbackController:
    """
    State machine and interaction manager for the August 1977 Big Ear flashback.
    Coordinates Dr. Jerry Ehman's printout review, red ballpoint pen annotation,
    hidden analog audio reel extraction, and reality anchor acquisition.
    """

    # Interaction zones (world X-coordinates)
    PRINTER_ZONE: Tuple[float, float] = (80.0, 160.0)
    VAULT_ZONE: Tuple[float, float] = (340.0, 420.0)
    EXIT_ZONE: Tuple[float, float] = (0.0, 56.0)

    # Authored fanfold printout telemetry
    SIGNAL_CHARS: List[str] = ["1", "1", "3", "1", "6", "E", "Q", "U", "J", "5", "1", "1", "2", "1"]
    WOW_INDICES: Tuple[int, int] = (4, 10)  # "6EQUJ5" slice

    def __init__(self, campaign: Optional[Any] = None, snapshot: Optional[FlashbackSnapshot] = None):
        self.stage: FlashbackStage = FlashbackStage.ENTERED
        self.snapshot: Optional[FlashbackSnapshot] = snapshot
        self.is_printout_open: bool = False
        self.dialogue_log: List[str] = []

        # Check if already completed in campaign state
        if campaign and hasattr(campaign, "state"):
            if campaign.state.room_flags.get("flashback_1977_completed", False):
                self.stage = FlashbackStage.COMPLETED

    def inspect_printout(self) -> Tuple[bool, str]:
        """Examine the continuous line-printer output from the IBM 1130."""
        if self.stage == FlashbackStage.ENTERED:
            self.stage = FlashbackStage.PRINTOUT_INSPECTED
            msg = "Dr. Ehman inspects the IBM 1130 continuous fanfold paper. Channel 2 displays a 30-sigma peak: 6EQUJ5."
            self.dialogue_log.append(msg)
            self.is_printout_open = True
            return True, msg
        elif self.stage in (FlashbackStage.PRINTOUT_INSPECTED, FlashbackStage.ANNOTATION_APPLIED, FlashbackStage.REEL_RETRIEVED, FlashbackStage.COMPLETED):
            self.is_printout_open = not self.is_printout_open
            msg = "Viewing IBM 1130 printer telemetry fanfold paper."
            return True, msg
        return False, "Printer is currently idle."

    def apply_red_annotation(self) -> Tuple[bool, str]:
        """Circle '6EQUJ5' in red ballpoint pen and annotate 'Wow!' in the margin."""
        if self.stage == FlashbackStage.PRINTOUT_INSPECTED:
            self.stage = FlashbackStage.ANNOTATION_APPLIED
            msg = "Dr. Ehman draws a red circle around '6EQUJ5' and writes 'Wow!' in the margin."
            self.dialogue_log.append(msg)
            self.is_printout_open = True
            return True, msg
        elif self.stage in (FlashbackStage.ANNOTATION_APPLIED, FlashbackStage.REEL_RETRIEVED, FlashbackStage.COMPLETED):
            return True, "'Wow!' annotation already permanently inscribed in red ink."
        return False, "Inspect the raw line printer output before annotating."

    def retrieve_hidden_reel(self) -> Tuple[bool, str]:
        """Retrieve the analog magnetic audio reel tape from the observatory vault cabinet."""
        if self.stage == FlashbackStage.ANNOTATION_APPLIED:
            self.stage = FlashbackStage.REEL_RETRIEVED
            msg = "Retrieved unquantized analog RF magnetic tape reel from TEAC audio vault cabinet."
            self.dialogue_log.append(msg)
            return True, msg
        elif self.stage in (FlashbackStage.REEL_RETRIEVED, FlashbackStage.COMPLETED):
            return True, "Analog tape reel already extracted and held in possession."
        return False, "Vault cabinet is locked. Complete line-printer observation review first."

    def lock_reality_anchor(self, campaign: Any) -> Tuple[bool, str]:
        """
        Resonate the magnetic tape reel against the observatory observation window,
        establishing the 1977 Reality Anchor and triggering safe return to 2029.
        """
        if self.stage == FlashbackStage.REEL_RETRIEVED:
            self.stage = FlashbackStage.COMPLETED
            # Grant campaign event if campaign is available
            if campaign:
                save_id = getattr(campaign.state, "save_id", "default")
                evt = {
                    "event_id": f"complete_flashback_1977_{save_id}",
                    "type": "complete_flashback_1977",
                }
                campaign.apply_event(evt)

            msg = "Reality Anchor 1977 established. Temporal feedback resonance collapsing."
            self.dialogue_log.append(msg)
            return True, msg
        elif self.stage == FlashbackStage.COMPLETED:
            return True, "Reality Anchor 1977 already locked and active."
        return False, "Cannot establish reality anchor: analog audio tape reel required."

    def get_prompt(self, player_x: float) -> str:
        """Compute contextual on-screen action prompt based on player location and stage."""
        if self.PRINTER_ZONE[0] <= player_x <= self.PRINTER_ZONE[1]:
            if self.stage == FlashbackStage.ENTERED:
                return "[E] INSPECT IBM 1130 COMPUTER PRINTOUT"
            elif self.stage == FlashbackStage.PRINTOUT_INSPECTED:
                return "[E] CIRCLE '6EQUJ5' WITH RED PEN & ANNOTATE 'WOW!'"
            else:
                return "[E] VIEW ANNOTATED 'WOW!' PRINTOUT"

        elif self.VAULT_ZONE[0] <= player_x <= self.VAULT_ZONE[1]:
            if self.stage in (FlashbackStage.ENTERED, FlashbackStage.PRINTOUT_INSPECTED):
                return "ANALOG TAPE VAULT // LOCKED (REVIEW SIGNAL FIRST)"
            elif self.stage == FlashbackStage.ANNOTATION_APPLIED:
                return "[E] RETRIEVE ANALOG MAGNETIC TAPE REEL"
            elif self.stage == FlashbackStage.REEL_RETRIEVED:
                return "[E] LOCK REALITY ANCHOR & RETURN TO 2029"
            else:
                return "ANALOG TAPE VAULT // REALITY ANCHOR ARCHIVED"

        elif self.EXIT_ZONE[0] <= player_x <= self.EXIT_ZONE[1]:
            if self.stage == FlashbackStage.COMPLETED:
                return "[E / ESC] RETURN TO 2029 WITH REALITY ANCHOR"
            else:
                return "[E / ESC] ABORT FLASHBACK & RETURN TO PRESENT"

        # General navigational cues
        if self.stage == FlashbackStage.ENTERED:
            return "INVESTIGATE IBM 1130 PRINTER TERMINAL AT DESK"
        elif self.stage == FlashbackStage.PRINTOUT_INSPECTED:
            return "EXAMINE TELEMETRY AND ANNOTATE 'WOW!' WITH RED PEN"
        elif self.stage == FlashbackStage.ANNOTATION_APPLIED:
            return "ACCESS TEAC AUDIO VAULT CABINET ON EAST WALL"
        elif self.stage == FlashbackStage.REEL_RETRIEVED:
            return "LOCK REALITY ANCHOR AT REEL CABINET"
        else:
            return "REALITY ANCHOR SECURED // EXIT VIA OBSERVATORY DOOR"

    def render_overlay(self, canvas: pygame.Surface, crt: Any, camera: Any) -> None:
        """Render 1977 warm amber CRT aesthetic and line printer fanfold overlay if active."""
        # 1. Warm amber phosphor ambient tint
        overlay = pygame.Surface((config.INTERNAL_WIDTH, config.INTERNAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((220, 150, 30, 24))  # 1977 warm amber tint
        canvas.blit(overlay, (0, 0))

        # 2. Fanfold line-printer modal inspection overlay
        if self.is_printout_open:
            box_x = 24
            box_y = 38
            box_w = config.INTERNAL_WIDTH - 48
            box_h = 144

            # Paper background (vintage paper off-white / pale buff)
            pygame.draw.rect(canvas, (244, 238, 218), (box_x, box_y, box_w, box_h))
            pygame.draw.rect(canvas, (180, 160, 120), (box_x, box_y, box_w, box_h), 2)

            # Tractor feed perforations along top and bottom edges
            for px in range(box_x + 8, box_x + box_w - 8, 12):
                pygame.draw.circle(canvas, (180, 160, 120), (px, box_y + 4), 2)
                pygame.draw.circle(canvas, (180, 160, 120), (px, box_y + box_h - 4), 2)

            # Header text
            header_str = "OSU RADIO OBSERVATORY // BIG EAR 1420.456 MHz // CH 02 // 1977-08-15"
            for index, line in enumerate(wrap_text_pixels(header_str, crt.font_sm, box_w - 24)):
                crt.draw_text(line, box_x + 12, box_y + 12 + index * 10, color=(50, 40, 20), size="sm", has_shadow=False)

            # Telemetry line printout
            line_str = "  ".join(self.SIGNAL_CHARS)
            crt.draw_text(f"RAW TELEMETRY:  {line_str}", box_x + 12, box_y + 40, color=(30, 30, 30), size="sm", has_shadow=False)
            crt.draw_text("INTENSITY BINS: 10-SECOND INTEGRATION // 72-SECOND BEAMPASS", box_x + 12, box_y + 56, color=(100, 90, 70), size="sm", has_shadow=False)

            # Red ballpoint pen annotation if applied
            if self.stage in (FlashbackStage.ANNOTATION_APPLIED, FlashbackStage.REEL_RETRIEVED, FlashbackStage.COMPLETED):
                # Use the same measured font as the printed line to enclose the signal.
                start, end = self.WOW_INDICES
                prefix = "RAW TELEMETRY:  " + "  ".join(self.SIGNAL_CHARS[:start]) + "  "
                signal = "  ".join(self.SIGNAL_CHARS[start:end])
                signal_x = box_x + 12 + crt.font_sm.size(prefix)[0]
                signal_w = crt.font_sm.size(signal)[0]
                circle_rect = pygame.Rect(signal_x - 3, box_y + 37, signal_w + 6, 16)
                pygame.draw.ellipse(canvas, (210, 30, 20), circle_rect, 2)
                # Handwritten "Wow!" margin note
                crt.draw_text("Wow!", box_x + box_w - 60, box_y + 32, color=(220, 25, 20), size="md", has_shadow=False)
                crt.draw_text("[RED BALLPOINT PEN ANNOTATION BY DR. J. EHMAN]", box_x + 12, box_y + 82, color=(180, 40, 30), size="sm", has_shadow=False)

            # Footer prompt
            crt.draw_text("[PRESS E OR ESC TO CLOSE TELEMETRY SHEET]", box_x + 12, box_y + box_h - 20, color=(80, 70, 50), size="sm", has_shadow=False)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize flashback state for save game persistence."""
        return {
            "stage": self.stage.value,
            "is_printout_open": self.is_printout_open,
            "dialogue_log": list(self.dialogue_log),
            "snapshot": {
                "origin_room": self.snapshot.origin_room,
                "origin_spawn": self.snapshot.origin_spawn,
                "saved_health": self.snapshot.saved_health,
                "saved_inventory": dict(self.snapshot.saved_inventory),
                "saved_unlocked_weapons": list(self.snapshot.saved_unlocked_weapons),
                "saved_active_weapon": self.snapshot.saved_active_weapon,
                "saved_unlocked_abilities": list(self.snapshot.saved_unlocked_abilities),
                "saved_timeline": self.snapshot.saved_timeline,
            } if self.snapshot else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], campaign: Optional[Any] = None) -> "FlashbackController":
        """Deserialize flashback state from saved dictionary."""
        controller = cls(campaign=campaign)
        controller.stage = FlashbackStage(data.get("stage", FlashbackStage.ENTERED.value))
        controller.is_printout_open = bool(data.get("is_printout_open", False))
        controller.dialogue_log = list(data.get("dialogue_log", []))

        snap_data = data.get("snapshot")
        if snap_data:
            controller.snapshot = FlashbackSnapshot(
                origin_room=str(snap_data.get("origin_room", "bunker_hub")),
                origin_spawn=str(snap_data.get("origin_spawn", "bunker_start")),
                saved_health=int(snap_data.get("saved_health", 100)),
                saved_inventory=dict(snap_data.get("saved_inventory", {})),
                saved_unlocked_weapons=list(snap_data.get("saved_unlocked_weapons", [])),
                saved_active_weapon=str(snap_data.get("saved_active_weapon", "maser_1420")),
                saved_unlocked_abilities=list(snap_data.get("saved_unlocked_abilities", [])),
                saved_timeline=str(snap_data.get("saved_timeline", "2029_CORE")),
            )
        return controller
