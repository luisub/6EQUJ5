"""
MODULE: video_game/engine/temporal_relay.py
PURPOSE: Implement the Dodleston Relay cross-era message exchange, historical action causality, safe room geometry rebuilding, deadlock prevention, and recovery pathways.
CALLED BY: video_game.engine.scenes.field, video_game.tests.test_timelines.
HOW TO MODIFY: Add new cross-era transmission puzzles or temporal channels; maintain zero wildcard imports.
"""

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
import pygame

from .campaign import Campaign
from .mandela_world import DisplacementSolver, MandelaWorld
from .world import (
    COLLISION_COVER,
    COLLISION_EMPTY,
    COLLISION_HAZARD,
    COLLISION_ONE_WAY,
    COLLISION_SOLID,
    Room,
    RoomObject,
)

ERA_1985 = "1985_ANALOG"
ERA_2029 = "2029_PRESENT"
ERA_2031 = "2031_FUTURE"

ERA_COLORS = {
    ERA_1985: (245, 180, 50),   # Warm amber BBC Micro phosphor
    ERA_2029: (65, 195, 245),   # Cold cyan Ohio CRT
    ERA_2031: (185, 115, 250),  # Deep violet future tachyon beacon
}


@dataclass
class RelayMessage:
    """A cross-era transmission message in the Dodleston terminal."""
    id: str
    era: str
    sender: str
    timestamp_label: str
    text: str
    requires_flags: List[str] = field(default_factory=list)


@dataclass
class HistoricalAction:
    """An authored historical transmission choice with deterministic present-day consequences."""
    id: str
    label: str
    target_era: str
    description: str
    prerequisites: List[str] = field(default_factory=list)
    consequence_summary: str = ""
    campaign_event: Optional[str] = None
    room_object_mutations: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    tile_mutations: List[Tuple[int, int, int]] = field(default_factory=list)  # (col, row, new_code)
    is_correct: bool = True
    recovery_action_id: Optional[str] = None


# Curated catalog of Dodleston relay messages across 1985, 2029, and 2031
AUTHORED_MESSAGES: List[RelayMessage] = [
    RelayMessage(
        id="msg_1985_intro",
        era=ERA_1985,
        sender="THOMAS HARDEN (1985 BBC MICRO)",
        timestamp_label="04-FEB-1985 22:40 GMT",
        text="TO YE WHO WRITETH ON THIS GLOWING PANE: I BE THOMAS HARDEN OF DODLESTON. PETER SAYETH THIS BOX BELONGETH TO A FUTURE YEAR. THE LARDER PIPE RUSHETH WITH BITTER STEAM. SHALL WE SEAL IT OR OPEN YE CISTERN?",
        requires_flags=[],
    ),
    RelayMessage(
        id="msg_2031_warning_coolant",
        era=ERA_2031,
        sender="MONITOR-2109 / VLA NODE (2031)",
        timestamp_label="29-AUG-2031 01:14 UTC",
        text="CAUSAL TELEMETRY ALERT: 2029 vault floor submerged in halogen refrigerant. Invariant preservation requires sealing 1985 larder pump valve. Opening cistern induces pipe rupture in 2029.",
        requires_flags=[],
    ),
    RelayMessage(
        id="msg_2029_inquiry_power",
        era=ERA_2029,
        sender="MATEO / OHIO RECEIVER (2029)",
        timestamp_label="11-NOV-2029 18:02 EST",
        text="Thomas, Ken: We have reached the Dodleston vault foundation in 2029. The main bulkhead is unpowered. Check your auxiliary fusebox for jumper pins.",
        requires_flags=["dodleston_coolant_drained"],
    ),
    RelayMessage(
        id="msg_1985_reply_power",
        era=ERA_1985,
        sender="KEN WEBSTER (1985 BBC MICRO)",
        timestamp_label="05-FEB-1985 01:15 GMT",
        text="Mateo: Peter found the fusebox behind the skirting board. Three jumper pins labeled J1 (Inductive Coil), J2 (Bypass), J3 (Overload Shunt). Which one shall we bridge?",
        requires_flags=["dodleston_coolant_drained"],
    ),
    RelayMessage(
        id="msg_2031_power_direction",
        era=ERA_2031,
        sender="MONITOR-2109 / VLA NODE (2031)",
        timestamp_label="29-AUG-2031 01:28 UTC",
        text="CAUSAL TELEMETRY: J1 bridges the 440V step-up feed to the 2029 door servo. Caution: J3 will trigger cascade fuse blowout.",
        requires_flags=["dodleston_coolant_drained"],
    ),
    RelayMessage(
        id="msg_1985_cache_inquiry",
        era=ERA_1985,
        sender="PETER (1985 BBC MICRO)",
        timestamp_label="05-FEB-1985 02:40 GMT",
        text="We have recorded the 1420 MHz pulse onto a Memorex C-60 cassette. Where can we cache it so that it will survive 44 years until your arrival?",
        requires_flags=["dodleston_bulkhead_unlocked"],
    ),
    RelayMessage(
        id="msg_2031_cache_direction",
        era=ERA_2031,
        sender="MONITOR-2109 / VLA NODE (2031)",
        timestamp_label="29-AUG-2031 02:50 UTC",
        text="Place tape in parlor chimney hearth, behind loose brick #4. Dry soot environment ensures 99.4% magnetic tape survival into 2029.",
        requires_flags=["dodleston_bulkhead_unlocked"],
    ),
    RelayMessage(
        id="msg_2029_completion",
        era=ERA_2029,
        sender="MATEO / OHIO RECEIVER (2029)",
        timestamp_label="11-NOV-2029 18:30 EST",
        text="C-60 cassette retrieved intact from chimney brick. Raw 1985 Wow! carrier harmonics decoded. Causal circuit closed.",
        requires_flags=["dodleston_cassette_cached"],
    ),
]


