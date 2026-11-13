# Current state — campaign flow and repository separation

The current game is installed at `/Users/nzlab-la/Desktop/Github/6EQUJ5` as a standalone offline repository, with the user-requested flat src layout. `video_game` remains its installed import name and `6equj5-game` remains its command. The historical AI application is installed separately at `/Users/nzlab-la/Desktop/Github/6EQUJ5-AI` from commit 120c39b604bca5a4a9dfef4d34b131b6751da0f9. Both local environments were recreated. Final-location validation gave 1,184 game tests passed with the same two known failures, and 22 AI tests passed. See the [transfer record](../migration/TRANSFER_COMPLETE.md) for backups and exact results.

All authored runtime assets/data, the intro-map briefing, current combat effects, Arc Lance/Nova Scatter temporary weapons, science, progression and save-envelope version 2 are preserved. Live AI adapters/workers were retired; the normal receiver continues through its authored channels. Rebuild civilization text is now owned by this repository.

The pre-separation baseline on a complete working-tree copy was 1,212 passed, 2 failed, 2 live tests excluded. The two failures were the missing FASR-001 legacy portrait source and FIELD_OPS render P95 5.881 ms against the unchanged 5.0 ms threshold. See [migration report](../migration/REPORT.md) for final validation and package evidence.

Historical current-state snapshots, captures and reports are preserved under `_trash/2026-11-13_separation`; [archive manifest](../migration/archive-manifest.json) records their paths and hashes. Art masters, provenance, maintained tools and active test fixtures remain in their owned directories. `_trash` and build outputs are not runtime package contents.

## Campaign flow — 2026-11-13

Boss victories play a 2.6-second breakup using the existing body artwork, followed by a short manual summary. A fresh Enter, controller A or button click can continue immediately, including during the breakup. A guardian's summary leads to its civilization's one-page message; recording that message saves the receipt before travel. Both forms of the final Core must be defeated, and the ending finishes at the title screen with the completed journey saved. Continue can resume a defeated guardian's pending summary without repeating combat or rewards.

The opening map and travel map share the same ordered route and curved connections. Travel shows the actual departure, destination and recovered-message count, and opens the gate at the destination node. Travel can be skipped immediately with a fresh input; arrival still requires a successful save. New Game is visible beside Continue and still requires explicit replacement confirmation. Area briefings no longer stop movement. Victory pages and contact dialogue use measured text wrapping and explicit Next/Return buttons; reading does not advance on a timer. The opening passage is unchanged.

Verification used temporary saves: 97 focused gameplay checks passed, followed by 73 checks covering the repaired route scripts, content, controls, persistence and maintenance conventions. All 52 levels validated and the asset-builder dry run passed. The initial broad run reported 1,191 passed and 11 failed; nine failures were corrected and covered by the successful rerun. Two previously documented issues remain: the missing legacy FASR-001 portrait rebuild source and a frame-budget failure (this run: SCIENCE_LAB total P95 8.373 ms against 8.0 ms). Thresholds and asset checks were preserved. Renderer captures cover the menu, guardian breakup, contact, map, both final forms and ending, with CRT/native and integer-scale inspection. These checks do not establish a human playthrough, physical-controller or audio acceptance.

## Earth route pacing — 2026-11-13

Ohio now connects the access trench, campus, salvage yard and dish directly before the Greenkeeper. The existing campus art is retained. Five duplicate-art corridors are bypassed, and the four active rooms use their native authored widths (3,520 px total rather than 42,240 px). The ordinary Act II–V rooms are 960 px each, with consecutive panorama slices across open boundaries. Walking between areas works in both directions in both combat modes, without an airlock or interaction prompt on the path. Existing boss and relay entry behavior is preserved.

The coupler, feedhorn repair and bosses remain required. Repair now opens the Greenkeeper gate immediately; the 72-second dish defense is optional. Old checkpoint names resolve inside the shorter geometry and support death recovery. Enemy positions, pickups and raised steps fit the new bounds. See [route evidence](evidence/EARTH_ROUTE/2026-11-13/report.md) for the earlier shortening pass and its validation: **1,208 passed, 1 failed** (the existing missing FASR-001 portrait rebuild source). Renderer budget checks passed that run with thresholds unchanged; 125 focused checks, all 52 levels and the asset-builder dry run also passed.

## Player-controlled pacing — 2026-11-13

The repaired gate remains usable during an active, jammed or failed optional defense. Leaving does not grant the defense reward or mark it complete. Space remains jump after a failed defense; R or the retry button restarts it. Boss arrivals accept movement and shooting immediately. Area arrival notices contain only the location name, routine milestone paragraphs and duplicate objective banners are removed, and earned victory/contact/ending screens each fit one short page.

Checks use disposable saves and cover immediate gate entry, fresh keyboard/controller-event/mouse activation, skippable destruction and travel, message receipts, save failures and text wrapping. See [pacing evidence](evidence/FREE_TRAVEL/2026-11-13/report.md) for final results and renderer captures.

## Denver landmarks — 2026-11-13

Neo-Denver now uses a clearer Fitzsimons-inspired sandstone building and the owner's mountain reference, including its pale crest and hillside A. Both remain background scenery in the existing panorama; routes and collision are unchanged. Native and 2× captures with CRT off/on were inspected, including the street/relay walking transition and Synchronicity arena. The README has a fresh Denver screenshot and walking GIF. Masters, reference sources, export command and archive locations are recorded in [art provenance](../../art/source/visual_upgrade/candidates/denver_landmarks_v01/provenance.md). The 58 focused checks, all 52 level validations and asset-builder dry run passed.

Formal gameplay/art gates are not promoted by these changes. Native-window play, physical-controller verification, audio acceptance, airborne armed poses, remaining realm art and strict native performance review remain open. The roadmap retains its gameplay task statuses.
