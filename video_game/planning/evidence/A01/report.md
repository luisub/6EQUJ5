# Milestone 2 — Task A01 Evidence Report: Load a Playable Room and Camera

**Date:** 2026-11-10  
**Task ID:** A01  
**Milestone:** 02_action_slice (Milestone 2: Complete Playable Act I)  
**Status:** Complete and Verified  
**Rollback Snapshot:** `video_game/_trash/2026-11-10_A01_before_changes.tar.gz` (SHA-256: `2cf0fcc036e618bf0016e43c44f26f1f32b85449fdbf7a84f3c6c088aad7f011`)  
**Manifest:** `video_game/_trash/2026-11-10_A01_before_changes_manifest.json`

---

## 1. Executive Summary

Task A01 establishes the foundational 2D world loading, camera viewport tracking, level blockout schema, collision system, and scene transitions for Milestone 2 (Act I Action Slice).

The approach level (`video_game/data/levels/act_01/approach.json`) provides a 60-tile wide ($960 \times 288\text{ px}$) outdoor access trench connecting the subterranean Big Ear bunker to the Ohio telescope dish array. The camera tracks Mateo smoothly within a $480 \times 270\text{ px}$ viewport, correctly handling the partial 14-pixel 17th tile row at the bottom edge, world boundary clamping, collision queries (solid, one-way, hazard, cover), and collision-free spawn and airlock exit points.

---

## 2. Acceptance Checks Verification

### Check 1: Room loads from data with actionable errors for invalid references
- **Implementation:** `Room.load_from_file()` and `validate_content.py` validate schema structure, collision grid dimensions ($H \times W$), layer lengths, exit/spawn references, and tile indices.
- **Actionable Errors:** Verified by `test_room_invalid_schema_raises_actionable_error` in `test_world.py`:
  - Missing required fields (e.g., `tile_size`, `layers`) raise clear `ValueError` detailing the missing field.
  - Inconsistent row lengths or dimensions raise precise `ValueError` reporting row indices and expected vs. actual lengths.
  - Spawns overlapping solid geometry raise `ValueError("Spawn point '...' collides with solid geometry")`.
  - Content validator CLI: `python -m video_game.tools.validate_content --all` validates all campaign levels with zero errors.

### Check 2: Viewport handles partial tiles and room edges correctly
- **Viewport Dimensions:** $480 \times 270\text{ px}$ canvas.
- **Tile Resolution:** $16 \times 16\text{ px}$.
- **Partial Tile Geometry:** Vertical span $270 / 16 = 16.875$ tiles. The 17th tile row rendered at the bottom viewport edge is a partial 14-pixel strip.
- **Verification:** Verified by `test_camera_clamping_and_partial_tile_rendering` in `test_world.py`:
  - `Camera.get_visible_tile_range(tile_size=16)` computes `max_row = min(world_h // 16, int((y + 270 + 15) // 16))` which correctly includes row 16 (the 17th row) without stretching or clipping.
  - Rendering tests verify that tile blits at $y \in [256, 269]$ render without throwing index errors or black seams.
  - Camera clamping clamps coordinates strictly to $[0, \text{world\_w} - 480]$ horizontally and $[0, \text{world\_h} - 270]$ vertically.

### Check 3: Player spawn and exit locations are collision-free
- **Level Spawns:**
  - `bunker_exit`: $(x=48.0, y=192.0)$ — Mateo's arrival spawn from bunker airlock.
  - `approach_checkpoint`: $(x=432.0, y=192.0)$ — Mid-point trench recovery.
  - `dish_perimeter`: $(x=816.0, y=192.0)$ — Telescope dish perimeter gate.
- **Exits & Checkpoints:**
  - Exit `exit_to_bunker`: $(x=16.0, y=176.0, w=32.0, h=48.0) \to$ `target_room: "bunker_hub"`, `target_spawn: "airlock_door"`.
  - Checkpoint 1: `approach_start` $(x=48.0, y=192.0)$.
  - Checkpoint 2: `approach_antenna_perimeter` $(x=816.0, y=192.0)$.
- **Verification:** Tested by `test_room_spawns_and_exits_are_collision_free` in `test_world.py`. Bounding boxes of all defined spawns and exit triggers have zero overlap with solid tiles.

### Check 4: Normal bunker navigation reaches the room
- **Normal Play Interaction:** Mateo walks to the far right of the bunker hub ($x \ge 350.0$) where the airlock door to the surface trench is located.
- **Interaction Prompt:** Context prompt displays `[E / ENTER] SURFACE ACCESS TRENCH (ACT I)`.
- **Navigation:** Pressing `K_RETURN` or `K_e` at the door triggers state transition to `STATE_FIELD_OPS` with room `act_01/approach.json` and spawn `bunker_exit`.
- **Return Route:** Pressing `K_RETURN` or `K_ESCAPE` at the trench airlock door ($x \le 48.0$) returns Mateo back to `STATE_BUNKER_HUB` with spawn `airlock_door`.
- **Verification:** Tested by `test_bunker_to_field_ops_normal_navigation` in `test_world.py`.

---

## 3. Visual Previews

| Screenshot | Description |
|---|---|
| `01_approach_room_overview_spawn.png` | Mateo spawned at bunker airlock exit ($x=48, y=192$) with parallax backdrop and airlock return prompt. |
| `02_traversal_platforms_and_catwalks.png` | Elevated catwalk platforms, one-way surfaces, and deep trench architecture ($x=240, y=160$). |
| `03_cover_blocks_and_hazard_sump.png` | Sandbag/concrete low cover blocks and high-voltage electrical sump pit ($x=464, y=192$). |
| `04_camera_tracking_and_partial_tile.png` | Smooth camera tracking at mid-level showing partial 14px 17th tile row rendered cleanly at bottom edge ($x=600, y=160$). |
| `05_checkpoint_activation_and_dish_approach.png` | Checkpoint activation at the perimeter antenna mast approaching the Big Ear dish ($x=816, y=192$). |

All preview images are saved under `video_game/planning/evidence/A01/previews/` ($480 \times 270\text{ px}$).

---

## 4. Test Suite Execution & Quality Gates

```bash
/opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests tests -q
# Result: 159 passed in 15.66s

/opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_checkpoint_audit.py -vv
# Result: 3 passed in 0.12s (headers, syntax, zero wildcard imports, no line budget violations)

/opt/anaconda3/envs/6equj5_game/bin/python -m video_game.tools.build_assets --dry-run
# Result: 14/14 locked asset groups preserved
```

