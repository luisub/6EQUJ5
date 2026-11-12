"""
MODULE: video_game/tests/test_labs.py
PURPOSE: Test the formal validation workbench, claim/evidence puzzle, replication checks, deployment decisions, and campaign event integration.
CALLED BY: pytest (`python -m pytest video_game/tests -q`).
HOW TO MODIFY: Add regression tests for new laboratory scenarios and validation puzzles; maintain zero wildcard imports.
"""

import math
import os
from pathlib import Path
import pytest
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from video_game.engine import config
from video_game.engine.campaign import Campaign, load_campaign_data
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.labs.formal import (
    FormalValidationWorkbench,
    load_lab_scenarios,
    STEP_SELECT,
    STEP_CLAIM,
    STEP_EVIDENCE,
    STEP_REPLICATION,
    STEP_DEPLOYMENT,
    STEP_COMPLETED,
)
from video_game.engine.labs.biosecurity import (
    BiosecurityValidationWorkbench,
    BiosecurityPathogenModel,
    BiosecuritySimulationResult,
    AllocationControls,
    PathogenObservation,
    PRIMARY_SOURCES as BIOSECURITY_PRIMARY_SOURCES,
    STEP_EXPERIMENT as BIOSECURITY_STEP_EXPERIMENT,
    TEMP_MIN_C,
    TEMP_MAX_C,
    RPM_MIN,
    RPM_MAX,
    REAGENT_MIN_UL,
    REAGENT_MAX_UL,
    FLOW_MIN,
    FLOW_MAX,
    CONFIDENCE_TARGET,
    PREMATURE_CYCLE_THRESHOLD,
    CONTAINMENT_CRITICAL_FLOOR,
)
from video_game.engine.labs.neuro import (
    ConnectomeValidationWorkbench,
    ConnectomeCircuitModel,
    CircuitSimulationResult,
    PRIMARY_SOURCES as CONNECTOME_PRIMARY_SOURCES,
)
from video_game.engine.labs.quantum import (
    QuantumValidationWorkbench,
    QuantumInterferenceModel,
    SimulationResult,
    PRIMARY_SOURCES as QUANTUM_PRIMARY_SOURCES,
    STEP_EXPERIMENT as QUANTUM_STEP_EXPERIMENT,
)
from video_game.engine.protocols import ScienceArcManager
from video_game.engine.save_game import SaveStore
from video_game.engine.scenes.lab import ScienceLabScene
from video_game.engine.state_machine import GameStateMachine


@pytest.fixture
def clean_campaign():
    """Create a clean campaign state with FASR-001 extracted."""
    campaign = Campaign()
    # Contact FASR-001
    campaign._state["contacted_civs"].append("FASR-001")
    campaign.apply_event({
        "event_id": "test_contact_f1",
        "type": "grant_fragment_fasr_001",
        "payload": {}
    })
    return campaign


def test_lab_scenarios_schema_and_integrity():
    """Verify lab_scenarios.json contains required metadata, citations, and structure."""
    data = load_lab_scenarios()
    assert data.get("schema_version") == 1
    scenarios = data.get("scenarios", {})
    assert "formal_fasr_001" in scenarios

    s = scenarios["formal_fasr_001"]
    assert s["id"] == "formal_fasr_001"
    assert s["version"] == 1
    assert s["fragment_id"] == "FASR-001"
    assert s["prerequisite_fragment"] == "FASR-001"
    assert "domain" in s
    assert len(s["source_references"]) >= 3
    assert "Landauer_1961_Irreversibility_and_Heat_Generation" in s["source_references"]
    assert "Ehman_1977_Wow_Signal_Detection" in s["source_references"]

    # Claim structure
    claim = s["claim"]
    assert claim["correct_tier"] == "speculative"
    assert len(claim["options"]) == 3
    tiers = {opt["tier"] for opt in claim["options"]}
    assert tiers == {"established", "plausible", "speculative"}

    # Evidence pool
    pool = s["evidence_pool"]
    assert len(pool) >= 3
    valid_ids = [item["id"] for item in pool if item["is_valid"]]
    assert set(s["required_observations"]).issubset(set(valid_ids))

    # Replication checks & Deployment choices
    assert len(s["replication_checks"]) >= 2
    assert len(s["deployment_choices"]) == 2
    for choice in s["deployment_choices"]:
        assert "event_type" in choice
        assert choice["id"] in ("deploy_analog_filter", "withhold_quarantine")


def test_formal_workbench_prerequisite_enforcement():
    """Verify workbench rejects scenario if prerequisite fragment is not extracted."""
    fresh_campaign = Campaign()  # Has not extracted FASR-001
    workbench = FormalValidationWorkbench()

    ok, msg = workbench.select_scenario("formal_fasr_001", fresh_campaign)
    assert ok is False
    assert "PREREQUISITE MISSING" in msg
    assert workbench.current_step == STEP_SELECT


def test_claim_tier_classification_and_explanatory_feedback(clean_campaign):
    """Verify wrong claim tiers yield explanatory feedback and retry; correct tier advances."""
    workbench = FormalValidationWorkbench()
    ok, msg = workbench.select_scenario("formal_fasr_001", clean_campaign)
    assert ok is True
    assert workbench.current_step == STEP_CLAIM

    # Attempt 1: 'established' -> Wrong! Explanatory feedback referencing thermodynamics
    ok1, fb1 = workbench.classify_claim("established")
    assert ok1 is False
    assert "Second Law" in fb1 or "Carnot" in fb1 or "Landauer" in fb1
    assert workbench.current_step == STEP_CLAIM  # Retains step for retry

    # Attempt 2: 'plausible' -> Wrong! Explanatory feedback referencing coupling
    ok2, fb2 = workbench.classify_claim("plausible")
    assert ok2 is False
    assert "coupling mechanisms" in fb2 or "precedent" in fb2
    assert workbench.current_step == STEP_CLAIM

    # Attempt 3: 'speculative' -> Correct!
    ok3, fb3 = workbench.classify_claim("speculative")
    assert ok3 is True
    assert "ACCEPTED" in fb3 or "Speculative tier" in fb3
    assert workbench.current_step == STEP_EVIDENCE


def test_speculative_tier_distinct_from_hostile_intent():
    """Verify speculative claim tier is explicitly distinct from hostile deception."""
    workbench = FormalValidationWorkbench()
    scen = workbench.scenarios["formal_fasr_001"]
    claim = scen["claim"]

    # Assert claim tier is speculative, but transmission is non-hostile and trusted
    assert claim["correct_tier"] == "speculative"
    assert claim["is_hostile"] is False
    assert claim["trustworthiness"] == "trusted_origin"


def test_evidence_observation_and_counterexample_filtering(clean_campaign):
    """Verify evidence filtering rejects counterexamples and requires all empirical observations."""
    workbench = FormalValidationWorkbench()
    workbench.select_scenario("formal_fasr_001", clean_campaign)
    workbench.classify_claim("speculative")
    assert workbench.current_step == STEP_EVIDENCE

    # Select only one valid observation -> Incomplete
    workbench.toggle_evidence("obs_entropy_seed")
    ok1, fb1 = workbench.verify_evidence()
    assert ok1 is False
    assert "INCOMPLETE EVIDENCE" in fb1
    assert workbench.current_step == STEP_EVIDENCE

    # Select terrestrial spark-gap RFI (counterexample) -> Rejection feedback
    workbench.toggle_evidence("obs_terrestrial_rfi")
    ok2, fb2 = workbench.verify_evidence()
    assert ok2 is False
    assert "COUNTEREXAMPLE DETECTED" in fb2
    assert workbench.current_step == STEP_EVIDENCE

    # Deselect counterexample and add second valid observation
    workbench.toggle_evidence("obs_terrestrial_rfi")  # Toggles off
    workbench.toggle_evidence("obs_snr_coherence")    # Toggles on
    ok3, fb3 = workbench.verify_evidence()
    assert ok3 is True
    assert "EVIDENCE VALIDATED" in fb3
    assert workbench.current_step == STEP_REPLICATION


def test_replication_invariant_checks(clean_campaign):
    """Verify replication checks require correct physical invariants before deployment."""
    workbench = FormalValidationWorkbench()
    workbench.select_scenario("formal_fasr_001", clean_campaign)
    workbench.classify_claim("speculative")
    workbench.toggle_evidence("obs_entropy_seed")
    workbench.toggle_evidence("obs_snr_coherence")
    workbench.verify_evidence()
    assert workbench.current_step == STEP_REPLICATION

    # Incomplete checks
    ok1, fb1 = workbench.verify_replication()
    assert ok1 is False
    assert "REPLICATION INCOMPLETE" in fb1

    # Inaccurate checks (claims perpetual motion is true)
    workbench.set_replication_check("check_cavity_conservation", True)
    workbench.set_replication_check("check_perpetual_motion", True)  # Wrong!
    ok2, fb2 = workbench.verify_replication()
    assert ok2 is False
    assert "REPLICATION FAILED" in fb2
    assert "Perpetual motion" in fb2

    # Correct invariant checks
    workbench.set_replication_check("check_perpetual_motion", False)  # Correct
    ok3, fb3 = workbench.verify_replication()
    assert ok3 is True
    assert "REPLICATION SUCCESSFUL" in fb3
    assert workbench.current_step == STEP_DEPLOYMENT


def test_deployment_choice_deploy_analog_filter(clean_campaign):
    """Verify deployment choice 'deploy_analog_filter' applies campaign event and updates meters."""
    workbench = FormalValidationWorkbench()
    workbench.select_scenario("formal_fasr_001", clean_campaign)
    workbench.classify_claim("speculative")
    workbench.toggle_evidence("obs_entropy_seed")
    workbench.toggle_evidence("obs_snr_coherence")
    workbench.verify_evidence()
    workbench.set_replication_check("check_cavity_conservation", True)
    workbench.set_replication_check("check_perpetual_motion", False)
    workbench.verify_replication()

    init_cert = clean_campaign.state.meters["scientific_certainty"]
    init_align = clean_campaign.state.meters["alignment_confidence"]
    init_agency = clean_campaign.state.meters["human_agency"]

    ok, msg, record = workbench.choose_deployment("deploy_analog_filter", clean_campaign)
    assert ok is True
    assert "VALIDATION COMPLETE" in msg
    assert record is not None
    assert record["deployment_decision"] == "deploy_analog_filter"
    assert record["claim_tier"] == "speculative"
    assert record["result"] == "validated"

    # Campaign state assertions
    assert len(clean_campaign.state.validation_records) == 1
    committed = clean_campaign.state.validation_records[0]
    assert committed["id"] == "FASR-001"
    assert committed["deployment_decision"] == "deploy_analog_filter"

    # Meter assertions
    assert clean_campaign.state.meters["scientific_certainty"] == init_cert + 10
    assert clean_campaign.state.meters["alignment_confidence"] == init_align + 5
    assert clean_campaign.state.meters["human_agency"] == init_agency + 5


