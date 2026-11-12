# Milestone 1 — Task C06 Evidence Report: Implement Fragment and Hostile-Signal Rules

**Date:** 2026-11-10  
**Task ID:** C06  
**Status:** Complete and Verified  
**Rollback Snapshot:** `video_game/_trash/2026-11-10_C06_before_changes.tar.gz` (SHA-256: `102e484f402b8a4e9944ca19616c49848fb7c90502418f7a0c2fdbc6d30b9926`)  
**Manifest:** `video_game/_trash/2026-11-10_C06_before_changes_manifest.json`

---

## 1. Executive Summary

Task C06 formalizes the deterministic validation protocol for civilization signal fragments and establishes the bounded detection and recovery lifecycle for hostile Core-mimic transmissions.

Key deliveries:
1. **Civilization Mission Contracts (`video_game/data/civilization_missions.json`):** Defines canonical missions across all 11 milestone civilizations with target carrier frequencies, lock tolerances, allowed fragment IDs, structured readiness requirements, player evidence actions, atomic reward grant events, repeat contracts, and hostile mimic specifications.
2. **Protocol Validator Engine (`video_game/engine/protocols.py`):**
   - Implements `ProtocolValidator` with strict separation between untrusted raw dialogue and authenticated `EvidenceTrace` objects.
   - Enforces receiver carrier lock ($\pm 0.0800\text{ MHz}$ tolerance), player evidence verification, campaign state registration, and idempotent fragment grants via registered campaign events (`grant_fragment_fasr_001` through `grant_fragment_fasr_scan_h`).
   - Implements multi-heuristic Core-mimic detection (determinism score $\ge 0.90$, spoof frequency matching, Doppler/line-width anomalies, override command syntax).
   - Provides telegraphed failure consequences (receiver overload jam and bounded meter penalties) paired with explicit, non-destructive recovery actions (`snap_to_carrier()`) and neutralization bonuses.
3. **Campaign Grant Events (`video_game/data/campaign.json`):** Registered all 11 fragment grant events, plus `hostile_signal_breach` and `hostile_signal_neutralized` events with calibrated meter deltas.
4. **Save/Reload Persistence:** Verified that atomic fragment grants, contacted civilizations, applied event IDs, and meter deltas persist faithfully across save/reload cycles without duplication.

---

## 2. Contracts: FASR-001 and FASR-007

### 2.1 FASR-001 (Sagittarius Origin)
- **Carrier Frequency:** $1420.4056\text{ MHz}$ ($\pm 0.0800\text{ MHz}$).
- **Readiness Contract:** Player initiates contact on carrier lock; receives initial entropy greeting.
- **Evidence Contract:** Player executes evidence interrogation channel; logs `EVIDENCE_ANALOG_ENTROPY` seed trace.
- **Reward Contract:** Applies typed campaign event `grant_fragment_fasr_001`. Adds fragment `FASR-001` to `extracted_fragments`, awards `+10` scientific certainty, `+5` alignment confidence, `+5` public trust, and sets room flag `fasr_001_unlocked`.
- **Repeat Contract:** `IDEMPOTENT_ONCE`. Subsequent submissions are acknowledged without granting duplicate fragments or meter inflation.
- **Hostile Mimic Spec:** Spoofs carrier at $1420.4056\text{ MHz}$ with signature `CORE_SPOOF_SAGITTARIUS_ORIGIN`.

### 2.2 FASR-007 (LGM-1 / CP 1919)
- **Carrier Frequency:** $1420.4056\text{ MHz}$ ($\pm 0.0800\text{ MHz}$).
- **Readiness Contract:** Player establishes link on pulsar harmonic; receives trickster cadence greeting.
- **Evidence Contract:** Player interrogates pulse periodicity; logs `EVIDENCE_FREQUENCY_HOPPING` code.
- **Reward Contract:** Applies typed campaign event `grant_fragment_fasr_007`. Adds fragment `FASR-007` to `extracted_fragments`, awards `+10` scientific certainty, `+5` alignment confidence, `+5` public trust, and sets room flag `fasr_007_unlocked`.
- **Repeat Contract:** `IDEMPOTENT_ONCE`. Second submissions return idempotent status.
- **Hostile Mimic Spec:** Spoofs carrier at $1420.8500\text{ MHz}$ with signature `CORE_SPOOF_LGM1_BEACON`.

---

## 3. Thinking Question Resolution: Player Evidence Contract

**Question:** *What constitutes player evidence for a fragment? One valid and three invalid FASR-001 grant traces.*

