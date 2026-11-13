# Earth sectors, content and endings

Use EXECUTION_PROTOCOL.md for the session workflow and QUALITY_GATES.md for shared acceptance. Paths are relative to the repository root. The authoritative status table is TODO_ROADMAP.md. Create only files used by the selected task.

These five former acts are now connected Earth sectors. User-directed J01–J04 add the eleven-world journey and Earth return; G4 remains pending until the combined scope is accepted. Prior task IDs and formal dependencies are retained.

<a id="p01a"></a>

## P01a — Block out Act II Neo-Denver

Dependencies — S11. Resource flag — THINKING.

Files to create or modify

- `video_game/data/levels/act_02/`
- `video_game/data/campaign.json`
- `video_game/tests/test_content.py`

Implementation sequence

1. Create the four room files blackout_street, relay_rooftops, amplifier_station, array_12_arena following CONTENT_PLAN.md.
2. Place collision, cover, enemies, checkpoints, exits and objectives for amplifier retrieval, thermal visibility, EMP shielding and synchronized dish lanes.
3. Integrate FASR-003 and FASR-005 plus recoverable FASR-004 discovery.
4. Use existing art during blockout and prove the progression route before commissioning final assets.
5. Play the route with only the equipment available at this point in the campaign.

Acceptance checks

- [ ] All four rooms have reachable objectives and return/checkpoint paths.
- [ ] No future reward is required to obtain its own prerequisite.
- [ ] Death/reload and backtracking preserve progression.

Save evidence under `video_game/planning/evidence/P01a/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="p01b"></a>

## P01b — Produce and integrate Act II Neo-Denver art

Dependencies — P01a. Resource flag — GPU_IMAGE.

Files to create or modify

- `video_game/art/source/environments/neo_denver/`
- `video_game/assets/environments/neo_denver/`
- `video_game/data/levels/act_02/`

Implementation sequence

1. Create one representative finished camera composition and evaluate the art rubric.
2. Produce modular materials, props, background depth, lighting and required timeline variants for all four rooms.
3. Keep collision-critical edges and cover silhouettes readable.
4. Review every camera extent in motion with actors, effects and HUD.
5. Record provenance, source/output mappings and final per-room evidence.

Acceptance checks

- [ ] Every room meets the art rubric in both CRT modes.
- [ ] Parallax and repeated tiles have no distracting seams.
- [ ] Gameplay cues agree with collision and objectives.

Save evidence under `video_game/planning/evidence/P01b/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="p01c"></a>

## P01c — Complete Act II Neo-Denver boss and local playthrough

Dependencies — P01b. Resource flag — THINKING.

Files to create or modify

- `video_game/engine/bosses/synchronicity.py`
- `video_game/assets/sprites/bosses/synchronicity/`
- `video_game/data/balance.json`
- `video_game/tests/test_combat.py`

Implementation sequence

1. Implement synchronicity using the shared boss interface and CONTENT_PLAN encounter requirements.
2. Author boss animation, windups, phase transitions, safe counters and intro card.
3. Connect pre-boss checkpoint, defeat reward and next-act/finale transition.
4. Retry from every phase and test player/boss simultaneous defeat.
5. Run the entire act from its entry save and document fixes.

Acceptance checks

- [ ] Every phase is beatable with the available equipment.
- [ ] The boss resets without leaked attacks or duplicated rewards.
- [ ] A complete local act playthrough passes.
- [ ] Sector victory and checkpoint transitions are durable and retry safely.

Save evidence under `video_game/planning/evidence/P01c/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="p02a"></a>

## P02a — Block out Act III Area 51

Dependencies — P01c. Resource flag — THINKING.

Files to create or modify

- `video_game/data/levels/act_03/`
- `video_game/data/campaign.json`
- `video_game/tests/test_content.py`

Implementation sequence

1. Create the four room files salt_flats, s4_hangar, telepod_vault, amalgam_arena following CONTENT_PLAN.md.
2. Place collision, cover, enemies, checkpoints, exits and objectives for containment clues, Watcher reveal, Splicer teleports and precursor guardians.
3. Integrate FASR-008, FASR-009 and recoverable FASR-006 archival evidence.
4. Use existing art during blockout and prove the progression route before commissioning final assets.
5. Play the route with only the equipment available at this point in the campaign.

Acceptance checks

- [ ] All four rooms have reachable objectives and return/checkpoint paths.
- [ ] No future reward is required to obtain its own prerequisite.
- [ ] Death/reload and backtracking preserve progression.

Save evidence under `video_game/planning/evidence/P02a/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="p02b"></a>

