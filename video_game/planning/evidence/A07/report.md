# Milestone 2 — Task A07 Evidence Report: Connect Bunker Stations, Inventory, and HUD

**Date:** 2026-11-11  
**Task ID:** A07  
**Milestone:** 02_action_slice (Milestone 2: Complete Playable Act I)  
**Status:** Complete and Verified  
**Rollback Snapshot:** `video_game/_trash/2026-11-11_A07_before_changes.tar.gz` (SHA-256: `24b426a778e2902622ca2f8acbc3c63afac3e97e89e8ab98bc539bfde67c8aab`)  
**Manifest:** `video_game/_trash/2026-11-11_A07_before_changes_manifest.json`  

---

## 1. Executive Summary

Task A07 connects the Big Ear bunker stations, collectible inventory items, mission objectives, and the complete player HUD for Act I of 6EQUJ5.

Key subsystems delivered and verified:
1. **Physical Proximity Station Interactions:** Replaced arbitrary global hotkey transitions with four physical trigger zones across the 480×270 bunker floor:
   - **Science Lab Workbench** ($x \in [124.0, 160.0]$): Transitions to formal validation workbench (`STATE_SCIENCE_LAB`).
   - **Big Ear Receiver Terminal** ($x \in [170.0, 260.0]$): Transitions to receiver CRT session (`STATE_CRT_TERMINAL`).
   - **Analog Repair Workbench** ($x \in [275.0, 315.0]$): Evaluates prerequisites, consumes recovered analog parts, and executes antenna feedhorn repairs.
   - **Surface Airlock** ($x \in [330.0, 364.0]$): Transitions to outdoor approach trench (`STATE_FIELD_OPS`).
   When standing outside station zones (e.g. neutral corridor at $x = 268.0$), pressing Interact (`E` or Enter) does not trigger any transition. In normal play (`machine.development == False`), direct jump shortcuts are disabled in favor of discoverable floating station prompts.
2. **Collectible Analog Parts & Idempotent Repair Event:** Added `"analog_coupler"` to `campaign.json` items and `"trench_coupler_collected"` / `"feedhorn_repaired"` to flags. A glowing pickup in the surface trench ($x = 560, y = 208$) awards the part atomically. Interacting with the bunker repair bench checks prerequisites, consumes the coupler, marks `feedhorn_repaired = True`, awards $+5$ Scientific Certainty and $+5$ Human Agency, and permanently records completion to prevent replay duplication or save corruption.
3. **Big Ear Dossier Overlay View:** Players can toggle the full-screen CRT Dossier view (`[TAB]`) at any time in the bunker. The dossier exposes:
   - All 6 campaign meters with visual progress gauges ($0–100\%$) and numerical readouts.
   - Active Act I objective title, description, and station guidance hint.
   - Inventory items (equipped maser, analog coupler, feedhorn status).
   - Signal intelligence summary (contacted civs, fragments, formal validations).
4. **Enhanced HUD with Disjoint Non-Overlapping Layout:** Expanded `video_game/engine/ui/hud.py` to communicate combat state with mathematically disjoint bounding zones:
   - **Zone 1: Top Bar** ($y \in [0, 16]$): Facility location, objective title snippet, timeline indicator.
   - **Zone 2: Player Combat Stats** ($x \in [8, 110], y \in [19, 33]$): Health numeric readout, dynamic health bar (green/amber/red), active weapon name, charge overdrive meter.
   - **Zone 3: Threat Lock Alert** ($x \in [155, 325], y \in [18, 31]$): Centered amber warning (`TARGETING DETECTED`) and flashing red alarm (`LOCK-ON: EVADE NOW!`).
   - **Zone 4: Notification Banner** ($x \in [50, 430], y \in [34, 47]$): Dedicated alert row for objective changes, item pickups, and failure notices (`PREREQUISITE UNMET: MISSING ANALOG COUPLER`).
   - **Zone 5: Footer Strip** ($y \in [254, 270]$): Monospace control cues.
   Pairwise collision tests prove strictly zero overlap between all five UI regions.
5. **Dynamic Objective Progression:** Created `video_game/engine/objectives.py` (`ObjectiveTracker`, `Objective`, `Notification`), dynamically advancing the player across five Act I stages (Receiver Contact $\to$ Lab Validation $\to$ Coupler Search $\to$ Feedhorn Repair $\to$ Perimeter Defense) with transient notification alerts.

---

## 2. Acceptance Checks Verification