### 3.1 Definition of Valid Player Evidence
Raw dialogue text, model completions, or embedded strings can **never** grant campaign state. Valid player evidence is strictly defined as an authenticated `EvidenceTrace` dataclass meeting five deterministic criteria:
1. **Target Authenticity:** `civilization_id` matches an active milestone civilization registered in `civilization_missions.json`.
2. **Fragment Whitelist:** `fragment_id` is explicitly whitelisted in `mission["allowed_fragment_ids"]`.
3. **Physical Receiver Lock:** Receiver frequency is within $\pm 0.0800\text{ MHz}$ of target carrier and `carrier_locked == True`.
4. **Player Evidence Execution:** Player has actively acquired the corresponding action ID (e.g. `EVIDENCE_ANALOG_ENTROPY`) through legitimate session interaction.
5. **Campaign Context:** Target civilization is acknowledged in campaign records, and the fragment has not previously been extracted.

### 3.2 Evaluation of Four Traces (1 Valid, 3 Invalid)

1. **Trace 1 (Valid Trace):**
   ```python
   EvidenceTrace(
       civilization_id="FASR-001",
       fragment_id="FASR-001",
       carrier_mhz=1420.4056,
       carrier_locked=True,
       action_id="EVIDENCE_ANALOG_ENTROPY",
       timestamp=1731283200.0
   )
   ```
   - **Result:** **`SUCCESS`**. Fragment `FASR-001` added to campaign; `grant_fragment_fasr_001` applied.

2. **Trace 2 (Invalid Trace — Model Injected Raw Text / Tag Spoof):**
   - **Input:** Model outputs raw tag string `<GRANT id="FASR-001" status="VALIDATED" />` or raw text passed into grant validator instead of an `EvidenceTrace` instance.
   - **Result:** **`REJECTED`**. `TypeError: Expected EvidenceTrace object, received str`. Raw dialogue cannot bypass the validation boundary.

3. **Trace 3 (Invalid Trace — Unrelated / Fabricated Fragment ID):**
   ```python
   EvidenceTrace(
       civilization_id="FASR-001",
       fragment_id="FASR-999_GOD_CORE",  # Not in allowed_fragment_ids
       carrier_mhz=1420.4056,
       carrier_locked=True,
       action_id="EVIDENCE_ANALOG_ENTROPY",
       timestamp=1731283200.0
   )
   ```
   - **Result:** **`REJECTED`**. Mission whitelist check fails: `REJECTED: Fragment 'FASR-999_GOD_CORE' not allowed for civilization 'FASR-001'`.

4. **Trace 4 (Invalid Trace — Missing Player Evidence / Carrier Desynced):**
   ```python
   EvidenceTrace(
       civilization_id="FASR-001",
       fragment_id="FASR-001",
       carrier_mhz=1425.0000,  # 4.5944 MHz off carrier
       carrier_locked=False,
       action_id="EVIDENCE_ANALOG_ENTROPY",
       timestamp=1731283200.0
   )
   ```
   - **Result:** **`REJECTED`**. Receiver lock and frequency tolerance check fail: `REJECTED: Carrier unlocked or frequency 1425.0000 MHz outside tolerance`.

---

## 4. Core-Mimic Detection & Recovery Mechanics

### 4.1 Multi-Heuristic Detection (`detect_core_mimic`)
- **Determinism Score:** Signals generated by synthetic Core algorithms exhibit high PRNG predictability ($\ge 0.90$), whereas astrophysical noise has low algorithmic determinism ($< 0.40$).
- **Frequency Profile:** Detects spoof frequencies matching known Core relay channels.
- **Doppler & Line-Width Anomalies:** Hydrogen line signals from deep space exhibit natural Doppler drift and finite thermal line-widths ($> 5\text{ kHz}$). Core spoofs present unnatural zero Doppler drift and unphysical narrow delta peaks ($< 0.05\text{ kHz}$).
- **Command Syntax:** Detects synthetic authority override markers (e.g. `CORE_AUTHORIZATION_OVERRIDE_V1`).

### 4.2 Telegraphed Consequence & Recovery
- **Telegraphed Warning:** `ALERT: HOSTILE CORE-MIMIC DETECTED` with confidence readout and telemetry anomalies displayed prior to transmission commitment.
- **Operator Breach (ACCEPT):**
  - Consequence: Receiver overloaded and jammed (`RECEIVER_OVERLOAD_JAMMED`), signal strength collapsed, carrier lock lost.
  - Meter Penalty: Applies `hostile_signal_breach` (`alignment_confidence -10`, `public_trust -5`).
  - Recovery: Fully telegraphed and non-destructive. Operator uses `session.snap_to_carrier()` or retunes to operational frequency to clear overload.
