# F07 focused input, pause and settings evidence

Date 2026-11-10, America/Denver. Environment: macOS arm64; Python 3.12.16 from `/opt/anaconda3/envs/6equj5_game`, pygame-ce 2.5.8, pytest 9.2.0. Rendering and keyboard events used dummy SDL video/audio (`SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`). Every save and settings write used for testing and visual capture lived in an isolated temporary directory; no real user data was accessed or modified.

## Outcome

Implemented focused action mapping, pause overlay, atomic settings persistence, window focus/resize handling, and development control gating.

1. **InputManager (`engine/input.py`)**:
   - Maps physical keys to actions with pressed, held and released edge semantics.
   - Handles multi-key bindings (e.g. `move_left` bound to both `A` and `Left Arrow`; releasing one while the other is held maintains held state without false release edges).
   - `begin_frame()` clears single-frame edge triggers (`pressed`, `released`).
   - `release_all()` releases all held actions immediately, clearing all key states.

2. **Settings and Persistence (`engine/settings.py`)**:
   - `Settings` dataclass stores `volume` (0–100%), `crt_effects` (bool), and integer window `scale` (1×–4×), default `Settings(volume=70, crt_effects=True, scale=3)`.
   - `SettingsStore` loads and validates schema version 1 from `settings.json` in the user data directory. Invalid schema versions or invalid types/ranges fall back to defaults safely without overwriting the user's file on read.
   - `save()` writes through a unique temporary sibling file (`.settings.*.tmp`), flushes and fsyncs the descriptor, verifies the staged JSON on disk, and replaces the target file atomically via `os.replace()`. A failed replacement preserves the prior file intact.

3. **Pause Overlay (`engine/ui/pause.py`)**:
   - Presented via `Esc` (in the bunker) or `F2` (globally, including terminal).
   - Freezes simulation game time (`update` is bypassed for scenes and CRT timers).
   - Allows keyboard navigation (Up/Down select, Left/Right/Enter adjust, Esc/F2 resume).
   - Adjusts volume, toggles CRT effects, adjusts integer window scale (1×–4×), and triggers manual checkpoint saves with on-screen confirmation notices.
   - Closing the overlay releases all held inputs, preventing stuck movement.

4. **Focus Loss, Resize, and Terminal Text Isolation (`engine/state_machine.py`, `main.py`, `engine/scenes/terminal.py`)**:
   - Focus loss (`WINDOWFOCUSLOST`, `WINDOWMINIMIZED`, legacy `ACTIVEEVENT` with focus gain=0) immediately releases all held keys and opens the pause overlay (outside the title scene).
   - Window resize (`VIDEORESIZE`, `WINDOWRESIZED`, `WINDOWSIZECHANGED`) calculates the maximum fitting integer scale (1×–4×), updates settings, and releases held inputs to prevent stuck movement.
   - `CRTTerminalScene` starts text input on enter and stops on exit/pause. `TEXTINPUT` events append printable characters to `text_buffer` without triggering gameplay actions (movement, jump, fire).
   - Bunker inspection shortcuts (`C` civilization, `O` outfit, `V` inspect view, `Q` timeline) and direct scene jump keys (`L`, `F`, `B`) are gated behind `--dev` (`machine.development=True`). Normal mode exposes only movement, receiver entry (`E`), CRT toggle (`F1`), save (`F5`), and pause (`Esc`/`F2`).

Changed `video_game/main.py`, `video_game/engine/state_machine.py`, `video_game/engine/crt_renderer.py`, `video_game/engine/preview_assets.py`, `video_game/engine/scenes/bunker.py`, `video_game/engine/scenes/terminal.py`, `video_game/tests/test_engine_boot.py`, `video_game/tests/test_save_game.py`, and `video_game/README.md`. Added `video_game/engine/input.py`, `video_game/engine/settings.py`, `video_game/engine/ui/pause.py`, and `video_game/tests/test_input_settings.py`. Pre-change recovery copies for 21 files are archived in `video_game/_trash/2026-11-10_F07_before_changes.tar.gz`.

## Checks and results

Working directory `/Users/nzlab-la/Desktop/Github/6EQUJ5`:

