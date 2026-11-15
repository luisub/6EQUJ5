"""Biosecurity workbench, pathogen simulation and sequential trial controls."""

from dataclasses import dataclass, field
import math
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from .validation import (
    DATA_DIR, SCENARIOS_PATH, STEP_SELECT, STEP_EXPERIMENT, STEP_CLAIM,
    STEP_EVIDENCE, STEP_REPLICATION, STEP_DEPLOYMENT, STEP_COMPLETED,
    ValidationWorkbench,
)


# Physical and Control Limits
TEMP_MIN_C = 20.0
TEMP_MAX_C = 45.0
TEMP_OPTIMAL_C = 37.0
TEMP_DEFAULT_C = 37.0

RPM_MIN = 1000.0
RPM_MAX = 15000.0
RPM_OPTIMAL_MIN = 8000.0
RPM_OPTIMAL_MAX = 12000.0
RPM_DEFAULT = 8000.0

REAGENT_MIN_UL = 5.0
REAGENT_MAX_UL = 50.0
REAGENT_DEFAULT_UL = 20.0

FLOW_MIN = 0.1
FLOW_MAX = 2.0
FLOW_DEFAULT = 1.0

DEFAULT_TOTAL_REAGENTS = 100.0
MAX_CYCLES = 8
CONFIDENCE_TARGET = 0.85
PREMATURE_CYCLE_THRESHOLD = 3
PREMATURE_CONFIDENCE_THRESHOLD = 0.75
CONTAINMENT_CRITICAL_FLOOR = 0.40

PRIMARY_SOURCES = [
    "Wald_1947_Sequential_Analysis_SPRT",
    "Graham_Sullivan_2018_Prototype_Pathogen_Approach",
    "WHO_2020_Laboratory_Biosafety_Manual_4th_Ed",
    "Lipsitch_2016_Transmission_Dynamics_R0",
    "Fletcher_2014_Clinical_Epidemiology_Diagnostic_Certainty",
]


@dataclass
class AllocationControls:
    """Operator microfluidic and environmental incubation allocations."""
    incubation_temp_c: float = TEMP_DEFAULT_C
    centrifuge_rpm: float = RPM_DEFAULT
    reagent_volume_ul: float = REAGENT_DEFAULT_UL
    filtration_flow_rate: float = FLOW_DEFAULT

    def validate(self) -> None:
        """Validate parameter ranges and physical sanity."""
        if math.isnan(self.incubation_temp_c) or math.isinf(self.incubation_temp_c):
            raise ValueError(f"Invalid incubation temperature: {self.incubation_temp_c}")
        if not (TEMP_MIN_C <= self.incubation_temp_c <= TEMP_MAX_C):
            raise ValueError(
                f"Incubation temperature {self.incubation_temp_c} C out of bounds [{TEMP_MIN_C}, {TEMP_MAX_C}]"
            )
        if math.isnan(self.centrifuge_rpm) or math.isinf(self.centrifuge_rpm):
            raise ValueError(f"Invalid centrifuge RPM: {self.centrifuge_rpm}")
        if not (RPM_MIN <= self.centrifuge_rpm <= RPM_MAX):
            raise ValueError(
                f"Centrifuge RPM {self.centrifuge_rpm} out of bounds [{RPM_MIN}, {RPM_MAX}]"
            )
        if math.isnan(self.reagent_volume_ul) or math.isinf(self.reagent_volume_ul):
            raise ValueError(f"Invalid reagent volume: {self.reagent_volume_ul}")
        if not (REAGENT_MIN_UL <= self.reagent_volume_ul <= REAGENT_MAX_UL):
            raise ValueError(
                f"Reagent volume {self.reagent_volume_ul} uL out of bounds [{REAGENT_MIN_UL}, {REAGENT_MAX_UL}]"
            )
        if math.isnan(self.filtration_flow_rate) or math.isinf(self.filtration_flow_rate):
            raise ValueError(f"Invalid filtration flow rate: {self.filtration_flow_rate}")
        if not (FLOW_MIN <= self.filtration_flow_rate <= FLOW_MAX):
            raise ValueError(
                f"Filtration flow rate {self.filtration_flow_rate} out of bounds [{FLOW_MIN}, {FLOW_MAX}]"
            )