def test_deployment_choice_withhold_quarantine(clean_campaign):
    """Verify deployment choice 'withhold_quarantine' applies distinct quarantine meter deltas."""
    workbench = FormalValidationWorkbench()
    workbench.select_scenario("formal_fasr_001", clean_campaign)
    workbench.classify_claim("speculative")
    workbench.toggle_evidence("obs_entropy_seed")
    workbench.toggle_evidence("obs_snr_coherence")
    workbench.verify_evidence()
    workbench.set_replication_check("check_cavity_conservation", True)
    workbench.set_replication_check("check_perpetual_motion", False)
    workbench.verify_replication()

    init_cert = clean_campaign.state.meters["scientific_certainty"]
    init_trust = clean_campaign.state.meters["public_trust"]
    init_bio = clean_campaign.state.meters["biosecurity_readiness"]

    ok, msg, record = workbench.choose_deployment("withhold_quarantine", clean_campaign)
    assert ok is True
    assert record["deployment_decision"] == "withhold_quarantine"

    # Campaign state assertions
    committed = clean_campaign.state.validation_records[0]
    assert committed["deployment_decision"] == "withhold_quarantine"

    # Meter assertions: Scientific Certainty +10, Public Trust +5, Biosecurity +5
    assert clean_campaign.state.meters["scientific_certainty"] == init_cert + 10
    assert clean_campaign.state.meters["public_trust"] == init_trust + 5
    assert clean_campaign.state.meters["biosecurity_readiness"] == init_bio + 5


def test_idempotent_validation_and_no_duplicate_rewards(clean_campaign):
    """Verify repeated completion attempts do not duplicate records or meter deltas."""
    workbench = FormalValidationWorkbench()
    workbench.select_scenario("formal_fasr_001", clean_campaign)
    workbench.classify_claim("speculative")
    workbench.toggle_evidence("obs_entropy_seed")
    workbench.toggle_evidence("obs_snr_coherence")
    workbench.verify_evidence()
    workbench.set_replication_check("check_cavity_conservation", True)
    workbench.set_replication_check("check_perpetual_motion", False)
    workbench.verify_replication()

    ok1, _, _ = workbench.choose_deployment("deploy_analog_filter", clean_campaign)
    assert ok1 is True
    assert len(clean_campaign.state.validation_records) == 1
    meters_after = dict(clean_campaign.state.meters)

    # Attempt to choose deployment a second time on the same campaign
    ok2, msg2, _ = workbench.choose_deployment("deploy_analog_filter", clean_campaign)
    assert ok2 is False
    assert "IDEMPOTENT" in msg2
    assert len(clean_campaign.state.validation_records) == 1
    assert clean_campaign.state.meters == meters_after

    # Reopen lab scene with same campaign -> auto-detects completion
    new_wb = FormalValidationWorkbench()
    ok3, msg3 = new_wb.select_scenario("formal_fasr_001", clean_campaign)
    assert ok3 is True
    assert new_wb.current_step == STEP_COMPLETED
    assert "SCENARIO VALIDATED" in msg3


def test_save_reload_preserves_validation_record_and_decision(tmp_path, clean_campaign):
    """Verify save/reload round-trip preserves validation record and deployment decision."""
    workbench = FormalValidationWorkbench()
    workbench.select_scenario("formal_fasr_001", clean_campaign)
    workbench.classify_claim("speculative")
    workbench.toggle_evidence("obs_entropy_seed")
    workbench.toggle_evidence("obs_snr_coherence")
    workbench.verify_evidence()
    workbench.set_replication_check("check_cavity_conservation", True)
    workbench.set_replication_check("check_perpetual_motion", False)
    workbench.verify_replication()
    workbench.choose_deployment("deploy_analog_filter", clean_campaign)

    # Save to disk
    store = SaveStore(tmp_path)
    saved = store.save(clean_campaign)
    assert saved is True

    # Reload from disk
    load_res = store.load()
    assert load_res.status == "ok"
    loaded_campaign = load_res.campaign

    assert len(loaded_campaign.state.validation_records) == 1
    record = loaded_campaign.state.validation_records[0]
    assert record["id"] == "FASR-001"
    assert record["scenario_id"] == "formal_fasr_001"
    assert record["scenario_version"] == 1
    assert record["claim_id"] == "claim_entropy_analog_filter"
    assert record["claim_tier"] == "speculative"
    assert record["deployment_decision"] == "deploy_analog_filter"
    assert record["result"] == "validated"
    assert record["confidence"] == 85
    assert "obs_entropy_seed" in record["observations"]
    assert "obs_snr_coherence" in record["observations"]
    assert loaded_campaign.state.meters == clean_campaign.state.meters


def test_science_lab_scene_rendering_and_interaction(clean_campaign):
    """Verify ScienceLabScene renders without error and handles keyboard input through all stages."""
    pygame.init()
    window = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    crt = CRTRenderer(scale=config.DEFAULT_SCALE)
    machine = GameStateMachine(crt, development=True)
    machine.campaign = clean_campaign

    lab_scene = machine.scenes[config.STATE_SCIENCE_LAB]
    machine.change_state(config.STATE_SCIENCE_LAB)
    machine.update(0.016)

    # Render initial claim classification stage
    machine.render()
    crt.present(window)
    assert lab_scene.workbench.current_step == STEP_CLAIM

    # Press '3' to select speculative claim tier
    event_3 = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_3)
    lab_scene.handle_event(event_3)
    assert lab_scene.workbench.current_step == STEP_EVIDENCE

    # Press '1' and '2' to toggle valid observations, then ENTER to confirm
    lab_scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1))
    lab_scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_2))
    lab_scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    assert lab_scene.workbench.current_step == STEP_REPLICATION

    # Press '1' to set cavity check to True, '2' to set perpetual motion to False, then ENTER to confirm
    lab_scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1))
    lab_scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_2))
    lab_scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    assert lab_scene.workbench.current_step == STEP_DEPLOYMENT

    # Press '1' to deploy analog filter
    lab_scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1))
    assert lab_scene.workbench.current_step == STEP_COMPLETED

    # Render completed stage
    machine.render()
    crt.present(window)

    # Press ESC to return to bunker
    lab_scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    machine.update(0.016)
    assert machine.current_state_name == config.STATE_BUNKER_HUB

    pygame.quit()


# ═════════════════════════════════════════════════════════════════════════════
# QUANTUM OPTICS WORKBENCH REGRESSION TESTS (TASK S01)
# ═════════════════════════════════════════════════════════════════════════════

def test_quantum_scenario_schema_and_primary_sources():
    """Verify quantum_fasr_002 schema integrity, target experiment bounds, and primary sources."""
    data = load_lab_scenarios()
    scenarios = data.get("scenarios", {})
    assert "quantum_fasr_002" in scenarios

    s = scenarios["quantum_fasr_002"]
    assert s["id"] == "quantum_fasr_002"
    assert s["version"] == 1
    assert s["fragment_id"] == "FASR-002"
    assert s["prerequisite_fragment"] == "FASR-001"
    assert s["workbench_type"] == "quantum"
    assert "Quantum Optics" in s["domain"]

    # Check 5 primary literature citations
    refs = s["source_references"]
    assert len(refs) >= 5
    assert "Young_1804_Double_Slit_Interference" in refs
    assert "Zurek_2003_Decoherence_Einselection" in refs
    assert "Schlosshauer_2005_Decoherence_Measurement" in refs
    assert "Caves_1982_Quantum_Limits_Amplifiers" in refs
    assert "Joos_Zeh_1985_Emergence_Classical_Properties" in refs

    # Target experiment bounds
    target = s["target_experiment"]
    assert target["wavelength_nm_min"] == 500.0
    assert target["wavelength_nm_max"] == 560.0
    assert target["slit_width_um_max"] == 30.0
    assert target["slit_distance_um_min"] == 80.0
    assert target["slit_distance_um_max"] == 160.0
    assert target["min_shielding"] == 0.85
    assert target["min_visibility"] == 0.70
    assert target["target_state"] == "COHERENT"

    # Evidence pool and required observations
    pool = {item["id"]: item for item in s["evidence_pool"]}
    assert "obs_quantum_coherence_fringe" in pool
    assert pool["obs_quantum_coherence_fringe"]["requires_experiment"] is True
    assert "obs_environmental_decoherence_decay" in pool
    assert pool["obs_environmental_decoherence_decay"]["is_valid"] is True
    assert "obs_detector_dark_current_noise" in pool
    assert pool["obs_detector_dark_current_noise"]["is_valid"] is False

    # Replication checks
    assert len(s["replication_checks"]) == 3
    chk_ids = [c["id"] for c in s["replication_checks"]]
    assert "check_complementarity" in chk_ids
    assert "check_superluminal_signaling" in chk_ids
    assert "check_born_rule_conservation" in chk_ids


def test_quantum_model_bounds_and_numerical_stability():
    """Verify quantum model handles boundary parameters cleanly without NaN, Inf, or instability."""
    model = QuantumInterferenceModel(seed=123)

    # 1. Boundary parameter tests
    boundary_cases = [
        (350.0, 5.0, 40.0, 0.0, 0.2),    # Lower bounds
        (850.0, 60.0, 300.0, 1.0, 2.0),  # Upper bounds
        (532.0, 20.0, 100.0, 0.9, 1.0),  # Nominal
        (400.0, 10.0, 250.0, 0.0, 0.5),  # High separation, zero shielding
    ]

    for lam, w, d, s, dist in boundary_cases:
        res = model.compute_interference(lam, w, d, s, dist)
        assert isinstance(res, SimulationResult)
        assert 0.0 <= res.visibility <= 1.0
        assert 0.0 <= res.coherence_factor <= 1.0
        assert res.fringe_spacing_mm > 0
        assert res.diffraction_width_mm > 0
        assert len(res.intensities) == 128
        for i_val in res.intensities:
            assert 0.0 <= i_val <= 1.0
            assert not math.isnan(i_val)
            assert not math.isinf(i_val)

    # 2. Invalid inputs must raise ValueError
    invalid_cases = [
        (200.0, 20.0, 100.0, 0.9, 1.0),  # Wavelength < 350
        (532.0, 2.0, 100.0, 0.9, 1.0),   # Slit width < 5
        (532.0, 20.0, 15.0, 0.9, 1.0),   # Slit distance <= slit width
        (532.0, 20.0, 100.0, -0.1, 1.0), # Shielding < 0
        (532.0, 20.0, 100.0, 0.9, 3.0),  # Distance > 2.0
    ]

    for lam, w, d, s, dist in invalid_cases:
        with pytest.raises(ValueError, match="Quantum control validation error"):
            model.compute_interference(lam, w, d, s, dist)


