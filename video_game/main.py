"""
═══════════════════════════════════════════════════════
MODULE: video_game/main.py
PURPOSE: Main Pygame entry point and 60 FPS game loop.
CALLED BY: CLI (`python -m video_game.main`) or test_engine_boot.py.
HOW TO MODIFY:
  - To change window title -> edit run_game().
  - To change global CRT toggle hotkey (currently F1) -> edit state_machine.py.
═══════════════════════════════════════════════════════
"""

import argparse
import sys
import pygame
from .engine import config
from .engine.asset_transactions import recover_before_load
from .engine.assets import AssetLoadError
from .engine.crt_renderer import CRTRenderer
from .engine.settings import MAX_SCALE, MIN_SCALE, SettingsStore
from .engine.state_machine import GameStateMachine


def run_game(max_frames=None, *, development=False, target_fps=None):
    """Initialize Pygame window, CRT renderer, and 60 FPS main loop."""
    recover_before_load(config.ASSETS_DIR)
    pygame.init()
    machine = None
    fps = target_fps or config.TARGET_FPS
    try:
        settings_store = SettingsStore()
        settings = settings_store.load()
        window_surface = pygame.display.set_mode((config.RENDER_WIDTH * settings.scale,
                                                   config.RENDER_HEIGHT * settings.scale), pygame.RESIZABLE)
        pygame.display.set_caption("6EQUJ5: THE FERMI OVERRIDE // 1420.4056 MHz")
        clock = pygame.time.Clock()
        crt = CRTRenderer(scale=settings.scale)
        machine = GameStateMachine(crt, development=development, settings_store=settings_store)
        is_running = True
        frame_count = 0
        while is_running:
            machine.input.begin_frame()
            raw_dt = clock.tick(fps) / 1000.0
            # Clamp simulation backlog after stalls to prevent update spiral (DATA_CONTRACTS.md)
            dt_seconds = min(raw_dt, 0.10)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    machine.handle_event(event)
                    is_running = False
                    break
                if event.type in (pygame.VIDEORESIZE, pygame.WINDOWRESIZED):
                    width, height = event.size if event.type == pygame.VIDEORESIZE else (event.x, event.y)
                    scale = max(MIN_SCALE, min(MAX_SCALE, min(width // config.RENDER_WIDTH,
                                                              height // config.RENDER_HEIGHT)))
                    if scale != machine.settings.scale:
                        machine.change_settings(scale=scale)
                    machine.handle_event(event)
                else:
                    machine.handle_event(event)
            if not is_running:
                break
            desired_size = (crt.win_w, crt.win_h)
            if window_surface.get_size() != desired_size:
                machine.input.release_all()
                window_surface = pygame.display.set_mode(desired_size, pygame.RESIZABLE)
            machine.update(dt_seconds)
            machine.render()
            crt.present(window_surface)
            pygame.display.flip()
            frame_count += 1
            if max_frames is not None and frame_count >= max_frames:
                is_running = False
        return frame_count
    finally:
        try:
            if machine is not None:
                machine.close()
        finally:
            pygame.quit()


def main(argv=None):
    """Parse command-line arguments and run the game loop."""
    parser = argparse.ArgumentParser(description="6EQUJ5 game prototype")
    parser.add_argument("--dev", action="store_true", help="Enable development inspection shortcuts")
    args = parser.parse_args(argv)
    try:
        return 0 if run_game(development=args.dev) >= 0 else 1
    except AssetLoadError as exc:
        print(f"Cannot start game: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
