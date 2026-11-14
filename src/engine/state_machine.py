"""
MODULE: video_game/engine/state_machine.py
PURPOSE: Route six scenes, lifecycle transitions, shared assets and campaign state.
CALLED BY: main.py and the preview command.
HOW TO MODIFY: Defer scene changes during callbacks and retain compatibility exports.
"""

import pygame
from dataclasses import replace
from uuid import uuid4
from . import config
from .assets import AssetCache
from .audio import AudioManager
from .input import InputManager
from .save_game import SaveError, SaveStore
from .settings import SettingsError, SettingsStore
# Preserve the old state_machine imports while scenes move to their own modules.
from .scenes.base import BaseScene
from .scenes.title import TitleBootScene
from .scenes.bunker import BunkerHubScene, MILESTONE_CIVS
from .scenes.terminal import CRTTerminalScene
from .scenes.lab import ScienceLabScene
from .scenes.field import FieldOpsScene
from .scenes.boss import BossScene
from .scenes.alien_contact import AlienContactScene
from .scenes.galaxy_transit import GalaxyTransitScene
from .scenes.restored_earth import RestoredEarthScene
from .ui.hud import render_global_hud
from .ui.pause import PauseOverlay


class SimplePlaceholderScene(BaseScene):
    """Scene view for Science Lab, Field Ops, and Boss Arena."""

    def __init__(self, machine, title, subtitle, accent_color, hud_label):
        super().__init__(machine)
        self.title, self.subtitle, self.accent_color, self.hud_label = title, subtitle, accent_color, hud_label

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            self.machine.change_state(config.STATE_BUNKER_HUB)

    def render(self, crt):
        crt.clear(config.COLOR_VOID_BLACK)
        crt.draw_panel((24, 28, 432, 212), bg_color=(6, 14, 10), border_color=self.accent_color, title=self.title)
        crt.draw_text(self.subtitle, 38, 54, color=self.accent_color, size="md")
        self.machine.render_global_hud(crt, location_label=self.hud_label)


