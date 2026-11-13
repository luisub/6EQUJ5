# Maser discharge v02 — single-asset brief

**Intent:** Give the player's 1420 maser a punchy, readable energy discharge in the existing night scenes. This is one candidate and a render-direction brief, not an acceptance or a change to gameplay.

## Observed problem

The scripted campus GIF's decoded [024](../previews/gameplay_gif_20261112_v01/preview_sample_024.png), [067](../previews/gameplay_gif_20261112_v01/preview_sample_067.png) and [096](../previews/gameplay_gif_20261112_v01/preview_sample_096.png) samples show an oversized white wedge with a vivid green bulb at the gun; its regular geometry reads as an arrow. Numerous bright cyan-white projectile strokes spread across the scene and compete with the actor and target. These are 640×360 GIF-derived, resampled/dithered stills of scripted direct-entry dummy-SDL play, not native-resolution or human-play evidence. Judge any new work in actual native captures as well.

## One bitmap

Generate one original, isolated right-facing energy muzzle flash. Suggested master path: `art/source/visual_upgrade/candidates/maser_discharge_v02/source/maser_discharge_v02_generated_master.png`; preserve the generated master and its prompt/provenance. Prepare one candidate runtime cell named `maser_discharge_v02_64x32.png`: **64×32 RGBA**, transparent outside the discharge, emitter pivot **(12,16)**; horizontal mirroring gives left pivot **(51,16)**. Place a roughly **24–30×14–18 native-pixel** visible discharge forward from the pivot, with room to keep all nonzero artwork clear of cell edges. Current Mateo displays in a 48×64 native cell, so the flash should remain a compact accent rather than dominate the figure.

The focal hierarchy is a small hot white/cyan core at the muzzle, irregular sharp cyan energy spikes pointing forward and slightly outward, then a very restrained warm edge or local halo. Use asymmetry and distinct pixel clusters, not a uniform diamond, cone, green arrow, smoke cloud, or diffuse screen bloom. Keep the player silhouette, weapon, target, hazards and telegraphs readable on dark blue night architecture and against warmer lamps. The asset is one static peak shape; timing and fading are runtime presentation, not extra painted animation frames. If the source supports it, a carefully documented crop and nearest-neighbor sampling to the native grid is acceptable; inspect the result at 1× and preserve source and transformation details. Do not manufacture runtime artwork with procedural drawing code.

## Presentation and boundaries

The discharge should strike immediately and fade quickly within the existing 0.08-second flash lifecycle, using the actual spawned muzzle position, both facings and relevant aim directions. Avoid overlapping the new image with the old flash. A small, localized warm response can complement the cool core without washing out the actor or scene. Preserve existing bounded approach lighting and keep HUD/telegraphs legible. Render-only refinements to existing projectile trails and impact sparks may reduce the dense bright fan: emphasize the primary trajectory, make supporting strokes quieter and keep them distinguishable without hiding any ray. Do not alter their world endpoints or simulation.

The field path selects the primary starter projectile for the flash; `EffectManager` draws the legacy green circle/diamond in campus and boss scenes. Approach `FiringLighting` currently suppresses the legacy eligible tap and draws a separate validated 64×32 authored burst and local world/actor response. Check both paths and their fallback, charged/other weapons, directions and depth ordering; do not draw two flashes. Replacing an exact-hash validated asset requires a coordinated loader/manifest and safe transaction decision, not simply overwriting the existing file.

Preserve aim, spawn, damage, projectile speed, beam world length, collision, firing rate, Assisted five-ray fan, saves, controller behavior, CRT handling and 480×270 world / 960×540 native render. This brief authorizes no source or runtime replacement by itself.

## Review required

Compare matching before/after actual game renders at 960×540 and integer display scale, CRT off/on: campus and boss legacy path plus approach lighting/fallback; right/left and angled fire; isolated peak and fade; repeated firing with five rays; dark background and warm lamp; moving camera, actor/weapon, target, hazards, telegraphs and HUD. Examine the alpha and pivot on light and dark fields at 1× and enlarged nearest-neighbor; record crop, alpha bounds, dimensions, hashes and provenance. Inspect whether the flash anchors correctly and reads as energy rather than an arrow, the supporting rays remain legible yet subordinate, and the local light preserves background and player detail. Sampled or scripted captures must disclose their fixtures and do not establish human motion or native-window acceptance. Review one candidate before any revision or batch.
