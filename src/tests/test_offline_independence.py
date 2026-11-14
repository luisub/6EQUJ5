"""PURPOSE: Verify the receiver does not import or contact the historical AI app.
CALLED BY: pytest tests/test_offline_independence.py.
HOW TO MODIFY: Keep the subprocess isolated with forbidden AI imports and network.
"""
import os
from pathlib import Path
import subprocess
import sys


def test_receiver_starts_and_grants_without_ai_or_network(tmp_path):
    script = '''
import importlib.abc
import socket
import sys

class BlockAI(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'signal_6EQUJ5', 'ollama'} or fullname in {
                'video_game.engine.ai_adapter', 'video_game.engine.ai_worker'}:
            raise AssertionError('Unexpected AI import: ' + fullname)
        return None
sys.meta_path.insert(0, BlockAI())
def no_network(*args, **kwargs):
    raise AssertionError('Unexpected network access')
socket.socket = no_network
import pygame
from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine
pygame.init()
pygame.display.set_mode((960, 540))
game = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(sys.argv[1]),
                        settings_store=SettingsStore(sys.argv[1]))
try:
    game.change_state(config.STATE_CRT_TERMINAL)
    session = game.current_scene.session
    assert session.worker is None and session.is_offline
    assert session.decode_bins == [6, 14, 26, 30, 19, 5]
    ok, _ = session.receive_authored_evidence()
    assert ok and 'FASR-001' in game.campaign.state.extracted_fragments
finally:
    game.close()
    pygame.quit()
'''
    env = dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy',
               SIX_GAME_SAVE_DIR=str(tmp_path))
    result = subprocess.run([sys.executable, '-I', '-c', script, str(tmp_path)],
                            cwd=tmp_path, env=env, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
