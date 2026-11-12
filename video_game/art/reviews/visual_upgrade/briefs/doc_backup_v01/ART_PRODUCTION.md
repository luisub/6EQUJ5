# Art production and review

The existing art is the starting inventory. Preserve reviewed work and improve assets through recorded visual comparisons. HUNTDOWN is the reference for material definition, expressive poses, scene composition, animation and interface consistency. Its actual engine dimensions are outside this project's specification.

## Asset family specifications

| Family | Production contract | Visual checkpoint |
|---|---|---|
| Civilization portrait | 128×128 RGBA subject, independent environment and chart | Distinct silhouette, lore-consistent form, readable composition |
| Portrait motion | 4–8 deliberate idle/pulse frames, separate speaking/receiving effect where appropriate | Stable anatomy and framing, no noisy contour crawl |
| Mateo combat | 48×64 cells, foot pivot initially (24,62), stable hurtbox | Silhouette and aim readable during combat |
| Mateo bunker | Existing 96×128 presentation, pivot initially (48,124) | Floor contact and prop scale consistent with room |
| Mateo clips | Idle 4, run 8–12, jump ascent/apex/descent/land, crouch, cover enter/hold/exit, slide, shoot/recoil, tune, hurt/death | Timing and motion judged at actual playback speed |
| Aim | Eight directions via authored poses or torso/weapon layers | Attachments stay aligned through moving and stationary firing |
| Enemy | Shared humanoid scale where appropriate, unique faction silhouette | Telegraphs visible against the actual biome |
| Boss | Case-specific cells up to viewport scale, metadata-driven frames | Vulnerability and attack lanes legible |
| Environment | 16×16 modular tile basis, larger authored props, 480×270 view | Clear traversal, cover, exits, quiet background values |
| Lights/effects | Separate assets with explicit blending and budgets | Effects preserve readability and can be reduced |
| Fonts/UI | Pixel-aligned glyphs, tested required characters, scalable dialogue option | Text fits actual panel bounds and is readable |

Frame counts are initial production targets. Change them when reviewed motion improves and record why. All three Mateo outfits share animation semantics. Reuse animation structure while preserving outfit details and silhouette.

## Per-asset work sequence

1. Read the corresponding lore, gameplay role and destination dimensions. Write a small art brief with silhouette, material, palette, pose, scale, lighting and layer needs.
2. Compare the existing candidate with references. Identify exact defects such as clipped hands, muddy faces, inconsistent pixel sizes, unrelated colors, or foreground clutter.
3. Produce one concept or revised master with available image/pixel-art tools. Preserve source, provenance and generation settings where available.
4. Build the native pixel grid deliberately. Clean contours, anatomical landmarks, material ramps and local contrast. Inspect downsampling artifacts at 1×. Source extraction and palette reduction are preparation steps that require visual review.
5. Export subject, background, props and lighting with conventional alpha. Opaque background plates fill their bounds. Transparent pixels in a foreground layer are expected. Produce separate flattened inspection previews.
6. Assemble animation with stable frame size, foot pivot and attachment points. Check each frame and playback. Remove unintended jitter, sliding feet, inconsistent limbs and clipped weapons.
7. Export through the safe asset builder. Record palette, dimensions, source/output hashes, frame timings and review state.
8. Preview inside the actual game scene at 480×270 and integer scale, CRT off/on, dark/light backgrounds, moving/still camera. Capture only evidence needed for the review.
9. Fix failed rubric items and repeat the relevant checks. Mark reviewed assets in the manifest with reviewer/date/evidence.
10. Archive replaced masters/exports using the retirement protocol after all callers and rebuild paths pass.

## Visual rubric

Score each applicable dimension 0–3. Zero means broken or missing, one means substantial revision, two means usable with minor issues, three means meets the intended art direction.

| Dimension | Inspect |
|---|---|
| Silhouette | Role and subject recognizable at native size |
| Anatomy and motion | Proportions, joints, weight, stable pivots, expressive poses |
| Pixel craft | Consistent grid, deliberate clusters, clean contours |
| Materials and light | Readable surfaces, coherent light direction, controlled highlights |
| Composition | Character/UI separation, focal hierarchy, useful environment detail |
| Lore and continuity | Civilization identity, outfit continuity, consistent palette language |
| Integration | Layer order, alpha, frame alignment, camera movement, font fit |

For the art gate, every applicable score must be at least two. Silhouette and integration must score three. Record remaining polish items and comparison images. Human art feedback can refine the result when available. The LLM still performs and records its own visual inspection before claiming the gate passed.

## Civilization direction checklist

Read all source profiles. Preserve energy-based FASR-001, gravitational FASR-002, architectural FASR-003, developing plasma FASR-004, diplomatic humanoid FASR-005, memorial FASR-006, theatrical beacon FASR-007, seven-voice FASR-008, probe FASR-009, geological memory FASR-010, and nonlinear FASR-SCAN-H.

Check each chart's relationship to its source. Record schematic depictions honestly. Ground survey and multi-quadrant anomaly views have their own graphic conventions. Keep foreground effects from obscuring dialogue.

## Background production checklist

For every room, author a blockout with collision and interactive objects first. Set the camera framing and player scale. Build far, middle, gameplay and foreground layers, then place props and lights. Review all camera positions and timeline variants. Check seamless tile repetition with adjacent copies. Avoid opaque borders that create a visible grid across joined tiles. Every visible cover object must agree with its collision and protection behavior.

## Tool and compute handling

Request image tools for new bitmap artwork when available. Code can package and validate images and build controlled effects. If art capability is missing, flag GPU_IMAGE and continue independent programming tasks. Keep affected art tasks incomplete with concrete missing outputs.

Advance from one reviewed portrait and one reviewed room to the full batch. Preserve all rebuild sources even when they are excluded from runtime packaging.

References are the [user's visual reference](https://www.loubagel.com/blog/beautiful-pixel-art-games/) and [Easy Trigger's HUNTDOWN page](https://easytrigger.com/huntdown/).
