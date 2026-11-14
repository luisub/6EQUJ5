# Current state — 2026-11-14

## Repository and validation

The offline game lives in this checkout; the legacy AI application is separate.
The flat `src/` directory installs as `video_game`, and `.venv/bin/6equj5-game`
remains the launch command. Runtime resources live in `src/assets/` and `src/data/`.

The [repository audit](../maintenance/REPOSITORY_AUDIT.md) records the cleanup,
verification results and [directory tree](../maintenance/repository-tree.txt).
Art masters now have descriptive domain folders in `src/art/source/`; retained
briefs and research live in `src/art/briefs/` and `src/art/references/`.
Tests and their deterministic fixtures live in `src/tests/`.
Old build copies, completed temporary runs, duplicate masters and historical
review output are preserved in `_trash/2026-11-14_repository_cleanup/`.
See the [asset guide](../ASSETS.md) for current ownership and necessary fallbacks.

The baseline before cleanup had 1,335 passing tests and two failures: missing
historical FASR-001 portrait source and FIELD_OPS render P95 of 5.533 ms against
5.0 ms. The portrait rebuild now expects originals in
`src/art/source/civilizations/legacy_ascii/`, rather than reading `_trash`.
No replacement portraits or relaxed performance limits hide these issues.
The final rerun also passed 1,335 tests with the same two failures (FIELD_OPS
render P95: 5.322 ms). All 52 levels, the asset dry run, 48 focused checks and
18 export reproductions passed. Direct and sdist-derived wheels each contain
564 matching runtime files and boot outside the checkout, including all eleven
native world/guardian families. See the audit for evidence and limits.

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
Earlier migration records remain in [migration/REPORT.md](../migration/REPORT.md)
and [TRANSFER_COMPLETE.md](../migration/TRANSFER_COMPLETE.md). Per-file archive
paths, SHA-256 hashes and restoration instructions are in the
[archive manifest](../migration/archive-manifest.json).
