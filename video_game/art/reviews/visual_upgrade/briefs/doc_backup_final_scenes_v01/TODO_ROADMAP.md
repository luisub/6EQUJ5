# Execution roadmap

This table is the single task-status record. Updated 2026-11-11. The previous phase checklist is archived with the original planning documents.

Total tasks — 66. Functional audit through Milestone 3 fixed runtime/input/save/package gaps; see [current audit](evidence/AUDIT/2026-11-11_through_G3/report.md). G0/G1 retain prior acceptance; live AI is optional and skipped by user direction. G2/G3 are pending the remaining normal-playthrough, visual/audio and graphical-performance acceptance. Implemented work is retained; P01a is planned until S11 acceptance.

The 2026-11-12 recovery verified installed native components for approach, salvage yard, dish catwalk and Greenkeeper arena, plus a clean combined headless checkpoint (493 passed, two named live tests deselected). The bunker backdrop is reviewed but not installed; annex has a brief only, and other prototype/character work remains pending. Current-revision wheel, human/native-window and graphical-performance acceptance remain open. G2/G3 and every task status below remain unchanged. See [current state](CURRENT_STATE.md).

The bounded UI readability increment now uses native-density text and scrollable dossier, relay and lab details; its earlier reported 463-test checkpoint has unconfirmed invocation and collection scope; the subsequent verified recovery checkpoint is recorded above. Existing G2/G3 and task statuses below are unchanged. The user-approved high-contrast direction is in staged, room-specific art production, not an accepted complete room. See [current state](CURRENT_STATE.md).

The bounded 960×540 render-density migration preserves the 480×270 logical world; existing scaled assets are not newly authored high-resolution art. An earlier Ohio background-only static composite was superseded by the user-requested high-contrast direction after two full-scene candidates failed geometry review; the single new standing pose is a static direction candidate pending native cleanup and animation review. The earlier [layered dressing plan](../art/reviews/visual_upgrade/briefs/ohio_layered_scene_dressing_v01.md) proposed a decorative bin; its subsequent bounded installation does not add collision or cover. This work does not change the task or gate statuses below. See [current state](CURRENT_STATE.md) and [visual upgrade working state](../art/reviews/visual_upgrade/CURRENT_ART_STATE.md).

Each task has ordered implementation actions, exact destination files, dependencies and acceptance checks in its milestone document. Complete one task per default session. Promote planned tasks to ready when their listed dependencies are done. Independent branches may proceed while an unrelated resource dependency is blocked.

