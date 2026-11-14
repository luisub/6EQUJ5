# Science, factions and reality mechanics

Use EXECUTION_PROTOCOL.md for the session workflow and QUALITY_GATES.md for shared acceptance. Paths are relative to the repository root. The authoritative status table is TODO_ROADMAP.md. Create only files used by the selected task.

This milestone ends at gate G3.

<a id="s01"></a>

## S01 — Build the quantum workbench

Dependencies — A14. Resource flag — THINKING.

Files to create or modify

- `video_game/engine/labs/quantum.py`
- `video_game/data/lab_scenarios.json`
- `video_game/tests/test_labs.py`

Implementation sequence

1. Inspect primary sources for the limited interference/coherence model used and record references.
2. Implement bounded wavelength, slit and environment controls with numerical validation.
3. Author observation, replication and confidence questions tied to signal sensing.
4. Return the common validation record and readable explanations.
5. Exercise parameter extremes and repeatability with fixed seeds.

Acceptance checks

- [x] Controls produce the documented model behavior and remain numerically stable.
- [x] Established observations and speculative rewards have correct claim labels.
- [x] A valid experiment unlocks only its intended evidence.

Save evidence under `video_game/planning/evidence/S01/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails. Status: done. [S01 Evidence Report](../../../_trash/2026-11-13_separation/historical-reviews/docs/planning/evidence/S01/report.md).

<a id="s02"></a>

## S02 — Build the connectome workbench

Dependencies — A14. Resource flag — THINKING.

Files to create or modify

- `video_game/engine/labs/neuro.py`
- `video_game/data/lab_scenarios.json`
- `video_game/tests/test_labs.py`

Implementation sequence

1. Define small authored sensory/intermediate/motor graphs with uncertainty and candidate edges.
2. Implement node/edge interaction and causal intervention trials.
3. Score evidence and replication against scenario data.
4. Provide feedback distinguishing observed connectivity from inferred function.
5. Return versioned validation records and persist completed work.

Acceptance checks

- [x] Puzzle solutions are reachable through supported input.
- [x] Wrong but plausible graphs receive understandable feedback.
- [x] Repeated trials are reproducible and cannot double-grant rewards.

Save evidence under `video_game/planning/evidence/S02/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails. Status: done. [S02 Evidence Report](../../../_trash/2026-11-13_separation/historical-reviews/docs/planning/evidence/S02/report.md).

<a id="s03"></a>

## S03 — Build the biosecurity workbench

Dependencies — A14. Resource flag — THINKING.

Files to create or modify

- `video_game/engine/labs/biosecurity.py`
- `video_game/data/lab_scenarios.json`
- `video_game/tests/test_labs.py`

Implementation sequence

1. Design an abstract resource/time/confidence scenario with fictional hazards.
2. Implement allocation controls, noisy observations and replication checks.
3. Expose uncertainty and resource tradeoffs in the interface.
4. Return validation and deployment decisions using the common schema.
5. Inspect primary sources for educational claims and record the simplifications.

Acceptance checks

- [x] Scenario bounds prevent negative resources and invalid confidence values.
- [x] Seeded cases cover success, premature deployment and recovery.
- [x] User feedback explains the evidence behind outcomes.

Save evidence under `video_game/planning/evidence/S03/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails. Status: done. [S03 Evidence Report](../../../_trash/2026-11-13_separation/historical-reviews/docs/planning/evidence/S03/report.md).

<a id="s04"></a>

## S04 — Integrate all science arcs and campaign meters

Dependencies — S01, S02, S03, C07. Resource flag — THINKING.

Files to create or modify

- `video_game/engine/scenes/lab.py`
- `video_game/engine/protocols.py`
- `video_game/data/lab_scenarios.json`
- `video_game/tests/test_labs.py`

Implementation sequence

1. Create beginner and advanced scenarios for each of the four workbenches.
2. Connect decode, experiment, replication, deployment and delayed-consequence records.
3. Author bounded meter changes and visible consequence messages.
4. Audit every educational claim tier and supporting primary reference.
5. Verify incomplete trials, repeat deployment and save migrations.

Acceptance checks

- [x] Each workbench contributes at least one required campaign validation.
- [x] Six meters update according to recorded events once.
- [x] Speculative narrative mechanics and scientific claims are clearly presented.
- [x] All scenarios pass automated and interactive checks.

Save evidence under `video_game/planning/evidence/S04/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="s05"></a>

## S05 — Expand the analog arsenal and ability framework

Dependencies — A14, C06. Resource flag — THINKING.

Files to create or modify

- `video_game/engine/abilities.py`
- `video_game/engine/weapons.py`
- `video_game/data/balance.json`
- `video_game/tests/test_combat.py`

Implementation sequence

1. Implement scattergun reveal, EMP bola stun and Fibonacci coilgun timing through shared damage/projectile rules.
2. Add a small ability interface with unlock ID, cooldown, cost, activate and reset behavior.
3. Implement decoy, shielding and time-dilation prototypes using explicit actor-time modifiers.
4. Wire unlocks through validated protocol events and HUD selection.
5. Author counterplay and interaction tests for simultaneous statuses.

Acceptance checks

- [x] Locked equipment cannot activate.
- [x] Costs/cooldowns persist or reset according to checkpoint rules.
- [x] Fibonacci timing and multi-hit behavior are deterministic.
- [x] All weapon effects remain bounded and readable.