class GameStateMachine:
    """Coordinate scene lifecycle and apply requested transitions after dispatch."""

    def __init__(self, crt, save_store=None, *, development=False, settings_store=None):
        self.crt = crt
        self.development = development
        self.save_store = save_store if save_store is not None else SaveStore()
        self.settings_store = settings_store if settings_store is not None else SettingsStore(self.save_store.directory)
        self.settings = self.settings_store.load()
        self.settings_notice = self.settings_store.warning
        self.crt.is_crt_enabled = self.settings.crt_effects
        if self.crt.scale != self.settings.scale:
            self.crt.set_scale(self.settings.scale)
        self.audio = AudioManager()
        self.audio.set_master_volume(self.settings.volume / 100.0)
        self.input = InputManager()
        self.input.initialize_controllers()
        self._charge_generation = self.input.charge_reset_generation
        self._suppress_charge_until_neutral = False
        self.pause = PauseOverlay(self)
        self.campaign = config.default_campaign_state()
        self.session_active = False
        self.save_notice = ""
        self.assets = AssetCache(config.ASSETS_DIR)
        self._dispatching = False
        self._pending = None
        self._closed = False
        self.scenes = {
            config.STATE_TITLE_BOOT: TitleBootScene(self),
            config.STATE_BUNKER_HUB: BunkerHubScene(self),
            config.STATE_CRT_TERMINAL: CRTTerminalScene(self),
            config.STATE_SCIENCE_LAB: ScienceLabScene(self),
            config.STATE_FIELD_OPS: FieldOpsScene(self),
            config.STATE_BOSS_BOUNTY: BossScene(self),
            config.STATE_ALIEN_CONTACT: AlienContactScene(self),
            config.STATE_GALAXY_TRANSIT: GalaxyTransitScene(self),
            config.STATE_RESTORED_EARTH: RestoredEarthScene(self),
        }
        self.current_state_name = config.STATE_TITLE_BOOT
        self.current_scene = self.scenes[self.current_state_name]
        self.current_scene.on_enter()
        self.audio.transition_scene_music(self.current_state_name)

    def change_state(self, new_state_name, **kwargs):
        if new_state_name not in self.scenes:
            raise KeyError(f"Unknown game scene: {new_state_name}")
        if self._closed:
            raise RuntimeError("Cannot transition a closed state machine")
        self._pending = (new_state_name, kwargs)
        if not self._dispatching:
            self._apply_transition()

    def _apply_transition(self):
        while self._pending is not None:
            state, kwargs = self._pending
            self._pending = None
            self._dispatching = True
            try:
                previous = self.current_state_name
                if (self.session_active and previous == config.STATE_BUNKER_HUB and state != previous
                        and not self.save_checkpoint()):
                    return
                self.input.release_all()
                self._release_scene_controls()
                self.current_scene.on_exit()
                self.current_state_name = state
                self.current_scene = self.scenes[state]
                self.current_scene.on_enter(**kwargs)
                if state == config.STATE_BUNKER_HUB and previous != state:
                    field_player = getattr(self.scenes.get(config.STATE_FIELD_OPS), 'player', None)
                    set_profile = getattr(field_player, 'set_combat_assisted', None)
                    recover = getattr(field_player, 'recover_health_at_safe_hub', None)
                    if set_profile is not None and recover is not None:
                        set_profile(self.settings.combat_mode == 'assisted')
                        recover()
                world_id = getattr(self.current_scene, 'journey_world', None)
                if state == config.STATE_ALIEN_CONTACT and self.current_scene.world:
                    world_id = self.current_scene.world['id']
                self.audio.transition_scene_music(state, world_id=world_id)
                if (self.session_active and state == config.STATE_BUNKER_HUB
                        and previous not in (config.STATE_TITLE_BOOT, config.STATE_BUNKER_HUB)):
                    self.save_checkpoint()
                # Transit uses a restrained animation rather than abrupt glitch flashes.
                if state != config.STATE_GALAXY_TRANSIT and previous != config.STATE_GALAXY_TRANSIT:
                    self.crt.trigger_glitch(duration_ms=140, intensity=3)
            finally:
                self._dispatching = False

    def toggle_timeline(self):
        target = "1977_ANALOG" if self.campaign.timeline_mode == "2029_CORE" else "2029_CORE"
        self.campaign.apply_event({"event_id": uuid4().hex, "type": "timeline_shift", "payload": {"timeline_mode": target}})
        if self.session_active and self.current_state_name == config.STATE_BUNKER_HUB:
            self.save_checkpoint()
        self.crt.trigger_glitch(duration_ms=280, intensity=6)

    def start_new_game(self, *, replace_existing=False, show_opening=False, opening_guard=None):
        if self.save_store.has_existing_data() and not replace_existing:
            return False, "CONFIRM NEW GAME FIRST"
        campaign = config.default_campaign_state()
        try:
            self.save_store.save(campaign, replace_invalid=replace_existing)
        except SaveError as exc:
            return False, f"SAVE FAILED: {exc}"
        self.campaign = campaign
        self._reset_session_scenes()
        if hasattr(self, "contact_session") and self.contact_session is not None:
            self.contact_session.campaign = self.campaign
        self.session_active = True
        self.save_notice = "NEW GAME SAVED"
        self.change_state(config.STATE_BUNKER_HUB, show_opening=show_opening, opening_guard=opening_guard)
        return True, "NEW GAME SAVED"

    def continue_game(self, *, recover=False):
        result = self.save_store.recover_backup() if recover else self.save_store.load()
        if result.status != "ok":
            return result
        self.campaign = result.campaign
        self._reset_session_scenes()
        if hasattr(self, "contact_session") and self.contact_session is not None:
            self.contact_session.campaign = self.campaign
        self.session_active = True
        self.save_notice = "BACKUP RESTORED" if recover else "SAVE LOADED"
        self.change_state(config.STATE_BUNKER_HUB)
        return result

    def save_checkpoint(self):
        if not self.session_active:
            return False
        field = self.scenes.get(config.STATE_FIELD_OPS)
        if field is not None:
            field.reality.persist()
        try:
            self.save_store.save(self.campaign)
        except SaveError as exc:
            self.save_notice = f"SAVE FAILED - F5 RETRY: {exc}"
            return False
        self.save_notice = "CHECKPOINT SAVED"
        return True

    def change_settings(self, **changes):
        previous_combat_mode = self.settings.combat_mode
        try:
            updated = replace(self.settings, **changes)
            self.settings_store.save(updated)
        except (SettingsError, TypeError) as exc:
            self.settings_notice = "SETTINGS NOT SAVED"
            self.settings_store.warning = str(exc)
            return False
        self.settings = updated
        if updated.combat_mode != previous_combat_mode:
            self.input.release_all()
            self._release_scene_controls()
        self.settings_notice = "SETTINGS SAVED"
        self.crt.is_crt_enabled = updated.crt_effects
        if self.crt.scale != updated.scale:
            self.input.release_all()
            self.crt.set_scale(updated.scale)
        self.audio.set_master_volume(updated.volume / 100.0)
        return True

    def open_pause(self):
        self.input.release_all()
        self._release_scene_controls()
        if self.current_state_name == config.STATE_CRT_TERMINAL:
            pygame.key.stop_text_input()
        self.pause.open()

    def _release_scene_controls(self):
        for scene in self.scenes.values():
            player = getattr(scene, "player", None)
            weapon = getattr(player, "weapon", None)
            cancel_charge = getattr(weapon, "cancel_charge", None)
            if cancel_charge is not None:
                cancel_charge()
            if player is not None and hasattr(player, "discard_pending_edges"):
                player.discard_pending_edges()
            if hasattr(scene, "keys_held"):
                scene.keys_held.clear()
            for name in ("_jump_pressed", "_jump_released", "_fire_pressed", "_fire_released"):
                if hasattr(scene, name):
                    setattr(scene, name, False)

    def prepare_player_input(self, player_input):
        """Cancel interrupted charges and require neutral before a fresh charge."""
        generation = self.input.charge_reset_generation
        if generation != self._charge_generation:
            self._charge_generation = generation
            # A genuinely new aggregate press after a reset is safe; a source
            # carried across a device handoff must first return to neutral.
            self._suppress_charge_until_neutral = (self.input.held('fire') and
                                                    not self.input.pressed('fire'))
            player = getattr(self.current_scene, 'player', None)
            cancel_charge = getattr(getattr(player, 'weapon', None), 'cancel_charge', None)
            if cancel_charge is not None:
                cancel_charge()
        if self._suppress_charge_until_neutral:
            player_input.fire_pressed = False
            player_input.fire_held = False
            player_input.fire_released = False
            if not self.input.held('fire'):
                self._suppress_charge_until_neutral = False
        player_input.combat_assisted = self.settings.combat_mode == 'assisted'
        return player_input

    def _route_input_event(self, event):
        """Quarantine a held charge immediately when an event changes devices."""
        fire_was_held = self.input.held('fire')
        generation = self.input.charge_reset_generation
        self.input.handle_event(event)
        if self.input.charge_reset_generation != generation:
            self._charge_generation = self.input.charge_reset_generation
            self._suppress_charge_until_neutral = fire_was_held and self.input.held('fire')
            player = getattr(self.current_scene, 'player', None)
            cancel_charge = getattr(getattr(player, 'weapon', None), 'cancel_charge', None)
            if cancel_charge is not None:
                cancel_charge()
        event.input_routed = True

    def _reset_session_scenes(self):
        """Never carry transcripts, unlocks, temporary buffs or room actors into another save."""
        old_field = self.scenes.get(config.STATE_FIELD_OPS)
        if old_field is not None:
            # Its pending on_exit must not write the old room into the newly loaded campaign.
            old_field.reality.world = None
        self.contact_session = None
        for state, scene_type in ((config.STATE_FIELD_OPS, FieldOpsScene),
                                  (config.STATE_BOSS_BOUNTY, BossScene),
                                  (config.STATE_ALIEN_CONTACT, AlienContactScene),
                                  (config.STATE_GALAXY_TRANSIT, GalaxyTransitScene),
                                  (config.STATE_RESTORED_EARTH, RestoredEarthScene),
                                  (config.STATE_SCIENCE_LAB, ScienceLabScene),
                                  (config.STATE_CRT_TERMINAL, CRTTerminalScene)):
            self.scenes[state] = scene_type(self)
        self._release_scene_controls()

    @property
    def is_paused(self) -> bool:
        """True when pause overlay is active."""
        return bool(self.pause.active) if hasattr(self, "pause") else False

    def _dispatch(self, callback, *args):
        self._dispatching = True
        try:
            callback(*args)
        finally:
            self._dispatching = False
        self._apply_transition()

    def handle_event(self, event):
        legacy_focus_lost = (event.type == pygame.ACTIVEEVENT and getattr(event, "state", 0) & 2
                             and not getattr(event, "gain", 0))
        if event.type in (pygame.QUIT, pygame.WINDOWFOCUSLOST, pygame.WINDOWMINIMIZED,
                          pygame.VIDEORESIZE, pygame.WINDOWRESIZED, pygame.WINDOWSIZECHANGED) or legacy_focus_lost:
            self.input.release_all()
            self._release_scene_controls()
            if ((event.type in (pygame.WINDOWFOCUSLOST, pygame.WINDOWMINIMIZED) or legacy_focus_lost)
                    and self.current_state_name != config.STATE_TITLE_BOOT and not self.pause.active):
                self.open_pause()
            return
        release_event = event.type in (pygame.KEYUP, pygame.CONTROLLERBUTTONUP, pygame.CONTROLLERAXISMOTION,
                                       pygame.MOUSEBUTTONUP)
        if ((not self.pause.active or release_event) and self.current_state_name == config.STATE_BUNKER_HUB
                and self.current_scene.opening_input_gate(event)):
            return
        controller_events = (pygame.CONTROLLERDEVICEADDED, pygame.CONTROLLERDEVICEREMOVED, pygame.CONTROLLERDEVICEREMAPPED,
                             pygame.CONTROLLERAXISMOTION, pygame.CONTROLLERBUTTONDOWN,
                             pygame.CONTROLLERBUTTONUP)
        is_controller = event.type in controller_events
        if is_controller:
            self._route_input_event(event)
        if self.pause.active:
            self.pause.handle_event(event)
            return
        if (event.type == pygame.CONTROLLERBUTTONDOWN and event.button == pygame.CONTROLLER_BUTTON_START
                and self.input.pressed('pause') and self.current_state_name != config.STATE_TITLE_BOOT):
            self.open_pause()
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F2 or (event.key == pygame.K_ESCAPE and self.current_state_name == config.STATE_BUNKER_HUB
                                           and not self.current_scene.dossier_open):
                self.open_pause()
                return
            if event.key == pygame.K_F1:
                self.change_settings(crt_effects=not self.settings.crt_effects)
                return
        # Story pages own input.  A and B are semantic next/back actions here,
        # not jump/fire; release device state before returning to gameplay.
        if ((self.current_state_name == config.STATE_BOSS_BOUNTY and self.current_scene.is_defeated_sequence)
                or (self.current_state_name == config.STATE_FIELD_OPS and self.current_scene.route_story)):
            if event.type == pygame.CONTROLLERBUTTONDOWN:
                key = {pygame.CONTROLLER_BUTTON_A: pygame.K_RETURN,
                       pygame.CONTROLLER_BUTTON_B: pygame.K_ESCAPE,
                       pygame.CONTROLLER_BUTTON_BACK: pygame.K_ESCAPE}.get(event.button)
                if key is not None:
                    self._dispatch(self.current_scene.handle_event,
                                   pygame.event.Event(pygame.KEYDOWN, key=key, controller_semantic=True))
            elif event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                self._dispatch(self.current_scene.handle_event, event)
            self.input.release_all()
            return
        if (self.current_state_name == config.STATE_FIELD_OPS
                and self.current_scene.pointer_context_hit(event)):
            self._dispatch(self.current_scene.activate_context)
            return
        if not is_controller and self.current_state_name in (config.STATE_BUNKER_HUB, config.STATE_FIELD_OPS,
                                                            config.STATE_BOSS_BOUNTY, config.STATE_RESTORED_EARTH):
            self._route_input_event(event)
        if event.type == pygame.CONTROLLERBUTTONDOWN:
            # Bridge menu and authored interaction controls without fabricating
            # input-manager key state or changing the keyboard bindings.
            key = None
            if self.current_state_name == config.STATE_TITLE_BOOT:
                key = {pygame.CONTROLLER_BUTTON_A: pygame.K_RETURN,
                       pygame.CONTROLLER_BUTTON_START: pygame.K_RETURN,
                       pygame.CONTROLLER_BUTTON_B: pygame.K_ESCAPE,
                       pygame.CONTROLLER_BUTTON_DPAD_UP: pygame.K_UP,
                       pygame.CONTROLLER_BUTTON_DPAD_DOWN: pygame.K_DOWN}.get(event.button)
            elif self.current_state_name == config.STATE_BUNKER_HUB:
                key = {pygame.CONTROLLER_BUTTON_X: pygame.K_e,
                       pygame.CONTROLLER_BUTTON_BACK: pygame.K_TAB}.get(event.button)
                if self.current_scene.dossier_open:
                    key = {pygame.CONTROLLER_BUTTON_DPAD_UP: pygame.K_UP,
                           pygame.CONTROLLER_BUTTON_DPAD_DOWN: pygame.K_DOWN,
                           pygame.CONTROLLER_BUTTON_B: pygame.K_ESCAPE}.get(event.button, key)
                elif event.button == pygame.CONTROLLER_BUTTON_A:
                    key = pygame.K_RETURN
            elif self.current_state_name in (config.STATE_CRT_TERMINAL, config.STATE_SCIENCE_LAB,
                                              config.STATE_ALIEN_CONTACT, config.STATE_GALAXY_TRANSIT,
                                              config.STATE_RESTORED_EARTH):
                key = {pygame.CONTROLLER_BUTTON_A: pygame.K_RETURN,
                       pygame.CONTROLLER_BUTTON_B: pygame.K_ESCAPE}.get(event.button)
            elif self.current_state_name == config.STATE_FIELD_OPS and event.button == pygame.CONTROLLER_BUTTON_X:
                key = pygame.K_e
            if key is not None:
                self._dispatch(self.current_scene.handle_event,
                               pygame.event.Event(pygame.KEYDOWN, key=key, controller_semantic=True,
                                                  controller_button=event.button,
                                                  controller_instance=getattr(event, 'instance_id', getattr(event, 'which', None))))
                return
        self._dispatch(self.current_scene.handle_event, event)

    def update(self, dt_seconds):
        if self.pause.active:
            return
        self.audio.update(dt_seconds)
        self.crt.update(dt_seconds)
        self._dispatch(self.current_scene.update, dt_seconds)

    def render(self):
        self.current_scene.render(self.crt)
        if self.pause.active:
            self.pause.render(self.crt)
        self.crt.finalize_frame()

    def close(self):
        if not self._closed:
            self._closed = True
            self._pending = None
            self.input.release_all()
            self.input.close_controllers()
            self.audio.stop_all()
            if self.session_active and self.current_state_name == config.STATE_BUNKER_HUB:
                self.save_checkpoint()
            self.current_scene.on_exit()

    def render_global_hud(self, crt, location_label="", footer_text=None, **kwargs):
        render_global_hud(crt, self.campaign, location_label, footer_text, **kwargs)
