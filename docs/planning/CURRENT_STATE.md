# Current state — 2026-11-14

## Repository and validation

The offline game lives in this checkout; the legacy AI application is separate.
The flat `src/` directory installs as `video_game`, and `.venv/bin/6equj5-game`
remains the launch command. Runtime resources live in `src/assets/` and `src/data/`.

The [repository audit](../maintenance/REPOSITORY_AUDIT.md) records the current
[tree](../maintenance/repository-tree.txt) and [verification](../maintenance/verification.json).
Runtime asset files decreased from 425 to 295; 76 retained files have canonical
paths and 136 retired project files are recoverable under
`_trash/2026-11-14_asset_layout/`. Music/SFX use `assets/audio`; all bitmap scene
backgrounds use `assets/environments`, grouped by location. Ohio rooms are distinct
locations with one shared far plane. Mateo and enemy animation manifests reuse
canonical images without changing timing. No exact runtime-media duplicates remain.

Art masters, briefs and research stay under `src/art/`; tests and deterministic
fixtures stay in `src/tests/`. The 85 maintained test modules include the unique
transaction checks migrated from the retired approach builder. The old comparison
sheet product and its missing historical-portrait check were retired together;
the missing source was not recovered or replaced with modern artwork.

All 52 levels and 14 protected asset groups validate. Twenty seeded renderer
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
Victory, contact and ending text each fit one short page and require acknowledgement.
Contact receipts save before travel. Briefing and travel share a winding route;
the ship reaches its destination before a centered vortex opens. The 4.1-second
transition is immediately skippable, but arrival still requires a successful save.

The README uses promotional title artwork, thirteen renderer screenshots and
three renderer GIFs. Capture fixtures are disclosed in the media notes.

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
