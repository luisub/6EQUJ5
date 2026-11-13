# Foundation and safe migration

Use EXECUTION_PROTOCOL.md for the session workflow and QUALITY_GATES.md for shared acceptance. Paths are relative to the repository root. The authoritative status table is TODO_ROADMAP.md. Create only files used by the selected task.

This milestone ends at gate G0.

<a id="f01"></a>

## F01 — Record the current baseline

Dependencies — none. Resource flag — STANDARD.

Files to create or modify

- `video_game/planning/CURRENT_STATE.md`
- `video_game/planning/evidence/F01/2026-11-10_baseline/report.md`

Implementation sequence

1. Inspect current code, manifests, sources, tests and repository status.
2. Run existing game and CLI suites and record their scope.
3. Inspect the rendered bunker and civilization roster.
4. Record concrete defects, test side effects, environment and next task.

Acceptance checks

- [x] Actual test output is recorded.
- [x] Implemented behavior and pending systems are distinguished in the baseline.
- [x] Source documents are recoverable from verified archive snapshots.

Save evidence under `video_game/planning/evidence/F01/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="f02"></a>

## F02 — Make checkpoint checks support readable development

Dependencies — F01. Resource flag — STANDARD.

Files to create or modify

- `video_game/tests/test_checkpoint_audit.py`
- `video_game/tests/test_engine_boot.py`
- `video_game/engine/preview_assets.py`
- `video_game/planning/QUALITY_GATES.md`

Implementation sequence

1. Capture hashes of active assets before tests and review the current audit assertions.
2. Replace the hard 220-line cap and duplicated file allowlist with syntax, explicit import, relevant manifest and behavior checks. Retain clear purpose/modification headers.
3. Move automatic test screenshots into pytest temporary output. Add an explicit preview command with an output-directory argument.
4. Keep preview_assets.py as a temporary documented tool entry until F08 moves it into tools. Record the runnable command.
5. Reconcile the maintenance workflow with these checks and record recovery handling for the currently untracked game folder.

Acceptance checks

- [x] Both suites pass with unchanged runtime asset hashes.
- [x] An intentional preview still writes inspectable PNGs to a chosen evidence directory.
- [x] Adding a legitimate scene module needs no duplicated allowlist edit.
- [x] No readability rule encourages compressed one-line logic.

Save evidence under `video_game/planning/evidence/F02/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="f03"></a>

## F03 — Make asset builds safe and recoverable

Dependencies — F02. Resource flag — STANDARD.

Files to create or modify

- `video_game/engine/build_assets.py`
- `video_game/engine/civ_art_builder.py`
- `video_game/engine/bunker_scene_builder.py`
- `video_game/engine/mateo_sprite_builder.py`
- `video_game/tests/test_assets.py`

Implementation sequence

1. Enumerate source and output groups and every write performed by each builder.
2. Make normal entry points preserve locked exports and manifests. Add explicit selected replacement and dry-run options.
3. Replace first-glob source selection with explicit source mappings. Validate all required source inputs before writing.
4. Stage each complete asset group, validate it, archive replaced files, then promote exports and metadata together with rollback handling.
5. Add regression cases for locked groups, missing sources, missing related outputs and simulated failure during promotion.

Acceptance checks

- [x] Normal builds preserve hashes of all locked face, environment, chart, composite and manifest records.
- [x] A selected replacement changes only its selected group and records recovery paths.
- [x] An interrupted build restores the previous usable group and manifest.
- [x] Running twice gives stable outputs for unchanged inputs.

Save evidence under `video_game/planning/evidence/F03/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="f04"></a>

## F04 — Extract scenes and centralize cached assets

Dependencies — F03. Resource flag — STANDARD.

Files to create or modify

- `video_game/engine/state_machine.py`
- `video_game/engine/scenes/base.py`
- `video_game/engine/scenes/title.py`
- `video_game/engine/scenes/bunker.py`
- `video_game/engine/scenes/terminal.py`
- `video_game/engine/assets.py`
- `video_game/engine/ui/hud.py`
- `video_game/main.py`
- `video_game/tests/test_engine_boot.py`

Implementation sequence

1. Extract title, bunker, terminal and base scene classes one at a time while preserving current navigation.
2. Introduce a manifest-aware asset cache and replace PNG loads inside render methods.
3. Add scene exit lifecycle and deferred transitions. Keep temporary compatibility exports for existing tests while migrating callers.
4. Convert dt_ms to dt_seconds consistently at one main-loop boundary, including CRT timing adapters.
5. Preserve current placeholder scenes until their implementation tasks. Add controlled error handling for required missing assets.

Acceptance checks

- [x] All six scene identifiers still render and navigate.
- [x] Repeated terminal/inspector rendering performs no additional disk loads after caching.
- [x] Ten enter/exit cycles keep state and resources consistent.
- [x] Timing-sensitive behavior matches the pre-extraction baseline at 30/60/120 render FPS.

Save evidence under `video_game/planning/evidence/F04/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="f05"></a>

