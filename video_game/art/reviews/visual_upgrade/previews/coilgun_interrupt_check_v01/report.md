# Coilgun interruption focused check

Command from the repository root:

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_combat_assist.py video_game/tests/test_combat.py -q
```

Result: 62 passed in 0.47 seconds, exit 0; see `pytest.log`. The new regression checks interruption while held, no release shot, unchanged cooldown on cancellation, and a subsequent ordinary charged shot. Dummy SDL; physical input and integration remain separate. Pre-edit recovery copies and hashes are in `../coilgun_interrupt_backup_v01/`.
