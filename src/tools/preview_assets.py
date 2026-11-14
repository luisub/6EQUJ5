"""
MODULE: src/tools/preview_assets.py
PURPOSE: Export intentional previews of the current bunker and terminal scenes.
CALLED BY: `python -m video_game.tools.preview_assets --output-dir DIRECTORY` and tests.
HOW TO MODIFY: Keep previews on the same scene and renderer paths as the game.
"""

import argparse
import tempfile
from pathlib import Path

import pygame

from video_game.engine import config
from video_game.engine.asset_transactions import recover_before_load
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine


def export_previews(output_dir):
    """Render native bunker and integer-scaled CRT previews into output_dir."""
    recover_before_load(config.ASSETS_DIR)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    pygame.init()
    machine = None
    temporary = tempfile.TemporaryDirectory(prefix="6equj5-preview-settings-")
    try:
        window = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
        crt = CRTRenderer(scale=config.DEFAULT_SCALE)
        machine = GameStateMachine(crt, development=True, settings_store=SettingsStore(temporary.name))
        machine.toggle_timeline()
        machine.change_state(config.STATE_BUNKER_HUB)
        crt.glitch_timer_ms = 0
        crt.is_crt_enabled = False
        machine.render()
        native = output_dir / "pygame_live_960x540_crt_off.png"
        pygame.image.save(crt.render_surface, str(native))
        crt.is_crt_enabled = True
        crt.present(window)
        scaled = output_dir / "pygame_live_1920x1080_crt_on.png"
        pygame.image.save(window, str(scaled))
        machine.change_state(config.STATE_CRT_TERMINAL)
        crt.glitch_timer_ms = 0
        machine.render()
        crt.present(window)
        terminal = output_dir / "pygame_live_crt_terminal.png"
        pygame.image.save(window, str(terminal))
        return native, scaled, terminal
    finally:
        try:
            if machine is not None:
                machine.close()
        finally:
            temporary.cleanup()
            pygame.quit()


def main():
    parser = argparse.ArgumentParser(description="Export game scene previews to a chosen directory.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for the PNG files")
    args = parser.parse_args()
    for path in export_previews(args.output_dir):
        print(path)


if __name__ == "__main__":
    main()

