# Milestone 2 — Task A02 Evidence Report: Implement Stable Player Locomotion

**Date:** 2026-11-10  
**Task ID:** A02  
**Milestone:** 02_action_slice (Milestone 2: Complete Playable Act I)  
**Status:** Complete and Verified  
**Rollback Snapshot:** `video_game/_trash/2026-11-10_A02_before_changes.tar.gz` (SHA-256: `d444ab9d13f02dfef8f70e429380cb293e4bf3e9ba7fdadb269f125f1aed16e3`)  
**Manifest:** `video_game/_trash/2026-11-10_A02_before_changes_manifest.json`

---

## 1. Executive Summary

Task A02 implements a deterministic, fixed-timestep kinematic player simulation for Mateo in `video_game/engine/player.py`, driven by physics tuning in `video_game/data/balance.json`.

The locomotion system decoupling input polling from 120 Hz fixed-step physics integration ensures bit-for-bit framerate invariance across 30 FPS, 60 FPS, and 120 FPS rendering targets. It incorporates jump buffering ($0.12\text{s}$), coyote time ($0.10\text{s}$), variable jump cut ($0.5\times$), smooth ground/air acceleration and deceleration, axis-separated collision resolution, one-way platform mechanics, hazard damage with directional knockback and invulnerability frames, and instant checkpoint respawning with coherent full state.

---

## 2. Acceptance Checks Verification

### Check 1: Equivalent inputs at 30/60/120 render FPS produce matching movement within documented tolerance
- **Simulation Frequency:** $120\text{ Hz}$ fixed step (`fixed_dt = 1/120 ≈ 0.008333s`).
- **Render Accumulator:** Fixed-step accumulator buffers arbitrary frame times, consuming integer sub-steps and clamping lag backlog to `max_accumulator = 0.10s` (preventing accumulator spiral of death).
- **Invariance Benchmark:** Verified by `test_framerate_invariance_at_30_60_120_fps` in `test_player.py`:
  - 1.0 second of sustained rightward locomotion across flat terrain was simulated at 30 FPS (4 sub-steps/frame), 60 FPS (2 sub-steps/frame), and 120 FPS (1 sub-step/frame).
  - Positional delta:
    - $|x_{60} - x_{120}| = 0.0000\text{ px} \le 0.5\text{ px}$ tolerance.
    - $|x_{30} - x_{120}| = 0.0000\text{ px} \le 0.5\text{ px}$ tolerance.
    - Final horizontal velocity difference: $0.0000\text{ px/s}$.
  - Jump arc benchmark in `test_jump_arc_framerate_invariance`: Peak jump apex matches across 30, 60, and 120 FPS within $< 0.1\text{ px}$.

### Check 2: Corners, ceilings, one-way edges and fast falls cannot tunnel or trap the player
- **Axis-Separated Collision:** Horizontal and vertical movements are resolved independently. Sub-pixel penetration is resolved by integer directional edge clamping.
- **Corners & Ceilings:** Verified by `test_corners_and_ceilings_prevent_trapping` and `test_ceiling_bonk_immediately_cancels_upward_velocity`:
  - Jumping into an inside corner (solid wall on right, ceiling above) prevents clipping into tiles ($x + \text{width} \le 160.0$, $y \ge 16.0$) and allows immediate leftward departure without getting stuck.
  - Upward ceiling collision immediately zeroes vertical velocity (`vy = 0.0`), snapping Mateo to the bottom edge of the ceiling tile and initiating downward fall.
- **One-Way Platforms:** Verified by `test_one_way_platforms_traversal_and_edges`:
  - Upward jump smoothly passes through one-way platform geometry from below without obstruction.
  - Downward descent cleanly catches on the platform top ($y = \text{platform\_top} - \text{height}$, `vy = 0`, `is_grounded = True`).
  - Walking off platform edges transitions cleanly from grounded to airborne, initiating coyote time.
- **Fast Falls & Anti-Tunneling:** Verified by `test_fast_fall_does_not_tunnel_through_thin_floors`:
  - Dropping at maximum terminal fall velocity ($360\text{ px/s}$) onto a 1-tile thick ($16\text{ px}$) floor cleanly catches Mateo on top ($y = 128.0$) with zero floor tunneling.

### Check 3: Death returns to a valid checkpoint with coherent state
- **Hazard Interaction:** Stepping on `COLLISION_HAZARD` tiles applies 25 damage, sets $0.8\text{s}$ invulnerability timer, triggers knockback velocity ($-160\text{ px/s}$ vertical, $120\text{ px/s}$ horizontal), and renders flashing transparency.
- **Checkpoint & Pit Fall Recovery:** Verified by `test_death_and_checkpoint_recovery`:
  - Depleting health to 0 or falling out of bounds ($y > \text{room\_height}$) triggers death.
  - Respawn restores Mateo to the active checkpoint coordinates (or initial spawn if none active).
  - Coherent full state is restored: health $= 100$, velocity $= (0, 0)$, grounded $= \text{True}$, dead $= \text{False}$, invulnerability $= 0.0$, and timers cleared.

---

## 3. Visual Previews

| Screenshot | Description |
|---|---|
| `01_locomotion_ground_running.png` | Mateo in ground locomotion across the approach trench floor with HUD showing `[HP: 100]`. |
| `02_jump_arc_and_variable_height.png` | Mateo at apex of jump arc crossing over the catwalk platform. |
| `03_coyote_time_ledge_leap.png` | Mateo executing a coyote-time leap immediately after departing elevated runway ledge. |
| `04_one_way_platform_landing.png` | Mateo landed cleanly on top of one-way catwalk platform. |
| `05_hazard_damage_knockback_flash.png` | Mateo taking high-voltage electrical sump damage with invulnerability flash and knockback. |

All preview images are saved under `video_game/planning/evidence/A02/previews/` ($480 \times 270\text{ px}$).

---

## 4. Test Suite Execution & Quality Gates

```bash
/opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_player.py -vv
# Result: 11 passed in 0.06s

/opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_world.py -vv
# Result: 8 passed in 0.22s

/opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests tests -q
# Result: 170 passed in 19.51s

/opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_checkpoint_audit.py -vv
# Result: 3 passed in 0.11s (syntax, explicit imports, module headers, no line budget violations)

/opt/anaconda3/envs/6equj5_game/bin/python -m video_game.tools.build_assets --dry-run
# Result: 14/14 locked asset groups preserved
```

