# Execution prompt for another LLM

Copy the following instructions into the LLM that will implement the next increment.

---

Work on `/Users/nzlab-la/Desktop/Github/6EQUJ5` using the execution plan in `/Users/nzlab-la/Desktop/Github/6EQUJ5/video_game/planning`.

Read these files in order.

1. `/Users/nzlab-la/Desktop/Github/6EQUJ5/video_game/planning/README.md`
2. `/Users/nzlab-la/Desktop/Github/6EQUJ5/video_game/planning/CURRENT_STATE.md`
3. `/Users/nzlab-la/Desktop/Github/6EQUJ5/video_game/planning/EXECUTION_PROTOCOL.md`
4. `/Users/nzlab-la/Desktop/Github/6EQUJ5/video_game/planning/TODO_ROADMAP.md`
5. `/Users/nzlab-la/Desktop/Github/6EQUJ5/video_game/planning/ISSUES_AND_DECISIONS.md`

Then read the selected task card, relevant file map, data contracts and quality gates. Inspect the current repository before editing because another session may have advanced it.

Execute exactly one ready task whose dependencies have passed. The initial next task is F02. If the roadmap has advanced, select its current next ready task. Claim the task in the roadmap and current handoff, then implement it through the normal entry points.

Follow the task's file ownership and ordered actions. Keep each change small, readable and integrated. Use `/opt/anaconda3/envs/6equj5_game/bin/python` for game work. Adapt to existing working code and preserve supported callers and data.

Run the relevant checks and required checkpoint suite. For visual or interactive work, inspect the actual output and record observations. Fix failures within the task before marking it complete. Document missing tool, hardware or reasoning needs with the flag, smallest next experiment, required result and independent work that can proceed.

Use the archive protocol for replaced files, including hashes, original paths, reference updates and restoration instructions. Preserve source masters and uniquely valuable work. Verify dynamically referenced assets before treating them as unused.

Record evidence under the task's planning/evidence directory. Update TODO_ROADMAP.md, CURRENT_STATE.md, PROGRESS_LOG.md and ISSUES_AND_DECISIONS.md. Update contracts or file maps only when the implemented change requires it. Record any assumption or justified deviation.

Finish with the completed task, observable behavior, files changed, actual checks and evidence, remaining limitations, retired files, and the next ready task. Completion requires every acceptance item to pass. A blocked task stays open with a concrete dependency and recovery action.

---

For a later multi-task session, the user can append a specific stopping condition such as “Continue through F04, completing and documenting each task separately.” The default remains one task.


Before starting, read `video_game/AGENTS.md` and the latest audit linked in CURRENT_STATE.md. Prior progress entries and generated scorecards can overstate completion. Verify actual normal-key callers, scene entry, SaveStore persistence and New/Continue isolation. Keep G2/G3 pending until their recorded manual/visual/audio/performance acceptance is satisfied. The user allows unavailable live AI to be skipped; focus on offline functionality. Use actual measured output, not hardcoded chart labels, for evidence.