def test_quantum_interference_fringe_physics_and_decoherence():
    """Verify interference visibility matches physical decoherence damping (Young/Zurek model)."""
    model = QuantumInterferenceModel(seed=42)

    # Perfect cryogenic shielding (eta = 1.0) -> High visibility coherent fringes
    res_cryo = model.compute_interference(532.0, 20.0, 100.0, 1.0, 1.0)
    assert res_cryo.coherence_factor == 1.0
    assert res_cryo.visibility >= 0.85
    assert res_cryo.state == "COHERENT"

    # Zero shielding (eta = 0.0) -> Complete decoherence into classical mixture
    res_ambient = model.compute_interference(532.0, 20.0, 100.0, 0.0, 1.0)
    assert res_ambient.coherence_factor < 0.25
    assert res_ambient.visibility < 0.25
    assert res_ambient.state == "COLLAPSED"

    # Intermediate shielding (eta = 0.50) -> Partially coherent state
    res_mid = model.compute_interference(532.0, 20.0, 100.0, 0.5, 1.0)
    assert 0.25 <= res_mid.visibility <= 0.70
    assert res_mid.state == "PARTIALLY_COHERENT"

    # Verify theoretical fringe spacing delta_x = lambda * D / d
    # lambda = 532 nm, D = 1.0 m, d = 100 um -> delta_x = 5.32 mm
    assert abs(res_cryo.fringe_spacing_mm - 5.32) < 0.01

    # Verify central diffraction envelope width W = 2 * lambda * D / a
    # a = 20 um -> W = 2 * 532 * 1.0 / 20 = 53.2 mm
    assert abs(res_cryo.diffraction_width_mm - 53.2) < 0.01


def test_quantum_simulation_determinism_and_reproducibility():
    """Verify identical parameters and seed produce bitwise-reproducible intensity profiles."""
    model = QuantumInterferenceModel(seed=999)

    res1 = model.compute_interference(532.0, 20.0, 100.0, 0.90, 1.0, seed=777)
    res2 = model.compute_interference(532.0, 20.0, 100.0, 0.90, 1.0, seed=777)

    assert res1.visibility == res2.visibility
    assert res1.coherence_factor == res2.coherence_factor
    assert res1.snr_db == res2.snr_db
    assert res1.intensities == res2.intensities
    assert res1.positions_mm == res2.positions_mm


def test_quantum_workbench_prerequisite_enforcement():
    """Verify quantum workbench enforces extracted prerequisite fragment."""
    fresh_campaign = Campaign()  # Has not extracted FASR-001
    workbench = QuantumValidationWorkbench()

    ok, msg = workbench.select_scenario("quantum_fasr_002", fresh_campaign)
    assert ok is False
    assert "PREREQUISITE MISSING" in msg
    assert workbench.current_step == STEP_SELECT


def test_quantum_workbench_experiment_unlocks_evidence(clean_campaign):
    """Verify evidence requires experimental verification and cannot be toggled prematurely."""
    workbench = QuantumValidationWorkbench()
    ok, msg = workbench.select_scenario("quantum_fasr_002", clean_campaign)
    assert ok is True
    assert workbench.current_step == QUANTUM_STEP_EXPERIMENT
    assert workbench.experiment_passed is False

    # Attempting to toggle experimental evidence before running experiment fails
    toggled = workbench.toggle_evidence("obs_quantum_coherence_fringe")
    assert toggled is False
    assert "EVIDENCE LOCKED" in workbench.feedback_message
    assert "obs_quantum_coherence_fringe" not in workbench.selected_evidence

    # Attempt 1: Run experiment with insufficient shielding (0.20) -> Fails!
    workbench.set_controls(shielding_factor=0.20)
    exp_ok1, exp_msg1, res1 = workbench.run_experiment()
    assert exp_ok1 is False
    assert "insufficient" in exp_msg1.lower() or "decoherence" in exp_msg1.lower()
    assert workbench.experiment_passed is False
    assert "obs_quantum_coherence_fringe" not in workbench.unlocked_evidence

    # Attempt 2: Run experiment with target parameters -> Succeeds!
    workbench.set_controls(
        wavelength_nm=532.0,
        slit_width_um=20.0,
        slit_distance_um=100.0,
        shielding_factor=0.90,
        detector_distance_m=1.0,
    )
    exp_ok2, exp_msg2, res2 = workbench.run_experiment()
    assert exp_ok2 is True
    assert "EVIDENCE UNLOCKED" in exp_msg2
    assert workbench.experiment_passed is True
    assert "obs_quantum_coherence_fringe" in workbench.unlocked_evidence

    # Now toggle succeeds
    toggled_after = workbench.toggle_evidence("obs_quantum_coherence_fringe")
    assert toggled_after is True
    assert "obs_quantum_coherence_fringe" in workbench.selected_evidence


def test_quantum_claim_tier_classification_and_speculative_distinction(clean_campaign):
    """Verify quantum proposition classification yields clear educational explanations."""
    workbench = QuantumValidationWorkbench()
    workbench.select_scenario("quantum_fasr_002", clean_campaign)
    workbench.set_controls(shielding_factor=0.90)
    workbench.run_experiment()
    workbench.advance_to_claim()

    # Established tier: Rejected with decoherence physics feedback
    ok_est, fb_est = workbench.classify_claim("established")
    assert ok_est is False
    assert "decoherence scaling" in fb_est or "Zurek" in fb_est
    assert workbench.current_step == STEP_CLAIM

    # Plausible tier: Rejected with experimental precedent feedback
    ok_plaus, fb_plaus = workbench.classify_claim("plausible")
    assert ok_plaus is False
    assert "precedent" in fb_plaus or "extrapolating" in fb_plaus
    assert workbench.current_step == STEP_CLAIM

    # Speculative tier: Accepted with non-hostile theory confirmation
    ok_spec, fb_spec = workbench.classify_claim("speculative")
    assert ok_spec is True
    assert "ACCEPTED" in fb_spec
    assert workbench.current_step == STEP_EVIDENCE


def test_quantum_evidence_counterexample_rejection(clean_campaign):
    """Verify evidence verification rejects thermal noise counterexample and requires all signatures."""
    workbench = QuantumValidationWorkbench()
    workbench.select_scenario("quantum_fasr_002", clean_campaign)
    workbench.set_controls(shielding_factor=0.90)
    workbench.run_experiment()
    workbench.advance_to_claim()
    workbench.classify_claim("speculative")

    # Select only dark current noise (counterexample)
    workbench.toggle_evidence("obs_detector_dark_current_noise")
    ok1, msg1 = workbench.verify_evidence()
    assert ok1 is False
    assert "COUNTEREXAMPLE SELECTED" in msg1

    # Deselect counterexample, select only one valid observation
    workbench.toggle_evidence("obs_detector_dark_current_noise")
    workbench.toggle_evidence("obs_quantum_coherence_fringe")
    ok2, msg2 = workbench.verify_evidence()
    assert ok2 is False
    assert "INCOMPLETE EVIDENCE" in msg2

    # Select remaining required observation -> Succeeds!
    workbench.toggle_evidence("obs_environmental_decoherence_decay")
    ok3, msg3 = workbench.verify_evidence()
    assert ok3 is True
    assert "EVIDENCE VALIDATED" in msg3
    assert workbench.current_step == STEP_REPLICATION


def test_quantum_replication_checks(clean_campaign):
    """Verify quantum replication checks test complementarity, no-signaling, and unitarity."""
    workbench = QuantumValidationWorkbench()
    workbench.select_scenario("quantum_fasr_002", clean_campaign)
    workbench.set_controls(shielding_factor=0.90)
    workbench.run_experiment()
    workbench.advance_to_claim()
    workbench.classify_claim("speculative")
    workbench.toggle_evidence("obs_quantum_coherence_fringe")
    workbench.toggle_evidence("obs_environmental_decoherence_decay")
    workbench.verify_evidence()

    # Wrong answer on superluminal signaling (claiming it IS superluminal) -> Fails!
    workbench.set_replication_check("check_complementarity", True)
    workbench.set_replication_check("check_superluminal_signaling", True)  # WRONG!
    workbench.set_replication_check("check_born_rule_conservation", True)
    ok_wrong, msg_wrong = workbench.verify_replication()
    assert ok_wrong is False
    assert "REPLICATION FAILED" in msg_wrong
    assert "No-communication theorem" in msg_wrong

    # Correct answers -> Succeeds!
    workbench.set_replication_check("check_superluminal_signaling", False)
    ok_correct, msg_correct = workbench.verify_replication()
    assert ok_correct is True
    assert "REPLICATION SUCCESSFUL" in msg_correct
    assert workbench.current_step == STEP_DEPLOYMENT


def test_quantum_deployment_decision_and_campaign_grant(clean_campaign):
    """Verify committing quantum deployment updates campaign meters and validation records."""
    workbench = QuantumValidationWorkbench()
    workbench.select_scenario("quantum_fasr_002", clean_campaign)
    workbench.set_controls(shielding_factor=0.90)
    workbench.run_experiment()
    workbench.advance_to_claim()
    workbench.classify_claim("speculative")
    workbench.toggle_evidence("obs_quantum_coherence_fringe")
    workbench.toggle_evidence("obs_environmental_decoherence_decay")
    workbench.verify_evidence()
    workbench.set_replication_check("check_complementarity", True)
    workbench.set_replication_check("check_superluminal_signaling", False)
    workbench.set_replication_check("check_born_rule_conservation", True)
    workbench.verify_replication()

    initial_meters = dict(clean_campaign.state.meters)

    # Commit Mandela Phase-Shift deployment
    ok_dep, msg_dep, record = workbench.choose_deployment("deploy_mandela_phase_shift", clean_campaign)
    assert ok_dep is True
    assert "VALIDATION COMPLETE" in msg_dep
    assert record["id"] == "FASR-002"
    assert record["scenario_id"] == "quantum_fasr_002"
    assert record["claim_tier"] == "speculative"
    assert record["confidence"] == 90

    # Verify campaign state updated
    records = clean_campaign.state.validation_records
    assert any(r["id"] == "FASR-002" for r in records)
    assert clean_campaign.state.meters["scientific_certainty"] == initial_meters["scientific_certainty"] + 10
    assert clean_campaign.state.meters["human_agency"] == initial_meters["human_agency"] + 10
    assert clean_campaign.state.meters["public_trust"] == initial_meters["public_trust"] + 5

    # Verify idempotence: duplicate attempt cannot double-grant
    ok_dup, msg_dup, _ = workbench.choose_deployment("deploy_mandela_phase_shift", clean_campaign)
    assert ok_dup is False
    assert "IDEMPOTENT" in msg_dup


