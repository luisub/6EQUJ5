# F01 baseline report

Date 2026-11-10, America/Denver.

## Environment

macOS arm64, Python 3.12.16, pygame-ce 2.5.8, Pillow 13.0.0, NumPy 2.5.4, Ollama Python package 0.6.3, pytest 9.2.0. These are observed installed versions. Availability of the Ollama service or model was not tested.

## Executed checkpoint

Working directory `/Users/nzlab-la/Desktop/Github/6EQUJ5`.

```sh
/opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests tests -q
```

Result `29 passed in 0.54s` with exit code 0. The suite uses dummy SDL display and audio. This establishes existing assertions and smoke rendering only.

## Inspected code and images

Reviewed scene routing, asset loading, alpha masking, rebuild lock handling, package configuration, imports hub, and audit assumptions. Viewed the native bunker image and full civilization roster. The bunker and portraits are integrated visual candidates. Animation fluency, combat readability, and artistic acceptance across all civilizations remain open.

## Concrete findings

- `build_assets.py` invokes `build_civilization_assets(force_overwrite=True)` as its normal module entry point.
- Chart exports and the manifest are rewritten outside the existing face lock condition.
- `_load_surf` is called during terminal and inspector rendering, causing repeated disk loads.
- Bunker layer masks encode inactive context with alpha 254, and the runtime masks alpha below 255.
- The structural audit enforces a hard 220-line maximum and a manually maintained file allowlist.
- Tests export three screenshots into runtime assets.
- Current campaign defaults pregrant a fragment and validation.
- The root package configuration discovers `src` packages only and omits graphical game dependencies/resources.
- `_trash/TRASH_LOG.md` refers to `_trash/concepts/`, while live builders read `assets/concepts/`.
- Terminal text includes `6 E Q U J 5 (30s)`. The signal duration in the game contract is 72 seconds and peak intensity is 30 sigma.

## Side effects and limits

The existing test suite refreshed `pygame_live_480x270_crt_off.png`, `pygame_live_1440x810_crt_on.png`, and `pygame_live_crt_terminal.png` under `video_game/assets/bunker/`. No live keyboard/controller session, AI model run, performance benchmark, or packaging test was performed.

## Planning integrity verification

The final documentation validator passed 66 unique task IDs, dependency ordering without cycles, exactly one task card per ID, complete roadmap coverage, and existing local document links. All five archived-document hashes match their recorded SHA-256 values. The six milestones contain 8, 8, 14, 11, 17 and 8 tasks respectively. Direct task-card anchors were checked after adding them.

The planning folder contains 20 Markdown files including the retained design bible and baseline evidence. The previous architecture/schedule sections now link to their canonical execution documents. The maintenance workflow points to this plan. No game-runtime Python source was edited during this task.
