# Big Ear 1977 flashback — observatory background v01

**Status: draft for review.** This is the existing playable flashback, not a new historical level. One state-neutral backdrop is the proposed next component after the relay is reviewed; no artist request is implied by this draft.

## Character and registration

An August 1977 radio-observatory workroom: period-appropriate institutional surfaces, an IBM-era line-printer station, analog equipment and an observation-window context. Shape dark brown/blue shadows against restrained warm desk and cabinet lighting, with concrete, painted steel, paper and wood materials. Make this an intimate working research room, distinct from the modern relay vault and the test annex. Detail should support the actual printer and vault interaction areas without painting a second interaction, false controls, new platforms, exits, cover or hazards. Avoid invented readable labels, telemetry, dates or signage. Do not bake an annotated page, red circle, loose reel, acquired anchor or other state into the background.

`data/levels/flashback/ehman_1977.json` defines a **480×288 world-unit** room; the viewport is 480×270 logical at density 2. Target one opaque **960×576 native PNG** at world/native origin `(0,0)`, world-fixed ratio 1, finite and nonrepeating. Camera x is 0 and y ranges 0–18 world units; source crops `(0,0,960,540)` and `(0,36,960,540)` are both required. Keep existing geometry and camera. The source describes a room behind gameplay; it must not depict extra ground, a false traversable shelf or a door inconsistent with the actual exit.

## Existing context and state boundaries

Inspect `previews/prototype_geometry_research_v01/capture_v01/flashback_1977_ANALOG_geometry_960x576.png`, the room fixture, the inspect/annotate fixtures and `context.json`. Guide rectangles are authored bounds, not proof that a separate sprite is currently rendered. Coordinates below are logical world units; multiply by two for the source.

- Printer terminal `(96,208,32,32)` and pen prop `(144,224,16,16)` sit in the actual printer interaction zone x=80–160. A static period workstation may visually support this existing interaction, but the visible signal and its annotation are the live overlay, not artwork in the background.
- Tape-deck cache `(368,208,32,32)` lies within the actual vault zone x=340–420. A neutral fixed cabinet provides context while avoiding a visible reel, opened door or state lamp that would contradict the locked, available, retrieved or completed states.
- The observation-window prop is `(208,144,64,48)`; it can inform the room's visual architecture, not promise a separate new interaction. The `FlashbackController`'s displayed prompt places the final anchor action at the reel cabinet. Do not visually imply a different required interaction sequence.
- Preserve exit zone x=0–56, solid side boundaries x=0–16 and x=464–480, and existing solid floor y=240–288. Keep the actor, prompts and HUD legible over the darkened lower wall. Do not copy guide outlines into the image.

`FlashbackController` owns stages, prompts, the warm amber tint, the fanfold modal and the red annotation. Its paper overlay occupies logical `(24,38,432,144)` when open. Preserve its actual text and state transitions above the background. Do not pre-tint the image as a substitute for that overlay, change the paper, or claim that stage progression has been tested by a single screenshot. The current field route suppresses combat during this flashback; no new combat or encounter is implied.

## Route, export and review

Unlike the annex/relay's `MandelaWorld` path, this scene uses the non-reality field path with the flashback controller layered over it. A future room-specific native hook must retain the true field tile/actor depth, prompts, tint, modal and return snapshot and fall back safely to the legacy background. The earlier annex hook is not proof of coverage here. No gameplay, collision, source room, equipment or return-rule change is authorized by the artwork brief.

Preserve the generated master, actual dimensions and alpha, prompt and SHA-256; after source review, derive `ehman_1977_background_v01_960x576.png` with disclosed proportional crop/resample. No procedural creative bitmap or mask-shaped holes. Review registered y=0/18 native and 1920 crops and both inspect/annotated printout states. Exercise real-input inspect, annotation, reel retrieval, anchor and return/abort where prerequisites allow; explicitly identify any injected stage fixtures and verify save/Continue, overlay, camera edges and fallback. Run relevant flashback/loader/input/content checks; a static background alone cannot establish a complete playthrough, performance, human acceptance or art-gate closure.
