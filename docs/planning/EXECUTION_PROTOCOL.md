# Development workflow

Use [CONTRIBUTING.md](../../CONTRIBUTING.md) for setup and code conventions. The [roadmap](TODO_ROADMAP.md) owns task status; [quality gates](QUALITY_GATES.md) defines acceptance.

## Working on a task

1. Read the current state, relevant task card and open issues. Inspect the working tree, callers and content before editing.
2. Define the observable result and the checks needed to verify it. Keep the change focused and preserve unrelated work.
3. Implement through the normal game entry point or a documented development command. Do not leave an unused parallel implementation.
4. Run the affected checks. For interactive changes, exercise mapped input, pause/focus, cancellation, retry and exit. Persistent changes also need SaveStore and New/Continue checks.
5. Inspect actual rendered output for visual changes. Report what was observed and what remains untested.
6. Review the diff. Update status and contracts only when behavior or acceptance changes; record material results in the progress log.

A feature can pass automated checks while human playtesting, art, audio or native performance remain open. Mark a task done only when its acceptance criteria are met. Do not treat a generated scorecard, screenshot filename or test count as evidence for a different claim.

## Status

| Status | Meaning |
|---|---|
| planned | Work has not started or dependencies remain |
| ready | Dependencies allow work to start |
| in_progress | Implementation or verification is underway |
| blocked | A named external dependency prevents progress |
| done | Acceptance passed with supporting evidence |
| superseded | A recorded replacement owns the requirement |

## Evidence

Use explicit, unused directories under `_temp/`, `captures/` or `profiles/` for generated output. Use temporary saves and settings. Keep durable reports with the relevant development record; promote only the evidence that is needed.

Record the command, environment, observed result and limitations. Disclose injected prerequisites and direct scene entry. A staged event does not prove the player completed the skipped activity. Dummy SDL does not establish native performance, audible quality, controller hardware support or human playability.

After packaging changes, inspect clean wheels built both from the checkout and from a source distribution, then boot an installed wheel outside the checkout. The game does not require the legacy AI application or live-model tests.

## Retirement and restoration

1. Check imports, manifests, builders, tests, packaging and dynamically constructed resource paths.
2. Verify the replacement through its real caller. Preserve source masters, provenance, user edits and saves.
3. Move unique retired material to `_trash/<date>_<task>/<original-relative-path>`.
4. Record original and archived paths, SHA-256, reason, replacement, checks and restoration steps in `_trash/TRASH_LOG.md` and `docs/migration/archive-manifest.json`.
5. Update references and rerun affected checks. Verify rebuilds when source locations change.
6. To restore, check the archive hash, confirm the original path is free, restore it, revert dependent references and rerun the checks.

Keep recovery material until the user requests its removal. A text search alone cannot prove a dynamic asset is unused.
