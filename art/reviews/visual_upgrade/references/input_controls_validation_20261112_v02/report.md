# Pointer/controller mapper — revised contract check

2026-11-12. Owned `video_game/engine/input.py` and new `video_game/tests/test_pointer_controller_input.py`. The pre-work source backup is `references/input_controls_backup_20261112_v01/input.py.bak` SHA-256 `22162d1c5a692bee8e4660de186a73bee61ea81e2f074d9337f3078d11a7e283`. Before the final mapping revision, byte-compared copies were saved in `references/input_controls_backup_20261112_v02/`: source SHA-256 `7be3145113fe62e7c7d6d8e123f8ef0870633463dad7352026f0b61fe4a2eb7f`, tests SHA-256 `83c882e5d135c3190d8f4eaae062fda7e9961db7b847fedf9c1176e69efe1f9a`.

Desktop left mouse and SDL-mapped right trigger provide `auto_fire`; existing keyboard charge, right mouse and left trigger use `fire`. The mapper exposes `mouse_position`, `controller_aim`, `aim_source`, `charge_reset_generation`, `invalidate_charge()`, and `initialize_controllers()` / `close_controllers()`. Keyboard and mouse are one desktop input group. Controller handoff, disconnect, remap, and explicit invalidation increment the generation; removal/remap suppress a synthetic fire-release, and `release_all` clears held/edge/aim state. Callers must cancel active charge on generation changes and prevent a still-held previous input from silently recharging until neutralized. Full mappings are in the module; raw joystick events are not consumed.

From repository root:

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_pointer_controller_input.py -q
```

Exit 0: `10 passed in 0.12s`. Tests use Pygame event objects and mocked controller enumeration, covering multi-source aggregation, positive and negative signed SDL axis values, deadzone, duplicate event delivery, mouse charge, controller mapping, disconnect/remap, desktop/controller handoff, focus reset and device closure. Real controller hardware and device mapping remain unverified.

During concurrent settings implementation, the broader mapper/settings invocation below exited 1 with `22 passed, 1 failed in 2.26s`; the failure was `test_invalid_settings_fallback_and_failed_write_preserves_previous`: invalid settings loaded `combat_mode='classic'` while the concurrently modified `Settings()` default was `assisted`. Technical owner was notified to reconcile the intended settings behavior and rerun after integration stabilizes.

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_pointer_controller_input.py video_game/tests/test_input_settings.py -q
```

Mapper tests alone do not prove actual device behavior, menu navigation, pointer-to-world aim, auto-repeat cadence, charge-cancellation caller behavior, pause, focus handling end to end, native-window use, human play or R01/R02 acceptance. Caller, settings and combat integration are separately owned and in progress.
