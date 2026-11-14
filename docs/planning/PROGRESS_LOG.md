# Progress log

2026-11-13 — Repository separation. Current game retained from the full working tree, historical AI recovered separately, flat src layout introduced, and live-model runtime dependency removed. Detailed verification and preservation records are in [migration report](../migration/REPORT.md).

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
