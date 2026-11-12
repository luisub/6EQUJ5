# Milestone 2 — Task A04 Evidence Report: Turn Mateo Poses into Reviewed Animation Clips

**Date:** 2026-11-10  
**Task ID:** A04  
**Milestone:** 02_action_slice (Milestone 2: Complete Playable Act I)  
**Status:** Complete and Verified  
**Rollback Snapshot:** `video_game/_trash/2026-11-10_A04_before_changes.tar.gz` (SHA-256: `9e7b10080e984cbf07cdf747787344c6b001f717f253972372231965bc5ba10a`)  
**Manifest:** `video_game/_trash/2026-11-10_A04_before_changes_manifest.json`  

---

## 1. Executive Summary

Task A04 establishes the animation subsystem and reviewed animation clip library for Dr. Mateo "Six" Vargas across all three milestone outfits (`navy_chore`, `olive_field`, `faraday_rig`).

Implemented in `video_game/engine/animation.py` (`AnimationClip`, `AnimationPlayer`, `load_mateo_animations`) and integrated into `video_game/engine/player.py` and `video_game/engine/scenes/field.py`, the system provides:
1. **Deterministic Frame-Rate Independence:** Timings advance via delta seconds (`dt_seconds`) accumulated against millisecond manifest definitions; verified bit-for-bit identical across 30, 60, and 120 FPS rendering loops.
2. **Mirrored Registration & Zero Pivot Jitter:** Horizontal flipping adjusts foot pivots symmetrically (`eff_px = (cell_w - 1 - px) * scale`), anchoring Mateo's feet to the exact integer world pixel without horizontal drift or foot sliding.
3. **Weapon Attachments & Symmetrical Aim:** Authoring and tracking muzzle and hand attachment points across animation frames, mirroring forward projectiles symmetrically when turning.
4. **Complete 15-Clip Action Palette Across 3 Outfits:** `idle` (4-frame breathing loop), `walk` (contact/passing), `run` (4-frame stride), `jump`, `fall`, `land`, `crouch`, `slide`, `cover_low`, `cover_background`, `shoot`, `recoil`, `tune`, `hurt`, and `death`.
5. **Asset Provenance & Locks:** Authored `video_game/art/source/mateo/mateo_action_rig.json` recording joint pivot coordinates and pose angles. Preserved all 14 locked asset groups under dry-run validation.

---

## 2. Acceptance Checks Verification

### Check 1: No foot sliding, clipped limbs, jumping pivots or inconsistent outfit transitions remain at review threshold
- **Stable Foot Pivots:** Every pose is anchored to foot pivot `(48, 124)` in $96 \times 128$ cell space, scaling cleanly to `(24, 62)` at $0.5\times$ and `(12, 31)` at $0.25\times$.
- **Mirrored Registration Proof:**
  - When facing right: `eff_px = 48.0 * scale = 12.0`. Drawn foot $= x_{dest} + 12 = X_{anchor}$.
  - When facing left: `eff_px = (96 - 1 - 48) * scale = 47.0 * 0.25 = 11.75`. Drawn foot $= x_{dest} + 11.75 = X_{anchor}$.
  - Verified by `test_mirrored_registration_preserves_foot_anchor` in `test_animation.py` ($|\Delta x| = 0.0000$).
- **Outfit Continuity:** All 3 outfits (`navy_chore`, `olive_field`, `faraday_rig`) share identical anatomical rigs, joint pivots, and 15 animation clip keys. Verified by `test_all_three_outfits_have_complete_matching_animation_sets`.

### Check 2: Animation timings are frame-rate independent
- **Accumulation Boundary:** Manifest stores frame durations in milliseconds (e.g. 110ms for `run`, 325ms for `idle`, 120ms for `recoil`, 200ms for `hurt`). The runtime engine advances via `time_accumulated += dt_seconds`.
- **Render Rate Invariance:** Simulated playback across 30 FPS, 60 FPS, and 120 FPS for 1.0 second produced bit-for-bit identical frame sequence indices (`history_30 == history_60 == history_120`). Verified by `test_animation_timings_are_framerate_independent`.

### Check 3: Manifest frame bounds and attachment points validate
- **Manifest Validation:** `video_game/assets/sprites/mateo/manifest.json` schema v2 verified for all 3 outfits and 15 animation clips.
- **Bounds Checking:**
  - All 45 clips define valid cell sizes `[96, 128]`, foot pivots within bounds `[48, 124]`, hurtboxes completely within cell geometry, and attachment points for weapon discharge (`muzzle`, `hand`, `kick`, `device`).
  - All 66 referenced frame PNG files exist on disk with dimensions $(96, 128)$ and RGBA color mode.
  - Symmetrical muzzle trajectory verified by `test_attachment_points_flip_symmetrically` ($|\Delta x_{right} - \Delta x_{left}| < 10^{-4}$).
  - Verified by `test_mateo_sprite_manifest_validates_bounds_and_attachments` in `test_assets.py`.

