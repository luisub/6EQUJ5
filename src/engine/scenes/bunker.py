"""
MODULE: video_game/engine/scenes/bunker.py
PURPOSE: Render the bunker, handle proximity station interactions, and dossier view.
CALLED BY: GameStateMachine.
HOW TO MODIFY: Request assets through the shared cache and keep movement in seconds.
"""

import pygame
from .. import config
from ..objectives import ObjectiveTracker
from ..campaign_route import departure, act_for_boss_room
from ..alien_journey import earth_portal_ready, ledger as journey_ledger, start_ledger, save_ledger as save_journey, dispatch as dispatch_journey
from ..native_room_assets import load_native_opaque_backdrop
from ..opening_story import OpeningStory, load_opening_pages
from ..ui.hud import dossier_lines, render_dossier_overlay
from ..ui.viewport import window_to_logical
from .base import BaseScene

MILESTONE_CIVS = (
    "FASR-001", "FASR-002", "FASR-003", "FASR-004", "FASR-005",
    "FASR-006", "FASR-007", "FASR-008", "FASR-009", "FASR-010", "FASR-SCAN-H"
)
LAYER_FILES = (
    "01_distant_structure.png", "02_rear_wall.png", "03_equipment.png",
    "04_playable_floor.png", "05_foreground_props.png", "06_lighting_overlay.png"
)

# Horizontal interaction stations across the bunker floor (x: 124.0 to 364.0)
BUNKER_STATIONS = {
    "lab": {
        "x_min": 124.0, "x_max": 160.0, "center_x": 140.0,
        "name": "SCIENCE LAB", "sub": "FORMAL VALIDATION BENCH",
        "state": config.STATE_SCIENCE_LAB,
    },
    "terminal": {
        "x_min": 170.0, "x_max": 260.0, "center_x": 215.0,
        "name": "CRT RECEIVER", "sub": "1420.4056 MHz WOW!",
        "state": config.STATE_CRT_TERMINAL,
    },
    "repair": {
        "x_min": 275.0, "x_max": 315.0, "center_x": 295.0,
        "name": "REPAIR BENCH", "sub": "ANALOG ELECTRONICS",
        "state": None,
    },
    "field": {
        "x_min": 330.0, "x_max": 364.0, "center_x": 348.0,
        "name": "SURFACE AIRLOCK", "sub": "ACT I APPROACH TRENCH",
        "state": config.STATE_FIELD_OPS,
    },
}


def station_prompt_rect(crt, label, sprite_x):
    """Fit the measured full station label inside the logical screen."""
    width = crt.font_sm.size(label)[0] + 16
    return pygame.Rect(max(8, min(sprite_x - 40, config.INTERNAL_WIDTH - width - 8)), 100, width, 14)


