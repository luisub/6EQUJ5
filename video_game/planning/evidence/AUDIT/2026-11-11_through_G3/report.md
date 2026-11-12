# Functional audit through Milestone 3 — 2026-11-11

## Result and scope

Audited the current foundation/contact/action/science/reality implementation against the task cards, actual router/input/save callers and current tests. Corrected defects below and added normal-key integration coverage. Live AI was deliberately excluded as authorized by the user. The current code is substantially more integrated than the previously claimed G3 completion. **G2/G3 acceptance remains pending** for full fresh-save normal-playthrough/fairness, outstanding art review, audible audio and real-display performance. Earlier reports and static scorecards claiming all gates passed do not establish these checks.

## Defects fixed

| Area | Defect | Correction and verification |
|---|---|---|
| S04 science | Beginner and advanced scenarios shared completion identity; beginner validation could mark advanced complete | Records use `(fragment ID, scenario ID)` uniqueness; all four workbenches check scenario ID. Eight scenarios now complete via scene keyboard handler and survive actual SaveStore reload |
| S04 consequences/readability | No delayed consequence record; compact lab prompts truncated essential questions | Persistent scenario-keyed consequence notices delivered on later bunker visits. H opens complete scrollable scenario prompts, evidence, checks, deployment descriptions, feedback and references |
| S05/S10 input | No dash/grapple bindings; C both crouched and activated ability; boss polled physical keys independently | Shared field/boss mapper: Shift dash, G grapple, C crouch, K/Alt ability; consistent press/hold/release. Duplicate PlayerInput declarations removed |
| S05 unlock/session state | Unlock checks accepted false flags or empty inventory keys; unlocks could stay true after switching campaigns | Recompute from current campaign, require positive inventory/true flags, reconstruct scene actors/equipment/contact sessions for New/Continue |
| F07 pause | Clearing InputManager alone left field's held-key cache active | Clear both control caches and pending edges on pause/focus/resize; crouch derives from held input |
| S06 persistence | MandelaWorld used an incompatible apply_event signature and nonexistent inventory mutators | Typed campaign timeline events with unique IDs, registered one-shot pickup events, durable room snapshots through Campaign |
| S06 platforms | Moving platforms were represented/rendered without a reliable landing/convey path | Swept landing and collision-safe convey; a falling-player test verifies contact. Authored grapple anchor is visible and usable |
| S06/S07 reachability | Timeline and relay code had no playable field controller/controls | Post-Act-I M annex, T safe swap, F6 relay, F7 flashback, F8 annex. New FieldReality owns normal input, relay panel, update/render/persistence |
| S07 safety/save | Relay mutated unregistered flags directly into campaign, potentially invalidating saves; unsafe geometry edits could commit with no safe displacement | Relay state stored in world snapshot; the bulkhead now has actual closed/open collision tiles and the recovered cassette uses a registered inventory grant; registered grant events own durable rewards. No-displacement edits roll back grid/layers/objects before flags or campaign change |
| S08 | Flashback integration existed but lacked a normal route from gameplay | Annex connector plus key-driven printer/vault sequence and return, verified with ordinary movement and interaction events |
| S09 | Faction archetypes only instantiated by component tests | N cycles four bounded mixed pairs through normal field control. Tests exercise all eight extended/representative archetypes; Static Hound is already in Act I |
| S10 counterplay | Tape activation lacked enemy context; dash damage helper had no combat caller; decoy movement attributes absent | Field supplies combat context; tape disrupts actual enemy locks; manager applies swept one-hit-per-dash damage; stationary decoy provides prediction velocity and visible outline |
| A09 boss | Defeated player could auto-respawn while boss state continued | Stop boss update on player death until explicit R retry; normal mapped movement and retry tested |
| Rendering | Field/boss redraw left old scene text behind | Clear canvas before world render; native/3x scene captures inspected |
| C05/C06 | Contact mutated private campaign state; quota could strand a session | Validated record_contact event after real transmission; `/restart` preserves evidence and opens another 12-exchange session; system help remains usable at quota |
| Packaging | Wheel included planning-only Python; clean package omitted namespace-only boss directory | Explicit package data/discovery and real bosses package. Clean wheel inspection and installed external-cwd headless launch |
| Tooling/evidence | A14/S11 card generators embedded unmeasured verdicts, wrong science/era/meter labels | Archived both with hashes and restoration log. Actual runtime capture tool makes no gate verdict; historical outputs remain preserved |

The runtime connector uses existing prototype rooms. It does not implement the later acts/campaign or claim those milestone-4 tasks are complete. Continue intentionally returns to a safe bunker, restoring room state on reentry. Temporary actors/bullets/buffs and cooldown/energy state reset on New/Continue; incomplete lab trials reset on scenario change or exit. These rules are now documented in CONTROLS and DATA_CONTRACTS.

## Coverage against the plan

