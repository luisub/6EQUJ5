"""
MODULE: video_game/engine/labs/quantum.py
PURPOSE: Implement quantum optics workbench, double-slit interference model with environmental decoherence, parameter controls, and formal validation.
CALLED BY: video_game.engine.scenes.lab, video_game.tests.test_labs.
HOW TO MODIFY: Add or update quantum simulation equations and scenario schemas; maintain zero wildcard imports.
"""

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
SCENARIOS_PATH = DATA_DIR / "lab_scenarios.json"

# Workflow Steps
STEP_SELECT = "SELECT"
STEP_EXPERIMENT = "EXPERIMENT"
STEP_CLAIM = "CLAIM"
STEP_EVIDENCE = "EVIDENCE"
STEP_REPLICATION = "REPLICATION"
STEP_DEPLOYMENT = "DEPLOYMENT"
STEP_COMPLETED = "COMPLETED"

# Physical and Control Limits
WAVELENGTH_MIN_NM = 350.0
WAVELENGTH_MAX_NM = 850.0
WAVELENGTH_DEFAULT_NM = 532.0  # 532 nm Nd:YAG frequency-doubled green laser line

SLIT_WIDTH_MIN_UM = 5.0
SLIT_WIDTH_MAX_UM = 60.0
SLIT_WIDTH_DEFAULT_UM = 20.0

SLIT_DISTANCE_MIN_UM = 40.0
SLIT_DISTANCE_MAX_UM = 300.0
SLIT_DISTANCE_DEFAULT_UM = 100.0

SHIELDING_MIN = 0.0
SHIELDING_MAX = 1.0
SHIELDING_DEFAULT = 0.90

DETECTOR_DISTANCE_MIN_M = 0.2
DETECTOR_DISTANCE_MAX_M = 2.0
DETECTOR_DISTANCE_DEFAULT_M = 1.0

DETECTOR_SPAN_DEFAULT_MM = 20.0
NUM_DETECTOR_POINTS = 128

PRIMARY_SOURCES = [
    "Young_1804_Double_Slit_Interference",
    "Zurek_2003_Decoherence_Einselection",
    "Schlosshauer_2005_Decoherence_Measurement",
    "Caves_1982_Quantum_Limits_Amplifiers",
    "Joos_Zeh_1985_Emergence_Classical_Properties",
]


@dataclass
class SimulationResult:
    """Detailed telemetry and metrics output from the quantum optics simulation."""
    wavelength_nm: float
    slit_width_um: float
    slit_distance_um: float
    shielding_factor: float
    detector_distance_m: float
    visibility: float
    coherence_factor: float
    fringe_spacing_mm: float
    diffraction_width_mm: float
    snr_db: float
    state: str  # "COHERENT", "PARTIALLY_COHERENT", "COLLAPSED"
    meets_target: bool
    feedback: str
    intensities: List[float]
    positions_mm: List[float]


