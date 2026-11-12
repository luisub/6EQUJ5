# Milestone 1 — Task C08 Evidence Report: Verify the Contact-to-Validation Loop & Gate G1

**Date:** 2026-11-10  
**Task ID:** C08  
**Status:** Complete and Verified (Gate G1 Signed Off)  
**Rollback Snapshot:** `video_game/_trash/2026-11-10_C08_before_changes.tar.gz` (SHA-256: `9bfa1a5d52135e704b2f6d35161a27570de2e223692ec7f417899bc4f9f1030c`)  
**Manifest:** `video_game/_trash/2026-11-10_C08_before_changes_manifest.json`

---

## 1. Executive Summary & Gate G1 Promotion

Task C08 performs the end-to-end verification of Milestone 1 (**The First Contact Loop**), formally promoting **Gate G1**.

The complete gameplay sequence from initial radio reception, carrier tuning, multi-channel dialogue interrogation, fragment extraction, formal scientific workbench puzzle validation, replication checking, protocol deployment choice, and atomic disk persistence has been exercised on a completely clean, unseeded campaign state and verified across both automated regression test suites and visual inspection captures.

In addition, parity between canonical offline dialogue trees and real live local LLM streaming via Ollama (`qwen3:8b`) was measured and validated under real operational conditions on the local host.

---

## 2. Full Contact-to-Validation Route Verification

### 2.1 Route Trajectory
1. **Fresh Campaign Initialization:**
   - Starts with `Campaign()`: zero contacted civs, zero fragments, zero validation records, baseline starter equipment (`maser_1420`).
2. **CRT Receiver Tuning & Carrier Acquisition:**
   - Operator tunes the Big Ear receiver to $1420.4056\text{ MHz}$ ($\pm 0.0800\text{ MHz}$ lock tolerance).
   - Receiver locks carrier, registers target `FASR-001`, and initializes the dialogue session.
3. **Dialogue Interrogation & Evidence Gathering:**
   - Operator executes channel `[1]` (Readiness) $\to$ Registers contact in `campaign.state.contacted_civs`.
   - Operator executes channel `[2]` (Evidence) $\to$ Acquires `EVIDENCE_ANALOG_ENTROPY`.
   - `ContactSession.claim_evidence_grant()` submits authenticated `EvidenceTrace`.
   - Atomic grant event `grant_fragment_fasr_001` commits `FASR-001` to `campaign.state.extracted_fragments`.
4. **Formal Science Workbench Engagement:**
   - Operator enters the Science Lab station (`STATE_SCIENCE_LAB`).
   - Workbench validates that `FASR-001` fragment prerequisite is satisfied.
   - **Step 1 (Claim Classification):** Operator classifies proposition as `speculative`. Explanatory feedback is verified if wrong options (`established` or `plausible`) are attempted.
   - **Step 2 (Evidence Filtering):** Operator selects empirical signatures (`obs_entropy_seed`, `obs_snr_coherence`) and rejects terrestrial RFI counterexamples.
   - **Step 3 (Replication Checks):** Operator verifies closed cavity conservation ($\ge kT \ln 2$) and rejects perpetual motion.
   - **Step 4 (Deployment Decision):** Operator selects `deploy_analog_filter` (arming the bunker waveguide maser).
   - Validation event `validate_fasr_001_deploy` is atomically applied: awards $+10$ Scientific Certainty, $+5$ Alignment Confidence, $+5$ Human Agency, and commits the versioned validation record to `campaign.state.validation_records`.
5. **Disk Persistence & State Reload:**
   - Campaign saved to disk using `SaveStore`.
   - Campaign reloaded from disk; verified bit-for-bit retention of fragment, validation record, and updated meter levels.

---

## 3. Live Inference vs Offline Parity

### 3.1 Live Local Model Performance (`qwen3:8b` via Ollama)
Live local inference was tested in `test_gate_g1_live_local_model_and_offline_route_parity` on the local host:
- **Service Endpoint:** `http://localhost:11434`
- **Model Identity:** `qwen3:8b` (8.2B parameter, Q4_K_M GGUF format)
- **Time to First Token (TTFT):** $0.14\text{ seconds}$
- **Total Duration:** $3.44\text{ seconds}$
- **Total Tokens Received:** $92\text{ tokens}$
- **Generation Throughput:** $26.7\text{ tokens/second}$
- **Main Thread Impact:** Completely non-blocking; UI frame rendering maintained at $60\text{ FPS}$ with $< 2\text{ ms}$ processing cost per frame.

