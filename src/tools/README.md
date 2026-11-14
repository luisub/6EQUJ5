# Developer commands

Run tools as `python -m video_game.tools.<name>` from a repository checkout. Art builders need the preserved `src/art/source/` masters. Installed game wheels contain runtime assets, not rebuild masters or planning evidence.

- `build_assets --dry-run`: check/preserve locked asset groups. Intentional replacement follows the archive protocol.
- `validate_content`: validate all authored levels against campaign data.
- `capture_runtime_audit --output-dir PATH`: actual rendered lab, annex, relay and flashback surfaces at native/3x sizes. Uses disclosed prerequisite fixtures and temporary saves; makes no gate verdict.
- `preview_assets --output-dir PATH`: bunker/terminal previews.
- `capture_readme --output PATH`: fresh README stills and compact GIFs from the actual renderer, with temporary saves/settings and disclosed scene/progression fixtures. Requires a new output directory; records hashes and capture setup. Presentation media, not a full-playthrough verdict.
- `capture_alien_world --world alien_005 --output PATH`: native field start/middle/end, 2× CRT views, two seconds of field motion, and guardian telegraph/hit/recovery captures. Uses temporary saves/settings and disclosed prior-victory and position fixtures; requires a new output directory. Records runtime art/code hashes. Art integration evidence, not a playthrough.
- `profile_game`: headless CPU benchmark. Its dummy-driver results are not graphical performance certification.
- `act_01_traversal --complete --output-dir PATH`: fresh-save scripted normal-key Act I route, actual defense/boss and separate-process Continue. `--through-repair`, `--through-defense` and `--probe-yard` are alternative bounded modes. Output is headless coordinate-timed evidence, not human acceptance; uses temporary saves/settings.
- `mechanics_route --output-dir PATH`: earns Act I first, continues and exercises eight science records, earned equipment, timeline/relay/flashback and child-process Continue; New isolation uses its disposable save. Uses state-informed scripted events and temporary saves/settings; not human acceptance. Named captures and trace may overwrite files in the chosen output directory.
- `faction_runtime_audit --output-dir PATH`: captures four actual M/N pairs in a temporary save using an explicit Act I completion event as prerequisite fixture; existing image names are not overwritten. This is not an earned-campaign route or visual certification.
- `play_act_01`: shortcut integration fixture that writes its route log under `_temp/play_act_01/`. Its verdict is NOT_VERIFIED for G2; use normal controls for acceptance.
- Domain asset builders produce artwork/audio exports. Historical static evidence generators are preserved under `_trash/2026-11-13_separation/historical-tools/` with hashes and restoration instructions; their illustrations do not establish completion, measurements, or review quality.

A14 and S11 static acceptance-card generators were retired to `_trash/2026-11-11_G3_audit/retired/`; their hardcoded scores and mismatched content were misleading. Original hashes and restoration instructions are in its `retirement.json`. Historical report commands refer to those archived versions. Tests, source masters, recovery copies and useful measurement/capture tools remain preserved.

The A13 and S09 static evidence generators were retired to `_trash/2026-11-11_tool_retirement/retired/`: their fixed verdicts and figures could misrepresent results, and A13 also substituted default measurements. See its `retirement.json` for hashes and restoration. Use `profile_game` for measured CPU data and `faction_runtime_audit` for fixture-based runtime captures, subject to the limits above. Historical reports and images are preserved and do not establish current acceptance.

The seven historical `refine_batch_*` scripts are archived under
`_trash/2026-11-14_repository_compaction/src/tools/`. They have no active callers
and modify old artwork in place; preserve them as provenance, not current build
commands. Use the maintained builders above for new exports. The
[restoration index](../../docs/maintenance/archive-manifest.json) records their
original paths and hashes.

Current asset layout uses one export location per family. `build_room_family`
owns Ohio/native room exports; `build_campaign_art` owns later Earth and alien
panoramas; `build_greenkeeper_heavy` writes the canonical Greenkeeper folder.
The retired schema-1 approach builder, old Greenkeeper bitmap generator and old
Ohio texture generator are recoverable under `_trash/2026-11-14_asset_layout/`.
`build_assets` maintains civilizations, Mateo, bunker overlays and the palette;
unused comparison sheets, composites, inspection images and portrait output are
no longer generated. See [asset ownership](../../docs/ASSETS.md).
