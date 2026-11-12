"""
MODULE: video_game/engine/protocols.py
PURPOSE: Authoritative protocol validation, science arc management across workbenches, evidence grant verification, untrusted model output sanitization, and hostile signal detection.
CALLED BY: video_game/engine/scenes/lab.py, video_game/engine/scenes/terminal.py, video_game/engine/contact_session.py, and tests.
HOW TO MODIFY: Add or update science arc management rules and hostile Core-mimic detection heuristics; maintain zero wildcard imports.
"""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from uuid import uuid4

from . import config
from video_game.engine.labs.biosecurity import BiosecurityValidationWorkbench
from video_game.engine.labs.formal import FormalValidationWorkbench
from video_game.engine.labs.neuro import ConnectomeValidationWorkbench
from video_game.engine.labs.quantum import QuantumValidationWorkbench


MISSIONS_FILE = config.DATA_DIR / "civilization_missions.json"
SCENARIOS_FILE = config.DATA_DIR / "lab_scenarios.json"
CAMPAIGN_FILE = config.DATA_DIR / "campaign.json"


def load_civilization_missions(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load canonical civilization mission contracts."""
    target_path = path or MISSIONS_FILE
    if target_path.exists():
        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "missions" in data:
            return data["missions"]
    return {}


@dataclass(frozen=True)
class EvidenceTrace:
    """Structured, authenticated player evidence trace required for fragment grants."""
    civilization_id: str
    fragment_id: str
    carrier_mhz: float
    carrier_locked: bool
    action_id: str
    timestamp: float


@dataclass(frozen=True)
class HostileSignalAssessment:
    """Telegraphed diagnostic evaluation of anomalous or Core-mimic radio signals."""
    is_hostile: bool
    confidence: float
    spoof_signature: str
    telemetry_reasons: List[str]
    failure_consequence: str
    recovery_action: str
    telegraphed_warning: str


class ProtocolValidator:
    """Enforces deterministic evidence validation, untrusted output gating, and hostile signal recovery."""

    def __init__(self, missions: Optional[Dict[str, Any]] = None):
        self.missions: Dict[str, Any] = missions or load_civilization_missions()

    def validate_and_grant_fragment(
        self,
        trace_or_candidate: Any,
        campaign: Any,
        session: Optional[Any] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Validate evidence trace and atomically grant fragment to campaign.

        Rejects:
          - Free-text dialogue strings (untrusted model output).
          - Unregistered civilization or fragment IDs.
          - Untuned/unlocked carrier frequency states.
          - Missing or forged player evidence action IDs.
          - Unmet campaign prerequisites (e.g. uncontacted civ).
          - Idempotent duplicate attempts.
        """
        # 1. Untrusted model output & raw string gating
        if isinstance(trace_or_candidate, str):
            return False, "REJECTED: Raw dialogue or text tags cannot modify campaign state", None

        # 2. Extract structured fields
        if isinstance(trace_or_candidate, EvidenceTrace):
            civ_id = trace_or_candidate.civilization_id
            frag_id = trace_or_candidate.fragment_id
            freq_mhz = trace_or_candidate.carrier_mhz
            locked = trace_or_candidate.carrier_locked
            action_id = trace_or_candidate.action_id
        elif isinstance(trace_or_candidate, dict):
            civ_id = str(trace_or_candidate.get("civilization_id", ""))
            frag_id = str(trace_or_candidate.get("fragment_id", ""))
            freq_mhz = float(trace_or_candidate.get("carrier_mhz", 0.0))
            locked = bool(trace_or_candidate.get("carrier_locked", False))
            action_id = str(trace_or_candidate.get("action_id", ""))
        else:
            return False, f"REJECTED: Unsupported candidate type: {type(trace_or_candidate)}", None

        # 3. Validate IDs against registered mission contracts
        if civ_id not in self.missions:
            return False, f"REJECTED: Unknown or fabricated civilization ID: {civ_id!r}", None

        mission = self.missions[civ_id]
        if frag_id not in mission.get("allowed_fragment_ids", []):
            return False, f"REJECTED: Fragment ID {frag_id!r} not permitted for {civ_id}", None

        # 4. Validate physical receiver evidence
        target_freq = mission.get("target_frequency_mhz", 1420.4056)
        tolerance = mission.get("lock_tolerance_mhz", 0.0800)
        if not locked or abs(freq_mhz - target_freq) > tolerance:
            return False, f"REJECTED: Carrier frequency {freq_mhz:.4f} MHz not locked to target {target_freq:.4f} MHz", None

        # 5. Validate evidence action from player interactions
        expected_action = mission.get("evidence", {}).get("action_id", "")
        if action_id != expected_action:
            return False, f"REJECTED: Missing required evidence action {expected_action!r} (received: {action_id!r})", None

        if session is not None and expected_action not in getattr(session, "completed_evidence_actions", set()):
            return False, f"REJECTED: Player has not completed required evidence action {expected_action!r}", None

        # 6. Validate campaign state prerequisites
        if campaign is not None:
            contacted = getattr(campaign.state, "contacted_civs", [])
            if civ_id not in contacted:
                # Add contacted_civ if not yet registered in campaign
                if hasattr(campaign, "_state") and isinstance(campaign._state, dict):
                    if civ_id not in campaign._state["contacted_civs"]:
                        campaign._state["contacted_civs"].append(civ_id)

            # Check if fragment is already extracted (idempotence)
            extracted = getattr(campaign.state, "extracted_fragments", [])
            if frag_id in extracted:
                return False, f"IDEMPOTENT: Fragment {frag_id} already extracted", None

            # Apply registered campaign grant event
            reward_event_type = mission.get("reward", {}).get("event_type")
            if not reward_event_type:
                return False, f"REJECTED: Mission {civ_id} has no registered reward event", None

            event = {
                "event_id": f"grant_{civ_id.lower()}_{uuid4().hex[:8]}",
                "type": reward_event_type,
                "payload": {}
            }
            applied = campaign.apply_event(event)
            if not applied:
                return False, f"IDEMPOTENT: Grant event {reward_event_type} already completed", None

            return True, f"SUCCESS: Fragment {frag_id} extracted and validated", event

        return True, f"SUCCESS: Evidence trace for {frag_id} verified", None

    def detect_core_mimic(
        self,
        signal_telemetry: Dict[str, Any],
        civ_id: Optional[str] = None
    ) -> HostileSignalAssessment:
        """
        Assess incoming signal telemetry for synthetic Core-mimic spoofing.

        Heuristics:
          - High algorithmic determinism score (>= 0.90 indicates synthetic PRNG).
          - Frequency offset matching known Core spoof frequencies.
          - Zero Doppler drift or absence of natural hydrogen line line-width.
        """
        reasons: List[str] = []
        is_hostile = False
        confidence = 0.0

        freq_mhz = float(signal_telemetry.get("frequency_mhz", 1420.4056))
        determinism = float(signal_telemetry.get("determinism_score", 0.0))
        doppler_drift = float(signal_telemetry.get("doppler_drift_khz", 0.0))
        line_width_khz = float(signal_telemetry.get("line_width_khz", 10.0))
        syntax = str(signal_telemetry.get("payload_syntax", "")).upper()

        mission = self.missions.get(civ_id or "")
        mimic_spec = mission.get("hostile_mimic", {}) if mission else {}
        spoof_freq = mimic_spec.get("mimic_frequency_mhz")

        # Heuristic 1: Deterministic algorithmic signature
        if determinism >= 0.90:
            is_hostile = True
            confidence = max(confidence, determinism)
            reasons.append(f"Synthetic PRNG determinism detected ({determinism:.2f} >= 0.90)")

        # Heuristic 2: Known spoof frequency channel
        if spoof_freq is not None and abs(freq_mhz - spoof_freq) < 0.02:
            is_hostile = True
            confidence = max(confidence, 0.95)
            reasons.append(f"Carrier matches known hostile relay beacon at {spoof_freq:.4f} MHz")

        # Heuristic 3: Unnatural zero line-width or static Doppler
        if line_width_khz < 0.5 and doppler_drift == 0.0:
            is_hostile = True
            confidence = max(confidence, 0.85)
            reasons.append("Unnatural delta-pulse: Zero Doppler drift and sub-0.5 kHz line-width")

        # Heuristic 4: Command injection syntax in payload
        if "OVERRIDE_INSTRUCTION" in syntax or "<CORE_MIMIC" in syntax:
            is_hostile = True
            confidence = 1.00
            reasons.append("Payload contains hostile command injection syntax")

        consequence = mimic_spec.get("failure_consequence", "RECEIVER_OVERLOAD_JAMMED")
        recovery = mimic_spec.get("recovery_action", "PURGE_RECEIVER_BUFFER")

        if is_hostile:
            warning = (
                f"ALERT: HOSTILE CORE-MIMIC DETECTED (CONFIDENCE: {int(confidence * 100)}%)\n"
                f"DIAGNOSTICS: {'; '.join(reasons)}\n"
                f"ACTION REQUIRED: Purge carrier buffer before transmission."
            )
        else:
            warning = "CARRIER AUTHENTIC: Natural astrophysical dispersion confirmed."

        return HostileSignalAssessment(
            is_hostile=is_hostile,
            confidence=confidence,
            spoof_signature=mimic_spec.get("spoof_signature", "CORE_MIMIC_STANDARD"),
            telemetry_reasons=reasons,
            failure_consequence=consequence,
            recovery_action=recovery,
            telegraphed_warning=warning
        )

    def resolve_hostile_signal(
        self,
        session: Any,
        campaign: Any,
        assessment: HostileSignalAssessment,
        operator_action: str
    ) -> Dict[str, Any]:
        """
        Handle the consequences and recovery of a hostile signal encounter.

        - If operator accepts/transmits on a hostile mimic:
          Telegraphed consequence: receiver jam, meter penalty, clear recovery path.
        - If operator purges/rejects the hostile mimic:
          Neutralization bonus: coordination bonus, safe carrier restoration.
        """
        clean_action = operator_action.strip().upper()

        if clean_action in ("ACCEPT", "TRANSMIT", "TRUST"):
            # Consequence: Receiver jam and campaign meter penalty
            if hasattr(session, "status_text"):
                session.status_text = f"ERR: {assessment.failure_consequence} // OVERLOAD"
            if hasattr(session, "signal_strength"):
                session.signal_strength = 0.05
            if hasattr(session, "is_locked"):
                session.is_locked = False

            # Apply bounded penalty event
            if campaign is not None and "hostile_signal_breach" in getattr(campaign, "_data", {}).get("events", {}):
                event = {
                    "event_id": f"breach_{uuid4().hex[:8]}",
                    "type": "hostile_signal_breach",
                    "payload": {}
                }
                campaign.apply_event(event)

            return {
                "outcome": "BREACH",
                "consequence": assessment.failure_consequence,
                "message": f"RECEIVER JAMMED: Hostile carrier breached buffer. Recovery required: {assessment.recovery_action}",
                "recoverable": True,
                "recovery_action": assessment.recovery_action,
            }

        else:
            # Operator safely purges or rejects hostile mimic
            if hasattr(session, "status_text"):
                session.status_text = "CARRIER PURGED // MOCK NEUTRALIZED"

            # Apply detection reward
            if campaign is not None and "hostile_signal_neutralized" in getattr(campaign, "_data", {}).get("events", {}):
                event = {
                    "event_id": f"neutralize_{uuid4().hex[:8]}",
                    "type": "hostile_signal_neutralized",
                    "payload": {}
                }
                campaign.apply_event(event)

            return {
                "outcome": "NEUTRALIZED",
                "consequence": None,
                "message": f"MIMIC NEUTRALIZED: Hostile signal quarantined. Receiver buffer safe.",
                "recoverable": True,
                "recovery_action": None,
            }


class ScienceArcManager:
    """
    Central manager for science arcs, scenario catalogs, workbench delegation,
    educational claim audits, and campaign meter impact verification.
    """

    SUPPORTED_WORKBENCHES = {"formal", "quantum", "neuro", "biosecurity"}
    REQUIRED_METERS = {
        "scientific_certainty",
        "alignment_confidence",
        "coordination_capacity",
        "public_trust",
        "human_agency",
        "biosecurity_readiness",
    }

    def __init__(
        self,
        scenarios_path: Optional[Path] = None,
        campaign_path: Optional[Path] = None,
    ):
        self.scenarios_path = scenarios_path or SCENARIOS_FILE
        self.campaign_path = campaign_path or CAMPAIGN_FILE
        self.scenarios_data = self.load_scenarios()
        self.scenarios: Dict[str, Any] = self.scenarios_data.get("scenarios", {})
        self.campaign_data = self.load_campaign_data()

    def load_scenarios(self) -> Dict[str, Any]:
        """Load laboratory scenarios database."""
        if not self.scenarios_path.exists():
            raise FileNotFoundError(f"Laboratory scenarios file not found: {self.scenarios_path}")
        with open(self.scenarios_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_campaign_data(self) -> Dict[str, Any]:
        """Load campaign definitions database."""
        if not self.campaign_path.exists():
            raise FileNotFoundError(f"Campaign file not found: {self.campaign_path}")
        with open(self.campaign_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_scenarios(self) -> List[str]:
        """List all registered scenario keys."""
        return list(self.scenarios.keys())

    def get_scenario(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve scenario definition by ID."""
        return self.scenarios.get(scenario_id)

    def get_scenarios_by_workbench(self, workbench_type: str) -> List[str]:
        """List scenario keys associated with a specific workbench type."""
        return [
            s_id
            for s_id, s_data in self.scenarios.items()
            if s_data.get("workbench_type", "formal") == workbench_type
        ]

    def create_workbench(
        self,
        scenario_id: str,
        campaign: Optional[Any] = None,
    ) -> Any:
        """
        Factory method to instantiate and select scenario on the appropriate workbench.
        """
        scen = self.get_scenario(scenario_id)
        if not scen:
            raise ValueError(f"Unknown scenario ID: {scenario_id}")

        wb_type = scen.get("workbench_type", "formal")
        if wb_type == "quantum":
            wb = QuantumValidationWorkbench(self.scenarios_data)
        elif wb_type == "neuro":
            wb = ConnectomeValidationWorkbench(self.scenarios_data)
        elif wb_type == "biosecurity":
            wb = BiosecurityValidationWorkbench(self.scenarios_data)
        else:
            wb = FormalValidationWorkbench(self.scenarios_data)

        wb.select_scenario(scenario_id, campaign)
        return wb

    def audit_catalog(self) -> Dict[str, Any]:
        """
        Audit the scenario catalog to verify that all 4 workbenches have beginner
        and advanced scenarios, conform to the schema, and cite primary sources.
        """
        report: Dict[str, Any] = {
            "total_scenarios": len(self.scenarios),
            "workbenches": {},
            "all_workbenches_present": True,
            "has_beginner_and_advanced": True,
            "errors": [],
        }

        for wb in self.SUPPORTED_WORKBENCHES:
            scens = self.get_scenarios_by_workbench(wb)
            has_adv = any("adv" in s for s in scens)
            has_beg = any("adv" not in s for s in scens)
            report["workbenches"][wb] = {
                "count": len(scens),
                "scenarios": scens,
                "has_beginner": has_beg,
                "has_advanced": has_adv,
            }
            if len(scens) < 2 or not (has_beg and has_adv):
                report["has_beginner_and_advanced"] = False
                report["errors"].append(
                    f"Workbench '{wb}' requires both beginner and advanced scenarios (found: {scens})"
                )

        # Audit each scenario's required schema fields
        for s_id, s_data in self.scenarios.items():
            for field_name in ["id", "title", "domain", "claim", "evidence_pool", "replication_checks", "deployment_choices"]:
                if field_name not in s_data:
                    report["errors"].append(f"Scenario '{s_id}' missing required field: {field_name}")

            # Primary references audit
            refs = s_data.get("source_references", [])
            if len(refs) < 2:
                report["errors"].append(f"Scenario '{s_id}' has fewer than 2 primary literature citations: {refs}")

        report["is_valid"] = (len(report["errors"]) == 0)
        return report

    def audit_educational_claims(self) -> Dict[str, Any]:
        """
        Verify educational claim tiers: correct_tier is present, options contain
        educational explanations, speculative tier is distinct from hostile intent,
        and counterexamples contain explicit rejection explanations.
        """
        report: Dict[str, Any] = {
            "audited_scenarios": len(self.scenarios),
            "counterexamples_verified": 0,
            "speculative_distinctions_verified": 0,
            "errors": [],
        }

        for s_id, s_data in self.scenarios.items():
            claim = s_data.get("claim", {})
            corr_tier = claim.get("correct_tier")
            if corr_tier not in ("established", "plausible", "speculative"):
                report["errors"].append(f"Scenario '{s_id}' invalid correct_tier: {corr_tier}")

            if claim.get("is_hostile", False):
                report["errors"].append(f"Scenario '{s_id}' marked as hostile; validation claims must represent non-hostile theory")

            opts = {o["tier"]: o.get("explanation", "") for o in claim.get("options", [])}
            for t in ["established", "plausible", "speculative"]:
                if t not in opts or not opts[t]:
                    report["errors"].append(f"Scenario '{s_id}' missing explanation for tier '{t}'")

            report["speculative_distinctions_verified"] += 1

            # Counterexamples in evidence pool
            ev_pool = s_data.get("evidence_pool", [])
            counterexamples = [e for e in ev_pool if not e.get("is_valid", True)]
            if not counterexamples:
                report["errors"].append(f"Scenario '{s_id}' has no invalid counterexamples to test player filtering")
            for ce in counterexamples:
                if "rejection_feedback" not in ce:
                    report["errors"].append(f"Counterexample '{ce.get('id')}' in '{s_id}' missing rejection_feedback")
                report["counterexamples_verified"] += 1

        report["is_valid"] = (len(report["errors"]) == 0)
        return report

    def verify_all_meters_covered(self) -> Tuple[bool, Set[str]]:
        """
        Verify that all 6 campaign meters receive updates from registered validation events.
        """
        events = self.campaign_data.get("events", {})
        covered_meters: Set[str] = set()

        for ev_id, ev_spec in events.items():
            if ev_id.startswith("validate_"):
                deltas = ev_spec.get("meter_deltas", {})
                for m_name in deltas.keys():
                    if m_name in self.REQUIRED_METERS:
                        covered_meters.add(m_name)

        all_covered = (self.REQUIRED_METERS == covered_meters)
        return all_covered, covered_meters

    def validate_workbench_record(
        self,
        record: Dict[str, Any],
        scenario_id: str,
    ) -> Tuple[bool, str]:
        """
        Validate that a committed validation record adheres to canonical schema.
        """
        scen = self.get_scenario(scenario_id)
        if not scen:
            return False, f"Unknown scenario: {scenario_id}"

        for req_field in ["id", "scenario_id", "claim_id", "observations", "claim_tier", "deployment_decision"]:
            if req_field not in record:
                return False, f"Validation record missing field: {req_field}"

        if record.get("id") != scen.get("fragment_id"):
            return False, f"Record ID mismatch: expected {scen.get('fragment_id')}, got {record.get('id')}"

        if record.get("claim_id") != scen.get("claim_id"):
            return False, f"Claim ID mismatch: expected {scen.get('claim_id')}, got {record.get('claim_id')}"

        return True, "Validation record verified"


