# Mandela annex v02 — registered visual review

**Recommendation: accept as a bounded static background component for an integration experiment.** The prior source remains rejected and preserved. This is not acceptance of timeline behavior, motion, gameplay, performance or the art gates.

The original 1619×971 RGB opaque source and generation details are in `src/art/source/environments/annex_shared_background_v02/`; source SHA-256 is `6541fdaf3974dd7630ad7a44c1073c9c67a2f02cb5fab27572ac11dcb9d9a282`. The full image was Lanczos-resized to `previews/annex_registration_director_v02/capture_v01/annex_shared_background_960x576.png`, SHA-256 `b12ba8f554e5cdb9f237a9f1266ed3bae06c10c480272a3c605decf50269dd4a`. There was no crop, mask, paint or cleanup; the source and export have nearly matching aspect ratios. Exact captures, hashes and fixture disclosure are in that directory's `context.json`.

The false floor lip is gone: the vertical wall continues behind the separately rendered real ground. The prominent continuous mid-height conduit is also gone, and the real moving platform is visually distinct against the central wall at both tested endpoints. Restrained concrete, machinery and warm/cool lighting survive the correction; the remaining wall seams and side machinery do not present the same continuous central platform cue in these stills.

The fixture draws the candidate behind real `MandelaWorld` terrain, active objects, weather/transition and the normal field actor/HUD. It directly selects `2029_CORE` and `1977_ANALOG`, settles the player for 30 updates and then injects platform positions at the authored `(200,160)` and `(280,160)` waypoints. Each combination was captured at camera y=0 and y=18, native 960 and nearest 1920. This is **eight static views**, not proof of platform motion or normal-input access. Example views:

- `previews/annex_registration_director_v02/capture_v01/2029_CORE_endpoint0_y18_native_960.png`
- `previews/annex_registration_director_v02/capture_v01/1977_ANALOG_endpoint1_y18_native_960.png`

Integration still needs the correct `MandelaWorld` background-only hook and fallback, timeline switching, moving-platform playback, stateful doors/pickups, saves, real input, HUD and camera checks, and the appropriate tests. No native window, CRT, human playthrough, motion, performance or complete-scene acceptance is established here.