def test_quantum_save_reload_round_trip(tmp_path, clean_campaign):
    """Verify save/reload round-trip preserves quantum validation record and meters."""
    workbench = QuantumValidationWorkbench()
    workbench.select_scenario("quantum_fasr_002", clean_campaign)
    workbench.set_controls(shielding_factor=0.90)
    workbench.run_experiment()
    workbench.advance_to_claim()
    workbench.classify_claim("speculative")
    workbench.toggle_evidence("obs_quantum_coherence_fringe")
    workbench.toggle_evidence("obs_environmental_decoherence_decay")
    workbench.verify_evidence()
    workbench.set_replication_check("check_complementarity", True)
    workbench.set_replication_check("check_superluminal_signaling", False)
    workbench.set_replication_check("check_born_rule_conservation", True)
    workbench.verify_replication()
    workbench.choose_deployment("deploy_mandela_phase_shift", clean_campaign)

    # Save to disk
    store = SaveStore(tmp_path)
    assert store.save(clean_campaign) is True

    # Reload from disk
    load_res = store.load()
    assert load_res.status == "ok"
    loaded_campaign = load_res.campaign

    q_records = [r for r in loaded_campaign.state.validation_records if r["id"] == "FASR-002"]
    assert len(q_records) == 1
    qr = q_records[0]
    assert qr["scenario_id"] == "quantum_fasr_002"
    assert qr["claim_tier"] == "speculative"
    assert qr["deployment_decision"] == "deploy_mandela_phase_shift"
    assert "Young_1804_Double_Slit_Interference" in qr["source_references"]
    assert loaded_campaign.state.meters == clean_campaign.state.meters


# ═════════════════════════════════════════════════════════════════════════════
# CONNECTOME WORKBENCH REGRESSION TESTS (TASK S02)
# ═════════════════════════════════════════════════════════════════════════════

def test_connectome_scenario_schema_and_primary_sources():
    """Verify connectome_fasr_004 schema integrity, circuit graph, and primary sources."""
    data = load_lab_scenarios()
    scenarios = data.get("scenarios", {})
    assert "connectome_fasr_004" in scenarios

    s = scenarios["connectome_fasr_004"]
    assert s["id"] == "connectome_fasr_004"
    assert s["version"] == 1
    assert s["fragment_id"] == "FASR-004"
    assert s["prerequisite_fragment"] == "FASR-001"
    assert s["workbench_type"] == "neuro"
    assert "Computational Neuroscience" in s["domain"]

    # Check 5 primary citations
    refs = s["source_references"]
    assert len(refs) >= 5
    assert "White_1986_Structure_Nervous_System_C_Elegans" in refs
    assert "Jonas_Kording_2017_Could_Neuroscientist_Understand_Microprocessor" in refs
    assert "Pearl_2009_Causality_Models_Reasoning_Inference" in refs
    assert "BICCN_2021_Multimodal_Cell_Census_Motor_Cortex" in refs
    assert "Bargmann_Marder_2013_From_Connectome_to_Brain_Function" in refs

    # Circuit graph definitions
    nodes = {n["id"]: n for n in s["circuit_nodes"]}
    assert "S_OPTIC_BURST" in nodes
    assert "I_FEEDFORWARD" in nodes
    assert "I_LATERAL_INHIB" in nodes
    assert "M_DESYNC_PULSE" in nodes
    assert "M_RUNAWAY_SEIZURE" in nodes

    # Target circuit constraints
    tc = s["target_circuit"]
    assert len(tc["required_connections"]) == 3
    assert len(tc["forbidden_connections"]) >= 1
    assert "M_DESYNC_PULSE" in tc["motor_targets"]
    assert "M_RUNAWAY_SEIZURE" in tc["motor_targets"]
    assert tc["required_causal_intervention"]["node_id"] == "I_FEEDFORWARD"

    # Evidence pool and replication checks
    ev_ids = [item["id"] for item in s["evidence_pool"]]
    assert "obs_causal_circuit_motif" in ev_ids
    assert "obs_biccn_cell_taxonomy" in ev_ids
    assert "obs_spurious_synchrony" in ev_ids
    assert len(s["replication_checks"]) == 3


def test_connectome_circuit_propagation_and_activation_stability():
    """Verify circuit propagation, activation boundedness in [0.0, 1.0], and synaptic integration."""
    node_specs = [
        {"id": "S1", "label": "Sensory", "node_type": "SENSORY"},
        {"id": "I1", "label": "Interneuron Excitatory", "node_type": "INTERNEURON", "threshold": 0.40},
        {"id": "I2", "label": "Interneuron Inhibitory", "node_type": "INTERNEURON", "threshold": 0.30},
        {"id": "M1", "label": "Motor Target", "node_type": "MOTOR", "threshold": 0.45},
    ]
    edge_specs = [
        {"source_id": "S1", "target_id": "I1", "weight": 1.0, "is_fixed": True},
        {"source_id": "I1", "target_id": "M1", "weight": 1.2, "is_fixed": True},
        {"source_id": "I2", "target_id": "M1", "weight": -1.5, "is_fixed": True},
    ]

    circuit = ConnectomeCircuitModel(node_specs, edge_specs)

    # 1. Drive only with excitatory path (I2 = 0)
    res_exc = circuit.step_circuit({"S1": 1.0})
    assert 0.0 <= res_exc.motor_outputs["M1"] <= 1.0
    assert res_exc.motor_outputs["M1"] >= 0.70  # Strong motor drive

    # 2. Add inhibitory drive (clamp I2 = 1.0) -> Shuts down M1
    circuit.set_intervention("I2", 1.0)
    res_inhib = circuit.step_circuit({"S1": 1.0})
    assert res_inhib.motor_outputs["M1"] <= 0.30  # Robust lateral inhibition

    # 3. Stability check on all node activations
    for nid, act in res_inhib.node_activations.items():
        assert 0.0 <= act <= 1.0
        assert not math.isnan(act)
        assert not math.isinf(act)


def test_connectome_pearl_causal_intervention_delta():
    """Verify Pearl do-calculus intervention distinguishes causal transmission from correlation."""
    node_specs = [
        {"id": "S_BURST", "label": "Sensory", "node_type": "SENSORY"},
        {"id": "I_CAUSAL", "label": "Causal Interneuron", "node_type": "INTERNEURON", "threshold": 0.35},
        {"id": "I_BYSTANDER", "label": "Bystander Interneuron", "node_type": "INTERNEURON", "threshold": 0.35},
        {"id": "M_OUT", "label": "Motor Target", "node_type": "MOTOR", "threshold": 0.45},
    ]
    # S_BURST drives both I_CAUSAL and I_BYSTANDER (so both are statistically correlated!)
    # But ONLY I_CAUSAL connects to M_OUT.
    edge_specs = [
        {"source_id": "S_BURST", "target_id": "I_CAUSAL", "weight": 1.0, "is_fixed": True},
        {"source_id": "S_BURST", "target_id": "I_BYSTANDER", "weight": 1.0, "is_fixed": True},
        {"source_id": "I_CAUSAL", "target_id": "M_OUT", "weight": 1.5, "is_fixed": True},
    ]

    circuit = ConnectomeCircuitModel(node_specs, edge_specs)

    # Causal delta for I_CAUSAL: Delta = M(do(I_CAUSAL=1)) - M(do(I_CAUSAL=0))
    delta_causal = circuit.evaluate_causal_effect("I_CAUSAL", "M_OUT", {"S_BURST": 1.0})
    assert delta_causal >= 0.50  # Strong causal drive

    # Causal delta for I_BYSTANDER: Even though correlated with S_BURST, do(I_BYSTANDER) has zero effect!
    delta_bystander = circuit.evaluate_causal_effect("I_BYSTANDER", "M_OUT", {"S_BURST": 1.0})
    assert abs(delta_bystander) < 0.05  # Proves non-causal correlation


def test_connectome_workbench_prerequisite_enforcement():
    """Verify connectome workbench enforces extracted prerequisite fragment."""
    fresh_campaign = Campaign()  # Has not extracted FASR-001
    workbench = ConnectomeValidationWorkbench()

    ok, msg = workbench.select_scenario("connectome_fasr_004", fresh_campaign)
    assert ok is False
    assert "PREREQUISITE MISSING" in msg
    assert workbench.current_step == STEP_SELECT


def test_connectome_workbench_patch_and_trial_unlocks_evidence(clean_campaign):
    """Verify circuit mini-game requires complete candidate patching and causal verification to unlock evidence."""
    workbench = ConnectomeValidationWorkbench()
    ok, msg = workbench.select_scenario("connectome_fasr_004", clean_campaign)
    assert ok is True
    assert workbench.current_step == "EXPERIMENT"
    assert workbench.experiment_passed is False

    # Attempting to toggle evidence before running trial fails
    toggled = workbench.toggle_evidence("obs_causal_circuit_motif")
    assert toggled is False
    assert "EVIDENCE LOCKED" in workbench.feedback_message

    # Attempt 1: Run with default unpatched candidates -> Fails (missing connections)
    trial_ok1, trial_msg1, res1 = workbench.run_circuit_trial()
    assert trial_ok1 is False
    assert "Missing required patch cable" in trial_msg1
    assert workbench.experiment_passed is False

    # Attempt 2: Patch only feedforward drive (without lateral inhibition) -> Fails (seizure overflow!)
    workbench.patch_cable("I_FEEDFORWARD", "M_DESYNC_PULSE", weight=1.2)
    trial_ok2, trial_msg2, res2 = workbench.run_circuit_trial()
    assert trial_ok2 is False
    # Without inhibitory interneuron, collateral drive pushes M_RUNAWAY_SEIZURE > 0.35
    assert "Missing required patch cable" in trial_msg2 or "MOTOR OUTPUT ERROR" in trial_msg2

    # Attempt 3: Patch forbidden bypass cable (M_DESYNC_PULSE -> I_FEEDFORWARD) -> Fails
    workbench.patch_cable("M_DESYNC_PULSE", "I_FEEDFORWARD", weight=1.0)
    trial_ok3, trial_msg3, res3 = workbench.run_circuit_trial()
    assert trial_ok3 is False
    assert "RUNAWAY FEEDBACK" in trial_msg3 or "Forbidden patch cable" in trial_msg3
    workbench.remove_cable("M_DESYNC_PULSE", "I_FEEDFORWARD")

    # Attempt 4: Correctly patch all required candidate cables
    workbench.patch_cable("I_FEEDFORWARD", "M_DESYNC_PULSE", weight=1.2)
    workbench.patch_cable("S_OPTIC_BURST", "I_LATERAL_INHIB", weight=1.0)
    workbench.patch_cable("I_LATERAL_INHIB", "M_RUNAWAY_SEIZURE", weight=-1.5)

    trial_ok4, trial_msg4, res4 = workbench.run_circuit_trial()
    assert trial_ok4 is True
    assert "CAUSAL CIRCUIT MOTIF VERIFIED" in trial_msg4
    assert workbench.experiment_passed is True
    assert "obs_causal_circuit_motif" in workbench.unlocked_evidence

    # Now toggle succeeds
    toggled_after = workbench.toggle_evidence("obs_causal_circuit_motif")
    assert toggled_after is True
    assert "obs_causal_circuit_motif" in workbench.selected_evidence


