# Execution protocol

## One task per session

1. Read CURRENT_STATE.md, the roadmap, the chosen task card, and relevant open issues. Check repository status and current files because another LLM may have changed them.
2. Select the first `ready` task whose dependencies are `done`. If it is blocked, choose another explicitly independent task and record why. Default to one task. Continue through more tasks only when the user's handoff requests it.
3. Record the task as `in_progress` in TODO_ROADMAP.md and identify the files being edited in CURRENT_STATE.md. Check for an existing active owner before overlapping edits.
4. Write a short task plan specifying the observable outcome, touched files, test cases, and risk or uncertainty. Inspect callers and existing data before replacing code. Reuse working behavior.
5. Implement the smallest integrated increment. Every new runtime component must have a caller through the normal game entry point or an explicitly documented development command.
6. Run the task's relevant checks and the current game checkpoint suite. Investigate failures before proceeding. Use the existing CLI tests when shared code, packaging, or imports change. Run both suites at milestone gates.
7. For visible changes, capture and inspect native-resolution and integer-scaled output. For interactive changes, exercise keyboard/controller input, cancellation, pause, retry, and exit as applicable. Record untested checks explicitly.
8. Fix defects in scope and rerun the affected checks. Keep the task `in_progress` if required evidence is missing. A test count or an image filename alone does not establish visual quality or playability.
9. Update the roadmap, current handoff, progress log, issue log, and any changed contracts. Add evidence paths and exact commands. Mark `done` only when every acceptance item passes.
10. Review the resulting file diff. Move superseded files only after the retirement checks below. End with the outcome, checks, remaining limitations, and next ready task.

## Status definitions

| Status | Meaning |
|---|---|
| planned | Dependencies or prior gates remain |
| ready | Dependencies passed and scope is executable |
| in_progress | An implementation attempt is active |
| blocked | A named external dependency prevents this task from proceeding |
| done | Task acceptance passed with linked evidence |
| superseded | Another recorded task replaces this task and its requirements |

Reopen a completed task if evidence becomes invalid. Keep its earlier history in PROGRESS_LOG.md. Split a task when it cannot end in a small verifiable increment. Use child IDs such as `A05a` and `A05b`, update dependencies, and retain the parent's acceptance requirements.

## Evidence records

Use `video_game/planning/evidence/<task-id>/<YYYY-MM-DD>_<attempt>/` for durable evidence. Create a `report.md` plus only relevant screenshots, short clips, metrics, and logs. Scratch exports belong in `video_game/_temp/<task-id>/`. Test scratch output should use pytest temporary directories.

Every report records the task, environment, files changed, exact checks, observed results, visual inspection, failures fixed, known limits, and cleanup performed. Include timings for performance claims and whether the run used real display/audio/Ollama or a dummy implementation.

## Compute and reasoning flags

Use the issue log fields `THINKING`, `GPU_IMAGE`, `GPU_LLM`, `CPU_PROFILE`, `PLATFORM`, or `USER_DECISION`.

Record the concrete question or bottleneck, smallest experiment, required hardware/tool, expected output, measured cost when known, and independent work that can continue. Split uncertainties from implementation before generating many assets or rebuilding all content.

For repeated failures, record what each attempt tested. After two similar failures, change the hypothesis or implementation strategy before repeating. Do not automatically purchase compute, download large models, or launch unbounded jobs. Use available tools and the user's existing authorization. A missing GPU may block an image task while offline gameplay work continues.

## Safe retirement and restoration

1. Identify each candidate and its replacement. Search imports, manifests, build scripts, docs, tests, packaging rules, and dynamically constructed filenames. Classify runtime assets, rebuild sources, evidence, and disposable scratch separately in the inventory.
2. Prove the replacement works through the normal entry point. Preserve unique source masters, provenance, user edits, and save data.
3. Move retired files under `video_game/_trash/<YYYY-MM-DD>_<task-id>/<original-relative-path>`. Keep filenames and original subdirectories to prevent collisions.
4. Record original path, archived path, reason, replacement, SHA-256, dependencies updated, checks, and restoration instructions in `_trash/TRASH_LOG.md` or its linked manifest.
5. Update references and rerun the relevant loader/build/playthrough. Rebuilding must also work if source locations changed.
6. Restore by checking the archive hash, moving the file to its recorded original path if that path is free, reverting associated references, and rerunning the recorded checks.

Retain archived material until a separate explicit cleanup decision. Exclude `_trash`, `_temp`, concepts, and planning evidence from game packages. A filename absent from a static import scan can still be a required source asset or dynamic resource.

## Progress entry template

```text
Date and task ID
Outcome and status
Files changed and observable behavior
Checks executed and results
Evidence paths and visual observations
Failures fixed or unresolved
Compute or reasoning flags
Retired files and restoration record
Next task and any changed assumptions
```

## Scope and implementation discipline

Keep the original terminal package usable. Isolate Pygame dependencies to the game installation path. New tests should target specific regressions or contracts. Existing checkpoint requirements remain active until F02 replaces conflicting audit rules together with their documentation. Avoid code compression to satisfy line counts. Use direct imports and clear responsibilities.

User instructions override these planning defaults. Record necessary adjustments without inventing approval gates for routine, reversible work.

## Audit discipline through Milestone 3

Use `video_game/AGENTS.md` and `CONTROLS.md` for the current owner boundaries and runtime controls. A task's functional implementation can pass automated checks while gate acceptance remains open for normal play, art, audible audio or native graphical performance. Preserve that distinction in status and evidence. If the user permits unavailable live AI to be skipped, record it as skipped rather than blocking unrelated offline work or asserting a live success.

For every mechanic verify (1) a normal route into its scene, (2) a physical-key-to-action caller, (3) state change and failure/retry, (4) a real SaveStore write/load when persistent, (5) New/Continue isolation. An event injected by a test establishes a precondition, not completion of the activity it bypasses. Save-envelope JSON roundtrips are not cross-process persistence evidence. Build and inspect a clean wheel after package changes; namespace discovery and stale build output can hide missing packages or ship planning files. Never use static generated acceptance cards as test evidence.
