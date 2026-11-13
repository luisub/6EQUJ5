# Salvage yard — separate maintenance wagon v01

**Status: proposed for Astra review; no image generation until approved.** One isolated vehicle follows the v02 background study, not a new scene, vehicle collection or runtime modification. The v01 painted-in wagon was rejected because its front overlapped the real hazard and its wheels sank into foreground tiles. This request allows precise placement and independent review.

## One subject

A plausible boxy **late-1980s/1990s observatory maintenance station wagon**, side-on with modest set-back perspective, weathered muted olive/gray enamel, dull windows, rubber tires and restrained warm reflected light from the yard's left-side fixtures. This is a whole believable vehicle with both wheels clearly articulated, not a toy, pickup truck, fantasy vehicle or invented branded object. Keep value and edge contrast subordinate to the real player, actual platform and hazard. Do not add lettering, logos, luminous beacons, hazard-colored stripes, exhaust, ground, props, scenery or a painted cast shadow. One static subject only.

## Exact cell, placement and actual room

Target `salvage_wagon_v01_168x76.png`: **168×76 straight-alpha RGBA** transparent outside subject; **84×38 world units** at density 2. Cell world rectangle `(196,202,84,38)` / full-yard native `(392,404,168,76)`, source top-left corresponds to world `(196,202)`. World-fixed at ratio 1:1, no repetition. Visible contact at world y=240 / source native y=480 should match the actual foreground ground; wheel bottoms may reach the final native cell row, with modest top/side transparent margins and no clipped bumper, wheel or roof. Keep all subject pixels inside its cell.

Real room is 640×288, viewport 480×270 world, camera x=0–160/y=0–18. At camera `(0,18)`, proposed native screen cell `(392,368,168,76)`; at `(80,18)` it is `(232,368,168,76)`; at `(160,18)` it is `(72,368,168,76)`. The cell begins four world units after west code-4 cover ending x=192, ends eight world units before real hazard beginning x=288, and sits below the true overhead platform at y=144. Existing other platform x=384–544/y=192, east cover x=448–480, pickup x=520 and exits x=32/576 remain separate. These clearances are only rectangle checks: actor/projectiles, enemies and screen-fixed UI can still overlap.

Render **after** approved far and yard background, and **before** actual tiles, objects, actor, enemies, projectile/effect and HUD stages, preserving real runtime order. It is decorative scenery with **no collision, damage protection, interaction or driveability**. The apparent vehicle must not promise usable cover, a walkable roof or an obstacle where none exists; Mateo must remain discernible while crossing in front. If even this correctly sized wagon looks like functional cover, hides characters/projectiles or confuses hazard/platform readability, do not ship it: move it only after a new reviewed geometry proposal or defer it. Do not change gameplay to justify the image.

## Deliverables and review

Preserve the untouched generated master, actual dimensions, exact prompt and SHA-256 in a new candidate folder. Image generation may not return 168×76; after source review, an explicitly recorded crop/resample can produce the exact cell. Never claim exact generator dimensions unless observed, and reject clipped wheels or distorted proportions. Use no procedural bitmap substitute. Inspect straight alpha on light/dark backgrounds, native 1× and integer display, then register on the v02 yard study behind actual geometry at x=0/80/160 and y=0/18. Show grounded actor crossing the wagon, projectile/telegraph, before/after pickup and HUD/exit states; static teleports alone are insufficient. Review motion and CRT off/on, and preserve source, transforms, hashes and observations.

This is a review candidate only, not production pixel-craft, collision/fairness, runtime integration or G2/G3 acceptance. The separate room-specific asset transaction and native renderer work must succeed before any integration.
