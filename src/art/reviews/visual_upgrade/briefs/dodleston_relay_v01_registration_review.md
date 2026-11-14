# Dodleston relay v01 — registered visual review

**Recommendation: accept as a bounded static background component for integration experiment.** The archive equipment, masonry arches, recessed brickwork and warm practical lamps give the relay a distinct identity while leaving the existing changing geometry and HUD visible. The low-contrast masonry course reads as a wall joint in the reviewed views; it does not form an obvious continuous traversable platform. No false foreground floor or painted cassette/door/coolant state was observed in these stills.

The rack is mounted above the player rather than drawn as a reachable desk. It contextualizes the existing radio interaction but does not by itself show its reach. `previews/relay_registration_director_v01/panel_v01/terminal_before_e_native_960.png` records the actual direct `relay_terminal_post` spawn at player x=80; `terminal_panel_e_native_960.png` records the result of synthetic E KEYDOWN/UP with the real relay panel open. The existing top-screen `[E] RELAY` hint is present; this fixture does not show a separate local prompt. This is not normal-route or usability acceptance.

Original opaque RGB master `art/source/visual_upgrade/candidates/relay_shared_background_v01/source/relay_shared_background_generated_master.png` is 1619×971, SHA-256 `f26f8f6c4c0441cdfb4e52d886515160c2c8d77d6e826660d31235575654397f`. Full-canvas Lanczos export `previews/relay_registration_director_v01/capture_v01/relay_shared_background_960x576.png` is opaque RGB, SHA-256 `9af9affb03ea68ace6b55293193a8a3ad80691b32b907421562ea17e75a1f447`. The source and export have nearly matching aspect ratios; no mask, painting or cleanup was applied. All output hashes, state flags and direct-action results are in `capture_v01/context.json`; the separate terminal fixture has its own `panel_v01/context.json`.

The temporary-save fixture directly enters the room and selects each timeline, then renders actual `MandelaWorld` terrain/objects and field actor/HUD above the candidate at camera y=0 and y=18. For 2029 it directly invokes the actual relay action methods to produce initial, ruptured, drained, bulkhead-open and cassette-spawned states; it also directly calls collection for the collected view. The 1977 view is the initial analog layout. These are **direct actions and state fixtures**, not evidence that a player reached those states. Examples:

- `previews/relay_registration_director_v01/capture_v01/initial_y18_native_960.png`
- `previews/relay_registration_director_v01/capture_v01/drained_y18_native_960.png`
- `previews/relay_registration_director_v01/capture_v01/bulkhead_open_y18_native_960.png`
- `previews/relay_registration_director_v01/capture_v01/cassette_spawned_y18_native_960.png`
- `previews/relay_registration_director_v01/capture_v01/cassette_collected_y18_native_960.png`
- `previews/relay_registration_director_v01/capture_v01/analog_initial_y18_native_960.png`

Integration still needs the `MandelaWorld` background-only hook and fallback, actual timeline swap, input-driven action/recovery and collection, saves, panel scrolling, all dynamic layers, camera edges and relevant tests. Neither these static images nor the synthetic E event establish native-window playback, full traversal, performance, human playthrough or art-gate closure.
