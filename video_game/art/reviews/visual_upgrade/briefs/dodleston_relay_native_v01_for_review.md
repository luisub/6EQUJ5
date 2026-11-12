# Dodleston relay vault — shared timeline background v01

**Status: draft for review.** One existing prototype room, one state-neutral backdrop. Generate only after the current annex source has been reviewed and the director coordinates the next artist request. This is a bounded art component, not a new room, geometry change or acceptance of the full scene.

## Identity and exact framing

An enclosed historical relay vault: weighty masonry and concrete, an old communications rack and recessed analog signal equipment, orderly conduits, and a few deep structural recesses. Give the room a distinctive archival communications character, not the annex test corridor or the 1977 observatory. Shape broad near-black cool shadows against selective warm practical light on masonry and metal. The image should feel richly authored but keep the player's lane and changing game objects legible. No decorative controls that promise a new interaction, text or date labels, new exits, floor breaks, ladders, cover, platforms or hazards. Keep long high-contrast horizontal edges from looking walkable.

`data/levels/act_04/dodleston_relay.json` defines a **480×288 world-unit** room. The 480×270 logical viewport is rendered at density 2. Make one opaque **960×576 native PNG**, world-fixed at native `(0,0)`, ratio 1, finite and nonrepeating. Camera x is 0; camera y is 0–18 world units. The viewport samples `(0, 2×camera_y, 960, 540)`, so check both source y=0 and y=36. Preserve the existing field camera and HUD. `1985` and `2031` identify relay-message eras; they are not additional playable room images.

## Existing states and authored anchors

Use `previews/prototype_geometry_research_v01/capture_v01/relay_2029_CORE_geometry_960x576.png` and `relay_1977_ANALOG_geometry_960x576.png`, plus the matching fixtures and their context. Annotated rectangles indicate authored bounds, not necessarily separately rendered sprites. World coordinates below are logical, not native; multiply by two for source placement.

- The relay terminal is authored at `(96,192,16,32)` and the existing E interaction operates near x=96. A modest, static background communications workstation can visually contextualize that interaction, but do not bake its text, active state, action prompts or a second functional terminal into the backdrop. The current generic object render does not itself prove a separate terminal sprite.
- The bulkhead at `(256,192,16,48)` changes state; do not paint a closed door, open portal, lock indicator or false doorway underneath it. Keep its silhouette distinct against a recessed wall.
- The coolant junction is authored at `(160,208,16,16)`. In the initial 2029 layout the hazard cells span x=160–240 at y=224, while the 1977 layout has one-way cells there. Relay actions can drain or rupture coolant and mutate those cells. Keep that entire region quiet and neutral: no baked coolant, grating, siren, damage or drained/ruptured state.
- The cassette pickup at `(384,208,16,16)` is initially unspawned in 2029, can become available, and can be collected. Do not paint a cassette or a permanent highlight there. The exit `(16,192,32,48)`, existing floor y=240, player, visual effects, timeline transition and HUD remain unchanged.

The terminal panel and its messages/actions are runtime overlays; its large logical panel `(10,52,460,190)` covers much of the scene while open. Preserve its readability and scrolling. Show no invented message, powered/unpowered result, warning, progression state or cassette location as static art. The two timeline layouts and each puzzle state must remain visually and mechanically distinct through the existing runtime layers.

## Integration boundary and acceptance

`FieldOpsScene` uses `FieldReality` and `MandelaWorld.render` here. A later room-specific hook must replace only `Room.render_background` for a valid family, retain the actual timeline tiles, mutated geometry, dynamic objects, weather and transition, actor/projectile depth, terminal panel and HUD, and fall back to the existing background when absent or invalid. The ordinary field-family hook alone does not establish this route. No object, puzzle, save, collision, camera or level-length changes are part of this artwork.

Preserve the generated original, dimensions, alpha, prompt and SHA-256; only after source review derive `relay_shared_background_v01_960x576.png` with a disclosed proportional crop/resample. Do not fabricate artwork procedurally or cut mask-shaped holes. Register actual y=0/18 views at native 960 and nearest 1920 for both timelines; exercise terminal E open/close and scrolling, initial/drained/ruptured coolant, locked/open bulkhead and cassette absent/spawned/collected, with state injection labeled when used. Verify real input, safe/blocked timeline switching, save/Continue, collision, HUD and fallback with relevant tests. Static fixtures do not prove complete playthrough, performance, art-gate or human acceptance.
