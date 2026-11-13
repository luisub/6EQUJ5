# Repository separation completed

The game is now at `/Users/nzlab-la/Desktop/Github/6EQUJ5` and the historical application at `/Users/nzlab-la/Desktop/Github/6EQUJ5-AI`. Both environments were recreated and validated after transfer on 2026-11-13. See [completed transfer](TRANSFER_COMPLETE.md) for the final-location results, preserved originals and launch commands. The remainder of this report records the earlier preparation and installed-wheel validation; references below to preparation or a future transfer are historical.

## Layout and entry points

| Game path | Contents |
|---|---|
| src/ | __init__.py, main.py, engine/, assets/, data/ |
| tests/ | Functional, persistence, input, content and regression tests |
| tools/ | Maintained validation, art builders, capture and profiling utilities |
| docs/ | Controls, architecture, current planning and migration records |
| art/ | Unique rebuild masters, provenance and necessary review inputs |
| _trash/ | Ignored obsolete implementations, captures, backups and retired tools |
| .venv/ | Ignored isolated development environment; recreate after moving |

The user-requested flat `src/` folder is explicitly mapped to the installed package `video_game`. There is no `src/video_game` intermediate directory. `6equj5-game` and `python -m video_game.main` retain their behavior. Runtime resources are included beside the installed package. Developer tools are run from the repository and are excluded from runtime wheels.

The AI repository retains `src/signal_6EQUJ5`, tests, tools, docs, its own pyproject and its own isolated environment. Its command remains `6equj5`, and its distribution is `6equj5-ai`. Both actual directory inventories are in each repository's `docs/migration/directory-tree.json`.

## History and preservation

Legacy baseline: **120c39b604bca5a4a9dfef4d34b131b6751da0f9**. Its Git tree is `7c08d4a3992318b4443482c1e0786d763f3a06da`, with 30 reachable commits. The AI repository uses independent objects and the AI remote. All 42 historical source/data files and the original test file match baseline blobs byte for byte. Later changes to `.gitignore`, `pyproject.toml` and `src/signal_6EQUJ5/ai_engine.py` are preserved as separate reviewable patches and were not applied to the baseline.

The game's branch remains at **a43c2b343f62150b74d57df8ae83676f8f2ccb92**, exactly one commit after the requested baseline. Its source was the full current working tree, with 61 modified tracked files, no staged edits, 5,089 untracked files and 2,559 ignored files. All **10,582 working-tree files** are mapped in `migration-manifest.json`, with no missing files. Original Git history and index are separately recoverable.

All **462 runtime data and asset files** are byte-for-byte preserved. The intro-map, temporary weapons, combat effects, input, campaign and save code remain unchanged. The only existing engine files changed for separation are config, contact_session, the terminal scene and state_machine; AI adapter/worker modules were archived and a small local codec was added. The normal authored receiver was already workerless and unlimited; that behavior is retained. Direct legacy developer commands `/reconnect`, `/offline` and `/restart` are no longer part of ContactSession; the normal button-driven receiver did not expose typed commands.

The preserved mechanics include Arc Lance/Nova Scatter, their pause/focus/expiry/reset behavior, mapped intro navigation, eleven-world dialogue/progression, science and save version 2. Tests still exercise New/Continue, compatibility and real temporary save roundtrips. No game runtime imports, symlinks or resource paths point into the AI repository.

## Archives and recovery

`archive-manifest.json` contains **9,369 archive entries** with original/archive paths, reasons, SHA-256 hashes and restoration instructions. Every recorded archived file was hash-checked. Preexisting archive logs remain intact; `_trash/SEPARATION_LOG.md` links the consolidated records. Historical captures, redundant document snapshots, retired static presentation generators, obsolete live-model game code and the current legacy/shared tree are retained in ignored `_trash` locations. All unique art masters and necessary rebuild/test inputs remain locally available. Civilization rebuild text is copied into game-owned `art/source/civilizations`.

Full original recovery stays at `/Users/nzlab-la/Desktop/Github/6EQUJ5-AI/.migration-recovery/20261113T164851Z`: filesystem snapshots, verified Git bundle, raw index, separate binary patches, ignored/untracked inventories and external player-save copies. `verify-recovery.py` rechecks it; `RECOVERY.md` gives restoration instructions. Restore into a new directory before considering replacement of any current work. The original game and index were checked again at the end; `__move/verification/original-source-final.json` records no changed or added files.

