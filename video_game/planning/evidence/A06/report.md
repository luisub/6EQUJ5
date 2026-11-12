# Milestone 2 — Task A06 Evidence Report: First Enemies and Predictive Attacks

**Date:** 2026-11-11  
**Task ID:** A06  
**Milestone:** 02_action_slice (Milestone 2: Complete Playable Act I)  
**Status:** Complete and Verified  
**Rollback Snapshot:** `video_game/_trash/2026-11-11_A06_before_changes.tar.gz` (SHA-256: `de1b6490e5e97ed437e1174fe912bdc4d80088c5c51d8c77080fdf24b717afa0`)  
**Manifest:** `video_game/_trash/2026-11-11_A06_before_changes_manifest.json`  

---

## 1. Executive Summary

Task A06 establishes the enemy combat AI and predictive targeting simulation for 6EQUJ5, introducing the first two hostile archetypes encountered across the Ohio telescope ruins:
1. **Core Recon Drone (Aerial):** A hovering robotic scout equipped with an articulated beam cannon, predictive trajectory lead tracking, aim locking, and pulsed plasma bolts.
2. **Static Hound (Ground):** A low-slung quad mechanical prowler with audio sensor horns, high-velocity forward leap pounce attacks, and vulnerability to Mateo's low slide-kick.

The core enemy architecture is implemented in `video_game/engine/enemies.py` (`EnemyConfig`, `Enemy`, `CoreReconDrone`, `StaticHound`, `EnemyProjectile`, `EnemyManager`), balanced via `video_game/data/balance.json` (`"enemies"` block), visualized using authentic pixel art frames in `video_game/assets/sprites/enemies/` with `manifest.json`, and integrated into `video_game/engine/scenes/field.py` (`FieldOpsScene`).

Key mechanics delivered:
1. **Predictive Aim with Telegraph Lock Window:** Drone computes the player's anticipated position $\vec{P}_{\text{pred}} = \vec{P}_{\text{player}} + \vec{V}_{\text{player}} \times 0.30\text{ s}$ during tracking. During the final 0.30s of windup, the aim vector freezes and the laser telegraph flashes solid red, guaranteeing a readable dodge window.
2. **Distinct Behavioral Archetypes:** Drone hovers smoothly, reverses horizontal patrol bounds at walls or turn distances, and maintains stand-off range. Static Hound patrols ground platforms, telegraphs pounce with rear crouch and glowing horns, and launches into a parabolic ballistic leap dealing 30 damage.
3. **Cover & Line-of-Sight Concealment:** Amanatides-Woo ray-marching occludes enemy sightlines through solid level tiles. Background doorway cover hides Mateo completely from detection; low sandbag cover absorbs frontal projectile fire.
4. **Counter-Play & Slide-Kick Interaction:** Mateo's low slide-kick ($35\text{ damage}$) safely slides beneath a pouncing hound's upper leap hitbox, interrupting the attack and staggering the hound.
5. **State Hygiene & Restart Idempotence:** Defeating enemies triggers death animations and single-tick reward flags; room transitions or respawns purge all active enemy projectiles and tracking state with zero memory leaks.

---

## 2. Acceptance Checks Verification

### Check 1: Telegraphed attacks leave a dodge window and clear player feedback
- **Tests:** `test_drone_state_transitions_and_predictive_aim` & `test_predictive_aim_locks_trajectory_during_final_lock_window` in `video_game/tests/test_combat.py`.
- **Result: PASSED.**
  - When the drone acquires line-of-sight, it transitions `PATROL` $\rightarrow$ `DETECT` (0.40s) $\rightarrow$ `WINDUP` (0.80s).
  - During the initial windup phase, the laser targeting line dynamically tracks the player's velocity vector with an anticipatory lead ($+0.30\text{ s}$).
  - During the final 0.30s (`lock_window`), `aim_locked` becomes `True` and the telegraph ray freezes in place. Player velocity changes during this window do not deflect the locked line, enabling reliable dodge/slide maneuvers.
  - Upon windup expiration, the drone discharges an energy projectile directly along the locked vector into `ATTACK` and `RECOVERY`.

