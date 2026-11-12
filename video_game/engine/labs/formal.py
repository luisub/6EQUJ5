"""
MODULE: video_game/engine/labs/formal.py
PURPOSE: Implement formal validation workbench, claim/evidence classification, replication checking, and deployment decisions.
CALLED BY: video_game.engine.scenes.lab, video_game.tests.test_labs.
HOW TO MODIFY: Add or update science workbench logic and scenario validation schemas; maintain zero wildcard imports.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
SCENARIOS_PATH = DATA_DIR / "lab_scenarios.json"

STEP_SELECT = "SELECT"
STEP_CLAIM = "CLAIM"
STEP_EVIDENCE = "EVIDENCE"
STEP_REPLICATION = "REPLICATION"
STEP_DEPLOYMENT = "DEPLOYMENT"
STEP_COMPLETED = "COMPLETED"


def load_lab_scenarios(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load and validate the laboratory scenario database."""
    target_path = path or SCENARIOS_PATH
    if not target_path.exists():
        raise FileNotFoundError(f"Laboratory scenarios file not found: {target_path}")
    raw = json.loads(target_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or "scenarios" not in raw:
        raise ValueError("Invalid lab scenarios catalog structure")
    return raw


class FormalValidationWorkbench:
    """
    Formal scientific validation workbench.

    Executes the formal validation pipeline:
      1. Scenario selection & fragment prerequisite check.
      2. Claim classification (established vs plausible vs speculative) with explanatory feedback.
         Note: A speculative claim tier is strictly distinct from hostile deception intent.
      3. Observation & evidence verification (separates valid empirical signatures from counterexamples).
      4. Replication checks (finite physical invariants & conservation laws).
      5. Risk assessment and deployment decision (applies campaign grant event).
    """

    def __init__(self, scenarios_data: Optional[Dict[str, Any]] = None):
        data = scenarios_data or load_lab_scenarios()
        self.scenarios: Dict[str, Any] = data.get("scenarios", {})
        self.active_scenario_id: Optional[str] = None
        self.active_scenario: Optional[Dict[str, Any]] = None

        # Workflow state
        self.current_step: str = STEP_SELECT
        self.selected_claim_tier: Optional[str] = None
        self.selected_evidence: Set[str] = set()
        self.replication_answers: Dict[str, bool] = {}
        self.selected_deployment: Optional[str] = None
        self.feedback_message: str = "SELECT A VALIDATION SCENARIO"
        self.feedback_is_error: bool = False

    def select_scenario(self, scenario_id: str, campaign: Optional[Any] = None) -> Tuple[bool, str]:
        """Select active workbench scenario and verify fragment prerequisite."""
        if scenario_id not in self.scenarios:
            self.feedback_message = f"UNKNOWN SCENARIO: {scenario_id}"
            self.feedback_is_error = True
            return False, self.feedback_message

        scenario = self.scenarios[scenario_id]
        prereq = scenario.get("prerequisite_fragment")

        if campaign is not None and prereq:
            extracted = getattr(campaign.state, "extracted_fragments", [])
            if prereq not in extracted:
                self.feedback_message = f"PREREQUISITE MISSING: Requires extracted fragment '{prereq}'"
                self.feedback_is_error = True
                return False, self.feedback_message

        self.active_scenario_id = scenario_id
        self.active_scenario = scenario

        # Check if already completed in campaign
        if campaign is not None and self.is_completed(campaign):
            self.current_step = STEP_COMPLETED
            record = self.get_completed_record(campaign)
            decision = record.get("deployment_decision", "ARCHIVED") if record else "ARCHIVED"
            self.feedback_message = f"SCENARIO VALIDATED // DECISION COMMITTED: {decision}"
            self.feedback_is_error = False
            return True, self.feedback_message

        # Reset pipeline state for fresh or uncompleted scenario
        self.current_step = STEP_CLAIM
        self.selected_claim_tier = None
        self.selected_evidence.clear()
        self.replication_answers.clear()
        self.selected_deployment = None
        self.feedback_message = f"SCENARIO LOADED: {scenario.get('title')}. Classify claim tier."
        self.feedback_is_error = False
        return True, self.feedback_message

    def classify_claim(self, tier: str) -> Tuple[bool, str]:
        """
        Classify the claim into established, plausible, or speculative tier.

        Provides explanatory feedback on failure; allows retry.
        Demonstrates that a speculative claim is distinct from hostile intent.
        """
        if not self.active_scenario:
            return False, "ERR: No active scenario selected"

        claim_spec = self.active_scenario.get("claim", {})
        correct_tier = claim_spec.get("correct_tier")
        clean_tier = tier.strip().lower()

        # Find option explanation
        options = {opt["tier"]: opt["explanation"] for opt in claim_spec.get("options", [])}
        explanation = options.get(clean_tier, f"Unknown tier option: {tier}")

        if clean_tier == correct_tier:
            self.selected_claim_tier = clean_tier
            self.current_step = STEP_EVIDENCE
            self.feedback_message = f"VALIDATED: {explanation}"
            self.feedback_is_error = False
            return True, self.feedback_message
        else:
            self.feedback_message = f"CLASSIFICATION ERROR: {explanation}"
            self.feedback_is_error = True
            return False, self.feedback_message

    def toggle_evidence(self, evidence_id: str) -> bool:
        """Toggle an observation in the active evidence selection."""
        if evidence_id in self.selected_evidence:
            self.selected_evidence.remove(evidence_id)
            return False
        else:
            self.selected_evidence.add(evidence_id)
            return True

    def verify_evidence(self) -> Tuple[bool, str]:
        """
        Validate observation selection: must include required evidence and reject counterexamples.
        """
        if not self.active_scenario:
            return False, "ERR: No active scenario selected"

        required = set(self.active_scenario.get("required_observations", []))
        evidence_pool = {item["id"]: item for item in self.active_scenario.get("evidence_pool", [])}

        # Check for selected counterexamples (invalid items)
        for eid in self.selected_evidence:
            item = evidence_pool.get(eid, {})
            if not item.get("is_valid", False):
                feedback = item.get("rejection_feedback", f"Invalid observation selected: {eid}")
                self.feedback_message = f"COUNTEREXAMPLE SELECTED: {feedback}"
                self.feedback_is_error = True
                return False, self.feedback_message

        # Check for missing required observations
        missing = required - self.selected_evidence
        if missing:
            self.feedback_message = f"INCOMPLETE EVIDENCE: Missing required observations ({len(missing)} remaining)."
            self.feedback_is_error = True
            return False, self.feedback_message

        self.current_step = STEP_REPLICATION
        self.feedback_message = "EVIDENCE VALIDATED: Empirical observations verified. Proceed to replication checks."
        self.feedback_is_error = False
        return True, self.feedback_message

    def set_replication_check(self, check_id: str, answer: bool):
        """Set player verification answer for a replication invariant."""
        self.replication_answers[check_id] = answer

    def verify_replication(self) -> Tuple[bool, str]:
        """
        Validate all replication checks against physical invariant expectations.
        """
        if not self.active_scenario:
            return False, "ERR: No active scenario selected"

        checks = self.active_scenario.get("replication_checks", [])
        for chk in checks:
            cid = chk["id"]
            if cid not in self.replication_answers:
                self.feedback_message = f"REPLICATION INCOMPLETE: Check '{chk['prompt'][:30]}...' not evaluated."
                self.feedback_is_error = True
                return False, self.feedback_message

            ans = self.replication_answers[cid]
            if ans != chk["expected"]:
                self.feedback_message = f"REPLICATION FAILED: {chk['explanation']}"
                self.feedback_is_error = True
                return False, self.feedback_message

        self.current_step = STEP_DEPLOYMENT
        self.feedback_message = "REPLICATION SUCCESSFUL: Physical invariants verified. Select deployment choice."
        self.feedback_is_error = False
        return True, self.feedback_message

    def choose_deployment(
        self,
        decision_id: str,
        campaign: Optional[Any] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Commit deployment decision and apply reward through registered campaign event.

        Returns (success, message, validation_record).
        """
        if not self.active_scenario:
            return False, "ERR: No active scenario selected", None

        # Verify prerequisite fragment
        prereq = self.active_scenario.get("prerequisite_fragment")
        if campaign is not None and prereq:
            extracted = getattr(campaign.state, "extracted_fragments", [])
            if prereq not in extracted:
                self.feedback_message = f"PREREQUISITE MISSING: Fragment '{prereq}' not extracted"
                self.feedback_is_error = True
                return False, self.feedback_message, None

        # Find chosen deployment
        choices = {c["id"]: c for c in self.active_scenario.get("deployment_choices", [])}
        if decision_id not in choices:
            self.feedback_message = f"UNKNOWN DEPLOYMENT: {decision_id}"
            self.feedback_is_error = True
            return False, self.feedback_message, None

        chosen = choices[decision_id]
        event_type = chosen.get("event_type")

        # Construct versioned validation record
        record = {
            "id": self.active_scenario.get("fragment_id", "FASR-001"),
            "scenario_id": self.active_scenario.get("id"),
            "scenario_version": int(self.active_scenario.get("version", 1)),
            "claim_id": self.active_scenario.get("claim_id"),
            "observations": sorted(list(self.selected_evidence)),
            "result": "validated",
            "confidence": 85,
            "claim_tier": self.selected_claim_tier or "speculative",
            "source_references": self.active_scenario.get("source_references", []),
            "deployment_decision": decision_id
        }

        # Apply campaign event
        if campaign is not None:
            # Check idempotence: fragment already validated
            existing_records = getattr(campaign.state, "validation_records", [])
            if any(r.get("scenario_id") == record["scenario_id"] for r in existing_records):
                self.current_step = STEP_COMPLETED
                self.feedback_message = f"IDEMPOTENT: Scenario {self.active_scenario_id} already validated"
                self.feedback_is_error = False
                return False, self.feedback_message, record

            event = {
                "event_id": f"val_{decision_id}_{uuid4().hex[:8]}",
                "type": event_type,
                "payload": {}
            }
            applied = campaign.apply_event(event)
            if not applied:
                self.feedback_message = f"IDEMPOTENT: Validation event {event_type} already completed"
                self.feedback_is_error = False
                return False, self.feedback_message, record

        self.selected_deployment = decision_id
        self.current_step = STEP_COMPLETED
        self.feedback_message = f"VALIDATION COMPLETE // {chosen['label']}: {chosen['summary']}"
        self.feedback_is_error = False
        return True, self.feedback_message, record

    def is_completed(self, campaign: Any) -> bool:
        """Check if active scenario has already been validated in campaign."""
        if not self.active_scenario or not campaign:
            return False
        frag_id = self.active_scenario.get("fragment_id")
        records = getattr(campaign.state, "validation_records", [])
        return any(r.get("scenario_id") == self.active_scenario.get("id") for r in records)

    def get_completed_record(self, campaign: Any) -> Optional[Dict[str, Any]]:
        """Retrieve the completed validation record from campaign if present."""
        if not self.active_scenario or not campaign:
            return None
        frag_id = self.active_scenario.get("fragment_id")
        records = getattr(campaign.state, "validation_records", [])
        for r in records:
            if r.get("scenario_id") == self.active_scenario.get("id"):
                return r
        return None

