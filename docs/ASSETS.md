# Game assets

`src/assets/` contains runtime exports. `src/art/source/` holds the masters and
export recipes; `src/art/reviews/` holds art reviews. Keep new candidates out of
the runtime tree until their dimensions, transparency, placement and game
rendering have been checked.

## Active families

| Content | Runtime location | Selection and rebuild owner |
|---|---|---|
| Ohio rooms | `environments/ohio_*` | `engine/room_art_contracts.py`, `engine/native_room_assets.py`; masters under `src/art/source/visual_upgrade/` |
| Later Earth backgrounds | `environments/campaign_worlds/` | `engine/campaign_scenery.py` and route metadata; `tools/build_campaign_art.py` validates exports |
| Alien world panoramas | `environments/campaign_worlds/realm_fasr_<id>_v1/` | `data/alien_journey.json`; each installed family has its own image hash and provenance |
| Alien guardians | `sprites/bosses/campaign/guardian_fasr_<id>/` | The same journey roster; `tools/build_campaign_art.py` validates body exports |
| Other bosses | `sprites/bosses/` | `engine/bosses/`; separate animation and body manifests |
| Mateo | `sprites/mateo/<outfit>/` | `sprites/mateo/manifest.json` is the animation source of truth |
| Patrol enemies and planet threats | `sprites/enemies/`, `sprites/planet_threats/` | Enemy animation manifests and `engine/planet_encounters.py` |
| Combat effects and galaxy travel | `effects/` | Each loader validates its family manifest before use |
| Civilization dossiers | `civilizations/` | `civilizations/manifest.json`; the small portraits, charts and environment plates are dossier artwork, not full-size landscapes |
| Title and sound | `ui/`, `audio/` | Title metadata, `engine/audio.py` and the scene music map |

New alien-world sources are grouped by civilization under
[`src/art/source/alien_worlds/`](../src/art/source/alien_worlds/). Earlier reviewed
masters remain under [`src/art/source/visual_upgrade/`](../src/art/source/visual_upgrade/),
with their existing provenance. A version suffix is an asset identifier, not a
reliable indication that a file can be deleted.

Panoramas are opaque 1920 × 540 PNGs. Guardian bodies are transparent 256 × 192
PNGs. Their runtime family contains one active export and one manifest; the
original generated master and export recipe belong in the source tree.

Guardian combat targets are tuned in `src/data/balance.json`. The optional
`weak_point_offsets` values use logical pixels from the body's rectangle center;
the Beacon Forger uses an offset to align its recovery target with its chest
reactor. When replacing a body, inspect its feet, hit flash and recovery marker
in the arena, as well as validating the export manifest.

## Versions that still have a purpose

| Files kept | Why both are present |
|---|---|
| `ohio_approach_v2` and `ohio_approach_v1` | The room loader prefers v2 and validates v1 if v2 is unavailable. The two world plates currently share pixels, but their family contracts differ. |
| `energy_filament_v2` and `energy_filament_v1` | The stream loader explicitly tries v2, then v1. |
| `maser_discharge_v2` and `approach_maser_flash_v1` | The current discharge presentation and the fallback firing-light renderer use separate contracts. |
| Flat `sprites/mateo_*` files and organized outfit clips | Some flat files are older rebuild baselines; the bunker still uses manifest-backed strips and sprite references. Several active clips have since changed, so the flat files are not all interchangeable duplicates. |
| Basic enemy/boss poses and animation folders | The basic poses support fallback rendering and legacy builders. |
| Bunker layers and inspection images | The asset rebuild group includes both exports and review products. |

The top-level `src/assets/manifest.json` describes the original locked asset
groups. Newer families have their own manifests; that top-level file is not a
complete inventory of everything the game loads. Follow the scene loader and
family manifest before changing a path.

## Archived exports

The obsolete `gobekli_tepe_v1` runtime family is archived: every authored Göbekli
route selects the car-free v2 background. The legacy identifier remains valid
in route metadata and isolated compatibility tests. Its source masters remain
available.

Five `sprites/mateo/field_outfit/` images were exact duplicates of the active
`olive_field` clips. Those copies are archived, and the refinement builder now
writes directly to the canonical clip paths.

Per-file original paths, archive paths, SHA-256 hashes and restoration steps
are recorded in [`migration/archive-manifest.json`](migration/archive-manifest.json).
Local recovery copies are in `_trash/2026-11-13_asset_cleanup/`. They are excluded
from Git and runtime packages. Restore an image and its matching manifest
together; preserve any newer active version first.

For future cleanup, verify dynamic references and builder inputs, preserve
unique material, and update the archive records before removing a runtime copy.
Run the affected loader tests and the asset-builder dry run afterward.
