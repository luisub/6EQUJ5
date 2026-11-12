# Content scope and coverage

This file translates the design bible into a finite first-release content inventory. Room counts and ending thresholds are provisional planning defaults recorded in ISSUES_AND_DECISIONS.md.

## Campaign rooms

Each directory below is under `video_game/data/levels/`. Each room has collision, spawns, checkpoint, objective, exits, props and corresponding art references. Room widths are determined during blockout using measured traversal and encounter needs.

| Act | Directory and room filenames | Required progression and boss |
|---|---|---|
| I Ohio Big Ear | `act_01/approach.json`, `salvage_yard.json`, `dish_catwalk.json`, `greenkeeper_arena.json` | Starter movement, scavenging, first contact, lab validation, 72-second defense, Greenkeeper |
| II Neo-Denver | `act_02/blackout_street.json`, `relay_rooftops.json`, `amplifier_station.json`, `array_12_arena.json` | Retrieve amplifier, thermal/EMP encounters, synchronized dish sweeps, Synchronicity |
| III Area 51 | `act_03/salt_flats.json`, `s4_hangar.json`, `telepod_vault.json`, `amalgam_arena.json` | Containment evidence, consensus/probe contact, biological hazard validation, Amalgam |
| IV VLA/Dodleston | `act_04/rail_yard.json`, `rift_array.json`, `dodleston_relay.json`, `architect_arena.json` | Gravity/time contact, timeline geometry and historical relay, Mandela Architect |
| V Göbekli Tepe | `act_05/pillar_approach.json`, `buried_archive.json`, `crust_waveguide.json`, `core_prime_arena.json` | Final evidence dossier, pillar activation, Core Prime and Archon of Silence |
| Flashback | `flashback/ehman_1977.json` | Read printout, mark Wow signal, hide reel, return with anchor |

Bunker stations are available at defined safe transitions. Backtracking has explicit exits and retained objectives. Every act has a recovery checkpoint before its boss. Save before the final deployment choice.

## Civilization mission coverage

Every row requires unique dialogue, a readiness activity, an evidence fragment, an offline path, validation, a reward, repeat behavior, a dossier entry and visual review. Unlock conditions are encoded in civilization_missions.json.

| Civilization | First access | Evidence/validation focus | Gameplay reward |
|---|---|---|---|
| FASR-001 | Act I | Restraint/readiness, formal evidence | Receiver master key and gate coordinates |
| FASR-007 | Act I | False patterns and adversarial skepticism | Decoy beacon |
| FASR-003 | Act II | Energy/waste heat, quantum observation | Thermal visor and maser overcharge |
| FASR-005 | Act II | Coordination and resilience | EMP shielding and music decoy |
| FASR-004 | Act II optional discovery, required before finale | Developing cognition and intervention | Plasma arc with recorded teaching-choice variation |
| FASR-008 | Act III | Seven-voice consensus and uncertainty | Up to three tactical drones |
| FASR-009 | Act III | Archival provenance and robustness | Air dash and ricochet shot |
| FASR-006 | Act III archive access, required before finale | Memory integrity and replication | Timeline anchor/totem |
| FASR-002 | Act IV | Relativity-inspired uncertainty | Local time-dilation field |
| FASR-SCAN-H | Act IV scan discovery | Language/causality framing | Telegraph foresight and one fatal-hit rewind per room |
| FASR-010 | Act V | Cultural memory and evidence synthesis | Pillar resonance and final broadcast access |

Act placements absent from the old plan are implementation defaults. All eleven fragments must have a reachable acquisition path before dossier completion. FASR-004/006 can be recovered later if missed on first access. The Heptapod is discovered through an authored anomaly condition, with a deterministic fallback after repeated eligible scans.

## Required systems and ownership

| Design feature | Tasks |
|---|---|
| Title, bunker, terminal, lab, field, boss and ending scenes | F04, C04, C07, A01, A09, P08 |
| Live dialogue, 12 exchanges, five-phase reception, frequency tuner | C03–C08 |
| Curated fallback and hostile/Core-mimic transmissions | C05, C06, P06 |
| Art for all eleven civilizations and charts | C01, P06 |
| Three Mateo outfits, animation, eight-direction aim | A04, A05, R03 |
| Run/jump, cover, slide-kick | A02, A03 |
| Wall jump, grapple reel, Fibonacci dash, tape-deck disruption | S10 |
| Maser, scattergun, EMP bolas, Fibonacci coilgun | A05, S05 |
| Heptapod logogram projector and civilization powers | S05, P07 |
| Core drones/enforcers/operatives, Static Hounds | A06, S09 |
| Watchers, Chrysalis Splicers, precursor guardians, Temporal Phantoms | S09, P02a, P03a |
| Predictive attack vectors and counterplay | A06, S10 |
| 72-second defense with six intensity bins | A08 |
| Five bosses and two-stage finale | A09, P01c–P04c |
| Quantum, neuro, biosecurity and formal workbenches | C07, S01–S04 |
| Six campaign meters and deployment consequences | F05, S04, P08 |
| Mandela geometry, Dodleston relay, Ehman flashback | S06–S08 |
| Five biome art sets, parallax, weather, particles | A11, A12, P01b–P04b |
| Dynamic lighting, normal/specular maps, optional CRT/VHS effects | C02, R03 |
| Save/load, settings, sound, keyboard/controller, readable UI | F06, F07, A12, R01, R02 |
| Credits, packaged macOS build and verified release | R06–R08 |

R03 evaluates normal/specular lighting on a representative room, then completes maps for assets affected by that lighting. If the measured approach fails performance or visual goals, record the renderer decision and retain the feature as explicitly deferred until the user accepts a scope revision. Avoid silently declaring the full visual scope complete.

## Boss encounter requirements

Greenkeeper has mortar windups, sweeping attacks, exposed weak points and three recoverable phases. Synchronicity rotates dish attack lanes and has safe cover windows. Amalgam teleports between pods with warning cues and interruptible attacks. Mandela Architect switches validated arena geometry and exposes its core through pattern recognition. Core Prime culminates in Archon of Silence and a bounded terminal interaction that suspends or safely shelters combat input.

Each boss has an intro card, phase data, telegraphs, health/death behavior, retry checkpoint, reward event and audio/visual feedback. Tune numbers in balance.json and test reset from every phase.

## Endings and release reachability

Implement Fermi Override, Controlled Peace and Severed Signal under the rules in DATA_CONTRACTS.md. All endings need authored text, consequences of the six meters, audio, credits access and post-ending save behavior. Exact wording is authored in P08.

Create a reachability matrix covering every room exit, mission prerequisite, fragment, validation, ability and ending. Run it against both a fresh campaign and migrated save fixtures. Preserve a full offline completion route and measured live-dialogue sessions.
