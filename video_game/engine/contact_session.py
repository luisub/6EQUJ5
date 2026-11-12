"""
MODULE: video_game/engine/contact_session.py
PURPOSE: Maintain active receiver contact session state, 1400-1440 MHz frequency tuning,
         signal lock status, 6EQUJ5 codec decoding, conversation history, and authored
         offline contact routes across all eleven civilizations.
CALLED BY: CRTTerminalScene in video_game/engine/scenes/terminal.py.
HOW TO MODIFY:
  - To adjust tuning frequencies per target -> edit TARGET_FREQUENCIES.
  - To adjust lock sensitivity -> edit LOCK_TOLERANCE_MHZ.
  - To edit authored offline routes or evidence branches -> edit video_game/data/dialogue_offline.json.
"""

import json
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from signal_6EQUJ5 import codec
from . import config
from .ai_worker import AIWorker
from .protocols import ProtocolValidator, EvidenceTrace, HostileSignalAssessment


TARGET_FREQUENCIES: Dict[str, float] = {
    "FASR-001": 1420.4056,  # Neutral Hydrogen Line (Ohio Big Ear carrier)
    "FASR-002": 1420.8500,  # Sgr A* horizon Doppler offset
    "FASR-003": 1421.1200,  # Cygnus KIC megastructure harmonic
    "FASR-004": 1419.8800,  # Orion M42 nebula maser
    "FASR-005": 1420.2500,  # Proxima Centauri flare band
    "FASR-006": 1422.3300,  # Crab Nebula pulsar 33.5ms harmonic
    "FASR-007": 1418.9000,  # LGM-1 CP 1919 carrier
    "FASR-008": 1421.7000,  # TRAPPIST-1 7-world resonance
    "FASR-009": 1423.0500,  # 1I/2017 U1 hyperbolic trajectory
    "FASR-010": 1415.5000,  # Göbekli Tepe terrestrial ground harmonic
    "FASR-SCAN-H": 1420.0000, # Heptapod non-linear carrier
}

LOCK_TOLERANCE_MHZ = 0.0800  # Lock acquired when within +/- 80 kHz of target carrier


