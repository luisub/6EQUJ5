# Repository separation update

Standalone offline packaging and the flat src layout are installed at the final game path; the legacy AI application is installed separately. Both environments were recreated and validated. See [completed transfer](../migration/TRANSFER_COMPLETE.md), [current state](CURRENT_STATE.md) and [migration report](../migration/REPORT.md). Historical evidence paths in the retained roadmap below refer to archived pre-separation material; resolve them through the archive manifest. Gameplay task statuses and gate acceptance are unchanged.

# Execution roadmap

User-requested increment: **intro map + temporary weapons + denser targets + action lighting — implemented** (root). Functional checks and packaged smoke completed; missing legacy art and renderer-budget review remain open. Extends A05/A12/S05 and opening presentation; formal gates remain unchanged. [Evidence](evidence/COMBAT/2026-11-13_intro_powerups/report.md).


The roadmap is the single task-status owner. User-directed serial J02 production and armed-air-pose work continue without promoting gates. Formal dependencies and acceptance requirements remain in the linked task cards. The full earlier roadmap is preserved in the [SHA-verified snapshot](evidence/WORLD_ART/2026-11-13_sequential_continuation/docs_before_final_v01/video_game/planning/TODO_ROADMAP.md).

**Counts:** 72 tasks, 36 done, 23 in progress, 13 planned. J01–J06 remain in progress. Current user increment: 1,212 passed / 2 failed / 2 live excluded; see the report above. Previous combined v03: **1,200 passed, 1 failed, 2 live excluded in 178.01 s**; the historical missing portrait source remains open. The dummy-render guard passed this run, while native FPS remains unmeasured. The clean wheel passed bounded installed checks: 635 members and 630 source/data/asset files matched in both directions, including all 52 levels; SHA-256 `dfac6f5efe9e819347110b20e9a5a25b84fe2d83dc3cf79eae21f4e8ec0beb41`. Installed opening/skip/Continue, FASR-001/003 native art, hazard action cues, earned-save Continue and offline CLI checks passed under dummy SDL with disclosed fixtures. [Wheel report](evidence/WORLD_ART/2026-11-13_sequential_continuation/technical_v01/wheel_check_v02/report.md). The earlier v01 wheel smoke failed due to a scale-specific click in the harness; v02 corrected viewport mapping only. [Current state](CURRENT_STATE.md) · [Opening report](evidence/OPENING_STORY/2026-11-13_basement_intro/report.md).

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
| P01a | Block out Act II Neo-Denver | S11 | in_progress | THINKING | [Task card](milestones/04_campaign.md#p01a) |
| P01b | Produce and integrate Act II Neo-Denver art | P01a | in_progress | GPU_IMAGE | [Task card](milestones/04_campaign.md#p01b) |
| P01c | Complete Act II Neo-Denver boss and local playthrough | P01b | in_progress | THINKING | [Task card](milestones/04_campaign.md#p01c) |
| P02a | Block out Act III Area 51 | P01c | in_progress | THINKING | [Task card](milestones/04_campaign.md#p02a) |
| P02b | Produce and integrate Act III Area 51 art | P02a | in_progress | GPU_IMAGE | [Task card](milestones/04_campaign.md#p02b) |
| P02c | Complete Act III Area 51 boss and local playthrough | P02b | in_progress | THINKING | [Task card](milestones/04_campaign.md#p02c) |
| P03a | Block out Act IV VLA/Dodleston | P02c | in_progress | THINKING | [Task card](milestones/04_campaign.md#p03a) |
| P03b | Produce and integrate Act IV VLA/Dodleston art | P03a | in_progress | GPU_IMAGE | [Task card](milestones/04_campaign.md#p03b) |
| P03c | Complete Act IV VLA/Dodleston boss and local playthrough | P03b | in_progress | THINKING | [Task card](milestones/04_campaign.md#p03c) |
| P04a | Block out Act V Göbekli Tepe | P03c | in_progress | THINKING | [Task card](milestones/04_campaign.md#p04a) |
| P04b | Produce and integrate Act V Göbekli Tepe art | P04a | in_progress | GPU_IMAGE | [Task card](milestones/04_campaign.md#p04b) |
| P04c | Complete Act V Göbekli Tepe boss and local playthrough | P04b | in_progress | THINKING | [Task card](milestones/04_campaign.md#p04c) |
| P05 | Validate the complete campaign graph | P04c, J03 | planned | STANDARD | [Task card](milestones/04_campaign.md#p05) |
| P06 | Complete all civilization arcs and portrait animation | P05 | planned | GPU_IMAGE + GPU_LLM | [Task card](milestones/04_campaign.md#p06) |
| P07 | Complete every civilization reward | P06 | planned | THINKING | [Task card](milestones/04_campaign.md#p07) |
| P08 | Implement endings and finale consequences | P07 | planned | STANDARD | [Task card](milestones/04_campaign.md#p08) |
| P09 | Accept the full campaign | P08, J04 | planned | THINKING | [Task card](milestones/04_campaign.md#p09) |
| J01 | Author eleven profile-bound worlds and journey data | User-directed scope | in_progress | THINKING | [Task card](milestones/06_alien_journey.md#j01) |
| J02 | Produce alien world and guardian art sequentially | J01 | in_progress | GPU_IMAGE | [Task card](milestones/06_alien_journey.md#j02) |
| J03 | Connect guardians, conversations, receipts and Earth finale | J01 | in_progress | THINKING | [Task card](milestones/06_alien_journey.md#j03) |
| J04 | Verify complete journey, recovery and final gate | J02, J03 | in_progress | THINKING | [Task card](milestones/06_alien_journey.md#j04) |
| J05 | Show and preserve inter-world galaxy transit | J03 | in_progress | STANDARD | [Task card](milestones/06_alien_journey.md#j05) |
| J06 | Build distinct planet threats and moving hazards | J01, J03 | in_progress | THINKING | [Task card](milestones/06_alien_journey.md#j06) |
| R01 | Finish readability and accessibility | P09 | planned | STANDARD | [Task card](milestones/05_release.md#r01) |
| R02 | Add controller support and complete input QA | R01 | planned | PLATFORM | [Task card](milestones/05_release.md#r02) |
| R03 | Complete visual effects and final art polish | R02 | planned | GPU_IMAGE + THINKING | [Task card](milestones/05_release.md#r03) |
| R04 | Profile and optimize the complete game | R03 | planned | CPU_PROFILE | [Task card](milestones/05_release.md#r04) |
| R05 | Run resilience and progression regression matrix | R04 | planned | GPU_LLM + THINKING | [Task card](milestones/05_release.md#r05) |
| R06 | Package a clean install and author player documentation | R05 | planned | PLATFORM | [Task card](milestones/05_release.md#r06) |
| R07 | Verify the packaged build on claimed platforms | R06 | planned | PLATFORM | [Task card](milestones/05_release.md#r07) |
| R08 | Accept the release and consolidate the workspace | R07 | planned | THINKING | [Task card](milestones/05_release.md#r08) |



## Continuation and dependencies

Develop the armed ascent/fall poses with add-only clip validation, and continue FASR-005 realm/guardian work in serial reviewed components. J06 remains open for human fairness and motion assessment. A12 still needs audio acceptance, A13 real-display performance and A14 a human fresh-save route; S09/S11 and the linked P/R acceptance dependencies remain open. Work authorized in parallel does not change those requirements.

## Milestone exits

| Gate | Completion condition | Status |
|---|---|---|
| G0 | F01–F08 foundation checks | done |
| G1 | C01–C08 art/contact/validation loop | done |
| G2 | A01–A14 complete Act I | pending |
| G3 | S01–S11 full mechanics | pending |
| G4 | P01a–P09 five acts and endings | pending |
| G5 | R01–R08 verified release | pending |

Every future done status requires supporting evidence in the progress log. See the linked task cards and [quality gates](QUALITY_GATES.md) for acceptance details.
