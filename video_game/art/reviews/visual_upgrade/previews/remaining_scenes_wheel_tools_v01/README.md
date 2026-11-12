# Remaining-scene wheel verification wrapper

Prepared for execution only after the parent confirms the complete integration is stable. This tool has not itself established a wheel result. From the repository root use a new output directory:

```sh
/opt/anaconda3/envs/6equj5_game/bin/python video_game/art/reviews/visual_upgrade/previews/remaining_scenes_wheel_tools_v01/check.py --output-dir video_game/art/reviews/visual_upgrade/previews/remaining_scenes_wheel_check_v01 --require-family ohio_approach_v1 --require-family ohio_approach_v2 --require-family ohio_salvage_v1 --require-family ohio_dish_v1 --require-family ohio_arena_v1 --require-family ohio_bunker_v1
```

Add `--require-family mandela_annex_v1`, `--require-family dodleston_relay_v1` and/or `--require-family ehman_1977_v1` only for families actually approved and installed by that checkpoint. Every other allowlisted family present is inspected and smoked even when not required. Missing optional families are explicitly reported; a partial present family fails. The fresh output directory stores each subprocess argv, cwd, relevant environment, exit code, stdout and stderr, plus wheel SHA-256, all verified packaged family file hashes and member count. The temporary copy, wheel and installed target remain under the recorded temporary root.

The copy omits game tests, art, planning, `_trash`, `_temp`, bytecode and build artifacts. Wheel inspection rejects excluded folders and verifies each allowlisted present family's manifest-referenced component hash against the copied source and wheel bytes. Isolated Python (`-I`) runs outside the checkout, explicitly imports the installed target, validates the actual installed family loaders, runs two dummy-driver game frames and directly enters/renders each installed scene. Scene transitions and positions here are fixtures; the tool does not prove normal-input progression, complete art or motion, native-window performance, audible output, human review or a milestone gate. The recorded environment includes only relevant values, not the user's entire environment.
