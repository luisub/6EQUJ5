# Bunker opaque backdrop contract and validation

2026-11-12. `ohio_bunker_v1` is the sole registered schema-3 opaque family: `bunker_hub`, viewport/world 480 × 270, density 2, opaque 960 × 540 backdrop at origin with logical-nearest positioning. `backdrop_manifest_template()` returns a fresh template; the builder fills the image hash. `build_backdrop_family()` and the existing layered `build_family()` share the same lock, pending-journal recovery, path checks, source and staged validation, and manifest-last promotion. The backdrop CLI accepts `--backdrop`; layered CLI arguments stay unchanged. No runtime asset was promoted in this work.

The three changed untracked files were copied and byte-compared before editing to `references/bunker_contract_backup_20261112_v01/`; backup SHA-256:

- `room_art_contracts.py.bak`: `3b2e98cf0aa2bf067a720756a3fb07c228d8a915d319a058939f4f59345209f9`
- `build_room_family.py.bak`: `af3fda2bf5c25b15a9b1894cd73e27dc4bd75b79dc4e32f17596defac1363e86`
- `test_room_family_transaction.py.bak`: `fb03c714185bf5b2302f3008138466c15f103c84e98e5fa1cc65340023caa87a`

Reviewed image lineage:

- Master `video_game/art/source/visual_upgrade/candidates/bunker_background_v01/source/bunker_background_generated_master.png` (1672 × 941 RGB), SHA-256 `42b06aac731cd221e8e82a34635211b9b039ff2342c79836c57d27d41770e10a`.
- Export `video_game/art/reviews/visual_upgrade/previews/bunker_registration_director_v01/capture_v01/bunker_background_960x540.png`, SHA-256 `cc9749e5373fbf97122426daf7e418aa21f77655e14077e399112c1256b74e40`.
- Registration context `video_game/art/reviews/visual_upgrade/previews/bunker_registration_director_v01/capture_v01/context.json`, SHA-256 `bf58cb7b9263cbae3e9a9b4179632941ced848e99163adfe548c08904d79a8d4`, records full-image Lanczos resizing and fixture-only composition. Station positions are directly placed and do not demonstrate normal movement, interaction, real-window behavior or art-gate acceptance.

Commands from repository root:

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_room_family_transaction.py video_game/tests/test_approach_family_transaction.py -q
/opt/anaconda3/envs/6equj5_game/bin/python -m video_game.tools.build_room_family --family ohio_bunker_v1 --backdrop video_game/art/reviews/visual_upgrade/previews/bunker_registration_director_v01/capture_v01/bunker_background_960x540.png --dry-run
```

Both exited 0: tests `38 passed in 1.19s` (`focused_tests.log`); source dry run returned `validated` with the export hash above (`source_dry_run.json`, stderr in `source_dry_run.stderr`). Temporary-root tests cover exact template/freshness, schema-2 regression, no-write validation, opaque/dimension checks, symlink and lock rejection, ordered manifest-last install, failure rollback for existing and absent files, and interrupted-process pending recovery. The reviewed-source check verifies supplied bytes and schema, not installed-family integrity, loader integration, interactive play, performance or final acceptance. Path preflight is not protection against a hostile concurrent filesystem writer; the local recovery journal is trusted state.
