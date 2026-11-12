# Roadmap and evidence audit — 2026-11-12

Scope: read-only comparison of the canonical planning files, latest installed-wheel report, current issue disposition, and representative historical task evidence. No tests, builds, GUI, or runtime changes were performed. The active firing-light experiment was not used as acceptance evidence.

## Summary

The roadmap's task table and gate table are internally consistent with the latest handoff: 66 tasks, 36 done, 5 in progress, 25 planned; A12/A13/A14/S09/S11 remain in progress, P01a remains planned, and G2/G3 remain pending. Do not promote those statuses based on the 510-test checkpoint or art packaging results. The latest handoff and wheel report corroborate nine installed families, 25 hash-matched manifest/component files, eight scene smoke entries, and the 487-member clean wheel.

The main maintenance problem is not the authoritative task table; it is conflicting legacy prose and a stale current-state dependency sentence. Preserve the roadmap statuses and rewrite the current snapshot as one concise point-in-time summary with separately labeled historical entries/links.

## Findings

### 1. Current-state next-work sentence misstates I38 integration — medium

`video_game/planning/CURRENT_STATE.md:24` says the A12 fade/load fix is “awaiting final integration.” The current checkpoint at lines 4–6 reports the 510 test run and current clean-wheel smoke; the issue disposition at `video_game/planning/ISSUES_AND_DECISIONS.md:27` says the final combined suite and clean-wheel smoke passed after the fix. The remaining dependency is audible transition/volume acceptance, not integration. The roadmap continuation at `video_game/planning/TODO_ROADMAP.md:91` already describes the fix as bounded and A12 as open for audible acceptance.

Suggested correction: “I38's bounded fix is integrated and covered by the latest combined suite and wheel smoke; A12 remains open for audible transition/volume acceptance.”

### 2. Historical task reports contain unqualified gate-complete verdicts — high

The canonical current state and current audit disposition clearly keep gates open, but older reports remain easy to mistake for current acceptance:

- `video_game/planning/evidence/A12/report.md:14` claims complete audio delivery and smooth transitions; current A12 supplements explicitly leave audible checks open.
- `video_game/planning/evidence/A13/report.md` reports profiling completion; current issue I24 and roadmap A13 continuation state no native graphical measurement exists. `ISSUES_AND_DECISIONS.md:89` also retains a CPU_PROFILE queue entry claiming an “Official 120s soak,” 590–930 FPS and P95 <1.95 ms, which conflicts with the same document's current disposition at line 13 and `CURRENT_STATE.md:24` stating the native display was unavailable and no FPS was measured.
- `video_game/planning/evidence/A14/report.md:6,128–130` says Gate G2 passed; current route supplements at `evidence/A14/2026-11-11_exit_reentry/report.md:16` and `CURRENT_STATE.md:24` keep G2 pending native/human acceptance.
- `video_game/planning/PROGRESS_LOG.md:51–77` says S11/G3 passed and P01a is ready; its later audit entries and the roadmap/current state reverse that conclusion, but those early claims are not labeled superseded at the claim itself.

Suggested action: add a prominent “historical, superseded verdict — see current roadmap and audit” notice to the affected legacy reports/queue entry, or create a single index mapping each legacy claim to its current disposition. Do not delete the historical material.

### 3. Audit history and single-owner status rule are sound, but status prose duplicates too much — low

`video_game/AGENTS.md:3` correctly says the roadmap is the task-status owner and current audit evidence overrides older completion claims. `TODO_ROADMAP.md:3–10` repeats three dated status snapshots before the table; CURRENT_STATE stacks many earlier checkpoint summaries. None changes the table, but this increases the chance that an older paragraph is quoted out of context. Replace the duplicated top-of-roadmap snapshots with a short current checkpoint and links to the detailed/historical handoff sections; retain detailed checkpoints in evidence and progress history.

### 4. Dependency chain and gate separation are appropriately represented — verified

- A12 → A13 → A14 is consistent across roadmap rows and task cards. A13 depends on A12 (`milestones/02_action_slice.md:366–389`); A14 depends on A13/C08 (`:393–416`). Current limitations remain in `TODO_ROADMAP.md:91`.
- S09 is in progress and S11 is in progress with S09 as a dependency (`milestones/03_science_and_reality.md:238–264,297–320`). S11's earned route is evidence for bounded mechanics/persistence, not full counter, claim-source, human readability, or G3 acceptance.
- G2 and G3 remain pending in the milestone exit table (`TODO_ROADMAP.md:98–104`); P01a remains planned. This matches `QUALITY_GATES.md` G2/G3 requirements for normal routes, playthrough and explicit counters/costs/resets.

## Verified latest checkpoint

- `video_game/planning/CURRENT_STATE.md:4–8`: 510 passed, two named live tests deselected; current 487-member wheel hash and isolated installed smoke; nine families across eight scenes; visual/audio/native performance and G2/G3 still open.
- `video_game/art/reviews/visual_upgrade/previews/remaining_scenes_wheel_check_v01/report.md:1–9`: exact copied-source build/install/smoke command and scope; 25 manifest/component members hash-matched; smoke entered and rendered eight scenes using installed code/assets. This does not establish native display, continuous motion, human art review, audio, graphical performance or milestone acceptance.
- `TODO_ROADMAP.md:12–13,75–104`: task count/statuses and gate states align with current handoff.

## Recommended documentation action

1. Correct the I38 “awaiting final integration” sentence.
2. Mark the contradictory A12/A13/A14/S11 legacy verdicts and stale performance queue claim as superseded in place, with a link to the current audit/current state.
3. Condense only repeated dated snapshots at the top of the roadmap/current handoff; preserve evidence, progress history, and all task IDs/statuses.
4. Leave all statuses unchanged pending required human, audible, real-display, art/motion, fairness, and scientific source review.
