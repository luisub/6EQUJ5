# Current prototype controls

Launch from the repository with `/opt/anaconda3/envs/6equj5_game/bin/python -m video_game.main`, or install the game extra and use `6equj5-game`. Python 3.12 is the tested game runtime. `--dev` enables optional inspection shortcuts; none of the controls below requires it.

| Context | Controls |
|---|---|
| Title | Follow New/Continue/Backup prompts; replacement confirmation protects existing saves |
| Bunker | A/D or arrows move; E/Enter interacts at nearby station; Tab opens/closes dossier; Up/Down scroll one row, PageUp/PageDown scroll eight rows, Esc closes dossier; F5 save; M reality annex after Act I completion |
| Field and boss | A/D or Left/Right move; W/Up/Space jump; S/Down/C crouch or slide while moving; X/J/Left Ctrl fire, hold/release charges; Q/1 cycle unlocked weapons |
| Abilities | R/2 cycle unlocked abilities; K/Left Alt activate; Shift dash; G grapple/release near an anchor |
| Receiver | Type and Enter; channels 1–3 use authored mission rules in either online/offline mode; Tab target; Up/Down transcript; `/choices`, `/offline`, `/reconnect`; `/restart` opens another 12-exchange session while preserving evidence |
| Laboratory | Up/Down/Tab select scenario; 1–4 configure/answer; Space experiment; Enter verify/advance; 1–2 deploy/withhold; H full prompt/details, Up/Down or PageUp/PageDown scroll eight rows, H/Enter/Esc close |
| Defense | E near feedhorn clears jam; R retries failed defense; kill enemies to stop integrity pressure; pause freezes the 72-second timer |
| Boss retry | R after player death; encounter stays stopped until retry or Esc exit |
| Reality annex | T attempts safe timeline swap; F6 relay room; F7 1977 flashback; F8 annex; N cycles four bounded faction pairs; Esc bunker |
| Relay room | E near terminal opens panel; Left/Right select messages; Up/Down scroll one row, PageUp/PageDown scroll six rows; 1–2 available historical actions; R recovery; E/Esc close panel |
| 1977 flashback | E twice at printer to inspect/annotate; E twice at vault to retrieve reel/lock anchor and return; Esc closes printout or returns safely; combat suppressed |
| General | F2 pause/settings; F1 CRT toggle; focus loss pauses and releases movement |

The reality annex and relay/flashback links are prototype access to Milestone 3 mechanics. The full later-act campaign is still planned. Weapon/ability unlocks derive from saved validation and event records. New/Continue reconstructs temporary actors, projectiles, energy and cooldowns; room edits, collected pickups, relay flags, validated scenarios and rewards persist. Incomplete lab trials reset on changing scenario or leaving the lab. Returning to the bunker delivers one pending science consequence notice per visit. Continue starts safely in the bunker.

For disposable testing set `SIX_GAME_SAVE_DIR` to a temporary directory. Real audio, graphical performance and full fresh-save campaign playthrough are separate acceptance checks; headless tests do not establish them.

In the reality annex, N places the next pair only where the active timeline has safe space and support. If no pair can be placed, a warning appears and the current encounter remains. A successful cycle clears existing encounter projectiles.