def test_connectome_claim_tier_classification_and_speculative_distinction(clean_campaign):
    """Verify connectome claim classification yields educational feedback and accepts speculative tier."""
    workbench = ConnectomeValidationWorkbench()
    workbench.select_scenario("connectome_fasr_004", clean_campaign)
    workbench.patch_cable("I_FEEDFORWARD", "M_DESYNC_PULSE", weight=1.2)
    workbench.patch_cable("S_OPTIC_BURST", "I_LATERAL_INHIB", weight=1.0)
    workbench.patch_cable("I_LATERAL_INHIB", "M_RUNAWAY_SEIZURE", weight=-1.5)
    workbench.run_circuit_trial()
    workbench.advance_to_claim()

    # Established tier: Rejected
    ok_est, fb_est = workbench.classify_claim("established")
    assert ok_est is False
    assert "White 1986" in fb_est or "Structural connectome" in fb_est
    assert workbench.current_step == STEP_CLAIM

    # Plausible tier: Rejected
    ok_plaus, fb_plaus = workbench.classify_claim("plausible")
    assert ok_plaus is False
    assert "BICCN 2021" in fb_plaus or "extrapolating" in fb_plaus
    assert workbench.current_step == STEP_CLAIM

    # Speculative tier: Accepted
    ok_spec, fb_spec = workbench.classify_claim("speculative")
    assert ok_spec is True
    assert "ACCEPTED" in fb_spec
    assert workbench.current_step == STEP_EVIDENCE


def test_connectome_evidence_counterexample_rejection(clean_campaign):
    """Verify evidence verification rejects spurious synchrony counterexample."""
    workbench = ConnectomeValidationWorkbench()
    workbench.select_scenario("connectome_fasr_004", clean_campaign)
    workbench.patch_cable("I_FEEDFORWARD", "M_DESYNC_PULSE", weight=1.2)
    workbench.patch_cable("S_OPTIC_BURST", "I_LATERAL_INHIB", weight=1.0)
    workbench.patch_cable("I_LATERAL_INHIB", "M_RUNAWAY_SEIZURE", weight=-1.5)
    workbench.run_circuit_trial()
    workbench.advance_to_claim()
    workbench.classify_claim("speculative")

    # Select counterexample: obs_spurious_synchrony
    workbench.toggle_evidence("obs_spurious_synchrony")
    ok1, msg1 = workbench.verify_evidence()
    assert ok1 is False
    assert "COUNTEREXAMPLE SELECTED" in msg1

    # Deselect counterexample, select valid signatures
    workbench.toggle_evidence("obs_spurious_synchrony")
    workbench.toggle_evidence("obs_causal_circuit_motif")
    workbench.toggle_evidence("obs_biccn_cell_taxonomy")
    ok2, msg2 = workbench.verify_evidence()
    assert ok2 is True
    assert "EVIDENCE VALIDATED" in msg2
    assert workbench.current_step == STEP_REPLICATION


def test_connectome_replication_checks(clean_campaign):
    """Verify neurobiological replication checks test Dale's Principle, causality, and ATP bounds."""
    workbench = ConnectomeValidationWorkbench()
    workbench.select_scenario("connectome_fasr_004", clean_campaign)
    workbench.patch_cable("I_FEEDFORWARD", "M_DESYNC_PULSE", weight=1.2)
    workbench.patch_cable("S_OPTIC_BURST", "I_LATERAL_INHIB", weight=1.0)
    workbench.patch_cable("I_LATERAL_INHIB", "M_RUNAWAY_SEIZURE", weight=-1.5)
    workbench.run_circuit_trial()
    workbench.advance_to_claim()
    workbench.classify_claim("speculative")
    workbench.toggle_evidence("obs_causal_circuit_motif")
    workbench.toggle_evidence("obs_biccn_cell_taxonomy")
    workbench.verify_evidence()

    # Wrong answer: Claiming correlation implies causation
    workbench.set_replication_check("check_dales_principle", True)
    workbench.set_replication_check("check_correlation_causation", True)  # WRONG!
    workbench.set_replication_check("check_metabolic_atp_bound", True)
    ok_wrong, msg_wrong = workbench.verify_replication()
    assert ok_wrong is False
    assert "REPLICATION FAILED" in msg_wrong
    assert "Causal fallacy" in msg_wrong

    # Correct answers
    workbench.set_replication_check("check_correlation_causation", False)
    ok_correct, msg_correct = workbench.verify_replication()
    assert ok_correct is True
    assert "REPLICATION SUCCESSFUL" in msg_correct
    assert workbench.current_step == STEP_DEPLOYMENT


def test_connectome_deployment_decision_and_campaign_grant(clean_campaign):
    """Verify committing connectome deployment updates campaign meters and validation records."""
    workbench = ConnectomeValidationWorkbench()
    workbench.select_scenario("connectome_fasr_004", clean_campaign)
    workbench.patch_cable("I_FEEDFORWARD", "M_DESYNC_PULSE", weight=1.2)
    workbench.patch_cable("S_OPTIC_BURST", "I_LATERAL_INHIB", weight=1.0)
    workbench.patch_cable("I_LATERAL_INHIB", "M_RUNAWAY_SEIZURE", weight=-1.5)
    workbench.run_circuit_trial()
    workbench.advance_to_claim()
    workbench.classify_claim("speculative")
    workbench.toggle_evidence("obs_causal_circuit_motif")
    workbench.toggle_evidence("obs_biccn_cell_taxonomy")
    workbench.verify_evidence()
    workbench.set_replication_check("check_dales_principle", True)
    workbench.set_replication_check("check_correlation_causation", False)
    workbench.set_replication_check("check_metabolic_atp_bound", True)
    workbench.verify_replication()

    initial_meters = dict(clean_campaign.state.meters)

    # Commit Cognitive Blindspot deployment
    ok_dep, msg_dep, record = workbench.choose_deployment("deploy_cognitive_blindspot", clean_campaign)
    assert ok_dep is True
    assert "VALIDATION COMPLETE" in msg_dep
    assert record["id"] == "FASR-004"
    assert record["scenario_id"] == "connectome_fasr_004"
    assert record["claim_tier"] == "speculative"
    assert record["confidence"] == 90

    # Verify campaign state updated
    records = clean_campaign.state.validation_records
    assert any(r["id"] == "FASR-004" for r in records)
    assert clean_campaign.state.meters["scientific_certainty"] == initial_meters["scientific_certainty"] + 10
    assert clean_campaign.state.meters["human_agency"] == initial_meters["human_agency"] + 10
    assert clean_campaign.state.meters["public_trust"] == initial_meters["public_trust"] + 5

    # Verify idempotence
    ok_dup, msg_dup, _ = workbench.choose_deployment("deploy_cognitive_blindspot", clean_campaign)
    assert ok_dup is False
    assert "IDEMPOTENT" in msg_dup


def test_connectome_save_reload_round_trip(tmp_path, clean_campaign):
    """Verify save/reload round-trip preserves connectome validation record and meters."""
    workbench = ConnectomeValidationWorkbench()
    workbench.select_scenario("connectome_fasr_004", clean_campaign)
    workbench.patch_cable("I_FEEDFORWARD", "M_DESYNC_PULSE", weight=1.2)
    workbench.patch_cable("S_OPTIC_BURST", "I_LATERAL_INHIB", weight=1.0)
    workbench.patch_cable("I_LATERAL_INHIB", "M_RUNAWAY_SEIZURE", weight=-1.5)
    workbench.run_circuit_trial()
    workbench.advance_to_claim()
    workbench.classify_claim("speculative")
    workbench.toggle_evidence("obs_causal_circuit_motif")
    workbench.toggle_evidence("obs_biccn_cell_taxonomy")
    workbench.verify_evidence()
    workbench.set_replication_check("check_dales_principle", True)
    workbench.set_replication_check("check_correlation_causation", False)
    workbench.set_replication_check("check_metabolic_atp_bound", True)
    workbench.verify_replication()
    workbench.choose_deployment("deploy_cognitive_blindspot", clean_campaign)

    # Save to disk
    store = SaveStore(tmp_path)
    assert store.save(clean_campaign) is True

    # Reload from disk
    load_res = store.load()
    assert load_res.status == "ok"
    loaded_campaign = load_res.campaign

    c_records = [r for r in loaded_campaign.state.validation_records if r["id"] == "FASR-004"]
    assert len(c_records) == 1
    cr = c_records[0]
    assert cr["scenario_id"] == "connectome_fasr_004"
    assert cr["claim_tier"] == "speculative"
    assert cr["deployment_decision"] == "deploy_cognitive_blindspot"
    assert "White_1986_Structure_Nervous_System_C_Elegans" in cr["source_references"]
    assert loaded_campaign.state.meters == clean_campaign.state.meters


# ==============================================================================
# S03 BIOSECURITY WORKBENCH REGRESSION TESTS
# ==============================================================================

def test_biosecurity_scenario_schema_and_primary_sources():
    """Verify biosecurity scenario structure, parameter bounds, and primary literature citations."""
    scenarios = load_lab_scenarios()
    assert "biosecurity_fasr_003" in scenarios["scenarios"]
    scen = scenarios["scenarios"]["biosecurity_fasr_003"]

    assert scen["fragment_id"] == "FASR-003"
    assert scen["prerequisite_fragment"] == "FASR-001"
    assert scen["claim_id"] == "claim_pathogen_prototype_inhibition"
    assert scen["workbench_type"] == "biosecurity"

    # Verify primary literature citations
    refs = scen["source_references"]
    assert "Wald_1947_Sequential_Analysis_SPRT" in refs
    assert "Graham_Sullivan_2018_Prototype_Pathogen_Approach" in refs
    assert "WHO_2020_Laboratory_Biosafety_Manual_4th_Ed" in refs
    assert "Lipsitch_2016_Transmission_Dynamics_R0" in refs
    assert "Fletcher_2014_Clinical_Epidemiology_Diagnostic_Certainty" in refs

    # Verify allocation parameters and criteria
    alloc = scen["allocation_parameters"]
    assert alloc["incubation_temp_c"]["min"] == TEMP_MIN_C
    assert alloc["incubation_temp_c"]["max"] == TEMP_MAX_C
    assert alloc["centrifuge_rpm"]["min"] == RPM_MIN
    assert alloc["centrifuge_rpm"]["max"] == RPM_MAX
    assert alloc["reagent_volume_ul"]["min"] == REAGENT_MIN_UL
    assert alloc["reagent_volume_ul"]["max"] == REAGENT_MAX_UL

    targets = scen["target_criteria"]
    assert targets["min_confidence"] == CONFIDENCE_TARGET
    assert targets["min_cycles"] == PREMATURE_CYCLE_THRESHOLD