class QuantumInterferenceModel:
    """
    Physical simulation model for double-slit interference with environmental decoherence.

    Implements:
      1. Classical Fraunhofer wave interference envelope (Young 1804).
      2. Environment-induced decoherence damping factor (Zurek 2003, Joos & Zeh 1985).
      3. Standard Quantum Limit detector noise and visibility metrics (Caves 1982, Schlosshauer 2005).
    """

    def __init__(self, seed: int = 42):
        self.default_seed = seed

    @staticmethod
    def validate_controls(
        wavelength_nm: float,
        slit_width_um: float,
        slit_distance_um: float,
        shielding_factor: float,
        detector_distance_m: float,
    ) -> Tuple[bool, str]:
        """Validate that all physical control knobs reside within safe, bounded limits."""
        if not (WAVELENGTH_MIN_NM <= wavelength_nm <= WAVELENGTH_MAX_NM):
            return False, f"Wavelength {wavelength_nm:.1f} nm out of bounds [{WAVELENGTH_MIN_NM}, {WAVELENGTH_MAX_NM}]"
        if not (SLIT_WIDTH_MIN_UM <= slit_width_um <= SLIT_WIDTH_MAX_UM):
            return False, f"Slit width {slit_width_um:.1f} um out of bounds [{SLIT_WIDTH_MIN_UM}, {SLIT_WIDTH_MAX_UM}]"
        if not (SLIT_DISTANCE_MIN_UM <= slit_distance_um <= SLIT_DISTANCE_MAX_UM):
            return False, f"Slit distance {slit_distance_um:.1f} um out of bounds [{SLIT_DISTANCE_MIN_UM}, {SLIT_DISTANCE_MAX_UM}]"
        if slit_distance_um <= slit_width_um + 2.0:
            return False, f"Slit separation ({slit_distance_um:.1f} um) must exceed slit width ({slit_width_um:.1f} um) by at least 2 um"
        if not (SHIELDING_MIN <= shielding_factor <= SHIELDING_MAX):
            return False, f"Shielding factor {shielding_factor:.2f} out of bounds [{SHIELDING_MIN}, {SHIELDING_MAX}]"
        if not (DETECTOR_DISTANCE_MIN_M <= detector_distance_m <= DETECTOR_DISTANCE_MAX_M):
            return False, f"Detector distance {detector_distance_m:.2f} m out of bounds [{DETECTOR_DISTANCE_MIN_M}, {DETECTOR_DISTANCE_MAX_M}]"
        return True, "Controls valid"

    def compute_interference(
        self,
        wavelength_nm: float,
        slit_width_um: float,
        slit_distance_um: float,
        shielding_factor: float,
        detector_distance_m: float,
        span_mm: float = DETECTOR_SPAN_DEFAULT_MM,
        num_points: int = NUM_DETECTOR_POINTS,
        seed: Optional[int] = None,
    ) -> SimulationResult:
        """
        Numerically evaluate double-slit spatial intensity distribution under decoherence.

        Guarantees:
          - Pure mathematical stability (no NaN, no Inf, zero division safely guarded).
          - Bounded intensities in [0.0, 1.0].
          - Deterministic repeatability with explicit seed.
        """
        valid, err_msg = self.validate_controls(
            wavelength_nm, slit_width_um, slit_distance_um, shielding_factor, detector_distance_m
        )
        if not valid:
            raise ValueError(f"Quantum control validation error: {err_msg}")

        # Unit conversions to SI
        lam_m = wavelength_nm * 1e-9
        a_m = slit_width_um * 1e-6
        d_m = slit_distance_um * 1e-6
        dist_m = detector_distance_m
        half_span_m = (span_mm / 2.0) * 1e-3

        # Environmental decoherence factor gamma (Zurek/Joos-Zeh scattering model)
        # Off-diagonal density matrix attenuation scales with spatial separation / de Broglie wavelength
        c_dec = 0.010
        decoherence_exponent = c_dec * (1.0 - shielding_factor) * (d_m / lam_m)
        gamma = math.exp(-max(0.0, min(100.0, decoherence_exponent)))
        gamma = max(0.0, min(1.0, gamma))

        # Detector sampling array
        dx_m = (2.0 * half_span_m) / max(1, num_points - 1)
        positions_mm: List[float] = []
        raw_intensities: List[float] = []

        # Noise parameters (Caves 1982 quantum and thermal noise floor)
        noise_level = 0.03 * (1.0 - shielding_factor) + 0.002
        active_seed = self.default_seed if seed is None else seed

        for i in range(num_points):
            x_m = -half_span_m + i * dx_m
            positions_mm.append(round(x_m * 1e3, 3))

            # Single-slit diffraction parameter beta = pi * a * x / (lambda * D)
            beta = (math.pi * a_m * x_m) / (lam_m * dist_m)
            if abs(beta) < 1e-6:
                diffraction = 1.0 - (beta * beta) / 6.0
            else:
                sinc = math.sin(beta) / beta
                diffraction = sinc * sinc

            # Double-slit phase difference delta = 2 * pi * d * x / (lambda * D)
            delta = (2.0 * math.pi * d_m * x_m) / (lam_m * dist_m)

            # Decoherence-damped interference intensity: I(x) = diffraction * (1 + gamma * cos(delta)) / 2
            # When gamma = 1 (pure quantum superposition): clean high-contrast fringes
            # When gamma = 0 (complete decoherence into classical mixture): fringes vanish into flat envelope
            cos_term = math.cos(delta)
            intensity_ideal = diffraction * (1.0 + gamma * cos_term) / 2.0

            # Deterministic pseudo-noise for detector shot noise
            pseudo_rand = math.sin((i + 1) * 137.5 + active_seed * 41.7) * 43758.5453
            noise = (pseudo_rand - math.floor(pseudo_rand) - 0.5) * noise_level

            measured_i = max(0.0, min(1.0, intensity_ideal + noise))
            raw_intensities.append(round(measured_i, 5))

        # Visibility analysis near central peak: V = (I_max - I_min) / (I_max + I_min)
        # Central fringe is at x = 0. First minimum is at delta = pi -> x_min = lambda * D / (2 * d)
        fringe_spacing_m = (lam_m * dist_m) / d_m
        diffraction_width_m = (2.0 * lam_m * dist_m) / a_m

        fringe_spacing_mm = round(fringe_spacing_m * 1e3, 3)
        diffraction_width_mm = round(diffraction_width_m * 1e3, 3)

        # Find peak intensity near x=0 and adjacent trough
        center_idx = num_points // 2
        # Radius of search in points corresponding to one fringe period
        fringe_pts = max(2, int(fringe_spacing_m / dx_m))
        local_window = raw_intensities[max(0, center_idx - fringe_pts): min(num_points, center_idx + fringe_pts + 1)]

        i_max = max(local_window) if local_window else 1.0
        i_min = min(local_window) if local_window else 0.0

        denom = i_max + i_min + 1e-12
        visibility = round(max(0.0, min(1.0, (i_max - i_min) / denom)), 4)

        # State classification
        if visibility >= 0.70:
            state = "COHERENT"
        elif visibility >= 0.30:
            state = "PARTIALLY_COHERENT"
        else:
            state = "COLLAPSED"

        # Signal-to-Noise Ratio (SNR) in dB
        signal_power = sum(val * val for val in raw_intensities) / max(1, len(raw_intensities))
        noise_power = noise_level * noise_level + 1e-12
        snr_db = round(10.0 * math.log10(max(1e-6, signal_power / noise_power)), 2)

        return SimulationResult(
            wavelength_nm=wavelength_nm,
            slit_width_um=slit_width_um,
            slit_distance_um=slit_distance_um,
            shielding_factor=shielding_factor,
            detector_distance_m=detector_distance_m,
            visibility=visibility,
            coherence_factor=round(gamma, 4),
            fringe_spacing_mm=fringe_spacing_mm,
            diffraction_width_mm=diffraction_width_mm,
            snr_db=snr_db,
            state=state,
            meets_target=False,
            feedback="",
            intensities=raw_intensities,
            positions_mm=positions_mm,
        )


