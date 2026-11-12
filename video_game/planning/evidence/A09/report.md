# Milestone 2 — Task A09 Evidence Report: Implement Greenkeeper and the Boss Framework

**Date:** 2026-11-11  
**Task ID:** A09  
**Milestone:** 02_action_slice (Milestone 2: Complete Playable Act I)  
**Status:** Complete and Verified  
**Rollback Snapshot:** `video_game/_trash/2026-11-11_A09_before_changes.tar.gz` (SHA-256: `979184d71ff0ad85381e360b086ce6deab90018128020e6b70365db9c34efc09`)  
**Manifest:** `video_game/_trash/2026-11-11_A09_before_changes_manifest.json`  

---

## 1. Executive Summary

Task A09 implements the foundational sector boss architecture and Dr. Mateo Vargas's primary Act I nemesis: **The Greenkeeper** (Core Warden Overseer), an automated heavy terraforming excavator hijacked by The Core to bulldoze the Big Ear bunker.

Key subsystems delivered and verified:
1. **Generic Sector Boss Framework (`Boss`, `BossAttackTelegraph`, `BossProjectile`):**
   - Implemented in `video_game/engine/bosses/base.py`.
   - Multi-phase lifecycle (`PHASE_INTRO`, `PHASE_1`, `PHASE_2`, `PHASE_3`, `PHASE_DEFEATED`).
   - Exposed weak point vulnerability calculations with critical damage multipliers ($2.0\times$).
   - Transition invulnerability protecting boss during cinematic phase changes.
   - Clean arena reset restoring pristine state without memory leaks or orphaned hitboxes.
   - Deterministic win/death edge case resolution prioritizing fair player recovery.
2. **Core Warden Greenkeeper Combat AI (`video_game/engine/bosses/greenkeeper.py`):**
   - Imposing tracked chassis ($64 \times 48\text{ px}$, 300 Max HP).
   - **Phase 1 (300 $\to$ 200 HP):** Turf mortar artillery barrages lobbing high-arc explosives onto player positions with $0.8\text{s}$ warning reticles. Overheated exhaust vents open for $2.5\text{s}$ after two volleys, exposing the core.
   - **Phase 2 (200 $\to$ 100 HP):** Low-altitude horizontal sweeping energy cutter ($y \in [216, 232]$) with $0.7\text{s}$ telegraph line, plus bulldozer charges. Emitter overheats and bulldozer blade binds in ground rubble, exposing the frontal cowl weak point for $3.0\text{s}$.
   - **Phase 3 (100 $\to$ 0 HP):** Critical reactor meltdown; core remains permanently exposed while Greenkeeper rapidly alternates mortar shells and floor sweep pulses with clear evasion windows.
3. **Playable Boss Arena Scene (`video_game/engine/scenes/boss.py`):**
   - Implemented `BossScene` wired to `config.STATE_BOSS_BOUNTY` in `GameStateMachine`.
   - Complete boss HUD with segmented health bar (notched at $33\%$ and $66\%$), phase readout, and `[!] CORE VULNERABLE` indicators.
   - Pre-boss checkpoint (`pre_boss`) recovery: dying allows immediate retry via `[R]`, respawning player at 100 HP and resetting Greenkeeper cleanly to Phase 1.
4. **Deep Reflector Basin Level Geometry (`act_01/greenkeeper_arena.json`):**
   - 40×18 tile map ($640 \times 288\text{ px}$) validated cleanly via `validate_content.py`.
   - Elevated upper catwalks ($y=144$) and mid catwalks ($y=192$) with one-way grating tiles (`COLLISION_ONE_WAY`), providing guaranteed safe high ground against ground sweeping beams and bulldozer surges.
   - Low sandbag bulkheads (`COLLISION_COVER`) absorbing explosive shrapnel.
5. **Campaign Progression & Atomic Rewards (`video_game/data/campaign.json`):**
   - Registered room `act_01_greenkeeper_arena` with checkpoint `pre_boss`.
   - Registered event `defeat_greenkeeper` awarding $+10$ Scientific Certainty, $+15$ Human Agency, $+10$ Alignment Confidence, and setting flags `greenkeeper_defeated = True`, `act_01_completed = True`, `act_02_unlocked = True`.
   - Replay idempotence ensures zero duplicate meter grants.

---

## 2. Acceptance Checks Verification

