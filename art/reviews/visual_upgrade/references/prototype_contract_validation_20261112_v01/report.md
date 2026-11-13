# Prototype opaque family contract and route preparation

2026-11-12. Added the three explicitly selected schema-3 backdrop descriptors to the shared allowlist. No prototype asset was promoted. The existing `ohio_bunker_v1` descriptor and schema-1/schema-2 contracts are unchanged.

| Family | Existing room ID | Viewport / world | Opaque native export |
| --- | --- | --- | --- |
| `mandela_annex_v1` | `act_01_mandela_test` | 480 × 270 / 480 × 288 | `backdrop_960x576.png` |
| `dodleston_relay_v1` | `act_04_dodleston_relay` | 480 × 270 / 480 × 288 | `backdrop_960x576.png` |
| `ehman_1977_v1` | `flashback_ehman_1977` | 480 × 270 / 480 × 288 | `backdrop_960x576.png` |

Density is 2, origin `[0,0]`, rounding `logical_nearest`, and repeat false. Existing `backdrop_manifest_template` returns independent nested values; the existing builder accepts each family and uses the same lock, image validation, staged revalidation, journal recovery and manifest-last promotion. At native density camera y=0…18 gives source y=0…36 and viewport ends y=540…576; x remains 0. Runtime bounds and fallback must be validated by the loader/caller owner; contract dimensions alone do not prove rendering registration.

Fresh backup copies were compared before editing under `references/prototype_contract_backup_20261112_v01/`: `room_art_contracts.py.bak` SHA-256 `53a05b7fce4f68732530c02b0e54ff6e1aabcf0e0353e73dc5ffa51453a74a84`; `test_room_family_transaction.py.bak` SHA-256 `7f658ecd68fc3df4217d084190363e5cb4f51fc755e8a69befeab6df0f7804ec`. The builder itself required no edit.

From repository root:

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_room_family_transaction.py video_game/tests/test_approach_family_transaction.py -q
```

Exit 0; `41 passed in 1.16s`; full output `focused_tests.log`. The new parametrized cases validate exact descriptors, fresh mutable return values, no-write source review and per-family isolated complete installation under pytest temporary roots. Existing shared transaction tests cover manifest-last order, rollback, symlink/lock rejection and interrupted-process recovery. Synthetic solid-color PNGs verify mechanics, not reviewed art or actual scene routing. Source validation and provenance must be repeated against each reviewed candidate separately; none was supplied or promoted for these three families in this contract step.

## Normal-input route preparation

Existing `video_game/tools/mechanics_route.py` supplies useful event-driven evidence: a temporary save is advanced through the earned Act I route, then title Continue and M enter the annex; F8/F6 swap annex/relay, T exercises `1977_ANALOG` and `2029_CORE`, and physical-event movement and E interact with the relay. The script deliberately causes and recovers from the relay failure, opens the door, collects the cassette, enters 1977 with F7, inspects and annotates the printout, interrupts once, completes and reenters, and verifies child-process Continue restores timeline, relay door and cassette. `video_game/tests/test_mechanics_route.py` asserts these trace milestones. These are automated input events in dummy SDL, not human play or native-window evidence.

For integration, adapt or supplement that route in the technical owner's test/capture harness using **temporary** asset and save roots. First stage only reviewed candidate families through the real builder; record the exported hash and actual loader-selected identity per room. Do not interpret a successful route alone as proof the new family loaded: assert the selected family and distinguish absent/corrupt/pending fallback. Existing `mechanics_route.py` uses configured assets and does not expose an asset-root argument, so invoking it unchanged would not establish a temporary-family integration test. Its CLI also creates an existing output directory if needed; choose a fresh path explicitly to preserve prior evidence.

Capture and check, when candidate assets exist:

- Annex: normal M entry, both timelines via T, moving platform and anchor over background, then exit and reentry; verify foreground tile alignment and y=0/y=18 camera extremes with a separately disclosed fixture if ordinary movement cannot reach both.
- Relay: F6 entry, terminal panel through E, failure/recovery, door open/closed and cassette before/after pickup, plus restored state after child-process Continue. No baked status may replace the live cue.
- 1977: F7 entry, E printout inspection and annotation, interruption and completion/return, then reentry. Preserve tint, printout telemetry, actor/HUD ordering and prior state.
- Per family, cover valid, absent and corrupt/partial/pending family behavior as well as unrelated-room routing, CRT on/off and any non-integer camera rounding relevant to the actual caller. A true one-native-pixel sentinel can show native rendering and crop alignment; compare terrain registration and z-order, not just a color present somewhere on screen.

The independent source audit and geometry guides are `references/remaining_scene_render_routes_v01.md` and `previews/prototype_geometry_research_v01/capture_v01/`. The latter contains direct-position/direct-timeline fixtures and is not an earned route. Existing route code was read for this plan; it was not rerun in this contract task. No new room, physics or save behavior is requested here.