# Curated catalog of Dodleston historical actions
AUTHORED_ACTIONS: Dict[str, HistoricalAction] = {
    # Puzzle 1: Coolant Trench
    "action_seal_valve_drain": HistoricalAction(
        id="action_seal_valve_drain",
        label="TRANSMIT 1985: SEAL LARDER PUMP VALVE",
        target_era=ERA_1985,
        description="Instruct Thomas in 1985 to close the brass larder pump valve to divert coolant away from the lower vault floor.",
        prerequisites=[],
        consequence_summary="2029: Coolant trench drains completely; dry catwalk grating revealed; lower junction accessible.",
        campaign_event="relay_action_drain_coolant",
        tile_mutations=[(col, 14, COLLISION_ONE_WAY) for col in range(10, 15)],
        room_object_mutations={
            "junction_coolant_drain": {
                "drained": True,
                "label": "PUMP DRAIN VALVE [SEALED 1985 - DRAINED]",
            }
        },
        is_correct=True,
    ),
    "action_open_cistern_flood": HistoricalAction(
        id="action_open_cistern_flood",
        label="TRANSMIT 1985: OPEN CISTERN FLOODGATE",
        target_era=ERA_1985,
        description="Instruct Thomas in 1985 to open the cistern floodgate to relieve line pressure.",
        consequence_summary="2029: Overpressure ruptures the secondary pipe! Trench coolant rises, triggering a warning siren.",
        campaign_event=None,
        tile_mutations=[(col, 14, COLLISION_HAZARD) for col in range(10, 15)],
        room_object_mutations={
            "junction_coolant_drain": {
                "ruptured": True,
                "label": "PUMP DRAIN VALVE [RUPTURED: OVERPRESSURE]",
            }
        },
        is_correct=False,
        recovery_action_id="action_seal_valve_drain",
    ),

    # Puzzle 2: Power Junction & Vault Bulkhead
    "action_install_jumper_j1": HistoricalAction(
        id="action_install_jumper_j1",
        label="TRANSMIT 1985: BRIDGE FUSEBOX JUMPER J1",
        target_era=ERA_1985,
        description="Instruct Ken in 1985 to bridge Jumper J1 (Inductive Coil) in the cottage junction box.",
        prerequisites=["dodleston_coolant_drained"],
        consequence_summary="2029: 440V auxiliary power restored to the relay vault. Bulkhead door unlocks and opens.",
        campaign_event="relay_action_power_bulkhead",
        tile_mutations=[(16, row, COLLISION_EMPTY) for row in range(12, 15)],
        room_object_mutations={
            "door_bulkhead_relay": {
                "open": True,
                "locked": False,
                "label": "RELAY VAULT BULKHEAD [UNLOCKED: 440V POWER ONLINE]",
            }
        },
        is_correct=True,
    ),
    "action_install_jumper_j3": HistoricalAction(
        id="action_install_jumper_j3",
        label="TRANSMIT 1985: BRIDGE OVERLOAD SHUNT J3",
        target_era=ERA_1985,
        description="Instruct Ken in 1985 to bridge Jumper J3 (Overload Shunt).",
        prerequisites=["dodleston_coolant_drained"],
        consequence_summary="2029: Relay fusebox suffers overload burnout; bulkhead remains dead and locked.",
        campaign_event=None,
        tile_mutations=[(16, row, COLLISION_SOLID) for row in range(12, 15)],
        room_object_mutations={
            "door_bulkhead_relay": {
                "open": False,
                "locked": True,
                "blown": True,
                "label": "RELAY VAULT BULKHEAD [LOCKED: FUSE BLOWN]",
            }
        },
        is_correct=False,
        recovery_action_id="action_install_jumper_j1",
    ),

    # Puzzle 3: Chimney Brick Cache
    "action_cache_tape_chimney": HistoricalAction(
        id="action_cache_tape_chimney",
        label="TRANSMIT 1985: CACHE CASSETTE BEHIND CHIMNEY BRICK #4",
        target_era=ERA_1985,
        description="Instruct Peter in 1985 to place the C-60 audio cassette behind loose chimney brick #4 in the parlor.",
        prerequisites=["dodleston_bulkhead_unlocked"],
        consequence_summary="2029: In the decayed chimney hearth, the tape cache is accessible and ready for collection.",
        campaign_event="relay_action_cache_cassette",
        room_object_mutations={
            "cache_relay_tape": {
                "spawned": True,
                "active": True,
                "label": "1985 DODLESTON AUDIO LOG TAPE [RECOVERABLE]",
            }
        },
        is_correct=True,
    ),
}