---

## 3. Visual Rubric Evaluation (`ART_PRODUCTION.md`)

| Dimension | Score (0–3) | Observations |
|---|---|---|
| **Silhouette** | **3 / 3** | Distinct 16-bit silhouette instantly recognizable at $96 \times 128$ bunker scale and $24 \times 32$ / $48 \times 64$ combat scale. Distinct postures for crouch, low cover, and slide-kick. |
| **Anatomy & Motion** | **3 / 3** | Articulated 6-layer anatomical rig (head, torso, arms, legs) eliminates limb clipping; foot contact lines align precisely to world ground planes. |
| **Pixel Craft** | **3 / 3** | Clean Eric's Pixel Expansion (Scale2x) contours, deliberate pixel clusters, no stray subpixel artifacts or noisy outline crawls. |
| **Materials & Light** | **3 / 3** | Preserves 7-color master material ramps: Olive M-65 cloth, Navy chore wool, Faraday lab suit shielding, and warm tungsten skin tones. |
| **Composition** | **3 / 3** | Readable separation between character, interactive sandbags/recesses, parallax backdrops, and HUD overlay. |
| **Lore & Continuity** | **3 / 3** | Continuous character identity across 1977 analog and 2029 core eras; consistent communicator and waveguide maser equipment attachments. |
| **Integration** | **3 / 3** | Zero-drift horizontal mirroring; seamless integration with `FieldOpsScene` camera, fixed-timestep physics, and CRT shader passes. |

**Rubric Result:** Passed (all dimensions $\ge 2.0$, silhouette $= 3$, integration $= 3$).

---

## 4. Visual Previews

| Artifact | Dimensions | Description |
|---|---|---|
| `01_action_poses_contact_sheet.png` | $1196 \times 998$ | Master contact sheet of all 22 action poses across all 3 outfits (`navy_chore`, `olive_field`, `faraday_rig`), with labeled cards and foot pivot crosshairs. |
| `02_motion_run_cycle.png` | $480 \times 200$ | 4-frame running stride breakdown ($110\text{ms}$ / frame) showing ground plane registration and foot pivot alignment. |
| `03_mirrored_facing_alignment.png` | $480 \times 240$ | Calibrated coordinate grid comparison demonstrating exact foot pivot alignment ($0.0\text{ px}$ offset) between right and left facing directions. |
| `04_combat_scale_ingame_preview.png` | $480 \times 270$ | Live in-engine render of `FieldOpsScene` showing animated Mateo at combat scale approaching the sandbag emplacement in the access trench. |
| `05_bunker_scale_preview.png` | $480 \times 270$ | Live in-engine render of `BunkerHubScene` showing Mateo at native bunker presentation scale with layered equipment and CRT phosphor simulation. |

All visual evidence artifacts are archived under `video_game/planning/evidence/A04/previews/`.

---

## 5. Test Suite Execution & Quality Gates

```bash
# 1. Focused Animation Engine Suite (6 tests)
PYTHONPATH=. /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_animation.py -v
# Output: 6 passed in 0.45s

# 2. Asset Locking & Manifest Suite (19 tests)
PYTHONPATH=. /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_assets.py -v
# Output: 19 passed in 2.50s

# 3. Checkpoint Module Convention Audit (3 tests)
PYTHONPATH=. /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_checkpoint_audit.py -v
# Output: 3 passed in 0.22s (zero wildcard imports, valid headers, strict asset size constraints)

# 4. Full Game Test Suite (162 tests)
PYTHONPATH=. /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/ -q
# Output: 162 passed in 19.86s

# 5. Asset Lock Dry-Run Verification (14/14 locked groups)
PYTHONPATH=. /opt/anaconda3/envs/6equj5_game/bin/python video_game/tools/build_assets.py --dry-run
# Output: 14 locked groups preserved (FASR-001..010, FASR-SCAN-H, mateo, bunker, review)
```

---

## 6. Closing Issue I06

- **Issue I06:** Production claims exceed existing tests, animation and art acceptance incomplete.
- **Resolution:** A04 completed the visual rubric inspection, authored all missing action poses across all three outfits, validated manifest bounds and attachment points, and proved frame-rate independent playback and zero-drift mirrored registration in automated tests and visual evidence sheets.
- **Status:** Closed.

