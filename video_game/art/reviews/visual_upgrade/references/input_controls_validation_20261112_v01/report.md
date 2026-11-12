# Pointer and controller mapper — initial focused check

2026-11-12. Ownership: `video_game/engine/input.py` and new `video_game/tests/test_pointer_controller_input.py`; caller integration, combat cadence and settings are separately owned and remain in progress. Pre-edit `input.py` was copied and byte-compared at `references/input_controls_backup_20261112_v01/input.py.bak`; SHA-256 `22162d1c5a692bee8e4660de186a73bee61ea81e2f074d9337f3078d11a7e283`.

From repository root:

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_pointer_controller_input.py video_game/tests/test_input_settings.py -q
```

Exit 0; observed output `20 passed in 2.28s`. These tests use Pygame event objects, mock mapped-controller enumeration, and existing dummy-driver scene/focus tests. They exercise multiple physical sources for one action, duplicate event delivery, mouse/keyboard separation, stick deadzone and aim-source handoff, disconnect preserving other held sources, neutralization without firing a charged-release edge, duplicate connect and close. They do not establish real controller hardware, OS mapping, mouse-to-world gameplay aim, combat repeat cadence, menu navigation or a playable end-to-end device route. Those depend on caller/combat integration and remain to be checked after the shared implementation is stable.

The mapper maintains keyboard `fire` edges for existing charge; mouse left and standard mapped right trigger use separate `auto_fire` intent. It exposes window-pixel `mouse_position`, dead-zoned unit `controller_aim`, and `aim_source` (`mouse`, `controller`, or None). SDL-mapped controllers are opened/closed through `initialize_controllers` and `close_controllers`; no raw joystick fallback or physical device acceptance is asserted. Device-to-action mapping is in `engine/input.py` and is provisional pending integrated input review.
