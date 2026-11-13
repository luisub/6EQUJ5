"""PURPOSE: Capture fixture-based annex faction frames through normal key dispatch.
CALLED BY: python -m tools.faction_runtime_audit --output-dir PATH.
HOW TO MODIFY: Disclose fixtures; do not claim the captures establish visual acceptance.
"""
import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

import pygame

from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine


def key(machine, code):
    machine.input.begin_frame()
    machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=code))
    machine.update(1 / 60)
    machine.handle_event(pygame.event.Event(pygame.KEYUP, key=code))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    pygame.init()
    pygame.display.set_mode((480, 270))
    with TemporaryDirectory(prefix='6equj5-faction-audit-') as directory:
        machine = GameStateMachine(CRTRenderer(), development=False,
                                   save_store=SaveStore(directory), settings_store=SettingsStore(directory))
        try:
            machine.start_new_game()
            machine.campaign.apply_event({'event_id': 'capture-fixture', 'type': 'defeat_greenkeeper'})
            key(machine, pygame.K_m)
            field = machine.current_scene
            for index in range(4):
                key(machine, pygame.K_n)
                machine.render()
                native = machine.crt.render_surface.copy()
                for suffix, surface in (('native', native), ('2x', pygame.transform.scale(native, (1920, 1080)))):
                    filename = args.output_dir / f'pair_{index + 1}_{suffix}.png'
                    with filename.open('xb') as stream:
                        pygame.image.save(surface, stream, filename.name)
        finally:
            machine.close()
            pygame.quit()


if __name__ == '__main__':
    main()
