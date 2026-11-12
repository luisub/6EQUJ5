# F02 checkpoint and preview evidence

Date: 2026-11-10, America/Denver. Environment: macOS arm64; `/opt/anaconda3/envs/6equj5_game/bin/python` 3.12.16; pygame-ce 2.5.8, SDL 2.32.10, pytest 9.2.0. Tests and captures used dummy SDL video and audio, not a real display or audio device.

## Outcome and changed files

The checkpoint discovers active Python modules without a registry or line limit, parses their syntax, checks purpose/caller/modification module headers and rejects wildcard imports. Its asset checks follow the actual civilization and bunker manifest references, confirm current locks and dimensions, and retain checks for other established artwork. A temporary 230-line scene fixture passes the audit without registration; a wildcard import in that same fixture fails it. Scene rendering and main-loop smoke tests remain in place.

`video_game/tests/test_engine_boot.py` exports previews to pytest's temporary directory and verifies the files and dimensions. The new `video_game/engine/preview_assets.py` exports the same bunker and terminal renders through the game scene and renderer to an explicitly selected directory. Its temporary location and maintenance/recovery guidance are documented in `planning/QUALITY_GATES.md` and the file map. The roadmap, handoff, progress and issue records are updated.

## Checks and results

Working directory: `/Users/nzlab-la/Desktop/Github/6EQUJ5`.

```sh
/opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests -q
# 7 passed in 0.92s
/opt/anaconda3/envs/6equj5_game/bin/python -m pytest tests -q
# 20 passed in 0.01s
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m video_game.engine.preview_assets --output-dir video_game/planning/evidence/F02/2026-11-10_checkpoint/previews
# Exit 0, three PNG paths printed.
```

Before tests, SHA-256 hashes of all 122 files under `video_game/assets/` were saved in [assets_before.sha256](assets_before.sha256). After both suites and the deliberate preview, recalculating the sorted paths and hashes produced an exact match: 122 files, no additions, removals, or changed hashes. Hash verification command:

```sh
/opt/anaconda3/envs/6equj5_game/bin/python -c 'import hashlib,pathlib; root=pathlib.Path("video_game/assets"); files=sorted(p for p in root.rglob("*") if p.is_file()); actual="".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.as_posix()}\n" for p in files); expected=pathlib.Path("video_game/planning/evidence/F02/2026-11-10_checkpoint/assets_before.sha256").read_text(); print(f"Asset hashes unchanged: {actual == expected} ({len(files)} files)"); raise SystemExit(0 if actual == expected else 1)'
# Asset hashes unchanged: True (122 files)
```

## Visual inspection

Inspected [native bunker](previews/pygame_live_480x270_crt_off.png), [3× CRT bunker](previews/pygame_live_1440x810_crt_on.png), and [3× CRT terminal](previews/pygame_live_crt_terminal.png). The bunker shows the centered character, equipment, green screens and both HUD strips; the scaled version has scanlines and preserves the composition. The terminal shows portrait, constellation chart, telemetry and exit prompt. The existing `30s` label remains incorrect and is tracked as I10 for C04. Captures intentionally match the former smoke-test timeline after its toggle to 1977. These captures do not establish motion, input usability or final art acceptance.

## Failures, limitations and cleanup

No test or preview execution failed. The initial inspection confirmed that `engine/preview_assets.py` did not yet exist; it was created as specified. The game folder remains untracked, so Git cannot restore it. No files were retired, moved or deleted; no asset builders were run. Before future replacement or retirement, create and verify recovery copies with original paths and hashes. A durable whole-directory backup/version-control choice remains open as I11. No real-window input, audio, GPU, performance or live Ollama testing was performed; these are outside F02. Pytest owns its temporary files. Only the hash inventory, this report and intentional screenshots were retained as evidence.
