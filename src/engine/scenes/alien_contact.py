"""PURPOSE: Present earned, authored information from each alien civilization.
CALLED BY: GameStateMachine after a world guardian victory or pending-contact Continue.
HOW TO MODIFY: Save the receipt before teleporting; retain no-typing offline input.
"""
import pygame
from .. import config
from ..alien_journey import ledger, world_by_id, record_receipt, dispatch
from ..assets import AssetLoadError
from ..ui.dialogue import action as dialogue_action, paginate, render_dialogue
from ..galaxy_transit import display_name
from .base import BaseScene


class AlienContactScene(BaseScene):
    """Short, readable offline conversation with a durable final acknowledgement."""
    def __init__(self, machine):
        super().__init__(machine)
        self.world = None
        self.page = 0
        self.save_pending = False
        self.committed = False
        self.portrait = None
        self.pages = []

    def on_enter(self, **kwargs):
        pygame.key.stop_text_input()
        current = ledger(self.machine.campaign)
        self.world = world_by_id(kwargs.get('world_id'))
        if (not self.world or current.get('stage') != 'contact'
                or current.get('world_id') != self.world['id']
                or not self.machine.campaign.state.room_flags.get(self.world['defeat_flag'], False)):
            self.machine.change_state(config.STATE_BUNKER_HUB)
            return
        self.page = 0
        self.save_pending = False
        self.committed = False
        try:
            self.portrait = self.machine.assets.civilization(self.world['civ_id'], 'face')
        except (AssetLoadError, OSError, pygame.error):
            self.portrait = None
        self.pages = paginate(self.world['contact_pages'], self.machine.crt.font_md,
                              width=274 if self.portrait is not None else 396)
        self.machine.input.release_all()

    def on_exit(self):
        pygame.key.stop_text_input()
        self.machine.input.release_all()

    def _advance(self):
        if not self.world:
            return
        if self.save_pending:
            if not self.machine.save_checkpoint():
                return
            self.save_pending = False
            dispatch(self.machine)
            return
        if self.page + 1 < len(self.pages):
            self.page += 1
            return
        if not self.committed:
            if not record_receipt(self.machine.campaign, self.world):
                return
            self.committed = True
        if not self.machine.save_checkpoint():
            self.save_pending = True
            return
        dispatch(self.machine)

    def handle_event(self, event):
        action = dialogue_action(event, self.machine.crt)
        if action == 'next':
            self._advance()
        elif action == 'back':
            if self.save_pending:
                self._advance()
            else:
                self.machine.change_state(config.STATE_BUNKER_HUB)

    def render(self, crt):
        crt.clear()
        if not self.world:
            return
        final = self.page == len(self.pages) - 1
        destination = self.world.get('next_world') or 'earth'
        name = display_name(destination)
        count = len(ledger(self.machine.campaign).get('receipts', [])) + (0 if self.committed else 1)
        render_dialogue(crt, self.pages[self.page],
                        eyebrow=f'{self.world["civ_id"]} · MESSAGE {count} OF 11',
                        progress=f'{self.page + 1} / {len(self.pages)}',
                        next_label='Record & travel' if final else 'Next',
                        detail=f'Next: {name}' if final else 'Read at your own pace.',
                        save_pending=self.save_pending, portrait=self.portrait)
