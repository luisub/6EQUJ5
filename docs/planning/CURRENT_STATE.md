# Current state — 2026-11-14

## Repository and validation

The offline game lives in this checkout; the legacy AI application is separate.
The flat `src/` directory installs as `video_game`, and `.venv/bin/6equj5-game`
remains the launch command. Runtime resources live in `src/assets/` and `src/data/`.

The [repository audit](../maintenance/REPOSITORY_AUDIT.md) records the current
[tree](../maintenance/repository-tree.txt) and [verification](../maintenance/verification.json).
The canonical-layout audit reduced runtime assets from 425 to 295; the latest
soundtrack, motion and finale additions bring the current total to 315. In that audit,
76 retained files acquired canonical
paths and 136 retired project files are recoverable under
`_trash/2026-11-14_asset_layout/`. Music/SFX use `assets/audio`; all bitmap scene
backgrounds use `assets/environments`, grouped by location. Ohio rooms are distinct
locations with one shared far plane. Mateo and enemy animation manifests reuse
canonical images without changing timing. No exact runtime-media duplicates remain.

Art masters, briefs and research stay under `src/art/`; tests and deterministic
fixtures stay in `src/tests/`. The 87 maintained test modules include the unique
transaction checks migrated from the retired approach builder. The old comparison
sheet product and its missing historical-portrait check were retired together;
the missing source was not recovered or replaced with modern artwork.

The earlier layout audit validated all 52 levels and 14 protected asset groups.
Twenty seeded renderer
captures are byte-identical. Clean direct/sdist wheels contain 434 runtime files,
boot independently and load every native world/guardian pair. Installed resource
tracing covers all rooms, both music tracks and SFX without escaping the owned
asset/data directories. Final full suite: 1,337 passed and one FIELD_OPS render-budget failure
(5.249 ms P95 versus 5.0 ms), without warnings. The isolated timing check passed;
the unchanged threshold remains open. All 86 focused checks passed.

Earlier repository and documentation cleanups are preserved in their dated
`_trash` folders. `docs/migration/` is retired; the sole full restoration index is
`docs/maintenance/archive-manifest.json`. See the [asset guide](../ASSETS.md) for
current ownership, source/export pairs and procedural fallbacks.

## Launch, movement and campaign

Launch displays the banner, soundtrack, one Press Start action and the
“by @luisub 2026” credit. Starting creates a fresh run immediately; settings
persist. Held start input cannot dismiss the opening story. Continue and
save recovery remain available through the existing developer APIs.

The basement opening retains the owner's supplied passage and galaxy briefing.
Ohio connects approach → campus → salvage yard → dish → Greenkeeper, with
3,520 px of authored terrain. Collection, science, repair and defense remain
optional; NEXT and empty-lab Continue Outside lead to the field. Walk boundaries
work in both directions and both combat modes, without door prompts.
The ordinary Act II–V rooms are 960 px wide. Old checkpoint aliases still work.

Leaving an incomplete optional defense grants no reward. Space remains jump;
R or the retry button restarts failed defense. Boss arrivals allow immediate
movement and firing. Defeating each boss still unlocks earned progression.
The eleven-world guardian/message journey leads back to both final Core forms.
Only defeating both final forms completes the journey.

## Artwork, combat and travel

Temporary weapon timers occupy a compact upper-right panel in both field and
boss scenes; long notifications leave room for the panel. Map captions are
simplified in the opening, travel screen and README captures. Enemy-entry labels
are removed; hazard edge markers and attack warnings remain.

SCAN-H now has Rift Raptor dinosaurs. Raptors, the golden Resonance Effigies and
Beacon Mites have four-pose leg cycles driven by actual distance traveled,
including the larger charging hazards. Beacon Mites use grounded lunges rather
than hovering. Poses and mirrored variants are cached on room entry; stopping,
pause and stun do not advance the stride. Runtime artwork remains under
`assets/sprites/planet_threats`; canonical masters and recipes are under
`art/source/planet_threats`. Superseded artwork is recoverable in `_trash`.

Latest checks: 1,343 tests passed; the existing FIELD_OPS render-budget check
measured 5.54 ms against 5.0 ms. All 52 levels and 14 protected asset groups
validate. A clean installed wheel boots and renders all three animated enemy
and hazard families. 144 HUD configurations had no text overlaps and matched
the full-flush renderer exactly. Scene captures verify grounded feet, leg poses,
map captions and the Memory Extractor energy-field presentation; these remain
staged visual checks, not a human campaign playthrough.

All eleven alien worlds have distinct 1920 × 540 native panoramas and transparent
256 × 192 guardian bodies. They were produced and reviewed one civilization at
a time; preserve that workflow. Proxima's feet, teleport visibility, paired attack
warnings and the Beacon Forger recovery-core alignment are corrected.
World-specific weather and signal particles are bounded and remain behind actors.
Denver retains its Fitzsimons-inspired building and mountain panorama.

Body hits always damage guardians; a small recovery core offers bonus damage.
The earlier perfect-aim projectile fixtures took about 10–13 seconds per guardian
and 23 seconds for the two-form finale. These ignore incoming damage and are not
human difficulty ratings. Temporary weapon expiration and earned rewards remain.