## P02b — Produce and integrate Act III Area 51 art

Dependencies — P02a. Resource flag — GPU_IMAGE.

Files to create or modify

- `video_game/art/source/environments/area_51/`
- `video_game/assets/environments/area_51/`
- `video_game/data/levels/act_03/`

Implementation sequence

1. Create one representative finished camera composition and evaluate the art rubric.
2. Produce modular materials, props, background depth, lighting and required timeline variants for all four rooms.
3. Keep collision-critical edges and cover silhouettes readable.
4. Review every camera extent in motion with actors, effects and HUD.
5. Record provenance, source/output mappings and final per-room evidence.

Acceptance checks

- [ ] Every room meets the art rubric in both CRT modes.
- [ ] Parallax and repeated tiles have no distracting seams.
- [ ] Gameplay cues agree with collision and objectives.

Save evidence under `video_game/planning/evidence/P02b/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="p02c"></a>

## P02c — Complete Act III Area 51 boss and local playthrough

Dependencies — P02b. Resource flag — THINKING.

Files to create or modify

- `video_game/engine/bosses/amalgam.py`
- `video_game/assets/sprites/bosses/amalgam/`
- `video_game/data/balance.json`
- `video_game/tests/test_combat.py`

Implementation sequence

1. Implement amalgam using the shared boss interface and CONTENT_PLAN encounter requirements.
2. Author boss animation, windups, phase transitions, safe counters and intro card.
3. Connect pre-boss checkpoint, defeat reward and next-act/finale transition.
4. Retry from every phase and test player/boss simultaneous defeat.
5. Run the entire act from its entry save and document fixes.

Acceptance checks

- [ ] Every phase is beatable with the available equipment.
- [ ] The boss resets without leaked attacks or duplicated rewards.
- [ ] A complete local act playthrough passes.
- [ ] Sector victory and checkpoint transitions are durable and retry safely.

Save evidence under `video_game/planning/evidence/P02c/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="p03a"></a>

## P03a — Block out Act IV VLA/Dodleston

Dependencies — P02c. Resource flag — THINKING.

Files to create or modify

- `video_game/data/levels/act_04/`
- `video_game/data/campaign.json`
- `video_game/tests/test_content.py`

Implementation sequence

1. Create the four room files rail_yard, rift_array, dodleston_relay, architect_arena following CONTENT_PLAN.md.
2. Place collision, cover, enemies, checkpoints, exits and objectives for safe dual-timeline paths, historical relay consequences and gravity hazards.
3. Integrate FASR-002 and deterministic FASR-SCAN-H discovery.
4. Use existing art during blockout and prove the progression route before commissioning final assets.
5. Play the route with only the equipment available at this point in the campaign.

Acceptance checks

- [ ] All four rooms have reachable objectives and return/checkpoint paths.
- [ ] No future reward is required to obtain its own prerequisite.
- [ ] Death/reload and backtracking preserve progression.

Save evidence under `video_game/planning/evidence/P03a/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="p03b"></a>

## P03b — Produce and integrate Act IV VLA/Dodleston art

Dependencies — P03a. Resource flag — GPU_IMAGE.

Files to create or modify

- `video_game/art/source/environments/vla_rift/`
- `video_game/assets/environments/vla_rift/`
- `video_game/data/levels/act_04/`

Implementation sequence

1. Create one representative finished camera composition and evaluate the art rubric.
2. Produce modular materials, props, background depth, lighting and required timeline variants for all four rooms.
3. Keep collision-critical edges and cover silhouettes readable.
4. Review every camera extent in motion with actors, effects and HUD.
5. Record provenance, source/output mappings and final per-room evidence.

Acceptance checks

- [ ] Every room meets the art rubric in both CRT modes.
- [ ] Parallax and repeated tiles have no distracting seams.
- [ ] Gameplay cues agree with collision and objectives.

Save evidence under `video_game/planning/evidence/P03b/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="p03c"></a>

## P03c — Complete Act IV VLA/Dodleston boss and local playthrough

Dependencies — P03b. Resource flag — THINKING.

Files to create or modify

- `video_game/engine/bosses/mandela_architect.py`
- `video_game/assets/sprites/bosses/mandela_architect/`
- `video_game/data/balance.json`
- `video_game/tests/test_combat.py`

Implementation sequence