### 3.2 Canonical Offline Dialogue Parity
- **100% Offline Reachability:** All 11 civilization routes fully playable and completable with zero external services or network connectivity.
- **Prerequisite Parity:** Unmet prerequisites consistently block unearned progress in both live and offline modes.
- **Mid-Stream Recovery:** Disconnection or model errors mid-turn automatically fall back to offline dialogue trees without duplicate user messages or session stranding.

---

## 4. Visual Inspection Evidence

Inspection screenshots were generated across the entire loop under [`video_game/planning/evidence/C08/previews/`](file:///Users/nzlab-la/Desktop/Github/6EQUJ5/video_game/planning/evidence/C08/previews/):

1. **`01_fresh_game_bunker_to_receiver.png`:** Fresh game initialized in bunker hub, preparing transition to CRT receiver terminal.
2. **`02_terminal_carrier_locked_fasr_001.png`:** Receiver locked on $1420.4056\text{ MHz}$, displaying 6EQUJ5 intensity histogram and greeting.
3. **`03_evidence_extracted_grant_committed.png`:** Channel 2 evidence interrogation executed; `FASR-001` fragment extracted and registered in campaign state.
4. **`04_science_lab_formal_validation.png`:** Science Lab workbench evaluating physical replication invariants for `formal_fasr_001`.
5. **`05_deployment_committed_and_reloaded.png`:** Protocol deployment committed to waveguide maser; campaign saved and reloaded from disk with valid record preserved.

---

## 5. Automated Test Results

1. **Contact Session & Gate G1 Suite (`video_game/tests/test_contact_session.py`):**
   - `test_contact_session_decode_bins_match_contract`: **PASSED**
   - `test_all_eleven_targets_render_without_clipping`: **PASSED**
   - `test_long_replies_and_unicode_wrap_and_scroll`: **PASSED**
   - `test_text_input_buffer_typing_backspace_and_limits`: **PASSED**
   - `test_target_switching_and_cancellation`: **PASSED**
   - `test_twelve_completed_exchanges_limit`: **PASSED**
   - `test_rapid_exit_and_reentry_preserves_state`: **PASSED**
   - `test_receiver_tuning_and_carrier_lock`: **PASSED**
   - `test_offline_dialogue_all_eleven_civs_reachable_without_model`: **PASSED**
   - `test_offline_civ_identity_and_voice_are_distinct`: **PASSED**
   - `test_offline_choices_enforce_campaign_prerequisites`: **PASSED**
   - `test_partial_ai_failure_recovers_to_offline_without_duplication_or_stranding`: **PASSED**
   - `test_reconnect_controls_and_channel_help`: **PASSED**
   - `test_offline_twelve_completed_exchanges_limit`: **PASSED**
   - `test_hostile_signal_core_mimic_detection`: **PASSED**
   - `test_hostile_signal_consequence_and_recovery`: **PASSED**
   - `test_claim_evidence_grant_integration`: **PASSED**
   - `test_gate_g1_fresh_game_end_to_end_contact_to_validation_route`: **PASSED**
   - `test_gate_g1_live_local_model_and_offline_route_parity`: **PASSED**
   **Result:** `19 passed in 3.56s`.

2. **Laboratory & Formal Workbench Suite (`video_game/tests/test_labs.py`):**
   - `11 passed in 0.24s`.

3. **Combined Test Suite (`video_game/tests` and `tests`):**
   - **Result:** `151 passed in 14.64s`.

4. **Checkpoint Audit Suite (`video_game/tests/test_checkpoint_audit.py`):**
   - **Result:** `3 passed in 0.11s`.

5. **Asset Builder Dry-Run (`build_assets --dry-run`):**
   - **Result:** All 14 locked asset groups verified and preserved.

---

## 6. Acceptance Criteria Sign-Off

- [x] **Gate G1 passes with linked route evidence:** Fully verified across `test_gate_g1_fresh_game_end_to_end_contact_to_validation_route`, `test_gate_g1_live_local_model_and_offline_route_parity`, and inspection previews.
- [x] **The loop uses normal UI and persistent campaign state:** Demonstrated through receiver terminal, science lab workbench scene, and atomic disk save/reload cycles.
- [x] **Required live-inference checks have actual results:** Measured live local inference on `qwen3:8b` (TTFT 0.14s, duration 3.44s, throughput 26.7 tok/s).

