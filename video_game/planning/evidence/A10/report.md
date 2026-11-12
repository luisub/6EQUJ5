# Milestone 2 — Task A10 Evidence Report: Assemble the Act I Mission Chain

**Date:** 2026-11-11  
**Task ID:** A10  
**Milestone:** 02_action_slice (Milestone 2: Complete Playable Act I)  
**Status:** Complete and Verified  
**Rollback Snapshot:** `video_game/_trash/2026-11-11_A10_before_changes.tar.gz` (SHA-256: `abefaca8cdd34278220274f9f76e8509c06819dcdb125394e24d9781fc9027ae`)  
**Manifest:** `video_game/_trash/2026-11-11_A10_before_changes_manifest.json`  

---

## 1. Executive Summary

Task A10 integrates all narrative, systemic, and environmental threads of Act I into a cohesive, uninterrupted 7-stage mission chain. Dr. Mateo Vargas progresses from the first radio signal detection at the Big Ear receiver through hazardous scrap scavenging in the Salvage Yard, workbench feedhorn restoration, high-altitude wave defense on the dish catwalk, and the climactic boss encounter against Core Warden Greenkeeper.

Key deliverables and architectural achievements:
1. **Act I Mission Progression Architecture (`video_game/engine/objectives.py`):**
   - Implemented 7 continuous operational stages in `ObjectiveTracker.get_active_objective`:
     - Stage 1: `obj_make_first_contact` / `obj_extract_fragment` (CRT Terminal Haystack Search).
     - Stage 2: `obj_validate_signal` (Science Lab protocol verification).
     - Stage 3: `obj_scavenge_coupler` (Airlock dispatch to Approach Trench & Salvage Yard).
     - Stage 4: `obj_repair_dish` (Bunker repair workbench analog coupler calibration).
     - Stage 5: `obj_defend_dish` (Big Ear dish array catwalk wave defense).
     - Stage 6: `obj_defeat_greenkeeper` (Core Warden boss battle in deep reflector basin).
     - Stage 7: `obj_act_01_complete` (FASR-007 spread-spectrum validation and Act II transit).
2. **Salvage Yard Level Blockout (`video_game/data/levels/act_01/salvage_yard.json`):**
   - 40×18 tile map ($640 \times 288\text{ px}$) validated cleanly via `validate_content.py`.
   - Upper and mid one-way scrap grating platforms (`COLLISION_ONE_WAY`, $y=144, 192$).
   - Active environmental hazard: electrical sump pit ($y=224$, cols 18–22) dealing 15 damage per tick.
   - Cover crate obstacles (`COLLISION_COVER`, $x=240, 480$).
   - Parts cache pickup (`analog_coupler`, $x=576, y=192$) for feedhorn restoration.
   - Dual checkpoints: `yard_start` ($x=48$) and `yard_depot` ($x=576$).
3. **Bunker Airlock Dynamic Dispatching (`video_game/engine/scenes/bunker.py`):**
   - Upgraded station interaction at airlock coordinates ($x=348$) to inspect campaign flags:
     - Dispatches to `act_01/approach.json` when starting the first field mission.
     - Intercepts and warns `"REPAIR REQUIRED // Analog Coupler must be calibrated at Workbench"` if player collects the coupler but attempts to proceed to the dish without repairing.
     - Dispatches to `act_01/dish_catwalk.json` when `feedhorn_repaired` is active.
     - Dispatches directly to `STATE_BOSS_BOUNTY` when `dish_defense_completed` is active.
4. **Seamless Field Operations Traversal (`video_game/engine/scenes/field.py`):**
   - Implemented `load_room(room_relative_path, spawn_name)` supporting bidirectional level streaming between Approach Trench (`act_01/approach.json`), Salvage Yard (`act_01/salvage_yard.json`), and Dish Catwalk (`act_01/dish_catwalk.json`).
   - Integrated door triggers with prerequisite checks (e.g., blocking catwalk if feedhorn is unpowered, blocking boss arena if dish defense is incomplete).
5. **Campaign Schema & Civilization Missions (`video_game/data/campaign.json`, `video_game/data/civilization_missions.json`):**
   - Registered `act_01_salvage_yard` room with checkpoints `["yard_start", "yard_depot"]`.
   - Annotated civilization missions `FASR-001` (Act I Stage 1) and `FASR-007` (Act I Stage 7 / Act II Transit) with progression metadata (`act_id`, `stage_order`, `unlocked_by`, `leads_to`).
6. **Persistence & Prerequisite Testing (`video_game/tests/test_campaign.py`):**
   - Added 4 acceptance tests verifying chain linearity, missing prerequisite feedback, mid-chain save/reload retention, and room navigation.

---

## 2. Acceptance Checks Verification

