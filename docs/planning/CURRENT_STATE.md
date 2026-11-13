# Current state — campaign flow and repository separation

The current game is installed at `/Users/nzlab-la/Desktop/Github/6EQUJ5` as a standalone offline repository, with the user-requested flat src layout. `video_game` remains its installed import name and `6equj5-game` remains its command. The historical AI application is installed separately at `/Users/nzlab-la/Desktop/Github/6EQUJ5-AI` from commit 120c39b604bca5a4a9dfef4d34b131b6751da0f9. Both local environments were recreated. Final-location validation gave 1,184 game tests passed with the same two known failures, and 22 AI tests passed. See the [transfer record](../migration/TRANSFER_COMPLETE.md) for backups and exact results.

All authored runtime assets/data, the intro-map briefing, current combat effects, Arc Lance/Nova Scatter temporary weapons, science, progression and save-envelope version 2 are preserved. Live AI adapters/workers were retired; the normal receiver continues through its authored channels. Rebuild civilization text is now owned by this repository.

The pre-separation baseline on a complete working-tree copy was 1,212 passed, 2 failed, 2 live tests excluded. The two failures were the missing FASR-001 legacy portrait source and FIELD_OPS render P95 5.881 ms against the unchanged 5.0 ms threshold. See [migration report](../migration/REPORT.md) for final validation and package evidence.

Historical current-state snapshots, captures and reports are preserved under `_trash/2026-11-13_separation`; [archive manifest](../migration/archive-manifest.json) records their paths and hashes. Art masters, provenance, maintained tools and active test fixtures remain in their owned directories. `_trash` and build outputs are not runtime package contents.

## Campaign flow — 2026-11-13

Boss victories now play a 2.6-second breakup using the existing body artwork, followed by a manual mission summary. A guardian's summary leads to its civilization's message; recording that message saves the receipt before travel. Both forms of the final Core must be defeated, and the ending finishes at the title screen with the completed journey saved. Continue can resume a defeated guardian's pending summary without repeating combat or rewards.

The opening map and travel map share the same ordered route and curved connections. Travel shows the actual departure, destination and recovered-message count, and opens the gate at the destination node. New Game is visible beside Continue and still requires explicit replacement confirmation. Earth briefings, victory pages and contact dialogue use measured text wrapping and explicit Next/Return buttons; reading no longer advances on a timer.

Verification used temporary saves: 97 focused gameplay checks passed, followed by 73 checks covering the repaired route scripts, content, controls, persistence and maintenance conventions. All 52 levels validated and the asset-builder dry run passed. The initial broad run reported 1,191 passed and 11 failed; nine failures were corrected and covered by the successful rerun. Two previously documented issues remain: the missing legacy FASR-001 portrait rebuild source and a frame-budget failure (this run: SCIENCE_LAB total P95 8.373 ms against 8.0 ms). Thresholds and asset checks were preserved. Renderer captures cover the menu, guardian breakup, contact, map, both final forms and ending, with CRT/native and integer-scale inspection. These checks do not establish a human playthrough, physical-controller or audio acceptance.

## Earth route pacing — 2026-11-13

Ohio now connects the access trench, campus, salvage yard and dish directly before the Greenkeeper. The existing campus art is retained. Five duplicate-art corridors are bypassed, and the four active rooms use their native authored widths (3,520 px total rather than 42,240 px). The ordinary Act II–V rooms are 960 px each, with consecutive panorama slices across open boundaries. Walking between areas works in both directions in both combat modes, without an airlock or interaction prompt on the path. Existing boss and relay entry behavior is preserved.

The coupler, feedhorn, full 72-second defense and all bosses remain required. Old checkpoint names resolve inside the shorter geometry and support death recovery. Enemy positions, pickups and raised steps fit the new bounds. See [route evidence](evidence/EARTH_ROUTE/2026-11-13/report.md) for scope and validation. Final full-suite result: **1,208 passed, 1 failed** (the existing missing FASR-001 portrait rebuild source). The renderer budget checks passed this run; thresholds are unchanged. The focused run passed 125 checks, all 52 levels validate, and the asset-builder dry run passes.

Formal gameplay/art gates are not promoted by this separation. Native-window play, physical-controller verification, audio acceptance, airborne armed poses, remaining realm art and strict native performance review remain open. The roadmap retains its gameplay task statuses.
