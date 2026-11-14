# Mateo larger presentation — coherent movement plan v01

**Planning only.** The unarmed 60×80 still is a direction candidate; the one armed recoil pose is queued, not generated or accepted. Do not install it across unrelated states or treat it as an animation set. This document authorizes no frame generation or runtime change. Proceed through individual reviewed sources in the coordinated artist sequence.

## Existing animation contract

`assets/sprites/mateo/manifest.json` defines olive-field cells at **96×128**, pivot **(48,124)** for every listed clip. Field and boss construct an `AnimationPlayer` at `.25`: the current field cell is 24×32 logical / 48×64 native. Manifest attachment coordinates below are source pixels; they are transformed relative to that pivot and `.25`, not relative to a proposed new picture. Hurtbox metadata and the physical collision rectangle are separate and remain unchanged.

| Clip | Frames; duration per frame | Muzzle / hand source coordinates | Notes |
|---|---|---|---|
| idle | 4; 325 ms; loop | (108,44) / (76,52) | breathing |
| walk | 2; 180 ms; loop | (108,44) / (76,52) | normal grounded movement |
| run | 4; 110 ms; loop | (108,44) / (76,52) | selected only above 1.1× walk speed |
| jump | 1; 0 ms | (108,36) / (74,46) | ascent |
| fall | 1; 0 ms | (108,42) / (74,50) | descent |
| land | 1; 120 ms | (106,54) / (72,60) | clip exists; normal caller not established |
| crouch | 1; 0 ms | (102,68) / (72,74) | low profile |
| slide | 1; 0 ms | (88,96) / (64,98) | kick attachment (98,114) |
| cover_low | 1; 0 ms | (98,72) / (70,78) | low cover |
| cover_background | 1; 0 ms | none / (62,54) | concealed cover |
| shoot | 1; 100 ms | (108,44) / (82,46) | clip exists; normal caller not established |
| recoil | 1; 120 ms | (104,34) / (80,40) | actual timer can select this state |
| tune | 1; 0 ms | none / (80,56) | device (96,52); normal caller not established |
| hurt | 1; 200 ms | (92,50) / (68,56) | clip exists; normal caller not established |
| death | 1; 0 ms | none / (30,110) | collapse |

Zero duration denotes the existing one-frame clip metadata, not a new timing instruction. `Player.animation_state` prioritizes death, cover, slide, crouch, airborne and recoil before movement. Ordinary grounded movement targets `walk_speed` 140 world units/s and selects walk; `run_speed` 180 is configured but is not the ordinary movement caller's target. Preserve existing state precedence, timing, movement speed, inputs, collider, hurtboxes, gameplay attachment coordinates, projectile behavior, saves and room logic. Fire can originate from the preceding active clip before animation-state update; inspect that instant as well as recoil.

## Next coherent source after the armed still

If the single armed recoil candidate passes native visual and registered anchor review, prepare a **two-frame walk source** matching its face, proportions, jacket, headset/radio, weapon treatment, palette and established larger idle direction. Each right-facing 60×80 candidate shares the visual foot anchor `(30,78)`, with a deliberate alternating planted contact, stable scale and connected in-between poses. Review both feet, ground contact, body rise and silhouette separately at native size and on light and dark rooms. The two currently used walk frames each last 180 ms, so the complete existing loop is 360 ms; preserve those two timings for this first replacement. Do not invent additional generated frames, reduce movement speed or claim smoothness from static frames. More in-betweens or altered timing would be a separate explicitly reviewed animation decision.

For walk and idle, existing gameplay hand is world offset `(+7,−18)` and muzzle `(+15,−20)` from foot, right-facing; retain the actual anchors even if the new pose is visually larger. A walking arm or weapon that cannot plausibly align to those positions is a review issue, not permission to move the projectile origin. Maintain a common foot registration through idle → walk → recoil and mirrored facing; verify muzzle location for both the preceding state and actual recoil at real shot time. Do not assume that the current unarmed idle concept proves weapon continuity. The new two-frame cycle remains a candidate until actual recorded input and playback have been inspected.

The rest of the active-state family still needs purpose-authored and reviewed visuals: jump/fall, crouch/slide, both cover postures and death, plus run when reachable. Clips with no established normal caller need audit before scheduling rather than automatic work. A live switch limited to larger idle/walk/recoil would visibly pop in scale on jumping, crouching or taking cover; use it only as an explicitly isolated test fixture, not a finished presentation. Either deliver a coherent set for all reachable states before default enablement, or agree on a separately reviewed transition/fallback approach. No new idle, walk, aerial or other frame is yet commissioned by this plan.

## Optional visual-only implementation contract

Use a new, versioned visual family with original masters, source prompts, exact native cells, visual pivots, state/frame mapping, dimensions and hashes; preserve all existing source assets and fall back completely when unavailable or invalid. The current animator stays the authority for state, frame index, elapsed time, `.25` gameplay scale, foot and attachment/hurtbox math. An optional native presentation lookup may select a reviewed image for the **same current state and frame index**, with its own independently declared visual pivot and native size. It must not replace clip metadata or alter the gameplay animator. A 60×80 visual has pivot `(30,78)` right and `(29,78)` under pixel-index mirroring; use declared clip-specific pivots if a later source differs. Resolve native placement at the original world foot and verify rounding and left/right mirroring.

Both `FieldOpsScene` and `BossScene` currently use animator surface/destination then `composite_native`; passing the original 24×32 logical size for a 60×80 image would shrink it. Any later implementation must use matching 30×40 logical display dimensions, preserve native transparency, scene-specific actor/projectile/foreground ordering, invulnerability blink, pause, camera clipping and fallback, and keep all source coordinate math unchanged. Bunker has a distinct sprite and layer route and is outside this field/boss proposal. A safe staged asset transaction, package data and rollback must be reviewed with the runtime owner before use.

## Evidence before default use

Verify original and new assets, all mapped frame indices and durations, exact foot/hand/muzzle registration in both directions, shot-before-state timing and no changed collision, hurtbox, speed or projectile coordinates. Record real-input idle/walk/recoil transitions, complete repeated walk playback at ordinary speed, jumps/landings, cover/crouch/slide, wall/edge clipping, attacks and effects in field and boss. Inspect feet, silhouettes and overhang against hazards and attacks on light/dark backgrounds and disclose any collision/art mismatch. Tests, actual native-window playback and human review are all separate evidence; a still or test suite alone does not establish coherent motion, fairness, production pixel craft or close G2/G3.
