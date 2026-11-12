"""
MODULE: video_game/engine/scenes/base.py
PURPOSE: Define the shared scene lifecycle.
CALLED BY: The state machine and game scenes.
HOW TO MODIFY: Keep lifecycle methods lightweight and use seconds for updates.
"""


class BaseScene:
    """Base interface for all game scenes."""

    def __init__(self, machine):
        self.machine = machine

    def on_enter(self, **kwargs):
        pass

    def on_exit(self):
        pass

    def handle_event(self, event):
        pass

    def update(self, dt_seconds):
        pass

    def render(self, crt):
        pass