### Check 1: A fresh save can reach every required objective in order
- **Test:** `test_act_01_fresh_save_reaches_every_objective_in_order` in `video_game/tests/test_campaign.py`.
- **Result: PASSED.**
  - Verified progression through all 7 stages:
    - Initial state: Active objective is `obj_make_first_contact` (Target: CRT Terminal).
    - Signal contacted: Active objective advances to `obj_extract_fragment`.
    - Fragment extracted: Active objective advances to `obj_validate_signal` (Target: Science Lab).
    - Protocol validated: Active objective advances to `obj_scavenge_coupler` (Target: Airlock).
    - Coupler collected: Active objective advances to `obj_repair_dish` (Target: Repair Workbench).
    - Feedhorn repaired: Active objective advances to `obj_defend_dish` (Target: Airlock $\to$ Dish Catwalk).
    - Dish defended: Active objective advances to `obj_defeat_greenkeeper` (Target: Airlock $\to$ Boss Arena).
    - Greenkeeper defeated: Active objective advances to `obj_act_01_complete`, unlocking Act II transit.

### Check 2: Missing prerequisites explain the next action
- **Test:** `test_missing_prerequisites_block_and_explain_next_action` in `video_game/tests/test_campaign.py`.
- **Result: PASSED.**
  - **Airlock lockout with uninstalled coupler:** Scavenging the coupler and interacting with the airlock station returns `False` and issues toast `"REPAIR REQUIRED: Analog Coupler must be installed at Workbench"`.
  - **Catwalk door lockout in Field Operations:** Interacting with the dish catwalk door prior to feedhorn restoration blocks entry and displays HUD prompt `"ACCESS DENIED // FEEDHORN UNREPAIRED"`.
  - **Boss arena lockout in Field Operations:** Interacting with the arena door prior to repelling catwalk drone waves blocks entry and displays HUD prompt `"ARENA LOCKOUT // DISH DEFENSE INCOMPLETE"`.

### Check 3: Backtracking and reload cannot strand required items or missions
- **Test:** `test_save_reload_mid_mission_chain_preserves_exact_stage_and_inventory` in `video_game/tests/test_campaign.py`.
- **Result: PASSED.**
  - Saved a campaign state mid-chain at Stage 4 (coupler in inventory, trench coupler flag true, feedhorn unrepaired, FASR-001 fragment validated).
  - Serialized to disk and reloaded into a fresh `Campaign` instance.
  - Verified exact preservation of:
    - Inventory count: `analog_coupler == 1`.
    - Room flags: `trench_coupler_collected == True`, `feedhorn_repaired == False`.
    - Progress lists: `contacted_civs`, `extracted_fragments`, `validation_records`.
    - Objective tracker: Points precisely to `obj_repair_dish` at station `"repair"`.
  - Backtracking between Approach Trench, Salvage Yard, and Bunker Hub preserves collected items without duplication or disappearance.

### Check 4: Act II unlocks only after valid Act I completion
- **Test:** `test_act_02_unlocks_only_after_valid_act_01_completion` in `video_game/tests/test_campaign.py`.
- **Result: PASSED.**
  - Verified that `act_02_unlocked` remains `False` across all intermediate stages (Stages 1–6).
  - Calling `bunker.interact_with_station()` before dish defense routes cleanly to field missions without triggering Act II.
  - After completing `complete_dish_defense`, airlock routes to `STATE_BOSS_BOUNTY`.
  - Only after `apply_event({"event_id": ..., "type": "defeat_greenkeeper"})` is `act_02_unlocked` set to `True` and `act_01_completed` set to `True`.

---

## 3. Visual Previews & Evidence Artifacts

The following visual evidence files were generated in `video_game/planning/evidence/A10/previews/`:

1. `01_act_01_mission_chain_flowchart.png`:
   - High-level sequence diagram detailing all 7 stages of Act I from radio contact to Act II transit with target stations and conditions.
2. `02_salvage_yard_level_blockout.png`:
   - In-engine CRT blockout of `act_01/salvage_yard.json` showing upper one-way scrap grating, electrical sump hazard pit, cover crates, and parts cache pickup.
3. `03_mission_prerequisite_blocking_card.png`:
   - Tactical HUD card detailing all 4 security interlocks, active enforcement statuses, and player guidance prompts.
4. `04_bunker_dispatch_and_airlock_routing.png`:
   - State transition routing table documenting airlock dispatch targets across campaign stages.
5. `05_save_reload_mid_chain_telemetry.png`:
   - State preservation telemetry comparing pre-save and post-reload metrics and confirming zero data loss.

---

## 4. Test Suite & Quality Audits

- **Full Game Test Suite:** **205 passed in 14.27s** (`pytest video_game/tests/`).
- **Campaign & Mission Chain Suite:** **37 passed in 0.81s** (`pytest video_game/tests/test_campaign.py`).
- **Engine Boot & Scene Suite:** **8 passed in 0.99s** (`pytest video_game/tests/test_engine_boot.py`).
- **Checkpoint Audit:** **3 passed in 0.32s** (`pytest video_game/tests/test_checkpoint_audit.py`).
- **Level Content Validation:** **4/4 levels validated cleanly** (`act_01/approach.json`, `act_01/dish_catwalk.json`, `act_01/greenkeeper_arena.json`, `act_01/salvage_yard.json`).
- **Locked Asset Groups:** All 14 groups preserved under dry-run check (`python video_game/tools/build_assets.py --dry-run`).