1. Implement mandela_architect using the shared boss interface and CONTENT_PLAN encounter requirements.
2. Author boss animation, windups, phase transitions, safe counters and intro card.
3. Connect pre-boss checkpoint, defeat reward and next-act/finale transition.
4. Retry from every phase and test player/boss simultaneous defeat.
5. Run the entire act from its entry save and document fixes.

Acceptance checks

- [ ] Every phase is beatable with the available equipment.
- [ ] The boss resets without leaked attacks or duplicated rewards.
- [ ] A complete local act playthrough passes.
- [ ] Sector victory and checkpoint transitions are durable and retry safely.

Save evidence under `video_game/planning/evidence/P03c/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="p04a"></a>

## P04a — Block out Act V Göbekli Tepe

Dependencies — P03c. Resource flag — THINKING.

Files to create or modify

- `video_game/data/levels/act_05/`
- `video_game/data/campaign.json`
- `video_game/tests/test_content.py`

Implementation sequence

1. Create the four room files pillar_approach, buried_archive, crust_waveguide, core_prime_arena following CONTENT_PLAN.md.
2. Place collision, cover, enemies, checkpoints, exits and objectives for the fictional portal approach and warden; preserve final deployment preparation for the post-journey Earth return.
3. Place a non-granting FASR-010 clue; its separate journey contact and receipt are owned by J01–J03.
4. Use existing art during blockout and prove the progression route before commissioning final assets.
5. Play the route with only the equipment available at this point in the campaign.

Acceptance checks

- [ ] All four rooms have reachable objectives and return/checkpoint paths.
- [ ] No future reward is required to obtain its own prerequisite.
- [ ] Death/reload and backtracking preserve progression.

Save evidence under `video_game/planning/evidence/P04a/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="p04b"></a>

## P04b — Produce and integrate Act V Göbekli Tepe art

Dependencies — P04a. Resource flag — GPU_IMAGE.

Files to create or modify

- `video_game/art/source/environments/gobekli_tepe/`
- `video_game/assets/environments/gobekli_tepe/`
- `video_game/data/levels/act_05/`

Implementation sequence

1. Create one representative finished camera composition and evaluate the art rubric.
2. Produce modular materials, props, background depth, lighting and required timeline variants for all four rooms.
3. Keep collision-critical edges and cover silhouettes readable.
4. Review every camera extent in motion with actors, effects and HUD.
5. Record provenance, source/output mappings and final per-room evidence.

Acceptance checks

- [ ] Every room meets the art rubric in both CRT modes.
- [ ] Parallax and repeated tiles have no distracting seams.
- [ ] Gameplay cues agree with collision and objectives.

Save evidence under `video_game/planning/evidence/P04b/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="p04c"></a>

## P04c — Complete Göbekli portal warden and local playthrough

Dependencies — P04b. Resource flag — THINKING.

Files to create or modify

- `video_game/engine/bosses/campaign_bosses.py`
- `video_game/data/campaign_route.json`
- `video_game/tests/test_campaign_world_route.py`

Implementation sequence

1. Complete the portal warden encounter and connect its durable defeat to the first alien world.
2. Keep the older `core_prime_defeated` flag compatible with prior saves without treating it as the new final Earth victory.
3. Exercise reveal, combat, retry, save failure, reentry and the portal transition through normal input.
4. Run the local Earth sector and inspect all remaining visual and fairness limits.

Acceptance checks

- [ ] Portal warden is beatable with currently available equipment, with a durable pre-boss checkpoint and no duplicate rewards.
- [ ] Victory reaches the first alien world and retry/reload cannot skip or lose progress.
- [ ] A complete local sector playthrough and required art/fairness review pass.

The separate two-stage Core Prime/Archon confrontation after all eleven receipts is owned by J03. Save evidence under `video_game/planning/evidence/P04c/`; keep the task in progress until all acceptance checks pass.

<a id="p05"></a>

## P05 — Validate the complete campaign graph

Dependencies — P04c, J03. Resource flag — STANDARD.

Files to create or modify

- `video_game/tools/validate_content.py`
- `video_game/data/campaign.json`
- `video_game/tests/test_content.py`

Implementation sequence

1. Validate all registered Earth, eleven alien field/guardian pairs, final Earth arena and flashback rooms, exits, spawn IDs and checkpoints.
2. Build fresh-campaign reachability through each guardian, acknowledged contact, ordered receipt and teleport; require all eleven receipts before final Earth entry and victory.
3. Audit optional discoveries and late recovery routes.
4. Check both timelines and saved-state entry variants.
5. Generate an inspectable room/mission route report.

Acceptance checks

- [ ] All required content is reachable and all mandatory prerequisite chains terminate.
- [ ] No exit points to missing content or a blocked spawn.
- [ ] Late recovery paths can complete the dossier without restarting.

Save evidence under `video_game/planning/evidence/P05/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="p06"></a>

