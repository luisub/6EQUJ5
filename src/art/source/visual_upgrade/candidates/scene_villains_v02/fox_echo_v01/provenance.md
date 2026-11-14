# Fox Echo v01 — isolated static concept provenance

Generated 2026-11-12 with `image_gen__imagegen`, transparent background true, no reference image or seed exposed. This is an original fictional machine inspired only by the broad fox motif documented in the scene research, not a reconstruction, a copy of a relief, or a representation of ancient beliefs. The subject is neither FASR-010 nor an installed enemy. Act V has no blockout. One pose does not establish animation, a fair encounter, collision, room readability, or gate acceptance.

The tool's original `generated_images/exec-fc540b49-e318-453d-b55f-aa09d8b5d00f.png` is preserved; its byte-identical copy is `source/fox_echo_generated_master.png`. Both have SHA-256 `33e32de0b639ced1d901252e7202546d9b914fa9d20cb9c8304b870ab3c6f5e3`. It is 1912×823 RGBA; alpha range 0–255, zero 1,006,248, partial 566,468, opaque 860; alpha >127 bounds `(93,18,1864,789)` (exclusive right/bottom). No painting or source modification was performed.

## Exact prompt

Create ONE original isolated transparent 2D side-view pixel-art concept of a fictional Fox Echo archive guardian, facing left, with a pointed muzzle, two separate upright ears, compact low chest, four articulated short legs and a long tapered wedge tail beginning to lift. Feet planted on one baseline; preserve clear negative space under its belly and between its ears. Warm chalk limestone-like armor plates, deep umber mechanical seams, small aged-bronze hinges and one restrained high-contrast amber/cyan eye. Use a strong horizontal silhouette and coarse deliberate pixel clusters for a later 100–120-pixel-wide, 42–50-pixel-high native study. It is a constructed machine, not a real animal or copy of any carving. One full-body representative pose with generous transparent margin, no environment, ground, cast shadow, pedestal, text, UI, weapon, relief panel, inscription, sacred symbol, duplicated subject or animation sheet.

## Static export and inspection

`previews/scene_villains_v02/artist/build_fox_study.py` crops alpha >127 bounds (possibly discarding lower-alpha edge pixels), proportionally Lanczos downsamples 1771×771 to 110×48 (about 0.23% aspect rounding), sets alpha <16 to 0 and ≥240 to 255, and places at `(41,68)` in a transparent 192×128 cell. No stretching, painting or upscale. `exports/fox_echo_192x128_study.png` SHA-256 `cc6da60bd2077b129e0848ab99cda59aa74a657a5a61c03a5b861bc1b4603553`; visible alpha >127 bounds `(41,68,151,116)`, 110×48, nominal pivot `(96,116)`. Baseline is an art registration convention, not a tested collider. The matching artist preview directory contains source context and individual output hashes. It compares actual field idle Mateo (48×64 cell, 25×59 visible, foot pivot y116), obtained by dummy SDL direct field entry after 30 updates with temporary saves; comparisons are 1× and nearest-neighbor 3× on dark and light fields, not game-scene renderings.

Artist inspection: pointed face, separate ears, four legs, belly gap, long armored tail and eye are visible, and the palette relates to Vulture. At native size the eye is tiny, joints/feet and edges have resampling softness, contrast is lower on light stone, and the narrow segmented tail and general profile may still read as a mechanical hound instead of a fox. A distinct gap above the tail root is weak or absent. The tail is raised more than a nearly horizontal silhouette; director review should decide whether it meets the desired family and pose. No motion or telegraph is established.

## Recovery

Retain the original master, export, preview images, helper and this provenance. If the copied master is lost or damaged, verify the original generated output against the SHA-256 above and copy it byte-for-byte to `source/fox_echo_generated_master.png`; rebuild into a new empty preview directory with `PYTHONPATH=. SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python video_game/art/reviews/visual_upgrade/previews/scene_villains_v02/artist/build_fox_study.py --output-dir NEW_EMPTY_PATH`, then verify the output hashes. Do not overwrite or discard a rejected version; preserve and document any subsequent revision separately.

## Director review

Root reviewed the source and native comparisons and requested v02 to address the narrow raised tail, oversized ears, tail-root gap and small-scale eye/foot readability. Retained as the superseded v01 concept; see sibling `fox_echo_v02` for the accepted static direction. This review is not runtime or animation acceptance.
