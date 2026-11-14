# Art sources

`source/` contains rebuild masters and provenance; `reviews/` contains visual
review material. Runtime exports remain in `src/assets/`. These masters are
excluded from game wheels and source distributions.

This directory moved from `art/` to `src/art/` without changing its existing
files. Historical records may use `art/...` or the older `video_game/art/...`;
resolve either prefix to `src/art/...` in this checkout.

Run maintained builders from the repository root as
`.venv/bin/python -m video_game.tools.<name>`. See the
[developer commands](../tools/README.md) for dry runs, captures and rebuilds.
