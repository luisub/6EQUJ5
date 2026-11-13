# Mateo olive-field standing pose — generation provenance v01

Status: generated master awaiting independent review. One static pose, not an animation or shipping asset. No 48×64 export, crop, downsample, alpha cleanup or environment composite has been made; neither exact-native generation nor native-size readability is claimed.

- Generation date: 2026-11-11.
- Tool: `image_gen__imagegen`; one image-guided request; `transparent_background: true`. No seed or further settings exposed.
- Unchanged original master: `source/mateo_olive_stand_generated_master.png`, 1086 × 1448 RGBA; SHA-256 `153f51c7865cb9a11495f0c59cb82085320f969fa519ddd1203538e2101c58e1`.
- Original tool output: `generated_images/exec-d82e0fd7-5618-4ea2-8aa9-c20d94336344.png`; copied byte-for-byte to source; hashes match.
- References in request, in order: `video_game/art/source/mateo/concept_mateo_idle_1794333616733.jpg`; `video_game/assets/sprites/mateo/olive_field/idle_1.png`.
- Approved brief: `video_game/art/reviews/visual_upgrade/briefs/ohio_approach_mateo_benchmark_v0.3_approved.md`.
- Requested final cell: 48 × 64, visible figure approximately 25 × 59 and foot at (24,62). Actual generated master: 1086 × 1448; pose dimensions, scale, contact and readability at 48 × 64 remain unverified.
- Source alpha inspection: corner alpha values all 0; alpha range 0–255. Nonzero-alpha bounds (114,35,978,1448); alpha >127 bounds (306,149,780,1377), ends exclusive. 372,878 pixels have partial alpha and 1,384 are fully opaque. This indicates extensive partial transparency and faint pixels outside the main figure; inspect on light and dark grounds before any alpha-cleanup decision.

## Exact generation prompt

Create ONE original static pixel-art standing idle sprite of Dr. Mateo “Six” Vargas, based on the two attached identity references. The first image is his character concept; the second is his existing olive-field idle sprite and is the authority for standing pose, in-game scale, footprint, facing and visual simplicity. Preserve his identity: adult man with medium-brown skin, short dark hair and stubble; sturdy adult proportions; olive M-65 field jacket with clear pockets and rolled sleeves, dark/khaki cargo trousers, sturdy dark boots, shoulder strap, neck headset and small belt radio where readable. He is an alert scientist, not a new character. He faces RIGHT in the same neutral, grounded standing orientation as the existing idle, with both feet planted; arms relaxed, hands visible, distinct head, shoulders, arms, jacket hem, two legs and boots. No prominently visible weapon, no held item, no invented accessory. One figure only, no animation, alternate poses, sprite sheet, text, interface, shadow plane or scenery.

The final intended game cell is 48×64 pixels, with the visible silhouette approximately 25×59 pixels and foot contact at cell coordinate (24,62). Preserve the existing small on-screen footprint, rather than making an enlarged broad hero. Compose the complete upright silhouette centered in the transparent canvas with breathing room above and at both sides and both boots aligned to the same ground-contact line near the bottom. The character must read at actual 48×64 cell size: purposeful hard-edged pixel clusters and restrained palette; clear separations of skin, olive jacket, dark trousers and boots. Render native pixel-art style with deliberate clean contours, no soft portrait shading, no gradients, no blur, no photorealism, no antialiased halo. Original artwork rather than a filtered enlargement of the existing sprite.

Output a single full-body sprite on a genuinely transparent background with clean transparency to the canvas edges; no magenta or other solid backdrop, no framing.