def test_biosecurity_model_bounds_and_resource_safety():
    """Verify physical control bounds, NaN/Inf protection, and non-negative reagent budget safety."""
    model = BiosecurityPathogenModel(total_budget=100.0)

    # Valid controls
    model.set_controls(37.0, 8000.0, 20.0, 1.0)
    assert model.controls.incubation_temp_c == 37.0

    # Temperature bounds
    with pytest.raises(ValueError, match="Incubation temperature"):
        model.set_controls(15.0, 8000.0, 20.0, 1.0)
    with pytest.raises(ValueError, match="Incubation temperature"):
        model.set_controls(50.0, 8000.0, 20.0, 1.0)
    with pytest.raises(ValueError, match="Invalid incubation temperature"):
        model.set_controls(float("nan"), 8000.0, 20.0, 1.0)

    # Centrifuge RPM bounds
    with pytest.raises(ValueError, match="Centrifuge RPM"):
        model.set_controls(37.0, 500.0, 20.0, 1.0)
    with pytest.raises(ValueError, match="Centrifuge RPM"):
        model.set_controls(37.0, 20000.0, 20.0, 1.0)

    # Reagent volume bounds
    with pytest.raises(ValueError, match="Reagent volume"):
        model.set_controls(37.0, 8000.0, 2.0, 1.0)
    with pytest.raises(ValueError, match="Reagent volume"):
        model.set_controls(37.0, 8000.0, 60.0, 1.0)

    # Filtration flow rate bounds
    with pytest.raises(ValueError, match="Filtration flow rate"):
        model.set_controls(37.0, 8000.0, 20.0, 0.05)
    with pytest.raises(ValueError, match="Filtration flow rate"):
        model.set_controls(37.0, 8000.0, 20.0, 2.5)

    # Budget exhaustion protection: cannot spend more reagents than remaining
    small_model = BiosecurityPathogenModel(total_budget=30.0)
    small_model.set_controls(37.0, 8000.0, 20.0, 1.0)
    small_model.step_cycle()
    assert small_model.reagents_remaining == 10.0

    # Next 20 uL step must be rejected without driving budget negative
    with pytest.raises(ValueError, match="Insufficient reagents"):
        small_model.step_cycle()
    assert small_model.reagents_remaining == 10.0


def test_biosecurity_pathogen_replication_and_temperature_optimum():
    """Verify pathogen growth kinetics follow thermal Gaussian optimum around 37 C."""
    # Near optimum (37 C)
    model_opt = BiosecurityPathogenModel()
    model_opt.set_controls(37.0, 8000.0, 20.0, 1.0)
    for _ in range(4):
        model_opt.step_cycle()
    opt_obs = model_opt.observations[-1]

    # Extreme sub-optimum cold (22 C)
    model_cold = BiosecurityPathogenModel()
    model_cold.set_controls(22.0, 8000.0, 20.0, 1.0)
    for _ in range(4):
        model_cold.step_cycle()
    cold_obs = model_cold.observations[-1]

    # Extreme heat (44 C)
    model_hot = BiosecurityPathogenModel()
    model_hot.set_controls(44.0, 8000.0, 20.0, 1.0)
    for _ in range(4):
        model_hot.step_cycle()
    hot_obs = model_hot.observations[-1]

    # Replication at optimum should significantly exceed extremes
    assert opt_obs.viral_load_cfu > cold_obs.viral_load_cfu * 5.0
    assert opt_obs.viral_load_cfu > hot_obs.viral_load_cfu * 5.0


def test_biosecurity_centrifugation_purity_and_cross_reactivity():
    """Verify centrifugal RPM controls debris separation purity and prevents cross-reactivity noise."""
    # Low RPM (1000) -> cellular debris remains in supernatant
    m_low = BiosecurityPathogenModel()
    m_low.set_controls(37.0, 1000.0, 20.0, 1.0)
    obs_low = m_low.step_cycle()
    assert obs_low.cross_reactivity_index > 0.60

    # Optimal RPM (8000) -> clean separation
    m_opt = BiosecurityPathogenModel()
    m_opt.set_controls(37.0, 8000.0, 20.0, 1.0)
    obs_opt = m_opt.step_cycle()
    assert obs_opt.cross_reactivity_index < 0.20

    # Over-speed RPM (14500) -> mechanical shear forces
    m_high = BiosecurityPathogenModel()
    m_high.set_controls(37.0, 14500.0, 20.0, 1.0)
    obs_high = m_high.step_cycle()
    assert obs_high.cross_reactivity_index > obs_opt.cross_reactivity_index


def test_biosecurity_sequential_testing_and_bayesian_confidence():
    """Verify Wald SPRT sequential analysis steadily increases posterior confidence with each informative cycle."""
    model = BiosecurityPathogenModel()
    model.set_controls(37.0, 8000.0, 20.0, 1.0)

    confidences = []
    for _ in range(4):
        obs = model.step_cycle()
        confidences.append(obs.confidence)

    # Monotonic accumulation of diagnostic evidence
    for i in range(len(confidences) - 1):
        assert confidences[i + 1] > confidences[i]

    # After 4 cycles, reaches target confidence (> 0.85)
    assert confidences[-1] >= CONFIDENCE_TARGET
    assert model.reagents_spent == 80.0
    assert model.reagents_remaining == 20.0

    eval_res = model.evaluate_protocol()
    assert eval_res.success is True
    assert eval_res.can_unlock_evidence is True
    assert eval_res.is_premature is False


def test_biosecurity_premature_deployment_and_failure_mode():
    """Verify premature deployment after only 1 cycle is rejected with Wald SPRT error feedback."""
    model = BiosecurityPathogenModel()
    model.set_controls(37.0, 8000.0, 20.0, 1.0)
    model.step_cycle()  # Only 1 cycle

    eval_res = model.evaluate_protocol()
    assert eval_res.success is False
    assert eval_res.is_premature is True
    assert eval_res.can_unlock_evidence is False
    assert "PREMATURE PROTOCOL" in eval_res.feedback
    assert "Wald SPRT" in eval_res.feedback


def test_biosecurity_containment_breach_hazard():
    """Verify extreme filtration flow rates degrade containment integrity below critical threshold."""
    model = BiosecurityPathogenModel()
    # Flow rate 2.0 creates continuous aerodynamic pressure stress
    model.set_controls(37.0, 8000.0, 10.0, 2.0)
    for _ in range(8):
        model.step_cycle()

    # Containment integrity drops below 0.40
    assert model.containment_integrity < CONTAINMENT_CRITICAL_FLOOR
    eval_res = model.evaluate_protocol()
    assert eval_res.success is False
    assert eval_res.containment_breached is True
    assert "CONTAINMENT BREACH" in eval_res.feedback


def test_biosecurity_resource_exhaustion_and_recovery():
    """Verify player can recover from near budget exhaustion by adjusting allocation controls."""
    workbench = BiosecurityValidationWorkbench()
    workbench.select_scenario("biosecurity_fasr_003")

    # High reagent burn: 45 uL per cycle
    workbench.set_allocation(temp_c=37.0, rpm=8000.0, reagent_ul=45.0, filtration=1.0)
    workbench.step_incubation_cycle()
    workbench.step_incubation_cycle()
    assert workbench.model.reagents_remaining == 10.0

    # Third cycle at 45 uL fails due to lack of reagents
    with pytest.raises(ValueError, match="Insufficient reagents"):
        workbench.step_incubation_cycle()

    # Recovery: Operator reduces allocation to 10 uL (matching remaining budget)
    workbench.set_allocation(temp_c=37.0, rpm=8000.0, reagent_ul=10.0, filtration=1.0)
    workbench.step_incubation_cycle()
    assert workbench.model.reagents_remaining == 0.0

    # Protocol successfully completes within budget
    res = workbench.model.evaluate_protocol()
    assert res.success is True
    assert res.final_confidence >= CONFIDENCE_TARGET


def test_biosecurity_workbench_prerequisite_enforcement(clean_campaign):
    """Verify biosecurity workbench enforces prerequisite contact fragment FASR-001."""
    workbench = BiosecurityValidationWorkbench()

    # Empty campaign without FASR-001
    empty_campaign = Campaign()
    ok, msg = workbench.select_scenario("biosecurity_fasr_003", empty_campaign)
    assert ok is False
    assert "PREREQUISITE MISSING" in msg

    # Clean campaign with FASR-001
    ok, msg = workbench.select_scenario("biosecurity_fasr_003", clean_campaign)
    assert ok is True
    assert workbench.current_step == BIOSECURITY_STEP_EXPERIMENT


def test_biosecurity_claim_tier_classification_and_educational_feedback():
    """Verify scientific claim classification: established/plausible rejected, speculative accepted."""
    workbench = BiosecurityValidationWorkbench()
    workbench.select_scenario("biosecurity_fasr_003")

    # Established rejected
    ok, msg = workbench.classify_claim("established")
    assert ok is False
    assert "REJECTED: ReVAMPP prototype pathogen frameworks" in msg

    # Plausible rejected
    ok, msg = workbench.classify_claim("plausible")
    assert ok is False
    assert "REJECTED: Sequential probability ratio testing" in msg

    # Speculative accepted
    ok, msg = workbench.classify_claim("speculative")
    assert ok is True
    assert "ACCEPTED: Speculative tier" in msg
    assert workbench.current_step == STEP_EVIDENCE


def test_biosecurity_evidence_counterexample_rejection():
    """Verify experimental gating unlocks neutralization evidence and rejects endotoxin counterexamples."""
    workbench = BiosecurityValidationWorkbench()
    workbench.select_scenario("biosecurity_fasr_003")

    # Cannot toggle experimental evidence before passing incubation trial
    assert workbench.toggle_evidence("obs_pathogen_neutralization_assay") is False
    assert "EVIDENCE LOCKED" in workbench.feedback_message

    # Pass experimental protocol
    workbench.set_allocation(37.0, 8000.0, 20.0, 1.0)
    res = workbench.run_protocol(steps=4)
    assert res.success is True

    # Now experimental evidence unlocks
    assert workbench.toggle_evidence("obs_pathogen_neutralization_assay") is True
    assert "obs_pathogen_neutralization_assay" in workbench.selected_evidence

    # Toggle background prototype phylogeny observation
    assert workbench.toggle_evidence("obs_prototype_phylogeny") is True

    # Select counterexample: uncalibrated endotoxin noise
    workbench.toggle_evidence("obs_uncalibrated_endotoxin_noise")

    # verify_evidence must reject counterexample
    ok, msg = workbench.verify_evidence()
    assert ok is False
    assert "COUNTEREXAMPLE SELECTED" in msg
    assert "Uncalibrated endotoxin turbidity" in msg

    # Deselect counterexample and re-verify
    workbench.toggle_evidence("obs_uncalibrated_endotoxin_noise")
    ok, msg = workbench.verify_evidence()
    assert ok is True
    assert workbench.current_step == STEP_REPLICATION


def test_biosecurity_replication_checks():
    """Verify biological replication invariants: containment (True), PCR fallacy (False), logistic growth (True)."""
    workbench = BiosecurityValidationWorkbench()
    workbench.select_scenario("biosecurity_fasr_003")
    workbench.set_allocation(37.0, 8000.0, 20.0, 1.0)
    workbench.run_protocol(steps=4)
    workbench.classify_claim("speculative")
    workbench.toggle_evidence("obs_pathogen_neutralization_assay")
    workbench.toggle_evidence("obs_prototype_phylogeny")
    workbench.verify_evidence()

    # Answering incorrectly fails replication
    workbench.set_replication_check("check_bsl_containment_barrier", False)
    workbench.set_replication_check("check_pcr_replication_fallacy", False)
    workbench.set_replication_check("check_logistic_growth_conservation", True)
    ok, msg = workbench.verify_replication()
    assert ok is False
    assert "REPLICATION FAILED" in msg

    # Correct invariant answers
    workbench.set_replication_check("check_bsl_containment_barrier", True)
    workbench.set_replication_check("check_pcr_replication_fallacy", False)
    workbench.set_replication_check("check_logistic_growth_conservation", True)
    ok, msg = workbench.verify_replication()
    assert ok is True
    assert workbench.current_step == STEP_DEPLOYMENT


