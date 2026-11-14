# Ohio approach + Mateo benchmark — v0.2 for approval

**Status: proposed; orchestrator approval required before artwork starts.** Supersedes v0.1. One static environment composition, then one static Mateo olive-field standing pose. The selected candidate grid is **960×540 only**; the existing 480×270 capture is the baseline. Do not create an improved 480 candidate, animation, additional rooms, asset collection or runtime changes. Generate the environment first, review it with the orchestrator, then have the same artist make the one pose. This is a visual benchmark, not a shipping asset or gate acceptance.

## Purpose and references

Give the Ohio Big Ear access trench an authored, lived-in radio-observatory identity at twilight. The mood is tense and quiet before contact: a working science facility under strain. HUNTDOWN is the primary reference for purposeful pixel clusters, material separation, readable cover and clear action staging; Kingdom informs layered atmospheric depth, and Star Renegades informs restrained localized color and light. Borrow relationships, not characters, buildings, exact compositions or palettes. See `src/art/references/design_reference_notes.md` for sources and limits.

Direct inspection of `assets/environments/ohio/bg_ohio_dish_lattice.png`, `assets/sprites/mateo/olive_field/idle_1.png`, the Mateo concept, and the actual settled capture below shows repetitive, high-density dish lattice dominating much of the frame, repeated diagonal floor marks and compressed blue-green materials. Mateo's small head, hands, jacket and legs are difficult to separate. Preserve the recognizable radio-array premise, but simplify and group distant structure, distinguish material planes and keep a quiet action corridor. These are observations, not claimed review scores.

## Locked registration

Baseline: `_trash/2026-11-13_separation/historical-reviews/art/reviews/visual_upgrade/previews/ohio_runtime_v01/approach_settled_native.png`; environment-only capture: `approach_environment_only_native.png`; capture metadata: `settled_context.json` in the same folder. It is a dummy-driver offscreen direct-entry fixture, fresh game, 30 updates at 1/60 second, no played progression, CRT off. Weather phase can differ between captures. It is an exact visual registration reference for this static instant, not human-playthrough evidence.

The room is 960×288 world units. Camera origin **(0,18)**; visible world rectangle **(0,18,480,270)**. The high canvas maps each world unit to **2×2 candidate pixels**: screen `(x,y) = (2×world_x, 2×(world_y−18))`. No pan, zoom, expanded FOV, alternative room layout or apparent player-size change. Baseline player collision rectangle is `(48,208,16,32)` world, foot `(56,240)` world / `(56,222)` baseline screen / **(112,444)** high screen. Baseline idle cell is 24×32 at `(44,191)`; high cell is **48×64 at (88,382)**. Existing visible alpha bounds baseline `(50,193,12,29)` become **(100,386,24,58)** high; preserve this overall apparent silhouette scale and foot contact, allowing deliberate contour refinement. Existing source 96×128 cell is scaled to one-quarter in the current runtime; it is not the displayed cell.

The clean environment does not include Mateo, HUD, enemies, bullets or telegraphs. For a review composite add the one new pose, and present the unchanged original HUD/other captured actors as a faithful overlay if technically separable; if not, show the clean composite beside the unchanged baseline and explicitly disclose the missing overlay rather than paint substitute HUD or claim equivalence. Top HUD occupies baseline `(0,0,480,16)` plus separator at y=16; bottom HUD `(0,254,480,16)`; status begins at `(8,19)` and `(8,27)`, equipment text at `(8,240)`; conditional prompts, telegraphs and other states can occupy more. Double these coordinates for the high candidate. Preserve low-detail, low-contrast background under these zones and around the player and action lanes. Do not repaint, resize or reflow HUD.

### Geometry that must remain legible

Use the baseline/environment-only capture as the visual authority and these collision extents for alignment. Coordinates below are world units, with ends exclusive; apply the mapping above. Never decorate a region as a different collision surface, place cover where there is none, move a platform, hide a lip, or invent a new hazard/exit. In this crop:

| Actual feature | World-space extent / location | High-screen guide |
|---|---|---|
| Airlock return exit | `(16,176,32,48)` | `(32,316,64,96)` |
| Airlock terminal | `(32,192,16,32)` | `(64,348,32,64)` |
| Background recess cover | `(160,176,32,48)` | `(320,316,64,96)` |
| Low sandbag cover | `(384,192,32,32)` | `(768,348,64,64)` |
| Warning sign | `(310,208,16,16)` | `(620,380,32,32)` |
| One-way platforms | x=160–272 at y=192; x=304–400 at y=208; x=448–480 at y=176 | x=320–544 at y=348; x=608–800 at y=380; x=896–960 at y=316 |
| Ground and sump | ground y=240 over x=0–320 and x=384–480; sump x=320–384 at y=256 | ground top y=444; gap x=640–768; sump top y=476 |

Ground continues below the view's lower boundary. The room also has collision value 4 at world x=128–144 and x=416–432, y=224–240; preserve what the capture actually renders there. The selected crop excludes the farther barrier, mast and salvage-yard exit. Existing terminal labels, checkpoint and HUD remain runtime elements, not invented environmental paint.

