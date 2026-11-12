# Readiness and repository-retention audit

Date: 2026-11-12. This document reconciles the current planning record with the independent [roadmap and evidence audit](../../../../art/reviews/visual_upgrade/previews/plan_audit_20261112_roadmap/report.md) and [cleanup and integrity audit](../../../../art/reviews/visual_upgrade/previews/plan_audit_20261112_cleanup/report.md). Those audits were read-only; their findings were checked against the roadmap, issue disposition, historical reports and current checkpoint. This reconciliation does not certify the in-progress firing-light experiment or change any task or gate verdict.

## Current disposition

The canonical [roadmap](../../../TODO_ROADMAP.md) contains **66 tasks: 36 done, 5 in progress and 25 planned**. A12, A13, A14, S09 and S11 remain in progress. P01a remains planned. G0/G1 retain earlier acceptance; G2/G3/G4/G5 remain pending. The task and gate tables were not altered. The [current-state snapshot](../../../CURRENT_STATE.md) is now concise and dependency ordered; its entire pre-edit text is preserved byte-for-byte as [current_state_before.md](current_state_before.md).

The current completed headless checkpoint, installed-family verification and isolated wheel smoke are described in [current state](../../../CURRENT_STATE.md) and the linked evidence. They are bounded evidence, not a substitute for human play, audio, native-window motion, graphical performance, scientific-source review or art acceptance. The active firing-light work remains separately owned and under review.

## Findings and actions

- **I38:** the bounded A12 fade/load fix was integrated and covered by the latest combined suite and clean-wheel smoke. The roadmap continuation now says so; audible transition and volume acceptance remain open. A13 follows A12, and A14 follows A13 and its other listed dependency.
- **Historical verdicts:** prominent supersession notices now appear above the untouched historical bodies of [A12](../../A12/report.md), [A13](../../A13/report.md) and [A14](../../A14/report.md). Their old completion, performance or G2 claims are not current acceptance. The CPU_PROFILE queue in [issues and decisions](../../../ISSUES_AND_DECISIONS.md) now labels its old performance claim superseded and unverified; the prior native-display attempt was unavailable and did not measure real-display FPS. Earlier S11/G3 and P01a statements in [progress history](../../../PROGRESS_LOG.md) are also superseded by the current roadmap and audit; the historical log was not rewritten.
- **Remaining work:** S09 still needs counter readability, encounter fairness and faction art/motion review, including the unverified I37 airborne-hound geometry. S11 requires its documented dependencies plus claim/source, readability, mechanics and persistence acceptance. P01a and later campaign/release work remain behind their roadmap dependencies. An existing bottom-HUD overlap with busy floor or notification content is a future R01 readability observation; the baseline predates the firing-light work and does not establish a new lighting regression.
- **Backups:** all edited planning/evidence files were copied byte-for-byte and checked against SHA-256 immediately before modification; [backup manifest](backup_manifest.json). The subsequent current-state version-control note has its own verified [second-edit manifest](second_edit_manifest.json). These local copies support recovery; they do not demonstrate remote persistence or an independent backup.

## Repository retention and next checkpoint

The game tree remains untracked, and the existing terminal/CLI edits and tracked packaging changes predate this audit. A **reviewed version-control checkpoint** is needed for intended game code, data, runtime assets and documentation. Do not blanket-stage the full evidence/master tree or modify unrelated CLI edits. Review durable source and evidence retention separately from cleanup. No files were staged or committed during this audit.

No justified runtime retirement or deletion was established. Preserve installed assets and manifests, source masters, generated files, player-save behavior, evidence, recovery copies and existing `_trash` archives. Exact duplicate bytes in different evidence folders may have different provenance; any future deduplication requires an owner-reviewed manifest and the project retirement protocol. Cache housekeeping is optional and was not performed. No archive, master, evidence or cache was moved or purged in this increment.

No new test run, visual acceptance, performance claim, time estimate or milestone promotion is made by this documentation reconciliation.
