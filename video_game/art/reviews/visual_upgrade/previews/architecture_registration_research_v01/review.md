# Two-layer architecture registration — independent review

2026-11-11. The candidate was registered as a disposable preview only. `capture.py` produces immediate teleports (`renders_v01/`); `capture_settled_v02.py` adds 30 simulation ticks after each authored spawn before forcing each camera position (`renders_settled_v02/`). Both use temporary saves and dummy SDL. The settled files show Mateo at player rect y208 with feet at world y240; v01 renders immediately at y192 and leaves him visibly above the floor. Neither fixture demonstrates normal-input route, animated parallax, fairness, native display, performance or art acceptance.

`context.json` in each render directory records exact sources, dimensions, hashes, crop mappings and output hashes. The 2172 × 724 RGBA master is resized in full to 1920 × 576 with Lanczos, no mask, crop or manual alpha/paint edits; aspect ratio changes from 3:1 to 10:3 (+11.11%). The accepted 1152 × 544 far layer is unchanged. The fixture-local callback composites far and world-fixed architecture through the native compositor; existing tiles, objects, actors, effects, weather and HUD are drawn by the scene afterwards. No original source, asset or runtime file was modified.

## Alpha exclusion measurements

Measured directly on `renders_settled_v02/architecture_full_rgba_1920x576.png` in requested native world rectangles, with upper bounds exclusive. Alpha >0 includes faint resampling; >127 identifies substantial opacity. Fully transparent was required in the candidate brief.

| Region | Rectangle (x0,y0,x1,y1) | Nonzero alpha / total | Alpha >127 |
|---|---|---:|---:|
| Airlock | (24,312,120,480) | 6,324 / 16,128 | 5,416 |
| Sump | (640,440,768,576) | 3,557 / 17,408 | 2,714 |
| Warning | (600,396,668,464) | 2,926 / 4,624 | 2,544 |
| Yard exit | (1808,336,1904,480) | 5,194 / 13,824 | 4,161 |

The output has 713,409 zero-alpha, 390,598 partial-alpha and 1,913 opaque pixels. The four intended exclusions therefore fail the exact alpha-zero contract, including many substantial pixels. These counts describe the resampled candidate, not proof that every nonzero pixel is perceptually disruptive.

## Visual assessment

- `renders_settled_v02/camera_x0_y18_native_960.png`: recognizable service building with warm practical lamp and material separation. The far foliage appears through sharp irregular empty patches near the airlock and lower sump-facing building edge, which makes the facade read as chopped rather than a natural boundary. The sump remains visibly occupied by its real hazard and warning; the quantitative test establishes that the underlying architecture is not fully transparent in those requested regions.
- `renders_settled_v02/camera_x240_y18_native_960.png`: the actual drone and targeting line remain visible in this one state, while authored catwalks lie in front of the building. Long bright building roof edges and horizontal piping compete with actual walkable platform edges; this is a readability risk to test in motion, not a proven collision defect.
- `renders_settled_v02/camera_x480_y18_native_960.png`: a straight transparent-looking gap/foliage exposure appears directly left of the right airlock. The long warm roofline behind the right catwalk and the prominent upper far-layer horizontal line may imply additional ledges. The doorway itself and foreground cover remain visible in this still; their usability is untested.
- The candidate retains many semitransparent pixels. No alpha cleanup, geometry reshaping or exclusion masks were applied here. Deliberate redesign/repair should preserve the building's light/dark material intent while resolving cut boundaries and fully transparent reservations; avoid mechanically punching holes as an unreviewed shortcut. Re-register and inspect real exits, platform silhouettes, sump/warning, actors, telegraphs and both camera extrema before any consideration of promotion.
