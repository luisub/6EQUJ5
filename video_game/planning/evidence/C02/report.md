# Milestone 1 — Task C02 Evidence Report: Bunker Layers and Lighting Normalization

**Date:** 2026-11-10  
**Task ID:** C02  
**Resource Flag:** GPU_IMAGE  
**Status:** Complete and Verified  
**Rollback Snapshot:** `video_game/_trash/2026-11-10_C02_before_changes.tar.gz` (SHA-256: `3cf1dfbb61522a5207e0104024ac350fe0c2b248b62b54dfdd49f1c2d9dc797a`)

---

## 1. Executive Summary

Task C02 normalizes the Ohio Big Ear bunker 6-layer scene stack, completely eliminating the legacy `alpha = 254` context flag hack and its associated runtime pixel-mutation loader. All layers now adhere to standard explicit alpha contracts (opaque base, clean binary alpha masks, and smooth radial alpha falloff for light pools). The 16×16 modular tileset has been freed from artificial perimeter rectangle outlines, enabling seamless repetitive tile surfaces. The engine runtime and preview pipelines now composite scenes using standard alpha compositing in the intended depth order (distant structure → rear wall → equipment → floor → Mateo shadow + sprite → foreground props → lighting overlay).

---

## 2. Key Actions and Implementation Details

### 2.1 Eradication of Legacy Alpha-254 Context Flags
- **Previous State:** `bunker_scene_builder.py` filled inactive layer areas with dimmed context at `alpha = 254` and active regions at `alpha = 255`. At runtime, `assets.py` mutated Pygame surfaces using `pixels_alpha`: `alpha[alpha < 255] = 0` and `alpha[alpha == 255] = 38` (for lights).
- **Normalized Implementation:**
  - `01_distant_structure.png`: Deep cavern hull and primary structural steel girders rendered as a solid opaque base plate (`alpha = 255` everywhere, `unique_alphas = {255}`).
  - `02_rear_wall.png`: Rear acoustic baffling panels and high-voltage conduits rendered with explicit binary alpha (`col` at `alpha = 255` where `is_wall`, `(0, 0, 0, 0)` transparent elsewhere; `unique_alphas = {0, 255}`).
  - `03_equipment.png`: Server racks, terminal console desk, electronics workbench, and airlock door frame rendered with explicit binary alpha (`col` at `alpha = 255` where `is_equip`, `(0, 0, 0, 0)` transparent elsewhere; `unique_alphas = {0, 255}`).
  - `04_playable_floor.png`: Playable concrete bunker deck with floor expansion joints and conduit runs rendered with explicit binary alpha (`col` at `alpha = 255` where `is_floor`, `(0, 0, 0, 0)` transparent elsewhere; `unique_alphas = {0, 255}`).
  - `05_foreground_props.png`: Overhead HVAC ducts, hanging sensor wires, and doorway vignette framing rendered with explicit binary alpha (`col` at `alpha = 255` where `is_fg`, `(0, 0, 0, 0)` transparent elsewhere; `unique_alphas = {0, 255}`).
  - `06_lighting_overlay.png`: Dedicated lighting overlay with explicit `(0, 0, 0, 0)` transparent background and smooth radial alpha falloff:
    - CRT green phosphor bloom (`cx=208, cy=148`, peak alpha 48)
    - Workbench tube amber glow (`cx=324, cy=126`, peak alpha 54)
    - Server rack status indicator amber (`cx=70, cy=56`, peak alpha 42)
    - Overhead halogen pool (`cx=235, cy=14`, peak alpha 38)
    - Airlock door beacon red alert (`cx=444, cy=56`, peak alpha 58)
    - Smooth native alpha: `unique_alphas = 59`, min alpha 0, max alpha 58, 0 legacy 254 values.

### 2.2 Removal of Runtime Pixel-Array Mutation Hack
- In `video_game/engine/assets.py`:
  - Removed `pygame.surfarray.pixels_alpha(surface)` slicing hack.
  - Simplified `bunker_layers()`: Loads each layer directly via standard `self.image(Path("bunker") / name, (480, 270))`.
  - Zero runtime CPU cycles spent inspecting or mutating pixel alpha buffers.

### 2.3 Layer Ordering & Standard Compositing
- In `video_game/engine/scenes/bunker.py` and `bunker_scene_builder._render_bunker_previews`:
  - Enforced exact 7-step compositing order:
    1. `self.layers[:4]` (Z0 Distant Structure, Z1 Rear Wall, Z2 Equipment, Z3 Playable Floor)
    2. Player floor contact shadow (`pygame.draw.ellipse` / Pillow ellipse at `y=238`)
    3. Mateo animated sprite (`(mx, 122)`)
    4. `self.layers[4:]` (Z4 Foreground Props, Z5 Lighting Overlay)
  - Fixed layer index omission in `BunkerHubScene.render()` where `self.layers[0]` was previously skipped.

