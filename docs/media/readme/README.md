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

All other PNGs are unretouched 960 × 540 render surfaces from the game. The GIFs show captured frames at 768 × 432, exported with nearest-neighbor scaling and a shared 128-color palette. Arc Lance and transit run at 10 frames per second; the Denver walk runs at 5.

The main README embeds thirteen screenshots and three animations. Three additional stills are linked from their captions: the receiver, Arc Lance and galaxy map. `capture.json` records the setup, dimensions, frame counts, file sizes and SHA-256 hashes. Denver has a full-width mountain view, a gallery view centered on Fitzsimons, and the walking sequence. Proxima shows its twilight outpost and Flare Bastion guardian. The superseded `neo-denver.png` is archived under `_trash/2026-11-14_repository_compaction/docs/media/readme/`.

| Media | Setup |
|---|---|
| `observatory.png` | Fresh game in the bunker after the opening. |
| `receiver.png` | Direct entry to the receiver's initial authored FASR-001 message. |
| `arc-lance.png`, `arc-lance.gif` | Normal bunker exit, mapped movement to the pickup and mapped mouse fire. |
| `ohio.png`, `area-51.png`, `vla-rift.png`, `gobekli-tepe.png`, `buried-archive.png` | Direct entry to the named Earth room, followed by mapped movement. Campaign prerequisites are not earned for these previews. |
| `neo-denver-walk.gif` | Direct Denver entry and player-position setup with a prior-act fixture. The walk uses held Right across the real relay boundary, with enemies cleared for scenery inspection. The landmarks form an intentionally fictional Colorado composition. |
| `neo-denver-mountains.png`, `neo-denver-fitzsimons.png` | Native renderer views at player x=96 and x=480 respectively, with camera centered on the player and the same prior-act fixture. Both keep their HUD and actual gameplay layers. |
| `crystal-network.png` | FASR-003 field with staged prior guardian progress and receipt; mapped movement after entry. |
| `signal-jailer.png`, `heat-auditor.png` | Guardian scenes with staged journey ledgers and 1.6 seconds of runtime. |
| `proxima-twilight.png` | Proxima field midpoint with staged prior victories, receipts and player position. |
| `flare-bastion.png` | Proxima guardian with a staged journey ledger and 0.2 seconds of runtime. |
| `galaxy-map.png`, `signal-transit.gif` | First Earth-to-FASR-001 crossing after a staged portal unlock. |

Proxima and the travel media were refreshed together on 2026-11-13. Travel now follows an irregular route and presents the gate at the screen center. The previous map, animation and matching metadata are indexed in the [archive record](../../maintenance/archive-manifest.json).

Arc Lance and travel captures were refreshed on 2026-11-14 to show the compact
upper-right timer and simplified map captions. Previous captures and metadata
are preserved under `_trash/2026-11-14_enemy_motion/docs/media/readme/`.

The captures use temporary saves and settings, dummy SDL video/audio, a fixed random seed, and disabled CRT effects. HUD elements remain visible. Scene fixtures demonstrate current rendering; they do not establish an earned campaign playthrough, native display performance, audible quality or controller acceptance.

## Reproduce

From an installed repository checkout, choose a **new, unused output directory**:

```bash
.venv/bin/python -m video_game.tools.capture_readme --output _temp/readme-capture-NEW
```

The command refuses to overwrite an existing directory. Review the generated media before copying it here. Keep the matching `capture.json` with the files; the command does not regenerate the promotional banner or modify the README.

Earlier gallery images are preserved in `_trash/`; use the restoration index to locate them. This gallery does not replace source masters or runtime artwork.