| Task scope | Current evidence and limits |
|---|---|
| F01–F08 | Existing baseline/build/state/save/input suites pass; wheel contents/install inspected. Independent backup, cross-platform locks and power-loss/concurrent-save checks remain I11–I13 |
| C01–C02 | Existing artwork contracts/locked assets pass. Art authorship, eleven-civilization lore and subjective rubric review were not re-certified by this audit |
| C03–C06 | Fake-worker/offline/contact/grant regression suites plus restart and validated-contact integration; live inference omitted by request |
| C07–C08 | Actual terminal input earns evidence; all lab keyboard paths and SaveStore persistence exercised. Historical live claims are not new live evidence |
| A01–A07 | World/player/animation/combat/objective suites pass; focused input and package fixes above. Full user-play traversal/fairness remains a separate acceptance |
| A08–A11 | Existing field-defense integration, 72-second timing/retry/reward, mission graph, boss and environment tests pass; boss mapper/death behavior fixed |
| A12–A14 | Functional/audio-device fallback/profile tests pass. No new listening session, real-window 120-second benchmark or complete normal-controls fresh-save Act I playthrough; tasks reopened for acceptance |
| S01–S04 | Eight scenarios across four workbenches completed through keyboard handlers, independent per-scenario rewards and pending consequence notices, saved/reloaded. Scientific sources/claims not independently revalidated here |
| S05 | Runtime arsenal/abilities share focused controls; unlock/new-save isolation checked; costs/cooldown and status tests pass |
| S06 | Router/keyboard swaps, campaign timeline sync, pickup persistence, moving-platform contact, safe rejection and save/load tested |
| S07 | Normal relay panel route, wrong choice, recalibration, three puzzles and save/reentry restoration; no-safe-displacement rollback tested |
| S08 | Normal movement/keys complete flashback, return to origin; real child process loads saved anchor/world state |
| S09 | Runtime encounters and existing faction/counter tests pass; final mixed-encounter fairness/art review remains open |
| S10 | Actual Shift/G/K controls, tape context, dash damage caller and existing wall/grapple/dash collision tests; teaching/fairness still needs player review |
| S11 | Component and newly integrated routes pass; no full combined human route/visual signoff. Gate remains pending |

## Reproducible checks

Host: macOS arm64, Python 3.12.16, pygame-ce 2.5.8; dummy SDL display/audio unless explicitly stated. Run from repository root:

```
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests tests -q -k 'not live_ollama_stream_if_available and not gate_g1_live_local_model_and_offline_route_parity'
/opt/anaconda3/envs/6equj5_game/bin/python -m video_game.tools.validate_content
/opt/anaconda3/envs/6equj5_game/bin/python -m video_game.tools.build_assets --dry-run
/opt/anaconda3/envs/6equj5_game/bin/python -m video_game.tools.capture_runtime_audit --output-dir video_game/planning/evidence/AUDIT/2026-11-11_through_G3/captures
```

Final test result and package verification are recorded in CURRENT_STATE/PROGRESS_LOG after the last run. All seven authored levels validated; all fourteen locked groups preserved. `tests/test_runtime_integration.py` discloses prerequisite fixtures: Act I completion is seeded for annex tests, pickup/dash collision tests position actors, and these do not constitute a complete Act I playthrough. The flashback and relay movement, lab solutions and actual child-process reload run without direct reward injection during the behavior under test.

Scene captures include four workbenches, full-text view, annex, relay panel and flashback at native 480×270 and integer 3×; these use disclosed fixture preconditions (capture_context.json). Inspected native workbench/annex/flashback and 3× relay/full-text images. Captures are static UI inspection, not art acceptance or proof of combat fairness.

Build check uses `python -m pip wheel . --no-deps --no-build-isolation --wheel-dir /tmp/6equj5_last_verified_wheel` from a clean build directory. Wheel is installed with `pip install --no-deps --target /tmp/6equj5_last_verified_install ...`; with that path on PYTHONPATH, dummy SDL and a disposable save directory, `run_game(max_frames=3)` launches from `/tmp` and confirms import origin inside the installation. Dependencies are supplied by the existing test environment; this is not native release certification or a dependency-free machine test.

## Organization, documentation and recovery

Runtime/data/assets/source-master responsibilities remain separated. Added narrow field_reality integration module rather than duplicating domain models. Large faction/weapon/player modules remain a maintainability risk; split by responsibility when changing their domain, preserving current callers/tests. Source masters, prior evidence, useful builders and all recoverable archives were retained.

Updated AGENTS.md, CONTROLS.md, tools README, current handoff, roadmap, milestone checklists, progress/issues, execution prompt/protocol, code map, contracts, quality-gate guidance and player README. Existing historical logs retain prior claims with this corrective record taking precedence. Tests/source masters/planning/archives are excluded from runtime wheel. Build intermediates created by packaging were removed from the checkout after verification.

Before edits, 400 original files were archived and hash-verified in `_trash/2026-11-11_G3_audit/before.tar.gz`, with member SHA-256 in manifest.json. Two retired generators are additionally logged in `retired/retirement.json` and `_trash/TRASH_LOG.md`; verify hash before restoring to a free original path. New files have no original to restore. Git still does not track video_game; this local snapshot is not an independent-device backup.

Final package check: 434 wheel entries, forbidden development directories absent, SHA-256 `95cb1bed6cc5eb160cbde26089123138fa68335bbd4e3f1169734126920a5ae5`. Installed import origin confirmed under `/tmp/6equj5_last_verified_install`; 3-frame headless boot passed outside checkout.

Final combined regression: **356 passed, 2 live-AI tests deliberately deselected in 13.37s**. New runtime integration module: 13 tests. `git diff --check` passed for tracked edits.