### Check 1: Each phase can be completed with available Act I equipment
- **Test:** `test_boss_equipment_clears_all_phases` in `video_game/tests/test_combat.py`.
- **Result: PASSED.**
  - Verified that Mateo equipped with the Starter Waveguide Maser (`maser_1420`) and slide-kick can deplete each phase:
    - Phase 1: Tap shots (15 damage) and exposed weak point hits (30 damage) reduce 300 to 200 HP, triggering Phase 2 transition.
    - Phase 2: Charged maser shot (50 base $\times 2.0 = 100$ damage) into the stalled cowl drops health to 100 HP, triggering Phase 3 transition.
    - Phase 3: Critical core shot directly into the meltdown reactor deals 100 damage, cleanly triggering defeat at 0 HP.

### Check 2: No attack pattern requires an unavoidable hit
- **Test:** `test_boss_attacks_have_telegraphs_and_safe_routes` in `video_game/tests/test_combat.py`.
- **Result: PASSED.**
  - Mortar barrage: Displays $0.8\text{s}$ warning reticles ($24\text{ px}$ radius); moving outside the reticle takes exactly 0 damage.
  - Low sweep cutter: Displays $0.7\text{s}$ warning line; traveling strictly at ground level ($y \in [216, 232]$), players on elevated mid/upper catwalks ($y \le 192$) or jumping take exactly 0 damage.
  - Bulldozer charge: Warning arrow allows jumping over the chassis or staying on catwalks with zero damage taken.

### Check 3: Boss reset clears prior attacks and restores arena state
- **Test:** `test_boss_reset_clears_attacks_and_restores_arena` in `video_game/tests/test_combat.py`.
- **Result: PASSED.**
  - Put Greenkeeper into a dirty combat state in Phase 2 with active mortar telegraphs, active in-flight projectiles, and active sweep cutter.
  - Calling `reset_to_pristine()` restored HP to 300, reset phase to `PHASE_1`, cleared all telegraphs and projectiles, extinguished sweep beams, reset coordinates to spawn ($x=460.0, y=192.0$), and reset weak point status.

### Check 4: Win/death edge cases resolve consistently
- **Test:** `test_boss_win_and_death_edge_cases` in `video_game/tests/test_combat.py`.
- **Result: PASSED.**
  - Simultaneous death: When player health hits 0 in the same frame as boss defeat, `resolve_simultaneous_death(player_alive=False)` returns `"PLAYER_DIED"`. Reward grant is suppressed, requiring a valid checkpoint retry.
  - Clean victory: When player survives, `resolve_simultaneous_death(player_alive=True)` returns `"BOSS_DEFEATED"`.
  - Atomic grant: First call to `apply_defeat_reward(campaign)` grants flags and meters; second call returns `False` with zero state corruption.

---

## 3. Visual Previews & Evidence Artifacts

The following visual evidence files were generated in `video_game/planning/evidence/A09/previews/`:

1. `01_greenkeeper_boss_arena_blockout.png`:
   - Full in-engine CRT rendering of `act_01/greenkeeper_arena.json` showing elevated catwalks, pre-boss checkpoint, basin floor, and boss spawn area.
2. `02_greenkeeper_chassis_and_weak_point.png`:
   - Technical schematic card illustrating Greenkeeper's tracked chassis, bulldozer scoop, mortar cannon, exposed core weak point ($2.0\times$ critical), and Dr. Vargas's tactical doctrine.
3. `03_phase_1_mortar_barrage_encounter.png`:
   - In-engine combat screenshot of Phase 1 showing mortar targeting reticles, Dr. Mateo Vargas in firing stance with Waveguide Maser, boss health bar, and HUD footer.
4. `04_phase_2_sweep_laser_and_catwalk_safety.png`:
   - Technical breakdown illustrating the ground sweep cutter danger zone ($y \in [216, 232]$) versus guaranteed safe player routing on elevated mid/upper catwalks ($y \le 192$).
5. `05_boss_defeat_and_act_02_unlock_flow.png`:
   - Step-by-step flowchart documenting the 4-stage defeat sequence: simultaneous death resolution $\to$ atomic event grant $\to$ save idempotence $\to$ unlock of Milestone 2 Task A10 (Act I Mission Chain Assembly).

---

## 4. Test Suite & Quality Audits

- **Full Game Test Suite:** **201 passed in 19.65s** (`pytest video_game/tests/`).
- **Combat & Boss Suite:** **27 passed in 0.48s** (`pytest video_game/tests/test_combat.py`).
- **Engine Boot & Scene Suite:** **8 passed in 0.92s** (`pytest video_game/tests/test_engine_boot.py`).
- **Checkpoint Audit:** **3 passed in 0.15s** (`pytest video_game/tests/test_checkpoint_audit.py`).
- **Level Content Validation:** **3/3 levels validated cleanly** (`python video_game/tools/validate_content.py`).
- **Locked Asset Groups:** All 14 groups preserved under dry-run check (`python video_game/tools/build_assets.py --dry-run`).