## Composition and craft

- **Far:** subdued twilight sky, Ohio tree silhouettes and an open, recognizable suggestion of the massive radio structure; group trusses into a few structural silhouettes and suppress repetitive dense wire mesh in the action zone.
- **Middle:** fence and trench wall give scale and layers. Selectively define steel joints, service conduit and weathering with intentional spacing, preserving clear differentiation from the play plane. Avoid parallel bright diagonals that mimic platform boundaries.
- **Gameplay:** concrete lips and one-way grating communicate their real edges; the sump and sign are unmistakable without expanding their danger area. Preserve the actual airlock, recessed cover and sandbag positions. Concrete uses broad chips/joints, steel uses crisp thin members and controlled highlights, sandbags read as soft bulk, earth as irregular mass. Keep the player silhouette and projectiles readable against them.
- **Foreground:** restrained at margins/below the walking surface; nothing masks feet, cover, warnings, interfaces or traversal edges. Do not add an opaque foreground veil.
- **Light and color:** cool twilight ambient and a modest motivated warm utility accent, with coherent direction. Use `src/art/source/environments/ohio/ohio_materials_and_palettes.json` as starting language; increase separation of sky, distant structure and gameplay planes. Reserve strongest accents for actual game cues and actors; avoid wall-to-wall glow, repetitive scratches or noise. No water reflection unless present in the actual room.

This is **new authored 960×540 detail**, not enlarged existing art, an enlarged 480 candidate, procedural substitute, filter, blanket noise or sharpening. A detailed master may be used if the export is deliberately cleaned and inspected at 960×540. Show material transitions, selected joints and depth-specific shapes that genuinely use the denser grid while preserving the baseline geometry and visual hierarchy.

## One Mateo pose — after environment review

Draw one transparent **48×64** standing idle cell, facing right. Dr. Mateo “Six” Vargas retains the existing concept's short dark hair, medium-brown skin, stubble, sturdy adult proportions, olive M-65 jacket with pockets and rolled sleeves, dark/khaki cargo trousers and boots, shoulder strap, neck headset and belt radio where readable. He is an alert scientist, not a new character or an enlarged hero. Match the pose and footprint above: planted feet at the established contact line, distinct head/shoulders/arms/coat hem/legs/boots, no hands hidden by decorative detail. Preserve recognizable equipment only where it reads at this footprint. Existing idle does not hold a prominently visible weapon; do not invent one. No animation, alternate poses or separate equipment collection.

## Exports and alpha

Write only to a new versioned review directory; never overwrite current runtime assets or masters. Exact filenames and dimensions for the benchmark:

| File | Canvas | Contents |
|---|---:|---|
| `ohio_approach_environment_high_960x540.png` | 960×540 | Opaque clean environment, registered to baseline; no character, HUD or actors. |
| `mateo_olive_stand_high_48x64.png` | 48×64 | One right-facing RGBA standing cell; high-screen origin `(88,382)`, foot `(112,444)`. |
| `ohio_approach_candidate_native_960x540.png` | 960×540 | Environment + pose at registered position; add faithful unchanged HUD/actors only if separable and document what was added. |
| `ohio_approach_candidate_review_1920x1080.png` | 1920×1080 | Exact nearest-neighbor 2× of candidate native composite. |
| `ohio_approach_baseline_review_1920x1080.png` | 1920×1080 | Exact nearest-neighbor 4× of unchanged settled baseline capture. |
| `source/` and `provenance.md` | Master dimensions documented | Editable master if available, source/tool/settings, draw and cleanup steps, exact files, hashes and review status. |

Preferred master has registered far, middle, gameplay and foreground layers, each 960×540 with common origin, straight/unassociated alpha and transparent pixels beyond their shapes; opaque sky/base fills the frame. If this cannot be produced faithfully, a **single flattened opaque plate** is acceptable for this static visual benchmark only. Record that choice: it does not demonstrate separable layers, parallax, layer occlusion or production readiness, and cannot be used to infer those outcomes. Preserve original source/master; no runtime edit or packaging. This crop has **no repeat guarantee**: do not tile it across the room. There are no commissioned scroll ranges or parallax ratios; existing manifest and room values differ, so implementation requires a separate technical design and seam tests.

## Review sequence and limits

1. Review the 960×540 environment first against the baseline and measured geometry, with the existing player footprint and HUD zones indicated. Fix wrong platform/sump/cover placement or unreadable edges before authoring Mateo.
2. Review the one pose at 48×64 native and in the registered environment; check alpha on light/dark grounds, foot placement and readability at its actual on-screen size.
3. Compare unchanged 480 baseline and 960 candidate at native size and each at 1920×1080 using the specified integer scaling; record source grids, bounds, overlays, method, hashes and concrete defects. Judge whether newly authored detail improves material and depth at equal framing. Do not call static inspection an animation, parallax, CRT-on, camera-travel, fairness, human-playthrough or performance test.
4. Apply the project's visual rubric only after actual inspection: every applicable criterion ≥2 and silhouette/integration 3 are the eventual art-gate threshold. No scores are claimed here. This benchmark alone does not establish full integration or G2/G3 acceptance.