### Check 1: Station activation works only when the relevant interaction is available
- **Test:** `test_bunker_station_activation_requires_proximity_and_valid_interaction` in `video_game/tests/test_campaign.py`.
- **Result: PASSED.**
  - When standing in the neutral corridor ($x = 268.0$), `get_active_station()` returns `None`; pressing `E` leaves `machine.current_state_name` in `STATE_BUNKER_HUB`.
  - Walking to $x = 140.0$ activates `lab` and transitions to `STATE_SCIENCE_LAB`.
  - Walking to $x = 215.0$ activates `terminal` and transitions to `STATE_CRT_TERMINAL`.
  - Walking to $x = 345.0$ activates `field` and transitions to `STATE_FIELD_OPS`.
  - In normal play (`machine.development = False`), pressing development shortcut keys (`L`, `F`, `B`) does not trigger state transitions.

### Check 2: Collected parts and repaired objects persist exactly once
- **Test:** `test_collectible_analog_coupler_and_repair_interaction_persist_once` in `video_game/tests/test_campaign.py`.
- **Result: PASSED.**
  - Attempting to repair without the analog coupler raises an unmet prerequisite error (`Unmet prerequisites for inventory item analog_coupler`).
  - Collecting the coupler in the approach trench awards `analog_coupler: 1`, sets `trench_coupler_collected = True`, and updates coordination capacity.
  - Re-applying the collect event is idempotent and returns `False`.
  - Executing repair consumes the coupler (`inventory["analog_coupler"] = 0`), sets `feedhorn_repaired = True`, and increases Scientific Certainty and Human Agency by $+5$.
  - Re-repairing is rejected as already completed.
  - Full disk save and reload cycle verifies that `feedhorn_repaired: true` and consumed inventory persist accurately, and replay after reload returns `False`.

### Check 3: HUD communicates damage, objective changes and failure reasons without overlap
- **Test:** `test_hud_rendering_and_zero_bounding_box_overlaps` in `video_game/tests/test_campaign.py`.
- **Result: PASSED.**
  - Simulated a full combat scenario with all elements rendered simultaneously: player health, charge meter, active objective, locked enemy threat alert, and failure notification banner.
  - Pairwise intersection tests across all five UI bounding boxes (`top_bar`, `player_stats`, `threat_alert`, `notification`, `bottom_bar`) verified that every bounding rect is mutually disjoint ($A \cap B = \emptyset$).

---

## 3. Visual Previews & Evidence Artifacts

The following visual evidence files were generated in `video_game/planning/evidence/A07/previews/`:

1. `01_bunker_station_proximity_prompts.png`:
   - 4-panel visual strip showing Mateo positioned at all four bunker stations with floating discoverable interaction prompt banners:
     - Panel 1: Science Lab workbench ($x = 140.0$, `[E] SCIENCE LAB // FORMAL VALIDATION BENCH`)
     - Panel 2: Big Ear Receiver console ($x = 215.0$, `[E] CRT RECEIVER // 1420.4056 MHz WOW!`)
     - Panel 3: Analog Repair workbench ($x = 295.0$, `[E] REPAIR BENCH // INSTALL ANALOG COUPLER`)
     - Panel 4: Surface Airlock door ($x = 345.0$, `[E] SURFACE AIRLOCK // ACT I APPROACH TRENCH`)
2. `02_dossier_campaign_meters_view.png`:
   - Full-screen in-engine CRT render of the Big Ear Dossier view (`[TAB]`), showing all 6 campaign meters with progress bars and numerical percentages, current operation title, active objective guidance, equipment inventory, and signal intelligence.
3. `03_hud_disjoint_layout_breakdown.png`:
   - In-engine HUD screenshot with color-coded bounding outlines and annotations highlighting the 5 mutually disjoint UI zones: Top Bar, Combat Stats, Threat Lock Alarm, Notification Banner, and Footer.
4. `04_collectible_coupler_trench_pickup.png`:
   - In-engine CRT render of the surface approach trench showing Mateo approaching the pulsing golden analog coupler pickup in the catwalk alcove ($x = 560, y = 208$).
5. `05_repair_interaction_and_meter_grant.png`:
   - Technical breakdown card documenting the 4-step repair lifecycle: initial prerequisite check rejection, trench pickup collection, atomic repair execution with coupler consumption and meter grants, and replay idempotence verification.

---

## 4. Test Suite & Quality Audits

- **Full Game Test Suite:** 189 passed in 16.46s (`pytest video_game/tests/`).
- **Campaign & Station Test Suite:** 33 passed in 0.75s (`pytest video_game/tests/test_campaign.py`).
- **Input & Settings Suite:** 15 passed in 0.35s (`pytest video_game/tests/test_input_settings.py`).
- **Combat Test Suite:** 22 passed in 0.14s (`pytest video_game/tests/test_combat.py`).
- **Checkpoint Audit:** 3 passed in 0.15s (`pytest video_game/tests/test_checkpoint_audit.py`).
- **Locked Asset Groups:** All 14 groups preserved under dry-run check (`python video_game/tools/build_assets.py --dry-run`).
- **Level Content Validation:** Clean (`python video_game/tools/validate_content.py`).