class BunkerHubScene(BaseScene):
    """6-Layer 480x270 Ohio Big Ear Bunker with proximity station interactions and dossier."""

    NEXT_BUTTON = pygame.Rect(12, 42, 220, 22)
    DETAILS_BUTTON = pygame.Rect(400, 244, 72, 18)
    EXPLORE_BUTTON = pygame.Rect(20, 70, 180, 20)

    def __init__(self, machine):
        super().__init__(machine)
        self.mateo_x = 186.0
        self.is_facing_right = True
        self.civ_idx = 0
        self.view_mode = 0
        self.outfit_idx = 0
        self.pose_idx = 0
        self.anim_seconds = 0.0
        self.dossier_open = False
        self.dossier_offset = 0
        self.objective_tracker = ObjectiveTracker()
        self.opening_story = None
        self._opening_guarded = set()

        self.layers = machine.assets.bunker_layers()
        self.native_backdrop = self._load_native_backdrop()
        outfits = ("navy_chore", "olive_field", "faraday_rig")
        self.strips = [machine.assets.image(f"sprites/mateo_{outfit}_strip.png", (1056, 128)) for outfit in outfits]
        self.mateo_surf = machine.assets.bunker_sprite("mateo_bunker", (96, 128))
        self.palette_surf = machine.assets.image("palette_sheet.png", (480, 270))

    def _load_native_backdrop(self):
        """Load the optional whole bunker backdrop only at scene setup/entry."""
        root = getattr(self.machine.assets, 'root', None)
        if root is None:
            return None
        return load_native_opaque_backdrop(root, 'bunker_hub', (480, 270), cached=getattr(self, 'native_backdrop', None))

    @property
    def active_civ(self):
        return MILESTONE_CIVS[self.civ_idx % len(MILESTONE_CIVS)]

    def on_enter(self, **kwargs):
        self.native_backdrop = self._load_native_backdrop()
        self.dossier_open = False
        self.dossier_offset = 0
        pages = load_opening_pages() if kwargs.get('show_opening', False) else []
        self.opening_story = OpeningStory(pages, asset_root=getattr(getattr(self.machine, 'assets', None), 'root', None)) if pages else None
        guard = kwargs.get('opening_guard')
        self._opening_guarded = {guard} if isinstance(guard, tuple) else set()
        snapshot = self.machine.campaign.state.world_states.get("bunker_hub", {})
        for notice in snapshot.get("science_consequences", {}).values():
            if not notice["delivered"]:
                self.objective_tracker.post_notification("SCIENCE CONSEQUENCE", notice["message"], "success", 6.0)
                notice["delivered"] = True
                self.machine.campaign.store_world_state("bunker_hub", snapshot)
                break

    def opening_input_gate(self, event):
        """Consume intro events before gameplay and guard held inputs until release."""
        active = self.opening_story is not None
        if event.type in (pygame.CONTROLLERDEVICEREMOVED, pygame.CONTROLLERDEVICEREMAPPED):
            instance = getattr(event, 'instance_id', getattr(event, 'which', None))
            self._opening_guarded = {token for token in self._opening_guarded
                                     if not (token[0] in ('controller', 'axis') and token[1] == instance)}
            return False
        if event.type in (pygame.KEYDOWN, pygame.KEYUP):
            token = ('key', event.key)
            if event.type == pygame.KEYUP:
                guarded = token in self._opening_guarded
                self._opening_guarded.discard(token)
                return active or guarded
            if token in self._opening_guarded:
                return True
            if not active:
                return False
            if event.key in (pygame.K_ESCAPE, pygame.K_F1, pygame.K_F2):
                return False
            self._opening_guarded.add(token)
            if not getattr(event, 'repeat', False) and event.key == pygame.K_n:
                self._next_opening_page()
                return True
            if not getattr(event, 'repeat', False) and event.key in (
                    pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE,
                    pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
                self.opening_story = None
                self.machine.input.release_all()
            return True
        if event.type in (pygame.CONTROLLERBUTTONDOWN, pygame.CONTROLLERBUTTONUP):
            instance = getattr(event, 'instance_id', getattr(event, 'which', None))
            token = ('controller', instance, event.button)
            if event.type == pygame.CONTROLLERBUTTONUP:
                guarded = token in self._opening_guarded
                self._opening_guarded.discard(token)
                return active or guarded
            if token in self._opening_guarded:
                return True
            if not active:
                return False
            if event.button == pygame.CONTROLLER_BUTTON_START:
                return False
            self._opening_guarded.add(token)
            if event.button == pygame.CONTROLLER_BUTTON_X:
                self._next_opening_page()
                return True
            if event.button in (pygame.CONTROLLER_BUTTON_A, pygame.CONTROLLER_BUTTON_DPAD_LEFT,
                                pygame.CONTROLLER_BUTTON_DPAD_RIGHT, pygame.CONTROLLER_BUTTON_DPAD_UP,
                                pygame.CONTROLLER_BUTTON_DPAD_DOWN):
                self.opening_story = None
                self.machine.input.release_all()
            return True
        if event.type == pygame.CONTROLLERAXISMOTION:
            instance = getattr(event, 'instance_id', getattr(event, 'which', None))
            token = ('axis', instance, event.axis)
            if not active and token not in self._opening_guarded:
                return False
            value = self.machine.input._axis_value(event.value)
            if abs(value) > self.machine.input.controller_deadzone:
                self._opening_guarded.add(token)
            else:
                self._opening_guarded.discard(token)
            return True
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            token = ('mouse', event.button)
            if event.type == pygame.MOUSEBUTTONUP:
                guarded = token in self._opening_guarded
                self._opening_guarded.discard(token)
                return active or guarded
            if token in self._opening_guarded:
                return True
            if not active:
                return False
            self._opening_guarded.add(token)
            position = window_to_logical(event.pos, self.machine.crt)
            if event.button == 1 and position is not None and self.opening_story.NEXT_BUTTON.collidepoint(position):
                self._next_opening_page()
                return True
            if event.button == 1 and position is not None and self.opening_story.SKIP_BUTTON.collidepoint(position):
                self.opening_story = None
                self.machine.input.release_all()
            return True
        if event.type in (pygame.CONTROLLERDEVICEADDED, pygame.CONTROLLERDEVICEREMOVED,
                          pygame.CONTROLLERDEVICEREMAPPED):
            return False
        return active

    def _next_opening_page(self):
        self.opening_story.advance()
        if self.opening_story.done:
            self.opening_story = None
        self.machine.input.release_all()

    def get_active_station(self) -> str:
        """Determine if Mateo is currently standing within a station interaction trigger zone."""
        for station_id, station in BUNKER_STATIONS.items():
            if station["x_min"] <= self.mateo_x <= station["x_max"]:
                return station_id
        return None

    def station_prompt(self, crt):
        """Return the short clickable action for the station in reach."""
        station = self.get_active_station()
        names = {"lab": "LAB", "terminal": "RECEIVER", "repair": "REPAIR", "field": "AIRLOCK"}
        if station is None:
            return None, None
        label = ("E: CONTINUE MISSION" if station == "field" and
                 self.machine.campaign.state.room_flags.get("greenkeeper_defeated", False)
                 else "E: USE " + names[station])
        return label, station_prompt_rect(crt, label, int(self.mateo_x))

    def interact_with_station(self) -> bool:
        """Activate the station Mateo is standing near. Returns True if handled."""
        station_id = self.get_active_station()
        if station_id is None:
            return False

        if station_id == "lab":
            if hasattr(self.machine, "audio") and self.machine.audio:
                self.machine.audio.play_sfx("station_chime")
            self.machine.change_state(config.STATE_SCIENCE_LAB)
            return True

        if station_id == "terminal":
            if hasattr(self.machine, "audio") and self.machine.audio:
                self.machine.audio.play_sfx("station_chime")
            self.machine.change_state(config.STATE_CRT_TERMINAL)
            return True

        if station_id == "field":
            return self.leave_bunker()

        if station_id == "repair":
            state = self.machine.campaign.state
            if state.room_flags.get("feedhorn_repaired", False):
                self.objective_tracker.post_notification(
                    title="STATION COMPLETE",
                    text="DISH FEEDHORN IS FULLY OPERATIONAL",
                    kind="info",
                )
                return True

            has_coupler = state.inventory.get("analog_coupler", 0) > 0
            if has_coupler:
                if hasattr(self.machine, "audio") and self.machine.audio:
                    self.machine.audio.play_sfx("printer_chatter")
                evt = {
                    "event_id": f"repair_feedhorn_{state.save_id}",
                    "type": "repair_dish_feedhorn",
                }
                applied = self.machine.campaign.apply_event(evt)
                if applied:
                    self.objective_tracker.post_notification(
                        title="REPAIR COMPLETE",
                        text="DISH FEEDHORN RESTORED (+5 CERTAINTY, +5 AGENCY)",
                        kind="success",
                    )
                else:
                    self.objective_tracker.post_notification(
                        title="ALREADY APPLIED",
                        text="DISH FEEDHORN REPAIR ALREADY REGISTERED",
                        kind="info",
                    )
                return True

            # Prerequisite unmet
            self.objective_tracker.post_notification(
                title="PREREQUISITE UNMET",
                text="MISSING ANALOG COUPLER (SEARCH SURFACE TRENCH)",
                kind="warning",
            )
            return False

        return False

    def leave_bunker(self) -> bool:
        """Use the airlock from anywhere while retaining campaign progression."""
        state = self.machine.campaign.state
        if not state.room_flags.get("first_mission_available", True):
            self.objective_tracker.post_notification(
                "STATION LOCKED", "SURFACE MISSION CURRENTLY LOCKED", "warning")
            return False

        if hasattr(self.machine, "audio") and self.machine.audio:
            self.machine.audio.play_sfx("station_chime")
        if earth_portal_ready(self.machine.campaign):
            current = start_ledger(self.machine.campaign)
            if current and current.get('stage') != 'complete':
                if not journey_ledger(self.machine.campaign):
                    save_journey(self.machine.campaign, current)
                if dispatch_journey(self.machine):
                    return True
            if current.get('stage') == 'complete':
                self.machine.change_state(config.STATE_FIELD_OPS, room='act_01/approach.json', spawn='bunker_exit')
                return True
        if state.room_flags.get("greenkeeper_defeated", False):
            destination = departure(self.machine.campaign)
            if destination:
                room, spawn, _act_id = destination
                room_id = room.removesuffix('.json').replace('/', '_')
                boss_act, boss = act_for_boss_room(room_id)
                if boss:
                    self.machine.change_state(config.STATE_BOSS_BOUNTY, room=room, spawn=spawn,
                                              campaign_act=boss_act, boss_id=boss['boss_id'])
                else:
                    self.machine.change_state(config.STATE_FIELD_OPS, room=room, spawn=spawn,
                                              campaign_route=True, show_intro=spawn == 'default')
                return True
            room, spawn = "act_01/approach.json", "bunker_exit"
            notice = ("ACT I COMPLETE", "EXPLORE OHIO")
        elif state.room_flags.get("dish_defense_completed", False):
            self.machine.change_state(config.STATE_BOSS_BOUNTY)
            return True
        elif state.room_flags.get("feedhorn_repaired", False):
            room, spawn = "act_01/dish_catwalk.json", "catwalk_start"
            notice = None
        else:
            room, spawn = "act_01/approach.json", "bunker_exit"
            notice = (("REPAIR DISH", "INSTALL COUPLER AT FEEDHORN OR BUNKER BENCH")
                      if state.inventory.get("analog_coupler", 0) > 0 else None)

        if notice:
            tracker = self.machine.scenes[config.STATE_FIELD_OPS].objective_tracker
            tracker.last_objective_id = tracker.get_active_objective(self.machine.campaign).id
            tracker.post_notification(*notice, duration=6.0)
        self.machine.change_state(config.STATE_FIELD_OPS, room=room, spawn=spawn)
        return True

    def follow_objective(self) -> bool:
        """Use the existing station interaction, including its normal guards."""
        objective = self.objective_tracker.get_active_objective(self.machine.campaign)
        if objective.station_id not in BUNKER_STATIONS:
            return False
        self.mateo_x = BUNKER_STATIONS[objective.station_id]["center_x"]
        return self.interact_with_station()

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            position = window_to_logical(event.pos, self.machine.crt)
            if self.dossier_open:
                if position is not None and self.DETAILS_BUTTON.collidepoint(position):
                    self.dossier_open = False
            else:
                if (position is not None and self.EXPLORE_BUTTON.collidepoint(position)
                        and self.machine.campaign.state.room_flags.get("greenkeeper_defeated", False)):
                    self.leave_bunker()
                elif position is not None and self.NEXT_BUTTON.collidepoint(position):
                    self.follow_objective()
                elif position is not None and self.DETAILS_BUTTON.collidepoint(position):
                    self.dossier_open = True
                    self.dossier_offset = 0
                elif position is not None:
                    _, prompt_rect = self.station_prompt(self.machine.crt)
                    if prompt_rect is not None and prompt_rect.collidepoint(position):
                        self.interact_with_station()
            return
        if event.type != pygame.KEYDOWN:
            return

        # Dossier inspection toggle (TAB)
        if event.key == pygame.K_TAB:
            self.dossier_open = not self.dossier_open
            self.dossier_offset = 0
            return

        # If dossier is open, ESC closes it
        if self.dossier_open:
            if event.key == pygame.K_ESCAPE:
                self.dossier_open = False
            elif event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_PAGEUP, pygame.K_PAGEDOWN):
                objective = self.objective_tracker.get_active_objective(self.machine.campaign)
                limit = max(0, len(dossier_lines(self.machine.crt, self.machine.campaign, objective)) - 15)
                delta = -1 if event.key == pygame.K_UP else 1 if event.key == pygame.K_DOWN else -8 if event.key == pygame.K_PAGEUP else 8
                self.dossier_offset = max(0, min(limit, self.dossier_offset + delta))
            return

        if event.key == pygame.K_m:
            if self.machine.campaign.state.room_flags.get("act_01_completed", False):
                self.machine.change_state(config.STATE_FIELD_OPS, room="act_01/mandela_test.json", spawn="default")
            else:
                self.objective_tracker.post_notification("ANNEX LOCKED", "COMPLETE ACT I TO OPEN REALITY ANNEX", "warning")
            return
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_UP):
            if event.key == pygame.K_UP:
                self.machine.input.consume_key(pygame.K_UP)
            self.leave_bunker()
            return
        if event.key == pygame.K_SPACE:
            self.follow_objective()
            return
        if event.key == pygame.K_e and self.interact_with_station():
            return

        # Development shortcuts only active in development mode
        if self.machine.development:
            if event.key == pygame.K_l:
                self.machine.change_state(config.STATE_SCIENCE_LAB)
            elif event.key == pygame.K_f:
                self.machine.change_state(config.STATE_FIELD_OPS)
            elif event.key == pygame.K_b:
                self.machine.change_state(config.STATE_BOSS_BOUNTY)
            elif event.key == pygame.K_c:
                self.civ_idx = (self.civ_idx + 1) % len(MILESTONE_CIVS)
            elif event.key == pygame.K_o:
                self.outfit_idx = (self.outfit_idx + 1) % 3
            elif event.key == pygame.K_v:
                self.view_mode = (self.view_mode + 1) % 3
            elif event.key == pygame.K_q:
                self.machine.toggle_timeline()

        # F5 Quick Save
        if event.key == pygame.K_F5:
            self.machine.save_checkpoint()

    def update(self, dt_seconds):
        if self.opening_story is not None:
            self.opening_story.update(dt_seconds)
            if self.opening_story.done:
                self.opening_story = None
                self.machine.input.release_all()
            return
        self.anim_seconds += dt_seconds
        self.objective_tracker.update(dt_seconds, self.machine.campaign)

        if self.dossier_open:
            return

        actions = self.machine.input
        moving = False
        if actions.held("move_left"):
            self.mateo_x = max(124.0, self.mateo_x - 110.0 * dt_seconds)
            self.is_facing_right = False
            moving = True
        if actions.held("move_right"):
            self.mateo_x = min(364.0, self.mateo_x + 110.0 * dt_seconds)
            self.is_facing_right = True
            moving = True

        if actions.held("jump"):
            self.pose_idx = 6
        elif actions.held("crouch"):
            self.pose_idx = 7
        elif actions.held("fire"):
            self.pose_idx = 9
        elif moving:
            self.pose_idx = 2 + (int((self.anim_seconds + 1e-9) / 0.11) % 4)
        else:
            self.pose_idx = int((self.anim_seconds + 1e-9) / 0.65) % 2

    def render(self, crt):
        crt.clear((6, 9, 12))

        # View mode 2: Palette sheet inspector
        if self.view_mode == 2 and self.palette_surf:
            crt.canvas.blit(self.palette_surf, (0, 0))
            self.machine.render_global_hud(crt, location_label="PALETTE SHEET // [V] NEXT VIEW")
            return

        # Only a complete validated native backdrop replaces pre-actor layers.
        if self.native_backdrop is None or not self.native_backdrop.render(crt, known_clean=True):
            for layer_surf in self.layers[:4]:
                if layer_surf:
                    crt.canvas.blit(layer_surf, (0, 0))

        # Render Mateo shadow and animated sprite
        mx = int(self.mateo_x)
        pygame.draw.ellipse(crt.canvas, (2, 4, 6), (mx + 16, 238, 64, 12))
        strip = self.strips[self.outfit_idx]
        frame = strip.subsurface((self.pose_idx * 96, 0, 96, 128)) if strip else self.mateo_surf
        if frame:
            sprite = frame if self.is_facing_right else pygame.transform.flip(frame, True, False)
            crt.canvas.blit(sprite, (mx, 122))

        # Render foreground props and lighting overlay (layers 4..5)
        for layer_surf in self.layers[4:]:
            if layer_surf:
                crt.canvas.blit(layer_surf, (0, 0))

        if self.opening_story is not None:
            self.opening_story.render(crt)
            return

        # Discoverable station prompt banner when Mateo is standing within station range
        active_station = self.get_active_station()
        if active_station is not None and not self.dossier_open:
            prompt_label, prompt_rect = self.station_prompt(crt)

            # Prompt banner floating above station area
            pygame.draw.rect(crt.canvas, (8, 16, 12), prompt_rect)
            pygame.draw.rect(crt.canvas, config.COLOR_FIBO_GOLD, prompt_rect, 1)
            crt.draw_text(prompt_label, prompt_rect.x + 8, prompt_rect.y + 2, color=config.COLOR_FIBO_GOLD, size="sm")

        # View mode 1: Civilization art inspector (dev mode)
        if self.view_mode == 1:
            crt.draw_panel(
                (16, 26, 448, 212),
                bg_color=(6, 12, 16),
                border_color=config.COLOR_CRT_GREEN,
                title=f"ART MILESTONE 1 INSPECTOR // {self.active_civ} (128x128 NATIVE LAYERS)",
            )
            for idx, (suf, lbl) in enumerate([("env", "ENV PLATE"), ("face", "PORTRAIT"), ("constellation", "STAR CHART")]):
                sp = self.machine.assets.civilization(self.active_civ, suf)
                x_p = 30 + idx * 144
                pygame.draw.rect(crt.canvas, (12, 20, 26), (x_p, 48, 128, 128))
                if sp:
                    crt.canvas.blit(sp, (x_p, 48))
                pygame.draw.rect(crt.canvas, config.COLOR_CRT_DIM, (x_p, 48, 128, 128), 1)
                crt.draw_text(f"{lbl} (128x128)", x_p + 12, 182, color=config.COLOR_FIBO_GOLD)

        # A state-derived shortcut uses the same guarded station handlers.
        active_obj = self.objective_tracker.get_active_objective(self.machine.campaign)
        if not self.dossier_open and active_obj.station_id is not None:
            pygame.draw.rect(crt.canvas, (8, 22, 14), self.NEXT_BUTTON)
            pygame.draw.rect(crt.canvas, config.COLOR_FIBO_GOLD, self.NEXT_BUTTON, 1)
            crt.draw_text("NEXT: " + active_obj.title, self.NEXT_BUTTON.x + 7,
                          self.NEXT_BUTTON.y + 7, color=config.COLOR_FIBO_GOLD, size="sm")

        if not self.dossier_open and self.machine.campaign.state.room_flags.get("greenkeeper_defeated", False):
            panel = pygame.Rect(12, 36, 456, 60)
            pygame.draw.rect(crt.canvas, (8, 22, 14), panel)
            pygame.draw.rect(crt.canvas, config.COLOR_CRT_DIM, panel, 1)
            crt.draw_text("MISSION ROUTE AVAILABLE", 20, 41,
                          color=config.COLOR_FIBO_GOLD, size="sm")
            crt.draw_text("CONTINUE TO THE LATEST UNLOCKED SECTOR", 20, 54,
                          color=config.COLOR_CRT_GREEN, size="sm")
            pygame.draw.rect(crt.canvas, (18, 44, 27), self.EXPLORE_BUTTON)
            pygame.draw.rect(crt.canvas, config.COLOR_FIBO_GOLD, self.EXPLORE_BUTTON, 1)
            crt.draw_text("CONTINUE", self.EXPLORE_BUTTON.x + 8,
                          self.EXPLORE_BUTTON.y + 5, color=config.COLOR_FIBO_GOLD, size="sm")

        # Keep save failures visible; ordinary checkpoint status is available in pause.
        if self.machine.session_active and self.machine.save_notice.startswith("SAVE FAILED"):
            crt.draw_text("SAVE FAILED - F5 RETRY", 10, 228, color=config.COLOR_FIBO_GOLD)

        if not self.dossier_open:
            exit_label = ("ENTER / UP: CONTINUE MISSION" if
                          self.machine.campaign.state.room_flags.get("greenkeeper_defeated", False)
                          else "ENTER / UP: GO OUTSIDE")
            crt.draw_text(exit_label, 12, 248,
                          color=config.COLOR_FIBO_GOLD, size="sm")
            pygame.draw.rect(crt.canvas, (8, 22, 14), self.DETAILS_BUTTON)
            pygame.draw.rect(crt.canvas, config.COLOR_CRT_DIM, self.DETAILS_BUTTON, 1)
            crt.draw_text("DETAILS", self.DETAILS_BUTTON.x + 8, self.DETAILS_BUTTON.y + 5,
                          color=config.COLOR_CRT_GREEN, size="sm")

        # Render global HUD
        self.machine.render_global_hud(
            crt,
            location_label=self.machine.campaign.current_act_label,
            objective=active_obj if active_obj.station_id is None else None,
            notification=self.objective_tracker.active_notification,
        )

        # Render Dossier Overlay if active
        if self.dossier_open:
            render_dossier_overlay(crt, self.machine.campaign, active_obj, self.dossier_offset)
            pygame.draw.rect(crt.canvas, (8, 22, 14), self.DETAILS_BUTTON)
            pygame.draw.rect(crt.canvas, config.COLOR_CRT_DIM, self.DETAILS_BUTTON, 1)
            crt.draw_text("CLOSE", self.DETAILS_BUTTON.x + 8, self.DETAILS_BUTTON.y + 5,
                          color=config.COLOR_CRT_GREEN, size="sm")
