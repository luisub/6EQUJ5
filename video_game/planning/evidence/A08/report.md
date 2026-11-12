# Milestone 2 — Task A08 Evidence Report: Implement the 72-Second Dish Defense

**Date:** 2026-11-11  
**Task ID:** A08  
**Milestone:** 02_action_slice (Milestone 2: Complete Playable Act I)  
**Status:** Complete and Verified  
**Rollback Snapshot:** `video_game/_trash/2026-11-11_A08_before_changes.tar.gz` (SHA-256: `0a8ac575772172c4a9814927f8e7900ccc1a707a46afcb5184074447068c215a`)  
**Manifest:** `video_game/_trash/2026-11-11_A08_before_changes_manifest.json`  

---

## 1. Executive Summary

Task A08 implements the culminating set-piece encounter of Act I: the **72-second Big Ear Dish Defense holdout**. The player climbs the exterior dish superstructure to defend the central feedhorn array while the Big Ear telescope acquires the complete historical Wow! signal envelope across six 12-second observation windows.

Key subsystems delivered and verified:
1. **72-Second Dish Defense State Machine (`DishDefenseHoldout`):**
   - Implemented in `video_game/engine/objectives.py`.
   - Four distinct lifecycle states: `IDLE`, `ACTIVE`, `FAILED`, `COMPLETED`.
   - Exact simulation time accumulation: tracks active non-paused gameplay time to precisely 72.0 seconds (`step_size = 0.2s`).
   - Pause time-freezing: simulation dt is only applied when `paused=False`, preventing pause-menu exploits.
2. **Six 12-Second Signal Observation Bins (`6EQUJ5` Envelope):**
   - Matches the true 1977 Big Ear telescope feedhorn sensitivity profile:
     - Bin 0 ($t \in [0.0, 12.0)$): Code `'6'` (SNR 6$\sigma$, acquisition start)
     - Bin 1 ($t \in [12.0, 24.0)$): Code `'E'` (SNR 14$\sigma$, signal amplification)
     - Bin 2 ($t \in [24.0, 36.0)$): Code `'Q'` (SNR 26$\sigma$, beam peak ingress)
     - Bin 3 ($t \in [36.0, 48.0)$): Code `'U'` (SNR 30$\sigma$, absolute transmission peak)
     - Bin 4 ($t \in [48.0, 60.0)$): Code `'J'` (SNR 19$\sigma$, beam egress decay)
     - Bin 5 ($t \in [60.0, 72.0)$): Code `'5'` (SNR 5$\sigma$, signal extinction)
3. **Assault Waves and Jammed Feedhorn Counterplay:**
   - 3 scheduled enemy waves configured from data:
     - Wave 1 ($t = 0.0s$): Scout assault (`CoreReconDrone` × 2)
     - Wave 2 ($t = 24.0s$): Electronic warfare jammer + `StaticHound` ground hounds. Automatically engages feedhorn jamming, causing continuous dish integrity decay ($-1.0$ HP/s).
     - Wave 3 ($t = 48.0s$): Combined air and perimeter assault.
   - Counterplay: Player must navigate to the feedhorn mast ($x = 296$) and activate `unjam()`, arresting decay and restoring telemetry.
4. **Dish Integrity, Failure, and Checkpoint Recovery:**
   - Dish integrity starts at $100.0\%$. Reaching $0.0\%$ triggers `FAILED` state.
   - Retry resets wave schedules, purges active enemies, resets holdout state to `IDLE`, and respawns the player at the catwalk ladder checkpoint (`catwalk_start`).
5. **Level Geometry (`act_01/dish_catwalk.json`):**
   - 40×18 tile map ($640 \times 288$ px) featuring upper catwalks with one-way grating tiles, mid-level support trusses, low sandbag cover emplacements, and the central feedhorn array mast.
   - Validated cleanly against schema and campaign registry via `Room.validate()`.
6. **Atomic Campaign Progression & Idempotent Rewards:**
   - On completion at $t \ge 72.0s$, `complete_dish_defense` event awards $+10$ Scientific Certainty, $+5$ Alignment Confidence, and $+5$ Human Agency.
   - Sets flag `dish_defense_completed = True`. Re-running `apply_completion_reward()` returns `False` and guarantees zero duplicate reward grants.

---

## 2. Acceptance Checks Verification

### Check 1: Completion occurs at exactly 72 seconds of accumulated active game time within one simulation step
- **Test:** `test_dish_defense_completion_at_exactly_72_seconds_within_one_step` in `video_game/tests/test_objectives.py`.
- **Result: PASSED.**
  - At $t = 71.8s$, the holdout remains in `ACTIVE` state with 0.2s remaining.
  - A single simulation step of $\Delta t = 0.2s$ advances elapsed time to $72.0s$, transitioning state to `COMPLETED` within that exact step.
  - Calling `update()` while `is_paused = True` does not advance elapsed time ($t$ remains locked at $20.0s$), verifying that pause strictly freezes holdout accumulation.