def load_offline_dialogue_catalog(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load canonical offline dialogue catalog from JSON data directory."""
    target_path = path or (config.DATA_DIR / "dialogue_offline.json")
    if target_path.exists():
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"schema_version": 1, "civilizations": {}}


class ContactSession:
    """Encapsulates tuning, carrier lock, 6EQUJ5 metrics, dialogue history, and offline routes."""

    def __init__(self,
                 worker: Optional[AIWorker] = None,
                 initial_civ: str = "FASR-001",
                 campaign: Optional[Any] = None,
                 force_offline: bool = False):
        self.worker = worker or AIWorker()
        self.campaign = campaign
        self.active_civ_id = initial_civ
        self.tuner_mhz: float = TARGET_FREQUENCIES.get(initial_civ, 1420.4056)
        self.target_mhz: float = TARGET_FREQUENCIES.get(initial_civ, 1420.4056)
        self.is_locked: bool = True
        self.signal_strength: float = 1.0  # 0.0 to 1.0

        self.max_exchanges: int = 12
        self.transcripts: Dict[str, List[Dict[str, Any]]] = {}
        self.exchange_counts: Dict[str, int] = {}
        self.completed_evidence_actions: Set[str] = set()
        self.validator = ProtocolValidator()

        # Offline catalogue and connection mode
        self.offline_data: Dict[str, Any] = load_offline_dialogue_catalog()
        has_live_model = False
        if self.worker and self.worker.adapter:
            try:
                has_live_model = self.worker.adapter.is_available()
            except Exception:
                has_live_model = False

        self.is_offline: bool = force_offline or (not has_live_model)

        self.current_incoming_tokens: List[str] = []
        self.is_streaming: bool = False
        self.active_request_id: Optional[str] = None
        self.active_session_id: Optional[str] = None

        self.acquisition_timer: float = 0.0
        mode_prefix = "OFFLINE" if self.is_offline else "ONLINE"
        self.status_text: str = f"CARRIER LOCKED [{mode_prefix}] // {self.tuner_mhz:.4f} MHz"

        # Codec-backed 6EQUJ5 intensity bins: [6, 14, 26, 30, 19, 5]
        decoded = codec.decode(codec.THE_SIGNAL)
        self.decode_bins: List[int] = [entry["intensity"] for entry in decoded]
        self.peak_intensity: int = max(self.decode_bins)  # 30 sigma ('U')
        self.duration_seconds: int = codec.OBSERVATION_WINDOW_SECONDS  # 72 seconds

        # Initialize session for first civilization
        self._init_civ_session(initial_civ)

    @property
    def exchange_count(self) -> int:
        return self.exchange_counts.get(self.active_civ_id, 0)

    def _record_civ_contact(self, civ_id: str):
        """Register active civilization as contacted in campaign."""
        if self.campaign is not None:
            if hasattr(self.campaign, "apply_event"):
                self.campaign.apply_event({"event_id": f"contact_{civ_id}", "type": "record_contact",
                                           "payload": {"civilization_id": civ_id}})
            elif hasattr(self.campaign, "contacted_civs") and isinstance(self.campaign.contacted_civs, list):
                if civ_id not in self.campaign.contacted_civs:
                    self.campaign.contacted_civs.append(civ_id)

    def _init_civ_session(self, civ_id: str):
        if civ_id not in self.transcripts:
            self.transcripts[civ_id] = []
            self.exchange_counts[civ_id] = 0

        civ_data = self.offline_data.get("civilizations", {}).get(civ_id, {})
        greeting = civ_data.get("initial_greeting")

        if self.is_offline:
            if greeting and not any(m.get("role") == "assistant" for m in self.transcripts[civ_id]):
                choices = civ_data.get("choices", [])
                choices_hint = "  ".join(f"[{c['id']}] {c['label']}" for c in choices)
                full_greeting = f"{greeting}\n\n[CHANNELS]: {choices_hint}" if choices_hint else greeting
                self.transcripts[civ_id].append({
                    "role": "assistant",
                    "text": full_greeting,
                    "timestamp": time.time(),
                })
            self.status_text = f"OFFLINE // EXCHANGES: {self.exchange_count}/{self.max_exchanges}"
        else:
            self.active_session_id = self.worker.start_contact(civ_id)

    def tune_frequency(self, delta_mhz: float):
        """Adjust receiver tuning frequency within 1400.0 to 1440.0 MHz."""
        new_freq = round(self.tuner_mhz + delta_mhz, 4)
        self.tuner_mhz = max(1400.0, min(1440.0, new_freq))

        freq_diff = abs(self.tuner_mhz - self.target_mhz)
        if freq_diff <= LOCK_TOLERANCE_MHZ:
            self.is_locked = True
            self.signal_strength = max(0.2, 1.0 - (freq_diff / LOCK_TOLERANCE_MHZ) * 0.8)
            mode_badge = "OFFLINE" if self.is_offline else "ONLINE"
            self.status_text = f"CARRIER LOCKED [{mode_badge}] // {self.tuner_mhz:.4f} MHz"
        else:
            self.is_locked = False
            self.signal_strength = max(0.02, 0.2 - min(0.18, freq_diff * 0.05))
            self.status_text = f"SEARCHING... // FREQ: {self.tuner_mhz:.4f} MHz"

    def snap_to_carrier(self):
        """Helper to lock receiver directly onto current target carrier."""
        self.tuner_mhz = self.target_mhz
        self.is_locked = True
        self.signal_strength = 1.0
        mode_badge = "OFFLINE" if self.is_offline else "ONLINE"
        self.status_text = f"CARRIER LOCKED [{mode_badge}] // {self.tuner_mhz:.4f} MHz"

    def switch_target(self, civ_id: str):
        """Switch active contact target, cancelling in-flight work and updating carrier."""
        if self.is_streaming:
            self.cancel_transmission()

        self.active_civ_id = civ_id
        self.target_mhz = TARGET_FREQUENCIES.get(civ_id, 1420.4056)
        self.snap_to_carrier()
        self._init_civ_session(civ_id)

    def reconnect(self) -> bool:
        """Attempt to restore live AI model connectivity and exit offline fallback."""
        try:
            if self.worker and self.worker.adapter and self.worker.adapter.is_available():
                self.is_offline = False
                self.status_text = f"RECONNECTED // LIVE MODEL ACTIVE ({self.tuner_mhz:.4f} MHz)"
                # Start live session for current civ if not already running
                self.active_session_id = self.worker.start_contact(self.active_civ_id)
                return True
        except Exception:
            pass

        self.is_offline = True
        self.status_text = f"RECONNECT FAILED // OFFLINE CANONICAL ACTIVE ({self.tuner_mhz:.4f} MHz)"
        return False

    def _check_prerequisite(self, prereq: str) -> bool:
        """Check if an evidence or campaign prerequisite is met."""
        if prereq in self.completed_evidence_actions:
            return True
        if self.campaign is not None:
            st = getattr(self.campaign, "state", self.campaign)
            if prereq in getattr(st, "applied_event_ids", []):
                return True
            if prereq in getattr(st, "extracted_fragments", []):
                return True
            if prereq in getattr(st, "contacted_civs", []):
                return True
            if prereq in getattr(st, "unlocked_weapons", []):
                return True
            if getattr(st, "room_flags", {}).get(prereq, False):
                return True
            if getattr(st, "inventory", {}).get(prereq, 0) > 0:
                return True
        return False

    def _process_offline_message(self, user_text: str) -> Tuple[str, Optional[str]]:
        """
        Resolve user transmission against canonical offline dialogue for active civ.
        Returns: (reply_text, action_id_if_granted)
        """
        civ_data = self.offline_data.get("civilizations", {}).get(self.active_civ_id, {})
        clean_lower = user_text.strip().lower()

        matched_branch = None

        # 1. Exact choice index match
        if clean_lower in ("1", "readiness", "status"):
            matched_branch = "readiness"
        elif clean_lower in ("2", "evidence", "fragment", "seed"):
            matched_branch = "evidence"
        elif clean_lower in ("3", "advanced", "tactics", "key", "action"):
            matched_branch = "advanced"
        else:
            # 2. Keyword scan
            keywords_map = civ_data.get("keywords", {})
            for branch_key, kws in keywords_map.items():
                if any(kw in clean_lower for kw in kws):
                    matched_branch = branch_key
                    break

        if not matched_branch or matched_branch not in civ_data:
            unknown_reply = civ_data.get("unknown_response",
                                         "Signal unparseable. Transmit [1] Readiness, [2] Evidence, or [3] Tactics.")
            return unknown_reply, None

        branch_info = civ_data[matched_branch]
        prereqs = branch_info.get("prerequisites", [])

        # Validate campaign / evidence prerequisites
        unmet = [p for p in prereqs if not self._check_prerequisite(p)]
        if unmet:
            unmet_reply = branch_info.get("unmet_reply", "Access restricted by current campaign parameters.")
            formatted_reply = f"[PREREQUISITE UNMET: Requires {', '.join(unmet)}] {unmet_reply}"
            return formatted_reply, None

        # Prerequisite met -> grant action and return reply
        reply_text = branch_info.get("reply", "")
        action_id = branch_info.get("action")
        if action_id:
            self.completed_evidence_actions.add(action_id)
            self._record_civ_contact(self.active_civ_id)
            if branch_info.get("fragment_id") and self.campaign is not None:
                self.claim_evidence_grant(self.active_civ_id)

        return reply_text, action_id

    def claim_evidence_grant(self, civ_id: Optional[str] = None) -> Tuple[bool, str]:
        """Validate authenticated player evidence and atomically grant fragment to campaign."""
        target_civ = civ_id or self.active_civ_id
        if self.campaign is None:
            return False, "ERR: No active campaign attached"

        mission = self.validator.missions.get(target_civ)
        if not mission:
            return False, f"ERR: Unknown mission for {target_civ}"

        expected_action = mission.get("evidence", {}).get("action_id", "")
        frag_id = mission.get("evidence", {}).get("fragment_id", target_civ)

        trace = EvidenceTrace(
            civilization_id=target_civ,
            fragment_id=frag_id,
            carrier_mhz=self.tuner_mhz,
            carrier_locked=self.is_locked,
            action_id=expected_action,
            timestamp=time.time(),
        )

        ok, msg, _event = self.validator.validate_and_grant_fragment(trace, self.campaign, session=self)
        if ok:
            self.status_text = f"EVIDENCE COMMITTED // {frag_id} EXTRACTED"
        return ok, msg

    def assess_signal_telemetry(self, signal_telemetry: Dict[str, Any]) -> HostileSignalAssessment:
        """Run Core-mimic detection heuristics against incoming signal telemetry."""
        return self.validator.detect_core_mimic(signal_telemetry, self.active_civ_id)

    def resolve_hostile_signal(self, assessment: HostileSignalAssessment, action: str) -> Dict[str, Any]:
        """Resolve a hostile signal breach or neutralization."""
        return self.validator.resolve_hostile_signal(self, self.campaign, assessment, action)

    def send_message(self, user_text: str) -> bool:
        """Submit user transmission to active target."""
        clean_text = user_text.strip()
        if not clean_text:
            return False
        if not self.is_locked:
            self.status_text = "ERR: NO CARRIER LOCK"
            return False
        if self.is_streaming:
            return False

        clean_lower = clean_text.lower()
        if clean_lower == "/restart":
            self.worker.cancel_current()
            self.exchange_counts[self.active_civ_id] = 0
            self.status_text = "SESSION RESTARTED // EVIDENCE RETAINED"
            return True
        if (self.exchange_count >= self.max_exchanges
                and clean_lower not in ("/choices", "choices", "?", "/offline", "offline", "/reconnect", "reconnect")):
            self.status_text = "LIMIT: 12 EXCHANGES COMPLETED // /RESTART"
            return False

        # Handle system commands
        if clean_lower in ("/reconnect", "reconnect"):
            self.transcripts[self.active_civ_id].append({
                "role": "user",
                "text": clean_text,
                "timestamp": time.time(),
            })
            ok = self.reconnect()
            sys_msg = "[SYSTEM]: Live model connection restored." if ok else "[SYSTEM]: Reconnect failed. Canonical offline archive active."
            self.transcripts[self.active_civ_id].append({
                "role": "assistant",
                "text": sys_msg,
                "timestamp": time.time(),
            })
            return True

        if clean_lower in ("/offline", "offline"):
            self.is_offline = True
            self.transcripts[self.active_civ_id].append({
                "role": "user",
                "text": clean_text,
                "timestamp": time.time(),
            })
            self.transcripts[self.active_civ_id].append({
                "role": "assistant",
                "text": "[SYSTEM]: Switched to canonical offline mode.",
                "timestamp": time.time(),
            })
            self.status_text = f"OFFLINE // EXCHANGES: {self.exchange_count}/{self.max_exchanges}"
            return True

        if clean_lower in ("/choices", "choices", "?"):
            self.transcripts[self.active_civ_id].append({
                "role": "user",
                "text": clean_text,
                "timestamp": time.time(),
            })
            civ_data = self.offline_data.get("civilizations", {}).get(self.active_civ_id, {})
            choices = civ_data.get("choices", [])
            lines = " | ".join(f"[{c['id']}] {c['label']}" for c in choices)
            self.transcripts[self.active_civ_id].append({
                "role": "assistant",
                "text": f"[CHANNELS]: {lines}",
                "timestamp": time.time(),
            })
            return True

        # Process standard transmission
        self._record_civ_contact(self.active_civ_id)
        if self.is_offline or clean_lower in ("1", "2", "3"):
            # Numbered mission channels use deterministic evidence rules in both modes;
            # free-form online messages still stream from the model.
            self.transcripts[self.active_civ_id].append({
                "role": "user",
                "text": clean_text,
                "timestamp": time.time(),
            })
            reply, _action = self._process_offline_message(clean_text)
            self.transcripts[self.active_civ_id].append({
                "role": "assistant",
                "text": reply,
                "timestamp": time.time(),
            })
            self.exchange_counts[self.active_civ_id] = self.exchange_count + 1
            mode = "OFFLINE" if self.is_offline else "CHANNEL"
            self.status_text = f"{mode} // EXCHANGES: {self.exchange_count}/{self.max_exchanges}"
            if self.exchange_count >= self.max_exchanges:
                self.status_text = "LIMIT: 12 EXCHANGES COMPLETED"
            return True

        # Live model transmission route
        self.transcripts[self.active_civ_id].append({
            "role": "user",
            "text": clean_text,
            "timestamp": time.time(),
        })

        req_id = self.worker.send_message(clean_text)
        if req_id is None:
            # Worker queue saturated or busy -> Fall back cleanly to offline without dropping turn
            self.is_offline = True
            reply, _ = self._process_offline_message(clean_text)
            self.transcripts[self.active_civ_id].append({
                "role": "assistant",
                "text": f"[OFFLINE FALLBACK]: {reply}",
                "timestamp": time.time(),
            })
            self.exchange_counts[self.active_civ_id] = self.exchange_count + 1
            self.status_text = f"OFFLINE FALLBACK // EXCHANGES: {self.exchange_count}/{self.max_exchanges}"
            return True

        self.active_request_id = req_id
        self.is_streaming = True
        self.current_incoming_tokens.clear()
        self.status_text = "TRANSMITTING..."
        return True

    def cancel_transmission(self) -> bool:
        """Cancel current in-flight stream."""
        if not self.is_streaming:
            return False
        self.worker.cancel_current()
        if self.current_incoming_tokens:
            partial = "".join(self.current_incoming_tokens) + " [INTERRUPTED]"
            self.transcripts[self.active_civ_id].append({
                "role": "assistant",
                "text": partial,
                "timestamp": time.time(),
            })
            self.current_incoming_tokens.clear()
        self.is_streaming = False
        self.status_text = "TRANSMISSION ABORTED"
        return True

    def update(self, dt_seconds: float):
        """Process worker events and advance signal acquisition timers."""
        self.acquisition_timer += dt_seconds

        for event in self.worker.poll_events():
            if event.session_id != self.active_session_id:
                continue

            if event.event_type == "STATUS":
                self.status_text = str(event.payload)

            elif event.event_type == "TOKEN":
                token = str(event.payload)
                if event.request_id == self.active_request_id:
                    self.current_incoming_tokens.append(token)
                    self.status_text = "RECEIVING..."

            elif event.event_type == "DONE":
                full_text = str(event.payload)
                if event.request_id == self.active_request_id:
                    self.transcripts[self.active_civ_id].append({
                        "role": "assistant",
                        "text": full_text,
                        "timestamp": time.time(),
                    })
                    self.exchange_counts[self.active_civ_id] = self.exchange_count + 1
                    self.current_incoming_tokens.clear()
                    self.is_streaming = False
                    self.active_request_id = None
                    self.status_text = f"STANDBY // EXCHANGES: {self.exchange_count}/{self.max_exchanges}"
                elif event.request_id == f"init_{self.active_session_id}":
                    if not any(msg.get("role") == "assistant" for msg in self.transcripts[self.active_civ_id]):
                        self.transcripts[self.active_civ_id].append({
                            "role": "assistant",
                            "text": full_text,
                            "timestamp": time.time(),
                        })
                    self.current_incoming_tokens.clear()

            elif event.event_type == "CANCELLED":
                if event.request_id == self.active_request_id or self.is_streaming:
                    self.is_streaming = False
                    self.active_request_id = None
                    self.current_incoming_tokens.clear()
                    self.status_text = "CARRIER RESET"

            elif event.event_type == "ERROR":
                if event.request_id == self.active_request_id or self.is_streaming:
                    # Connection failure mid-stream: preserve prior exchanges, switch to offline
                    self.is_offline = True
                    # Look up offline recovery reply for the pending transmission
                    last_user_msg = next((m["text"] for m in reversed(self.transcripts.get(self.active_civ_id, []))
                                          if m.get("role") == "user"), "")
                    recovery_reply, _ = self._process_offline_message(last_user_msg)
                    self.transcripts[self.active_civ_id].append({
                        "role": "assistant",
                        "text": f"[OFFLINE RECOVERY]: {recovery_reply}",
                        "timestamp": time.time(),
                    })
                    self.exchange_counts[self.active_civ_id] = self.exchange_count + 1
                    self.is_streaming = False
                    self.active_request_id = None
                    self.current_incoming_tokens.clear()
                    self.status_text = f"OFFLINE RECOVERY // EXCHANGES: {self.exchange_count}/{self.max_exchanges}"

    def get_transcript_lines(self) -> List[Tuple[str, Tuple[int, int, int]]]:
        """Return formatted transcript entries for display."""
        lines = []
        for msg in self.transcripts.get(self.active_civ_id, []):
            role = msg["role"]
            text = msg["text"]
            if role == "user":
                lines.append((f"> OPERATOR: {text}", config.COLOR_FIBO_GOLD))
            else:
                lines.append((f"[{self.active_civ_id}]: {text}", config.COLOR_CRT_GREEN))

        if self.is_streaming and self.current_incoming_tokens:
            partial = "".join(self.current_incoming_tokens)
            lines.append((f"[{self.active_civ_id}]: {partial}▌", config.COLOR_CRT_DIM))

        return lines