| ID | Task | Dependencies | Status | Resource | Instructions |
|---|---|---|---|---|---|
| F01 | Record the current baseline | none | done | STANDARD | [Task card](milestones/00_foundation.md#f01) |
| F02 | Make checkpoint checks support readable development | F01 | done | STANDARD | [Task card](milestones/00_foundation.md#f02) |
| F03 | Make asset builds safe and recoverable | F02 | done | STANDARD | [Task card](milestones/00_foundation.md#f03) |
| F04 | Extract scenes and centralize cached assets | F03 | done | STANDARD | [Task card](milestones/00_foundation.md#f04) |
| F05 | Create authoritative campaign state | F04 | done | STANDARD | [Task card](milestones/00_foundation.md#f05) |
| F06 | Implement saves and recovery | F05 | done | STANDARD | [Task card](milestones/00_foundation.md#f06) |
| F07 | Define focused input, pause and settings | F06 | done | STANDARD | [Task card](milestones/00_foundation.md#f07) |
| F08 | Migrate assets and tools into the target structure | F07 | done | THINKING | [Task card](milestones/00_foundation.md#f08) |
| C01 | Review and refine the visual standard | F08 | done | GPU_IMAGE | [Task card](milestones/01_contact_loop.md#c01) |
| C02 | Normalize bunker layers and lighting | C01 | done | GPU_IMAGE | [Task card](milestones/01_contact_loop.md#c02) |
| C03 | Build the cancellable AI adapter and worker | F08 | done | GPU_LLM | [Task card](milestones/01_contact_loop.md#c03) |
| C04 | Implement receiver interaction and dialogue UI | C03 | done | STANDARD | [Task card](milestones/01_contact_loop.md#c04) |
| C05 | Author offline contact routes | C04 | done | STANDARD | [Task card](milestones/01_contact_loop.md#c05) |
| C06 | Implement fragment and hostile-signal rules | C05 | done | THINKING | [Task card](milestones/01_contact_loop.md#c06) |
| C07 | Make the first formal-validation workbench playable | C06 | done | STANDARD | [Task card](milestones/01_contact_loop.md#c07) |
| C08 | Verify the contact-to-validation loop | C02, C07 | done | GPU_LLM | [Task card](milestones/01_contact_loop.md#c08) |
| A01 | Load a playable room and camera | F08 | done | STANDARD | [Task card](milestones/02_action_slice.md#a01) |
| A02 | Implement stable player locomotion | A01 | done | STANDARD | [Task card](milestones/02_action_slice.md#a02) |
| A03 | Implement cover, crouch and slide-kick | A02 | done | STANDARD | [Task card](milestones/02_action_slice.md#a03) |
| A04 | Turn Mateo poses into reviewed animation clips | A03 | done | GPU_IMAGE | [Task card](milestones/02_action_slice.md#a04) |
| A05 | Implement the starter weapon and projectile loop | A04 | done | STANDARD | [Task card](milestones/02_action_slice.md#a05) |
| A06 | Build first enemies and predictive attacks | A05 | done | STANDARD | [Task card](milestones/02_action_slice.md#a06) |
| A07 | Connect bunker stations, inventory and HUD | A06 | done | STANDARD | [Task card](milestones/02_action_slice.md#a07) |
| A08 | Implement the 72-second dish defense | A07 | done | STANDARD | [Task card](milestones/02_action_slice.md#a08) |
| A09 | Implement Greenkeeper and the boss framework | A08 | done | THINKING | [Task card](milestones/02_action_slice.md#a09) |
| A10 | Assemble the Act I mission chain | A09 | done | STANDARD | [Task card](milestones/02_action_slice.md#a10) |
| A11 | Finish Ohio environment art | A10 | done | GPU_IMAGE | [Task card](milestones/02_action_slice.md#a11) |
| A12 | Add audio and bounded combat effects | A11 | in_progress | STANDARD | [Task card](milestones/02_action_slice.md#a12) |
| A13 | Measure and fix Act I performance | A12 | in_progress | CPU_PROFILE | [Task card](milestones/02_action_slice.md#a13) |
| A14 | Accept the complete Act I gameplay loop | A13, C08 | in_progress | THINKING | [Task card](milestones/02_action_slice.md#a14) |
| S01 | Build the quantum workbench | A14 | done | THINKING | [Task card](milestones/03_science_and_reality.md#s01) |
| S02 | Build the connectome workbench | A14 | done | THINKING | [Task card](milestones/03_science_and_reality.md#s02) |
| S03 | Build the biosecurity workbench | A14 | done | THINKING | [Task card](milestones/03_science_and_reality.md#s03) |
| S04 | Integrate all science arcs and campaign meters | S01, S02, S03, C07 | done | THINKING | [Task card](milestones/03_science_and_reality.md#s04) |
| S05 | Expand the analog arsenal and ability framework | A14, C06 | done | THINKING | [Task card](milestones/03_science_and_reality.md#s05) |
| S06 | Implement safe Mandela geometry swaps | S04, S05 | done | THINKING | [Task card](milestones/03_science_and_reality.md#s06) |
| S07 | Implement the Dodleston relay | S06 | done | THINKING | [Task card](milestones/03_science_and_reality.md#s07) |
| S08 | Build the playable 1977 flashback | S06 | done | GPU_IMAGE | [Task card](milestones/03_science_and_reality.md#s08) |
| S09 | Complete faction behaviors and visual identities | A14, S05 | in_progress | GPU_IMAGE | [Task card](milestones/03_science_and_reality.md#s09) |
| S10 | Complete advanced traversal and prediction counterplay | S06 | done | THINKING | [Task card](milestones/03_science_and_reality.md#s10) |
| S11 | Verify the complete mechanics set | S04, S07, S08, S09, S10 | in_progress | THINKING | [Task card](milestones/03_science_and_reality.md#s11) |
| P01a | Block out Act II Neo-Denver | S11 | planned | THINKING | [Task card](milestones/04_campaign.md#p01a) |
| P01b | Produce and integrate Act II Neo-Denver art | P01a | planned | GPU_IMAGE | [Task card](milestones/04_campaign.md#p01b) |
| P01c | Complete Act II Neo-Denver boss and local playthrough | P01b | planned | THINKING | [Task card](milestones/04_campaign.md#p01c) |
| P02a | Block out Act III Area 51 | P01c | planned | THINKING | [Task card](milestones/04_campaign.md#p02a) |
| P02b | Produce and integrate Act III Area 51 art | P02a | planned | GPU_IMAGE | [Task card](milestones/04_campaign.md#p02b) |
| P02c | Complete Act III Area 51 boss and local playthrough | P02b | planned | THINKING | [Task card](milestones/04_campaign.md#p02c) |
| P03a | Block out Act IV VLA/Dodleston | P02c | planned | THINKING | [Task card](milestones/04_campaign.md#p03a) |
| P03b | Produce and integrate Act IV VLA/Dodleston art | P03a | planned | GPU_IMAGE | [Task card](milestones/04_campaign.md#p03b) |
| P03c | Complete Act IV VLA/Dodleston boss and local playthrough | P03b | planned | THINKING | [Task card](milestones/04_campaign.md#p03c) |
| P04a | Block out Act V Göbekli Tepe | P03c | planned | THINKING | [Task card](milestones/04_campaign.md#p04a) |
| P04b | Produce and integrate Act V Göbekli Tepe art | P04a | planned | GPU_IMAGE | [Task card](milestones/04_campaign.md#p04b) |
| P04c | Complete Act V Göbekli Tepe boss and local playthrough | P04b | planned | THINKING | [Task card](milestones/04_campaign.md#p04c) |
| P05 | Validate the complete campaign graph | P04c | planned | STANDARD | [Task card](milestones/04_campaign.md#p05) |
| P06 | Complete all civilization arcs and portrait animation | P05 | planned | GPU_IMAGE + GPU_LLM | [Task card](milestones/04_campaign.md#p06) |
| P07 | Complete every civilization reward | P06 | planned | THINKING | [Task card](milestones/04_campaign.md#p07) |
| P08 | Implement endings and finale consequences | P07 | planned | STANDARD | [Task card](milestones/04_campaign.md#p08) |
| P09 | Accept the full campaign | P08 | planned | THINKING | [Task card](milestones/04_campaign.md#p09) |
| R01 | Finish readability and accessibility | P09 | planned | STANDARD | [Task card](milestones/05_release.md#r01) |
| R02 | Add controller support and complete input QA | R01 | planned | PLATFORM | [Task card](milestones/05_release.md#r02) |
| R03 | Complete visual effects and final art polish | R02 | planned | GPU_IMAGE + THINKING | [Task card](milestones/05_release.md#r03) |
| R04 | Profile and optimize the complete game | R03 | planned | CPU_PROFILE | [Task card](milestones/05_release.md#r04) |
| R05 | Run resilience and progression regression matrix | R04 | planned | GPU_LLM + THINKING | [Task card](milestones/05_release.md#r05) |
| R06 | Package a clean install and author player documentation | R05 | planned | PLATFORM | [Task card](milestones/05_release.md#r06) |
| R07 | Verify the packaged build on claimed platforms | R06 | planned | PLATFORM | [Task card](milestones/05_release.md#r07) |
| R08 | Accept the release and consolidate the workspace | R07 | planned | THINKING | [Task card](milestones/05_release.md#r08) |

## Dependency-correct continuation

- A12 has a bounded fade/load stall fix (I38) awaiting final integration and remains open for audible transition/volume acceptance; A13 requires a named-machine, real-display workload measurement after A12. Native display creation failed on this host, so no FPS result exists. Do not retry the same unavailable display as evidence. A14 still requires failure/retry, pause, exit/reentry and fresh-save human/real-window acceptance in addition to the earned scripted route.
- S09 still requires distinct readable counters, simultaneous statuses and mixed-encounter fairness, plus required faction art/motion review. The unsupported airborne-hound hazard case (I37) remains unverified for future level authoring. The current counter and recovery investigations are useful bounded work alongside these external reviews; their results alone do not close A14 or S09.
- S11 combines those prerequisites with normal-input mechanics, failure/recovery, claim-tier/source review and persistence evidence. The earned route demonstrates eight scenario records and several mechanics, but does not establish all counter effects, source verification, human readability or G3. P01a remains planned until S11 is accepted.
- After S11, the existing chain is P01a/b/c through P04a/b/c (four later acts with blockout, art and boss/playthrough), P05 graph reachability, P06 eleven civilization arcs, P07 all civilization rewards, P08 endings, and P09 full campaign acceptance. G4 precedes R01–R08 and G5; preserve the existing task identities and acceptance requirements. Independent work may proceed only where the documented dependencies and owned files permit it.

## Milestone exits

| Gate | Completion condition | Status |
|---|---|---|
| G0 | F01–F08 foundation checks | done |
| G1 | C01–C08 art/contact/validation loop | done |
| G2 | A01–A14 complete Act I | pending |
| G3 | S01–S11 full mechanics | pending |
| G4 | P01a–P09 five acts and endings | pending |
| G5 | R01–R08 verified release | pending |

F01 evidence is linked in CURRENT_STATE.md. Every future done status requires an evidence link in PROGRESS_LOG.md. A task returning to in_progress retains its prior evidence and gains a new attempt record.

## Earlier roadmap reconciliation

Earlier phases 0/1/1.5 provide the existing bootstrap and visual candidates. Their completed checkboxes are preserved in the archived roadmap. F01 records the narrower behavior actually verified. The former Phase 2 maps to C03–C08. Platformer/enemy/holdout work maps to A01–A14 and S09/S10. Timeline work maps to S06–S08. Labs map to C07 and S01–S04. Campaign/audio/save/release work is distributed across F06, A12, P tasks and R tasks to exercise foundations earlier.
