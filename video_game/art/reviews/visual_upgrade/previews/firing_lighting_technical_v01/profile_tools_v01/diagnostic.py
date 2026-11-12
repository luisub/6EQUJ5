"""PURPOSE: Record the existing fresh-session scene-budget sequence and its timings.
CALLED BY: python diagnostic.py --output-dir NEW_DIRECTORY.
HOW TO MODIFY: Keep the actual profile session, scene sequence, duration and thresholds intact.
"""
import argparse
import json
import os
import sys
from pathlib import Path

from video_game.engine import config
from video_game.tools.profile_game import BenchmarkProfileSession


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    session = BenchmarkProfileSession(scale=config.DEFAULT_SCALE, headless=True)
    try:
        scenes = [config.STATE_BUNKER_HUB, config.STATE_CRT_TERMINAL, config.STATE_SCIENCE_LAB,
                  config.STATE_FIELD_OPS, config.STATE_BOSS_BOUNTY]
        results = {scene: session.run_scene_benchmark(scene, duration_seconds=0.6, simulate_input=True)
                   for scene in scenes}
    finally:
        session.close()
    report = {'argv': sys.argv, 'cwd': os.getcwd(),
              'environment': {key: os.environ.get(key) for key in ('SDL_VIDEODRIVER', 'SDL_AUDIODRIVER', 'SIX_GAME_SAVE_DIR', 'TMPDIR')},
              'results': results, 'limitations': 'Dummy-SDL diagnostic; not native-window performance or gameplay acceptance.'}
    (args.output_dir / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    for scene, result in results.items():
        print(scene, 'render_p95_ms=', result['render_time_ms']['p95'],
              'total_p95_ms=', result['total_frame_time_ms']['p95'])


if __name__ == '__main__':
    main()
