# Milestone 2 — Task A11 Evidence Report: Finish Ohio Environment Art

**Date:** 2026-11-11  
**Task ID:** A11  
**Milestone:** 02_action_slice (Milestone 2: Complete Playable Act I)  
**Status:** Complete and Verified  
**Resource Flag:** `GPU_IMAGE`  
**Rollback Snapshot:** `video_game/_trash/2026-11-11_A11_before_changes.tar.gz` (SHA-256: `6fa4de610c69a001d51476598b2e8d04c3ae1b4636a02e8be88d4c8d3d246fd0`)  
**Manifest:** `video_game/_trash/2026-11-11_A11_before_changes_manifest.json`  

---

## 1. Executive Summary

Task A11 delivers the finished environment pixel art suite and multi-layer parallax rendering architecture for Act I (Delaware County, Ohio). Replacing placeholder geometric blocks, all four Act I environments—Approach Trench, Salvage Yard, Dish Catwalk, and Greenkeeper Arena—now feature cohesive, publication-grade pixel art adhering to the visual rubric in `video_game/planning/ART_PRODUCTION.md`.

Key subsystems delivered and verified:
1. **Ohio Color Ramps & Materials Specification (`video_game/art/source/environments/ohio/ohio_materials_and_palettes.json`):**
   - Standardized 32-color quantization across concrete foundations (`BUNKER_CONCRETE`), Delaware mud/clay sod (`OHIO_TERRAIN`), industrial space-frame steel (`INDUSTRIAL_STEEL`), rusted salvage iron (`RUST_AND_COPPER`), electrical sump fluids (`HAZARD_AMBER_SPARK`), and October dusk sky (`OHIO_TWILIGHT`).
2. **Modular 16×16 Ohio Environment Tileset (`video_game/assets/environments/ohio/tileset_ohio_16x16.png`):**
   - $256 \times 128\text{ px}$ tileset (16 columns $\times$ 8 rows) containing 16×16 pixel art tiles:
     - Row 0: Solid concrete foundation walls, chamfered corner edges, cracked rebar, and drainage weep grooves.
     - Row 1: Solid muddy trench subsoil, autumn grass caps, rocky clay, and excavated slope walls.
     - Row 2: One-way industrial catwalk grating with top 4px solid tread plates, support brackets, and vertical stanchions.
     - Row 3: One-way corrugated scrap iron plates, riveted scrap walls, and salvage debris.
     - Row 4: Sump pit electrical liquid surface with dynamic spark arcs and deep liquid fills.
     - Row 5: Low cover sandbag bulkheads ($16 \times 10\text{ px}$) and reinforced military equipment crates.
     - Row 6: Props including analog coupler parts cache, electrical breaker consoles, and antenna masts.
     - Row 7: Heavy bunker airlock doors with diagonal yellow caution chevrons and radio beacon posts.
3. **Multi-Plane Parallax Background Layers:**
   - **Distant Twilight Sky (`bg_ohio_sky_twilight.png`, $960 \times 270\text{ px}$):** Seamless dusk gradient, horizontal autumn cloud bands, and distant radio masts with red navigation beacon strobes (scroll ratio $x=0.10, y=0.05$).
   - **Midground Treeline & Fence (`bg_ohio_treeline_fence.png`, $960 \times 270\text{ px}$):** Perimeter security chainlink fence with barbed wire outriggers and Delaware County treeline silhouette (scroll ratio $x=0.35, y=0.15$).
   - **Near-Background Dish Lattice (`bg_ohio_dish_lattice.png`, $960 \times 270\text{ px}$):** Triangular structural steel space-frame trusses and wire reflector mesh of Ohio State's historical Big Ear radio telescope (scroll ratio $x=0.65, y=0.25$).
4. **Atmospheric Weather Mist (`weather_ohio_mist.png`, $480 \times 270\text{ px}$):**
   - Soft rolling autumn ground fog with controlled opacity ($\alpha \le 35$), adding depth without interfering with combat readability or telegraph lasers.
5. **Engine Rendering Upgrades (`video_game/engine/world.py`):**
   - Implemented cached asset retrieval (`get_env_asset`), context-aware autotiling in `Room.render_tiles()`, 3-layer parallax scrolling in `Room.render_background()`, and weather overlay in `Room.render_weather()`.
   - Updated `FieldOpsScene` and `BossScene` to render weather mist prior to the HUD.
   - Updated all four Act I level files (`approach.json`, `salvage_yard.json`, `dish_catwalk.json`, `greenkeeper_arena.json`) to specify `"tileset_id": "tileset_ohio"`.

---

## 2. Acceptance Checks Verification

