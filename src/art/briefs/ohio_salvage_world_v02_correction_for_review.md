# Ohio salvage yard — background correction v02

**Status: proposed to Astra; one backdrop edit only after review.** The registered v01 yard source was rejected for promotion because its wagon is too low and extends into the real hazard. Preserve the v01 master, previews and review. This changes the hypothesis: **remove the wagon from the background entirely** and later create one separately registered vehicle asset. Do not generate the vehicle in this request.

## Source and edit scope

Use `src/art/source/environments/salvage_world_scene_v01/source/salvage_world_scene_generated_master.png` as the image-edit source. It is 1870×841 RGBA; the earlier proportional-near registration used the entire image resized to 1280×576. Consult `previews/salvage_registration_director_v01/capture_v01/` for x=0/80/160 actual-room composites and `previews/salvage_geometry_director_v01/capture_v02/actual_room_geometry_1280x576.png` for the real 2× geometry. These are references, not artwork to paint over.

**Edit only the backdrop:** remove the entire station wagon and replace its space with coherent **dark vertical scenic structure** belonging to this outdoor surplus yard—e.g. a recessed shed wall, subdued vertical supports and distant stored machinery in shadow. Preserve the distinctive tilted radio dish, shed, racks, cable reels, autumn silhouettes, shaped amber work lights, deep cool shadow and overall material richness. Do not add a new vehicle, bins batch, gameplay objects, ladders or uniform fog. Keep a restrained field behind the real hazard so its warning remains clearly visible; any retained cable reel behind it must be subordinate and must not make the real hazard look like its own decoration. Soften competing bright horizontal roof/shelf highlights near actual platform tops while preserving readable authored architecture.

Remove the illustrated floor strip as a would-be play surface: do not paint a broad horizontal floor, curb or reflective apron above the real ground, and do not put an apparent safe surface behind the real hazard. Continue low-contrast **vertical** wall/depth shapes downward or natural transparency where appropriate. Do not create rectangle-shaped mask holes around gameplay or clip architectural features into conspicuous hard gaps. Real tiles render above the background. Natural transparency above skyline/structure is appropriate.

## Locked world contract

Target a clean, coherent **1280×576 RGBA** world-fixed export, density 2, world origin `(0,0)`, finite/nonrepeating; viewport crop `(2cx,2cy,960,540)`, current camera x=0–160/y=0–18. All game geometry and HUD remain the actual runtime: ground world y=240, hazard world x=288–368/y=224–240, cover world x=160–192 and x=448–480/y=224–240, platform tops x=96–256/y=144 and x=384–544/y=192; actual pickup at `(520,208,16,16)` and exits `(32,192,32,48)` / `(576,192,32,48)`. Maintain actor, projectile, telegraph and pickup contrast at every camera. The wagon visible in the v01 full-image transform occupies approximately native x=376–626 and intrudes into the hazard beginning x=576; removal must not leave its silhouette, wheel rims or fake shadow.

A future separate wagon is expected to use a candidate 168×76 native cell corresponding to world `(196,202,84,38)` if the actual gameplay/readability review supports that placement. This is a plan, not an immediate asset request or collision/cover change.

## Deliver and review

Preserve the untouched edited master, actual output dimensions, alpha, exact prompt and SHA-256; it may not be 1280×576. After visual inspection, technical may derive an exact candidate through a recorded proportional crop/resample and report any clipping or aspect change. No procedural painting, old-image enlargement or silent mask-based patching. Use a new versioned path; do not overwrite prior sources.

Register after the interim far plate and before actual yard tiles/objects, grounded actor, enemies, effects and HUD. Inspect native 960 and nearest 1920 at x=0,80,160/y=18 and y=0, with coupler still uncollected; inspect pickup, both platforms and exits, actual hazard, hound/drone cues and practical light/actor contrast. Review normal-input motion, later collected state and CRT separately. Stop on visible scene defects rather than claiming production readiness from one still. This is not a runtime promotion, completed scene, animation, human fairness, native performance or G2/G3 acceptance.
