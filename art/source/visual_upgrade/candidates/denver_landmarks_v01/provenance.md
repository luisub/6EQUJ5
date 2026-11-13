# Denver: Fitzsimons and mountain ridge

Created on 2026-11-13 at the owner's request. This replaces the generic Neo-Denver brick frontage with a recognizable Fitzsimons-inspired sandstone building and the specific forested ridge in the supplied photograph. The pale cliff crest and hillside A remain visible. Warm architectural lighting and a clearer blue mountain silhouette make both landmarks readable behind gameplay. This is a fictional Colorado composition, not a literal geographic view.

## Sources and generation

- Existing game palette/material reference: `src/assets/environments/campaign_worlds/neo_denver_v1/background.png`, prior SHA-256 `5332a05acb3b7c6fe9d763515da8e22840eade73f00145e9b087f3d123ae8048`.
- Owner's mountain photograph: <https://www.raftmw.com/wp-content/uploads/2012/04/slide_1.jpg>.
- Architectural reference: [CU Anschutz, “20 Years: The Evolution from Fitzsimons to Anschutz”](https://news.cuanschutz.edu/medicine/magazine-som-cover-history), hero image of Building 500. Photographs were used as visual references, not installed as game textures. Reference hashes and the image URL are recorded in `manifest.json`.
- Both masters were created with `image_gen.imagegen`. `prompts.md` preserves the complete edit and composition instructions. The revision adds top clearance, keeps the ridge silhouette inside the scrolling crop and removes the generated inscription above the entrance.

| File | Dimensions | SHA-256 |
|---|---|---|
| `master_v01.png` | 2172 × 724 RGB | `97ddb2dcb1ca4212ab8a1b052633740ea0ef10ce773005424f50d077d7da83e8` |
| `master_v02.png` | 2172 × 724 RGB | `85daaf1d94ac912f3fa2371c2ab30576ce356eb2e6822c29f163c4b8a0b2f486` |
| `background.png` | 1920 × 540 RGB | `de5c8ae7ca062458fb7f8887a2d2581f0f2fcfe8adae83811ebf302a61b3a093` |

## Export

Only a crop, nearest-neighbor downsample and RGB format conversion follow generation. No programmatic painting or contrast filter was applied. From this directory, write to a new output path:

```bash
ffmpeg -hide_banner -loglevel error -i master_v02.png \
  -vf 'crop=2172:611:0:86,scale=1920:540:flags=neighbor,format=rgb24' \
  -frames:v 1 -update 1 rebuilt-background.png
```

The crop is `(0, 86, 2172, 697)`, using exclusive right/bottom coordinates. Runtime keeps the existing `neo_denver_v1` ID, validated 1920 × 540 manifest and consecutive panorama slices. Scenery remains non-colliding. Routes, player controls and room dimensions are unchanged.

## Installation and review

The existing campaign-art validator checked the export; `promote_group` installed the PNG and then its manifest under the asset lock. The previous pair is preserved in `_trash/2026-11-13_F03/b52df69faf604cecbbcaca6abd526549/`, with hashes and restoration instructions. `docs/migration/archive-manifest.json` indexes both originals.

Actual renderer inspection covers Denver entry, middle and end views, relay rooftops, amplifier station and the Synchronicity arena. Entry captures include CRT off/on at 960 × 540 and 1920 × 1080. A held-Right fixture crosses the street/relay boundary without an interruption. Captures use temporary saves/settings and explicit prior-progress/position fixtures; the walk clears enemies to inspect scrolling. They are not a human playthrough, controller-hardware or native-performance acceptance.

Validation: 58 focused scenery, content, panorama and UI checks passed; all 52 levels validated; the asset-builder dry run passed. Inspection files and context are in `_temp/denver_landmarks_20261113/visuals/`. The README still and walking GIF are reproducible with `python -m tools.capture_readme --output <new-directory>`; their setup and hashes are in `docs/media/readme/capture.json`.
