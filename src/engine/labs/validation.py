"""Shared scenario loading and claim/evidence/replication rules for science labs."""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
SCENARIOS_PATH = DATA_DIR / "lab_scenarios.json"

STEP_SELECT = "SELECT"
STEP_EXPERIMENT = "EXPERIMENT"
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


class ValidationWorkbench:
    """Shared validation steps; each lab owns its experiment and deployment rules."""

    EVIDENCE_SUCCESS = "EVIDENCE VALIDATED: Empirical observations verified. Proceed to replication checks."
    REPLICATION_SUCCESS = "REPLICATION SUCCESSFUL: Physical invariants verified. Select deployment choice."

    load_scenarios = staticmethod(load_lab_scenarios)

    def classify_claim(self, tier: str) -> Tuple[bool, str]:
        """Classify evidence strength, independently of hostile intent; allow retry."""
        if not self.active_scenario:
            return False, "ERR: No active scenario selected"

        claim_spec = self.active_scenario.get("claim", {})
        correct_tier = claim_spec.get("correct_tier")
        clean_tier = tier.strip().lower()

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

    def verify_evidence(self) -> Tuple[bool, str]:
        """Require all observations and reject counterexamples before replication."""
        if not self.active_scenario:
            return False, "ERR: No active scenario selected"

        required = set(self.active_scenario.get("required_observations", []))
        evidence_pool = {item["id"]: item for item in self.active_scenario.get("evidence_pool", [])}

        for eid in self.selected_evidence:
            item = evidence_pool.get(eid, {})
            if not item.get("is_valid", False):
                feedback = item.get("rejection_feedback", f"Invalid observation selected: {eid}")
                self.feedback_message = f"COUNTEREXAMPLE SELECTED: {feedback}"
                self.feedback_is_error = True
                return False, self.feedback_message

        missing = required - self.selected_evidence
        if missing:
            self.feedback_message = f"INCOMPLETE EVIDENCE: Missing required observations ({len(missing)} remaining)."
            self.feedback_is_error = True
            return False, self.feedback_message

        self.current_step = STEP_REPLICATION
        self.feedback_message = self.EVIDENCE_SUCCESS
        self.feedback_is_error = False
        return True, self.feedback_message

    def set_replication_check(self, check_id: str, answer: bool) -> None:
        """Set player verification answer for a replication invariant."""
        self.replication_answers[check_id] = answer

    def verify_replication(self) -> Tuple[bool, str]:
        """Require every invariant answer before advancing to deployment."""
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
        self.feedback_message = self.REPLICATION_SUCCESS
        self.feedback_is_error = False
        return True, self.feedback_message

    def is_completed(self, campaign: Any) -> bool:
        """Check if active scenario has already been validated in campaign."""
        return self.get_completed_record(campaign) is not None

    def get_completed_record(self, campaign: Any) -> Optional[Dict[str, Any]]:
        """Retrieve the completed validation record from campaign if present."""
        if not self.active_scenario or not campaign:
            return None
        records = getattr(campaign.state, "validation_records", [])
        for r in records:
            if r.get("scenario_id") == self.active_scenario.get("id"):
                return r
        return None
