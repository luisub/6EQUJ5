# README media

Created on 2026-11-13 for the [game README](../../../README.md).

## Promotional artwork

`title-art.png` is generated promotional key art, not a gameplay screenshot. It was created with image generation using the game's existing observatory, guardian and crystal-realm screenshots as visual references. Its panoramic composition combines an observatory, a small explorer, a cyan radio signal and violet crystal architecture with the game title. It is documentation artwork only; runtime assets are unchanged.

## Actual game captures

All other PNGs are unretouched 960 × 540 render surfaces from the game. The GIFs show captured frames at 768 × 432, exported with nearest-neighbor scaling and a shared 128-color palette. Arc Lance and transit run at 10 frames per second; the Denver walk runs at 5.

The main README embeds eleven screenshots and three animations. Three additional stills are linked from their captions: the receiver, Arc Lance and galaxy map. `capture.json` records the setup, dimensions, frame counts, file sizes and SHA-256 hashes. Denver now has a full-width mountain view, a gallery view centered on Fitzsimons, and the walking sequence. The earlier `neo-denver.png` capture remains preserved; other locations retain their earlier setup.

| Media | Setup |
|---|---|
| `observatory.png` | Fresh game in the bunker after the opening. |
| `receiver.png` | Direct entry to the receiver's initial authored FASR-001 message. |
| `arc-lance.png`, `arc-lance.gif` | Normal bunker exit, mapped movement to the pickup and mapped mouse fire. |
| `ohio.png`, `area-51.png`, `vla-rift.png`, `gobekli-tepe.png`, `buried-archive.png` | Direct entry to the named Earth room, followed by mapped movement. Campaign prerequisites are not earned for these previews. |
| `neo-denver.png`, `neo-denver-walk.gif` | Direct Denver entry and player-position setup with a prior-act fixture. The still retains the HUD; the walk uses held Right across the real relay boundary, with enemies cleared for scenery inspection. The landmarks form an intentionally fictional Colorado composition. |
| `neo-denver-mountains.png`, `neo-denver-fitzsimons.png` | Native renderer views at player x=96 and x=480 respectively, with camera centered on the player and the same prior-act fixture. Both keep their HUD and actual gameplay layers. |
| `crystal-network.png` | FASR-003 field with staged prior guardian progress and receipt; mapped movement after entry. |
| `signal-jailer.png`, `heat-auditor.png` | Guardian scenes with staged journey ledgers and 1.6 seconds of runtime. |
| `galaxy-map.png`, `signal-transit.gif` | First Earth-to-FASR-001 crossing after a staged portal unlock. Map positions are fictional and schematic. |

The captures use temporary saves and settings, dummy SDL video/audio, a fixed random seed, and disabled CRT effects. HUD elements remain visible. Scene fixtures demonstrate current rendering; they do not establish an earned campaign playthrough, native display performance, audible quality or controller acceptance.

## Reproduce

From an installed repository checkout, choose a **new, unused output directory**:

```bash
.venv/bin/python -m tools.capture_readme --output _temp/readme-capture-NEW
```

The command refuses to overwrite an existing directory. Review the generated media before copying it here. Keep the matching `capture.json` with the files; the command does not regenerate the promotional banner or modify the README.

The earlier images in `docs/media/` remain preserved. This gallery does not replace source masters or runtime artwork.
