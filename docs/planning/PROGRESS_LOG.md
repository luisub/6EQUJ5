# Progress log

2026-11-13 — Repository separation. Current game retained from the full working tree, historical AI recovered separately, flat src layout introduced, and live-model runtime dependency removed. Detailed verification and preservation records are in [migration report](../../_trash/2026-11-14_repository_compaction/docs/migration/REPORT.md).

The complete earlier log is retained at `_trash/2026-11-13_separation/documentation-before-integration/docs/planning/PROGRESS_LOG.md`; no historical entries were discarded.

2026-11-14 — Repository organization audit. Consolidated 363 source/fixture paths;
archived 15,007 unnecessary files plus three prior documentation snapshots with
per-file hashes and restoration records. Retained all 86 useful test modules;
active code no longer uses candidate/review folders or the archive for portrait
rebuild inputs. All original media bytes are preserved. Full suite before and
after: 1,335 passed, the same two known failures. All 52 levels, asset dry run,
48 focused checks, 18 export reproductions, and both clean package installations
passed. Runtime packages contain 564 files and load all eleven native world/guardian
families outside the checkout. No acceptance gates were promoted. See the
[repository audit and tree](../maintenance/REPOSITORY_AUDIT.md).

2026-11-14 — Second organization audit. Archived 29 additional historical or
duplicate files and preserved four documentation snapshots. Removed the obsolete
`docs/migration` folder; its current restoration index now lives in
`docs/maintenance`. Retired seven one-off refinement scripts (6,336 lines), and
shared the title PNG between README and runtime. All runtime/test files remain
byte-identical; 63 focused checks, complete 1,337-test collection, all 52 levels
and the asset dry run passed. See the [current audit](../maintenance/REPOSITORY_AUDIT.md).

2026-11-14 — Canonical asset layout. Reduced runtime assets from 425 to 295 files;
relocated 76 files and archived 136 retired project files, 116 validation-cache
files and ten code/document snapshots with restoration records. Every one of
579 original active media files remains byte-identical in the checkout/archive.
Ohio rooms now have location folders and one shared far plane; music/SFX,
backgrounds, sprites and effects load from their owning package directories.
Twenty seeded captures match. Full suite: 1,337 passed, one unchanged timing
failure (FIELD_OPS render P95 5.249 ms vs 5.0 ms), no warnings; isolated profile
and 86 focused checks pass. All 52 levels/14 asset groups validate. Both clean
wheels have 434 matching runtime files; installed reads cover every room,
eleven guardians, both tracks and twelve SFX with zero path violations.
Retired comparison-sheet tests do not imply missing historical portraits were
recovered. Unique approach safety checks migrated to current room tests; 85
maintained test modules remain. See the current audit for evidence and limits.
