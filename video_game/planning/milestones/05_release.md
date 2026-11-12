# Polish, packaging and release

Use EXECUTION_PROTOCOL.md for the session workflow and QUALITY_GATES.md for shared acceptance. Paths are relative to the repository root. The authoritative status table is TODO_ROADMAP.md. Create only files used by the selected task.

This milestone ends at gate G5.

<a id="r01"></a>

## R01 — Finish readability and accessibility

Dependencies — P09. Resource flag — STANDARD.

Files to create or modify

- `video_game/engine/ui/`
- `video_game/engine/settings.py`
- `video_game/assets/ui/`
- `video_game/planning/evidence/R01/`

Implementation sequence

1. Review every screen at native and enlarged display sizes.
2. Implement a larger readable dialogue view, remappable text controls and persistent effects/audio settings.
3. Add reduced-flash/shake options, captions for essential audio cues and redundant shape/text cues for color-only information.
4. Review long text, glyph fallback, focus order and paused overlays.
5. Test all key paths with visual effects and audio reduced.

Acceptance checks

- [ ] Essential UI text fits and remains readable.
- [ ] Every essential audio/color cue has an accessible equivalent.
- [ ] Settings persist and apply consistently across scenes.

Save evidence under `video_game/planning/evidence/R01/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="r02"></a>

## R02 — Add controller support and complete input QA

Dependencies — R01. Resource flag — PLATFORM.

Files to create or modify

- `video_game/engine/input.py`
- `video_game/engine/ui/pause.py`
- `video_game/engine/settings.py`
- `video_game/tests/test_player.py`

Implementation sequence

1. Map controller buttons/sticks to the existing action layer with configurable dead zones.
2. Implement menu navigation and keyboard handoff for free-text dialogue, with controller-accessible curated choices.
3. Handle disconnect/reconnect and switching active input devices.
4. Test aim, movement, cover, abilities and pause using actual hardware when available.
5. Record platform/device details and remaining hardware dependencies.

Acceptance checks

- [ ] All campaign actions have usable controller mappings.
- [ ] Disconnect cannot leave held movement/fire active.
- [ ] The campaign can finish through curated dialogue on controller.
- [ ] Actual controller checks are recorded before claiming support.

Save evidence under `video_game/planning/evidence/R02/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="r03"></a>

## R03 — Complete visual effects and final art polish

Dependencies — R02. Resource flag — GPU_IMAGE + THINKING.

Files to create or modify

- `video_game/engine/crt_renderer.py`
- `video_game/engine/effects.py`
- `video_game/assets/`
- `video_game/art/source/`
- `video_game/planning/evidence/R03/`

Implementation sequence

1. Audit all assets against the art rubric and remove remaining prototype visual defects.
2. Prototype normal/specular lighting on one representative player/room set and measure visual benefit and cost.
3. Integrate the chosen implementation and complete required maps for lit assets, with a lower-cost settings path.
4. Polish VHS curvature/chroma/glitch behavior and timeline transitions while keeping controls readable.
5. Record any proposed scope revision explicitly and leave affected acceptance open until resolved.

Acceptance checks

- [ ] All shipped assets meet their recorded review thresholds.
- [ ] Lighting/effects preserve pixel registration and combat readability.
- [ ] Required visual features and any accepted deferrals are explicit.
- [ ] Reduced-effects rendering remains functional.

Save evidence under `video_game/planning/evidence/R03/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="r04"></a>

## R04 — Profile and optimize the complete game

Dependencies — R03. Resource flag — CPU_PROFILE.

Files to create or modify

- `video_game/tools/profile_game.py`
- `video_game/engine/`
- `video_game/planning/evidence/R04/`

Implementation sequence

1. Benchmark representative worst-load scenes, the finale, room transitions and live dialogue.
2. Measure frame work, stalls, memory and asset cache behavior under the QUALITY_GATES protocol.
3. Fix measured hotspots with scoped changes and behavior regression checks.
4. Apply bounded enemy/projectile/effect budgets from data.
5. Document tested hardware and recommended settings.

Acceptance checks

- [ ] Full-game performance meets the recorded release budgets.
- [ ] No sustained resource growth occurs during repeated room/contact cycles.
- [ ] Results include reproducible commands, scenarios and machine details.

Save evidence under `video_game/planning/evidence/R04/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="r05"></a>

