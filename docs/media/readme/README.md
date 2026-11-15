# README media

Created on 2026-11-13 for the [game README](../../../README.md).

## Promotional artwork

The README and arcade title screen share the canonical image at
`src/assets/ui/title_banner.png`. It is generated promotional key art, not a
gameplay screenshot, created using the observatory, guardian and crystal-realm
captures as references. Its panoramic composition combines an observatory,
explorer, cyan radio signal and violet architecture with the game title. The
duplicate `title-art.png` was archived after verifying identical bytes. The
small author credit is rendered separately by the game.

## Actual game captures

All other PNGs are unretouched 960 × 540 render surfaces from the game. Full-scene GIFs now retain the native 960 × 540 pixels and use a shared 256-color palette without dithering. Arc Lance and transit run at 10 frames per second; the Denver walk runs at 5. The three creature GIFs use unscaled 440 × 184 crops at (520, 320), sampled every five simulation frames and encoded at 80 ms per frame. Their linked PNGs show the complete scene and HUD.

The main README selects a smaller gallery for players; this directory retains the full capture collection and provenance. `capture.json` records the retained original captures and the seven-world route refresh; `finale-capture.json` records the three finale additions; `enemy-motion-capture.json` records five enemy additions. All include setup, dimensions, frame counts, file sizes and SHA-256 hashes. Denver has a full-width mountain view, a gallery view centered on Fitzsimons, and the walking sequence. The active gallery now shows the TRAPPIST-1 port and Crab memorial. Earlier screenshots retain the fixture context recorded at capture time. The superseded `neo-denver.png` is archived under `_trash/2026-11-14_repository_compaction/docs/media/readme/`.

| Media | Setup |
|---|---|
| `observatory.png` | Fresh game in the bunker after the opening. |
| `receiver.png` | Direct entry to the receiver's initial authored FASR-001 message. |
| `arc-lance.png`, `arc-lance.gif` | Normal bunker exit, mapped movement to the pickup and mapped mouse fire. |
| `ohio.png`, `area-51.png`, `vla-rift.png`, `gobekli-tepe.png`, `buried-archive.png` | Direct entry to the named Earth room, followed by mapped movement. Campaign prerequisites are not earned for these previews. |
| `neo-denver-walk.gif` | Direct Denver entry and player-position setup with a prior-act fixture. The walk uses held Right across the real relay boundary, with enemies cleared for scenery inspection. The landmarks form an intentionally fictional Colorado composition. |
| `neo-denver-mountains.png`, `neo-denver-fitzsimons.png` | Native renderer views at player x=96 and x=480 respectively, with camera centered on the player and the same prior-act fixture. Both keep their HUD and actual gameplay layers. |
| `trappist-port.png` | First retained world after a staged Earth portal victory; mapped movement after entry. |
| `crab-memorial.png` | Crab field midpoint with staged prior victories, receipts and player position. |
| `signal-constellation.png`, `signal-constellation.gif` | Earth plus the seven retained alien worlds; first crossing to TRAPPIST-1 after a staged portal unlock. Eight travel legs include the return to Earth. |
| `rift-raptor`, `resonance-effigy`, `beacon-mite` PNG/GIF pairs | Staged prior progress, player/enemy placement and extended attack cooldown; ordinary runtime updates drive the patrol and leg cycle. GIFs are labeled native detail crops; PNGs retain the full HUD. |
| `memory-extractor.png` | Staged guardian progress, then ordinary runtime updates through the first warning into an active energy-field attack. |
| `core-network.png` | Eleven prior victories and receipts staged, then 100 normal final-arena updates. |
| `central-park.png`, `central-park-walk.gif` | Same prior-progress fixture and player x=250 for the fight; mapped fire defeats both full-health Core forms. Acknowledging the six earned ending pages enters the park. The GIF shows five seconds of mapped Right movement at 10 fps, with actual family strides, birds and glints. |
| `earth-cyber-insects.png`, `earth-cyber-insects.gif` | Ohio entry with staged Mantis, Beetle and Wasp positions, replaced encounters and extended attack cooldowns. Four seconds of ordinary patrol updates at native 960×540 and 10 fps. |
| `beacon-forger-left.png`, `beacon-forger-right.png`, `beacon-forger-turn.gif` | Prior ten victories/receipts, player start and extended boss cooldown staged. Mapped Right and Space carry Mateo past the guardian; normal updates turn its body. Native 960×540, 10 fps, 2.5 seconds. |

Proxima and the travel media were refreshed together on 2026-11-13. Travel now follows an irregular route and presents the gate at the screen center. The previous map, animation and matching metadata are indexed in the [archive record](../../maintenance/archive-manifest.json).

Arc Lance and travel captures were refreshed on 2026-11-14 to show the compact
upper-right timer and simplified map captions. Previous captures and metadata
are preserved under `_trash/2026-11-14_enemy_motion/docs/media/readme/`.

The complete gallery was refreshed again on 2026-11-14 with native GIF exports, 256 colors, creature-motion details and an actual Memory Extractor attack. Fifteen replaced captures/metadata files are preserved under `_trash/2026-11-14_readme_refresh/`. The capture tool no longer emits the retired redundant `neo-denver.png`.

The captures use temporary saves and settings, dummy SDL video/audio, a fixed random seed, and disabled CRT effects. HUD elements remain visible. Scene fixtures demonstrate current rendering; they do not establish an earned campaign playthrough, native display performance, audible quality or controller acceptance.

The seven-world route refresh on 2026-11-15 replaces the active gallery landscapes
and first-crossing map/GIF. Five obsolete world PNGs and previous travel media /
metadata are archived under `_trash/2026-11-15_shorter_journey/`; their hashes are
in the restoration index. Current travel shows eight named chart markers, eight
legs including the return, a centered aperture and a radial tunnel. New captures
use the same isolated saves, native resolution and fixture disclosures. Earlier
finale/enemy records describe their original eleven-world prerequisite fixtures.

## Reproduce

From an installed repository checkout, choose a **new, unused output directory**:

```bash
.venv/bin/python -m video_game.tools.capture_readme --output _temp/readme-capture-NEW
.venv/bin/python -m video_game.tools.capture_finale --output _temp/finale-capture-NEW
.venv/bin/python -m video_game.tools.capture_enemy_motion --output _temp/enemy-motion-NEW
```

The command refuses to overwrite an existing directory. Review the generated media before copying it here. Keep the matching `capture.json` with the files; the command does not regenerate the promotional banner or modify the README.

The finale command creates six review captures. This gallery retains the Core
still, peaceful park still and park walk; their matching subset of metadata is
saved as `finale-capture.json`. It also captures the second form and two dialogue
views for local review. Both commands use temporary saves and settings.

The enemy-motion command creates the five captures listed above. Its metadata is
retained as `enemy-motion-capture.json`. The original gallery records an earlier
renderer revision; these new previews show the current Earth enemy artwork and
boss-facing behavior. Native-display and human playthrough acceptance remain open.

Earlier gallery images are preserved in `_trash/`; use the restoration index to locate them. This gallery does not replace source masters or runtime artwork.
