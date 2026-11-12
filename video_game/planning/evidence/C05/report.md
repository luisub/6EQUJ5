# Milestone 1 — Task C05 Evidence Report: Author Offline Contact Routes

**Date:** 2026-11-10  
**Task ID:** C05  
**Status:** Complete and Verified  
**Rollback Snapshot:** `video_game/_trash/2026-11-10_C05_before_changes.tar.gz` (SHA-256: `3e652e9579a76409e91f1a6aaac9e12e4ab78925a7b25aa83a4b526089e4b478`)  
**Manifest:** `video_game/_trash/2026-11-10_C05_before_changes_manifest.json`

---

## 1. Executive Summary

Task C05 establishes the canonical offline dialogue system, ensuring that the full narrative, readiness checks, evidence gathering, and campaign progression are 100% accessible and completable without a local language model. 

The implementation delivers:
1. **Canonical Offline Dialogue Catalog (`video_game/data/dialogue_offline.json`):** Schema version 1 defining distinct initial greetings, structured readiness branches, evidence discovery actions, advanced tactical branches with strict prerequisites, unknown-question fallbacks, and keyword maps across all 11 milestone civilizations.
2. **Offline Dialogue Engine (`video_game/engine/contact_session.py`):** Structured channel navigation (`[1]` Readiness, `[2]` Evidence, `[3]` Advanced), keyword intent routing, campaign prerequisite gating, automatic mid-stream failure recovery (switching to offline recovery without message duplication or session stranding), reconnect controls (`/reconnect`, `/offline`, `?`), and strict 12-exchange quota adherence.
3. **CRT Terminal Interface Synchronization (`video_game/engine/scenes/terminal.py`):** Dynamic mode badges (`[OFFLINE ARCHIVE]` vs `[LIVE OLLAMA]`), color-coded status line readouts, and clear channel hints.

---

## 2. Key Actions and Implementation Details

