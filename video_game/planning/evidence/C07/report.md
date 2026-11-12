# Milestone 1 — Task C07 Evidence Report: Make the First Formal-Validation Workbench Playable

**Date:** 2026-11-10  
**Task ID:** C07  
**Status:** Complete and Verified  
**Rollback Snapshot:** `video_game/_trash/2026-11-10_C07_before_changes.tar.gz` (SHA-256: `36959ba6bfc9ac9625a862438ded5a1b5e7493fc3752de5040e153f0cf897fd2`)  
**Manifest:** `video_game/_trash/2026-11-10_C07_before_changes_manifest.json`

---

## 1. Executive Summary

Task C07 builds and verifies the first interactive scientific validation workbench, bridging raw signal contact and operational campaign abilities. Players can inspect extracted signal fragments, classify scientific claim tiers with explanatory feedback, isolate empirical signatures from counterexamples, test physical replication invariants, and commit risk-managed protocol deployment decisions to the campaign.

Key deliveries:
1. **Laboratory Scenario Catalog (`video_game/data/lab_scenarios.json`):** Authored schema version 1 scenario `formal_fasr_001` with educational domain metadata (*Information Thermodynamics & Statistical Mechanics*), primary literature citations (Landauer 1961, Bennett 1982, Ehman 1977), claim tier options, empirical evidence pool with counterexamples, replication invariants, and two distinct deployment choices.
2. **Formal Validation Workbench Engine (`video_game/engine/labs/formal.py`):** Implemented `FormalValidationWorkbench` coordinating the 5-stage validation pipeline (`CLAIM` $\to$ `EVIDENCE` $\to$ `REPLICATION` $\to$ `DEPLOYMENT` $\to$ `COMPLETED`), enforcing fragment prerequisites, generating versioned validation records, and applying atomic rewards via campaign grant events.
3. **Interactive Science Lab Scene (`video_game/engine/scenes/lab.py`):** Replaced the placeholder scene with an interactive dual-CRT workbench scene wired to `config.STATE_SCIENCE_LAB` in `GameStateMachine`. Left CRT displays validation stations, citations, and pipeline progress; Right CRT renders interactive step cards, option lists, toggleable evidence, and real-time color-coded feedback.
4. **Campaign Events Registration (`video_game/data/campaign.json`):** Registered `formal_fasr_001` in `validation_scenarios` and added `validate_fasr_001_deploy` and `validate_fasr_001_withhold` grant events.
5. **Campaign Persistence & Idempotence:** Confirmed that completed validation records and deployment choices persist across atomic disk save/reload cycles without reward duplication.

---

## 2. Formal Validation Pipeline & Game Mechanics

### 2.1 Fragment Prerequisite Gate
A workbench scenario cannot be initiated until the operator has extracted the associated civilization signal fragment (`FASR-001` in `campaign.state.extracted_fragments`). Attempting to engage the scenario without the fragment returns `PREREQUISITE MISSING: Requires extracted fragment 'FASR-001'`.

### 2.2 Claim Classification & Explanatory Feedback
The operator must classify the fragment claim into one of three tiers:
- **`ESTABLISHED` (Standard Classical Physics):** Incorrect. Explanatory feedback informs the operator that direct reduction of macroscopic entropy without work expenditure violates the Second Law of Thermodynamics (Carnot / Landauer bounds). The workbench retains the step and permits immediate retry.
- **`PLAUSIBLE` (Direct Extrapolation):** Incorrect. Explanatory feedback informs the operator that plausible claims require demonstrable physical coupling mechanisms without historical precedent in macro-scale entropy reduction.
- **`SPECULATIVE` (Advanced Non-Standard Theory):** Correct. Validated as an advanced theoretical or extraterrestrial physics concept requiring isolation and replication safeguards before operational deployment.

### 2.3 Distinction: Speculative Claim Tier vs Hostile Intent
Per acceptance criteria and `DATA_CONTRACTS.md`, the workbench maintains a strict ontological boundary:
- `claim["correct_tier"] == "speculative"`
- `claim["trustworthiness"] == "trusted_origin"`
- `claim["is_hostile"] == False`

A speculative claim tier describes an unverified or advanced physical theory, and is **never** conflated with hostile deception or a Core-mimic attack.

### 2.4 Evidence vs Counterexample Filtering
The operator must review the observation pool and select only empirical signatures corresponding to the genuine signal:
- **`obs_entropy_seed`:** Valid analog entropy modulation at 1420.4056 MHz.
- **`obs_snr_coherence`:** Valid 30-sigma Gaussian envelope tracking the 72-second transit duration.
- **`obs_terrestrial_rfi`:** Counterexample representing terrestrial spark-gap interference. Selecting this counterexample triggers immediate explanatory rejection feedback: `COUNTEREXAMPLE DETECTED: Terrestrial spark-gap RFI is broadband and non-coherent, not monochromatic 1420.4056 MHz carrier.`

