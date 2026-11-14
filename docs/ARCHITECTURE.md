# Architecture

`src/` is mapped to the installed Python package `video_game`. There is no nested `src/video_game` folder and no dependency on the AI repository.

| Location | Ownership |
|---|---|
| src/main.py | Game entry point and bounded runtime loop |
| src/engine | Scenes, mapped input, physics, combat, receiver, science and persistence |
| src/assets | Exported runtime images, audio, fonts and asset manifests |
| src/data | Authored campaign, dialogue, levels, opening and journey data |
| tests | Unit, mapped-input, persistence and regression tests |
| src/tools | Maintained builders, validators, captures and profiling commands |
| src/art/source | Unique rebuild masters, civilization text and provenance |
| docs | Current controls, architecture, planning and migration records |
| _trash | Ignored historical implementations, captures and recovery copies |

`Campaign` is the persistent-state authority. `SaveStore` retains envelope version 2 and earlier-save migration, using the existing platform user-data location; tests override it with `SIX_GAME_SAVE_DIR`.

The receiver resolves authored dialogue locally. Its small codec retains the historical six-bin 6EQUJ5 decoding rules. No live model adapter, worker or network service participates in progression.

Runtime assets and authored data are resolved relative to package files, so the installed wheel runs outside the checkout. Developer tools resolve repository-level art masters and are intentionally excluded from runtime wheels. A source checkout with art masters is required for art rebuilds; the source distribution supports rebuilding the runtime wheel.
