# Greenkeeper heavy chassis — review brief v01

Status: **idle candidate authorized; no runtime promotion**. This is a bounded Act I boss upgrade, not the campaign's final boss.

## Direction

The Greenkeeper is an automated Ohio Big Ear terraforming excavator hijacked by the Core. Author an original, massive industrial machine facing left toward Mateo: broad articulated tracks, an earthmoving blade and hydraulic mounts, distinctive armored cab, rear terraforming plant, and elevated mortar. Use dark blue-green steel, soot and rust, disciplined amber rim/weapon light and a small green reactor diagnostic. Pixel-art clusters should read against the installed dark reflector basin. No background, floor, typography or detached effects. Keep a readable silhouette and an unmistakable exposed reactor position for the later pose. Preserve existing source art unchanged as a complete fallback, not as a visible nested vehicle.

## Serial asset workflow

Create **four key poses one at a time**: idle → attack → exposed reactor → destroyed wreck. Obtain review after each pose before starting the next; use the accepted first master as edit reference to retain registration and identity. Idle is the only pose currently authorized. New poses are mapped deliberately to existing states (idle/charge, mortar/sweep, vulnerable, defeated); this means reduced pose coverage, not eleven newly authored frames. Motion and phase readability remain review requirements.

Each pose is a transparent RGBA master for a **256 × 192 native pixel** export, corresponding to **128 × 96 world pixels** at 2× density. Preserve generated sources, tool settings, transforms and source/export hashes. Image-generation output dimensions may require recorded extraction/resampling; inspect at both sizes. Nominal idle origin **(428,144)** retains old center x=492 with the foot at world floor **y=240**. Review the actual opaque bounds and landmarks before finalizing the anchors.

For idle, deliver the master, registered export, light/dark previews and an actual-arena static composite. Review with actual player and framing. Do not change runtime until the four serial reviews establish a coherent family.

## Geometry and integration constraints

The scene instantiates Greenkeeper at **(460,192)** and the current body is **64 × 48**; `boss_spawn` metadata is not the current constructor position. The existing weak-point rectangle is **(x+8,y+6,24,20)**, mortar smoke is placed in the scene at **(boss.x+24,boss.y+8)**, sweep starts at `boss.x`, and the charge warning uses boss position and a fixed 80 × 48 box. Enlarge the damage/charge body only after explicit treatment of these anchors, downstream callers and fairness. Preserve floor y=240, 480 × 270 world view and player physics; inspect initial camera framing, catwalks and charge clearance.

The boss currently renders to the **480 × 270 logical canvas**; simply blitting 256 × 192 there doubles intended world size, whereas shrinking it before that canvas discards native detail. A correctly ordered native-density composite requires coordination with the owner of `scenes/boss.py`; telegraphs, projectiles, actor, effects and CRT layer order must remain correct. No full renderer rewrite is authorized.

## Promotion evidence

Inspect idle, attack, exposed reactor and destroyed composite at actual 960 × 540 output with CRT on/off and reduced effects. Check targeting, telegraphs, both attacks, floor contact, actor separation, camera crop and movement, and retry/reset. Validate no per-frame I/O, complete fallback when the new family is unavailable, packaging, hashes and provenance. Preserve every original PNG and manifest. Fixture screenshots are not human/native-window play acceptance.

## Review and installation ledger

Root reviewed and accepted the idle, attack, exposed and wreck directions individually and the combined nearest-neighbor pose sheet. Four 1448×1086 generated source masters use transparent backgrounds; the latter three were edits of the idle master. The exports use alpha threshold <16 removed, nearest-neighbor reduction to 256×192 and an 11-native-pixel downward translation, preserving the registered baseline. Nearest edges retain minor fine-detail aliasing; the four poses are discrete keys and do not create an animated track cycle. Exact prompts, masters, export alternatives, preparation scripts and per-pose provenance are in [`greenkeeper_heavy_v01`](../../../source/visual_upgrade/candidates/greenkeeper_heavy_v01/).

| Pose | Master SHA-256 | Installed 256×192 SHA-256 |
|---|---|---|
| Idle | `f2e9166a6cd5470e835a6665df0bcaa837079651b6f69ba0ddc1fea34af432e7` | `e5aa98b55d761de1d1ea4959e025ff51b7ac310a434752da6eab537d4da0918c` |
| Attack | `b8f909333fab83b9efbf5fa71c2fd3c4da2e8fad9648956faf850a5672355df3` | `1e607d90a4c4a54bf386c0b24b1d4981a6d8f87e99ab8173958a81fc3fb0eddf` |
| Exposed | `857933e0982a6676682fb1477da5b35db8aa570b85ade8b40eb272f19245c148` | `f88ac427ed68d7321222d205ceb2f60b9a67f0b111c2707ff6ed0102a92cf1e7` |
| Wreck | `8f5f939fa5cf0f9ce9c3d25ab87397cf12296873abb865d3720e8946c6a6e0f7` | `d54d7e427dfd3632e94522fac21bdced7d2bfd935600c9f0483bfdf483ca4f6f` |

Manifest SHA-256 `11c49520aed6a84b709269fd4977c1159364c4dd9ae1f563b75718020718b49f`. The builder used the shared asset lock, staged and revalidated all four images, wrote its transaction journal and installed the manifest last. The restore record is `video_game/_trash/2026-11-11_F03/feac5ccd831e4704b4686d5524727991/manifest.json`; these files were new. The 11 legacy PNGs and original manifest matched their HEAD SHA-256 hashes after promotion.

The heavy family is validated all-or-nothing at construction; absent, incomplete, corrupt or pending-transaction art selects legacy 64×48 geometry. The reviewed model uses local reactor rect (62,49,23,19), muzzle (39,16), sweep source (5,80), foot y96 and default world body (428,144,128,96); explicit constructor coordinates denote the chosen body's top-left. A target-specific swept-projectile hook allows an aimed shot to reach the exposed core at actual impact time while retaining wall, other-target and volley ordering. Focused family/projectile/combat run passed 66 tests. A pre-edit `weapons.py` recovery copy has SHA-256 `707ea2809949c46acad01d52b9f11f53e26c1aaab7f4584afb0528a4a3823ad4` at `art/reviews/visual_upgrade/previews/greenkeeper_heavy_collision_backup_v01/weapons.py`.

The separate actual-scene fixtures and whole-tree checkpoint are tracked by the integrator. Their static dummy-driver results are not a native-window human-play or visual-gate acceptance.
