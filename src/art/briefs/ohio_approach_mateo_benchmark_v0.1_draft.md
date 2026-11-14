# Ohio approach + Mateo visual benchmark — v0.1 DRAFT

**Status: direction draft; not approved for production.** One static Ohio approach composition and one standing olive-field Mateo pose. Exact camera, displayed player footprint, HUD bounds and baseline capture must be supplied by the technical owner and entered in a new version before the orchestrator approves an artist to begin. This is an art comparison, not a runtime integration, animation commission, biome set or replacement of locked assets.

## Purpose and evidence

Make the first Ohio Big Ear approach feel like a specific, inhabited radio-observatory perimeter at twilight, with readable traversal and a strong human focal point. Mood: tense, weathered, quiet before contact; a working science facility under strain, not generic ruins. HUNTDOWN is the primary visual ambition for authored pixel clusters, material separation, clear staging and confident light; use Kingdom as a secondary prompt for layered atmospheric depth and Star Renegades for selective colored light. Translate principles into this game's identity; do not copy characters, architecture or compositions.

Directly inspected: `assets/environments/ohio/bg_ohio_dish_lattice.png`, `assets/sprites/mateo/olive_field/idle_1.png`, `src/art/source/mateo/concept_mateo_idle_1794333616733.jpg`, and historical `planning/evidence/A11/previews/01_act_01_approach_ohio_trench_render.png` and `planning/evidence/A01/previews/01_approach_room_overview_spawn.png`. These previews are historical illustrations, not a verified current camera capture. The dish asset has dense uniform mesh, highly repeated trusses and masts; in the A11 image the pattern competes with the action corridor, while repeated diagonal floor marks and dark blue/green planes give few material or depth cues. In the existing pose, head, hands, coat, trouser and boot shapes become hard to separate at field scale. Inspect the current runtime capture before judging exactly where these weaknesses appear today. Historical scores are not treated as present review results.

## Fixed composition and scene grammar

Use the technical owner's one current Ohio approach capture as the registration template: exactly the same camera position, field of view, world-to-screen scale, visible terrain/platform/collision geometry, player world/screen position and footprint, and HUD coverage. Both candidates depict that *same instant*: no cinematic zoom, extra horizon, shifted foreground, different character size, or altered UI. Do not infer the screenshot from the older previews. The room is 60×18 tiles at 16 world units per tile; these world coordinates are context, not a substitute for the supplied camera crop. Show only room features actually inside that crop.

- **Far:** dusk sky, restrained Ohio treeline, and only as much of the large radio reflector/structure as the current framing permits. Let a few readable structural masses imply scale; avoid a wall of evenly spaced mesh. Keep a relatively quiet value behind HUD and any high-action lane.
- **Middle:** perimeter fence, trench wall and selected industrial utility silhouettes. Separate fence, weathered concrete and steel by shape and value, not indiscriminate bright edges. A few anchored cables, fasteners and service marks tell use and age; spacing should be irregular and intentional.
- **Gameplay:** reproduce the current capture's walkable surfaces, one-way platform extents, edges and visible object silhouettes at their actual locations. Preserve legible cover, exits and interactions; never paint decorative cover where no cover exists. `approach.json` defines an airlock console at (32,192), background recess cover at (160,176), sump warning at (310,208), low cover at (384,192), training barrier at (512,192), checkpoint near (480,192), mast at (576,80), exits at (16,176) and (912,192). These positions are world units; draw only the features that the selected crop actually exposes. Match the real geometry and the technician's capture; do not invent pickups, enemies or hazards.
- **Foreground:** restrained framing at margins or below the walking plane, leaving feet, platform edges, hazards and interaction markers unobscured. No high-contrast screen-crossing foreground pattern, opaque veil or simulated HUD.
- **Lighting/materials:** cool twilight ambient with a directional, modest warm utility accent; choose one coherent light direction, make the character separate from the background, reserve highest contrast for the player, playable edges, hazards and real interaction cues. Concrete should read heavy and jointed, steel as thin hard-edged members, canvas as soft bulk, clay/sod as fractured organic masses. Rust, copper and amber warnings are accents rather than a field of orange pixels. Use the established ramps in `src/art/source/environments/ohio/ohio_materials_and_palettes.json` as a starting language, not a requirement to retain current muddy values. No blanket noise, bloom or gradient/filter pass standing in for drawn material detail.
- **Action and HUD quiet zones:** determine exact rectangles from the supplied baseline. Keep the pixels underneath existing text, bars, prompts and telegraphs low-detail and comparatively low-contrast. Leave open space around the actual player, expected projectile corridor, platform edges, hazard edge and exits. Existing runtime HUD should be overlaid unchanged only in the registered review preview; it is not baked into the clean environment artwork.

## Mateo: one standing pose