Save evidence under `video_game/planning/evidence/S05/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="s06"></a>

## S06 — Implement safe Mandela geometry swaps

Dependencies — S04, S05. Resource flag — THINKING.

Files to create or modify

- `video_game/engine/mandela_world.py`
- `video_game/engine/world.py`
- `video_game/tests/test_timelines.py`

Implementation sequence

1. Add aligned 2029/1977 collision layers and timeline-aware object IDs.
2. Implement transactional swap validation against player/actor footprints.
3. Define safe displacement or explicit rejected-swap feedback.
4. Persist pickups, doors and objectives across repeated swaps.
5. Author a small room with blocked, safe, moving-platform and checkpoint cases.

Acceptance checks

- [x] Player and required objects never become embedded in solid geometry.
- [x] Repeated swaps cannot duplicate pickups or reset rewards.
- [x] Save/reload preserves both timeline choice and persistent objects.
- [x] Camera, lighting and collision change coherently.

Save evidence under `video_game/planning/evidence/S06/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="s07"></a>

## S07 — Implement the Dodleston relay

Dependencies — S06. Resource flag — THINKING.

Files to create or modify

- `video_game/engine/temporal_relay.py`
- `video_game/data/levels/act_04/dodleston_relay.json`
- `video_game/tests/test_timelines.py`

Implementation sequence

1. Define authored historical actions and deterministic present-day consequences.
2. Add terminal choices/messages with visible era labels and prerequisites.
3. Apply historical edits as unique campaign events and rebuild affected room objects safely.
4. Provide recovery from a wrong choice and prevent causal dependency deadlocks.
5. Test reload, replay, cancellation and repeated cross-time messages.

Acceptance checks

- [x] Every required relay puzzle has a reachable solution and recovery route.
- [x] Historical edits persist once and never trap the player.
- [x] 1985, 2029 and 2031 messages remain coherent.

Save evidence under `video_game/planning/evidence/S07/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="s08"></a>

## S08 — Build the playable 1977 flashback

Dependencies — S06. Resource flag — GPU_IMAGE.

Files to create or modify

- `video_game/data/levels/flashback/ehman_1977.json`
- `video_game/engine/scenes/field.py`
- `video_game/data/campaign.json`

Implementation sequence

1. Author the laboratory, printout inspection, red annotation and hidden-reel sequence.
2. Use an explicit flashback player presentation and interaction set.
3. Connect entry/return to campaign state and the reality-anchor reward.
4. Create period-specific art, text and sound.
5. Test interruption, checkpoint reload and repeated visits.

Acceptance checks

- [x] Flashback completes through normal input and returns to the correct present-day room.
- [x] Anchor is granted once.
- [x] Present-day equipment and health follow explicit return rules.

Save evidence under `video_game/planning/evidence/S08/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="s09"></a>

## S09 — Complete faction behaviors and visual identities

Dependencies — A14, S05. Resource flag — GPU_IMAGE.

Files to create or modify

- `video_game/engine/enemies.py`
- `video_game/assets/sprites/enemies/`
- `video_game/data/balance.json`
- `video_game/tests/test_combat.py`

Implementation sequence

1. Add Core enforcer/operative variants, shield/charge Hounds, Watchers, Chrysalis Splicers, precursor guardians and Temporal Phantoms.
2. Give each distinct movement, telegraphs, attack/counter and recovery rules.
3. Integrate reveal, stun, coherence drain, teleport and timeline visibility effects.
4. Author motion and effects per ART_PRODUCTION.md.
5. Test mixed-faction encounters with bounded counts and safe spawn locations.

Acceptance checks

- [ ] Each faction teaches a distinct readable counter.
- [ ] Invisible/teleporting attacks remain signaled and avoid solid geometry.
- [ ] Reset and simultaneous status effects remain consistent.
- [ ] All required faction assets meet review thresholds.

Save evidence under `video_game/planning/evidence/S09/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="s10"></a>

## S10 — Complete advanced traversal and prediction counterplay

Dependencies — S06. Resource flag — THINKING.

Files to create or modify

- `video_game/engine/player.py`
- `video_game/engine/abilities.py`
- `video_game/engine/world.py`
- `video_game/tests/test_player.py`

Implementation sequence

1. Implement wall jump, magnetic grapple anchors and Fibonacci dash from authored room data.
2. Add the Serendipity tape-deck action and explicit prediction-lock disruption.
3. Define costs, cooldowns, collision and ability combinations.
4. Author small teaching encounters for each mechanic.
5. Test grapple release, fast movement into corners, paused dash and timeline changes mid-action.

Acceptance checks

- [x] Advanced movement cannot leave the valid room or tunnel through walls.
- [x] Prediction disruption has visible feedback and a bounded combat benefit.
- [x] Every required traversal route is possible with equipment available on arrival.

Save evidence under `video_game/planning/evidence/S10/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="s11"></a>

## S11 — Verify the complete mechanics set

Dependencies — S04, S07, S08, S09, S10. Resource flag — THINKING.

Files to create or modify

- `video_game/planning/evidence/S11/`
- `video_game/tests/test_timelines.py`
- `video_game/tests/test_content.py`

Implementation sequence

1. Run a combined route using all workbenches, timeline swaps, relay, flashback and advanced equipment.
2. Test action combinations and checkpoint persistence.
3. Record art, controls, failure recovery and claim-tier review.
4. Fix contradictions between task behavior and data contracts.

Acceptance checks

- [ ] Gate G3 passes with gameplay evidence.
- [ ] All required mechanics have normal entry points and controlled failure behavior.
- [ ] Unresolved defects have concrete task ownership.

Save evidence under `video_game/planning/evidence/S11/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.
