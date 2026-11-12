# Current prototype controls

Launch from the repository with `/opt/anaconda3/envs/6equj5_game/bin/python -m video_game.main`, or install the game extra and use `6equj5-game`. Python 3.12 is the tested game runtime. `--dev` enables optional inspection shortcuts; none of the controls below requires it.

**Easier combat:** Restart the game to load the update. If you already have settings, open **F2 → COMBAT → ASSISTED** and resume; existing settings remain on Classic. Fresh settings default to Assisted. The chosen profile persists. In field and boss scenes, point with the mouse and hold the left button to repeat the starter maser; hold and release the right button for a charged shot. The X/J/Left Ctrl keyboard fire/charge action remains available. Other unlocked weapons keep their own firing and charging behavior.

| Context | Controls |
|---|---|
| Title | Follow New/Continue/Backup prompts; replacement confirmation protects existing saves |
| Bunker | A/D or arrows move; E/Enter interacts at nearby station; Tab opens/closes dossier; Up/Down scroll one row, PageUp/PageDown scroll eight rows, Esc closes dossier; F5 save; M reality annex after Act I completion |
| Field and boss | A/D or Left/Right move; W/Up/Space jump; S/Down/C crouch or slide while moving; mouse aim, left button repeats starter-maser shots, right button charges/releases; X/J/Left Ctrl fire/charge; Q/1 cycle unlocked weapons |
| Abilities | R/2 cycle unlocked abilities; K/Left Alt activate; Shift dash; G grapple/release near an anchor |
| Receiver | Type and Enter; channels 1–3 use authored mission rules in either online/offline mode; Tab target; Up/Down transcript; `/choices`, `/offline`, `/reconnect`; `/restart` opens another 12-exchange session while preserving evidence |
| Laboratory | Up/Down/Tab select scenario; 1–4 configure/answer; Space experiment; Enter verify/advance; 1–2 deploy/withhold; H full prompt/details, Up/Down or PageUp/PageDown scroll eight rows, H/Enter/Esc close |
| Defense | E near feedhorn clears jam; R retries failed defense; kill enemies to stop integrity pressure; pause freezes the 72-second timer |
| Boss retry | R after player death; encounter stays stopped until retry or Esc exit |
| Reality annex | T attempts safe timeline swap; F6 relay room; F7 1977 flashback; F8 annex; N cycles four bounded faction pairs; Esc bunker |
| Relay room | E near terminal opens panel; Left/Right select messages; Up/Down scroll one row, PageUp/PageDown scroll six rows; 1–2 available historical actions; R recovery; E/Esc close panel |
| 1977 flashback | E twice at printer to inspect/annotate; E twice at vault to retrieve reel/lock anchor and return; Esc closes printout or returns safely; combat suppressed |
| General | F2 or controller Start pauses/settings; F1 toggles CRT; focus loss pauses and cancels held input and charging |

**Mapped controller:** Left stick or D-pad moves; right stick aims; RT repeats starter-maser shots, LT charges/releases. A jumps, B dashes, X interacts, Y grapples, LB cycles weapons, RB activates the selected ability, and Start pauses. Back opens the bunker dossier. Controller A can start/continue on the title screen; D-pad/A/B navigate the supported pause and bunker dossier controls. The pause settings can also be clicked with the mouse. Free-text receiver interaction and advanced panels still need the keyboard. Controller events have been tested with simulated devices; physical hardware compatibility and a controller-only playthrough remain unverified.

The on-screen reticle and projectiles show angled aim; the current Mateo sprite faces left or right and does not yet have a separate angled weapon pose. Opening a modal, losing focus or disconnecting a controller cancels interrupted charging rather than releasing a shot.

The reality annex and relay/flashback links are prototype access to Milestone 3 mechanics. The full later-act campaign is still planned. Weapon/ability unlocks derive from saved validation and event records. New/Continue reconstructs temporary actors, projectiles, energy and cooldowns; room edits, collected pickups, relay flags, validated scenarios and rewards persist. Incomplete lab trials reset on changing scenario or leaving the lab. Returning to the bunker delivers one pending science consequence notice per visit. Continue starts safely in the bunker.

For disposable testing set `SIX_GAME_SAVE_DIR` to a temporary directory. Real audio, graphical performance and full fresh-save campaign playthrough are separate acceptance checks; headless tests do not establish them.

In the reality annex, N places the next pair only where the active timeline has safe space and support. If no pair can be placed, a warning appears and the current encounter remains. A successful cycle clears existing encounter projectiles.
