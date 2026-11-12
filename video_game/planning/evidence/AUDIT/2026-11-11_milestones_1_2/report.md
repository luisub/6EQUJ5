# Milestone 1 and 2 audit — 2026-11-11

## Scope and verdict

Reviewed the roadmap, protocol, quality gates, C01–C08 and A01–A14 task cards, current handoff, issue log, gate reports, route harness, live-model tests, performance tool, defense implementation and field-scene callers. Ran the combined test suite and locked-asset dry run. This is an initial audit, not a complete independent acceptance of every visual, interaction and performance requirement. No manual player playthrough, visual rubric re-review, audible test or live model session was performed. G1 and G2 cannot currently be accepted.

## Findings, in priority order

1. **Blocker — A08/A10:** `DishDefenseHoldout` in `engine/objectives.py` has no runtime scene caller: searching the engine finds only its definition. The field scene has no start/update, wave spawn, player unjam, hostile dish damage, failure/retry or completion grant for the holdout. Yet the boss transition requires `dish_defense_completed`. Thus the normal route stops at the catwalk. The standalone holdout tests do not cover scene integration. Integrate the entire encounter, not merely a timer or forced reward.
2. **High — A14:** `tools/play_act_01.py` directly changes scenes, positions the player, injects a coupler event, creates a detached holdout, calls its completion reward, directly damages the boss and applies its reward. It bypasses the interactions being certified. Its reload constructs a second state machine in the same process, not a new process. The 13.5–19.5 minute values in `generate_a14_evidence.py` are hardcoded estimates, not observed player timings. Do not treat the report's gate pass, player playtime, or inferred lack of progression defects as established. Run the route with normal controls, record actual duration and verify recovery and disk reload in a separate process.
3. **High — C08:** `test_gate_g1_live_local_model_and_offline_route_parity` checks only receipt of an assistant reply; it does not exercise live evidence acquisition, validation or parity. Both live-model tests skipped in this audit. Prior reports describe measurements, but the cited parity test cannot establish the stated conclusion. Verify a genuine live route and normal UI plus persistence; investigate how evidence can be earned in live mode before accepting G1.
4. **Medium — A12/A13:** A12's checked audible acceptance is not supported by an identified listening session in its report. A13's CLI constructs `BenchmarkProfileSession(..., headless=True)`, so the reported numbers cannot establish real display/audio performance. A 30-frame `builtins.open` interception cannot establish zero disk activity from other APIs or threads. Record an audible review and representative 120-second real-window benchmark with hardware, settings, workload, AI state and raw timings.
5. **Medium — test evidence mutation:** The initial combined pytest run overwrote `planning/evidence/A14/playthrough.json` via the A14 runner. The prior file contents were not recovered. The test fixture now redirects that output to pytest's temporary directory. A focused rerun passed, and SHA-256 of the existing evidence file remained `c0b17435d6cc6561e55486321b033e02d93b5afa2b72de9a55ff3206495327cd` before and after. Existing A14 telemetry is not independent gate evidence.
6. **Low — plan drift:** The roadmap summary was stale, current-state handoff repeats sections and contains contradictory historical statements, C01's task card has unchecked criteria despite done status, and `QUALITY_GATES.md` still shows retired `video_game.engine` builder/preview commands. An audit banner and roadmap correction identify the current situation; the remaining documents need reconciliation.

## Coverage and limitations

- C01–C02: Existing reports and tests exist; art rubrics and layer appearance were not independently viewed during this audit. C01 checkboxes are inconsistent with its status.
- C03–C07: Combined tests passed apart from the live test; historical reports exist. No independent manual cancellation, all-civilization visual review, or complete normal-input contact-to-lab route was performed.
- C08: Live reply test does not substantiate live progression parity; G1 reopened.
- A01–A07, A09, A11: Existing automated tests pass, but this audit has not independently exercised every acceptance item or confirmed combat fairness, animation and art in motion.
- A08/A10: Definite integration blocker described above.
- A12–A14: Acceptance evidence gaps described above; reopened. S01 implementation remains in place, but S02 is planned until A14 is accepted again.

## Checks executed

From repository root, macOS host, dedicated `/opt/anaconda3/envs/6equj5_game/bin/python`, dummy SDL display and audio:

```
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests tests -q
# 249 passed, 2 skipped in 11.76s; live Ollama checks skipped
/opt/anaconda3/envs/6equj5_game/bin/python -m video_game.tools.build_assets --dry-run
# 14 locked groups preserved
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_act_01_playthrough.py -q
# 3 passed in 0.26s; evidence file hash unchanged
```

The first attempt used the default Python and failed collection because that environment lacks pygame; the dedicated project environment worked. Passing component tests do not prove playability. The combined suite ran before the fixture-only change; the affected suite was rerun afterward.

## File inventory and preservation

The entire `video_game/` tree is untracked (I11); Git cannot restore it. `_trash` is approximately 369 MB, including snapshots with manifests and prior source; retain it until a separate informed cleanup decision and a verified independent backup. `art/source` contains rebuild masters, `assets` runtime content, and `planning/evidence` project evidence; none are disposable based on filename alone. Found 89 `.pyc` files during inspection: regenerable interpreter caches, but left untouched because the project asks for conservative retirement. No assets, user files or snapshots were deleted. Generated evidence scripts and images require a reference-by-reference review before retirement. Tests can recreate caches.

Before edits, planning documents and the modified test were copied to `video_game/_trash/2026-11-11_milestone_audit/video_game/`; SHA-256 records are in `MANIFEST.sha256`. Planning files were verified against copies before editing. To restore, verify the manifest from the repository root, then copy the desired archived file to its original `video_game/` path after preserving any later edits. The A14 JSON overwritten by the initial test run is not included as an original backup.

## Ordered remaining work

1. Implement and test A08 scene integration: actual waves, readable telegraphs and HUD, jamming counterplay, attack/dish damage, pause, death, retry, room transitions, one-shot completion and save/reload.
2. Exercise A10 progression through real field scene and bunker routing, without injecting campaign events.
3. Verify C08 with actual available Ollama and complete both offline and live prerequisite/validation routes through normal UI; document genuine results.
4. Perform A12 audible review and A13 representative graphical performance measurement; correct any defects found.
5. Run A14 from fresh save using normal controls with route captures, actual elapsed duration, failures/retries and separate-process save/reload. Revisit D02 based on measured observations.
6. Re-review the remaining milestone cards and visible assets against each acceptance check, reconcile status and commands, then rerun both checkpoint suites and dry-run asset audit before gate promotion.