class TemporalRelay:
    """
    Coordinator managing the Dodleston cross-era terminal, causal edits,
    safe room geometry rebuilding, deadlock prevention, and recovery pathways.
    """

    def __init__(self, campaign: Optional[Campaign] = None):
        self.campaign: Optional[Campaign] = campaign
        self.active_actions: Set[str] = set()
        self.message_history: List[str] = ["msg_1985_intro", "msg_2031_warning_coolant"]
        self.puzzle_flags: Dict[str, bool] = {
            "dodleston_coolant_drained": False,
            "dodleston_bulkhead_unlocked": False,
            "dodleston_cassette_cached": False,
            "pipe_ruptured": False,
            "fuse_blown": False,
        }

        if self.campaign:
            self.sync_from_campaign(self.campaign)

    def get_visible_messages(self) -> List[RelayMessage]:
        """Return all messages whose prerequisites are satisfied."""
        result: List[RelayMessage] = []
        for msg in AUTHORED_MESSAGES:
            # Check if all required flags are set
            req_met = all(self.puzzle_flags.get(f, False) for f in msg.requires_flags)
            if req_met:
                result.append(msg)
        return result

    def get_available_actions(self) -> List[HistoricalAction]:
        """Return available historical actions given current causal state."""
        actions: List[HistoricalAction] = []

        # Puzzle 1 actions
        if not self.puzzle_flags["dodleston_coolant_drained"]:
            actions.append(AUTHORED_ACTIONS["action_seal_valve_drain"])
            if not self.puzzle_flags["pipe_ruptured"]:
                actions.append(AUTHORED_ACTIONS["action_open_cistern_flood"])

        # Puzzle 2 actions
        elif not self.puzzle_flags["dodleston_bulkhead_unlocked"]:
            actions.append(AUTHORED_ACTIONS["action_install_jumper_j1"])
            if not self.puzzle_flags["fuse_blown"]:
                actions.append(AUTHORED_ACTIONS["action_install_jumper_j3"])

        # Puzzle 3 action
        elif not self.puzzle_flags["dodleston_cassette_cached"]:
            actions.append(AUTHORED_ACTIONS["action_cache_tape_chimney"])

        return actions

    def apply_action(
        self,
        action_id: str,
        world: MandelaWorld,
        player: Any,
    ) -> Tuple[bool, str]:
        """
        Execute an authored historical action, rebuild affected room objects/tiles,
        ensure anti-trap safety for the player, and record campaign progression.
        """
        if action_id not in AUTHORED_ACTIONS:
            return False, f"Unknown action ID: '{action_id}'"

        action = AUTHORED_ACTIONS[action_id]
        if action_id in self.active_actions:
            return True, "Historical action already recorded."

        # Check prerequisites
        for req in action.prerequisites:
            if not self.puzzle_flags.get(req, False):
                return False, f"Causal prerequisite '{req}' not satisfied for {action.label}"

        prior_grid = deepcopy(world.room.collision_grid)
        prior_layers = deepcopy(world.room.timeline_collision_layers)
        prior_objects = deepcopy(world.room.objects)
        prior_world_state = deepcopy(world.state)
        # 1. Apply tile mutations to the room (both active and 2029 layer)
        for c, r, code in action.tile_mutations:
            if 0 <= r < len(world.room.collision_grid) and 0 <= c < len(world.room.collision_grid[r]):
                world.room.collision_grid[r][c] = code
            if "2029_CORE" in world.room.timeline_collision_layers:
                grid_2029 = world.room.timeline_collision_layers["2029_CORE"]
                if 0 <= r < len(grid_2029) and 0 <= c < len(grid_2029[r]):
                    grid_2029[r][c] = code

        # 2. Apply object mutations
        for obj_id, props in action.room_object_mutations.items():
            # Update room object
            for obj in world.room.objects:
                if obj.id == obj_id:
                    obj.properties.update(props)
                    if "open" in props:
                        world.state.set_door_state(obj_id, is_open=props["open"], is_locked=props.get("locked"))

        # 3. ANTI-TRAP SAFETY: Ensure player is not trapped or embedded in modified tiles/objects
        col = world.room.check_rect_collision(player.rect)
        if col["solid"] or col["hazard"]:
            safe_disp = DisplacementSolver.find_safe_displacement(
                world.room, world.active_timeline, player.rect, max_distance=32.0, prioritize_upward=True
            )
            if safe_disp is not None:
                player.x += safe_disp[0]
                player.y += safe_disp[1]
            else:
                world.room.timeline_collision_layers = prior_layers
                world.room.collision_grid = prior_grid
                world.room.objects = prior_objects
                world.state = prior_world_state
                return False, "CAUSAL EDIT BLOCKED: no safe space for the player."

        # 4. Update puzzle flags
        if action_id == "action_seal_valve_drain":
            self.puzzle_flags["dodleston_coolant_drained"] = True
            self.puzzle_flags["pipe_ruptured"] = False
        elif action_id == "action_open_cistern_flood":
            self.puzzle_flags["pipe_ruptured"] = True
        elif action_id == "action_install_jumper_j1":
            self.puzzle_flags["dodleston_bulkhead_unlocked"] = True
            self.puzzle_flags["fuse_blown"] = False
        elif action_id == "action_install_jumper_j3":
            self.puzzle_flags["fuse_blown"] = True
        elif action_id == "action_cache_tape_chimney":
            self.puzzle_flags["dodleston_cassette_cached"] = True

        self.active_actions.add(action_id)

        # 5. Apply campaign event if defined and campaign connected
        if self.campaign and action.campaign_event:
            self.campaign.apply_event({
                "event_id": f"{action.campaign_event}_{action_id}",
                "type": action.campaign_event,
            })

        # Sync back to campaign room flags
        if self.campaign:
            self.sync_to_campaign(self.campaign)

        return True, action.consequence_summary

    def recalibrate_puzzles(self, world: MandelaWorld, player: Any) -> Tuple[bool, str]:
        """
        Deadlock recovery: Safely reverses any erroneous choices (e.g. pipe rupture, fuse blowout)
        without trapping the player or resetting solved puzzles.
        """
        recovered_any = False

        if self.puzzle_flags.get("pipe_ruptured", False):
            # Reverse cistern flood back to dry drainage
            self.apply_action("action_seal_valve_drain", world, player)
            self.puzzle_flags["pipe_ruptured"] = False
            recovered_any = True

        if self.puzzle_flags.get("fuse_blown", False):
            # Reverse blowout and bridge J1
            self.apply_action("action_install_jumper_j1", world, player)
            self.puzzle_flags["fuse_blown"] = False
            recovered_any = True

        if recovered_any:
            return True, "Causal recalibration successful: erroneous historical edits reversed safely."
        return True, "Causal flux nominal: all active relay stages are stable."

    def to_dict(self) -> Dict[str, Any]:
        """Serialize relay state for save files."""
        return {
            "active_actions": sorted(list(self.active_actions)),
            "puzzle_flags": deepcopy(self.puzzle_flags),
        }

    def from_dict(self, data: Dict[str, Any]):
        """Deserialize relay state from saved data."""
        self.active_actions = set(data.get("active_actions", []))
        self.puzzle_flags = deepcopy(data.get("puzzle_flags", {}))

    def sync_to_campaign(self, campaign: Campaign):
        """Sync puzzle flags to campaign room flags."""
        snapshot = campaign.state.world_states.get("act_04_dodleston_relay", {})
        snapshot["relay"] = self.to_dict()
        campaign.store_world_state("act_04_dodleston_relay", snapshot)

    def sync_from_campaign(self, campaign: Campaign):
        """Restore puzzle flags from campaign room flags."""
        saved = campaign.state.world_states.get("act_04_dodleston_relay", {}).get("relay")
        if saved:
            self.from_dict(saved)
        rf = campaign.state.room_flags if hasattr(campaign, "state") else {}
        for flag in self.puzzle_flags:
            if flag in rf:
                self.puzzle_flags[flag] = bool(rf[flag])
