# Art standard and contact loop

Use EXECUTION_PROTOCOL.md for the session workflow and QUALITY_GATES.md for shared acceptance. Paths are relative to the repository root. The authoritative status table is TODO_ROADMAP.md. Create only files used by the selected task.

This milestone ends at gate G1.

<a id="c01"></a>

## C01 — Review and refine the visual standard

Dependencies — F08. Resource flag — GPU_IMAGE.

Files to create or modify

- `video_game/art/palettes/materials.json`
- `video_game/art/source/civilizations/`
- `video_game/assets/civilizations/manifest.json`
- `video_game/planning/evidence/C01/`

Implementation sequence

1. Inspect all eleven current portrait sets against their source lore and the ART_PRODUCTION rubric.
2. Refine one representative energy, humanoid and machine portrait before updating the remaining candidates.
3. Record per-asset silhouette, material, palette, pixel-grid and composition decisions.
4. Review all charts and distinguish schematic source displays from verified coordinates.
5. Export a native roster and in-terminal comparison, then record each asset review state and remaining polish.

Acceptance checks

- [x] Every civilization has a distinct lore-consistent depiction.
- [x] All required portrait layers load and meet dimension/alpha contracts.
- [x] Every applicable rubric score reaches its threshold with viewed evidence.

Save evidence under `video_game/planning/evidence/C01/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="c02"></a>

## C02 — Normalize bunker layers and lighting

Dependencies — C01. Resource flag — GPU_IMAGE.

Files to create or modify

- `video_game/tools/bunker_scene_builder.py`
- `video_game/assets/bunker/scene_manifest.json`
- `video_game/engine/assets.py`
- `video_game/engine/scenes/bunker.py`
- `video_game/tests/test_assets.py`

Implementation sequence

1. Capture the current room as the composition baseline.
2. Replace alpha-254 context flags with explicit alpha masks and separate flattened inspection previews.
3. Verify intended layer order including distant structure, equipment, floor, player, foreground and lights.
4. Clean layer boundaries and occlusion around the desk, player and door. Preserve flexible light intensity.
5. Check the extracted tiles in repeated layouts and revise visible grid seams.

Acceptance checks

- [x] Ordinary alpha compositing renders the scene correctly.
- [x] Each layer has documented blend behavior and clean boundaries.
- [x] CRT off/on captures meet the art rubric with visible floor contact and readable stations.

Save evidence under `video_game/planning/evidence/C02/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="c03"></a>

## C03 — Build the cancellable AI adapter and worker

Dependencies — F08. Resource flag — GPU_LLM.

Files to create or modify

- `video_game/engine/ai_adapter.py`
- `video_game/engine/ai_worker.py`
- `src/signal_6EQUJ5/ai_engine.py`
- `video_game/tests/test_ai_worker.py`

Implementation sequence

1. Reuse existing civilization prompts, history and cleanup. Add optional client/timeout parameters only where needed and preserve CLI call signatures.
2. Implement bounded request/event queues, session/request IDs and ordered events.
3. Run network/model work off the main thread with finite timeouts and cooperative cancellation.
4. Handle queue saturation, partial streams, connection failure, retries and graceful process shutdown.
5. Use fake clients to exercise failures before one measured local-model stream.

Acceptance checks

- [x] Fake slow streams keep the main loop responsive.
- [x] Cancelled or stale events never reach the active session.
- [x] No Pygame API is invoked by the worker.
- [x] Shutdown completes within its recorded timeout budget.
- [x] One live model stream is measured or explicitly tracked as a remaining GPU_LLM dependency.

Save evidence under `video_game/planning/evidence/C03/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="c04"></a>

## C04 — Implement receiver interaction and dialogue UI

Dependencies — C03. Resource flag — STANDARD.

Files to create or modify

- `video_game/engine/contact_session.py`
- `video_game/engine/scenes/terminal.py`
- `video_game/engine/ui/text.py`
- `video_game/assets/ui/`
- `video_game/tests/test_contact_session.py`

Implementation sequence

1. Implement target selection, 1400–1440 MHz tuning, signal lock and codec-backed 6EQUJ5 intensity display.
2. Add text editing, submit/cancel, transcript wrapping/scrolling, status feedback and keyboard focus.
3. Animate acquisition, pulse extraction, hash-style display, glyph transition and typewriter receipt using timers.
4. Wire worker events to the active session and discard stale IDs.
5. Implement 12 completed exchanges, reconnect and exit/reentry. Correct the 30s label to distinguish 72-second duration and 30-sigma peak.

Acceptance checks

- [x] All eleven targets render without clipped essential text.
- [x] Long replies and supported Unicode wrap and scroll correctly.
- [x] Decode bins match [6,14,26,30,19,5].
- [x] Typing, target switching, cancellation and rapid exit/reentry have regression coverage.

Save evidence under `video_game/planning/evidence/C04/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="c05"></a>

