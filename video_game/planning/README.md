# 6EQUJ5 execution plan

Updated 2026-11-10. Start here for every implementation session.

This plan takes the existing Pygame art preview through a complete five-act game. Work advances through small, verified tasks. A single task is the default unit for one LLM session.

## Reading order

1. [CURRENT_STATE.md](CURRENT_STATE.md) records the next task and observed implementation.
2. [EXECUTION_PROTOCOL.md](EXECUTION_PROTOCOL.md) defines how to execute and report one task.
3. [TODO_ROADMAP.md](TODO_ROADMAP.md) owns task status, dependencies, and milestone gates.
4. Open the task's milestone document and the contracts it references.
5. [CODE_STANDARDS_AND_MAP.md](CODE_STANDARDS_AND_MAP.md) owns file responsibilities and migrations.
6. [QUALITY_GATES.md](QUALITY_GATES.md) defines acceptance evidence.
7. [ISSUES_AND_DECISIONS.md](ISSUES_AND_DECISIONS.md) owns unresolved issues and explicit design defaults.
8. [PROGRESS_LOG.md](PROGRESS_LOG.md) records completed attempts and handoffs.

Use [LLM_EXECUTION_PROMPT.md](LLM_EXECUTION_PROMPT.md) to start another LLM.

## Document ownership

| Document | Owns |
|---|---|
| [Video_game_planning.md](Video_game_planning.md) | Story, characters, visual references, aspirational design |
| [CODE_STANDARDS_AND_MAP.md](CODE_STANDARDS_AND_MAP.md) | Target folders, module responsibilities, migration order |
| [DATA_CONTRACTS.md](DATA_CONTRACTS.md) | State, events, manifests, save and content formats |
| [ART_PRODUCTION.md](ART_PRODUCTION.md) | Asset production steps and visual acceptance |
| [CONTENT_PLAN.md](CONTENT_PLAN.md) | Rooms, civilization rewards, bosses, endings, scope coverage |
| [QUALITY_GATES.md](QUALITY_GATES.md) | Test commands, playthroughs, measured acceptance criteria |
| [TODO_ROADMAP.md](TODO_ROADMAP.md) | The authoritative task status table |
| milestone files | Exact implementation actions and task-specific checks |
| [CURRENT_STATE.md](CURRENT_STATE.md) | Short current handoff with evidence links |
| [PROGRESS_LOG.md](PROGRESS_LOG.md) | Append-only work history |
| [ISSUES_AND_DECISIONS.md](ISSUES_AND_DECISIONS.md) | Problems, compute needs, and recorded decisions |

The execution documents govern implementation order and architecture. The design bible supplies creative intent. Its earlier schedules, engine alternatives, directory examples, and statements that artwork is production-ready are historical context. Resolve genuine changes to scope in the decision log before changing task acceptance criteria.

All paths in file maps and task cards are relative to the repository root `/Users/nzlab-la/Desktop/Github/6EQUJ5`, unless a table explicitly says they are relative to `video_game/`. This convention keeps implementation instructions portable.

## Completion target

The first full release is a single-player macOS build with five connected acts, eleven civilization arcs, four science workbenches, five sector bosses, both timeline mechanics, the 72-second defense, save/load, endings, settings, sound, and reviewed pixel art. Both curated offline dialogue and local Ollama dialogue must support progression. Windows and Linux remain separately tracked port targets until exercised on their actual platforms.

Four authored rooms per act, three endings, and macOS-first packaging are provisional scope decisions introduced by this plan. Their definitions and rationale are in the decision log. The full design feature coverage is in CONTENT_PLAN.md.

Create future files only when their task begins. The target tree documents destinations without requiring empty folders or placeholder modules today.