@dataclass
class PathogenObservation:
    """Telemetry recorded during an incubation cycle."""
    cycle: int
    incubation_temp_c: float
    centrifuge_rpm: float
    reagent_spent_ul: float
    viral_load_cfu: float
    neutralization_titer: float
    cross_reactivity_index: float
    estimated_r0: float
    confidence: float
    containment_integrity: float
    containment_status: str  # "SECURE", "WARNING", "BREACH"


@dataclass
class BiosecuritySimulationResult:
    """Outcome of a biosecurity incubation or validation run."""
    success: bool
    cycle_observations: List[PathogenObservation]
    final_confidence: float
    reagents_spent: float
    reagents_remaining: float
    containment_integrity: float
    feedback: str
    can_unlock_evidence: bool
    is_premature: bool
    containment_breached: bool


class BiosecurityPathogenModel:
    """
    Simulation model for BSL-4 pathogen characterization, sequential testing (Wald SPRT),
    and resource allocation trade-offs.
    """

    def __init__(
        self,
        total_budget: float = DEFAULT_TOTAL_REAGENTS,
        max_cycles: int = MAX_CYCLES,
        target_confidence: float = CONFIDENCE_TARGET,
        min_cycles: int = PREMATURE_CYCLE_THRESHOLD,
    ) -> None:
        self.total_budget: float = float(total_budget)
        self.reagents_remaining: float = float(total_budget)
        self.reagents_spent: float = 0.0
        self.max_cycles: int = int(max_cycles)
        self.target_confidence: float = float(target_confidence)
        self.min_cycles: int = int(min_cycles)
        self.current_cycle: int = 0
        self.containment_integrity: float = 1.0
        self.log_odds: float = -1.5  # Prior log-odds (~18% prior danger)
        self.observations: List[PathogenObservation] = []
        self.controls: AllocationControls = AllocationControls()

    def reset(self) -> None:
        """Reset the incubation model to initial baseline."""
        self.reagents_remaining = self.total_budget
        self.reagents_spent = 0.0
        self.current_cycle = 0
        self.containment_integrity = 1.0
        self.log_odds = -1.5
        self.observations.clear()
        self.controls = AllocationControls()

    def set_controls(
        self,
        incubation_temp_c: float,
        centrifuge_rpm: float,
        reagent_volume_ul: float,
        filtration_flow_rate: float,
    ) -> None:
        """Update operator allocation controls with bounds checking."""
        controls = AllocationControls(
            incubation_temp_c=float(incubation_temp_c),
            centrifuge_rpm=float(centrifuge_rpm),
            reagent_volume_ul=float(reagent_volume_ul),
            filtration_flow_rate=float(filtration_flow_rate),
        )
        controls.validate()
        self.controls = controls

    def step_cycle(self) -> PathogenObservation:
        """
        Execute one microfluidic incubation and centrifugal separation cycle.
        Returns the recorded observation telemetry.
        """
        if self.current_cycle >= self.max_cycles:
            raise RuntimeError(f"Max incubation cycles ({self.max_cycles}) reached.")

        if self.reagents_remaining < self.controls.reagent_volume_ul:
            raise ValueError(
                f"Insufficient reagents: requested {self.controls.reagent_volume_ul:.1f} uL, "
                f"remaining {self.reagents_remaining:.1f} uL."
            )

        self.current_cycle += 1
        vol = self.controls.reagent_volume_ul
        self.reagents_remaining -= vol
        self.reagents_spent += vol

        # 1. Pathogen growth kinetics (Gaussian thermal optimum centered at 37 C)
        temp_diff = self.controls.incubation_temp_c - TEMP_OPTIMAL_C
        growth_rate = 1.20 * math.exp(- (temp_diff ** 2) / (2.0 * (5.0 ** 2)))
        # Standard analytical logistic solution with initial inoculum V0 = 1000 CFU, K = 1.0e6 CFU
        v0 = 1000.0
        k_cap = 1.0e6
        t_eff = float(self.current_cycle)
        exp_arg = -min(20.0, max(-20.0, growth_rate * t_eff))
        viral_load = k_cap / (1.0 + ((k_cap - v0) / v0) * math.exp(exp_arg))

        # 2. Centrifugal purification and cross-reactivity
        # Lower RPM leaves cellular debris and non-specific binding artifacts.
        # RPM in [8000, 12000] gives clean separation; > 13500 causes mechanical shear.
        rpm = self.controls.centrifuge_rpm
        if rpm < RPM_OPTIMAL_MIN:
            cross_reactivity = 0.15 + 0.70 * math.exp(-(rpm - RPM_MIN) / 3000.0)
        elif rpm <= RPM_OPTIMAL_MAX:
            cross_reactivity = 0.12 + 0.05 * ((rpm - RPM_OPTIMAL_MIN) / (RPM_OPTIMAL_MAX - RPM_OPTIMAL_MIN))
        else:
            shear_factor = (rpm - RPM_OPTIMAL_MAX) / (RPM_MAX - RPM_OPTIMAL_MAX)
            cross_reactivity = 0.17 + 0.15 * shear_factor

        # 3. Containment integrity evolution
        # Balanced flow (around 1.0) maintains inward negative pressure with minor wear (-0.02/cycle).
        # Flow deviations cause aerodynamic turbulence or pressure drops.
        flow_dev = abs(self.controls.filtration_flow_rate - FLOW_DEFAULT)
        decay = 0.02 + 0.08 * (flow_dev ** 2)
        self.containment_integrity = max(0.0, self.containment_integrity - decay)

        if self.containment_integrity < CONTAINMENT_CRITICAL_FLOOR:
            status = "BREACH"
        elif self.containment_integrity < 0.65:
            status = "WARNING"
        else:
            status = "SECURE"

        # 4. Sequential Hypothesis Testing (Wald SPRT log-likelihood accumulation)
        # Quality of evidence per cycle depends on reagent volume and purity (1 - cross_reactivity)
        signal_purity = max(0.0, 1.0 - cross_reactivity)
        reagent_efficiency = min(1.0, vol / 20.0)
        thermal_adequacy = max(0.0, 1.0 - abs(temp_diff) / 10.0)

        # Increment log-odds if conditions are adequate for informative assay
        delta_info = (2.20 * signal_purity * reagent_efficiency * thermal_adequacy) - 0.20
        self.log_odds += delta_info

        # Posterior confidence (bounded strictly in [0.0, 1.0])
        clamped_odds = max(-15.0, min(15.0, self.log_odds))
        confidence = 1.0 / (1.0 + math.exp(-clamped_odds))
        confidence = max(0.0, min(1.0, confidence))

        # 5. Neutralization titer & estimated R0
        # Titer increases as informative cycles accumulate
        titer = min(0.96, confidence * signal_purity * (1.0 - math.exp(-self.reagents_spent / 30.0)))
        titer = max(0.0, min(1.0, titer))

        estimated_r0 = max(0.8, 3.5 * (1.0 - titer) * (viral_load / 1.0e6))

        obs = PathogenObservation(
            cycle=self.current_cycle,
            incubation_temp_c=self.controls.incubation_temp_c,
            centrifuge_rpm=self.controls.centrifuge_rpm,
            reagent_spent_ul=vol,
            viral_load_cfu=viral_load,
            neutralization_titer=titer,
            cross_reactivity_index=cross_reactivity,
            estimated_r0=estimated_r0,
            confidence=confidence,
            containment_integrity=self.containment_integrity,
            containment_status=status,
        )
        self.observations.append(obs)
        return obs

    def evaluate_protocol(self) -> BiosecuritySimulationResult:
        """
        Evaluate current experimental state against validation criteria.
        Checks for premature deployment, containment breaches, and sufficient statistical power.
        """
        if not self.observations:
            return BiosecuritySimulationResult(
                success=False,
                cycle_observations=[],
                final_confidence=0.0,
                reagents_spent=0.0,
                reagents_remaining=self.reagents_remaining,
                containment_integrity=self.containment_integrity,
                feedback="NO OBSERVATIONS: Run at least one incubation cycle before evaluating protocol.",
                can_unlock_evidence=False,
                is_premature=True,
                containment_breached=False,
            )

        last_obs = self.observations[-1]
        conf = last_obs.confidence
        cycles = self.current_cycle
        breached = (self.containment_integrity < CONTAINMENT_CRITICAL_FLOOR)

        # Check containment safety first
        if breached:
            return BiosecuritySimulationResult(
                success=False,
                cycle_observations=list(self.observations),
                final_confidence=conf,
                reagents_spent=self.reagents_spent,
                reagents_remaining=self.reagents_remaining,
                containment_integrity=self.containment_integrity,
                feedback="CONTAINMENT BREACH: Negative pressure failed! Critical pathogen bio-escape hazard.",
                can_unlock_evidence=False,
                is_premature=False,
                containment_breached=True,
            )

        # Check premature deployment / insufficient statistical power (Wald 1947 SPRT)
        is_premature = (cycles < self.min_cycles or conf < PREMATURE_CONFIDENCE_THRESHOLD)
        if is_premature:
            return BiosecuritySimulationResult(
                success=False,
                cycle_observations=list(self.observations),
                final_confidence=conf,
                reagents_spent=self.reagents_spent,
                reagents_remaining=self.reagents_remaining,
                containment_integrity=self.containment_integrity,
                feedback=(
                    f"PREMATURE PROTOCOL: {cycles} cycle(s) completed with confidence {conf:.1%}. "
                    f"Wald SPRT requires >= {self.min_cycles} cycles and >= {self.target_confidence:.1%} "
                    "confidence to reject Type I / Type II error."
                ),
                can_unlock_evidence=False,
                is_premature=True,
                containment_breached=False,
            )

        # Check target confidence
        if conf < self.target_confidence:
            return BiosecuritySimulationResult(
                success=False,
                cycle_observations=list(self.observations),
                final_confidence=conf,
                reagents_spent=self.reagents_spent,
                reagents_remaining=self.reagents_remaining,
                containment_integrity=self.containment_integrity,
                feedback=(
                    f"INSUFFICIENT STATISTICAL POWER: Confidence {conf:.1%} below target {self.target_confidence:.1%}. "
                    "Optimize centrifuge separation or increase reagent volume."
                ),
                can_unlock_evidence=False,
                is_premature=False,
                containment_breached=False,
            )

        # Success: Sufficient statistical confidence and secure containment
        feedback = (
            f"PROTOCOL VALIDATED: {cycles} cycles completed with {conf:.1%} confidence. "
            f"Neutralization titer reached {last_obs.neutralization_titer:.1%}. "
            f"Containment secure ({self.containment_integrity:.1%})."
        )
        return BiosecuritySimulationResult(
            success=True,
            cycle_observations=list(self.observations),
            final_confidence=conf,
            reagents_spent=self.reagents_spent,
            reagents_remaining=self.reagents_remaining,
            containment_integrity=self.containment_integrity,
            feedback=feedback,
            can_unlock_evidence=True,
            is_premature=False,
            containment_breached=False,
        )


