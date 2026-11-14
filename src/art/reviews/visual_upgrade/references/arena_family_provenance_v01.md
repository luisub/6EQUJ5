# Arena family source lineage and validation — v01

2026-11-11. The following identifies reviewed registration inputs for `ohio_arena_v1`, schema 2, `act_01_greenkeeper_arena`. World 640 × 288, viewport 480 × 270, native density 2; ordered far and world layers; no props. These source records do not themselves mean promotion or final human acceptance.

| Role | Repository-relative input and SHA-256 | Transform |
| --- | --- | --- |
| World master | `video_game/art/source/visual_upgrade/candidates/greenkeeper_world_scene_v02/source/greenkeeper_world_scene_generated_master.png`, 1870 × 841, `c91950103b984c1e8c44bb70333b86a79c76d34b086d0d5a38225feae44e7d3d` | Full-image Lanczos resize to 1280 × 576, no mask, alpha edit, painting or cleanup, per registration context. |
| World export | `video_game/art/reviews/visual_upgrade/previews/arena_registration_director_v02/capture_v01/arena_world_layer_1280x576.png`, `b5f6188a37c5e042d8c4f591692b49bf4728f022d5a83ad2375287c8f565b7b7` | World-fixed, native density 2; staged review stills use this export. |
| Far master | `video_game/art/source/visual_upgrade/candidates/approach_far_v01/source/approach_far_generated_master.png`, 1825 × 862, `eec86caf566730b53adbc1bbbc510cf1015a98eaf32c89648bdb3af3b8476700` | Full-image Lanczos resize to 1152 × 544, per far registration context. |
| Far export | `video_game/art/reviews/visual_upgrade/previews/approach_far_registration_v01/far_native_1152x544.png`, `f57b938219cb4d228ad3f6339a854b2cc770bf15b97bdb36f83a1df31997718e` | Opaque, parallax (0.1, 0.05); this is the shared approach far used as an interim arena fixture, not an independently approved arena sky. |

Arena registration context `video_game/art/reviews/visual_upgrade/previews/arena_registration_director_v02/capture_v01/context.json` SHA-256 `28a9a61f14edb5cd669be4c08190ed2a9ebd64cbd7d6c6923ae25a20eafa44ae` documents fixture composition, crop positions and injected states; far context `video_game/art/reviews/visual_upgrade/previews/approach_far_registration_v01/context.json` SHA-256 `f04f00eb4b14e2fca2afc5b76d746f66fd6f64dfa8302a2a2c64c4ac1ea164fd`. Recorded source/export/context hashes were rechecked. Arena stills include injected boss states; they do not prove a normal-input earned fight, continuous motion, native-display performance, accessibility, fairness or final art acceptance.

## Focused validation

The contract adds one immutable room descriptor; prior three descriptors and schema-1 approach are unchanged. Pre-edit copies of both changed files were byte-compared and retained under `references/arena_contract_backup_v01/` with `.bak` suffix.

From repository root, test command:

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_room_family_transaction.py video_game/tests/test_approach_family_transaction.py -q
```

Exit 0; `29 passed in 0.91s`. Full output: `references/arena_validation_v01/focused_tests.log`. The family-parametrized test validates no-write source review, transaction order and isolated promotion for arena in a temporary root; other generic transaction tests cover failure and recovery behavior. It is not a real-asset promotion.

Actual-source dry run:

```sh
/opt/anaconda3/envs/6equj5_game/bin/python -m video_game.tools.build_room_family --family ohio_arena_v1 --far video_game/art/reviews/visual_upgrade/previews/approach_far_registration_v01/far_native_1152x544.png --world video_game/art/reviews/visual_upgrade/previews/arena_registration_director_v02/capture_v01/arena_world_layer_1280x576.png --dry-run
```

Exit 0, `status: validated`, with both expected hashes, world dimensions, room ID and an empty props list. Exact output: `references/arena_validation_v01/source_dry_run.json` (stderr `source_dry_run.stderr`). This checks the supplied image bytes and schema, not installed-family integrity, loader integration or boss rendering. No arena asset promotion was performed by this task. The family is scoped to the existing arena; future route integration and staged boss review are separately owned.
