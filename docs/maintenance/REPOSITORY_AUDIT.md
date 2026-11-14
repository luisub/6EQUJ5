# Repository audit — 2026-11-14

The asset-layout pass consolidated runtime files into their owning folders,
updated their consumers and removed retired exports, builders and tests. Music
loads from `src/assets/audio`; bitmap scene backgrounds load from
`src/assets/environments`. Source masters, documentation and `_trash` are not
runtime inputs.

- [Current directory tree](repository-tree.txt)
- [Verification summary](verification.json)
- [Full restoration index](archive-manifest.json)
- [Asset ownership and rebuild guide](../ASSETS.md)

## Consolidation

Runtime assets decreased from **425 to 295 files** (30.6% fewer), and from
48,841,607 to 41,392,223 bytes. **76 retained files** now have canonical paths.
There are **no byte-identical media duplicates inside `src/assets`**.

**136 retired project files** are preserved under
`_trash/2026-11-14_asset_layout/`, with hashes, reasons and restoration steps.
Code/document snapshots are recorded separately. All **579 original media files**
in the active `src/` and `docs/` trees are preserved byte-for-byte in the active
checkout or this archive. Archiving does not reclaim their disk space.

| Area | Result |
|---|---|
| Ohio scenery | Distinct approach, campus, salvage yard, dish, arena and bunker rooms grouped under `environments/ohio/`; obsolete approach v1 retired |
| Shared scenery | Four identical far planes replaced by one `ohio/shared/far.png`; shared replacement cannot invalidate other rooms |
| Other backgrounds | Earth locations and eleven alien worlds have one active directory per location, without versioned runtime folder names |
| Bunker | Current background and two overlays grouped together; old layers, tileset, inspection sheets and previews archived |
| Mateo | Organized outfit animations only; flat duplicates, unused snapshots and unused portrait archived; bunker reuses navy idle |
| Enemy animation | Seventeen repeated image files replaced with manifest aliases; frame order and timing preserved |
| Bosses and effects | Current Greenkeeper and effect families use canonical names; obsolete bitmap fallbacks archived; procedural recovery retained |
| Civilization dossiers | Face, environment vignette and constellation retained; eleven unused composites and review products archived |
| Build tools | Old approach, Greenkeeper-bitmap and Ohio-texture generators archived; supported transaction checks retained in current builders |
| Tests | One obsolete approach-builder test module archived after migrating unique safety cases; 85 maintained test modules remain |
| Metadata | Stale aggregate asset registry removed; current family manifests own resource references |

The accepted bunker overlays and five refined olive poses have explicit lossless
rebuild masters. These source/export pairs have different responsibilities.
Historical source versions and provenance remain under `src/art`, outside the
runtime tree. Optional missing/corrupt backgrounds use procedural rendering;
small dossier plates are no longer reused as gameplay backgrounds.

## Verification

The final full suite reports **1,337 passed, one timing failure, no warnings**.
FIELD_OPS render P95 is **5.249 ms** against the unchanged **5.0 ms** limit.
The final focused checks pass **86/86**. Detailed results are recorded in
[verification.json](verification.json).
All **52 levels** validate; all **14 protected asset groups** pass the builder
dry run. Twenty seeded renderer screenshots/GIFs match their pre-change files
byte-for-byte. No normal artwork or animation timing changed.

Both a clean wheel and a wheel rebuilt from the source distribution contain
**434 matching runtime files**. Each boots outside the checkout, enters the
opening bunker and loads all eleven native world/guardian pairs. The installed
package excludes source masters, tools and tests. Actual resource-read tracing
covers all 52 rooms, eleven guardians, both music tracks and sound effects;
see the verification summary for its checked categories and results.

The initial full suite passed 1,336 tests and hit the existing FIELD_OPS timing
budget (13.187 ms total P95 against 8.0 ms); the isolated timing check then passed.
A test-only audio preload race was corrected before the final run: per-frame
no-read assertions now wait for the already requested background music read.
No exception was suppressed and no timing threshold changed.

The old historical-portrait failure disappeared because the obsolete comparison
sheet product and its test were retired together. Those missing portraits were
**not recovered**, and modern portraits were not substituted. Supported
transaction, path-containment, corrupt-asset and procedural-fallback checks
remain active.

Checks use disposable saves/settings and dummy SDL. They establish automated
behavior and package independence, not audible quality, controller hardware,
native-display performance or a human campaign playthrough.

## Earlier cleanup and restoration

The first pass archived 15,007 temporary/build/review files and grouped art
sources by subject. The second pass archived `docs/migration/`, seven one-off
refinement scripts and redundant gallery/maintenance material. Previous reports
and exact results remain in their dated `_trash` directories. The sole current
restoration index is `docs/maintenance/archive-manifest.json`; no historical
migration document is a game dependency.

Per-file retirement and relocation records and the current validation logs are
under [asset-layout evidence](../../_trash/2026-11-14_asset_layout/verification/).
Verify hashes before restoring. Preserve newer files and restore dependent
images, manifests and consumers together. No player saves or Git index/history
were changed; no stage, commit, push or pull was performed.
