# Game assets

The installed game reads exports from `src/assets/` and campaign content from
`src/data/`. Music and sound effects belong in `assets/audio`; scene backgrounds
belong in `assets/environments`. Loaders resolve these directories relative to
the installed `video_game` package, independent of the working directory.
Source masters and export recipes belong in `src/art/source/`, outside runtime
packages. Temporary output and `_trash` are never runtime inputs.

## Runtime ownership

| Content | Location within `src/assets/` | Selection and rebuild owner |
|---|---|---|
| Music and sound effects | `audio/` | `engine/audio.py`; thirteen music tracks and twelve effects; absolute paths, traversal and symlink redirects rejected |
| Ohio rooms | `environments/ohio/{approach,campus,salvage_yard,dish,arena,bunker}/` | `engine/room_art_contracts.py`, `native_room_assets.py`; `tools/build_room_family.py` |
| Shared Ohio textures | `environments/ohio/shared/` | One far plane for approach, salvage, dish and arena; tileset and mist used by world/hazard rendering |
| Later Earth backgrounds | `environments/{neo_denver,area_51,gobekli_tepe,vla}/` | `engine/campaign_scenery.py`; `tools/build_campaign_art.py` |
| Historical rooms | `environments/{dodleston_relay,mandela_annex,ehman_1977}/` | Native-room contracts and builder |
| Eleven alien panoramas | `environments/alien_worlds/fasr_<id>/` | `data/alien_journey.json`; campaign scenery and export builder |
| Core chamber and restored Denver | `environments/earth_finale/{core_network,central_park}/` | `engine/campaign_scenery.py`; `tools/build_finale_art.py` |
| Park families | `sprites/people/park_family/` | `engine/scenes/restored_earth.py`; four cached walking poses and mirrored variants |
| Alien guardians and Earth bosses | `sprites/bosses/` | Boss controllers and family manifests; Greenkeeper uses `greenkeeper/` |
| Mateo | `sprites/mateo/<outfit>/` | One animation manifest, individual poses and bunker strips; frame paths stay within this directory |
| Patrol enemies | `sprites/enemies/<type>/` | Manifests preserve animation order/timing while repeated slots share one image |
| Planet threats | `sprites/planet_threats/<type>/` | `engine/planet_encounters.py`, `world_hazards.py`; `tools/build_planet_threat.py` |
| Combat and travel effects | `effects/{energy_filament,maser_discharge,firing_flash,galaxy_transit}/` | Validated family loaders and builders |
| Civilization dossiers | `civilizations/` | Portrait, environment vignette and constellation chart per civilization; these small UI plates are not scene backgrounds |
| Title and developer palette | `ui/` | Title screen and bunker developer view |

Ohio's approach, campus, salvage yard, dish and arena are different rooms, not
alternate city versions. Their directories now reflect that distinction. The
campus has its own far plane. Area 51 and Göbekli Tepe each have two distinct
locations. Stable logical identifiers in level data may retain old version
suffixes for compatibility; they map to the canonical directories above.

## Manifests and rebuilding

`art/source/finale/recipe.json` owns four generated masters, full prompts and
registration settings. `build_finale_art` exports two 1920×540 panoramas, the
256×192 projected Core and a 512×96 family strip with four 128×96 cells. Shared
cropping and foot registration keep family poses grounded. Background and boss
exports use the existing scenery manifest contracts; family loading validates
the strip's dimensions and hash. Original Core exports remain in the restoration
index. Source masters and tools are excluded from runtime packages.

`audio/manifest.json` owns the eleven world-to-track assignments, titles, hashes
and durations. Two original MP3s cover Earth and the observatory; eleven stereo
Vorbis scores cover the signal worlds. Scores and provenance live in
`art/source/audio/world_themes.json`. `tools/build_world_music.py` synthesizes
the original compositions without samples, with distinct motifs, modes, tempos,
arrangements and circular effect tails. NumPy and a local ffmpeg executable are
needed only for rebuilding. The game needs neither ffmpeg nor a network service.
Generate into a new staging directory, review the audio, then copy the OGG files
and merge `music_tracks.json` into the canonical audio manifest. The SFX builder
preserves existing music entries. Ogg container hashes can vary by encoder;
the synthesis is seeded and produces deterministic PCM.

Rift Raptors (SCAN-H), Resonance Effigies (FASR-010) and Beacon Mites (FASR-007)
have a 96×72 idle body and an optional 384×72 four-pose `run.png`. Each manifest
hashes both files. The loader checks every pose against the original safe sprite
bounds; unavailable motion art falls back to the idle body. Runtime strides
follow actual travel distance and reuse cached left/right frames.

Their two-file source folders contain `run_master.png` and `provenance.json`,
including the exact generation prompt, reference hash, shared registration and
rebuild command. `build_planet_threat --master` exports all four cells with one
crop and scale. `--replace-existing` preserves old exports through the asset
transaction archive before promotion. Superseded static sources are indexed
in the archive manifest.

Family manifests own filenames, geometry, hashes and animation order. The unused
aggregate `assets/manifest.json` was retired because it described an obsolete
subset. There is no second runtime registry to keep synchronized.

`build_assets --dry-run` checks the protected civilization, Mateo, bunker-overlay
and palette groups. Room, effect, campaign and Greenkeeper builders retain
transaction locks, staged validation and recoverable replacement. Shared Ohio
far-plane replacements must agree with every dependent family; changing one
room cannot silently invalidate the others.

Bunker art consists of a native background plus `foreground.png` and
`lighting.png`; `scene.json` references those overlays and canonical Mateo poses.
The approved overlays and five refined olive-field poses have lossless rebuild
masters under `src/art/source/bunker/overlays/` and
`src/art/source/mateo/approved_poses/`. These source/export pairs are intentional.
The accepted shared Ohio tileset and mist remain runtime exports; the old
procedural generator did not reproduce them and has been archived.

Other source families are grouped by environment, boss, effect, character and
civilization. The [source guide](../src/art/README.md) records their ownership.
Do not replace accepted exports with an older procedural baseline. Build into a
temporary directory and compare pixels before an intentional replacement.

Panoramas are opaque 1920 × 540 PNGs; guardian bodies are transparent
256 × 192 PNGs. Keep their manifest geometry and foot anchors aligned with the
480 × 270 gameplay coordinates and 960 × 540 renderer. Combat core offsets in
`data/balance.json` use logical pixels from the body's rectangle center.

## Retirement and recovery

The 2026-11-14 asset-layout pass retired duplicate flat Mateo exports, repeated
enemy frames, obsolete approach/energy versions, old bunker layers and previews,
old Greenkeeper fallback bitmaps, unused civilization composites and review
sheets. Current image pixels and normal animation timing are preserved. Missing
or corrupt optional room, effect and boss art uses procedural fallback instead
of loading a second historical image family.

The obsolete comparison-sheet product and its historical-portrait source check
were retired together. The missing historical portraits were **not recovered**;
modern portraits were not substituted. Supported transaction safety cases from
the old approach-builder tests now live with the canonical room-builder tests.

All retired material is recoverable under `_trash/2026-11-14_asset_layout/`.
Earlier cleanups remain in their dated directories. The sole full restoration
index is [maintenance/archive-manifest.json](maintenance/archive-manifest.json),
which records original path, archive path, SHA-256 and reason. Restore matching
images, manifests and consumers together, preserving newer files first.

See the [repository audit](maintenance/REPOSITORY_AUDIT.md) for the current tree,
package checks, actual resource-read tracing and verification limits.