class BiosecurityValidationWorkbench(ValidationWorkbench):
    """
    Formal scientific validation workbench for BSL-4 pathogen characterization,
    diagnostic certainty, and biosecurity countermeasure deployment.

    Executes the formal validation pipeline:
      1. Scenario selection & fragment prerequisite check.
      2. Interactive microfluidic incubation & sequential testing:
         - Tune incubation temperature, centrifuge RPM, reagent volume, filtration flow.
         - Observe pathogen replication kinetics, cross-reactivity, and containment integrity.
         - Validated sequential protocol unlocks empirical evidence.
      3. Claim classification (established vs plausible vs speculative).
      4. Evidence verification (requires neutralization assay, rejects endotoxin counterexamples).
      5. Replication check (BSL containment, PCR replication fallacy, logistic growth conservation).
      6. Deployment decision (applies campaign grant event, returns canonical validation record).
    """

    EVIDENCE_SUCCESS = 'EVIDENCE VALIDATED: Biosecurity evidence verified. Proceed to replication checks.'
    REPLICATION_SUCCESS = 'REPLICATION SUCCESSFUL: Biological invariants verified. Select deployment choice.'

    def __init__(self, scenarios_data: Optional[Dict[str, Any]] = None):
        self.scenarios_data = scenarios_data or self.load_scenarios()
        self.scenarios: Dict[str, Any] = self.scenarios_data.get("scenarios", {})

        self.active_scenario_id: Optional[str] = None
        self.active_scenario: Optional[Dict[str, Any]] = None
        self.model: BiosecurityPathogenModel = BiosecurityPathogenModel()

        # Simulation output state
        self.last_result: Optional[BiosecuritySimulationResult] = None
        self.experiment_passed: bool = False
        self.unlocked_evidence: Set[str] = set()

        # Validation pipeline state
        self.current_step: str = STEP_SELECT
        self.selected_claim_tier: Optional[str] = None
        self.selected_evidence: Set[str] = set()
        self.replication_answers: Dict[str, bool] = {}
        self.selected_deployment: Optional[str] = None
        self.validation_record: Optional[Dict[str, Any]] = None
        self.feedback_message: str = "SELECT A BIOSECURITY VALIDATION SCENARIO"
        self.feedback_is_error: bool = False

    def select_scenario(self, scenario_id: str, campaign: Optional[Any] = None) -> Tuple[bool, str]:
        """Select active biosecurity workbench scenario and verify fragment prerequisite."""
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

        # Initialize incubation model from scenario specification
        alloc = scenario.get("allocation_parameters", {})
        budget = alloc.get("total_reagent_budget", DEFAULT_TOTAL_REAGENTS)
        max_c = alloc.get("max_cycles", MAX_CYCLES)
        targets = scenario.get("target_criteria", {})
        target_conf = targets.get("min_confidence", CONFIDENCE_TARGET)
        min_c = targets.get("min_cycles", PREMATURE_CYCLE_THRESHOLD)

        self.model = BiosecurityPathogenModel(
            total_budget=budget,
            max_cycles=max_c,
            target_confidence=target_conf,
            min_cycles=min_c,
        )

        # Check if already completed in campaign
        if campaign is not None and self.is_completed(campaign):
            self.current_step = STEP_COMPLETED
            self.feedback_message = f"SCENARIO COMPLETED: Scenario {scenario_id} already validated"
            self.feedback_is_error = False
            return True, self.feedback_message

        self.current_step = STEP_EXPERIMENT
        self.experiment_passed = False
        self.unlocked_evidence.clear()
        self.selected_evidence.clear()
        self.replication_answers.clear()
        self.selected_deployment = None
        self.validation_record = None
        self.feedback_message = (
            f"LOADED: {scenario.get('title', scenario_id)}. "
            "Configure incubation parameters and execute sequential assay cycles."
        )
        self.feedback_is_error = False
        return True, self.feedback_message

    def set_allocation(
        self,
        temp_c: float,
        rpm: float,
        reagent_ul: float,
        filtration: float,
    ) -> None:
        """Update operator allocation controls."""
        self.model.set_controls(temp_c, rpm, reagent_ul, filtration)

    def set_controls(
        self,
        temp_c: float,
        rpm: float,
        reagent_ul: float,
        filtration: float,
    ) -> None:
        """Alias for set_allocation to match workbench control conventions."""
        self.set_allocation(temp_c, rpm, reagent_ul, filtration)

    def step_incubation_cycle(self) -> PathogenObservation:
        """Execute a single incubation and separation cycle."""
        return self.model.step_cycle()

    def run_protocol(self, steps: int = 4) -> BiosecuritySimulationResult:
        """Run multiple incubation cycles sequentially and evaluate."""
        for _ in range(steps):
            if self.model.current_cycle >= self.model.max_cycles:
                break
            if self.model.reagents_remaining < self.model.controls.reagent_volume_ul:
                break
            self.model.step_cycle()

        result = self.model.evaluate_protocol()
        self.last_result = result

        if result.success:
            self.experiment_passed = True
            self.unlocked_evidence.add("obs_pathogen_neutralization_assay")
            self.feedback_message = f"VALIDATION EXPERIMENT PASSED: {result.feedback}"
            self.feedback_is_error = False
        else:
            self.experiment_passed = False
            self.feedback_message = f"VALIDATION EXPERIMENT FAILED: {result.feedback}"
            self.feedback_is_error = True

        return result

    def reset_experiment(self) -> None:
        """Reset incubation state back to baseline."""
        self.model.reset()
        self.experiment_passed = False
        self.unlocked_evidence.clear()
        self.feedback_message = "Incubation model reset. Reagents restored to initial budget."
        self.feedback_is_error = False

    def advance_to_claim(self) -> Tuple[bool, str]:
        """Advance from experiment phase to claim classification phase."""
        if not self.experiment_passed:
            self.feedback_message = "EXPERIMENT REQUIRED: Validate incubation and neutralization protocol first."
            self.feedback_is_error = True
            return False, self.feedback_message
        self.current_step = STEP_CLAIM
        self.feedback_message = "Classify proposition into established, plausible, or speculative tier."
        self.feedback_is_error = False
        return True, self.feedback_message

    def toggle_evidence(self, evidence_id: str) -> bool:
        """Toggle an observation in active evidence selection with experimental gate enforcement."""
        if not self.active_scenario:
            return False

        pool = {item["id"]: item for item in self.active_scenario.get("evidence_pool", [])}
        item = pool.get(evidence_id)
        if not item:
            self.feedback_message = f"UNKNOWN EVIDENCE: {evidence_id}"
            self.feedback_is_error = True
            return False

        if item.get("requires_experiment", False) and evidence_id not in self.unlocked_evidence:
            self.feedback_message = f"EVIDENCE LOCKED: Observation '{evidence_id}' requires validated incubation protocol."
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

        choices = {c["id"]: c for c in self.active_scenario.get("deployment_choices", [])}
        if decision_id not in choices:
            self.feedback_message = f"UNKNOWN DEPLOYMENT: {decision_id}"
            self.feedback_is_error = True
            return False, self.feedback_message, None

        chosen = choices[decision_id]
        event_type = chosen.get("event_type")

        # Construct versioned validation record
        record = {
            "id": self.active_scenario.get("fragment_id", "FASR-003"),
            "scenario_id": self.active_scenario.get("id"),
            "scenario_version": int(self.active_scenario.get("version", 1)),
            "claim_id": self.active_scenario.get("claim_id"),
            "observations": sorted(list(self.selected_evidence)),
            "result": "validated",
            "confidence": 92,
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
        self.validation_record = record
        self.current_step = STEP_COMPLETED
        self.feedback_message = f"VALIDATION COMPLETE // {chosen['label']}: {chosen['summary']}"
        self.feedback_is_error = False
        return True, self.feedback_message, record

    def to_dict(self) -> Dict[str, Any]:
        """Serialize workbench state to persistent dictionary."""
        return {
            "scenario_id": self.active_scenario_id,
            "current_step": self.current_step,
            "selected_claim_tier": self.selected_claim_tier,
            "selected_evidence": sorted(list(self.selected_evidence)),
            "replication_answers": dict(self.replication_answers),
            "selected_deployment": self.selected_deployment,
            "validation_record": self.validation_record,
            "feedback_message": self.feedback_message,
            "experiment_passed": self.experiment_passed,
            "unlocked_evidence": sorted(list(self.unlocked_evidence)),
            "model": {
                "total_budget": self.model.total_budget,
                "reagents_remaining": self.model.reagents_remaining,
                "reagents_spent": self.model.reagents_spent,
                "current_cycle": self.model.current_cycle,
                "containment_integrity": self.model.containment_integrity,
                "log_odds": self.model.log_odds,
                "controls": {
                    "incubation_temp_c": self.model.controls.incubation_temp_c,
                    "centrifuge_rpm": self.model.controls.centrifuge_rpm,
                    "reagent_volume_ul": self.model.controls.reagent_volume_ul,
                    "filtration_flow_rate": self.model.controls.filtration_flow_rate,
                },
                "observations": [
                    {
                        "cycle": o.cycle,
                        "incubation_temp_c": o.incubation_temp_c,
                        "centrifuge_rpm": o.centrifuge_rpm,
                        "reagent_spent_ul": o.reagent_spent_ul,
                        "viral_load_cfu": o.viral_load_cfu,
                        "neutralization_titer": o.neutralization_titer,
                        "cross_reactivity_index": o.cross_reactivity_index,
                        "estimated_r0": o.estimated_r0,
                        "confidence": o.confidence,
                        "containment_integrity": o.containment_integrity,
                        "containment_status": o.containment_status,
                    }
                    for o in self.model.observations
                ],
            },
        }

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        scenarios_data: Optional[Dict[str, Any]] = None,
    ) -> "BiosecurityValidationWorkbench":
        """Reconstruct workbench from serialized dictionary."""
        wb = cls(scenarios_data=scenarios_data)
        scen_id = data.get("scenario_id")
        if scen_id:
            wb.select_scenario(scen_id)

        wb.current_step = data.get("current_step", STEP_SELECT)
        wb.selected_claim_tier = data.get("selected_claim_tier")
        wb.selected_evidence = set(data.get("selected_evidence", []))
        wb.replication_answers = data.get("replication_answers", {})
        wb.selected_deployment = data.get("selected_deployment")
        wb.validation_record = data.get("validation_record")
        wb.feedback_message = data.get("feedback_message", "")
        wb.experiment_passed = data.get("experiment_passed", False)
        wb.unlocked_evidence = set(data.get("unlocked_evidence", []))

        m_data = data.get("model", {})
        if m_data:
            wb.model.total_budget = m_data.get("total_budget", DEFAULT_TOTAL_REAGENTS)
            wb.model.reagents_remaining = m_data.get("reagents_remaining", DEFAULT_TOTAL_REAGENTS)
            wb.model.reagents_spent = m_data.get("reagents_spent", 0.0)
            wb.model.current_cycle = m_data.get("current_cycle", 0)
            wb.model.containment_integrity = m_data.get("containment_integrity", 1.0)
            wb.model.log_odds = m_data.get("log_odds", -1.5)

            ctrl_data = m_data.get("controls", {})
            if ctrl_data:
                wb.model.controls = AllocationControls(
                    incubation_temp_c=ctrl_data.get("incubation_temp_c", TEMP_DEFAULT_C),
                    centrifuge_rpm=ctrl_data.get("centrifuge_rpm", RPM_DEFAULT),
                    reagent_volume_ul=ctrl_data.get("reagent_volume_ul", REAGENT_DEFAULT_UL),
                    filtration_flow_rate=ctrl_data.get("filtration_flow_rate", FLOW_DEFAULT),
                )

            obs_list = m_data.get("observations", [])
            wb.model.observations = [
                PathogenObservation(
                    cycle=o["cycle"],
                    incubation_temp_c=o["incubation_temp_c"],
                    centrifuge_rpm=o["centrifuge_rpm"],
                    reagent_spent_ul=o["reagent_spent_ul"],
                    viral_load_cfu=o["viral_load_cfu"],
                    neutralization_titer=o["neutralization_titer"],
                    cross_reactivity_index=o["cross_reactivity_index"],
                    estimated_r0=o["estimated_r0"],
                    confidence=o["confidence"],
                    containment_integrity=o["containment_integrity"],
                    containment_status=o["containment_status"],
                )
                for o in obs_list
            ]

        return wb
