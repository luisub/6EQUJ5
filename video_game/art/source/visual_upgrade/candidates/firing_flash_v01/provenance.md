# Ohio approach maser flash — generation provenance v01

Status: unchanged generated master awaiting independent native-size, alpha, pivot and mirrored review. One static transparent flash only; no crop, resampling, cleanup, light-field art, composite or runtime edit was made by the artist. It does not demonstrate environmental illumination, gameplay integration, motion or art-gate acceptance.

- Generation date: 2026-11-12.
- Tool: `image_gen__imagegen`; one image-guided request; `transparent_background: true`. No seed or further settings exposed.
- Original generated master: `source/firing_flash_generated_master.png`, 1774 × 887 RGBA; SHA-256 `e572751bb235e9dc92a80cbbb3ceb9428dffacedea9e1f7ff74bb6b861441b8f`.
- Original tool output: `generated_images/exec-55d4aab1-18c9-403f-81ea-d6049a52ce37.png`; copied byte-for-byte; hashes match.
- Image references in request, in order: `video_game/art/reviews/visual_upgrade/previews/mateo_fire_preview_v02/right_original_frame0_native_960.png`; `video_game/art/reviews/visual_upgrade/previews/firing_lighting_technical_v01/baseline_v01/right_fire0_native_960.png`.
- Brief: `video_game/art/reviews/visual_upgrade/briefs/firing_lighting_benchmark_v02.md`, asset portion of one request explicitly approved by Astra.
- Intended export: 64 × 32 transparent RGBA, right emitter pivot (12,16), mirrored pivot (51,16), compact principal burst. Actual generated master 1774 × 887 (2:1); no exact-native claim. Crop/resampling, registration, light/dark contrast and alpha handling remain unverified.
- Original alpha range 0–255; zero-alpha pixels 1,497,730; partial 74,745; opaque 1,063. Nonzero-alpha bounds (160,116,1609,750); alpha >127 bounds (340,272,810,605), exclusive ends; all corners alpha 0. Alpha >127 bounds map approximately to native x=12.3–29.2 and y=9.8–21.8 under a full-canvas proportional resize, an estimate only.
- Initial observation: a small pale-green directional cluster is present near the intended emitter location. Top/bottom green blocks appear detached and faint partial alpha extends far beyond the main shape; inspect at native size and on light/dark backgrounds before deciding whether the source is suitable.

## Exact generation prompt

Create ONE original transparent pixel-art SPRITE for a compact right-facing energy-maser muzzle discharge in a side-scrolling action game. The attached current in-game firing screenshots are references ONLY for existing weapon scale, shot direction and position: do not reproduce the character, room, old green bulb, diamond, projectile line, text, HUD or any surrounding pixels. This is the bright FLASH SHAPE ALONE, not a lighting overlay or a complete screenshot.

Intended final native sprite cell is exactly 64×32 pixels, landscape 2:1. The emitter/pivot is at (12,16), where the gun muzzle touches the flash. Design a tight asymmetrical burst pointing horizontally RIGHT from that pivot, concentrated in the left half of the cell with considerable fully transparent padding to the right, top, bottom and left. The hot central cluster is near-white with a slight pale green tint, approximately color (232,255,234), occupying about 12×8 native pixels. Surround it with a restrained green edge approximately (140,215,162). The whole principal directional burst should fit roughly a 24×16 native-pixel envelope around and forward of the emitter. Use a few coherent, purposeful stepped pixel clusters to form a compact directional energy discharge; readable at actual 1× native pixel size. Leave the barrel and actual projectile visually legible; the burst is a small single instantaneous accent.

NO perfect disc, round bulb, huge needle/spike, oversized starburst, broad halo, bloom cloud, particle field, colored environmental light pool, glow on walls, ground, weapon, actor, background, border, text, HUD or multiple frames. No orange, red or coral in this bitmap; the warm environmental response is a separate renderer effect. Transparent background with clean true alpha outside the shaped burst and transparent padding on all sides. No black, white, green, checkerboard or other matte, no blurred photographic plasma, airbrushing, gradient blob, procedural noise or line of tiny sparkles. One original static single-frame right-facing sprite, not a sheet or animation, with deliberate hard-edged clusters and controlled tiny alpha transitions where useful.

