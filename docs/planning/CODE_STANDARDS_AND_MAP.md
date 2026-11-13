# Code standards and file map

The current game uses the flat `src/` layout, installed as `video_game`. The legacy AI application is a separate repository. This map describes existing files; historical task cards may name planned or retired modules.

Coding conventions and checks are in [CONTRIBUTING.md](../../CONTRIBUTING.md). See [architecture](../ARCHITECTURE.md) for package boundaries.

## Runtime ownership

| File or directory | Responsibility |
|---|---|
| [main.py](../../src/main.py) | Window, clock, events, shutdown and CLI |
| [config.py](../../src/engine/config.py) | Shared paths, display dimensions and defaults |
| [state_machine.py](../../src/engine/state_machine.py) | Shared services, deferred scene transitions, New/Continue |
| [scenes/](../../src/engine/scenes/) | Title, bunker, receiver, lab, field, boss, alien contact and transit |
| [input.py](../../src/engine/input.py), [settings.py](../../src/engine/settings.py) | Mapped actions, focus, controllers and preferences |
| [campaign.py](../../src/engine/campaign.py), [save_game.py](../../src/engine/save_game.py) | Persistent state, validated events, atomic saves and recovery |
| [campaign_route.py](../../src/engine/campaign_route.py), [alien_journey.py](../../src/engine/alien_journey.py) | Earth routes, alien order, guardian progress and information receipts |
| [world.py](../../src/engine/world.py), [player.py](../../src/engine/player.py) | Rooms, camera, collision and movement |
| [weapons.py](../../src/engine/weapons.py), [temporary_weapons.py](../../src/engine/temporary_weapons.py), [abilities.py](../../src/engine/abilities.py) | Combat, pickups and abilities |
| [enemies.py](../../src/engine/enemies.py), [bosses/](../../src/engine/bosses/), [planet_encounters.py](../../src/engine/planet_encounters.py), [world_hazards.py](../../src/engine/world_hazards.py) | Enemy behavior, bosses and hazards |
| [contact_session.py](../../src/engine/contact_session.py), [protocols.py](../../src/engine/protocols.py), [labs/](../../src/engine/labs/) | Offline conversations, evidence and science |
| [field_reality.py](../../src/engine/field_reality.py), [mandela_world.py](../../src/engine/mandela_world.py), [temporal_relay.py](../../src/engine/temporal_relay.py), [flashback.py](../../src/engine/flashback.py) | Timeline, relay and flashback behavior |
| [assets.py](../../src/engine/assets.py), [asset_transactions.py](../../src/engine/asset_transactions.py) | Resource cache, validation and safe asset promotion |
| [crt_renderer.py](../../src/engine/crt_renderer.py), [animation.py](../../src/engine/animation.py), [ui/](../../src/engine/ui/) | Rendering, animation and interface |
| [campaign_scenery.py](../../src/engine/campaign_scenery.py), [native_room_assets.py](../../src/engine/native_room_assets.py) | Room backgrounds and activity |
| [audio.py](../../src/engine/audio.py) | Music, sound channels and volume |
| [data/](../../src/data/) | Campaign, balance, dialogue, levels and journey definitions |
| [assets/](../../src/assets/) | Exported runtime resources and manifests |

## Dependency direction

The entry point owns the main loop. The state machine owns shared services and scenes. Scenes coordinate domain modules; domain modules use validated content. Builders consume repository-level source art and produce runtime exports. Runtime code must not depend on builders, the checkout's working directory or the sibling AI application.

Keep Pygame display, event and surface operations on the main thread. The audio manager may read bytes in the background, but mixer operations remain on the main update thread.

`Campaign` owns persistent mutations. Scene changes go through the state machine. The field and boss scenes share input mapping, arsenal and ability rules. When moving between rooms or pausing, clear transient input and traversal without discarding durable progress.

## Developer material

| Location | Purpose |
|---|---|
| [tests/](../../tests/) | Behavior, input, persistence, content and rendering checks |
| [tools/](../../tools/) | Maintained builders, validators, capture tools and profiling |
| [art/source/](../../art/source/) | Rebuild masters and provenance |
| [art/palettes/](../../art/palettes/) | Palette definitions |
| [docs/](../) | Public documentation and development records |
| `_temp/`, `captures/`, `profiles/` | Ignored generated output |
| `_trash/` | Ignored recovery archive with restoration records |

Use Python 3.12 in the local `.venv`. Run tools as `python -m tools.<name>` from the repository root. Wheels contain runtime code and resources; they exclude developer material and local assistant instructions.

Some modules are large. Split by responsibility only when the change needs it, preserving callers and behavior. Avoid parallel implementations and wrappers that merely rename existing interfaces.