Dr. Mateo “Six” Vargas in the established 1977 olive M-65 field outfit, facing the same direction and occupying the same screen footprint as the baseline. Match the existing identity and proportions: short dark hair, medium-brown skin, stubble, sturdy adult build; olive field jacket with pockets and rolled sleeves, dark cargo trousers and boots. Preserve the concept's shoulder strap, neck headset and belt radio as scale permits; do not enlarge him to display details. One grounded, alert standing pose with arms and hands understandable and both feet planted, matching the established neutral idle rather than inventing a new combat action. At the small grid prioritize head/torso/limbs, jacket silhouette and boots; put tiny equipment accents only where they survive. Do not add a prominently held weapon if the baseline idle lacks one. Transparent subject, no magenta background, halo or shadow baked beyond the agreed footprint. No additional poses, expressions, strips or motion.

The existing manifest's 96×128 source cell and foot pivot (48,124), and production guidance's 48×64 combat cell and initial pivot (24,62), are source conventions, **not proof of displayed runtime size**. The technical owner must specify source cell, actual displayed bounds and foot baseline in the next version. Do not assume an attachment point outside the cell is visible.

## Two separately judged grids; one composition

Low is a deliberately crafted **480×270** native scene. High is a separately crafted **960×540** native scene with identical world content and geometry at exactly double coordinate scale. High must add authored, meaningful detail at its own grid: e.g. recognizable material transitions, selected structural joints, controlled light and more specific clothing/equipment forms that cannot be made by nearest-neighbor enlargement of low. Maintain the same hierarchy and silhouette, not different staging, denser visual noise or arbitrary pixel texture. A detailed master may be used if both exports are deliberately drawn/cleaned and inspected at their respective native grids. Upscaling old assets, upscaling the low candidate as the high candidate, procedural substitutes, filters and noise are not finished art.

## Required deliverables and boundaries — draft filenames

Write only new candidate files into a versioned review directory, not `assets/` or existing masters. Dimensions below are canvas dimensions; final sprite cell dimensions and exact placement still require technical confirmation. Names and dimensions are the proposed contract for approval:

| File | Size | Content |
|---|---:|---|
| `ohio_approach_low_480x270.png` | 480×270 | Opaque clean static environment, without Mateo or HUD. |
| `ohio_approach_high_960x540.png` | 960×540 | Same composition, separately resolved higher-grid environment, without Mateo or HUD. |
| `mateo_olive_stand_low_48x64.png` | 48×64 | One low-grid RGBA pose; source cell/pivot pending technical confirmation. |
| `mateo_olive_stand_high_96x128.png` | 96×128 | Same pose in a genuinely higher-grid RGBA cell; source cell/pivot pending confirmation. |
| `ohio_approach_low_native_480x270.png` | 480×270 | Registered flattened review composite with pose and unchanged baseline HUD. |
| `ohio_approach_high_native_960x540.png` | 960×540 | Same registration and HUD coverage at double grid; no altered HUD layout. |
| `ohio_approach_low_review_1920x1080.png` | 1920×1080 | Exact 4× nearest-neighbor display of low native review composite. |
| `ohio_approach_high_review_1920x1080.png` | 1920×1080 | Exact 2× nearest-neighbor display of high native review composite. |
| `source/` master and `provenance.md` | Native master dimensions recorded | Editable layers and exact source/generation/edit steps, sizes, hashes and review status. |

The master should register far, middle, gameplay and foreground independently at the selected crop, with conventional straight alpha for nonopaque layers; sky/base opaque across the full canvas, all layers share the same origin and canvas, transparent pixels outside their shapes, no premultiplied dark fringes. This is a static composition; **do not assert any camera motion or parallax test passes**. The crop is not a seamless room-wide asset. Do not repeat it to cover a scrolling level; layer parallax ratios and repeat bounds for a possible later implementation are explicitly unassigned pending technical design. Existing environment manifest ratios (0.10/0.35/0.65 horizontal) and room background layer ratios differ; neither is a new benchmark requirement. No asset manifest or runtime file changes in this experiment.

## Review and acceptance

Compare current actual capture, low native and high native at matching framing and at 1920×1080, first CRT off. Verify dimensions, opacity/alpha, player position and relative size, platform and collision registration, unchanged HUD coverage and legibility, and that high contains real authored detail while low remains intentional at 1×. Inspect against light and dark behind the isolated sprite, at native 1×, and inspect its foot contact in both composites. Describe concrete defects and revisions; retain candidate and baseline paths, provenance and hashes. Apply the project's 0–3 rubric only after actual visual inspection: all applicable dimensions ≥2 and silhouette/integration 3 are the project art-gate threshold, not scores assigned here. This static benchmark cannot establish motion, runtime integration, all camera positions, seamless repeats, CRT-on behavior, human playability or G2/G3 acceptance.

## Blocking measurements for v0.2

1. Exact baseline image path, capture method and game state; current camera origin and viewport in world coordinates; visible tile/object extents.
2. Player screen rectangle and foot baseline, facing, source cell/pivot and actual render scaling; chosen sprite placements at both grids.
3. HUD, prompts and action/telegraph coverage rectangles and any temporary capture overlays; identify what is invariant in the preview.
4. Whether selected capture actually shows any cover, sump, exit or interaction; record visible geometry and its screen coordinates.
5. Approval of output filenames, sprite cell sizes, review method and any reference-specific refinements.
