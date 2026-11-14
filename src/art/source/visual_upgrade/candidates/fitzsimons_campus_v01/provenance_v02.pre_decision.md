# Fitzsimons-inspired fictional Ohio campus — lighting revision v02

Status: one targeted image-generation edit of v01 for registered composite review. The source/master and export from v01 are preserved. No runtime asset was promoted.

## Edit source and result

- Input: `source/fitzsimons_campus_generated_master_v01.png`, SHA-256 `6288eeb97d0549b12661cb25901d91e4ef0a3cd41107fc2e56beff353deaff7a`.
- `image_gen.imagegen` edit, opaque requested, 2026-11-12. Tool output `generated_images/exec-20a59729-b66d-4447-bd23-d5523f0265fe.png` copied byte-for-byte to `source/fitzsimons_campus_generated_master_v02.png`; both SHA-256 `e303e5f71b3e2a51fa0da30ceaa57596e3b9419920a56fb2779d63accccce529`.
- Actual result 1825×862 RGB, no alpha channel. Master and native export visually inspected.

## Exact edit prompt

> Edit this exact original game background image. Preserve the complete framing, image dimensions/aspect, unchanged sky composition, the precise silhouette, exact location and layout of the building, stepped crown and wings, architectural proportions, all window grid and stone-band geometry, and central tower position. Do not add or remove any structures or objects. Change ONLY the building's lighting and color: it is a distant building at deep night, substantially darker and cooler than this version, with most of its brick facade in deep indigo and slate-blue shadow, while enough texture remains legible. Preserve dark tall central window strips and a restrained cool moonlight rim on roof and stone edges. Leave most windows pitch dark. Retain only a few warm amber windows and wall lamps as small bright cores, with visible, carefully bounded warm halos that illuminate only small nearby patches of real brick and stone. Strong local dark/light contrast; the overall building must read clearly cooler, darker and quieter than a warmly lit near foreground would. Preserve crisp intentional pixel-art clusters; no blanket bloom, fog, airbrush, blur, photographic filter or global colored overlay. No text, logo, characters, trees, foreground, terrain, platforms or sky additions.

## Review export

`fitzsimons_campus_far_v02_1152x544.png`: crop master using Pillow exclusive box `(12, 12, 1812, 862)`, yielding 1800×850, then uniformly downsample by 0.64 with nearest-neighbor to 1152×544. No upscaling, nonuniform stretch, code-applied painting or tonal filter. RGB is opaque by construction; SHA-256 `201353a9d2be77ad7f583e800e88baada55bdcc94702875caae3ec3b5fdc4e7a`; RGB extrema each `(0,255)`. The v01 export still hashes `a3a96302e58f0c6322a0e2c200800dc140eb4e8264c9bed8eae7b6129b4debc3`.

In the standalone image the mass is markedly darker and cooler, with a cool roof rim and sparse localized warm window and entrance pools. The overall architectural arrangement and crop anchors appear retained; this is a generative edit, not a guarantee of identical individual pixels or windows. The central strips are very dark and their readability against the actual scene needs particular review. This is an unapproved review candidate; motion, parallax, CRT and gameplay readability are not established by the standalone image.

Artist viewed the technical fixture's 960×540 CRT-off stills at x0, x400 and x800, y18 under `art/reviews/visual_upgrade/previews/fitzsimons_campus_v01/candidate_v02/`. The far mass is visually cooler and darker than the near buildings, and the stepped crown and rooflines remain legible. The tower strips are nearly black; the v01 tower lamps are absent in this generative edit, and only one or two warm windows are visible in each crop. The dome still masks the central tower at x0. Static fixture conditions and evidence are in that directory's `context.json`; no human play, full-motion or art-gate acceptance follows.
