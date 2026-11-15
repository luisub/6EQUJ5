"""Connectome workbench, circuit inference and causal intervention trials."""

from dataclasses import dataclass, field
import math
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from .validation import (
    DATA_DIR, SCENARIOS_PATH, STEP_SELECT, STEP_EXPERIMENT, STEP_CLAIM,
    STEP_EVIDENCE, STEP_REPLICATION, STEP_DEPLOYMENT, STEP_COMPLETED,
    ValidationWorkbench,
)


PRIMARY_SOURCES = [
    "White_1986_Structure_Nervous_System_C_Elegans",
    "Jonas_Kording_2017_Could_Neuroscientist_Understand_Microprocessor",
    "Pearl_2009_Causality_Models_Reasoning_Inference",
    "BICCN_2021_Multimodal_Cell_Census_Motor_Cortex",
    "Bargmann_Marder_2013_From_Connectome_to_Brain_Function",
]


@dataclass
class NeuralNode:
    """A neuron in the authored connectome circuit."""
    id: str
    label: str
    node_type: str  # "SENSORY", "INTERNEURON", "MOTOR"
    threshold: float = 0.50
    base_activity: float = 0.0
    activation: float = 0.0
    clamped_value: Optional[float] = None  # Pearl do(X = v) causal intervention clamp


@dataclass
class SynapticEdge:
    """A synaptic connection or copper patch cable between neurons."""
    source_id: str
    target_id: str
    weight: float = 1.0  # Positive = excitatory (+1.0), Negative = inhibitory (-1.0)
    is_fixed: bool = False  # Fixed baseline anatomical connection
    is_candidate: bool = True  # Can be patched/toggled by player
    is_active: bool = False  # Currently connected by patch cable


@dataclass
class CircuitSimulationResult:
    """Telemetry and metrics from a connectome circuit trial."""
    node_activations: Dict[str, float]
    motor_outputs: Dict[str, float]
    causal_effects: Dict[str, float]
    is_stable: bool
    meets_target: bool
    feedback: str
    active_connections: List[Tuple[str, str, float]]


