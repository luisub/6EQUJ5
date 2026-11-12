# Ohio approach firing-flash provenance

This is one reviewed approach-only presentation asset. No legacy or locked artwork is replaced.

- Master: `video_game/art/source/visual_upgrade/candidates/firing_flash_v01/source/firing_flash_generated_master.png`, SHA-256 `e572751bb235e9dc92a80cbbb3ceb9428dffacedea9e1f7ff74bb6b861441b8f`.
- Review and prompt context: `video_game/art/reviews/visual_upgrade/briefs/firing_flash_v01_registration_review.md` and `video_game/art/reviews/visual_upgrade/briefs/firing_lighting_benchmark_v03.md`.
- Reviewed export: `video_game/art/reviews/visual_upgrade/previews/firing_flash_registration_v01/cell_v01/firing_flash_64x32.png`, SHA-256 `027df21d8bb8d6d21f1421ad7bb50845e941a6907de2af430571fd95374ef7e5`. Full-canvas nearest resampling produced the 64×32 RGBA image; no alpha editing, painting or crop. Registration context and original transform are beside the export.
- Intended installed family: `video_game/assets/effects/approach_maser_flash_v1/`, consisting of this exact image and a manifest pinned to its hash, approach room, dimensions and emitter pivots. Installation is explicit, staged and journaled under the existing asset-root lock.
- The warm architectural and actor response uses bounded mathematical light masks, not extra bitmap artwork. Existing actors, level geometry and gameplay data remain unchanged.

The `staged_install_v02` native frames use an isolated asset root, actual scene entry and physical fire input; their peak left/right PNG bytes match the accepted `candidate_shadow_v04` preview frames. The earlier `staged_install_v01` failed before a transaction because `/var` is a symlink; the second fixture uses its canonical path. Dummy SDL stills do not establish native-window behavior or playback.
