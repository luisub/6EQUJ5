# Ohio salvage yard — full-room art brief v01

**Status: draft; no generation or integration before approach-layer review and a yard-specific technical capture.** This is the next existing Act I room, not a copy of approach and not an unapproved room expansion. The user-approved direction is rich high-contrast retrofuturist Ohio material craft: deep cool shadows, warm practical lights, deliberate machinery and plausible service history, without losing action readability.

## Identity and purpose

This is an outdoor, fenced decommissioned surplus **parts yard and depot**, distinct from the approach’s brick garage wall: organized traces of obsolete radio work mixed with weathered scrap, covered service racks, crates, coiled cable and stripped instrument housings. A legible depot destination should reward the search for the actual analog feedhorn coupler. Contrast its rusty stored equipment, partial roof and crowded rack silhouettes with the approach's brick access yard, while retaining the shared Big Ear infrastructure and coherent material language. No newly painted object is a pickup, cover, obstacle or exit. Preserve the real coupler, both cover positions and objective cues.

The historical `planning/evidence/A11/previews/02_act_01_salvage_yard_render.png` was inspected as an older illustration, not a verified current capture. A dummy-driver direct-entry yard guide and two native endpoint captures are in `previews/salvage_geometry_director_v01/capture_v02/`: grounded entrance x=0 before pickup and grounded depot x=160 after the 30-update fixture auto-collected the coupler; actual HUD, drone, platforms and exits are present. These are scripted fixtures, not a played route; a separate near-depot pre-collection capture and normal-input traversal remain necessary. The full 1280×576 guide renders actual tiles and objects only; the pickup, actor, HUD and effects are scene-rendered and excluded from the guide. Use `data/levels/act_01/salvage_yard.json` as geometry authority.

## Current room and full-camera coverage

Room is **640×288 world units**, 16-unit tiles, logical viewport **480×270**, native presentation density **2**. Current camera x=0–160 and y=0–18. Ground is solid across x=0–640 from y=240; ceiling y=0–16 and side walls x=0–32, 608–640. One-way tops are **x=96–256/y=144** and **x=384–544/y=192**. Hazard code 3 is **x=288–368/y=224–240**; two actual low-cover zones are x=160–192 and x=448–480 at y=224–240. Preserve exact collisions and truthful silhouettes.

Spawns are entrance `(48,208)`, midpoint `(240,144)` and depot `(520,208)`. Checkpoints at `(48,208)` and `(520,208)`; return exit `(32,192,32,48)` and catwalk exit `(576,192,32,48)`; actual coupler pickup `(520,208,16,16)` must remain clear and its collected state must remain distinguishable. Drone initial x=440/patrol 380–500; yard hound initial x=560/patrol 480–600. These dynamic actors can overlap in play: do not fill the depot with high-contrast junk or assume a clean empty lane. Existing route and feedhorn-repair gate remain as implemented.

The 960×540 render remains the same view at twice density; HUD is screen fixed, with conditional prompts and telegraphs. Keep clear areas beneath actual text at every camera position. Current x=0–160 and y=0–18 values are authoritative; a 960-world-unit yard is only an unapproved pacing proposal and cannot be implied by these art bounds.

## Candidate planes — proposed, not yet commissioned

| Layer | Proposed exact canvas | Contents / contract |
|---|---:|---|
| Far | **992×544 opaque** | If x=.10/y=.05 is selected, source origin `(0,0)` at camera `(0,0)`, native crop `round(2×ratio×camera)` yields x=0–32/y=0–2. Distant reflector/treeline glimpses and deep dusk behind the existing roof/yard; finite, no repeat. A future width decision requires recalculation; do not stretch this as a room expansion. |
| Mid | **1072×548 RGBA** | If x=.35/y=.15, x crop=0–112/y=0–5/6. Silhouetted surplus sheds and distant storage masses, no misleading solid roof where the real platform is absent. |
| World-fixed | **1280×576 RGBA** | World origin 0; source crop `(2cx,2cy,960,540)`. Connected racks, wall sections, sparse props and real-span supports behind tiles/actors; no decorative safe floor over the real hazard, fake exits, collision or functional cover. |

Ratios are proposed to match the currently hardcoded Ohio loaded-asset values; they are not evidence that room metadata controls actual rendering. New native phase, room-specific mapping, alpha, nonrepeat coverage and safe asset transaction need technical agreement. The single artist produces one reviewed layer at a time, preserving original generated masters and actual dimensions; deliberate 1× cleanup is required. Do not regenerate the entire room as one flat background or use a procedural bitmap substitute. Separately reviewed near props or a vehicle can follow only where their shape never implies protection or a platform.

## Proposed full-world composition

- **Entry / west:** dark gate and structural posts, a few warm-lit steel/brick surfaces around the actual entrance. Do not obscure the return exit or its conditional label; avoid a false door at the opposite depth.
- **Center:** stacked decommissioned dish parts and service shelving at several depths, with broad connected shadows and a few selective amber pools. Preserve clear silhouette behind Mateo and enemies, real cover edges, the two real platform lips and the real x=288–368 hazard. Any hazard backing must not look like a safe continuous floor.
- **East / depot:** a recognizable, weathered service rack and small focused light surrounding—but not covering—the actual coupler location. Keep hound, drone, pickup glow, checkpoint, exit and action lane distinguishable under both pre- and post-collection conditions. Vehicle or clutter belongs behind action and may not cross a platform or hide the real warning/exit.

### Full-size wagon: provisional yard-only opportunity

The approach wagon was rejected for being too small; assess a single **full-size, boxy 1980s/1990s observatory maintenance wagon** in the yard instead. An initial design-only background cell is world `(196,202,84,38)` / native `(392,404,168,76)`, grounded at world y=240 and drawn behind actors/real tiles; its length is 2.625× the 32-unit standing player height, rather than a 56-unit compressed vehicle. This rectangle sits after the west low-cover extent ending x=192 and before the hazard beginning x=288, and its top y=202 is below the overhead x=96–256/y=144 platform. Its four-world-unit gap from cover is tight and this is **not an approved placement**. The other real platform and east pickup/exit are farther right.

The captured full-room geometry guide confirms the rectangle is between the two real cover/hazard regions and below the first platform; inspect its perspective and every gameplay angle before commission. The parked vehicle must read as set-back decorative scenery, not functional low cover, a new exit, roof platform or floor; actors and projectiles must remain legible while passing in front. Because visual collision may still be misleading even with separated rectangles, move or defer the wagon if its perceived plane or scale is unclear. Do not alter existing gameplay or assume a future 960-wide yard. Vehicle is a later single-asset proposal, not part of the approach equipment request and not authorized for immediate generation.

Natural steel, canvas, oxidized copper, rust and concrete should read as different large materials, with hand-authored seams and restrained accents. Dark structural shapes frame the lit work zone; neither all-over black nor uniform blue haze. No screen-wide fence, repeated ladder or high-contrast horizontal decorative edge that suggests new traversal.

## Review gates for a future commission

First confirm no conflict with any approved blockout/pacing change and obtain actual yard camera/geometry guide with source/world/native transforms. Review each candidate at camera x=0, 80 and 160 plus y endpoints, then during normal-input traversal, in native 960 and nearest 1920, CRT off/on. Verify entrance and gated exit, real hazard, both cover volumes, pickup/collected state, enemy telegraphs, projectile paths, HUD and camera boundaries. Preserve source/master hashes and failure/rollback evidence. A static art proposal is not a gameplay, parallax, animation, native performance or G2/G3 acceptance.