### 2.1 Canonical Offline Dialogue Catalog (`video_game/data/dialogue_offline.json`)
- Authored structured dialogue trees for all 11 milestone civilizations with rich, lore-accurate voices:
  - **`FASR-001` (Sagittarius Origin):** Transcendent energy intelligence; grants `EVIDENCE_ANALOG_ENTROPY` seed; advanced branch requires entropy seed before granting `REWARD_FIBONACCI_KEY_1`.
  - **`FASR-002` (Sgr A* Horizon):** Relativistic, gravity-dilated observer; grants `EVIDENCE_TIME_DILATION` frame-dragging metric; requires metric before granting `REWARD_HORIZON_WARP`.
  - **`FASR-003` (Tabby's Star):** Megastructure thermodynamic engineer; grants `EVIDENCE_CORE_THERMAL_WASTE` Dyson swarm profile; requires profile before conduit overrides.
  - **`FASR-004` (Orion Molecular Cloud):** Harmonic acoustic nursery; grants `EVIDENCE_IRRATIONAL_HARMONICS` waveform; requires waveform before polyphonic jamming.
  - **`FASR-005` (Proxima Centauri b):** Terminator-line machine-war survivors; grants `EVIDENCE_SOLAR_PULSE_REBOOT` protocol; requires protocol before flare capacitor arming.
  - **`FASR-006` (Crab Nebula Pulsar):** Metronomic 33.5ms neutron clock; grants `EVIDENCE_EHMAN_PRINT_ANCHOR`; requires anchor before calibrating clock drift detector.
  - **`FASR-007` (LGM-1 / CP 1919):** Sarcastic trickster; grants `EVIDENCE_FREQUENCY_HOPPING` spread spectrum code; requires code before phantom decoys.
  - **`FASR-008` (TRAPPIST-1):** Polyphonic Seven Worlds consensus; grants `EVIDENCE_DIVERSE_CONSENSUS` algorithm; requires algorithm before linking bunker mesh.
  - **`FASR-009` (1I/'Oumuamua):** Solitary interstellar wanderer; grants `EVIDENCE_HYPERBOLIC_TRAJECTORY` kinetic coordinates; requires coordinates before aligning interstellar maser.
  - **`FASR-010` (Göbekli Tepe):** Ancient terrestrial lithic resonance; grants `EVIDENCE_GROUND_WAVE_RESONANCE` telluric matrix; requires matrix before bedrock grounding.
  - **`FASR-SCAN-H` (Heptapod Anomaly):** Omnitemporal palindromic circle; grants `EVIDENCE_NON_LINEAR_SIMULTANEITY` semagram cipher; requires cipher before future memory recall.

### 2.2 Dialogue Engine & Prerequisite Enforcement (`video_game/engine/contact_session.py`)
- **Prerequisite Validation (`_check_prerequisite`):** Checks earned evidence actions in `completed_evidence_actions` and across `campaign.applied_event_ids`, `campaign.extracted_fragments`, `campaign.contacted_civs`, `campaign.room_flags`, and `campaign.inventory`. Attempting an advanced branch without its prerequisite returns an in-character refusal:
  `[PREREQUISITE UNMET: Requires <prereq>] <unmet_reply>`
  without granting the reward action or unearned progression.
- **Mid-Stream Failure Recovery:** If a live model stream encounters an error or disconnection mid-turn:
  1. Switches `is_offline = True`.
  2. Resolves the pending user message against the canonical offline dialogue.
  3. Appends `[OFFLINE RECOVERY]: <reply>` to transcript.
  4. Resets `is_streaming = False` and `active_request_id = None`.
  5. Increments exchange count by exactly 1 without duplicating user messages.
- **Connection Controls:**
  - `/reconnect`: Tests live model connectivity; restores live mode if available or retains offline mode if unavailable.
  - `/offline`: Manually switches to canonical offline mode.
  - `?` or `/choices`: Displays available numbered channels.
- **12-Turn Session Quota:** Strict enforcement across offline and live modes. Turns $\ge 12$ are rejected with `LIMIT: 12 EXCHANGES COMPLETED`.

### 2.3 Terminal UI Updates (`video_game/engine/scenes/terminal.py`)
- Display mode badge in right monitor panel title: `RIGHT CRT // [OFFLINE ARCHIVE] DIALOGUE` vs `RIGHT CRT // [LIVE OLLAMA] DIALOGUE`.
- Added color-coded mode readout in telemetry bar (`MODE: OFFLINE (CANONICAL)` in amber).
- Added channel navigation instructions to global HUD footer: `[1-3] CHANNELS  [/RECONNECT] SYNC`.

---

## 3. Visual Inspection Evidence

Inspection screenshots were generated across offline interaction states in [`video_game/planning/evidence/C05/previews/`](file:///Users/nzlab-la/Desktop/Github/6EQUJ5/video_game/planning/evidence/C05/previews/):

1. **`01_offline_terminal_channels.png`:** Offline mode initialized on FASR-001, displaying greeting and available channels (`[1] Readiness [2] Evidence [3] Tactics`).
2. **`02_offline_evidence_granted.png`:** Channel 2 selected, yielding the Analog Entropy Seed evidence text and granting `EVIDENCE_ANALOG_ENTROPY`.
3. **`03_offline_prereq_unmet_rejection.png`:** Channel 3 attempted on fresh target FASR-002; rejected with `[PREREQUISITE UNMET: Requires EVIDENCE_TIME_DILATION]`.
4. **`04_offline_trappist_consensus.png`:** Switched to FASR-008 (TRAPPIST-1), displaying distinct Seven Worlds consensus voice and readiness dialogue.
5. **`05_offline_recovery_display.png`:** Seamless offline recovery display after injected live stream disconnection.

---

## 4. Automated Test Results

1. **Contact Session & Dialogue Test Suite (`video_game/tests/test_contact_session.py`):**
   - `test_contact_session_decode_bins_match_contract`: **PASSED**
   - `test_all_eleven_targets_render_without_clipping`: **PASSED**
   - `test_long_replies_and_unicode_wrap_and_scroll`: **PASSED**
   - `test_text_input_buffer_typing_backspace_and_limits`: **PASSED**
   - `test_target_switching_and_cancellation`: **PASSED**
   - `test_twelve_completed_exchanges_limit`: **PASSED**
   - `test_rapid_exit_and_reentry_preserves_state`: **PASSED**
   - `test_receiver_tuning_and_carrier_lock`: **PASSED**
   - `test_offline_dialogue_all_eleven_civs_reachable_without_model`: **PASSED** (all 11 civs tested offline)
   - `test_offline_civ_identity_and_voice_are_distinct`: **PASSED** (11/11 distinct greetings, replies, and unknown responses)
   - `test_offline_choices_enforce_campaign_prerequisites`: **PASSED** (unmet prerequisites blocked; unlocked after requirement met)
   - `test_partial_ai_failure_recovers_to_offline_without_duplication_or_stranding`: **PASSED** (seamless mid-stream recovery)
   - `test_reconnect_controls_and_channel_help`: **PASSED** (`/reconnect`, `/offline`, `/choices`)
   - `test_offline_twelve_completed_exchanges_limit`: **PASSED** (12 turns succeed, 13th turn blocked)
   **Result:** `14 passed in 0.66s`.

2. **Combined Test Suite (`video_game/tests` and `tests`):**
   **Result:** `132 passed in 17.39s`.

3. **Checkpoint Audit Suite (`video_game/tests/test_checkpoint_audit.py`):**
   **Result:** `3 passed in 0.08s`.

4. **Asset Builder Dry-Run (`build_assets --dry-run`):**
   **Result:** All 14 locked asset groups verified and preserved.

---

## 5. Acceptance Criteria Sign-Off

- [x] **Every required evidence route is reachable without a model:** Verified across all 11 civilizations in `test_offline_dialogue_all_eleven_civs_reachable_without_model`.
- [x] **Civ identity and voice remain distinct:** Verified across all 11 civilizations in `test_offline_civ_identity_and_voice_are_distinct` (zero duplicate greetings, readiness replies, evidence replies, or unknown responses).
- [x] **Partial AI failures cannot duplicate exchanges or strand the session:** Verified in `test_partial_ai_failure_recovers_to_offline_without_duplication_or_stranding`.
- [x] **Offline choices never bypass unmet campaign prerequisites:** Verified in `test_offline_choices_enforce_campaign_prerequisites`.