Boss victories use a 2.6-second destruction effect, skippable with a fresh input.
Victory and contact text use short pages requiring acknowledgement. The final
ending now spans six pages, followed by four pages in the restored park.
Contact receipts save before travel. Briefing and travel share a winding route;
the ship reaches its destination before a centered vortex opens. The 4.1-second
transition is immediately skippable, but arrival still requires a successful save.

The README uses promotional title artwork, fifteen embedded renderer screenshots
and seven renderer GIFs, with seven additional full-scene stills linked. Capture fixtures are disclosed in the media notes.

## Remaining work and evidence

Armed airborne poses, guardian motion polish, human fairness/full-playthrough
review, audible quality, physical controllers and native display performance
remain open. J01–J06 and formal acceptance gates retain their roadmap status.
Headless tests and staged captures do not establish those acceptance criteria.

Historical validation narratives were consolidated without discarding them.
The full preceding state is preserved at
`_trash/2026-11-14_repository_cleanup/documentation-before-cleanup/CURRENT_STATE.md`.
Earlier migration records remain in [migration/REPORT.md](../../_trash/2026-11-14_repository_compaction/docs/migration/REPORT.md)
and [TRANSFER_COMPLETE.md](../../_trash/2026-11-14_repository_compaction/docs/migration/TRANSFER_COMPLETE.md). Per-file archive
paths, SHA-256 hashes and restoration instructions are in the
[archive manifest](../maintenance/archive-manifest.json).

## World soundtracks and README refresh

Each of the eleven signal worlds now has an original 32-bar instrumental loop
(65–107 seconds), with a distinct key/mode, motif, tempo and arrangement. The two
existing Earth/bunker MP3s remain; the audio bank contains thirteen music tracks
and twelve effects. Packaged OGG files add 13.9 MB. World assignments belong to
`assets/audio/manifest.json`; source scores and the reproducible NumPy/ffmpeg
builder remain outside the installed game.

Scene entry selects music after the world context is established. Exploration,
guardian and earned contact share a score without restarting it or extending a
pending fade. Transit retains the departing score until arrival. Unknown or
missing world files fall back to Earth music. New game returns to the bunker
score. Existing mute, volume, cancellation and main-thread mixer ownership remain.

README media now include native 960×540, 256-color GIFs, three labeled native
creature-motion crops with linked full scenes, and the Memory Extractor's first
active energy attack reached through normal updates. All 26 captures use isolated
saves and disclosed progression/placement fixtures. Changed captures and the old
audio manifest are preserved with restoration records. Original composed tracks
and source recipes are licensed with the repository. Human listening on actual
speakers remains part of A12 acceptance.

Latest validation: 1,351 tests passed; the render-budget test measured BOSS_BOUNTY
at 5.394 ms P95 against 5.0 ms in the full suite, then passed alone in 3.35 seconds.
All 38 focused audio/journey checks, 52 levels and 14 asset groups pass. A clean
wheel boots outside the checkout and streams all thirteen tracks, with volume
and mute verified. World scores measure −18.7 to −18.1 LUFS and stay below
−4.5 dBFS true peak. All 26 media hashes, 16 archive records and README links
verify. Native captures were inspected; the local browser preview was blocked
by its origin permission check, so rendered README layout acceptance remains open.

## Core liberation and restored Denver

The final chamber now has its own machine-cathedral panorama and original green
projected Core, with bounded falling-code activity and a faster second-form scan.
Its two full-health forms, eleven required receipts, attack behavior and earned
victory flag remain intact. Six closing dialogue pages explain the independent
broadcast, disconnection of the Core's control network, restored city links and
local control of hospitals, power and water. Mateo explicitly confirms that they
saved the world. See [the story and ending](../STORY.md).

Completion opens `RESTORED_EARTH`, three springs later in Central Park, Denver.
The native panorama contains trees, water, warm light and the distant skyline;
bounded glints, birds and three four-pose family groups animate around a walkable
Mateo. Four more dialogue pages wait for input and save each acknowledgement.
The park remains open after reading, with message replay and explicit title exit.
Completed Continue/recovery returns through the bunker to the saved park page;
New game resets the scene. Page-save and final-completion failures retain the
previous durable progress and allow retry. The terrestrial-memory score returns
for the homecoming. Missing optional park scenery has a simple green fallback.

Four canonical image masters and a complete recipe rebuild eight exports exactly.
The replaced Core body and manifest are archived with verified hashes. Three new
README captures have their own metadata, bringing the maintained gallery to 29.
The capture tool stages eleven prior receipts/victories and a player position,
then defeats both final forms with mapped fire before entering the park. Actual
Core, dialogue, park and walking-pose captures were inspected. They remain staged
renderer evidence rather than a human campaign playthrough.

Final validation: **1,360 tests passed in 184.20 seconds**, including the unchanged
render-budget assertions. All 55 focused ending/journey/story/audio checks and
40 scenery/park checks pass, as do 52 levels and 14 protected asset groups. The
initial full run exposed an old background-count assertion; it now checks all
20 backgrounds, including both finale additions. A clean wheel with 315 runtime
asset files boots outside the checkout, renders the Core and park, recovers a
saved park page, streams the homecoming music and resets correctly on New game.
Park render P95 measured 5.49 ms with dummy SDL during that bounded probe; this
is not native-display certification. All 29 README media hashes, two new archive
records and checked local links verify. Formal gate statuses are unchanged.
