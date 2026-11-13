# Ohio approach — one maintenance-equipment cluster v02

**Status: Astra approved for one artist request; no runtime promotion.** Supersedes the rejected `ohio_approach_vehicle_prop_v01_for_review.md`: a 112-pixel wagon would be implausibly compressed beside Mateo and too close to the adjacent catwalk/cover to read safely. Reserve a full-size period vehicle for the salvage yard after its geometry is reviewed. No current collision, art, asset family or runtime change.

## One coherent isolated subject

A small, worn **wheeled steel maintenance waste bin with a nearby cable reel**, appropriate to a late-1980s/1990s observatory service yard. Subdued blue-gray/olive metal, rust at a few joints and dark rubber; use selective warm reflected light, not a warning glow, text or bright markers. One natural grouped composition: the bin and reel share a physical base and consistent side-on view. No extra objects, ground plane, painted shadow, architecture or background. The shapes must not resemble a usable ledge or convey that the bin/reel protects the player. These are decoration only, drawn **behind** Mateo, enemies, projectiles and foreground tiles, with no collision, protection or interaction.

## Exact candidate canvas and placement

Create **one 112×64 native-pixel straight-alpha RGBA cell**, full transparent outside the subject. Cell world rectangle `(804,208,56,32)`; full-room native `(1608,416,112,64)`; origin top-left, world-fixed 1:1, nonrepeating. Ground contact line is world y=240 / full-room native y=480. Keep **the top 28 native rows fully transparent** (world y=208–222); objects are at most 18 world units / 36 native pixels tall, less than the 32-world-unit standing player. Reserve at least 8 transparent native pixels at left/right; keep visible body and wheels inside the cell.

Use these approximate proportions to avoid arbitrary scale: bin roughly **12 world units wide × 17 high** (24×34 native) and reel roughly **12–14 world units wide × 13–15 high** (24–28×26–30 native), with a modest horizontal gap and wheels/base anchored at the actual ground line. Exact silhouette may vary within the cell; no opaque background or opaque border. Do not bake the old tile beneath it. The real foreground ground starts at y=240 and renders in front, so leave no fake floor above it.

From `approach.json`, the fourth true platform ends at world x=800 and a collision-code-4 feature starts x=864: the cell leaves **4 world units** on either side, and the subject's internal transparent margins increase that clearance. Sump x=320–384, mast x=576, exit x=912 and real warning are elsewhere. At camera `(480,18)` cell screen rectangle is `(648,380,112,64)` native; it appears in the right-hand traversal, not initial spawn. These are geometric clearances only. The actor and projectiles may pass in front; the HUD, prompts and effects are screen-fixed/conditional. Review those states rather than assuming safe play.

## Source and review

Preserve untouched generated master, exact prompt, output dimensions and SHA-256 in a new candidate directory. The generator may not output an exact cell: deliberate crop and resampling with recorded method may produce the final 112×64 cell; inspect native clusters and alpha on light/dark grounds. Deterministic clipping to the cell is not a substitute for correct authored shape; reject visibly cut subjects and do not procedurally invent artwork. No automatic runtime installation.

Register the subject after the accepted far and building candidates and before **actual** tiles, objects, actor, projectiles, effects and HUD at camera x=240 and 480, y=0 and 18, in native 960 and nearest 1920. Include actual normal-input traversal past the cluster and projectile/telegraph states, not only static teleports. Reject if the cluster looks like real low cover, hides a projectile or player's body, creates an apparent platform, conflicts with x864 cover, loses contact or makes the yard unreadable. If no safe position exists, defer the cluster; do not change gameplay to accommodate it. This is not motion, gameplay fairness, production pixel-craft or gate acceptance.