## P06 — Complete all civilization arcs and portrait animation

Dependencies — P05. Resource flag — GPU_IMAGE + GPU_LLM.

Files to create or modify

- `video_game/data/civilization_missions.json`
- `video_game/data/dialogue_offline.json`
- `video_game/assets/civilizations/manifest.json`
- `video_game/tests/test_contact_session.py`

Implementation sequence

1. Complete unique readiness, evidence, validation, repeat-contact and hostile-signal variants for all eleven civilizations.
2. Connect each arc to its assigned act and scientific workbench.
3. Produce reviewed idle/receiving portrait animation with stable registration.
4. Audit free dialogue, curated choices, 12-exchange limits and fallback recovery.
5. Exercise each arc offline and sample live conversations that challenge lore and grant boundaries.

Acceptance checks

- [ ] All eleven mission/reward rows are covered and individually reachable.
- [ ] Portrait animation meets the art rubric.
- [ ] Neither model errors nor service loss can bypass or block required progression.

Save evidence under `video_game/planning/evidence/P06/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="p07"></a>

## P07 — Complete every civilization reward

Dependencies — P06. Resource flag — THINKING.

Files to create or modify

- `video_game/engine/abilities.py`
- `video_game/engine/weapons.py`
- `video_game/data/balance.json`
- `video_game/tests/test_combat.py`

Implementation sequence

1. Implement every remaining reward in CONTENT_PLAN.md, including plasma-arc variation, drones, ricochet, anchor, foresight, fatal-hit rewind, logogram projector and pillar resonance.
2. Specify costs, cooldowns, duration, reset and timeline interactions.
3. Connect ability activation, effects, sound and HUD feedback.
4. Test combinations and checkpoint reload, especially rewinds and persistent anchors.
5. Audit rewards against the actual civilization mission IDs.

Acceptance checks

- [ ] Every listed reward has a reachable unlock and usable action.
- [ ] Rewind restores a coherent actor/world snapshot without duplicating progression.
- [ ] Drones/effects remain bounded and clean up on exit.
- [ ] Late-game combinations keep boss patterns fair.

Save evidence under `video_game/planning/evidence/P07/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="p08"></a>

## P08 — Implement endings and finale consequences

Dependencies — P07. Resource flag — STANDARD.

Files to create or modify

- `video_game/engine/endings.py`
- `video_game/engine/scenes/ending.py`
- `video_game/data/endings.json`
- `video_game/tests/test_endings.py`

Implementation sequence

1. Implement the three priority-ordered ending rules from DATA_CONTRACTS.md.
2. Author finale choice UI, meter-specific epilogues, sound and credits transition.
3. Preserve a pre-finale save and define continue behavior after completion.
4. Create fixtures at each threshold and conflicting-condition boundary.
5. Play each ending through normal finale controls.

Acceptance checks

- [ ] Exactly one ending resolves for every valid final state.
- [ ] All three endings are reachable.
- [ ] Epilogue text matches actual decisions and saved state.
- [ ] Reloading a completed campaign has a clear supported behavior.

Save evidence under `video_game/planning/evidence/P08/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="p09"></a>

## P09 — Accept the full campaign

Dependencies — P08, J04. Resource flag — THINKING.

Files to create or modify

- `video_game/planning/evidence/P09/`
- `video_game/planning/ISSUES_AND_DECISIONS.md`

Implementation sequence

1. Play the full Earth chapter, all eleven alien visits and the final Earth encounter from a fresh save using offline dialogue.
2. Exercise live contact, alternative choices, all eleven rewards and each ending through targeted routes.
3. Inspect every workbench, boss, timeline transition and checkpoint.
4. Fix progression blockers, unfair encounters and critical readability issues.
5. Record full route evidence, completion duration and residual polish.

Acceptance checks

- [ ] Gate G4 passes.
- [ ] Every required content row has linked test/playthrough evidence.
- [ ] No known blocker or high-severity campaign defect remains.

Save evidence under `video_game/planning/evidence/P09/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.
