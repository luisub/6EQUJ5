# Milestone 2 — Task A05 Evidence Report: Starter Weapon and Projectile Loop

**Date:** 2026-11-10  
**Task ID:** A05  
**Milestone:** 02_action_slice (Milestone 2: Complete Playable Act I)  
**Status:** Complete and Verified  
**Rollback Snapshot:** `video_game/_trash/2026-11-10_A05_before_changes.tar.gz` (SHA-256: `eb34906bc668b4a33a7fac33c284c7bb5809d435c0fab2d52b5a4ac9ecfd3cbd`)  
**Manifest:** `video_game/_trash/2026-11-10_A05_before_changes_manifest.json`  

---

## 1. Executive Summary

Task A05 establishes the starter weapon and projectile simulation engine for 6EQUJ5, centered around Dr. Mateo Vargas's primary firearm: the **1420 MHz Waveguide Maser**.

The implementation resides in `video_game/engine/weapons.py` (`WeaponConfig`, `CombatTarget`, `HitResult`, `Projectile`, `ProjectileManager`, `StarterMaser`), integrated into `video_game/engine/player.py` (`PlayerInput`, recoil state transitions, camera-independent muzzle attachment queries) and `video_game/engine/scenes/field.py` (`FieldOpsScene` combat loops and CRT beam rendering).

Key capabilities delivered:
1. **Continuous Collision Detection (CCD) via Amanatides-Woo Grid Ray-Marching:** Fast-moving maser bolts (420–2000 px/s) mathematically cannot tunnel through thin 1-tile (16px) solid barriers or enemy hitboxes, even during large delta-time frame drops.
2. **8-Directional Aim Vectors:** Normalized unit vectors support firing horizontally, vertically, diagonally, and forward from low crouch with zero magnitude distortion.
3. **Multi-Target Piercing Mechanics:** Charged maser overcharge bolts (75 HP, 3-target pierce budget) penetrate up to three targets in spatial sequence; explicit `hit_target_ids` tracking prevents multi-frame re-damage within hitboxes.
4. **Cadence Cooldown and Charge Timing:** Rapid tap fire enforces strict 0.20s cooldown (5 shots/sec); held fire accumulates charge up to 0.60s to unleash a high-energy plasma beam upon trigger release.
5. **Pause Safety & Lifecycle Containment:** Game pause (`is_paused=True`) completely freezes cadence timers, charge progression, active projectile positions, lifetimes, and spark particles; `ProjectileManager.clear()` prevents orphan projectiles across respawns or retries.

---

## 2. Acceptance Checks Verification

### Check 1: Fast projectiles hit thin walls and targets reliably
- **Test:** `test_swept_ray_tile_collision_prevents_thin_wall_tunneling` & `test_fast_projectile_hits_thin_target_reliably` in `video_game/tests/test_combat.py`.
- **Result: PASSED.**
  - A 1-tile solid wall (16px wide at $x = 80$) successfully blocked a projectile jumping 120px in a single frame ($x = 20 \rightarrow 140$). The swept collision ray-traversal intersected the wall face at $x = 80.0$, arresting the projectile with zero tunneling.
  - A thin target hitbox (8px wide at $x = 100$) was reliably detected and damaged by a 1400 px/s projectile moving 140px in a single tick ($x = 10 \rightarrow 150$).

### Check 2: A piercing shot has explicit per-target hit behavior
- **Test:** `test_piercing_shot_per_target_hit_behavior` & `test_simultaneous_multi_target_piercing_in_single_tick` in `video_game/tests/test_combat.py`.
- **Result: PASSED.**
  - A charged maser shot (`pierce_remaining = 3`, 75 damage) traveled across four targets ($A, B, C, D$).
  - Target $A$ took 75 damage in Frame 1; Target $B$ took 75 damage in Frame 2; Target $C$ took 75 damage in Frame 3, exhausting the pierce budget.
  - Target $D$ remained completely protected at full 100 HP.
  - `hit_count` for each pierced target remained strictly $1$, proving that projectiles continuing across subsequent frames never double-damage the same target.

### Check 3: Held fire respects timing and pause
- **Test:** `test_held_fire_respects_timing_and_cadence`, `test_weapon_charge_and_release_mechanic`, & `test_game_pause_freezes_combat_and_cooldowns` in `video_game/tests/test_combat.py`.
- **Result: PASSED.**
  - Holding fire cannot exceed the rate of fire limit: 0.20s cooldown is enforced between shots.
  - Holding fire for 0.65s builds full charge (`charge_timer >= 0.60s`); releasing fire triggers the charged 75 HP plasma beam. Releasing before 0.60s releases no extra shot.
  - Pausing the simulation (`is_paused=True`) freezes all projectile velocities, positions, lifetimes, charge accumulation, and cooldown decay.

### Check 4: Damage/retry cannot duplicate rewards or leave orphan projectiles
- **Test:** `test_death_retry_idempotence_and_no_orphan_projectiles` in `video_game/tests/test_combat.py`.
- **Result: PASSED.**
  - Lethal damage sets `target.is_dead = True` and returns `target_killed = True` with `reward_claimed = True` on the fatal tick only.
  - Subsequent damage calls against a dead target return `hit = False`, `damage_dealt = 0`, and `target_killed = False`, preventing duplicate reward claims or score exploits.
  - Calling `ProjectileManager.clear()` flushes all projectiles and particle sparks, ensuring zero memory leaks or orphan hitboxes on room respawn or retry.

---

## 3. Visual Previews & Evidence Artifacts

The following visual evidence files were generated in `video_game/planning/evidence/A05/previews/`:

1. `01_swept_ccd_thin_wall_containment.png`:
   - Visual comparison of discrete point sampling (which tunnels through a 16px wall during a 128px step) versus Amanatides-Woo swept ray-marching (which arrests the bolt exactly at $x = 240.0$).
2. `02_piercing_beam_multi_target.png`:
   - Diagram of the 1420 MHz charged plasma beam cutting through three consecutive targets, showing damage logs, spark bursts, and final absorption before the fourth target.
3. `03_aim_vectors_8_directions.png`:
   - Compass diagram showing Mateo's 8 aim vectors (Right, Up-Right, Up, Up-Left, Left, Down-Left, Down, Down-Right) with normalized unit lengths and muzzle attachment registration.
4. `04_ingame_combat_field_preview.png`:
   - In-engine CRT render of `FieldOpsScene` showing animated Mateo discharging the waveguide maser in the Ohio trench with muzzle recoil and dual maser bolts.
5. `05_charge_state_meter_preview.png`:
   - Side-by-side specification card comparing standard cyan maser pulse (25 HP, 420 px/s, 1 pierce) against charged gold plasma overdrive (75 HP, 483 px/s, 3 pierce).

---

## 4. Test Suite & Quality Audits

- **Full Test Suite:** 174 passed in 14.29s (`pytest video_game/tests/`).
- **Combat Test Suite:** 12 passed in 0.08s (`pytest video_game/tests/test_combat.py`).
- **Checkpoint Audit:** 3 passed in 0.28s (`pytest video_game/tests/test_checkpoint_audit.py`).
- **Locked Asset Groups:** All 14 groups preserved under dry-run check (`python video_game/tools/build_assets.py --dry-run`).
- **Level Content Validation:** Clean (`python video_game/tools/validate_content.py`).