class ConnectomeCircuitModel:
    """
    Simulation model for neural circuit motifs and causal intervention trials.

    Implements:
      1. Heterogeneous sensory, interneuron, and motor graph propagation.
      2. Excitatory and inhibitory synaptic integration with sigmoid activation.
      3. Pearl's do-calculus causal interventions (do(X = 0) ablation vs do(X = 1) clamp).
      4. Spurious correlation detection distinguishing structural connectivity from functional causation.
    """

    def __init__(self, node_specs: List[Dict[str, Any]], edge_specs: List[Dict[str, Any]]):
        self.nodes: Dict[str, NeuralNode] = {}
        for ns in node_specs:
            self.nodes[ns["id"]] = NeuralNode(
                id=ns["id"],
                label=ns["label"],
                node_type=ns["node_type"],
                threshold=ns.get("threshold", 0.50),
                base_activity=ns.get("base_activity", 0.0),
            )

        self.edges: Dict[Tuple[str, str], SynapticEdge] = {}
        for es in edge_specs:
            key = (es["source_id"], es["target_id"])
            self.edges[key] = SynapticEdge(
                source_id=es["source_id"],
                target_id=es["target_id"],
                weight=float(es.get("weight", 1.0)),
                is_fixed=bool(es.get("is_fixed", False)),
                is_candidate=bool(es.get("is_candidate", True)),
                is_active=bool(es.get("is_fixed", False)),  # Fixed edges active by default
            )

    def reset_activity(self):
        """Reset all dynamic neuron activations to base activity."""
        for node in self.nodes.values():
            node.activation = node.base_activity
            node.clamped_value = None

    def patch_cable(self, source_id: str, target_id: str, weight: Optional[float] = None) -> bool:
        """Connect or enable a synaptic patch cable."""
        key = (source_id, target_id)
        if key not in self.edges:
            if source_id not in self.nodes or target_id not in self.nodes:
                return False
            # Allow authoring new candidate cable
            self.edges[key] = SynapticEdge(
                source_id=source_id,
                target_id=target_id,
                weight=1.0 if weight is None else float(weight),
                is_fixed=False,
                is_candidate=True,
                is_active=True,
            )
            return True

        edge = self.edges[key]
        edge.is_active = True
        if weight is not None:
            edge.weight = float(weight)
        return True

    def remove_cable(self, source_id: str, target_id: str) -> bool:
        """Disconnect an active candidate patch cable (fixed anatomical edges cannot be removed)."""
        key = (source_id, target_id)
        if key not in self.edges:
            return False
        edge = self.edges[key]
        if edge.is_fixed:
            return False  # Cannot remove locked anatomical spine
        edge.is_active = False
        return True

    def set_intervention(self, node_id: str, clamped_val: Optional[float]):
        """Apply Pearl causal intervention do(node = clamped_val); None releases intervention."""
        if node_id in self.nodes:
            self.nodes[node_id].clamped_value = clamped_val

    def step_circuit(
        self,
        sensory_inputs: Dict[str, float],
        steps: int = 8,
    ) -> CircuitSimulationResult:
        """
        Execute forward recurrent neural propagation across network.
        Sensory nodes drive interneurons; interneurons drive motor outputs.
        """
        # Apply sensory input stimuli
        for nid, val in sensory_inputs.items():
            if nid in self.nodes and self.nodes[nid].node_type == "SENSORY":
                self.nodes[nid].activation = max(0.0, min(1.0, float(val)))

        # Multi-step recurrent relaxation
        for _ in range(max(1, steps)):
            new_activations: Dict[str, float] = {}

            for nid, node in self.nodes.items():
                # If Pearl intervention is active, force clamped value
                if node.clamped_value is not None:
                    new_activations[nid] = max(0.0, min(1.0, node.clamped_value))
                    continue

                if node.node_type == "SENSORY":
                    new_activations[nid] = node.activation
                    continue

                # Calculate dendritic synaptic sum: z = sum(W_ij * A_i)
                synaptic_drive = 0.0
                for (src_id, tgt_id), edge in self.edges.items():
                    if tgt_id == nid and edge.is_active:
                        src_act = self.nodes[src_id].activation
                        synaptic_drive += edge.weight * src_act

                # Sigmoid transfer function: A = 1 / (1 + exp(-4 * (z - theta)))
                net_input = 4.0 * (synaptic_drive - node.threshold)
                # Bounded numerical stability for exponential
                clamped_net = max(-50.0, min(50.0, net_input))
                activation = 1.0 / (1.0 + math.exp(-clamped_net))
                new_activations[nid] = round(max(0.0, min(1.0, activation)), 4)

            # Synchronous state update
            for nid, act in new_activations.items():
                self.nodes[nid].activation = act

        # Collect telemetry
        all_acts = {nid: n.activation for nid, n in self.nodes.items()}
        motor_outs = {nid: n.activation for nid, n in self.nodes.items() if n.node_type == "MOTOR"}
        active_conns = [
            (e.source_id, e.target_id, e.weight)
            for e in self.edges.values()
            if e.is_active
        ]

        return CircuitSimulationResult(
            node_activations=all_acts,
            motor_outputs=motor_outs,
            causal_effects={},
            is_stable=True,
            meets_target=False,
            feedback="",
            active_connections=active_conns,
        )

    def evaluate_causal_effect(
        self,
        intervention_node_id: str,
        target_motor_id: str,
        baseline_sensory: Dict[str, float],
    ) -> float:
        """
        Quantitatively compute Pearl causal delta:
          Delta = M(do(X = 1.0)) - M(do(X = 0.0))
        Differentiates genuine causal mediators from correlational epiphenomena.
        """
        # Baseline with X = 1
        self.reset_activity()
        self.set_intervention(intervention_node_id, 1.0)
        res_hi = self.step_circuit(baseline_sensory)
        m_hi = res_hi.motor_outputs.get(target_motor_id, 0.0)

        # Baseline with X = 0
        self.reset_activity()
        self.set_intervention(intervention_node_id, 0.0)
        res_lo = self.step_circuit(baseline_sensory)
        m_lo = res_lo.motor_outputs.get(target_motor_id, 0.0)

        # Clean up clamp
        self.set_intervention(intervention_node_id, None)

        causal_delta = round(m_hi - m_lo, 4)
        return causal_delta