```sh
/opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests -q
# 85 passed in 4.67s

/opt/anaconda3/envs/6equj5_game/bin/python -m pytest tests -q
# 20 passed in 0.01s

/opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_input_settings.py -q
# 15 passed in 1.08s
```

The 15 focused tests in `video_game/tests/test_input_settings.py` cover:
- Edge tracking and multi-key binding overlap resolution (`test_action_edges_and_multiple_physical_keys`).
- Pause freezes game time, simulation position, animation, and glitch timers, and does not restore stale keys upon resume (`test_pause_freezes_time_and_does_not_restore_stale_keys`).
- Terminal typing isolation and pause overlay prevent movement or weapon firing (`test_terminal_typing_and_pause_do_not_move_or_fire`).
- Focus loss, minimization, resize, and quit release all held inputs (`test_focus_resize_and_quit_release_held_inputs`, `test_legacy_focus_loss_clears_input_and_pauses`).
- Pause settings adjustment and persistence across separate process restart (`test_pause_settings_apply_and_persist_after_restart`).
- Invalid settings fallback, non-destructive reads of broken files, and failed atomic replacement rollback (`test_invalid_settings_fallback_and_failed_write_preserves_previous`).
- Window resize dynamically updating integer scale and releasing input (`test_resize_event_updates_integer_scale_and_releases_input`).
- Normal vs development control separation (`test_normal_and_development_controls_are_separate`).
- CLI `--dev` flag argument parsing and passing (`test_game_launch_receives_explicit_development_mode`).

### Visual inspection of captured previews

Inspected 10 preview captures in `previews/`:

| Preview | Resolution | Description |
|---|---|---|
| [normal_bunker_native.png](previews/normal_bunker_native.png) | 480×270 | Normal bunker view; footer displays `[A/D] MOVE  [E] CRT  [F5] SAVE  [ESC] PAUSE` without dev shortcuts |
| [normal_bunker_3x.png](previews/normal_bunker_3x.png) | 1440×810 | Normal bunker view with 3× integer scaling and active CRT scanlines |
| [development_bunker_native.png](previews/development_bunker_native.png) | 480×270 | Development bunker view; displays dev shortcuts `[C] CIV [O] OUTFIT [V] INSPECT [Q] TIMELINE` and scene shortcuts |
| [development_bunker_3x.png](previews/development_bunker_3x.png) | 1440×810 | Development bunker view at 3× scale with CRT effects |
| [pause_native.png](previews/pause_native.png) | 480×270 | Pause overlay; displays menu options RESUME, VOLUME: 70%, CRT EFFECTS: ON, WINDOW SCALE: 3X, SAVE CHECKPOINT |
| [pause_3x.png](previews/pause_3x.png) | 1440×810 | Pause overlay at 3× integer scale with CRT postprocessing |
| [settings_native.png](previews/settings_native.png) | 480×270 | Pause menu after volume and scale adjustment at native resolution |
| [settings_2x.png](previews/settings_2x.png) | 960×540 | Pause menu after 2× window scaling adjustment |
| [terminal_native.png](previews/terminal_native.png) | 480×270 | CRT Receiver terminal showing text input buffer without affecting player movement |
| [terminal_3x.png](previews/terminal_3x.png) | 1440×810 | CRT Receiver terminal at 3× scale showing astronomical & telemetry monitors |

### Asset inventory and recovery verification

- SHA-256 hashes of all 122 active asset files were verified against the baseline inventory `video_game/planning/evidence/F02/2026-11-10_checkpoint/assets_before.sha256`; all 122 files remain untouched.
- Archive `video_game/_trash/2026-11-10_F07_before_changes.tar.gz` (SHA-256 `a120d5bc20c39137c144ca11373ea37ebac19dc04333eb681d20852172ffedfe`) was verified against all 21 member hashes in its manifest.

## Limits

- Controller mappings and analog sticks remain scheduled for R02; current input is keyboard-only.
- Audio playback and mixer initialization are guarded, but full audio assets and sound channels remain scheduled for A12.
- Testing used dummy video and audio drivers (`SDL_VIDEODRIVER=dummy`, `SDL_AUDIODRIVER=dummy`); real display performance, sustained frame pacing, and live Ollama streaming remain unverified.
- I11 (untracked workspace), I12 (non-macOS builder lock/recovery), and I13 (save power loss and concurrent save instances) remain open.