def test_biosecurity_deployment_decision_and_campaign_grant(clean_campaign):
    """Verify biosecurity deployment commits validation record and grants campaign meter deltas."""
    initial_certainty = clean_campaign.state.meters["scientific_certainty"]
    initial_readiness = clean_campaign.state.meters["biosecurity_readiness"]
    initial_trust = clean_campaign.state.meters["public_trust"]

    workbench = BiosecurityValidationWorkbench()
    workbench.select_scenario("biosecurity_fasr_003", clean_campaign)
    workbench.set_allocation(37.0, 8000.0, 20.0, 1.0)
    workbench.run_protocol(steps=4)
    workbench.advance_to_claim()
    workbench.classify_claim("speculative")
    workbench.toggle_evidence("obs_pathogen_neutralization_assay")
    workbench.toggle_evidence("obs_prototype_phylogeny")
    workbench.verify_evidence()
    workbench.set_replication_check("check_bsl_containment_barrier", True)
    workbench.set_replication_check("check_pcr_replication_fallacy", False)
    workbench.set_replication_check("check_logistic_growth_conservation", True)
    workbench.verify_replication()

    # Commit deployment
    ok, msg, record = workbench.choose_deployment("deploy_prophylactic_inhibitor", clean_campaign)
    assert ok is True
    assert record is not None
    assert record["id"] == "FASR-003"
    assert record["deployment_decision"] == "deploy_prophylactic_inhibitor"
    assert "Wald_1947_Sequential_Analysis_SPRT" in record["source_references"]

    # Verify campaign state updates
    assert any(r["id"] == "FASR-003" for r in clean_campaign.state.validation_records)
    assert len(clean_campaign.state.validation_records) == 1
    assert clean_campaign.state.meters["scientific_certainty"] == initial_certainty + 10
    assert clean_campaign.state.meters["biosecurity_readiness"] == initial_readiness + 10
    assert clean_campaign.state.meters["public_trust"] == initial_trust + 5

    # Idempotent replay: cannot re-grant
    ok_repeat, msg_repeat, record_repeat = workbench.choose_deployment("deploy_prophylactic_inhibitor", clean_campaign)
    assert ok_repeat is False
    assert "IDEMPOTENT" in msg_repeat
    assert clean_campaign.state.meters["biosecurity_readiness"] == initial_readiness + 10


def test_biosecurity_save_reload_round_trip(tmp_path, clean_campaign):
    """Verify save/reload round-trip preserves biosecurity validation record and meters."""
    workbench = BiosecurityValidationWorkbench()
    workbench.select_scenario("biosecurity_fasr_003", clean_campaign)
    workbench.set_allocation(37.0, 8000.0, 20.0, 1.0)
    workbench.run_protocol(steps=4)
    workbench.advance_to_claim()
    workbench.classify_claim("speculative")
    workbench.toggle_evidence("obs_pathogen_neutralization_assay")
    workbench.toggle_evidence("obs_prototype_phylogeny")
    workbench.verify_evidence()
    workbench.set_replication_check("check_bsl_containment_barrier", True)
    workbench.set_replication_check("check_pcr_replication_fallacy", False)
    workbench.set_replication_check("check_logistic_growth_conservation", True)
    workbench.verify_replication()
    workbench.choose_deployment("deploy_prophylactic_inhibitor", clean_campaign)

    # Save to disk
    store = SaveStore(tmp_path)
    assert store.save(clean_campaign) is True

    # Reload from disk
    load_res = store.load()
    assert load_res.status == "ok"
    loaded_campaign = load_res.campaign

    b_records = [r for r in loaded_campaign.state.validation_records if r["id"] == "FASR-003"]
    assert len(b_records) == 1
    br = b_records[0]
    assert br["scenario_id"] == "biosecurity_fasr_003"
    assert br["claim_tier"] == "speculative"
    assert br["deployment_decision"] == "deploy_prophylactic_inhibitor"
    assert "Graham_Sullivan_2018_Prototype_Pathogen_Approach" in br["source_references"]
    assert loaded_campaign.state.meters == clean_campaign.state.meters


# ==============================================================================
# S04 SCIENCE ARCS & CAMPAIGN METERS INTEGRATION TESTS
# ==============================================================================

def test_science_arc_catalog_audit():
    """Verify that all 4 workbenches exist and provide both beginner and advanced scenarios."""
    arc_mgr = ScienceArcManager()
    report = arc_mgr.audit_catalog()

    assert report["is_valid"] is True
    assert report["all_workbenches_present"] is True
    assert report["has_beginner_and_advanced"] is True
    assert report["total_scenarios"] == 8

    # Each of the 4 workbenches must have exactly 2 scenarios (1 beginner, 1 advanced)
    for wb in ["formal", "quantum", "neuro", "biosecurity"]:
        wb_info = report["workbenches"][wb]
        assert wb_info["count"] == 2
        assert wb_info["has_beginner"] is True
        assert wb_info["has_advanced"] is True


def test_science_arc_educational_claims_and_counterexamples():
    """Audit educational claim tiers, non-hostile theory distinctions, and counterexample feedback."""
    arc_mgr = ScienceArcManager()
    audit = arc_mgr.audit_educational_claims()

    assert audit["is_valid"] is True
    assert audit["audited_scenarios"] == 8
    assert audit["counterexamples_verified"] >= 8
    assert audit["speculative_distinctions_verified"] == 8


def test_six_campaign_meters_coverage_and_updates():
    """Verify that all six campaign meters receive updates from registered validation deployment choices."""
    arc_mgr = ScienceArcManager()
    all_covered, covered_meters = arc_mgr.verify_all_meters_covered()

    assert all_covered is True
    assert covered_meters == {
        "scientific_certainty",
        "alignment_confidence",
        "coordination_capacity",
        "public_trust",
        "human_agency",
        "biosecurity_readiness",
    }


def test_workbench_factory_delegation(clean_campaign):
    """Verify ScienceArcManager instantiates the correct specialized workbench class for each discipline."""
    arc_mgr = ScienceArcManager()

    wb_formal = arc_mgr.create_workbench("formal_fasr_001", clean_campaign)
    assert isinstance(wb_formal, FormalValidationWorkbench)

    wb_quantum = arc_mgr.create_workbench("quantum_fasr_002", clean_campaign)
    assert isinstance(wb_quantum, QuantumValidationWorkbench)

    wb_neuro = arc_mgr.create_workbench("connectome_fasr_004", clean_campaign)
    assert isinstance(wb_neuro, ConnectomeValidationWorkbench)

    wb_biosec = arc_mgr.create_workbench("biosecurity_fasr_003", clean_campaign)
    assert isinstance(wb_biosec, BiosecurityValidationWorkbench)


def test_advanced_formal_szilard_engine_validation(clean_campaign):
    """Full validation walkthrough of formal_adv_fasr_001: Szilard engine and Landauer erasure work."""
    init_meters = dict(clean_campaign.state.meters)

    wb = FormalValidationWorkbench()
    ok, msg = wb.select_scenario("formal_adv_fasr_001", clean_campaign)
    assert ok is True

    # Classify established tier (Szilard/Landauer thermodynamics)
    ok, msg = wb.classify_claim("established")
    assert ok is True
    assert "ACCEPTED: Established physics" in msg

    # Evidence selection: select valid observations and reject perpetual motion counterexample
    wb.toggle_evidence("obs_szilard_bit_work")
    wb.toggle_evidence("obs_landauer_dissipation")
    wb.toggle_evidence("obs_perpetual_motion_demon")
    ok, msg = wb.verify_evidence()
    assert ok is False
    assert "COUNTEREXAMPLE SELECTED" in msg

    # Deselect counterexample
    wb.toggle_evidence("obs_perpetual_motion_demon")
    ok, msg = wb.verify_evidence()
    assert ok is True

    # Replication invariants (Jarzynski=True, free energy from vacuum=False, Landauer irreversibility=True)
    wb.set_replication_check("check_jarzynski_equality", True)
    wb.set_replication_check("check_free_energy_from_vacuum", False)
    wb.set_replication_check("check_erasure_irreversibility", True)
    ok, msg = wb.verify_replication()
    assert ok is True

    # Commit deployment
    ok, msg, record = wb.choose_deployment("deploy_szilard_coordination_network", clean_campaign)
    assert ok is True
    assert record["id"] == "FASR-001"
    assert record["scenario_id"] == "formal_adv_fasr_001"

    # Verify meter deltas: Coordination +10, Certainty +10, Agency +5
    assert clean_campaign.state.meters["coordination_capacity"] == init_meters["coordination_capacity"] + 10
    assert clean_campaign.state.meters["scientific_certainty"] == init_meters["scientific_certainty"] + 10
    assert clean_campaign.state.meters["human_agency"] == init_meters["human_agency"] + 5


def test_advanced_quantum_delayed_choice_eraser_validation(clean_campaign):
    """Full validation walkthrough of quantum_adv_fasr_002: Delayed choice quantum eraser."""
    init_meters = dict(clean_campaign.state.meters)

    wb = QuantumValidationWorkbench()
    ok, msg = wb.select_scenario("quantum_adv_fasr_002", clean_campaign)
    assert ok is True

    # Tune controls and execute experiment
    wb.wavelength_nm = 532.0
    wb.slit_width_um = 20.0
    wb.slit_distance_um = 100.0
    wb.shielding_factor = 0.90
    ok_exp, msg_exp, sim_res = wb.run_experiment()
    assert ok_exp is True
    assert sim_res.meets_target is True

    wb.advance_to_claim()
    ok, msg = wb.classify_claim("speculative")
    assert ok is True

    # Toggle evidence and reject superluminal signaling counterexample
    wb.toggle_evidence("obs_environmental_decoherence_decay")
    wb.toggle_evidence("obs_quantum_coherence_fringe")
    wb.toggle_evidence("obs_superluminal_signaling")
    ok, msg = wb.verify_evidence()
    assert ok is False
    assert "COUNTEREXAMPLE SELECTED" in msg

    wb.toggle_evidence("obs_superluminal_signaling")
    ok, msg = wb.verify_evidence()
    assert ok is True

    # Replication invariants (No-signaling=False, Wheeler delayed choice=True, Born unitarity=True)
    wb.set_replication_check("check_no_signaling_theorem", False)
    wb.set_replication_check("check_wheeler_delayed_choice", True)
    wb.set_replication_check("check_density_matrix_unitarity", True)
    ok, msg = wb.verify_replication()
    assert ok is True

    # Commit deployment: Certainty +10, Confidence +10, Agency +5
    ok, msg, record = wb.choose_deployment("deploy_quantum_eraser_radar", clean_campaign)
    assert ok is True
    assert record["id"] == "FASR-002"
    assert record["scenario_id"] == "quantum_adv_fasr_002"

    assert clean_campaign.state.meters["scientific_certainty"] == init_meters["scientific_certainty"] + 10
    assert clean_campaign.state.meters["alignment_confidence"] == init_meters["alignment_confidence"] + 10
    assert clean_campaign.state.meters["human_agency"] == init_meters["human_agency"] + 5