### Check 2: Signal display follows the rising and falling six-bin sequence
- **Test:** `test_holdout_signal_display_follows_six_bin_curve` in `video_game/tests/test_objectives.py`.
- **Result: PASSED.**
  - Evaluated `get_signal_display()` across all 6 time intervals ($t \in \{6.0, 18.0, 30.0, 42.0, 54.0, 66.0\}$).
  - Telemetry output verified:
    - Bin 0: Code `'6'`, SNR 6
    - Bin 1: Code `'E'`, SNR 14
    - Bin 2: Code `'Q'`, SNR 26
    - Bin 3: Code `'U'`, SNR 30 (Peak)
    - Bin 4: Code `'J'`, SNR 19
    - Bin 5: Code `'5'`, SNR 5
  - Confirmed SNR monotonic rise from Bin 0 to Bin 3 ($6 \to 14 \to 26 \to 30$), followed by monotonic fall from Bin 3 to Bin 5 ($30 \to 19 \to 5$).

### Check 3: Failure/retry clears wave state and restores valid geometry
- **Test:** `test_holdout_failure_and_retry_restores_clean_geometry` in `video_game/tests/test_objectives.py`.
- **Result: PASSED.**
  - Inflicted 100 direct damage to dish integrity, triggering state transition from `ACTIVE` to `FAILED`.
  - While failed, holdout updates are frozen.
  - Invoking `retry(player_spawn_pos=(48.0, 208.0))` resets state to `IDLE`, clears active and completed wave sets, restores dish integrity to $100.0\%$, clears feedhorn jamming flags, and repositions the player at the valid starting spawn.
  - Re-starting holdout initiates fresh wave sequencing from $t = 0.0s$.

### Check 4: Completion reward applies once
- **Test:** `test_dish_defense_completion_reward_applies_exactly_once` in `video_game/tests/test_objectives.py`.
- **Result: PASSED.**
  - Advanced holdout through completion at $72.0s$.
  - First call to `apply_completion_reward(campaign)` returned `True`, awarded $+10$ Certainty, $+5$ Alignment, $+5$ Agency, and marked `dish_defense_completed = True`.
  - Immediate subsequent call returned `False` with zero change to campaign meters.
  - Saved campaign to disk and reloaded; calling `apply_completion_reward()` again on loaded state returned `False`, confirming atomic persistence and zero replay duplication.

---

## 3. Visual Previews & Evidence Artifacts

The following visual evidence files were generated in `video_game/planning/evidence/A08/previews/`:

1. `01_72s_wow_signal_bins_telemetry.png`:
   - Visual readout displaying the six 12-second observation windows ($72.0s$ total) with historical SNR curve ($6 \to E \to Q \to U \to J \to 5$), bar graphs, carrier frequency ($1420.4056\text{ MHz}$), and bin time stamps.
2. `02_dish_catwalk_level_blockout.png`:
   - Full in-engine CRT rendering of `act_01/dish_catwalk.json` showcasing the upper one-way catwalk platforms, mid-level structural trusses, central feedhorn mast at $x=296$, and ground walkway.
3. `03_holdout_combat_encounter_preview.png`:
   - In-engine combat screenshot during active holdout at $t=34.0s$ (Bin 3 'Q', 26$\sigma$ peak), featuring player in firing stance, `CoreReconDrone` targeting laser lock, `StaticHound` ground patrol, and the complete holdout HUD footer and top bar.
4. `04_jammed_feedhorn_and_unjam_interaction.png`:
   - Technical alert card detailing the feedhorn jamming mechanics: Wave 2 trigger, continuous $-1.0$ HP/s integrity decay, player counterplay via proximity and `unjam()`, and failure reset behavior.
5. `05_mission_completion_reward_flow.png`:
   - Step-by-step flowchart and telemetry breakdown detailing the 4-stage progression lifecycle: 72.0s accumulation completion $\to$ atomic event grant $\to$ replay idempotence $\to$ unlock of Milestone 2 Task A09 (Greenkeeper Boss Arena).

---

## 4. Test Suite & Quality Audits

- **Full Game Test Suite:** 196 passed (`pytest video_game/tests/`).
- **Holdout & Objectives Suite:** 7 passed in 0.29s (`pytest video_game/tests/test_objectives.py`).
- **Campaign & Station Suite:** 33 passed in 0.75s (`pytest video_game/tests/test_campaign.py`).
- **Combat Test Suite:** 22 passed in 0.14s (`pytest video_game/tests/test_combat.py`).
- **Checkpoint Audit:** 3 passed in 0.44s (`pytest video_game/tests/test_checkpoint_audit.py`).
- **Locked Asset Groups:** All 14 groups preserved under dry-run check (`python video_game/tools/build_assets.py --dry-run`).
- **Level Content Validation:** Clean (2/2 levels valid via `python video_game/tools/validate_content.py`).

