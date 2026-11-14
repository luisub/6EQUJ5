"""
MODULE: video_game/engine/objectives.py
PURPOSE: Track mission objectives, 72-second dish defense holdout, and alert notification banners.
CALLED BY: BunkerHubScene, FieldOpsScene, HUD, and GameStateMachine.
HOW TO MODIFY: Define new Act I objective steps or wave schedules; keep state reads detached.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

from .campaign_route import act_meta, unlocked_act
from .alien_journey import earth_portal_ready, ledger as journey_ledger, world_by_id

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

        # Alien information is earned only after each guardian and conversation.
        journey = journey_ledger(campaign)
        if journey or earth_portal_ready(campaign):
            stage = journey.get('stage', 'field')
            if stage == 'complete':
                return Objective('obj_campaign_complete', 'EARTH IS FREE',
                                 'The Core is defeated and the messages are safe.', 'RETURN TO BUNKER', is_completed=True)
            if stage == 'final':
                return Objective('obj_defeat_earth_ai', 'RETURN TO EARTH',
                                 'All eleven messages are secured. Confront the Core.', 'ENTER TO CONTINUE', station_id='field')
            world = world_by_id(journey.get('world_id')) if journey else None
            name = world['civ_id'] if world else 'FIRST SIGNAL'
            if stage == 'contact':
                return Objective('obj_alien_contact', 'MEET ' + name,
                                 'The guardian is defeated. Receive the message.', 'ENTER TO CONTINUE', station_id='field')
            return Objective('obj_alien_world', 'REACH ' + name,
                             'Cross the alien world and defeat its guardian.', 'CONTINUE RIGHT', station_id='field')

        # Later missions are derived only from earned, durable boss flags.
        act_id = unlocked_act(campaign)
        if act_id:
            act = act_meta(act_id)
            if act_id == 'act_05' and state.room_flags.get(act.get('complete_flag'), False):
                return Objective('obj_campaign_complete', 'CORE PRIME DEFEATED',
                                 'The signal route is secure.', 'RETURN TO BUNKER', is_completed=True)
            return Objective('obj_' + act_id, act.get('title', 'CONTINUE MISSION'),
                             'Follow the route and confront the sector boss.',
                             'CONTINUE RIGHT', station_id='field')

        # Receiver, science, collection and repair are optional side activities.
        if not state.room_flags.get("greenkeeper_defeated", False):
            return Objective(
                id="obj_defeat_greenkeeper",
                title="NEUTRALIZE GREENKEEPER",
                description="Follow the path right to confront the Greenkeeper.",
                hint="CONTINUE RIGHT",
                station_id="field",
                is_completed=False,
            )

        return Objective(
            id="obj_act_01_complete",
            title="OHIO FREE ROAM",
            description="Ohio complete. Continue from the bunker.",
            hint="ENTER / UP: CONTINUE MISSION",
            station_id=None,
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


class DishDefenseHoldout:
    """
    State machine and wave coordinator for the 72-second Big Ear dish defense holdout.
    Enforces exact 72.0s timing, 6 signal bins (6-E-Q-U-J-5), dish integrity, and atomic reward grant.
    """

    def __init__(self, total_duration: float = TOTAL_DEFENSE_DURATION, jam_drain_rate: float = 1.0):
        self.total_duration = float(total_duration)
        self.jam_drain_rate = float(jam_drain_rate)
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

        # Jamming decay, in integrity per second while the feedhorn is jammed.
        if self.is_jammed:
            self.dish_integrity = max(0.0, self.dish_integrity - self.jam_drain_rate * dt)

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