### 2.5 Replication Invariant Checks
The operator must verify physical conservation laws on laboratory replication apparatus:
- **`check_cavity_conservation` (Expected: True):** Confirms that information erasure produces finite dissipative heat $\ge kT \ln(2)$ per Landauer's principle.
- **`check_perpetual_motion` (Expected: False):** Rejects perpetual motion counterexamples; verifies that closed-system enthalpy remains conserved.

### 2.6 Deployment Decision & Campaign Event Application
Upon satisfying replication checks, the operator selects between two risk-managed deployment decisions:
1. **`deploy_analog_filter` (Operational Waveguide Deployment):**
   - Applies event `validate_fasr_001_deploy`.
   - Meter deltas: `scientific_certainty +10`, `alignment_confidence +5`, `human_agency +5`.
   - Arms the sub-basement maser with an analog entropy filter for Act I combat encounters.
2. **`withhold_quarantine` (Faraday Safe Harbor):**
   - Applies event `validate_fasr_001_withhold`.
   - Meter deltas: `scientific_certainty +10`, `public_trust +5`, `biosecurity_readiness +5`.
   - Secures protocol in bunker Faraday vault pending multi-site replication.

---

## 3. Visual Inspection Evidence

Inspection screenshots were captured under [`video_game/planning/evidence/C07/previews/`](file:///Users/nzlab-la/Desktop/Github/6EQUJ5/video_game/planning/evidence/C07/previews/):

1. **`01_lab_bench_claim_tier_options.png`:** Left CRT shows scenario status and literature citations (Landauer 1961, Bennett 1982, Ehman 1977); Right CRT displays the proposition statement and options `[1] Established`, `[2] Plausible`, `[3] Speculative`.
2. **`02_claim_classification_error_feedback.png`:** Player selected `[1] Established`; red/amber feedback message explains Carnot/Landauer Second Law violation.
3. **`03_evidence_selection_and_counterexample_feedback.png`:** Player toggled counterexample (`obs_terrestrial_rfi`); feedback identifies broadband terrestrial spark-gap RFI.
4. **`04_replication_checks_and_deployment_options.png`:** Replication verified; Right CRT displays choices `[1] Deploy Maser Waveguide Filter` vs `[2] Quarantine in Faraday Vault` with meter impacts.
5. **`05_protocol_validated_campaign_committed.png`:** Protocol committed; displays versioned validation record and status `REWARDS COMMITTED TO CAMPAIGN STATE`.

---

## 4. Automated Test Results

1. **Laboratory & Validation Workbench Test Suite (`video_game/tests/test_labs.py`):**
   - `test_lab_scenarios_schema_and_integrity`: **PASSED**
   - `test_formal_workbench_prerequisite_enforcement`: **PASSED**
   - `test_claim_tier_classification_and_explanatory_feedback`: **PASSED**
   - `test_speculative_tier_distinct_from_hostile_intent`: **PASSED**
   - `test_evidence_observation_and_counterexample_filtering`: **PASSED**
   - `test_replication_invariant_checks`: **PASSED**
   - `test_deployment_choice_deploy_analog_filter`: **PASSED**
   - `test_deployment_choice_withhold_quarantine`: **PASSED**
   - `test_idempotent_validation_and_no_duplicate_rewards`: **PASSED**
   - `test_save_reload_preserves_validation_record_and_decision`: **PASSED**
   - `test_science_lab_scene_rendering_and_interaction`: **PASSED**
   **Result:** `11 passed in 0.25s`.

2. **Combined Test Suite (`video_game/tests` and `tests`):**
   **Result:** `149 passed in 15.64s`.

3. **Checkpoint Audit Suite (`video_game/tests/test_checkpoint_audit.py`):**
   - `test_active_modules_have_valid_syntax_headers_and_explicit_imports`: **PASSED**
   - `test_new_scene_needs_no_registry_or_line_budget`: **PASSED**
   - `test_art_milestone_1_asset_dimensions_and_locks`: **PASSED**
   **Result:** `3 passed in 0.11s`.

4. **Asset Builder Dry-Run (`build_assets --dry-run`):**
   **Result:** All 14 locked asset groups verified and preserved.

---

## 5. Acceptance Criteria Sign-Off

- [x] **A fragment becomes a validated protocol through normal player interaction:** Verified in `test_deployment_choice_deploy_analog_filter`, `test_deployment_choice_withhold_quarantine`, and `test_science_lab_scene_rendering_and_interaction`.
- [x] **Incorrect answers can be corrected with explanatory feedback:** Verified in `test_claim_tier_classification_and_explanatory_feedback`, `test_evidence_observation_and_counterexample_filtering`, and `test_replication_invariant_checks`.
- [x] **Speculative claim tier and hostile intent remain distinct:** Verified in `test_speculative_tier_distinct_from_hostile_intent`.
- [x] **Reload preserves the result and deployment decision:** Verified in `test_save_reload_preserves_validation_record_and_decision`.

