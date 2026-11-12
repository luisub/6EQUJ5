# Milestone 2 — Task A03 Evidence Report: Implement Cover, Crouch and Slide-Kick

**Date:** 2026-11-10  
**Task ID:** A03  
**Milestone:** 02_action_slice (Milestone 2: Complete Playable Act I)  
**Status:** Complete and Verified  
**Rollback Snapshot:** `video_game/_trash/2026-11-10_A03_before_changes.tar.gz` (SHA-256: `f0e580e9c34e6b02a37b44397c1f65a6c3a0c1c574893b15b22e486efc81c6cb`)  
**Manifest:** `video_game/_trash/2026-11-10_A03_before_changes_manifest.json`

---

## 1. Executive Summary

Task A03 implements tactical crouch, legal standing clearance checks, low/background cover systems with directional ballistic protection, and dynamic slide-kick kinematics for Mateo.

Tuned in `video_game/data/balance.json` and executed within the 120 Hz fixed-step simulation in `video_game/engine/player.py`, the system guarantees that standing up under low overhangs is safely rejected, slide-kicks cannot cross solid walls or double-damage targets, and background alcove concealment protects against incoming horizontal fire while forbidding firing through geometry.

---

## 2. Acceptance Checks Verification

### Check 1: Protection matches attack direction and cover type
- **Low Foreground Cover (Sandbags / Crates):**
  - Standing behind low cover provides 0% protection against incoming projectiles.
  - Crouching behind low cover blocks frontal attacks from the direction of the barrier (`protection_directions=["right"]`), while remaining vulnerable to flank attacks from behind (`"left"`) and plunging attacks from above (`"above"`).
  - Verified by `test_cover_protection_matches_attack_direction_and_type` in `test_player.py`.
- **Background Doorway Cover (Recessed Corridors / Alcoves):**
  - Stepping into a background doorway recess (`in_cover=True, cover_type="background"`) conceals Mateo from horizontal combat planes, blocking attacks from both `"left"` and `"right"`.
  - Forbidden geometry rule: Mateo cannot fire weapons while fully concealed in background recess (`can_fire == False`).
  - Verified by `test_cover_protection_matches_attack_direction_and_type` in `test_player.py`.

### Check 2: Standing under low ceilings is rejected safely
- **Clearance Verification:** Overhead headroom is verified via `can_stand(room)` querying a 12px vertical region above Mateo's crouched profile (`self.y .. self.y + 12`).
- **Safety Rejection:**
  - Inside a 16px crawlspace (e.g. pipe or duct overhead), releasing the crouch key safely rejects standing, keeping `is_crouching = True`.
  - When completing a slide underneath low ceilings, Mateo automatically transitions into a crouch rather than forcing standing geometry into solid tiles.
  - Once Mateo crawls or slides into open space, `can_stand(room)` returns `True` and normal standing posture resumes.
  - Verified by `test_standing_under_low_ceilings_rejected_safely` in `test_player.py`.

### Check 3: Sliding cannot cross solid walls or repeatedly damage one target per slide
- **Slide Kinematics:** Triggered by crouch input during horizontal movement (`slide_speed = 220.0 px/s`, duration $= 0.35\text{s}$, cooldown $= 0.20\text{s}$, height $= 14\text{ px}$).
- **Wall Collision Safety:** Sliding into a solid wall terminates the slide immediately (`is_sliding = False`, `slide_timer = 0.0`), resets velocity to 0, and snaps Mateo safely out of wall geometry.
- **Kick Damage Tracking:**
  - Slide kick deals 35 damage via leading kick hitbox (`slide_kick_rect`).
  - Target tracking (`slide_damaged_targets`) ensures that any individual enemy target can be damaged at most once per slide execution.
  - Verified by `test_sliding_wall_stop_and_slide_kick_target_tracking` in `test_player.py`.

### Check 4: Pause/death/reset restore the right locomotion state
- **Neutral Restoration:** Death, checkpoint respawns, and scene resets cleanly wipe slide timers, cooldowns, damaged target registries, crouch flags, and cover concealment states.
- **Coherent State:** Health is restored to 100, velocity reset to (0, 0), grounded set to `True`, and standard standing height ($32\text{ px}$) restored.
- **Verified by:** `test_locomotion_reset_on_death_and_pause` in `test_player.py`.

---

## 3. Teaching Geometry & Level Blockout

Added visible tutorial cues to `video_game/data/levels/act_01/approach.json`:
1. `doorway_recess_cover` ($x=160.0, y=176.0$): Recessed doorway alcove teaching background cover concealment (`[UP / E] CONCEAL IN COVER`).
2. `sandbag_low_cover` ($x=384.0, y=192.0$): Fortified sandbag barrier teaching low crouching cover (`[CROUCH] TO DUCK`).
3. `slide_training_barrier` ($x=512.0, y=192.0$): Training barrier dummy requiring slide-kick to breach (`SLIDE-KICK TO BREACH`, 35 HP).

---

## 4. Visual Previews

| Screenshot | Description |
|---|---|
| `01_low_cover_crouch_sandbags.png` | Mateo crouched behind the fortified low sandbag emplacement ($x=370, y=192$) with prompt `"FORTIFIED COVER EMPLACEMENT // [CROUCH] TO DUCK"`. |
| `02_background_doorway_cover_concealed.png` | Mateo concealed in the recessed doorway alcove ($x=168, y=192$) with prompt `"CONCEALED IN RECESSED ALCOVE // COVER ACTIVE"`. |
| `03_tactical_slide_kick_action.png` | Mateo executing low-profile slide-kick ($x=480, y=192$) with leading attack hitbox approaching training dummy barrier. |
| `04_low_clearance_crawlspace_clearance_rejection.png` | Mateo crouched under low ceiling overhang ($x=288, y=192$) with standing clearance rejected safely. |
| `05_cover_exit_and_run_transition.png` | Mateo transitioning out of cover into full forward sprint toward the radio mast ($x=520, y=192$). |

All preview images are saved under `video_game/planning/evidence/A03/previews/` ($480 \times 270\text{ px}$).

---

## 5. Test Suite Execution & Quality Gates

```bash
/opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_player.py -vv
# Result: 15 passed in 0.06s

/opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_world.py -vv
# Result: 8 passed in 0.23s

/opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests tests -q
# Result: 174 passed in 19.02s

/opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_checkpoint_audit.py -vv
# Result: 3 passed in 0.29s (syntax, explicit imports, module headers, no line budget violations)

/opt/anaconda3/envs/6equj5_game/bin/python -m video_game.tools.build_assets --dry-run
# Result: 14/14 locked asset groups preserved
```