### 2.4 Modular Tileset Seam Elimination
- In `bunker_scene_builder._build_modular_tileset`:
  - Removed line drawing dark perimeter outline: `ImageDraw.Draw(tile).rectangle((0, 0, 15, 15), outline=(12, 18, 22, 255))`.
  - Extracted 32 authentic 16×16 tiles now repeat cleanly without visible borders, seams, or grid lines.

### 2.5 Flattened Inspection Previews
- Exported 6 flattened inspection previews under `video_game/assets/bunker/inspection/`:
  - `01_distant_structure_inspect.png`
  - `02_rear_wall_inspect.png`
  - `03_equipment_inspect.png`
  - `04_playable_floor_inspect.png`
  - `05_foreground_props_inspect.png`
  - `06_lighting_overlay_inspect.png`
- Each layer is composited over a 35% dimmed and desaturated room background (`Image.blend(rgb, gray, 0.70).point(lambda c: int(c * 0.35))`), providing immediate visual inspection of layer boundaries and occlusion.

### 2.6 Metadata & Provenance Manifest Enrichment
- `video_game/assets/bunker/scene_manifest.json`: Added `layer_metadata` recording `z_order` (0–5), `file`, `name`, `blend_mode: "alpha_composite"`, `alpha_type`, `role`, and human-readable descriptions.
- `video_game/assets/manifest.json`: Updated SHA-256 output hashes for normalized layers and tileset; added 6 inspection preview entries (now 66 tracked assets).

---

## 3. Verification and Evidence Files

| File | Path | Description |
| :--- | :--- | :--- |
| **Before / After Comparison** | [bunker_before_after_comparison.png](bunker_before_after_comparison.png) | Side-by-side comparison of baseline (alpha-254 hack) vs normalized (explicit alpha masks). |
| **All Layers Inspection Grid** | [all_layers_inspection_grid.png](all_layers_inspection_grid.png) | 2×3 composite grid showing all 6 layers over 35% dimmed background. |
| **Seamless Tile Grid** | [tile_seamless_repetition_grid.png](tile_seamless_repetition_grid.png) | 4× scaled 8×4 repeated tile layout demonstrating zero grid seams or border artifacts. |
| **CRT Off Native Capture** | [previews/pygame_live_480x270_crt_off.png](previews/pygame_live_480x270_crt_off.png) | Native 480×270 live Pygame engine capture with all 6 layers and Mateo shadow. |
| **CRT On Scaled Capture** | [previews/pygame_live_1440x810_crt_on.png](previews/pygame_live_1440x810_crt_on.png) | Integer-scaled 1440×810 live capture with scanlines and phosphor glow. |
| **Terminal Live Capture** | [previews/pygame_live_crt_terminal.png](previews/pygame_live_crt_terminal.png) | CRT receiver terminal showing FASR-001 signal lock. |

---

## 4. Automated Test Results

1. **Video Game Test Suite (`video_game/tests/`):**
   ```bash
   /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests -q
   ```
   **Result:** `89 passed in 4.43s` (includes 4 new regression tests in `test_assets.py`).

2. **Root Test Suite (`tests/`):**
   ```bash
   /opt/anaconda3/envs/6equj5_game/bin/python -m pytest tests -q
   ```
   **Result:** `20 passed in 0.01s`.

3. **Checkpoint Audit Suite (`test_checkpoint_audit.py`):**
   ```bash
   /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_checkpoint_audit.py -vv
   ```
   **Result:** `3 passed in 0.20s` (syntax headers, module boundaries, asset dimensions and locks).

4. **Transactional Replacement & Preservation Test:**
   ```bash
   /opt/anaconda3/envs/6equj5_game/bin/python -m video_game.tools.build_assets --dry-run
   ```
   **Result:** All locked groups preserved; zero unexpected modifications.

---

## 5. Acceptance Criteria Sign-Off

- [x] **Ordinary alpha compositing renders the scene correctly:** `Image.alpha_composite` in PIL and standard `blit` in Pygame render the room with correct layering, occlusion, and lighting.
- [x] **Each layer has documented blend behavior and clean boundaries:** Documented in `scene_manifest.json` (`layer_metadata`) and verified by inspection previews in `video_game/assets/bunker/inspection/`.
- [x] **CRT off/on captures meet the art rubric with visible floor contact and readable stations:** Verified in native and scaled captures; Mateo shadow grounds the character on the floor deck; equipment consoles and terminals remain crisp and legible.
- [x] **Zero visible grid seams on repeated tiles:** Verified on 8×4 repeated tile grid; border rectangle code removed.
- [x] **Rollback archive created and documented:** `video_game/_trash/2026-11-10_C02_before_changes.tar.gz` and `TRASH_LOG.md`.