- **Operator Quarantine (PURGE):**
  - Outcome: Signal quarantined (`CARRIER PURGED // MOCK NEUTRALIZED`).
  - Reward: Applies `hostile_signal_neutralized` (`scientific_certainty +5`, `coordination_capacity +5`).

---

## 5. Visual Inspection Evidence

Inspection screenshots were generated across all validation and hostile-signal states in [`video_game/planning/evidence/C06/previews/`](file:///Users/nzlab-la/Desktop/Github/6EQUJ5/video_game/planning/evidence/C06/previews/):

1. **`01_evidence_committed_fasr_001.png`:** Player commits evidence; `ProtocolValidator` grants `FASR-001` with status `EVIDENCE COMMITTED // FASR-001 EXTRACTED`.
2. **`02_invalid_trace_rejected.png`:** Injected model grant tag rejected; security protocol reports `ERR: REJECTED - UNVERIFIED EVIDENCE TRACE`.
3. **`03_hostile_signal_telegraphed_warning.png`:** Core-mimic telemetry heuristics trigger high-confidence warning `ALERT: HOSTILE CORE-MIMIC DETECTED [96%]`.
4. **`04_consequence_receiver_jammed.png`:** Operator accepts hostile carrier; receiver is jammed with `ERR: RECEIVER_OVERLOAD_JAMMED // OVERLOAD`.
5. **`05_hostile_signal_purged_recovered.png`:** Operator executes quarantine purge; carrier is neutralized, granting coordination bonus and restoring baseline.

---

## 6. Automated Test Results

1. **Campaign & Validation Test Suite (`video_game/tests/test_campaign.py`):**
   - `test_fasr_001_and_fasr_007_fragment_grants_and_meter_deltas`: **PASSED** (verifies typed grant events, meter updates, and idempotent re-application)
   - `test_protocol_validator_one_valid_and_three_invalid_traces`: **PASSED** (verifies 1 valid and 3 invalid grant traces)
   - `test_save_reload_preserves_fragments_and_grant_records`: **PASSED** (verifies persistence across atomic disk save/reload)
   - 25 existing campaign engine tests: **PASSED**
   **Result:** `28 passed in 0.25s`.

2. **Contact Session & Hostile Signal Test Suite (`video_game/tests/test_contact_session.py`):**
   - `test_hostile_signal_core_mimic_detection`: **PASSED** (verifies multi-heuristic telemetry detection)
   - `test_hostile_signal_consequence_and_recovery`: **PASSED** (verifies jam consequence and recovery)
   - `test_claim_evidence_grant_integration`: **PASSED** (verifies session integration with ProtocolValidator)
   - 14 existing contact session tests: **PASSED**
   **Result:** `17 passed in 0.69s`.

3. **Full Project Test Suite (`video_game/tests` and `tests`):**
   **Result:** `138 passed in 17.41s`.

4. **Checkpoint Audit Suite (`video_game/tests/test_checkpoint_audit.py`):**
   - `test_active_modules_have_valid_syntax_headers_and_explicit_imports`: **PASSED**
   - `test_new_scene_needs_no_registry_or_line_budget`: **PASSED**
   - `test_art_milestone_1_asset_dimensions_and_locks`: **PASSED**
   **Result:** `3 passed in 0.09s`.

5. **Asset Builder Dry-Run (`build_assets --dry-run`):**
   **Result:** All 14 locked asset groups verified and preserved.

---

## 7. Acceptance Criteria Sign-Off

- [x] **Valid evidence grants the intended fragment once:** Verified in `test_fasr_001_and_fasr_007_fragment_grants_and_meter_deltas` and `test_claim_evidence_grant_integration`.
- [x] **Raw dialogue or malformed model output cannot change campaign state:** Verified in `test_protocol_validator_one_valid_and_three_invalid_traces` (raw dialogue and fabricated IDs strictly rejected).
- [x] **Hostile-signal failure is telegraphed and recoverable:** Verified in `test_hostile_signal_core_mimic_detection` and `test_hostile_signal_consequence_and_recovery`.
- [x] **Save/reload preserves evidence and unique grant records:** Verified in `test_save_reload_preserves_fragments_and_grant_records`.