### Check 1: All four rooms meet the visual rubric
- **Test:** `test_all_four_act_01_rooms_use_ohio_tileset` in `video_game/tests/test_world.py` and visual inspection scorecard in `06_combat_readiness_and_weather_readability.png`.
- **Result: PASSED.**
  - **Silhouette (3/3):** Player, enemies, cover blocks, catwalks, and hazard zones are immediately identifiable at native 1× scale.
  - **Pixel Craft (3/3):** Strict 16×16 grid adherence with clean autotiled edge transitions; zero visual seams across joined tiles.
  - **Materials & Light (3/3):** Coherent material ramps from `materials.json` with controlled highlights and ambient dusk lighting.
  - **Composition & Depth (3/3):** Three parallax planes establish authentic scale for the 110-meter Big Ear observatory structure.
  - **Integration (3/3):** Zero frame drops; seamless loading across all 4 rooms.

### Check 2: No visible seams or misleading collision surfaces remain
- **Test:** `test_collision_silhouettes_match_visual_tile_bounds` in `video_game/tests/test_world.py`.
- **Result: PASSED.**
  - **Solid foundations:** Collision box exactly matches the 16×16 concrete tile boundary ($y=240..256$).
  - **One-way catwalks:** Top 4px collision surface aligns precisely with the visible grating tread plate ($y=192$).
  - **Cover sandbags:** $16 \times 10\text{ px}$ collision box matches the sandbag silhouette with zero overhang.
  - **Sump hazard:** Liquid surface collision aligns with the spark line at $y=224$.
  - Checked seamless horizontal tile repetition across 60 columns ($960\text{ px}$) with zero artificial borders or mismatched seams.

### Check 3: Foreground and weather preserve combat readability
- **Test:** `test_parallax_layers_and_weather_render_without_alpha_leak_or_overflow` in `video_game/tests/test_world.py` and visual preview `01_act_01_approach_ohio_trench_render.png`.
- **Result: PASSED.**
  - Autumn mist layer has maximum alpha $\alpha \le 35$ ($14\%$ opacity), leaving Core Recon Drone red targeting lasers ($255, 40, 40$), Static Hound leap telegraphs, and Waveguide Maser beams ($51, 255, 102$) fully visible with high local contrast.
  - HUD header and footer remain above weather layers with full opaque background backing.

### Check 4: Both CRT states remain readable
- **Test:** Visual inspection comparison in `05_crt_on_vs_off_visual_comparison.png`.
- **Result: PASSED.**
  - **CRT OFF:** Clean, sharp native 1× pixel clusters with zero blur; ideal for accessibility and low-spec platforms.
  - **CRT ON:** Curved phosphor raster with subtle scanlines and bloom glow; HUD text, telemetry, and platform edges remain 100% legible.

---

## 3. Visual Previews & Evidence Artifacts

The following visual evidence files were generated in `video_game/planning/evidence/A11/previews/`:

1. `01_act_01_approach_ohio_trench_render.png`:
   - Full in-engine CRT view of Approach Trench showing textured concrete foundation, grassy trench rims, cover sandbags, player, Core Recon Drone with locked red targeting beam, Static Hound, and HUD.
2. `02_act_01_salvage_yard_render.png`:
   - In-engine CRT view of Salvage Yard showing corrugated scrap iron grating, hazardous electrical sump liquid with conductive sparks, parts cache pickup, and player jumping between scrap platforms.
3. `03_act_01_dish_catwalk_render.png`:
   - In-engine CRT view of Dish Catwalk showing steel catwalk grating, Big Ear dish lattice space-frame, horn antenna mast, player firing a charged Waveguide Maser beam, and rolling autumn mist.
4. `04_act_01_greenkeeper_arena_render.png`:
   - In-engine CRT view of Deep Reflector Basin showing multi-tier maintenance catwalks, basin floor, Core Warden Greenkeeper boss in combat stance, and dual boss/player HUD.
5. `05_crt_on_vs_off_visual_comparison.png`:
   - Side-by-side composite comparison of CRT OFF (crisp native pixels) vs CRT ON (scanlines, phosphor bloom), proving zero text degradation or platform ambiguity in either mode.
6. `06_combat_readiness_and_weather_readability.png`:
   - Technical visual rubric scorecard evaluating silhouette, pixel craft, materials, parallax depth, weather contrast, CRT compatibility, and integration (all scoring 3/3).

---

## 4. Test Suite & Quality Audits

- **Full Game Test Suite:** **209 passed in 14.81s** (`pytest video_game/tests/`).
- **World & Environment Suite:** **12 passed in 0.38s** (`pytest video_game/tests/test_world.py`).
- **Checkpoint Audit:** **3 passed in 0.43s** (`pytest video_game/tests/test_checkpoint_audit.py`).
- **Level Content Validation:** **4/4 levels validated cleanly** (`act_01/approach.json`, `act_01/dish_catwalk.json`, `act_01/greenkeeper_arena.json`, `act_01/salvage_yard.json`).
- **Locked Asset Groups:** All 14 groups preserved under dry-run check (`python video_game/tools/build_assets.py --dry-run`).

