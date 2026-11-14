# Alien world artwork

One directory per civilization holds the reviewed background and guardian masters,
their runtime exports and the generation/export record. The route order is
FASR-001, FASR-003, FASR-005, FASR-004, FASR-008, FASR-009, FASR-006,
FASR-002, FASR-SCAN-H, FASR-010 and FASR-007. FASR-001 and FASR-003 have
separate `background/` and `guardian/` folders, with their original recipes and
provenance. Their duplicate FASR-003 source alias is archived.

| Civilization | Background | Guardian |
|---|---|---|
| FASR-001 | Sagittarius signal landscape | Radio-array guardian |
| FASR-003 | Cobalt crystal-network landscape | Copper and charcoal heat auditor |
| FASR-005 | Blue-violet twilight outpost and mountain shields | Armored solar siege crab |
| FASR-004 | Lilac cloud refinery and suspended condensers | Crescent-finned gas harvester |
| FASR-008 | Teal ocean port and seven-world assembly hall | Ivory and brass mobile siege organ |
| FASR-009 | Graphite ancient probe and abandoned observation arrays | Silver lance on a stabilised monowheel |
| FASR-006 | Cold blue memorial vaults and copper beacon | Walking bronze archive vault |
| FASR-002 | Indigo gravimetric observatory | Gyroscope around a dark optical core |
| FASR-SCAN-H | Gray-green tidal monoliths and suspended chambers | Pale mineralized seven-limbed organism |
| FASR-010 | Rainy forest reclaiming an old observatory | Stone-and-root memory colossus |
| FASR-007 | Indigo insectoid beacon workshops | Gold-edged mantis engineer |

For the nine families from FASR-005 onward, `background_master.png` and
`guardian_master.png` are untouched generated source
images. `background.png` is the opaque 1920 × 540 panorama; `body.png` is the
transparent 256 × 192 guardian. `provenance.json` records prompts, original
generation filenames, hashes and export settings.

To reproduce exports for those nine families (the earlier two use the recipes
in their separate provenance records):

```bash
.venv/bin/python src/art/source/alien_worlds/export.py src/art/source/alien_worlds/fasr_005
```

Backgrounds use an aspect-preserving cover crop. Guardians have transparent
margins trimmed using alpha ≥ 64 body bounds, then fit proportionally within 248 × 184 pixels and are
bottom-centered in the runtime frame. The export does not paint or reshape the
artwork. Runtime promotion uses `video_game.tools.build_campaign_art`, retaining
its validation, lock and manifest-last transaction. Existing families must not
be silently overwritten.

The visual direction uses cool, restrained landscapes with small practical
lights and brighter, readable threats. Each civilization has its own materials,
landmarks and guardian silhouette. Backgrounds are continuous panoramas;
civilization profile thumbnails are not tiled into level scenery.

Design references:

- [Light and VFX](https://www.madvfx.com/blogs/the-interplay-of-light-and-vfx-in-games-how-they-work-together)
- [Color theory in real-time VFX](https://www.madvfx.com/blogs/color-theory-in-real-time-vfx)

Renderer captures use temporary campaign fixtures. Visual review does not claim
a complete human playthrough or native-platform performance acceptance.
