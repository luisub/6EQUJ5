# Repository audit — 2026-11-15

The cleanup consolidates duplicated science validation logic, retires superseded
robot generators and makes the status documents describe the current game.
The preceding player-focused README changes are retained.

- [Verification summary](verification.json)
- [Active directory map](repository-tree.txt)
- [Restoration index](archive-manifest.json)
- [Asset ownership](../ASSETS.md)

## Implementation

Four science workbenches now inherit shared catalog loading, claim classification,
evidence verification, replication and completion lookup from
`src/engine/labs/validation.py`. Each discipline keeps its simulation, experiment
unlocks, reset behavior, deployment and feedback. Existing public workbench,
loader and workflow-step imports remain available.

The unused `enemy_sprite_builder.py` and `generate_faction_sprites.py` were
archived after checking imports, tools, tests, art recipes and packaging. They
write historical robot designs over current enemy paths. `build_cyber_insects`
is the maintained replacement and reproduces all accepted exports exactly.

| Area | Result |
|---|---|
| Lab implementation | 2,486 → 2,117 lines across the four labs and shared module; 369 duplicated lines removed |
| Obsolete builders | Two files / 764 lines retired with verified restoration copies |
| Current status | Repeated chronology moved out of the active summary; roadmap rows and gates preserved |
| Directory map | Grouped runtime resources and sources; ignored historical evidence excluded |
| Preservation | 587 runtime/source/gallery media and metadata files unchanged; seven archive records verified |

The archive preserves original bytes and restoration instructions; moving files
there reduces the maintained tree, not disk use. Existing player saves, source
masters and recovery archives were not cleanup targets. The Git index is unchanged.

## Verification

**1,407 tests passed; one existing timing check failed.** FIELD_OPS render P95
was **5.466 ms** against the unchanged **5.0 ms** limit. The isolated check also
failed at **5.909 ms**. The cleanup does not resolve or waive that performance
issue. All **139 focused checks** passed, including eight added loader-failure
and scenario-specific completion cases.

Before/after comparison matched **221 operations across eight lab scenarios**,
including success/error feedback, state transitions, retries and completed-record
lookup. Scientific simulation classes are structurally unchanged.

All **52 levels** and **14 protected asset groups** validate. The retained insect
builder reproduces **37 exports byte-for-byte**. A clean direct wheel and a wheel
rebuilt from the source distribution contain **447 identical runtime files**.
Both boot outside the checkout and exercise the four lab interfaces using only
installed package resources; tools, tests and masters are excluded from wheels.

Detailed results and logs are linked from [verification.json](verification.json).
Checks use temporary saves/settings and dummy SDL. They do not establish human
playability, audible quality, physical-controller compatibility or native-display
performance. Formal acceptance gates remain open.

## Historical evidence

The previous audit, directory map, verification, current state and roadmap are
preserved under `_trash/2026-11-15_repository_cleanup/before/`. Earlier asset
layout, repository separation and visual audits remain in their dated archives.
The [restoration index](archive-manifest.json) records paths, hashes and recovery
steps. The current [progress log](../planning/PROGRESS_LOG.md) retains the work
history; historical counts are not current inventory claims.
