# Mandela annex v01 — registered visual review

**Verdict: reject this source for integration; revise the two observed geometry cues.** This is a static component review, not an assessment of the complete room, timeline behavior, playthrough or art gates.

The generated 1620×971 opaque master is documented in `src/art/source/environments/annex_shared_background_v01/provenance.md`. The disposable fixture and hashes are recorded in `previews/annex_registration_director_v01/capture_v01/context.json`. Its full canvas was Lanczos-resized to 960×576 with only a very small aspect change, without masking, painting or cleanup. The fixture substitutes only the room background, then renders the actual `MandelaWorld` tiles, moving platform, objects, weather/transition, player and HUD. It directly selects each timeline, settles the player for 30 updates, and forces camera y=0 or 18; it is not a normal-input traversal or timeline-switch test.

Review these native 960 captures, with nearest 1920 versions alongside:

- `previews/annex_registration_director_v01/capture_v01/2029_CORE_y18_native_960.png`
- `previews/annex_registration_director_v01/capture_v01/1977_ANALOG_y18_native_960.png`
- `previews/annex_registration_director_v01/capture_v01/2029_CORE_y0_native_960.png`
- `previews/annex_registration_director_v01/capture_v01/1977_ANALOG_y0_native_960.png`

At camera y=18, a conspicuous continuous background lip appears around screen y=424 while the actual floor begins at y=444. It therefore suggests a traversable floor 20 native pixels above the true floor; the source equivalent is around y=460 versus actual ground at y=480. The heavy horizontal conduit also runs directly behind the moving platform at about source y=320–340. It makes the platform appear part of a continuous horizontal structure and competes with the edge that needs to communicate the real moving surface. Both conflicts are visible in the two timelines, including where the real 1977 blocks interrupt the view.

The strong concrete paneling, recessed machinery, vertical structural rhythm and warm practical light against cool shadow provide a useful basis for a targeted correction. For one proposed edit, retain the full room framing and those materials, **remove the false floor lip and any painted floor above the real terrain**, continuing coherent vertical wall and machinery backing down behind the actual ground. Replace or interrupt the prominent mid-height horizontal conduit in the moving-platform path with subdued vertical or recessed structure that cannot read as another platform or continuous walkway. Keep real moving-platform travel, pickups, door, grapple, hazards and both collision variants entirely separate; no mask-shaped holes, fake state indicators, new geometry or other redesign. Review the corrected full 960×576 registered source in both timelines and at both camera positions before integration.

The present images do not test moving-platform endpoints, timeline swap, collected/open states, CRT, native window, performance or human play. No runtime or shared planning files were changed by this review.
