# Repository transfer completed — 2026-11-13

The prepared repositories are installed at their final locations. Both isolated Python 3.12 environments were recreated there. Runtime source, assets, tests and packaging configuration were unchanged during this transfer. No commit, push, model download or model-service startup was performed.

| Project | Final path | HEAD |
|---|---|---|
| Offline game | `/Users/nzlab-la/Desktop/Github/6EQUJ5` | `a43c2b343f62150b74d57df8ae83676f8f2ccb92` |
| Historical AI terminal | `/Users/nzlab-la/Desktop/Github/6EQUJ5-AI` | `120c39b604bca5a4a9dfef4d34b131b6751da0f9` |

Both `origin` remotes remain `https://github.com/luisub/<repository-name>.git`. Git object checks passed, object alternates are absent, and the prepared staged changes remain available for review. The completion documentation is left unstaged.

## Preserved originals

- Complete original game, including its uncommitted work and Git metadata: `/Users/nzlab-la/Desktop/Github/6EQUJ5.before-separation-20261113T180135Z`. All 14,147 original files were checked against the recovery inventory after moving.
- Original empty AI Git metadata: `/Users/nzlab-la/Desktop/Github/6EQUJ5-AI/.migration-recovery/original-git-transfer-20261113T180135Z/.git`; verified against its original inventory.
- Full pre-separation recovery snapshot remains at `/Users/nzlab-la/Desktop/Github/6EQUJ5-AI/.migration-recovery/20261113T164851Z`. Its repository snapshots, saved-player-data copies and artifact checksums passed verification before transfer.
- Each old staging environment is retained in that repository's `_trash/staging-environment-20261113`. The adjacent `staging-environment-20261113-manifest.json` records every archived file hash and symlink target.

Retain these backups until independently deciding they are no longer needed. Do not rerun the old move instructions over the completed repositories.

## Environments and launch

Package-index access failed in this session. Installation instead used the existing local dependency wheel cache, local Setuptools, and locally repacked `build`/`pyproject_hooks` distributions. Shared environments were not modified. Both complete development extras are installed and `pip check` passes. Provenance is recorded in `6EQUJ5-AI/__move/verification/transfer-bootstrap-provenance.json`.

```bash
# Game
/Users/nzlab-la/Desktop/Github/6EQUJ5/.venv/bin/6equj5-game

# Legacy terminal; live dialogue requires a separately configured model service
/Users/nzlab-la/Desktop/Github/6EQUJ5-AI/.venv/bin/6equj5
```

The game retains the flat `src/` layout, mapped to the `video_game` import. Imports resolve to the final checkouts. The game environment contains neither Ollama nor `signal_6EQUJ5`; the AI environment does not import `video_game`.

## Validation at final locations

| Check | Result |
|---|---|
| Full game suite | 1,184 passed, 2 known failures; 175.52 seconds |
| Missing legacy portrait input | Existing failure: `_trash/legacy_ascii_portraits/fasr-001_legacy_face.png` |
| Scene render budget | Existing failure: FIELD_OPS P95 5.323 ms against the unchanged 5.0 ms limit |
| Full legacy AI suite | 22 passed |
| Authored levels | All 52 valid |
| Protected asset dry run | All 14 locked groups preserved |
| Game startup outside checkout | Three rendered frames with socket connections blocked; console `--help` passed |
| Legacy launch paths outside checkout | Console script and module startup, HELP and EXIT passed with a fake model client and socket connections blocked |
| Historical AI fidelity | All 43 original source/data/test files match baseline Git blobs |
| Git integrity | Both `git fsck --full` checks passed; expected histories and remotes retained |

Game tests and rendering used dummy SDL video/audio drivers and isolated temporary save directories. Live model responses, native-window performance, physical controllers and audible playback were not validated. No gameplay gate is promoted by these checks.

Exact commands, outcomes, logs, startup-harness details and integrity results are retained in `/Users/nzlab-la/Desktop/Github/6EQUJ5-AI/__move/verification/final-location-20261113T180135Z/`. The move journal is the adjacent `transfer-20261113T180135Z.json`.
