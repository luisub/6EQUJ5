# Remaining scene render routes and geometry — v01

Read-only integration research for existing scenes. The captures below are diagnostics and direct-position fixtures, not proof of a playable traversal, approved replacement art, or an integrated native background. Preserve existing locked source and exports. Coordinates are logical pixels unless marked native; density 2 doubles coordinates.

## Dimensions and routing

| Existing scene | Room / canvas | Camera and diagnostic coverage | Current draw route |
| --- | --- | --- | --- |
| Bunker | Fixed 480 × 270 canvas | Fixed view; guide is 960 × 540 | `BunkerScene.render`; manifest-loaded 480 × 270 layers surround actor drawing. |
| Mandela annex (`act_01_mandela_test`) | 30 × 18 tiles of 16 = 480 × 288 | 480 × 270 view, x = 0, y = 0…18; 960 × 576 full-room guide | `FieldOpsScene.render` → `FieldReality.world.render` → `MandelaWorld.render` → `Room.render_background`. |
| Dodleston relay (`act_04_dodleston_relay`) | 480 × 288 | Same as annex | Same `MandelaWorld` route. |
| 1977 flashback (`flashback_ehman_1977`) | 480 × 288 | Same as annex | Non-reality `FieldOpsScene` route → `Room.render_background`, tiles and objects, plus `FlashbackController.render_overlay`. |

Sources: `engine/scenes/bunker.py`, `engine/scenes/field.py`, `engine/field_reality.py`, `engine/mandela_world.py`, `engine/flashback.py`, `engine/world.py`, `data/levels/`. `FieldReality.load()` creates a `MandelaWorld` for the annex and relay; the 1977 flashback has its own controller. The current field native-family background hook is in the non-reality path, so it does not by itself cover the annex/relay. A future implementation must select a validated background or legacy fallback before `MandelaWorld` renders tiles and stateful objects, suppressing precisely its legacy background when successful. Keep foreground geometry, interactables, player, effects, interface and modal overlays above that background; do not change global rendering callbacks. Verify camera rounding and native-to-logical registration against real tile edges at y=0 and y=18.

## Bunker: fixed layered hub

`AssetCache.bunker_layers()` reads `assets/bunker/scene_manifest.json`; six 480 × 270 layers form the scene. The first four layers precede Mateo and his ground ellipse; the final two are drawn afterward, then station labels, save/HUD and dossier. Flattening all six is useful for a geometry guide but does **not** represent runtime actor depth. The existing bunker is a locked asset group in the asset build; preserve its master, manifest and exported layers. The fixed scene also uses cached Mateo sprite strips / manifest sprite; a background upgrade must retain original positioning and interaction ranges.

`BUNKER_STATIONS` uses Mateo's **top-left x** for activation, not fixture bounds. Movement clamps that x to 124…364:

| Station | Trigger x | Center used in fixture |
| --- | ---: | ---: |
| Lab | 124…160 | 140 |
| Receiver / terminal | 170…260 | 215 |
| Repair | 275…315 | 295 |
| Field airlock | 330…364 | 348 |

Diagnostic `bunker_station_bounds_960.png` overlays those ranges on a flattened six-layer composite; visible line positions do not claim physical extents of consoles or doors. Individual `bunker_*_fixture_960.png` files use actual rendering at direct station positions. Keep station prompts, HUD, save status and dossier readable and reachable. Verify native art registration with the existing actor between background and foreground layers, not only against the flattened guide.

## Annex and relay: state and interaction layers

`MandelaWorld.render` draws the legacy room background, active-timeline tiles, moving platforms, pickups, doors, grapple anchors and its weather/transition effects. The field scene then draws the remaining field elements, actors, effects and UI. `MandelaWorld.render` is not a call to generic `Room.render_objects`: types with no branch there must not be assumed to appear merely because their rectangles exist in a room JSON. The field route also calls room weather later; inspect real output before changing that ordering or interpreting whether weather is drawn twice.

| Scene | Existing variants and interaction-sensitive geometry |
| --- | --- |
| Annex | `2029_CORE` and `1977_ANALOG` collision/object variants; default spawn (32,208), corridor spawn (144,208), exit (440,192). 2029 coupler pickup at (64,208); 1977 log pickup at (220,208); door (300,192,16,48); moving platform (200,160,32,12) travels toward x=280; grapple anchor (112,96); field low-cover region (48,224). Preserve collected/uncollected, door state, platform travel and timeline switching. |
| Relay | `2029_CORE` and `1977_ANALOG` grids; relay entrance (32,208), terminal-post spawn (80,208), exit rectangle (16,192,32,48). Authored terminal (96,192), bulkhead (256,192), valve (160,208) and cassette (384,208); cassette is timeline/state dependent. Terminal input uses proximity to x=96 and a substantial message/choices overlay. Saved power/coolant, cassette, failure and recovery states remain authoritative. Relay message-era labels 1985/2031 are content semantics, not two extra playable-room art variants. |

The relay's terminal and other `prop` types do not acquire a generic `Room.render_objects` rendering branch through the `MandelaWorld` route. Check their actual gameplay cues and interaction in real play before designing around a visual fixture; the numbered guides are authored object bounds, not evidence that every rectangle is visible or interactive in every state. Never bake door status, pickup presence, platform position, collision, prompts or state-dependent highlights into a static background.

## 1977 flashback: separate route and overlay

`FlashbackController` renders an amber scene tint and a large printout panel when open, before field actors and later interface elements. The printout has inspected and annotated states, including its real telemetry and the existing red annotation. Its interaction stages and x ranges govern inspection, reel and exit. Preserve wording, controls, the annotation, and return-to-origin state. `Room.render_objects` draws its supported terminal, hazard, antenna, anchor, exit and checkpoint kinds; authored `prop`/`cache` entries such as pen, window and tape deck do not gain generic rendered sprites from that function alone. Their coordinate outlines in the guide are diagnostic, not proof of rendered objects.

## Reproducible diagnostic set

Script: `_trash/2026-11-13_separation/historical-reviews/art/reviews/visual_upgrade/previews/prototype_geometry_research_v01/capture.py`. Captures: `_trash/2026-11-13_separation/historical-reviews/art/reviews/visual_upgrade/previews/prototype_geometry_research_v01/capture_v01/`; `context.json` records fixture setup, source/output information, guide legend and hashes. The script uses a temporary save and refuses an existing output directory. Example from repository root:

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. /opt/anaconda3/envs/6equj5_game/bin/python _trash/2026-11-13_separation/historical-reviews/art/reviews/visual_upgrade/previews/prototype_geometry_research_v01/capture.py --output-dir /tmp/6equj5_prototype_geometry_fresh
```

Full-room files `annex_*_geometry_960x576.png`, `relay_*_geometry_960x576.png`, and `flashback_1977_ANALOG_geometry_960x576.png` use actual tile geometry with numbered cyan object rectangles and orange exit rectangles. Matching `*_fixture_960.png` files are rendered scene fixtures; timeline/position is set directly, not reached through normal player traversal. Flashback inspect and annotate fixtures exercise the E interaction after direct placement; `context.json` records observed stages. Bunker flattened and range guides are diagnostic overlays, not runtime composites.

Future acceptance should include normal entry, return and Continue; both timeline variants, each relevant collected/door/terminal/printout state; actor and platform overlap; near/far camera bounds; CRT modes; prompts and overlays; and a failure/absent-family fallback with no partial background draw. The captures establish coordinate evidence only; they do not assert successful complete traversal or visual approval.