class QuantumValidationWorkbench:
    """
    Quantum optics scientific validation workbench.

    Executes the formal quantum validation pipeline:
      1. Scenario selection & fragment prerequisite check.
      2. Interactive quantum simulation:
         - Tune wavelength, slit width, slit separation, and shielding controls.
         - Numerically evaluate double-slit interference with environmental decoherence.
         - Successful experimental demonstration unlocks empirical observation evidence.
      3. Claim classification (established vs plausible vs speculative).
      4. Evidence verification (requires experimental observation, rejects counterexamples).
      5. Replication check (physical conservation invariants: complementarity, no-signaling, unitarity).
      6. Deployment decision (applies campaign grant event, returns canonical validation record).
    """

    def __init__(self, scenarios_data: Optional[Dict[str, Any]] = None):
        self.scenarios_data = scenarios_data or self.load_scenarios()
        self.scenarios: Dict[str, Any] = self.scenarios_data.get("scenarios", {})
        self.model = QuantumInterferenceModel()

        self.active_scenario_id: Optional[str] = None
        self.active_scenario: Optional[Dict[str, Any]] = None

        # Interactive simulation controls
        self.wavelength_nm: float = WAVELENGTH_DEFAULT_NM
        self.slit_width_um: float = SLIT_WIDTH_DEFAULT_UM
        self.slit_distance_um: float = SLIT_DISTANCE_DEFAULT_UM
        self.shielding_factor: float = SHIELDING_DEFAULT
        self.detector_distance_m: float = DETECTOR_DISTANCE_DEFAULT_M

        # Simulation output state
        self.last_result: Optional[SimulationResult] = None
        self.experiment_passed: bool = False
        self.unlocked_evidence: Set[str] = set()

        # Validation pipeline state
        self.current_step: str = STEP_SELECT
        self.selected_claim_tier: Optional[str] = None
        self.selected_evidence: Set[str] = set()
        self.replication_answers: Dict[str, bool] = {}
        self.selected_deployment: Optional[str] = None
        self.feedback_message: str = "SELECT A QUANTUM VALIDATION SCENARIO"
        self.feedback_is_error: bool = False

    @staticmethod
    def load_scenarios(path: Optional[Path] = None) -> Dict[str, Any]:
        """Load laboratory scenario catalog."""
        target_path = path or SCENARIOS_PATH
        if not target_path.exists():
            raise FileNotFoundError(f"Laboratory scenarios file not found: {target_path}")
        raw = json.loads(target_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or "scenarios" not in raw:
            raise ValueError("Invalid lab scenarios catalog structure")
        return raw

    def select_scenario(self, scenario_id: str, campaign: Optional[Any] = None) -> Tuple[bool, str]:
        """Select active quantum workbench scenario and verify fragment prerequisite."""
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

        # Reset pipeline state for fresh scenario
        self.current_step = STEP_EXPERIMENT
        self.experiment_passed = False
        self.unlocked_evidence.clear()
        self.selected_claim_tier = None
        self.selected_evidence.clear()
        self.replication_answers.clear()
        self.selected_deployment = None

        # Reset controls to defaults
        self.wavelength_nm = WAVELENGTH_DEFAULT_NM
        self.slit_width_um = SLIT_WIDTH_DEFAULT_UM
        self.slit_distance_um = SLIT_DISTANCE_DEFAULT_UM
        self.shielding_factor = SHIELDING_DEFAULT
        self.detector_distance_m = DETECTOR_DISTANCE_DEFAULT_M
        self.last_result = None

        self.feedback_message = f"SCENARIO LOADED: {scenario.get('title')}. Tune quantum controls & execute experiment."
        self.feedback_is_error = False
        return True, self.feedback_message

    def set_controls(
        self,
        wavelength_nm: Optional[float] = None,
        slit_width_um: Optional[float] = None,
        slit_distance_um: Optional[float] = None,
        shielding_factor: Optional[float] = None,
        detector_distance_m: Optional[float] = None,
    ) -> Tuple[bool, str]:
        """Update simulation controls with validation."""
        new_lam = self.wavelength_nm if wavelength_nm is None else wavelength_nm
        new_w = self.slit_width_um if slit_width_um is None else slit_width_um
        new_d = self.slit_distance_um if slit_distance_um is None else slit_distance_um
        new_s = self.shielding_factor if shielding_factor is None else shielding_factor
        new_dist = self.detector_distance_m if detector_distance_m is None else detector_distance_m

        valid, err = self.model.validate_controls(new_lam, new_w, new_d, new_s, new_dist)
        if not valid:
            self.feedback_message = f"CONTROL ERROR: {err}"
            self.feedback_is_error = True
            return False, self.feedback_message

        self.wavelength_nm = new_lam
        self.slit_width_um = new_w
        self.slit_distance_um = new_d
        self.shielding_factor = new_s
        self.detector_distance_m = new_dist
        self.feedback_message = "Controls updated successfully."
        self.feedback_is_error = False
        return True, self.feedback_message

    def run_experiment(self, seed: Optional[int] = None) -> Tuple[bool, str, SimulationResult]:
        """
        Execute the quantum interference simulation and check target criteria.

        If target criteria are met, unlocks empirical evidence (e.g. obs_quantum_coherence_fringe).
        """
        if not self.active_scenario:
            raise RuntimeError("Cannot run experiment without active scenario")

        result = self.model.compute_interference(
            self.wavelength_nm,
            self.slit_width_um,
            self.slit_distance_um,
            self.shielding_factor,
            self.detector_distance_m,
            seed=seed,
        )

        target = self.active_scenario.get("target_experiment", {})
        lam_min = target.get("wavelength_nm_min", 400.0)
        lam_max = target.get("wavelength_nm_max", 700.0)
        w_max = target.get("slit_width_um_max", 35.0)
        d_min = target.get("slit_distance_um_min", 60.0)
        d_max = target.get("slit_distance_um_max", 200.0)
        min_shield = target.get("min_shielding", 0.80)
        min_vis = target.get("min_visibility", 0.70)
        req_state = target.get("target_state", "COHERENT")

        # Check conditions
        failed_reasons: List[str] = []
        if not (lam_min <= self.wavelength_nm <= lam_max):
            failed_reasons.append(f"Wavelength {self.wavelength_nm:.0f}nm outside target [{lam_min:.0f}, {lam_max:.0f}]nm")
        if self.slit_width_um > w_max:
            failed_reasons.append(f"Slit width {self.slit_width_um:.0f}um too wide (diffraction collapsed; max {w_max:.0f}um)")
        if not (d_min <= self.slit_distance_um <= d_max):
            failed_reasons.append(f"Slit separation {self.slit_distance_um:.0f}um outside target [{d_min:.0f}, {d_max:.0f}]um")
        if self.shielding_factor < min_shield:
            failed_reasons.append(f"Shielding {self.shielding_factor:.2f} insufficient (< {min_shield:.2f}); decoherence destroys fringes")
        if result.visibility < min_vis:
            failed_reasons.append(f"Visibility {result.visibility:.3f} below required threshold {min_vis:.3f}")
        if result.state != req_state:
            failed_reasons.append(f"Interference state is {result.state}, required: {req_state}")

        if not failed_reasons:
            result.meets_target = True
            result.feedback = (
                f"EXPERIMENT SUCCESSFUL: High-contrast interference fringes observed "
                f"(V={result.visibility:.3f} >= {min_vis:.2f}, SNR={result.snr_db:.1f} dB). "
                f"Coherence preserved under cryogenic shielding (gamma={result.coherence_factor:.3f})."
            )
            self.last_result = result
            self.experiment_passed = True

            # Unlock observation evidence
            for item in self.active_scenario.get("evidence_pool", []):
                if item.get("requires_experiment", False):
                    self.unlocked_evidence.add(item["id"])

            self.feedback_message = f"EVIDENCE UNLOCKED: Coherence fringes verified. Proceed to claim classification."
            self.feedback_is_error = False
            return True, self.feedback_message, result
        else:
            result.meets_target = False
            primary_reason = failed_reasons[0]
            result.feedback = f"EXPERIMENT FAILED: {primary_reason}"
            self.last_result = result
            self.experiment_passed = False
            self.feedback_message = result.feedback
            self.feedback_is_error = True
            return False, self.feedback_message, result

    def advance_to_claim(self) -> Tuple[bool, str]:
        """Advance from experiment to claim classification step."""
        if not self.experiment_passed:
            self.feedback_message = "EXPERIMENT REQUIRED: Execute a successful quantum optics trial before classifying claims."
            self.feedback_is_error = True
            return False, self.feedback_message
        self.current_step = STEP_CLAIM
        self.feedback_message = "Classify proposition into established, plausible, or speculative tier."
        self.feedback_is_error = False
        return True, self.feedback_message

    def classify_claim(self, tier: str) -> Tuple[bool, str]:
        """Classify proposition into established, plausible, or speculative tier."""
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

    def toggle_evidence(self, evidence_id: str) -> bool:
        """
        Toggle an observation in active evidence selection.

        Rejects experimental evidence if the experiment has not been successfully completed.
        """
        if not self.active_scenario:
            return False

        # Look up evidence item
        pool = {item["id"]: item for item in self.active_scenario.get("evidence_pool", [])}
        item = pool.get(evidence_id)
        if not item:
            self.feedback_message = f"UNKNOWN EVIDENCE: {evidence_id}"
            self.feedback_is_error = True
            return False

        if item.get("requires_experiment", False) and evidence_id not in self.unlocked_evidence:
            self.feedback_message = f"EVIDENCE LOCKED: Observation '{evidence_id}' requires successful experimental verification."
            self.feedback_is_error = True
            return False

        if evidence_id in self.selected_evidence:
            self.selected_evidence.remove(evidence_id)
            self.feedback_message = f"Deselected {evidence_id}"
            self.feedback_is_error = False
            return False
        else:
            self.selected_evidence.add(evidence_id)
            self.feedback_message = f"Selected {evidence_id}"
            self.feedback_is_error = False
            return True

    def verify_evidence(self) -> Tuple[bool, str]:
        """Validate observation selection: must include required evidence and reject counterexamples."""
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
        self.feedback_message = "EVIDENCE VALIDATED: Quantum signatures verified. Proceed to replication checks."
        self.feedback_is_error = False
        return True, self.feedback_message

    def set_replication_check(self, check_id: str, answer: bool):
        """Set player verification answer for a physical quantum invariant check."""
        self.replication_answers[check_id] = answer

    def verify_replication(self) -> Tuple[bool, str]:
        """Validate all replication checks against quantum physical invariant expectations."""
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
        campaign: Optional[Any] = None,
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Commit deployment decision and apply reward through registered campaign event."""
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
            "id": self.active_scenario.get("fragment_id", "FASR-002"),
            "scenario_id": self.active_scenario.get("id"),
            "scenario_version": int(self.active_scenario.get("version", 1)),
            "claim_id": self.active_scenario.get("claim_id"),
            "observations": sorted(list(self.selected_evidence)),
            "result": "validated",
            "confidence": 90,
            "claim_tier": self.selected_claim_tier or "speculative",
            "source_references": self.active_scenario.get("source_references", PRIMARY_SOURCES),
            "deployment_decision": decision_id,
        }

        # Apply campaign event
        if campaign is not None:
            # Check idempotence: scenario already validated
            existing_records = getattr(campaign.state, "validation_records", [])
            if any(r.get("scenario_id") == record["scenario_id"] for r in existing_records):
                self.current_step = STEP_COMPLETED
                self.feedback_message = f"IDEMPOTENT: Scenario {self.active_scenario_id} already validated"
                self.feedback_is_error = False
                return False, self.feedback_message, record

            event = {
                "event_id": f"val_{decision_id}_{uuid4().hex[:8]}",
                "type": event_type,
                "payload": {},
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
        scen_id = self.active_scenario.get("id")
        records = getattr(campaign.state, "validation_records", [])
        return any(r.get("scenario_id") == scen_id for r in records)

    def get_completed_record(self, campaign: Any) -> Optional[Dict[str, Any]]:
        """Retrieve the completed validation record from campaign if present."""
        if not self.active_scenario or not campaign:
            return None
        frag_id = self.active_scenario.get("fragment_id")
        scen_id = self.active_scenario.get("id")
        records = getattr(campaign.state, "validation_records", [])
        for r in records:
            if r.get("scenario_id") == scen_id:
                return r
        return None

