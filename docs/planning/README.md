# Development plan

The current scope is five Earth acts, eleven signal worlds and a return to Earth. The game is offline; live-model integration belongs to the separate legacy application.

Start with [current state](CURRENT_STATE.md), the [roadmap](TODO_ROADMAP.md) and the task's milestone card. [CONTRIBUTING.md](../CONTRIBUTING.md) contains setup, coding conventions and verification commands.

## Document ownership

| Document | Purpose |
|---|---|
| [CURRENT_STATE.md](CURRENT_STATE.md) | Current implementation and verification limits |
| [TODO_ROADMAP.md](TODO_ROADMAP.md) | Task status, dependencies and acceptance gates |
| [CODE_STANDARDS_AND_MAP.md](CODE_STANDARDS_AND_MAP.md) | Current file responsibilities |
| [DATA_CONTRACTS.md](DATA_CONTRACTS.md) | State, events, saves, manifests and content formats |
| [ART_PRODUCTION.md](ART_PRODUCTION.md) | Visual direction and asset production |
| [CONTENT_PLAN.md](CONTENT_PLAN.md) | Rooms, civilization rewards, bosses and story scope |
| [QUALITY_GATES.md](QUALITY_GATES.md) | Acceptance criteria and evidence requirements |
| [EXECUTION_PROTOCOL.md](EXECUTION_PROTOCOL.md) | Task workflow and restoration procedure |
| [ISSUES_AND_DECISIONS.md](ISSUES_AND_DECISIONS.md) | Open issues and design decisions |
| [PROGRESS_LOG.md](PROGRESS_LOG.md) | Historical work records |
| [milestones/](milestones/) | Task-specific requirements |

Older plans describe the former combined repository, live AI and proposed modules that may not exist. Use the current code, [architecture](../ARCHITECTURE.md) and separation record to resolve those differences. Historical reports do not establish current test results.

Paths in current documentation are relative to this repository unless stated otherwise. Archived `video_game/` paths refer to the layout before separation; use the [archive manifest](../maintenance/archive-manifest.json) to locate preserved material.

Implemented features still require their stated gameplay, art, audio and native-performance checks before a release is accepted. Windows and Linux support remains unverified until exercised on those platforms.