## F05 — Create authoritative campaign state

Dependencies — F04. Resource flag — STANDARD.

Files to create or modify

- `video_game/engine/campaign.py`
- `video_game/engine/config.py`
- `video_game/data/campaign.json`
- `video_game/tests/test_campaign.py`

Implementation sequence

1. Implement CampaignState fields and validation from DATA_CONTRACTS.md.
2. Move campaign mutations behind apply_event with prerequisites and unique event IDs.
3. Define new-game starter equipment and remove pregranted fragments from new-game defaults. Keep explicit seeded fixtures for development.
4. Represent act, room, checkpoint and meter identifiers consistently.
5. Wire the state owner into scenes and HUD with backward-compatible reads during migration.

Acceptance checks

- [x] Fresh state has the starter maser and no earned fragment/validation.
- [x] Repeated events grant rewards once and meters stay within 0–100.
- [x] Invalid IDs and unmet prerequisites leave the prior state intact.
- [x] Existing scene boot behavior still passes.

Save evidence under `video_game/planning/evidence/F05/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="f06"></a>

## F06 — Implement saves and recovery

Dependencies — F05. Resource flag — STANDARD.

Files to create or modify

- `video_game/engine/save_game.py`
- `video_game/engine/scenes/title.py`
- `video_game/tests/test_save_game.py`

Implementation sequence

1. Implement configurable platform user-data paths with a test override.
2. Serialize versioned campaign/checkpoint data and validate before atomic replacement.
3. Retain a valid previous backup and implement supported-version migrations.
4. Add New Game and Continue behavior, missing/corrupt-save feedback and explicit retry/recovery routes.
5. Connect saves to safe scene/objective boundaries. Keep active network requests out of persisted state.

Acceptance checks

- [x] Save/reload round trips preserve earned progression.
- [x] Simulated partial write or failed replace keeps the prior save usable.
- [x] Missing, corrupt, old and future-version saves return clear outcomes.
- [x] Restarting the process restores a valid checkpoint.

Save evidence under `video_game/planning/evidence/F06/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="f07"></a>

## F07 — Define focused input, pause and settings

Dependencies — F06. Resource flag — STANDARD.

Files to create or modify

- `video_game/engine/input.py`
- `video_game/engine/settings.py`
- `video_game/engine/ui/pause.py`
- `video_game/main.py`
- `video_game/tests/test_engine_boot.py`

Implementation sequence

1. Map physical keys to actions with pressed, held and released semantics.
2. Route input to the focused scene or overlay. Reserve text input for terminal typing.
3. Implement pause/resume, volume/effects settings and integer window scaling with persistence.
4. Move outfit/civilization/act inspection shortcuts behind explicit development mode where they bypass campaign state.
5. Ensure focus loss, window resize and quit release inputs and resources.

Acceptance checks

- [x] Pause freezes game time and resumes without stuck movement.
- [x] Settings survive restart and invalid values fall back safely.
- [x] Terminal typing does not move/fire the player.
- [x] Normal and development launches expose the intended controls.

Save evidence under `video_game/planning/evidence/F07/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="f08"></a>

## F08 — Migrate assets and tools into the target structure

Dependencies — F07. Resource flag — THINKING.

Files to create or modify

- `video_game/tools/`
- `video_game/art/source/`
- `video_game/assets/manifest.json`
- `video_game/assets/sprites/mateo/manifest.json`
- `video_game/engine/imports.py`
- `pyproject.toml`
- `video_game/_trash/TRASH_LOG.md`

Implementation sequence

1. Inventory runtime resources, source masters, generated previews and archived references. Record every old-to-new path before moving.
2. Move four builders and the preview tool into tools, concepts into art/source, and review sheets into planning evidence. Group sprite sheets by outfit and animation.
3. Update manifests, tests, rebuild mappings and dynamic filename consumers in the same change.
4. Use explicit imports and retire imports.py only after callers migrate. Declare a minimal optional game dependency set and package discovery that includes both packages.
5. Reconcile the inaccurate concepts archive entry and add provenance/hash metadata. Create no unused directories.
6. Run rebuilt resources and the normal game, then archive redundant aliases only after the migration checks pass.

Acceptance checks

- [x] Runtime loads every referenced asset and all source masters remain rebuildable.
- [x] Install metadata recognizes the game package without imposing graphical dependencies on CLI-only use.
- [x] Both suites pass and the native preview matches the prior scene.
- [x] Gate G0 passes with migration/restoration records.

Save evidence under `video_game/planning/evidence/F08/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.