class ConnectomeValidationWorkbench(ValidationWorkbench):
    """
    Connectome scientific validation workbench.

    Executes the formal connectome validation pipeline:
      1. Scenario selection & fragment prerequisite check.
      2. Interactive circuit patch-cable mini-game:
         - Connect synaptic patch cables across heterogeneous sensory/interneuron/motor nodes.
         - Execute Pearl causal interventions (do(X = 0) ablation vs do(X = 1) clamp).
         - Resolve circuit puzzle without runaway excitation or spurious epiphenomena.
         - Successful causal demonstration unlocks empirical observation evidence.
      3. Claim classification (established vs plausible vs speculative).
      4. Evidence verification (requires causal motif, rejects spurious synchrony counterexamples).
      5. Replication check (Dale's Principle, Causal Intervention, Metabolic Bound).
      6. Deployment decision (applies campaign grant event, returns canonical validation record).
    """

    EVIDENCE_SUCCESS = 'EVIDENCE VALIDATED: Connectome motifs verified. Proceed to replication checks.'
    REPLICATION_SUCCESS = 'REPLICATION SUCCESSFUL: Biological invariants verified. Select deployment choice.'

    def __init__(self, scenarios_data: Optional[Dict[str, Any]] = None):
        self.scenarios_data = scenarios_data or self.load_scenarios()
        self.scenarios: Dict[str, Any] = self.scenarios_data.get("scenarios", {})

        self.active_scenario_id: Optional[str] = None
        self.active_scenario: Optional[Dict[str, Any]] = None
        self.circuit: Optional[ConnectomeCircuitModel] = None

        # Simulation output state
        self.last_result: Optional[CircuitSimulationResult] = None
        self.experiment_passed: bool = False
        self.unlocked_evidence: Set[str] = set()

        # Validation pipeline state
        self.current_step: str = STEP_SELECT
        self.selected_claim_tier: Optional[str] = None
        self.selected_evidence: Set[str] = set()
        self.replication_answers: Dict[str, bool] = {}
        self.selected_deployment: Optional[str] = None
        self.feedback_message: str = "SELECT A CONNECTOME VALIDATION SCENARIO"
        self.feedback_is_error: bool = False

    def select_scenario(self, scenario_id: str, campaign: Optional[Any] = None) -> Tuple[bool, str]:
        """Select active connectome workbench scenario and verify fragment prerequisite."""
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

        # Initialize neural circuit graph
        nodes_spec = scenario.get("circuit_nodes", [])
        edges_spec = scenario.get("circuit_edges", [])
        self.circuit = ConnectomeCircuitModel(nodes_spec, edges_spec)

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
        self.last_result = None

        self.feedback_message = f"SCENARIO LOADED: {scenario.get('title')}. Patch circuit cables & execute causal trial."
        self.feedback_is_error = False
        return True, self.feedback_message

    def patch_cable(self, source_id: str, target_id: str, weight: Optional[float] = None) -> Tuple[bool, str]:
        """Connect or adjust a candidate patch cable in the circuit."""
        if not self.circuit:
            return False, "ERR: No active circuit loaded"
        ok = self.circuit.patch_cable(source_id, target_id, weight)
        if ok:
            self.feedback_message = f"CABLE CONNECTED: {source_id} -> {target_id} (w={weight if weight is not None else 1.0:+.1f})"
            self.feedback_is_error = False
            return True, self.feedback_message
        else:
            self.feedback_message = f"PATCH ERROR: Unknown connection {source_id} -> {target_id}"
            self.feedback_is_error = True
            return False, self.feedback_message

    def remove_cable(self, source_id: str, target_id: str) -> Tuple[bool, str]:
        """Remove a candidate patch cable."""
        if not self.circuit:
            return False, "ERR: No active circuit loaded"
        ok = self.circuit.remove_cable(source_id, target_id)
        if ok:
            self.feedback_message = f"CABLE DISCONNECTED: {source_id} -> {target_id}"
            self.feedback_is_error = False
            return True, self.feedback_message
        else:
            self.feedback_message = f"DISCONNECT REJECTED: Fixed anatomical edge cannot be unpatched"
            self.feedback_is_error = True
            return False, self.feedback_message

    def run_circuit_trial(
        self,
        sensory_stimulus: Optional[Dict[str, float]] = None,
        intervention_node: Optional[str] = None,
        intervention_clamp: Optional[float] = None,
    ) -> Tuple[bool, str, CircuitSimulationResult]:
        """
        Execute a simulation trial across the neural circuit with optional causal intervention.

        Validates whether current wiring satisfies scenario functional targets:
          - Target motor output reaches required threshold.
          - Spurious or seizure motor outputs are suppressed by lateral inhibition.
          - Pearl causal intervention delta proves necessity (ablation reduces response).
        """
        if not self.circuit or not self.active_scenario:
            raise RuntimeError("Cannot run trial without active circuit and scenario")

        target_spec = self.active_scenario.get("target_circuit", {})
        default_stimulus = target_spec.get("default_sensory_stimulus", {})
        active_stim = default_stimulus if sensory_stimulus is None else sensory_stimulus

        # Apply causal intervention clamp if specified
        if intervention_node:
            self.circuit.set_intervention(intervention_node, intervention_clamp)

        # Run circuit propagation
        result = self.circuit.step_circuit(active_stim)
        self.last_result = result

        # Check required connections
        req_conns = target_spec.get("required_connections", [])
        active_keys = {(s, t) for s, t, _ in result.active_connections}
        missing_conns = [f"{s}->{t}" for s, t in req_conns if (s, t) not in active_keys]

        # Check forbidden connections (e.g. bypass cables causing runaway feedback)
        forbidden_conns = target_spec.get("forbidden_connections", [])
        violating_conns = [f"{s}->{t}" for s, t in forbidden_conns if (s, t) in active_keys]

        # Check motor output thresholds
        motor_targets = target_spec.get("motor_targets", {})
        motor_failures: List[str] = []
        for mid, spec in motor_targets.items():
            actual = result.motor_outputs.get(mid, 0.0)
            min_val = spec.get("min", 0.0)
            max_val = spec.get("max", 1.0)
            if not (min_val <= actual <= max_val):
                motor_failures.append(
                    f"{mid} activation {actual:.2f} outside required bounds [{min_val:.2f}, {max_val:.2f}]"
                )

        # Check causal intervention requirement (Jonas & Kording 2017: prove causal necessity)
        causal_spec = target_spec.get("required_causal_intervention")
        causal_passed = True
        causal_msg = ""
        if causal_spec and not missing_conns and not violating_conns:
            inode = causal_spec["node_id"]
            tmotor = causal_spec["target_motor"]
            min_delta = causal_spec.get("min_delta", 0.30)
            delta = self.circuit.evaluate_causal_effect(inode, tmotor, active_stim)
            result.causal_effects[f"{inode}->{tmotor}"] = delta
            if delta < min_delta:
                causal_passed = False
                causal_msg = f"Causal test failed: Delta M={delta:.2f} < {min_delta:.2f}. Node {inode} is not causally driving {tmotor}."

        # Compile feedback
        if violating_conns:
            result.meets_target = False
            result.feedback = f"RUNAWAY FEEDBACK: Forbidden patch cable(s) active: {', '.join(violating_conns)}"
            self.experiment_passed = False
            self.feedback_message = result.feedback
            self.feedback_is_error = True
            return False, self.feedback_message, result
        elif missing_conns:
            result.meets_target = False
            result.feedback = f"CIRCUIT INCOMPLETE: Missing required patch cable(s): {', '.join(missing_conns)}"
            self.experiment_passed = False
            self.feedback_message = result.feedback
            self.feedback_is_error = True
            return False, self.feedback_message, result
        elif motor_failures:
            result.meets_target = False
            result.feedback = f"MOTOR OUTPUT ERROR: {motor_failures[0]}"
            self.experiment_passed = False
            self.feedback_message = result.feedback
            self.feedback_is_error = True
            return False, self.feedback_message, result
        elif not causal_passed:
            result.meets_target = False
            result.feedback = causal_msg
            self.experiment_passed = False
            self.feedback_message = result.feedback
            self.feedback_is_error = True
            return False, self.feedback_message, result
        else:
            result.meets_target = True
            result.feedback = (
                "CAUSAL CIRCUIT MOTIF VERIFIED: Feedforward drive and lateral inhibition validated. "
                "Causal intervention confirms interneuron necessity. Evidence 'obs_causal_circuit_motif' unlocked."
            )
            self.experiment_passed = True
            for item in self.active_scenario.get("evidence_pool", []):
                if item.get("requires_experiment", False):
                    self.unlocked_evidence.add(item["id"])
            self.feedback_message = result.feedback
            self.feedback_is_error = False
            return True, self.feedback_message, result

    def advance_to_claim(self) -> Tuple[bool, str]:
        """Advance from circuit mini-game to claim classification step."""
        if not self.experiment_passed:
            self.feedback_message = "EXPERIMENT REQUIRED: Solve the neural circuit puzzle and verify causal intervention first."
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
            self.feedback_message = f"EVIDENCE LOCKED: Observation '{evidence_id}' requires successful causal circuit trial."
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
            "id": self.active_scenario.get("fragment_id", "FASR-004"),
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
