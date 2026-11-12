"""
MODULE: video_game/engine/objectives.py
PURPOSE: Track mission objectives, 72-second dish defense holdout, and alert notification banners.
CALLED BY: BunkerHubScene, FieldOpsScene, HUD, and GameStateMachine.
HOW TO MODIFY: Define new Act I objective steps or wave schedules; keep state reads detached.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

# Constants for 72-second holdout defense
HOLDOUT_IDLE = "IDLE"
HOLDOUT_ACTIVE = "ACTIVE"
HOLDOUT_FAILED = "FAILED"
HOLDOUT_COMPLETED = "COMPLETED"

TOTAL_DEFENSE_DURATION = 72.0
SIGNAL_BIN_DURATION = 12.0

# The six 12-second observation bins tracking the Wow! signal intensity envelope: 6 - E - Q - U - J - 5
SIGNAL_BINS = (
    {"bin": 0, "code": "6", "snr": 6, "intensity": 0.17, "label": "BIN 1/6 [6] 6σ (RISING)"},
    {"bin": 1, "code": "E", "snr": 14, "intensity": 0.39, "label": "BIN 2/6 [E] 14σ (RISING)"},
    {"bin": 2, "code": "Q", "snr": 26, "intensity": 0.72, "label": "BIN 3/6 [Q] 26σ (PEAK ACQUISITION)"},
    {"bin": 3, "code": "U", "snr": 30, "intensity": 1.00, "label": "BIN 4/6 [U] 30σ (MAXIMUM PEAK)"},
    {"bin": 4, "code": "J", "snr": 19, "intensity": 0.53, "label": "BIN 5/6 [J] 19σ (FALLING)"},
    {"bin": 5, "code": "5", "snr": 5, "intensity": 0.14, "label": "BIN 6/6 [5] 5σ (BASELINE RETURN)"},
)

# Scheduled enemy assault waves during the 72-second defense
DEFENSE_WAVES = (
    {"trigger_time": 0.0, "wave_id": "wave_01", "name": "SCOUT PROBE",
     "drone_count": 1, "hound_count": 1, "jam_feedhorn": False},
    {"trigger_time": 24.0, "wave_id": "wave_02", "name": "PEAK ATTACK",
     "drone_count": 2, "hound_count": 1, "jam_feedhorn": True},
    {"trigger_time": 48.0, "wave_id": "wave_03", "name": "FLANK SIEGE",
     "drone_count": 1, "hound_count": 2, "jam_feedhorn": True},
)


@dataclass(frozen=True)
class Objective:
    """An authoritative mission objective with player-facing guidance."""

    id: str
    title: str
    description: str
    hint: str
    station_id: Optional[str] = None
    is_completed: bool = False


@dataclass
class Notification:
    """A bounded transient on-screen notification alert."""

    title: str
    text: str
    kind: str
    duration: float
    timer: float


class ObjectiveTracker:
    """Tracks active campaign objectives and surfaces failure notifications."""

    def __init__(self):
        self.active_notification: Optional[Notification] = None
        self.last_objective_id: Optional[str] = None

    def get_active_objective(self, campaign) -> Objective:
        """Derive the current Act I primary objective from authoritative campaign state."""
        state = campaign.state

        # Stage 1: Initial receiver contact
        if "FASR-001" not in state.contacted_civs:
            return Objective(
                id="obj_tune_receiver",
                title="TUNE RECEIVER TERMINAL",
                description="Tune Big Ear receiver to 1420.4056 MHz and establish carrier lock.",
                hint="[E] CRT RECEIVER [CENTER]",
                station_id="terminal",
            )

        # Stage 2: Science Lab formal validation
        validated_ids = [r["id"] for r in state.validation_records]
        if "FASR-001" not in validated_ids:
            return Objective(
                id="obj_validate_signal",
                title="VALIDATE FASR-001 AT LAB",
                description="Classify entropy traces and prove information conservation on the lab workbench.",
                hint="[E] SCIENCE LAB [LEFT]",
                station_id="lab",
            )

        # Stage 3: Surface trench analog coupler search
        has_coupler = state.inventory.get("analog_coupler", 0) > 0
        coupler_collected = state.room_flags.get("trench_coupler_collected", False)
        feedhorn_repaired = state.room_flags.get("feedhorn_repaired", False)

        if not has_coupler and not coupler_collected and not feedhorn_repaired:
            return Objective(
                id="obj_recover_coupler",
                title="RECOVER ANALOG COUPLER",
                description="Explore the Ohio approach trench and recover the analog feedhorn coupler.",
                hint="[E] SURFACE AIRLOCK [RIGHT]",
                station_id="field",
            )

        # Stage 4: Bunker repair workbench
        if not feedhorn_repaired:
            return Objective(
                id="obj_repair_dish",
                title="REPAIR DISH FEEDHORN",
                description="Install the recovered analog coupler at the bunker repair workbench.",
                hint="[E] REPAIR BENCH [LEFT-CENTER]",
                station_id="repair",
            )

        # Stage 5: Perimeter 72-second defense
        if not state.room_flags.get("dish_defense_completed", False):
            return Objective(
                id="obj_defend_perimeter",
                title="DEFEND ANTENNA ARRAY",
                description="Defend the horn reflector array for 72 seconds against Core incursions.",
                hint="[E] SURFACE AIRLOCK [RIGHT]",
                station_id="field",
                is_completed=False,
            )

        # Stage 6: Defense completed -> Confront Greenkeeper in boss arena
        if not state.room_flags.get("greenkeeper_defeated", False):
            return Objective(
                id="obj_defeat_greenkeeper",
                title="NEUTRALIZE GREENKEEPER",
                description="Perimeter secured. Infiltrate the deep reflector basin and neutralize Core Warden Greenkeeper.",
                hint="[E] REFLECTOR BASIN BOSS ARENA",
                station_id="field",
                is_completed=False,
            )

        # Stage 7: Greenkeeper defeated -> Act I Complete, Act II unlocked
        return Objective(
            id="obj_act_01_complete",
            title="ACT I COMPLETE // ACT II UNLOCKED",
            description="Core Warden neutralized. Proceed through transit corridor to initiate Act II Neo-Denver relay.",
            hint="[E] ACT II TRANSIT READY",
            station_id="field",
            is_completed=True,
        )

    def post_notification(self, title: str, text: str, kind: str = "info", duration: float = 3.0):
        """Queue or replace the active on-screen notification banner."""
        self.active_notification = Notification(
            title=title,
            text=text,
            kind=kind,
            duration=duration,
            timer=duration,
        )

    def update(self, dt: float, campaign=None):
        """Advance notification timers and detect objective transitions."""
        if self.active_notification is not None:
            self.active_notification.timer -= dt
            if self.active_notification.timer <= 0.0:
                self.active_notification = None

        if campaign is not None:
            current = self.get_active_objective(campaign)
            if self.last_objective_id is None:
                self.last_objective_id = current.id
            elif self.last_objective_id != current.id:
                self.last_objective_id = current.id
                self.post_notification(
                    title="OBJECTIVE UPDATED",
                    text=f"{current.title}: {current.hint}",
                    kind="success",
                    duration=3.5,
                )


class DishDefenseHoldout:
    """
    State machine and wave coordinator for the 72-second Big Ear dish defense holdout.
    Enforces exact 72.0s timing, 6 signal bins (6-E-Q-U-J-5), dish integrity, and atomic reward grant.
    """

    def __init__(self, total_duration: float = TOTAL_DEFENSE_DURATION):
        self.total_duration = float(total_duration)
        self.bin_duration = SIGNAL_BIN_DURATION
        self.state = HOLDOUT_IDLE
        self.elapsed_time = 0.0
        self.dish_integrity = 100.0
        self.max_integrity = 100.0
        self.is_jammed = False
        self.current_bin_index = 0
        self.spawned_waves: Set[str] = set()
        self.failure_reason = ""

    @property
    def is_active(self) -> bool:
        return self.state == HOLDOUT_ACTIVE

    @property
    def is_completed(self) -> bool:
        return self.state == HOLDOUT_COMPLETED

    @property
    def is_failed(self) -> bool:
        return self.state == HOLDOUT_FAILED

    @property
    def active_bin(self) -> Dict[str, Any]:
        return SIGNAL_BINS[min(5, max(0, self.current_bin_index))]

    def start(self):
        """Begin the 72-second defense sequence."""
        self.state = HOLDOUT_ACTIVE
        self.elapsed_time = 0.0
        self.dish_integrity = self.max_integrity
        self.is_jammed = False
        self.current_bin_index = 0
        self.spawned_waves.clear()
        self.failure_reason = ""

    def update(self, dt: float, is_paused: bool = False) -> List[Dict[str, Any]]:
        """
        Advance active defense time, evaluate signal bin transitions,
        trigger scheduled enemy waves, and resolve completion or integrity failure.
        Returns a list of event dictionaries emitted during this update tick.
        """
        if is_paused or self.state != HOLDOUT_ACTIVE:
            return []

        events: List[Dict[str, Any]] = []
        self.elapsed_time += dt

        # Update signal bin
        new_bin = min(5, int(self.elapsed_time / self.bin_duration))
        if new_bin != self.current_bin_index:
            self.current_bin_index = new_bin
            events.append({
                "type": "BIN_TRANSITION",
                "bin": SIGNAL_BINS[new_bin],
            })

        # Check wave triggers
        for wave in DEFENSE_WAVES:
            w_id = wave["wave_id"]
            if self.elapsed_time >= wave["trigger_time"] and w_id not in self.spawned_waves:
                self.spawned_waves.add(w_id)
                if wave["jam_feedhorn"]:
                    self.is_jammed = True
                events.append({
                    "type": "SPAWN_WAVE",
                    "wave": wave,
                })

        # Jamming decay (1.0 HP/sec while feedhorn is jammed)
        if self.is_jammed:
            self.dish_integrity = max(0.0, self.dish_integrity - 1.0 * dt)

        # Integrity failure check
        if self.dish_integrity <= 0.0:
            self.state = HOLDOUT_FAILED
            self.failure_reason = "DISH INTEGRITY COLLAPSED"
            events.append({
                "type": "FAILED",
                "reason": self.failure_reason,
            })
            return events

        # Exact 72.0s completion check within one simulation step
        if self.elapsed_time >= self.total_duration:
            self.elapsed_time = self.total_duration
            self.state = HOLDOUT_COMPLETED
            events.append({
                "type": "COMPLETED",
                "elapsed_time": self.elapsed_time,
            })

        return events

    def damage_dish(self, amount: float):
        """Apply damage directly to dish integrity from hostile attacks."""
        if self.state != HOLDOUT_ACTIVE:
            return
        self.dish_integrity = max(0.0, self.dish_integrity - amount)
        if self.dish_integrity <= 0.0:
            self.state = HOLDOUT_FAILED
            self.failure_reason = "DISH DESTROYED BY HOSTILES"

    def unjam(self):
        """Clear feedhorn jamming to arrest automated integrity decay."""
        self.is_jammed = False

    def fail(self, reason: str = "PLAYER CASUALTY"):
        """Trigger holdout failure upon player death or critical breach."""
        self.state = HOLDOUT_FAILED
        self.failure_reason = reason

    def reset(self):
        """Restore holdout state to neutral idle for retry or checkpoint respawn."""
        self.state = HOLDOUT_IDLE
        self.elapsed_time = 0.0
        self.dish_integrity = self.max_integrity
        self.is_jammed = False
        self.current_bin_index = 0
        self.spawned_waves.clear()
        self.failure_reason = ""

    def get_signal_display(self) -> Dict[str, Any]:
        """Provide structured telemetry for HUD and terminal signal displays."""
        b_data = self.active_bin
        remaining = max(0.0, self.total_duration - self.elapsed_time)
        return {
            "bin": self.current_bin_index,
            "code": b_data["code"],
            "snr": b_data["snr"],
            "intensity": b_data["intensity"],
            "label": b_data["label"],
            "remaining": remaining,
            "dish_integrity": self.dish_integrity,
            "is_jammed": self.is_jammed,
            "state": self.state,
        }

    def apply_completion_reward(self, campaign) -> bool:
        """Apply one-shot completion grant event to authoritative campaign state."""
        if not self.is_completed:
            return False
        evt = {
            "event_id": f"dish_defense_{campaign.state.save_id}",
            "type": "complete_dish_defense",
        }
        return campaign.apply_event(evt)