### Check 2: Ground / aerial variants behave distinctly and handle ledges / ceilings
- **Tests:** `test_drone_patrol_reversal_on_boundaries_and_walls`, `test_static_hound_windup_telegraph_and_pounce`, `test_slide_kick_counters_pouncing_hound`, & `test_hound_pounce_blocked_by_low_cover` in `video_game/tests/test_combat.py`.
- **Result: PASSED.**
  - Aerial Drone maintains altitude, detects solid tile barriers or maximum patrol distance ($120\text{ px}$), and smoothly flips velocity without falling or getting stuck.
  - Ground Hound stays grounded on platform surfaces. On detecting the player within $180\text{ px}$, it initiates a 0.60s windup before launching a $240\text{ px/s}$ pounce.
  - A slide-kick timed during the hound's leap deals 35 damage and interrupts the pounce.
  - A low sandbag barrier absorbs the hound's leap, protecting the player crouching behind it.

### Check 3: Line of sight and cover mechanics
- **Tests:** `test_line_of_sight_blocked_by_solid_tiles` & `test_player_concealed_in_doorway_background_cover` in `video_game/tests/test_combat.py`.
- **Result: PASSED.**
  - Amanatides-Woo grid raycast between enemy eye origin and player center detects intervening solid geometry; enemies behind solid walls never acquire target lock or leave patrol.
  - When Mateo is overlapping a doorway zone in the background cover state (`cover_active=True`), enemy line-of-sight checks return `False`, keeping enemies in neutral patrol.

### Check 4: Idempotence & Lifecycle Containment
- **Tests:** `test_death_and_projectile_cleanup_idempotence` & `test_offscreen_enemies_remain_passive` in `video_game/tests/test_combat.py`.
- **Result: PASSED.**
  - Lethal damage triggers `STATE_DEATH`. Dead enemies do not update aim or fire projectiles.
  - `manager.clear()` purges all active projectiles and hit effects on level reload or player death.
  - Off-screen enemies ($> 80\text{ px}$ beyond camera viewport) sleep in passive state and do not spam off-screen projectiles.

---

## 3. Visual Previews & Evidence Artifacts

The following visual evidence files were generated in `video_game/planning/evidence/A06/previews/`:

1. `01_enemy_roster_contact_sheet.png`:
   - Pixel art frame roster for Core Recon Drone (`patrol_1/2`, `windup_1/2`, `attack`, `recovery`, `hurt`, `death`) and Static Hound (`patrol_1/2`, `windup`, `pounce`, `recovery`, `hurt`, `death`) alongside specs.
2. `02_predictive_targeting_telegraph.png`:
   - Visual comparison of active dynamic tracking phase (dashed amber line leading moving player) versus locked telegraph phase (solid red line fixed in space, allowing dodge slide).
3. `03_cover_and_line_of_sight_occlusion.png`:
   - Diagram of line-of-sight occlusion: raycast blocked by solid bunker wall, doorway cover concealing player, and sandbags absorbing low trajectory shot.
4. `04_hound_pounce_vs_slidekick.png`:
   - Trajectory breakdown showing Static Hound leap arc ($240\text{ px/s}$), unmitigated impact damage (30 HP), and Mateo's low slide-kick counter ($35\text{ damage}$, invulnerable frame passage).
5. `05_ingame_encounter_preview.png`:
   - In-engine CRT screenshot of `FieldOpsScene` trench encounter showing active Recon Drone targeting Mateo over catwalk and Static Hound prowling below.

---

## 4. Test Suite & Quality Audits

- **Full Test Suite:** 184 passed in 14.38s (`pytest video_game/tests/`).
- **Combat Test Suite:** 22 passed in 0.14s (`pytest video_game/tests/test_combat.py`).
- **Checkpoint Audit:** 3 passed in 0.15s (`pytest video_game/tests/test_checkpoint_audit.py`).
- **Locked Asset Groups:** All 14 groups preserved under dry-run check (`python video_game/tools/build_assets.py --dry-run`).
- **Level Content Validation:** Clean (`python video_game/tools/validate_content.py`).