## C05 — Author offline contact routes

Dependencies — C04. Resource flag — STANDARD.

Files to create or modify

- `video_game/data/dialogue_offline.json`
- `video_game/engine/contact_session.py`
- `video_game/tests/test_contact_session.py`

Implementation sequence

1. Create distinct initial messages and authored readiness/evidence branches for all eleven civilizations.
2. Provide structured choices or discoverable evidence actions for guaranteed progression.
3. Add unknown-question responses, reconnect controls and clear offline status.
4. Preserve completed dialogue evidence when switching from live to offline after failure.
5. Exercise the session limit and repeat-contact behavior with the same mission contracts.

Acceptance checks

- [x] Every required evidence route is reachable without a model.
- [x] Civ identity and voice remain distinct.
- [x] Partial AI failures cannot duplicate exchanges or strand the session.
- [x] Offline choices never bypass unmet campaign prerequisites.

Save evidence under `video_game/planning/evidence/C05/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="c06"></a>

## C06 — Implement fragment and hostile-signal rules

Dependencies — C05. Resource flag — THINKING.

Files to create or modify

- `video_game/engine/protocols.py`
- `video_game/data/civilization_missions.json`
- `video_game/tests/test_campaign.py`
- `video_game/tests/test_contact_session.py`

Implementation sequence

1. Define FASR-001 and FASR-007 readiness, evidence, reward and repeat contracts first.
2. Implement deterministic grant validation and typed campaign events.
3. Treat any model-produced grant tag as an untrusted candidate requiring valid IDs, prerequisites and player evidence.
4. Define a bounded Core-mimic detection activity and failure consequence with recovery.
5. Add curated tests for valid grants, forged tags, unrelated IDs, repeated completion and interrupted sessions.

Acceptance checks

- [x] Valid evidence grants the intended fragment once.
- [x] Raw dialogue or malformed model output cannot change campaign state.
- [x] Hostile-signal failure is telegraphed and recoverable.
- [x] Save/reload preserves evidence and unique grant records.

Save evidence under `video_game/planning/evidence/C06/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="c07"></a>

## C07 — Make the first formal-validation workbench playable

Dependencies — C06. Resource flag — STANDARD.

Files to create or modify

- `video_game/engine/scenes/lab.py`
- `video_game/engine/labs/formal.py`
- `video_game/data/lab_scenarios.json`
- `video_game/tests/test_labs.py`

Implementation sequence

1. Add workbench selection and a finite FASR-001 claim/evidence puzzle.
2. Require observation and replication checks before deployment choice.
3. Return a versioned validation record and apply its reward through campaign events.
4. Provide feedback for wrong classification, incomplete evidence and retry.
5. Save completion and reopen the lab without repeating rewards.

Acceptance checks

- [x] A fragment becomes a validated protocol through normal player interaction.
- [x] Incorrect answers can be corrected with explanatory feedback.
- [x] Speculative claim tier and hostile intent remain distinct.
- [x] Reload preserves the result and deployment decision.

Save evidence under `video_game/planning/evidence/C07/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="c08"></a>

## C08 — Verify the contact-to-validation loop

Dependencies — C02, C07. Resource flag — GPU_LLM.

Files to create or modify

- `video_game/planning/evidence/C08/`
- `video_game/tests/test_contact_session.py`
- `video_game/tests/test_labs.py`

Implementation sequence

1. Run a fresh-game route through receiver, FASR-001 evidence, formal lab, deployment and save/reload.
2. Exercise an offline route and a real local-model route with the same prerequisites.
3. Test failure during stream, target switch, pause, exhausted exchanges and reopening.
4. Record visual rubric results and frame responsiveness. Fix failures before promoting the gate.

Acceptance checks

- [x] Gate G1 passes with linked route evidence.
- [x] The loop uses normal UI and persistent campaign state.
- [x] Required live-inference checks have actual results.

Save evidence under `video_game/planning/evidence/C08/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.
