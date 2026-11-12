# F05 authoritative campaign state evidence

Date 2026-11-10, America/Denver. Environment: macOS arm64; Python 3.12.16 from `/opt/anaconda3/envs/6equj5_game`, pygame-ce 2.5.8, pytest 9.2.0. Rendering and simulated input used dummy SDL video/audio; no real-window or controller playthrough was performed.

## Outcome

Created `engine/campaign.py` and `data/campaign.json`. The game now creates a validated campaign owner with stable string identifiers, the starter maser, the initial mission-access flag and the six existing starting meters. Its fresh state has no contacted civilization, extracted fragment or validation record. `seeded_development_campaign()` explicitly creates the former FASR-001-style progressed fixture and does not affect new games.

`Campaign.apply_event` validates identified, content-defined events and prerequisites against a staged copy before committing. Applied event IDs make retries idempotent, one-shot grant event types cannot pay again under another ID, and bounded integer meter deltas clamp the resulting meters to 0–100. A fragment requires its registered civilization contact; a validation record requires its registered fragment, scenario version and claim. Invalid IDs, malformed events and unmet prerequisites leave prior state unchanged. Snapshots and legacy mapping reads are detached from the owner. Canonical JSON-compatible snapshots use string act, room, checkpoint and meter IDs; legacy reads retain integer act names, display meter labels and `validated_protocols` during migration.

The bunker and HUD read from the owner, and the existing timeline shortcut submits uniquely identified `timeline_shift` events. F05 supplies no production contact, fragment or validation grant events: the contact and validation tasks must define actual gameplay evidence and rewards. The explicit development validation scenario is a fixture and does not represent a scientific result. Only the bunker room and initial checkpoint are registered so far; further content registrations belong to their owning tasks. Actual save files, recovery and migration are F06 work; the tested JSON round trip is in memory.

Changed `engine/config.py`, `engine/state_machine.py`, `engine/scenes/bunker.py`, `engine/ui/hud.py`, `tests/test_engine_boot.py`; added `engine/campaign.py`, `data/campaign.json`, and `tests/test_campaign.py`. Updated campaign contracts, roadmap, handoff, progress, issue and archive records. No existing asset or source file was retired. A [verified pre-F05 snapshot manifest](../../../../_trash/2026-11-10_F05_before_changes_manifest.json) records 12 original paths and hashes, archive hash and recovery instructions; the local snapshot is not an independent backup.

## Verification

Working directory `/Users/nzlab-la/Desktop/Github/6EQUJ5`:

```sh
/opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests -q
# 47 passed in 3.04s
/opt/anaconda3/envs/6equj5_game/bin/python -m pytest tests -q
# 20 passed in 0.01s
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m video_game.engine.preview_assets --output-dir video_game/planning/evidence/F05/2026-11-10_campaign/previews
# Exit 0; three PNGs written.
```

Tests cover the unseeded starter state, explicitly seeded fixture, detached copies, compatibility reads, invalid state and event IDs, invalid validation scenario/claim, unmet prerequisites, atomic failure after staging, unique event retries, same one-shot event under different IDs, meter limits at 0 and 100, and a JSON snapshot round trip with replay protection. Test-only data defines the contact → fragment → validation chain; it is not loaded by normal play. The normal six-scene smoke test verifies fresh rewards are empty and two timeline changes apply as distinct events.

The [state trace](state_trace.json) records a new-game snapshot, rejection of a premature test-only fragment event without mutation, bounded meter changes, duplicate-event results, and a subsequent valid test-only fragment. SHA-256 hashes of all 122 active asset files matched the [F02 baseline inventory](../../F02/2026-11-10_checkpoint/assets_before.sha256) after checks. The pre-change archive and all 12 member hashes were reverified.

Inspected the [native bunker](previews/pygame_live_480x270_crt_off.png), [3× bunker](previews/pygame_live_1440x810_crt_on.png), and [terminal](previews/pygame_live_crt_terminal.png). Mateo, equipment, HUD, portrait and chart remain in the expected positions. All three images have RGB pixels identical to F04. The existing `30s` terminal label remains I10; these captures do not establish final art or motion quality.

## Limitations and cleanup

No failures remain in F05. No production files were retired; only the verified local snapshot, test trace, and preview evidence were retained. The workspace is untracked and the snapshots share its device (I11); an independent backup or version-control strategy remains open. Actual saves are not implemented, real contact/evidence rules remain C06/C07, and real-window input, audio, live inference, power loss and non-macOS platform behavior remain unverified. No special hardware was needed for this increment.