## R05 — Run resilience and progression regression matrix

Dependencies — R04. Resource flag — GPU_LLM + THINKING.

Files to create or modify

- `video_game/tests/`
- `video_game/planning/evidence/R05/`

Implementation sequence

1. Exercise fresh, old-version, corrupt and interrupted-save cases.
2. Test unavailable model, slow model, partial response, reconnect, queue saturation and quitting during inference.
3. Exercise repeated reward events, scene changes, final-boss death, timeline swap during movement and device loss.
4. Run both test suites and targeted normal-entry-point playthroughs.
5. Close high-severity failures and record actual fixes.

Acceptance checks

- [ ] All supported recovery routes work without lost progression.
- [ ] AI failures leave campaign data consistent.
- [ ] Both suites pass and every required matrix row has an observed result.

Save evidence under `video_game/planning/evidence/R05/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="r06"></a>

## R06 — Package a clean install and author player documentation

Dependencies — R05. Resource flag — PLATFORM.

Files to create or modify

- `pyproject.toml`
- `video_game/packaging/game.spec`
- `video_game/README.md`
- `video_game/CREDITS.md`
- `video_game/assets/manifest.json`

Implementation sequence

1. Finalize graphical entry point and optional game dependencies while preserving CLI-only installation.
2. Package runtime assets, font and content data through an explicit inclusion list.
3. Exclude source masters, archives, temporary files and planning evidence.
4. Document install, launch, controls, settings, saves, offline mode and optional Ollama setup.
5. Record licenses/provenance for shipped assets and dependencies. Produce an artifact with checksum and build log.

Acceptance checks

- [ ] Clean installation launches from a working directory outside the repository.
- [ ] All runtime resources resolve without source-tree assumptions.
- [ ] The CLI entry point still works.
- [ ] Packaged size/content and credits have been inspected.

Save evidence under `video_game/planning/evidence/R06/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="r07"></a>

## R07 — Verify the packaged build on claimed platforms

Dependencies — R06. Resource flag — PLATFORM.

Files to create or modify

- `video_game/planning/evidence/R07/`
- `video_game/README.md`

Implementation sequence

1. Install the packaged macOS artifact on a clean test location or account.
2. Exercise boot, input, sound, contact offline/online, save/reload, room transitions and finale fixtures.
3. Record OS, architecture, artifact checksum and actual results.
4. Test Windows/Linux only if they will be advertised as supported in this release, using native environments.
5. Fix packaging-specific failures and rebuild/retest affected artifacts.

Acceptance checks

- [ ] The exact distributable passes its platform smoke and gameplay route.
- [ ] Every advertised platform has actual evidence.
- [ ] Untested ports are clearly tracked as pending.

Save evidence under `video_game/planning/evidence/R07/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="r08"></a>

## R08 — Accept the release and consolidate the workspace

Dependencies — R07. Resource flag — THINKING.

Files to create or modify

- `video_game/planning/TODO_ROADMAP.md`
- `video_game/planning/CURRENT_STATE.md`
- `video_game/planning/PROGRESS_LOG.md`
- `video_game/_trash/TRASH_LOG.md`
- `video_game/README.md`

Implementation sequence

1. Run the final normal-entry-point campaign acceptance on the release artifact.
2. Review all feature coverage rows, quality gates, asset reviews and unresolved issues.
3. Inventory redundant exports and retired modules, then archive only verified obsolete items with recovery records.
4. Ensure package inclusion, rebuild sources, docs and final checksums agree.
5. Record release version, tested platforms, known limitations, restore procedure and future backlog. Mark completion only when every required gate passes.

Acceptance checks

- [ ] Gate G5 passes and all first-release requirements have evidence.
- [ ] No undocumented active duplicate implementation or broken reference remains.
- [ ] Archive recovery and rebuild sources are intact.
- [ ] Release notes describe the actual verified artifact.

Save evidence under `video_game/planning/evidence/R08/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.
