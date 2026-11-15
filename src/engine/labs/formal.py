"""Formal claim, evidence and deployment workbench."""

from typing import Any, Dict, Optional, Set, Tuple
from uuid import uuid4

from .validation import (
    DATA_DIR, SCENARIOS_PATH, STEP_SELECT, STEP_EXPERIMENT, STEP_CLAIM,
    STEP_EVIDENCE, STEP_REPLICATION, STEP_DEPLOYMENT, STEP_COMPLETED,
    ValidationWorkbench, load_lab_scenarios,
)


class FormalValidationWorkbench(ValidationWorkbench):
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

    def toggle_evidence(self, evidence_id: str) -> bool:
        """Toggle an observation in the active evidence selection."""
        if evidence_id in self.selected_evidence:
            self.selected_evidence.remove(evidence_id)
            return False
        else:
            self.selected_evidence.add(evidence_id)
            return True

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
