"""
MODULE: video_game/engine/scenes/bunker.py
PURPOSE: Render the bunker, handle proximity station interactions, and dossier view.
CALLED BY: GameStateMachine.
HOW TO MODIFY: Request assets through the shared cache and keep movement in seconds.
"""

import pygame
from .. import config
from ..objectives import ObjectiveTracker
from ..native_room_assets import load_native_opaque_backdrop
from ..ui.hud import dossier_lines, render_dossier_overlay
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
        return load_native_opaque_backdrop(root, 'bunker_hub', (480, 270))

    @property
    def active_civ(self):
        return MILESTONE_CIVS[self.civ_idx % len(MILESTONE_CIVS)]

    def on_enter(self, **kwargs):
        self.native_backdrop = self._load_native_backdrop()
        self.dossier_open = False
        self.dossier_offset = 0
        snapshot = self.machine.campaign.state.world_states.get("bunker_hub", {})
        for notice in snapshot.get("science_consequences", {}).values():
            if not notice["delivered"]:
                self.objective_tracker.post_notification("SCIENCE CONSEQUENCE", notice["message"], "success", 6.0)
                notice["delivered"] = True
                self.machine.campaign.store_world_state("bunker_hub", snapshot)
                break

    def get_active_station(self) -> str:
        """Determine if Mateo is currently standing within a station interaction trigger zone."""
        for station_id, station in BUNKER_STATIONS.items():
            if station["x_min"] <= self.mateo_x <= station["x_max"]:
                return station_id
        return None

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
            state = self.machine.campaign.state
            if not state.room_flags.get("first_mission_available", True):
                self.objective_tracker.post_notification(
                    title="STATION LOCKED",
                    text="SURFACE MISSION CURRENTLY LOCKED",
                    kind="warning",
                )
                return False

            if hasattr(self.machine, "audio") and self.machine.audio:
                self.machine.audio.play_sfx("station_chime")

            # If Greenkeeper is already defeated, Act I is complete
            if state.room_flags.get("greenkeeper_defeated", False):
                self.objective_tracker.post_notification(
                    title="ACT I COMPLETE",
                    text="SECTOR OVERSEER PURGED // TRANSIT CORRIDOR TO ACT II OPEN",
                    kind="success",
                )
                return True

            # If dish defense is completed, dispatch to Boss Arena
            if state.room_flags.get("dish_defense_completed", False):
                self.machine.change_state(config.STATE_BOSS_BOUNTY)
                return True

            # If feedhorn is repaired, dispatch to Dish Catwalk for 72s holdout defense
            if state.room_flags.get("feedhorn_repaired", False):
                field_scene = self.machine.scenes.get(config.STATE_FIELD_OPS)
                if field_scene:
                    field_scene.load_room("act_01/dish_catwalk.json", spawn_name="catwalk_start")
                self.machine.change_state(config.STATE_FIELD_OPS)
                return True

            # If coupler is in inventory but not repaired, remind player to repair before leaving
            if state.inventory.get("analog_coupler", 0) > 0:
                self.objective_tracker.post_notification(
                    title="REPAIR REQUIRED",
                    text="INSTALL ANALOG COUPLER AT BUNKER BENCH BEFORE DEFENSE",
                    kind="warning",
                )
                return False

            # Otherwise dispatch to surface approach trench / salvage yard
            field_scene = self.machine.scenes.get(config.STATE_FIELD_OPS)
            if field_scene:
                field_scene.load_room("act_01/approach.json", spawn_name="bunker_exit")
            self.machine.change_state(config.STATE_FIELD_OPS)
            return True

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

    def handle_event(self, event):
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

        # Proximity interaction (E or RETURN)
        if event.key == pygame.K_m:
            if self.machine.campaign.state.room_flags.get("act_01_completed", False):
                self.machine.change_state(config.STATE_FIELD_OPS, room="act_01/mandela_test.json", spawn="default")
            else:
                self.objective_tracker.post_notification("ANNEX LOCKED", "COMPLETE ACT I TO OPEN REALITY ANNEX", "warning")
            return
        if event.key in (pygame.K_e, pygame.K_RETURN):
            handled = self.interact_with_station()
            if handled:
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

        # Discoverable station prompt banner when Mateo is standing within station range
        active_station = self.get_active_station()
        if active_station is not None and not self.dossier_open:
            st = BUNKER_STATIONS[active_station]
            st_name = st["name"]
            st_sub = st["sub"]

            if active_station == "repair":
                state = self.machine.campaign.state
                if state.room_flags.get("feedhorn_repaired", False):
                    prompt_label = f"[{st_name}] FEEDHORN ONLINE"
                elif state.inventory.get("analog_coupler", 0) > 0:
                    prompt_label = f"[E] {st_name} // INSTALL ANALOG COUPLER"
                else:
                    prompt_label = f"[E] {st_name} // MISSING ANALOG COUPLER"
            else:
                prompt_label = f"[E] {st_name} // {st_sub}"

            # Prompt banner floating above station area
            prompt_rect = station_prompt_rect(crt, prompt_label, mx)
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

        # Quick-save status text
        if self.machine.session_active:
            if self.machine.save_notice.startswith("SAVE FAILED"):
                notice = "SAVE FAILED - F5 RETRY"
            elif self.machine.save_notice:
                notice = f"{self.machine.save_notice}  [F5] SAVE"
            else:
                notice = "[F5] SAVE CHECKPOINT"
            crt.draw_text(notice, 10, 228, color=config.COLOR_FIBO_GOLD)

        # Footer controls
        if self.machine.development:
            footer = "[A/D] MOVE  [E] INTERACT  [TAB] DOSSIER  [L/F/B] SCENES  [F5] SAVE  [ESC] PAUSE"
        else:
            footer = "[A/D] MOVE [E] STATION [M] ANNEX [TAB] DOSSIER [F5] SAVE"

        active_obj = self.objective_tracker.get_active_objective(self.machine.campaign)

        # Render global HUD
        self.machine.render_global_hud(
            crt,
            location_label=self.machine.campaign.current_act_label,
            footer_text=footer,
            objective=active_obj,
            notification=self.objective_tracker.active_notification,
        )

        # Render Dossier Overlay if active
        if self.dossier_open:
            render_dossier_overlay(crt, self.machine.campaign, active_obj, self.dossier_offset)
