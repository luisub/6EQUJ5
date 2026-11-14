# Art sources

`source/` contains descriptive rebuild masters, accepted exports and provenance.
Runtime exports remain in `src/assets/`. Art sources are checkout-only and are
excluded from game wheels and source distributions.

| Directory | Contents |
|---|---|
| `source/alien_worlds/` | All eleven civilization backgrounds and guardians |
| `source/environments/` | Ohio, Earth campaign, annex, relay and flashback scenery |
| `source/bosses/` | Earth bosses, Greenkeeper poses and Göbekli animal studies |
| `source/effects/` | Firing flash, maser, energy streams and galaxy transit |
| `source/mateo/`, `source/props/` | Player masters and environmental objects |
| `source/civilizations/`, `source/bunker/` | Original dossier and bunker rebuild inputs |
| `briefs/` | Authored generation prompts and geometry/visual contracts |
| `references/` | Design research and source-registration notes |
| `palettes/` | Material palettes |

Production inputs no longer live under `visual_upgrade/candidates` or review
folders. The firing-flash source, export and preparation script are together in
`source/effects/firing_flash_v01/`. The 88 UUID-named generated-image copies and
the duplicate FASR-003 guardian source were verified against descriptive masters
before archival; every unique master remains available.

Briefs and provenance include historical decisions and may mention older
captures or generation filenames. They do not override current manifests or
the [current state](../../docs/planning/CURRENT_STATE.md). Historical validation
outputs, recovery snapshots and one-off inspection scripts are preserved under
`_trash/`; exact locations and hashes are in the
[archive manifest](../../docs/maintenance/archive-manifest.json).

Use detailed pixel art, quiet scenery behind readable actors, restrained lights,
and distinct silhouettes/materials for each civilization. Keep gameplay at
480 × 270 and rendering at 960 × 540. Preserve registration, alpha, pivots and
combat geometry when exporting. Review one family at a time in the actual game;
source previews alone do not establish animation or playability acceptance.

Run maintained builders from the repository root as
`.venv/bin/python -m video_game.tools.<name>`. See the
[developer commands](../tools/README.md) for dry runs, captures and rebuilds.
