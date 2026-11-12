# Final remaining-scene clean-wheel check

2026-11-12. From the repository root, the following command exited 0:

```sh
/opt/anaconda3/envs/6equj5_game/bin/python video_game/art/reviews/visual_upgrade/previews/remaining_scenes_wheel_tools_v01/check.py --output-dir video_game/art/reviews/visual_upgrade/previews/remaining_scenes_wheel_check_v01 --require-family ohio_approach_v1 --require-family ohio_approach_v2 --require-family ohio_salvage_v1 --require-family ohio_dish_v1 --require-family ohio_arena_v1 --require-family ohio_bunker_v1 --require-family mandela_annex_v1 --require-family dodleston_relay_v1 --require-family ehman_1977_v1
```

The clean copied-source build produced a 487-member wheel with SHA-256 `bf7cc9eb1e617a8d5e5d055b8220061a68b791385228861195f49e8d6d16c736`. It contained all nine required native-family directories. All **25** manifest and manifest-referenced component members matched copied-source hashes; component files also matched their manifests. No game tests, art, planning, `_trash` or `_temp` folders were found in the wheel. Loader, shared contract and builder modules were present. `context.json` contains the complete member hash inventory, wheel path and temporary root.

Build, install and smoke subprocesses each exited 0; their exact argv, working directory and relevant environment are in `build.json`, `install.json`, `smoke.json`, alongside matching `.stdout`/`.stderr` files. The installed smoke used isolated Python with the checkout excluded from Python's import path, ran from the recorded temporary directory, explicitly verified game and assets paths in the installed target, ran two dummy-driver frames, loaded all nine families through their actual loaders, and directly entered/rendered the bunker, approach, salvage, dish, arena, annex, relay and 1977 scenes. The source checkout script acts as harness only; the game and assets came from the installed target. Temporary saves were used. `smoke.stdout` records each observed family and scene.

The wrapper stdout was the JSON saved as `context.json`. The shell startup emitted `/opt/homebrew/Library/Homebrew/cmd/shellenv.sh: line 18: /bin/ps: Operation not permitted` before execution; the wheel build and smoke nevertheless completed with exit 0. This dummy-SDL fixture does not demonstrate native-window behavior, continuous player motion, human review, audio, real graphical performance, or milestone acceptance.
