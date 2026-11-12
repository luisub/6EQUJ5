# Starter-maser assist: focused unit check

Command (repository root):

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_combat_assist.py video_game/tests/test_combat.py -q
```

The first pytest invocation printed 61 passed in 0.42 seconds (`pytest.log`), but its surrounding zsh harness then exited 1 because it attempted to assign the read-only variable `status`; pytest's exit status was consequently not captured. A corrected harness reran the same command, returned exit 0 and printed 61 passed in 0.39 seconds (`pytest_rerun.log`). Both runs used dummy SDL. The targeted new tests cover classic/assisted cadence, charge precedence and cancellation, fan symmetry and normalized rays, primary identification, single-hit volley behavior across updates, target absorption and solid-wall collision, and no change to scattergun auto intent. These are unit checks, not hardware or normal-play acceptance.

Pre-edit recovery copies and SHA-256 manifest: `../combat_assist_backup_v01/`; the original `/tmp/6equj5-combat-assist-ZxR4NJ/` copies are also retained.