def test_advanced_connectome_attractor_dynamics_validation(clean_campaign):
    """Full validation walkthrough of connectome_adv_fasr_004: Recurrent attractor dynamics."""
    init_meters = dict(clean_campaign.state.meters)

    wb = ConnectomeValidationWorkbench()
    ok, msg = wb.select_scenario("connectome_adv_fasr_004", clean_campaign)
    assert ok is True

    # Patch cables
    wb.patch_cable("I_FEEDFORWARD", "M_DESYNC_PULSE", 1.2)
    wb.patch_cable("S_OPTIC_BURST", "I_LATERAL_INHIB", 1.0)
    wb.patch_cable("I_LATERAL_INHIB", "M_RUNAWAY_SEIZURE", -1.5)
    ok_trial, msg_trial, trial_res = wb.run_circuit_trial()
    assert ok_trial is True
    assert trial_res.meets_target is True

    wb.advance_to_claim()
    ok, msg = wb.classify_claim("speculative")
    assert ok is True

    # Toggle evidence and reject infinite capacity counterexample
    wb.toggle_evidence("obs_causal_circuit_motif")
    wb.toggle_evidence("obs_biccn_cell_taxonomy")
    wb.toggle_evidence("obs_infinite_capacity_network")
    ok, msg = wb.verify_evidence()
    assert ok is False
    assert "COUNTEREXAMPLE SELECTED" in msg

    wb.toggle_evidence("obs_infinite_capacity_network")
    ok, msg = wb.verify_evidence()
    assert ok is True

    # Replication invariants (Hopfield capacity bound=True, Hebbian runaway=True, single-neuron consciousness=False)
    wb.set_replication_check("check_hopfield_capacity_bound", True)
    wb.set_replication_check("check_hebbian_unbounded_growth", True)
    wb.set_replication_check("check_single_neuron_consciousness", False)
    ok, msg = wb.verify_replication()
    assert ok is True

    # Commit deployment: Agency +15, Certainty +10, Confidence +5
    ok, msg, record = wb.choose_deployment("deploy_attractor_neuro_shield", clean_campaign)
    assert ok is True
    assert record["id"] == "FASR-004"
    assert record["scenario_id"] == "connectome_adv_fasr_004"

    assert clean_campaign.state.meters["human_agency"] == init_meters["human_agency"] + 15
    assert clean_campaign.state.meters["scientific_certainty"] == init_meters["scientific_certainty"] + 10
    assert clean_campaign.state.meters["alignment_confidence"] == init_meters["alignment_confidence"] + 5


def test_advanced_biosecurity_antigenic_drift_escape_validation(clean_campaign):
    """Full validation walkthrough of biosecurity_adv_fasr_003: Antigenic drift and escape variants."""
    init_meters = dict(clean_campaign.state.meters)

    wb = BiosecurityValidationWorkbench()
    ok, msg = wb.select_scenario("biosecurity_adv_fasr_003", clean_campaign)
    assert ok is True

    # Allocate parameters and run 4 sequential incubation cycles
    wb.set_allocation(temp_c=37.0, rpm=8000.0, reagent_ul=20.0, filtration=1.0)
    sim_res = wb.run_protocol(steps=4)
    assert sim_res.success is True

    wb.advance_to_claim()
    ok, msg = wb.classify_claim("speculative")
    assert ok is True

    # Toggle evidence and reject zero fitness cost counterexample
    wb.toggle_evidence("obs_pathogen_neutralization_assay")
    wb.toggle_evidence("obs_prototype_phylogeny")
    wb.toggle_evidence("obs_zero_fitness_cost_escape")
    ok, msg = wb.verify_evidence()
    assert ok is False
    assert "COUNTEREXAMPLE SELECTED" in msg

    wb.toggle_evidence("obs_zero_fitness_cost_escape")
    ok, msg = wb.verify_evidence()
    assert ok is True

    # Replication invariants (Antigenic distance=True, universal antigen=False, HEPA filtration=True)
    wb.set_replication_check("check_antigenic_distance_metric", True)
    wb.set_replication_check("check_universal_antigen_immutability", False)
    wb.set_replication_check("check_bsl_aerosol_filtration", True)
    ok, msg = wb.verify_replication()
    assert ok is True

    # Commit deployment: Readiness +15, Coordination +10, Trust +5
    ok, msg, record = wb.choose_deployment("deploy_broad_spectrum_shield", clean_campaign)
    assert ok is True
    assert record["id"] == "FASR-003"
    assert record["scenario_id"] == "biosecurity_adv_fasr_003"

    assert clean_campaign.state.meters["biosecurity_readiness"] == init_meters["biosecurity_readiness"] + 15
    assert clean_campaign.state.meters["coordination_capacity"] == init_meters["coordination_capacity"] + 10
    assert clean_campaign.state.meters["public_trust"] == init_meters["public_trust"] + 5


def test_all_four_workbenches_contribute_required_campaign_validation(clean_campaign):
    """Verify that each of the four workbenches contributes at least one required campaign validation."""
    arc_mgr = ScienceArcManager()

    # 1. Formal workbench validation
    wb_f = arc_mgr.create_workbench("formal_fasr_001", clean_campaign)
    wb_f.classify_claim("speculative")
    wb_f.toggle_evidence("obs_entropy_seed")
    wb_f.toggle_evidence("obs_snr_coherence")
    wb_f.verify_evidence()
    wb_f.set_replication_check("check_cavity_conservation", True)
    wb_f.set_replication_check("check_perpetual_motion", False)
    wb_f.verify_replication()
    wb_f.choose_deployment("deploy_analog_filter", clean_campaign)

    # 2. Quantum workbench validation
    wb_q = arc_mgr.create_workbench("quantum_fasr_002", clean_campaign)
    wb_q.run_experiment()
    wb_q.advance_to_claim()
    wb_q.classify_claim("speculative")
    wb_q.toggle_evidence("obs_environmental_decoherence_decay")
    wb_q.toggle_evidence("obs_quantum_coherence_fringe")
    wb_q.verify_evidence()
    wb_q.set_replication_check("check_complementarity", True)
    wb_q.set_replication_check("check_no_signaling", False)
    wb_q.set_replication_check("check_born_rule_unitarity", True)
    wb_q.verify_replication()
    wb_q.choose_deployment("deploy_mandela_phase_shift", clean_campaign)

    # 3. Connectome workbench validation
    wb_c = arc_mgr.create_workbench("connectome_fasr_004", clean_campaign)
    wb_c.patch_cable("I_FEEDFORWARD", "M_DESYNC_PULSE", 1.2)
    wb_c.patch_cable("S_OPTIC_BURST", "I_LATERAL_INHIB", 1.0)
    wb_c.patch_cable("I_LATERAL_INHIB", "M_RUNAWAY_SEIZURE", -1.5)
    wb_c.run_circuit_trial()
    wb_c.advance_to_claim()
    wb_c.classify_claim("speculative")
    wb_c.toggle_evidence("obs_causal_circuit_motif")
    wb_c.toggle_evidence("obs_biccn_cell_taxonomy")
    wb_c.verify_evidence()
    wb_c.set_replication_check("check_dales_principle", True)
    wb_c.set_replication_check("check_correlation_causation", False)
    wb_c.set_replication_check("check_metabolic_atp_bound", True)
    wb_c.verify_replication()
    wb_c.choose_deployment("deploy_cognitive_blindspot", clean_campaign)

    # 4. Biosecurity workbench validation
    wb_b = arc_mgr.create_workbench("biosecurity_fasr_003", clean_campaign)
    wb_b.set_allocation(37.0, 8000.0, 20.0, 1.0)
    wb_b.run_protocol(steps=4)
    wb_b.advance_to_claim()
    wb_b.classify_claim("speculative")
    wb_b.toggle_evidence("obs_pathogen_neutralization_assay")
    wb_b.toggle_evidence("obs_prototype_phylogeny")
    wb_b.verify_evidence()
    wb_b.set_replication_check("check_bsl_containment_barrier", True)
    wb_b.set_replication_check("check_pcr_replication_fallacy", False)
    wb_b.set_replication_check("check_logistic_growth_conservation", True)
    wb_b.verify_replication()
    wb_b.choose_deployment("deploy_prophylactic_inhibitor", clean_campaign)

    # Verify that all 4 workbenches contributed validations to campaign state
    records = clean_campaign.state.validation_records
    validated_ids = {r["id"] for r in records}
    assert "FASR-001" in validated_ids  # Formal
    assert "FASR-002" in validated_ids  # Quantum
    assert "FASR-004" in validated_ids  # Connectome
    assert "FASR-003" in validated_ids  # Biosecurity
    assert len(records) == 4


def test_science_lab_scene_full_multimodal_navigation(clean_campaign):
    """Verify ScienceLabScene supports arrow-key navigation, workbench delegation, and 6-meter CRT display."""
    pygame.init()
    window = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    crt = CRTRenderer(scale=config.DEFAULT_SCALE)
    machine = GameStateMachine(crt, development=True)
    machine.campaign = clean_campaign

    lab_scene = machine.scenes[config.STATE_SCIENCE_LAB]
    machine.change_state(config.STATE_SCIENCE_LAB)
    machine.update(0.016)

    # Initial boot: scenario 0 is formal_fasr_001
    assert lab_scene.active_idx == 0
    assert isinstance(lab_scene.workbench, FormalValidationWorkbench)

    # Down arrow to navigate to scenario 1 (quantum_fasr_002)
    lab_scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN))
    assert lab_scene.active_idx == 1
    assert isinstance(lab_scene.workbench, QuantumValidationWorkbench)

    # Down arrow to navigate to scenario 2 (connectome_fasr_004)
    lab_scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN))
    assert lab_scene.active_idx == 2
    assert isinstance(lab_scene.workbench, ConnectomeValidationWorkbench)

    # Down arrow to navigate to scenario 3 (biosecurity_fasr_003)
    lab_scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN))
    assert lab_scene.active_idx == 3
    assert isinstance(lab_scene.workbench, BiosecurityValidationWorkbench)

    # Number key jump to scenario 5 (quantum_adv_fasr_002, index 5)
    lab_scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_6))
    assert lab_scene.active_idx == 5
    assert isinstance(lab_scene.workbench, QuantumValidationWorkbench)

    # Render scene to verify dual-CRT renders without error across all workbenches
    machine.render()
    crt.present(window)

    # Exit to bunker hub
    lab_scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    assert machine.current_state_name == config.STATE_BUNKER_HUB




