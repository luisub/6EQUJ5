# Current state — 2026-11-15

## Repository and validation

This checkout contains the offline game. Flat `src/` installs as `video_game`;
`.venv/bin/6equj5-game` launches it. The legacy AI application is independent.
Runtime resources are in `src/assets/` and `src/data/`; accepted art masters and
recipes are in `src/art/source/`. Tests and tools remain development material.

The shared-lab cleanup consolidated validation rules across four workbenches
and retired two superseded procedural robot generators. The accepted insect
builder remains the sole maintained Earth-enemy export path. Original generators
and previous status reports are preserved with restoration hashes.

See the [current audit](../maintenance/REPOSITORY_AUDIT.md),
[verification results](../maintenance/verification.json) and
[directory map](../maintenance/repository-tree.txt). These own measured results
and inventories; earlier reports are historical evidence. Formal task and gate
statuses remain in the [roadmap](TODO_ROADMAP.md).

## Launch, movement and campaign

Launch shows the title banner, soundtrack and one Press Start action. Starting
replaces the campaign with a fresh basement run; settings persist. Held start
input cannot dismiss the opening. Continue and save recovery are available
through developer APIs; the title has no Continue button.

The opening retains the supplied passage and galaxy briefing. Ohio connects
approach → campus → salvage yard → dish → Greenkeeper. Walk boundaries work in
both directions and combat modes. Collection, science, repair and defense are
optional; NEXT and an empty lab's Continue Outside lead to the field. Leaving
an incomplete defense grants no reward. Space remains jump; R retries defense.

Boss arrivals allow immediate movement and firing. Victories unlock progression;
contacts save their receipts before travel. Seven guardian victories and
receipts unlock the final Core encounter. Both final forms must be defeated.
Existing checkpoint aliases, save migration and New/Continue isolation remain.

## Artwork, combat and travel

All seven alien worlds have distinct panoramas, guardian artwork, local minor
foes and warned charging hazards. Denver retains its Fitzsimons-inspired building
and mountain panorama. World weather and signal particles are bounded and stay
behind actors. Review new art one family at a time.

Temporary weapon timers occupy a compact upper-right panel. Body hits damage
guardians; their exposed recovery core grants bonus damage. Aimed attacks track
airborne targets until release and fire from mirrored weapon sockets. Bolts use
bounded directional trails and launch flashes; mortar ground impacts occur once.
Temporary equipment expires normally. Enemy arrivals are quiet, while attack
warnings remain visible.

Victory destruction is skippable; dialogue pages wait for acknowledgement.
The opening and transit share a seven-stop constellation. Named stars, a moving
ship, earned links and a centered gate/tunnel distinguish the eight travel legs,
including the return to Earth. Travel is immediately skippable,
but arrival requires a successful save and offers retry on failure.

The former first four visited worlds (Sagittarius Signal, Tabby's Star, Proxima
and Orion) and their unique level/art/music families are recoverably archived.
Every Earth scene and shared receiver/science catalog remains active. A validated
legacy journey resumes at the first retained stop when necessary and filters
retired receipts while preserving retained victories, later checkpoints and
finale/park progress. Missing victories or invalid receipt order remain blocked.

## Science workbenches

Formal, quantum, connectome and biosecurity labs share catalog loading, workflow
step constants, claim classification, evidence checks, replication and completed
record lookup in `src/engine/labs/validation.py`. Each lab retains its experiment,
evidence-unlock rules, scenario reset, deployment rewards and feedback. Existing
workbench classes, step imports and loader entry points remain available.

## World soundtracks and README refresh

Every signal world has its own instrumental theme. Exploration, guardian combat
and earned contact share that world's score without restarting it. Arrival fades
to the next theme; missing tracks fall back to Earth music. New game returns to
the bunker score. Volume, mute and main-thread mixer ownership remain intact.

The README is for players: premise, installation, controls and selected gameplay
previews. It labels promotional art, discloses staged scenes and hides ending
spoilers. The [media notes](../media/readme/README.md) retain the full capture
collection, metadata and reproducible commands. Original soundtrack scores and
rebuild recipes remain outside the runtime package.

## Core liberation and restored Denver

The final chamber uses an original green projected Core and machine-cathedral
panorama with bounded falling code. Its two full-health forms and earned victory
flag remain intact. Six closing pages explain the independent broadcast,
disconnection of the Core's control network and restored local control of city
services. Mateo explicitly confirms that they saved the world.

Completion opens a walkable Central Park, Denver, three springs later. Trees,
water, light, birds and animated families surround Mateo. Four aftermath pages
save each acknowledgement; the park stays open for walking, message replay or
explicit title exit. The terrestrial-memory score returns for the homecoming.
Completed recovery resumes the saved park page through the bunker; New game
resets it. Page-save and final-completion failures retain durable progress for
retry. See [the story and ending](../STORY.md).

## Enemy facing and Earth cyber-insects

All campaign bosses and Greenkeeper follow Mateo's side, including overhead
crossings. Cached mirrors keep bodies, hit flashes, weak points, mortar anchors
and destruction fragments aligned. Directional attacks work on either side;
warned sweeps and charges retain matching committed body and attack directions.
The next attack reacquires Mateo. Retry resets facing.

Recurring cover, slide and directional-movement banners are removed. Boss health
bars use a compact warning symbol instead of repeated lock-on banners. Interaction
buttons, brief checkpoints, damage/hazard cues and save failures remain visible.

Nine Earth combat roles use Wasp, Beetle and Mantis families with four registered
poses. Grounded strides follow distance; flight follows actor time. Stopped,
stunned or paused ground insects do not step. Raptors, Resonance Effigies and
Beacon Mites also use distance-driven leg cycles. Existing combat IDs, collision
sizes, rewards and progression remain. All seven guardians retain their own art.

`build_cyber_insects` rebuilds the accepted Earth enemies from preserved masters.
The retired robot generators are historical source only; running them against
current assets would overwrite accepted art. The [asset guide](../ASSETS.md)
describes canonical ownership and supported procedural fallbacks.

## Remaining work and evidence

Armed airborne poses, guardian motion polish, human fairness/full-playthrough
review, audible quality, physical controllers and native-display performance
remain open. Windows and Linux playtesting is pending. Automated checks and
staged captures do not establish these acceptance criteria or promote formal
gates. The existing render-budget threshold remains unchanged.

Earlier chronology and measurements remain in the [progress log](PROGRESS_LOG.md)
and archived reports indexed by the [restoration manifest](../maintenance/archive-manifest.json).
The immediately preceding current-state snapshot is preserved under
`_trash/2026-11-15_repository_cleanup/before/docs/planning/CURRENT_STATE.md`.