## Dependencies

| Project | Runtime | Development / optional tools |
|---|---|---|
| Game, distribution 6equj5-game | Python >=3.12; pygame-ce >=2.5.0; Pillow >=10.0.0; NumPy >=1.24.0 | pytest >=8; setuptools >=77; wheel |
| Legacy, distribution 6equj5-ai | Python >=3.8; ollama >=0.4 | pytest >=7; build >=1; optional Pillow >=9 for image utility |

Validation used Python 3.12.16 on this Mac. The game environment contains no Ollama SDK or legacy application. A clean installed-wheel smoke blocks network sockets and forbidden AI imports and boots and renders three frames outside both repositories. Live-model CLI output, other Python/platform versions, native display performance, physical controllers and audible playback were not validated.

Dependencies for the local isolated validation environments were reconstructed from installed local distributions, without changing shared/global packages. This is an offline local separation check; a fresh public-index download was not tested. Each `.venv` must be recreated after its repository is moved because venv scripts contain absolute paths.

## Validation

| Check | Result |
|---|---|
| Installed game, full suite outside both repositories | **1,184 passed, 2 failed**, 177.40 seconds |
| Remaining game failures | Missing historical FASR-001 portrait rebuild input; FIELD_OPS render P95 **5.068 ms** versus unchanged **5.0 ms** limit |
| Authored content validation | **52 / 52 levels** |
| Protected asset dry run | **14 / 14 locked groups preserved** |
| Legacy installed-wheel suite | **22 passed** |
| Legacy startup | Both CLI entry points, HELP/EXIT and mocked AI integration passed |
| No-model game smoke | Clean noneditable installed wheel, no AI packages, sockets blocked, 3 rendered frames; passed |

No migration regressions remain in the final installed full run. The two remaining failures were present before separation. Test counts differ because the legacy codec suite belongs to the AI repository and game live-worker tests were archived; all active game tests ran without deselection.

The full original baseline was 1,212 passed, 2 failed, 2 named live tests excluded. Game live-worker tests were archived with their implementation; authored tests and assertions were retained or replaced with direct authored-path coverage. `test-disposition.json` records the changed test names. The old streaming profiler was replaced by repeated authored exchanges/scene reentry; one-time caches are warmed before measuring repeated growth, and both memory limits are unchanged.

An initial outside-checkout test run exposed cwd-relative test fixture paths. Those were changed to installed runtime data/assets or explicit repository paths for rebuild fixtures; assertions were retained. The final run uses the real installed wheel with no editable game import. Full command, working directory and environment are recorded in `verification/installed-final-v2.json`. A clean rebuild produced identical runtime payload; the final wheel was reinstalled and all 63 focused offline/intro/temporary-weapon/save checks passed. The final AI wheel was also reinstalled and its 22 tests passed again.

Prepared changes are staged for review, with no commit or push. Whitespace diagnostics in `verification/whitespace.txt` reflect preserved user source/data and captured patches/transcripts; those bytes were retained.

Build audit: the wheel contains 541 members, including all 462 runtime resource files verified in both directions. Tests, tools, art masters, docs, caches, archives and legacy AI modules are excluded. Exact wheel hashes, payload comparison and source-distribution results are in `verification/`.

## Setup, launch and checks

After transfer, recreate each old `.venv` as described in the manual instructions. In the game repository:

```bash
/opt/anaconda3/envs/6equj5_game/bin/python -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/6equj5-game
# Alternative: .venv/bin/python -m video_game.main
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy SIX_GAME_SAVE_DIR="$(mktemp -d)" .venv/bin/python -m pytest tests -q
.venv/bin/python -m tools.validate_content
.venv/bin/python -m tools.build_assets --dry-run
.venv/bin/python -m pip wheel --no-deps . -w dist
.venv/bin/python -c "from setuptools.build_meta import build_sdist; print(build_sdist('dist'))"
```

In the AI repository:

```bash
/opt/anaconda3/envs/6equj5_game/bin/python -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/6equj5
# Alternative: .venv/bin/python -m signal_6EQUJ5
.venv/bin/python -m pytest tests -q
.venv/bin/python -m build
```

The AI README explains live-model configuration for optional future use. No model was downloaded or started for this task. Review the prepared Git changes and remotes before making your own commit or push.
