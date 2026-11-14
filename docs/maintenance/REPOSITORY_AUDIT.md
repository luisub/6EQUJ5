# Repository organization audit — 2026-11-14

The active checkout now separates runtime resources, rebuild sources, tests and
documentation. Confirmed obsolete material is recoverable in `_trash/`.
The game boots from independently installed packages, and the full suite has
the same two known failures as before cleanup, with no new failures.

- [Complete active directory tree](repository-tree.txt)
- [Exact source relocations and before/after hashes](source-moves.json)
- [Verification summary](verification.json)
- [Per-file archive and restoration index](../migration/archive-manifest.json)

## Findings and changes

| Area | Finding | Result |
|---|---|---|
| Runtime loading | Normal gameplay loads package assets/data, not temporary art folders. Manifest source paths were descriptive provenance. | Kept the flat `src` → `video_game` package and stable runtime identifiers; corrected provenance paths. |
| Temporary output | Completed verification runs included copied environments, package trees and repeated tests. | Moved `_temp/`, stale `build/`, `dist/`, generated package metadata and caches to the cleanup archive. |
| Art sources | Active masters were nested under `visual_upgrade/candidates`; source and review material were mixed. | Consolidated masters under descriptive source domains; retained briefs and research separately. |
| Duplicate art | 88 UUID-named generated images matched descriptive masters; the FASR-003 guardian source was duplicated. | Archived the duplicates after SHA-256 comparison. Also merged two unreferenced identical Göbekli source exports. |
| Runtime leftovers | Three old bunker captures and one duplicate tileset had no runtime, manifest or maintained-builder readers. | Archived all four; runtime inventory decreased from 568 to 564 files. |
| Rebuild dependencies | The historical portrait comparison builder read originals from `_trash`; a firing-flash recipe and tests used review paths. | Active inputs now resolve from `src/art/source/`. Missing historical portraits remain an explicit failure. |
| Test organization | Two deterministic timing fixtures lived among historical evidence. The geometry test retained an obsolete expansion name. | Moved fixtures into `src/tests/fixtures/scene_timing/`; renamed the module to `test_world_geometry.py`; simplified discovery/import paths. |
| Documentation | Several current instructions used earlier root layouts; historical links pointed to moved evidence. | Updated commands and links; consolidated the current-state handoff; retained prior narrative snapshots. |

There are **363 recorded source relocations**, including art, briefs, two timing
fixtures and one test-module rename. **15,007 files were moved to `_trash`**, and
three prior documentation snapshots were copied there before consolidation.
The 15,010 archive records total **2.46 GB (2.29 GiB)**. Moving preserves recovery
copies; it does not reclaim their disk space.

All **698 original image, audio and font files** under source/documentation
were found unchanged at their retained or archived locations. Every new archive
record passed SHA-256 verification. Existing recovery archives were preserved.

## Directory ownership

| Path | Contents |
|---|---|
| `src/main.py`, `src/engine/` | Entry point and game implementation |
| `src/assets/`, `src/data/` | Installed runtime exports and authored content |
| `src/art/source/environments/` | Ohio and other Earth scenery masters |
| `src/art/source/alien_worlds/` | All eleven world/guardian source families |
| `src/art/source/effects/`, `bosses/`, `mateo/`, `props/`, `planet_threats/` | Domain-specific art masters and export records |
| `src/art/source/civilizations/`, `bunker/` | Original dossier/bunker rebuild inputs |
| `src/art/briefs/`, `references/`, `palettes/` | Retained prompts, visual contracts, research and palettes |
| `src/tests/`, `src/tests/fixtures/` | Maintained tests and their input fixtures |
| `src/tools/` | Maintained builders, validators, captures and profiling tools |
| `docs/media/readme/` | Current README images, GIFs and capture notes |
| `docs/planning/` | Current roadmap, contracts and acceptance criteria |
| `docs/migration/`, `docs/maintenance/` | Historical transfer records and this organization audit |
| `_trash/2026-11-14_repository_cleanup/` | Retired material, pre-cleanup snapshots and verification records |
| `.venv/` | Existing local Python environment; retained |

The [full tree](repository-tree.txt) lists active files. Archive contents, Git
internals, local assistant state and environment internals are collapsed or omitted.
The complete pre-cleanup inventory and tree are preserved in the
[verification folder](../../_trash/2026-11-14_repository_cleanup/verification/).

## Test-file disposition

All **86 maintained test modules** still exercise active behavior, supported
builders or failure handling. None was removed simply because it is old or
failing. The archived temporary copies contain **688 test scripts**, including
tests inside copied dependency environments; those are not part of active test
discovery. The two timing fixtures are now ordinary versioned test inputs.

Runtime fallbacks, locked builder baselines, transaction-recovery code and
reproducible source exports remain where they have a demonstrated consumer.
For example, similarly named Ohio, energy-stream and Mateo files are not all
interchangeable duplicates. See the [asset guide](../ASSETS.md).

## Verification

| Check | Result |
|---|---|
| Before-cleanup full suite | 1,335 passed; 2 known failures |
| After-cleanup full suite | 1,335 passed; the same 2 failures |
| Focused relocation/boot/source checks | 48 passed |
| Authored level validation | All 52 passed |
| Asset-builder dry run | Passed; locked groups preserved |
| Alien-master export reproduction | All 18 exports match byte-for-byte |
| Ohio campus source validation | Both locked outputs validated |
| Firing-flash recipe | Identical RGBA pixels; current PNG encoding differs, so the accepted original bytes were retained |
| Runtime art provenance | All 161 source paths resolve |
| Clean direct wheel and wheel rebuilt from sdist | Each has 564 runtime files, matching current checkout hashes |
| Installed game smoke, each wheel | Main loop, fresh-start opening, all 11 native backgrounds and guardians passed with fallback disabled |
| Installed resource independence | Outside-checkout runs; zero Python file opens inside the checkout; tools, tests and masters absent from runtime packages |
| Syntax and metadata | 203 active Python files parsed; source/documentation JSON parsed |
| Preservation | All 15,010 archive hashes and all 698 original media files verified |
| Git | Index unchanged; no stage, commit, push, pull or history rewrite |

The missing historical FASR-001 portrait prevents rebuilding the old before/after
comparison sheet. Its expected input now lives under
`src/art/source/civilizations/legacy_ascii/`; that directory documents the
required originals. It is not needed to play the installed game.

The FIELD_OPS render P95 was **5.533 ms before** and **5.322 ms after**, against
the unchanged **5.0 ms** threshold. These measurements do not establish a
performance improvement; the existing timing check remains failing.

Checks used disposable saves/settings and dummy SDL. They do not establish
human campaign acceptance, audible quality, physical-controller compatibility
or native-display performance. Gameplay acceptance gates are unchanged.

## Recovery and future work

The [archive manifest](../migration/archive-manifest.json) records the original
path, archived path, SHA-256, reason and restoration instructions for each file.
Verify its hash and copy it back only when the target is free; preserve newer
work first. Restore paired image/manifests together. Canonical source moves are
recorded separately in [source-moves.json](source-moves.json).

Keep new runtime exports in `src/assets`, source masters in their art domain,
test inputs in `src/tests/fixtures`, and temporary checks in an explicitly chosen
scratch output directory. Generated verification environments and captures can
be archived after their useful results are recorded. Missing portrait originals,
native performance and the existing human/art acceptance work remain open.
