# Scorpion Echo v01 — isolated static concept provenance

Generated 2026-11-12 with `image_gen__imagegen`, transparent background true, no reference image or seed exposed. This is an original fictional machine inspired only by the broad scorpion motif documented in the scene research, not a reconstruction, copied relief, or statement about ancient belief. It is an optional imagined waveguide concept and not FASR-010 or an installed enemy. Act V has no blockout. A still does not establish animation, a fair encounter, collision, room readability or gate acceptance.

The original `generated_images/exec-a4fed6f6-98da-4175-ad19-4020f811871b.png` remains preserved; its byte-identical copy is `source/scorpion_echo_generated_master.png`. Both share SHA-256 `1d3a8c9828d9dae4321ae1f5e41026305c2a58c641c6b9adda50cac7da65f205`. The source is 1635×962 RGBA; alpha range 0–255, zero 854,728, partial 717,505, opaque 637; alpha >127 bounds `(17,22,1606,944)` (exclusive right/bottom).

## Exact prompt

Create ONE original isolated transparent 2D side-view pixel-art concept of a fictional Scorpion Echo waveguide guardian, facing left. A squat low oval armored construct on simple planted articulated legs; two visibly separated open forward pincers; one segmented tail arches over its rear with a blunt tip held back. Preserve open space inside the curved tail, between pincers and under its body. Warm chalk limestone-like carapace plates, deep umber structural gaps, small aged-bronze joints, and a restrained high-contrast amber/cyan warning lens at the tail tip. Coarse purposeful pixel clusters and strong readable side silhouette for a later 110–125-pixel-wide, 58–70-pixel-high study including tail. This is a fictional machine, not a real animal or copy of a carving. One full-body pose with generous transparent margin; no floor, shadow, environment, pedestal, relief slab, inscription, sacred symbol, text, UI, weapon, other subject or animation sheet.

## Static export and inspection

`previews/scene_villains_v02/artist/build_scorpion_study.py` crops alpha >127 bounds (potentially discarding lower-alpha edge pixels), proportionally Lanczos downsamples 1589×922 to 120×70 (about 0.53% aspect rounding), sets alpha <16 to 0 and ≥240 to 255, and places at `(36,46)` in a transparent 192×128 cell. No painting or upscale. `exports/scorpion_echo_192x128_study.png` SHA-256 `16ad413361158ee61cba1169ce22e3b0f225f0e3e25a5966056783c3b5fca8aa`; visible alpha >127 bounds `(36,46,156,116)`, 120×70, nominal pivot `(96,116)`. Baseline is art registration, not a collider. The artist preview directory contains context and every PNG hash; 1× and nearest-neighbor 3× comparisons use actual field idle Mateo (48×64 cell, 25×59 visible, foot pivot y116), captured with dummy SDL, direct field entry, 30 updates and temporary saves. These are comparison fields, not game-scene renders.

Artist inspection: the curved tail and interior gap, low armored body, separate support feet, blunt tail lens and material family are legible on both fields. The two forward shapes resemble the jaws of one large open crab claw more than **two independently open pincers**; this is a concrete brief failure. An unrequested glowing face stripe competes with the tail lens, and the tail is already raised high, leaving less evident lift range for a later windup. Dark inner legs lose contrast on the dark field; light edges are softer on the light field. The eye/cue and pose require review; no animation or actual gameplay claim is made.

## Recovery

Retain this original master, export, previews, helper and provenance even if rejected. If the copied master is lost or damaged, verify the original generated output against the SHA-256 above and copy it byte-for-byte to `source/scorpion_echo_generated_master.png`. Rebuild into a new empty preview directory with `PYTHONPATH=. SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python video_game/art/reviews/visual_upgrade/previews/scene_villains_v02/artist/build_scorpion_study.py --output-dir NEW_EMPTY_PATH`, then verify output hashes. Document any later revision separately.

## Director review

Root reviewed the source and native comparisons and requested v02 because the front read as a single open claw; requested two separate two-prong pincers, a slightly lower tail and tail-focused cue. Retained as the superseded v01 concept; see sibling `scorpion_echo_v02` for the accepted static direction. This review is not runtime or animation acceptance.
