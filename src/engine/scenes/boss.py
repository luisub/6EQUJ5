"""
# PURPOSE: Playable Boss Arena Scene managing sector boss encounters, camera framing, health bars, and defeat flow.
# CALLED BY: video_game.engine.state_machine, video_game.tests.test_combat.
# HOW TO MODIFY: Adjust camera tracking bounds, boss HUD layout, pre-boss checkpoint restore, or defeat reward triggers.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pygame

from video_game.engine import config
from video_game.engine.core_network import CoreNetwork
from video_game.engine.animation import AnimationPlayer, load_mateo_animations
from video_game.engine.effects import EffectManager, load_maser_presentation
from video_game.engine.energy_stream_assets import load_energy_filament
from video_game.engine.energy_filament import EnergyFilament
from video_game.engine.bosses.base import (
    PHASE_1,
    PHASE_2,
    PHASE_3,
    PHASE_DEFEATED,
    STATE_DEFEATED,
    STATE_VULNERABLE,
    STATE_TELEGRAPH,
    STATE_ATTACK,
)
from video_game.engine.bosses.greenkeeper import Greenkeeper
from video_game.engine.boss_destruction import BossDestruction
from video_game.engine.bosses.campaign_bosses import BOSSES, AlienGuardian, PortalWarden, EarthFinalAI
from video_game.engine.alien_journey import (journey_data, ledger as journey_ledger,
    save_ledger as save_journey, start_ledger, world_by_id, dispatch as dispatch_journey, earth_portal_ready)
from video_game.engine.campaign_route import act_meta, room_meta, store_route
from video_game.engine.campaign_scenery import CampaignScenery, load_campaign_boss
from video_game.engine.native_room_assets import load_native_room_family
from video_game.engine.objectives import Objective
from video_game.engine.player import Player, PlayerConfig, PlayerInput
from video_game.engine.scenes.base import BaseScene
from video_game.engine.story_sequence import StorySequence, earned_story_pages
from video_game.engine.ui.hud import render_global_hud
from video_game.engine.ui.aim_reticle import render_aim_reticle
from video_game.engine.ui.dialogue import action as dialogue_action, NEXT_BUTTON
from video_game.engine.weapons import ArsenalManager, ProjectileManager, StarterMaser
from video_game.engine.combat_feedback import CombatFeedback, SceneAtmosphere
from video_game.engine.temporary_weapons import WeaponPickups, render_weapon_timer, style_temporary_flash
from video_game.engine.abilities import AbilityManager
from video_game.engine.world import Camera, Room

LEVELS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "levels"


class BossScene(BaseScene):
    """
    Playable Sector Boss Arena Scene.

    Manages arena geometry, player combat locomotion, sector boss lifecycle,
    phase transitions, pre-boss checkpoint resets, and defeat reward progression.
    """

    def __init__(self, machine: Any, room_relative_path: str = "act_01/greenkeeper_arena.json"):
        super().__init__(machine)
        self.room_path = LEVELS_DIR / room_relative_path
        self.room = Room.load_from_file(self.room_path)
        self.camera = Camera(config.INTERNAL_WIDTH, config.INTERNAL_HEIGHT)
        self.camera.set_world_bounds(self.room.width_px, self.room.height_px)
        self.native_room = self._load_native_room()

        # Player setup
        self.player = Player(64.0, 208.0)
        self.player_input = PlayerInput()

        # Wire animation player
        try:
            clips = load_mateo_animations(self.machine.assets.root, outfit="olive_field")
            self.player.animator = AnimationPlayer(
                clips=clips,
                default_state="idle",
                scale_factor=0.25,
            )
        except Exception:
            self.player.animator = None

        # Weapons setup
        self.proj_mgr = ProjectileManager()
        self.player.arsenal = ArsenalManager()
        self.player.abilities = AbilityManager()
        self.player.weapon = self.player.arsenal.active_weapon
        self.effects = EffectManager()
        self.feedback = CombatFeedback()
        self.atmosphere = SceneAtmosphere()
        self.weapon_pickups = WeaponPickups(self.room, arena=True)
        self.maser_presentation = load_maser_presentation(getattr(getattr(self.machine, 'assets', None), 'root', None))
        self.energy_filament = self._load_energy_filament()
        self._prev_boss_proj_count: int = 0
        self._prev_player_hp: int = self.player.health
        self._prev_is_grounded: bool = False
        self._prev_is_sliding: bool = False

        # Boss setup
        self.boss = Greenkeeper()
        self.campaign_act = None
        self.journey_world = None
        self.journey_final = False
        self.campaign_scenery = None
        self.encounter_intro_remaining = 0.0
        # Physical inputs tracked during the frozen reveal for fresh-retry checks.
        # The shared state-machine control reset clears this on pause/focus loss.
        self.keys_held = {}

        # Encounter tracking
        self.checkpoint_pos: Tuple[float, float] = (64.0, 208.0)
        self.is_fight_active: bool = False
        self.is_defeated_sequence: bool = False
        self.defeat_banner_timer: float = 0.0
        self.simultaneous_death_occurred: bool = False
        self.story = None
        self.destruction = None
        self.story_save_pending = False

    def _load_energy_filament(self):
        image = load_energy_filament(getattr(getattr(self.machine, 'assets', None), 'root', None))
        return EnergyFilament(image) if image is not None else None

    def _load_native_room(self):
        """Load the complete optional room family at scene entry."""
        root = getattr(getattr(self.machine, "assets", None), "root", None)
        if root is None:
            return None
        return load_native_room_family(root, self.room.room_id, (self.room.width_px, self.room.height_px))

    def on_enter(self, **kwargs):
        """Prepare arena on transition enter."""
        self.campaign_act = kwargs.get('campaign_act')
        self.journey_world = kwargs.get('journey_world')
        self.journey_final = bool(kwargs.get('journey_final', False))
        self.core_network = CoreNetwork() if self.journey_final else None
        current = journey_ledger(self.machine.campaign)
        if self.journey_world and (current.get('world_id') != self.journey_world or current.get('stage') != 'guardian'):
            self.machine.change_state(config.STATE_BUNKER_HUB)
            return
        if self.journey_final and (current.get('stage') != 'final' or len(current.get('receipts', [])) != 11):
            self.machine.change_state(config.STATE_BUNKER_HUB)
            return
        room = kwargs.get('room', 'act_01/greenkeeper_arena.json')
        self.room_path = LEVELS_DIR / room
        self.room = Room.load_from_file(self.room_path)
        self.camera.set_world_bounds(self.room.width_px, self.room.height_px)
        boss_id = kwargs.get('boss_id')
        if self.journey_world:
            world = world_by_id(self.journey_world)
            if not world or boss_id != world['boss_id'] or room != world['arena_room']:
                self.machine.change_state(config.STATE_BUNKER_HUB)
                return
            self.boss = AlienGuardian(world)
        elif self.journey_final:
            final = journey_data()['final_earth']
            if room != final.get('arena_room') or boss_id != final.get('boss_id'):
                self.machine.change_state(config.STATE_BUNKER_HUB)
                return
            self.boss = EarthFinalAI()
        elif boss_id == 'portal_warden':
            self.boss = PortalWarden()
        else:
            self.boss = BOSSES[boss_id]() if boss_id in BOSSES else Greenkeeper()
        if boss_id in BOSSES or self.journey_world or self.journey_final or boss_id == 'portal_warden':
            root = getattr(getattr(self.machine, 'assets', None), 'root', None)
            art_id = 'earth_core_ai' if self.journey_final else boss_id
            self.boss.art_surface = load_campaign_boss(root, art_id)
            if self.boss.art_surface is None:
                # Use the reviewed Core machinery body when a specific body is unavailable.
                self.boss.art_surface = load_campaign_boss(root, 'synchronicity')
        self.native_room = self._load_native_room()
        self.energy_filament = self._load_energy_filament()
        self.campaign_scenery = (CampaignScenery(getattr(getattr(self.machine, 'assets', None), 'root', None),
                                                  self.room, room_meta(self.room.room_id))
                                 if self.campaign_act or self.journey_world or self.journey_final else None)
        self.atmosphere = SceneAtmosphere(self.room.room_id)
        spawn_id = kwargs.get("spawn", "arena_checkpoint")
        if spawn_id in self.room.spawns:
            sp = self.room.spawns[spawn_id]
            self.checkpoint_pos = (sp.x, sp.y)
        else:
            self.checkpoint_pos = (64.0, 208.0)

        self.player.arsenal.sync_unlocks(self.machine.campaign)
        self.player.abilities.sync_unlocks(self.machine.campaign)
        self.player.weapon = self.player.arsenal.active_weapon
        self.player.set_checkpoint("pre_boss", self.checkpoint_pos[0], self.checkpoint_pos[1])
        self.player.respawn_at_checkpoint(self.room)
        self.feedback.clear()
        self.weapon_pickups = WeaponPickups(self.room, arena=True)
        self.camera.snap_to(self.player.x, self.player.y)
        self.boss.reset_to_pristine()
        self.boss.skip_intro()
        self.encounter_intro_remaining = 0.0
        self.is_fight_active = True
        self.is_defeated_sequence = False
        self.defeat_banner_timer = 0.0
        self.simultaneous_death_occurred = False
        self.story = None
        self.destruction = None
        self.story_save_pending = False
        if self._already_defeated():
            self.encounter_intro_remaining = 0.0
            if self.journey_final:
                self.boss.final_stage = 2
            self.boss.trigger_defeat()
            self._start_story(saved=True, animate=False)

    def _defeated_flag(self):
        if self.journey_world:
            return world_by_id(self.journey_world)['defeat_flag']
        if self.journey_final:
            return journey_data()['final_earth']['defeat_flag']
        if isinstance(self.boss, PortalWarden):
            return 'portal_warden_defeated'
        return act_meta(self.campaign_act).get('complete_flag', 'greenkeeper_defeated') if self.campaign_act else 'greenkeeper_defeated'

    def _already_defeated(self):
        flags = self.machine.campaign.state.room_flags
        return bool(flags.get(self._defeated_flag(), False) or
                    (self.campaign_act == 'act_05' and flags.get('core_prime_defeated', False)))

    def _guardian_victory(self):
        current = journey_ledger(self.machine.campaign)
        if current.get('world_id') != self.journey_world or current.get('stage') != 'guardian':
            return False
        prior = dict(current)
        current['stage'] = 'contact'
        current['checkpoint'] = None
        save_journey(self.machine.campaign, current)
        if self.machine.save_checkpoint():
            return dispatch_journey(self.machine)
        save_journey(self.machine.campaign, prior)
        self.story_save_pending = True
        return False

    def on_exit(self):
        """Purge lingering projectiles, effects, and state upon leaving."""
        self.proj_mgr.clear()
        self.effects.clear()
        self.feedback.clear()
        self.player.arsenal.clear_temporary()
        self.boss.telegraphs.clear()
        self.boss.projectiles.clear()
        self.destruction = None

    def handle_event(self, event: pygame.Event):
        """Process player combat inputs and debug keys."""
        if self.is_defeated_sequence:
            action = dialogue_action(event, self.machine.crt)
            advance, back = action == 'next', action == 'back'
            if self.story_save_pending and (advance or back):
                self.story_save_pending = not self.machine.save_checkpoint()
                if self.story_save_pending:
                    return
                if self.story and self.story.done:
                    self._finish_story(to_bunker=back)
                    return
                if not back:
                    return
            if back:
                self._finish_story(to_bunker=True)
            elif advance and self.story:
                self.story.advance()
                if self.story.done:
                    self._finish_story()
            return
        if getattr(self.machine.pause, "active", False):
            return
        reveal = self.encounter_intro_remaining > 0
        fresh = getattr(event, "input_fresh", False)
        if reveal:
            if event.type in (pygame.KEYDOWN, pygame.KEYUP):
                token = ('key', event.key)
                if event.type == pygame.KEYDOWN:
                    fresh = token not in self.keys_held
                    self.keys_held[token] = True
                else:
                    self.keys_held.pop(token, None)
            elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                token = ('mouse', event.button)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    fresh = token not in self.keys_held
                    self.keys_held[token] = True
                else:
                    self.keys_held.pop(token, None)

        legacy_retry = (event.type == pygame.KEYDOWN and event.key == pygame.K_r
                        and (self.player.is_dead or self.boss.is_defeated))
        easy_retry = (self.player.is_dead and not self.boss.is_defeated
                      and fresh
                      and ((event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE)
                           or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1)))
        if legacy_retry or easy_retry:
            # Retry owns its input; never carry fire, charge, movement or edges.
            self.machine.input.release_all()
            self.machine._release_scene_controls()
            self.retry_from_checkpoint()
            return

        if reveal:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.machine.change_state(config.STATE_BUNKER_HUB)
            else:
                self.machine.input.release_all()
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.machine.change_state(config.STATE_BUNKER_HUB)
            return

    def update(self, dt: float):
        """Execute fixed-step combat simulation across player, boss, and arena."""
        if self.is_defeated_sequence:
            if self.destruction and not self.destruction.done:
                self.destruction.update(dt)
                self.effects.update(dt, room=self.room)
            self.feedback.update(dt, paused=getattr(self.machine, "is_paused", False))
            return
        if self.campaign_scenery:
            self.campaign_scenery.update(dt, paused=getattr(self.machine, 'is_paused', False))
        if self.encounter_intro_remaining > 0:
            self.encounter_intro_remaining = max(0.0, self.encounter_intro_remaining - max(0.0, dt))
            self.machine.input.release_all()
            return
        # Use the same focused, edge-triggered action mapper as field gameplay.
        if self.player.is_dead:
            return  # An explicit retry restarts the encounter; never silently respawn.
        self.player_input = PlayerInput.from_input_manager(self.machine.input)
        self.player_input.apply_aim_context(self.machine.input, self.camera, self.machine.crt)
        prepare_input = getattr(self.machine, 'prepare_player_input', None)
        if prepare_input is not None:
            self.player_input = prepare_input(self.player_input)

        is_paused = getattr(self.machine, "is_paused", False) or getattr(getattr(self.machine, "pause", None), "active", False)

        self.feedback.update(dt, paused=is_paused)
        self.atmosphere.update(dt, paused=is_paused)
        previous_temporary = self.player.arsenal.temporary_id

        # Trigger jump audio and dust
        if self.player_input.jump_pressed and (self.player.is_grounded or self.player.coyote_timer > 0.0):
            if hasattr(self.machine, "audio") and self.machine.audio:
                self.machine.audio.play_sfx("player_jump")
            self.effects.add_dust_puff(self.player.x + 8.0, self.player.y + 32.0, count=4)

        prev_proj_len = len(self.proj_mgr.projectiles)

        # 2. Update player kinematics and weapon discharge
        self.player.update(
            dt,
            self.player_input,
            self.room,
            projectile_manager=self.proj_mgr,
            is_paused=is_paused,
        )

        if previous_temporary and not self.player.arsenal.temporary_id:
            self.feedback.emit(*self.player.rect.center, "expired", "MASER RESTORED")
        self.weapon_pickups.update(dt, self.player, self.feedback, paused=is_paused)

        # Trigger audio and muzzle flash on weapon discharge
        if len(self.proj_mgr.projectiles) > prev_proj_len:
            spawned = self.proj_mgr.projectiles[prev_proj_len:]
            new_proj = spawned[-1]
            if new_proj.weapon_type == 'starter_maser':
                new_proj = next((p for p in spawned if getattr(p, 'is_primary_discharge', True)), new_proj)
            sfx_name = "maser_charge" if new_proj.is_charged else "maser_tap"
            if hasattr(self.machine, "audio") and self.machine.audio:
                self.machine.audio.play_sfx(sfx_name)
            direction = 'left' if new_proj.dir_x < 0 else 'right' if new_proj.dir_x > 0 else self.player.weapon_facing
            compact = (self.energy_filament is not None and new_proj.weapon_type == 'starter_maser'
                       and not new_proj.is_charged)
            if compact:
                self.energy_filament.register(spawned, self.machine.input.charge_reset_generation)
            self.effects.add_muzzle_flash(new_proj.x, new_proj.y, direction=direction, is_charged=new_proj.is_charged,
                                          maser_presentation=(self.maser_presentation is not None and
                                                              new_proj.weapon_type == 'starter_maser'),
                                          lighting_only=compact,
                                          input_generation=self.machine.input.charge_reset_generation if compact else None)
            self.effects.flashes[-1]['aim_vector'] = (new_proj.dir_x, new_proj.dir_y)
            style_temporary_flash(self.effects.flashes[-1], new_proj.weapon_type)

        # Trigger landing and slide dust / audio
        if not self._prev_is_grounded and self.player.is_grounded:
            if hasattr(self.machine, "audio") and self.machine.audio:
                self.machine.audio.play_sfx("player_land")
            self.effects.add_dust_puff(self.player.x + 8.0, self.player.y + 32.0, count=5)
        if not self._prev_is_sliding and self.player.is_sliding:
            if hasattr(self.machine, "audio") and self.machine.audio:
                self.machine.audio.play_sfx("player_slide")
            self.effects.add_dust_puff(self.player.x + 8.0, self.player.y + 32.0, count=4)

        self._prev_is_grounded = self.player.is_grounded
        self._prev_is_sliding = self.player.is_sliding

        # 3. Resolve player maser projectiles against world and boss
        if self.player.is_dashing and self.player.dash_attack_rect.colliderect(self.boss.rect):
            self.player.apply_dash_attack(self.boss)
        if not self.boss.is_dead:
            targets = [self.boss]
            hits = self.proj_mgr.update(dt, self.room, targets=targets, is_paused=is_paused)
            if hits:
                for hit in hits:
                    self.feedback.hit(hit)
                    if hasattr(self.machine, "audio") and self.machine.audio:
                        self.machine.audio.play_sfx("impact_spark")
                    self.effects.add_impact_sparks(hit.hit_x, hit.hit_y, count=6)

        # 5. Update Boss AI and attack cycles
        if not self.player.is_dead and not self.boss.is_dead:
            self.boss.update(dt, player_pos=self.player.rect.center)

            # Trigger mortar launch sfx and smoke
            curr_boss_projs = len(self.boss.projectiles)
            if curr_boss_projs > self._prev_boss_proj_count:
                if isinstance(self.boss, Greenkeeper) and hasattr(self.machine, "audio") and self.machine.audio:
                    self.machine.audio.play_sfx("boss_mortar_launch")
                if isinstance(self.boss, Greenkeeper):
                    self.effects.add_mortar_smoke(*self.boss.mortar_muzzle, count=5)
            self._prev_boss_proj_count = curr_boss_projs

            # Check for exploding mortar shells reaching ground level
            for bp in self.boss.projectiles:
                if isinstance(self.boss, Greenkeeper) and bp.y >= 216.0 and bp.lifetime > 0.0:
                    self.effects.add_mortar_smoke(bp.x, 228.0, count=3)
                    self.effects.add_impact_sparks(bp.x, 228.0, count=4, is_charged=True)

            # 6. Check boss attack hitboxes against player
            dmg = self.boss.check_attack_collisions(self.player.rect)
            if dmg > 0 and self.player.invulnerable_timer <= 0.0:
                kb_x = -80.0 if self.player.facing == "right" else 80.0
                self.player.take_damage(dmg, knockback_vx=kb_x, knockback_vy=-60.0,
                                        damage_source="hostile")

        # Check player damage taken
        if self.player.health < self._prev_player_hp:
            self.feedback.emit(*self.player.rect.center, "hurt", f"-{self._prev_player_hp - self.player.health} HP")
            if hasattr(self.machine, "audio") and self.machine.audio:
                self.machine.audio.play_sfx("player_hurt")
            self.effects.add_impact_sparks(self.player.x + 8.0, self.player.y + 16.0, count=8, is_charged=True)
        self._prev_player_hp = self.player.health

        # Step bounded effects
        self.effects.update(dt, room=self.room, is_paused=is_paused)

        # 7. Check simultaneous death edge case
        resolution = self.boss.resolve_simultaneous_death(not self.player.is_dead)
        if resolution == "PLAYER_DIED":
            # Player defeat takes priority
            if self.boss.is_defeated:
                self.simultaneous_death_occurred = True

        elif resolution == "BOSS_DEFEATED":
            if not self.is_defeated_sequence:
                if self.journey_final:
                    current = journey_ledger(self.machine.campaign)
                    if current.get('stage') != 'final' or len(current.get('receipts', [])) != 11:
                        return
                earned = self.boss.apply_defeat_reward(self.machine.campaign)
                if earned or self._already_defeated():
                    self._start_story(saved=self.machine.save_checkpoint())

        # 8. Defeat timer tick
        if self.is_defeated_sequence:
            self.defeat_banner_timer = max(0.0, self.defeat_banner_timer - dt)

        # Frame the player and moving warden together without changing the FOV.
        # At the entrance the larger authored body can be partially revealed;
        # as Mateo approaches, both fit in the existing 480-pixel viewport.
        focus_x = (self.player.x + self.player.width / 2 + self.boss.x + self.boss.width / 2) / 2
        half_view = self.camera.viewport_w / 2
        focus_x = min(focus_x, self.player.x + half_view - 16)
        focus_x = max(focus_x, self.player.x + self.player.width - half_view + 16)
        self.camera.update(focus_x, self.player.y)

    def _start_story(self, *, saved, animate=True):
        """Freeze combat after an earned victory while the checkpoint is durable."""
        if self.journey_world:
            world = world_by_id(self.journey_world)
            completed = len(journey_ledger(self.machine.campaign)['receipts'])
            pages = [{'title': f'{self.boss.title.title()} defeated',
                      'text': f'{world["civ_id"]} is ready to transmit.'}]
            next_label = 'Receive message'
            detail = f'{completed} / 11 messages recovered'
        elif self.journey_final:
            pages = journey_data()['final_earth'].get('epilogue', [])
            next_label, detail = 'See the new world', 'The Core is disconnected. Earth is free.'
        else:
            pages = (act_meta(self.campaign_act).get('victory', []) if self.campaign_act
                     else earned_story_pages(self.machine.campaign))
            next_act = act_meta(act_meta(self.campaign_act).get('next_act') if self.campaign_act else 'act_02')
            next_label = 'Travel onward' if self.campaign_act == 'act_05' else 'Continue'
            detail = ('Next: Sagittarius signal' if self.campaign_act == 'act_05'
                      else 'Next: ' + next_act['title'].split(' // ')[0].title() if next_act else 'Return to the observatory')
        if not pages:
            pages = [{'title': 'GREENKEEPER NEUTRALIZED',
                      'text': 'The bunker is safe for now. Return to the receiver.'}]
        self.story = StorySequence(pages, font=self.machine.crt.font_md, auto_advance=False,
                                   next_label=next_label, detail=detail)
        self.story_save_pending = not saved
        self.is_defeated_sequence = True
        self.is_fight_active = False
        self.proj_mgr.clear()
        self.boss.projectiles.clear()
        self.boss.telegraphs.clear()
        if hasattr(self.boss, 'attack_rects'):
            self.boss.attack_rects.clear()
        self.destruction = BossDestruction(self.boss) if animate else None
        self.machine.input.release_all()
        release = getattr(self.machine, '_release_scene_controls', None)
        if release:
            release()

    def _finish_story(self, *, to_bunker=False):
        self.machine.input.release_all()
        if self.journey_final:
            if not to_bunker:
                current = journey_ledger(self.machine.campaign)
                if current.get('stage') != 'final' or len(current.get('receipts', [])) != 11:
                    return
                current['stage'] = 'complete'
                save_journey(self.machine.campaign, current)
                if not self.machine.save_checkpoint():
                    current['stage'] = 'final'
                    save_journey(self.machine.campaign, current)
                    self.story_save_pending = True
                    return
            self.machine.change_state(config.STATE_BUNKER_HUB if to_bunker else config.STATE_RESTORED_EARTH)
            return
        if self.journey_world:
            if not to_bunker:
                self._guardian_victory()
                return
            self.machine.change_state(config.STATE_BUNKER_HUB)
            return
        if self.campaign_act == 'act_05' and self._already_defeated() and not to_bunker:
            current = start_ledger(self.machine.campaign)
            if current:
                save_journey(self.machine.campaign, current)
                if not self.machine.save_checkpoint():
                    self.story_save_pending = True
                    return
                if dispatch_journey(self.machine):
                    return
        if not to_bunker:
            next_id = (act_meta(self.campaign_act).get('next_act') if self.campaign_act else 'act_02')
            act = act_meta(next_id)
            if act and self.machine.campaign.state.room_flags.get(act.get('unlock_flag'), False):
                room_id = act['entry_room'].removesuffix('.json').replace('/', '_')
                store_route(self.machine.campaign, room_id, act.get('entry_spawn', 'default'))
                if not self.machine.save_checkpoint():
                    self.story_save_pending = True
                    return
                self.machine.change_state(config.STATE_FIELD_OPS, room=act['entry_room'],
                                          spawn=act.get('entry_spawn', 'default'),
                                          campaign_route=True, show_intro=True)
                return
        self.machine.change_state(config.STATE_BUNKER_HUB)

    def retry_from_checkpoint(self):
        """Restore pristine encounter state and respawn player at arena entrance."""
        self.player.set_checkpoint("pre_boss", self.checkpoint_pos[0], self.checkpoint_pos[1])
        self.player.respawn_at_checkpoint(self.room)
        self.boss.reset_to_pristine()
        self.boss.skip_intro()
        self.encounter_intro_remaining = 0.0
        self.proj_mgr.clear()
        self.effects.clear()
        self.feedback.clear()
        self.weapon_pickups = WeaponPickups(self.room, arena=True)
        self.is_fight_active = True
        self.is_defeated_sequence = False
        self.destruction = None
        self.defeat_banner_timer = 0.0
        self.simultaneous_death_occurred = False

    def _visible_lighting_events(self):
        events = self.effects.current_lighting_flashes(self.machine.input.charge_reset_generation)
        if self.player.is_dead or self.encounter_intro_remaining > 0:
            return [flash for flash in events if not flash.get('lighting_only')]
        return events

    def render(self, crt: Any):
        """Render complete boss arena view: background, terrain, boss, player, and boss HUD."""
        crt.clear()
        # 1. Parallax background
        campaign_background = bool(self.campaign_scenery and self.campaign_scenery.render_background(crt, self.camera))
        if not campaign_background and (self.native_room is None or not self.native_room.render(crt, self.camera, known_clean=True)):
            self.room.render_background(crt.canvas, self.camera)
        if self.campaign_scenery:
            self.campaign_scenery.render_activity(crt, self.camera)

        if self.journey_final and self.core_network:
            self.core_network.render(crt, self.boss, self.camera, self.destruction)

        self.atmosphere.render(crt, self.camera)

        # 2. Collision tiles & platforms
        self.room.render_tiles(crt.canvas, self.camera)

        # 3. Level objects & props
        self.room.render_objects(crt.canvas, self.camera)

        self.weapon_pickups.render(crt, self.camera)

        # 4. Boss entity & telegraphs
        if not self.is_defeated_sequence or (self.destruction and self.destruction.body_visible):
            self.boss.render(crt.canvas, self.camera, crt=crt)

        # 5. Player projectiles
        self.proj_mgr.render(crt.canvas, self.camera, enhanced_maser=self.maser_presentation is not None,
                             compact_maser=self.energy_filament is not None)

        # 6. Player character
        flash_hide = (self.player.invulnerable_timer > 0.0 and int(self.player.invulnerable_timer * 20) % 2 == 0)
        if not flash_hide:
            if self.player.animator is not None:
                foot_wx = self.player.x + (self.player.width / 2.0)
                foot_wy = self.player.y + 32.0
                dest_x, dest_y = self.player.animator.get_render_dest_for_density(foot_wx, foot_wy, self.camera, config.RENDER_DENSITY)
                sprite = self.player.animator.surface_for_density(config.RENDER_DENSITY)
                if self.maser_presentation:
                    flashes = self.maser_presentation.active_flashes(
                        self._visible_lighting_events())
                    sprite = self.maser_presentation.light_actor(sprite, (dest_x, dest_y), self.camera, flashes)
                logical_size = self.player.animator.current_surface.get_size()
                crt.composite_native(sprite, (dest_x / config.RENDER_DENSITY, dest_y / config.RENDER_DENSITY), logical_size)
            else:
                screen_px, screen_py = self.camera.world_to_screen(self.player.x, self.player.y)
                pygame.draw.rect(crt.canvas, config.COLOR_FIBO_GOLD, (screen_px, screen_py, self.player.width, self.player.height), 2)
                pygame.draw.circle(crt.canvas, config.COLOR_FIBO_GOLD, (screen_px + 8, screen_py + 8), 6)

        # 6.2 Visual combat particles, mortar smoke, sparks, and flashes
        if hasattr(self, "effects"):
            self.effects.render(crt.canvas, self.camera, suppress_maser=self.maser_presentation is not None)

        # 6.5 Atmospheric weather mist
        if not campaign_background:
            self.room.render_weather(crt.canvas, self.camera)
        if self.maser_presentation:
            flashes = self.maser_presentation.active_flashes(
                self._visible_lighting_events())
            burst_flashes = [flash for flash in flashes if not flash.get('lighting_only')]
            if burst_flashes:
                self.maser_presentation.render_bursts(crt, self.camera, burst_flashes)
        filament_layers = []
        if self.energy_filament is not None:
            filament_layers = self.energy_filament.render(crt, self.camera, self.proj_mgr.projectiles,
                                        self.machine.input.charge_reset_generation,
                                        blocked=(self.player.is_dead or self.encounter_intro_remaining > 0
                                                 or getattr(self.machine, 'is_paused', False)),
                                        muzzle=self.player.get_muzzle_world_pos(), room=self.room,
                                        targets=(self.boss,),
                                        aim_vector=self.energy_filament.current_aim(
                                            self.player_input, self.player.get_muzzle_world_pos(), self.player.weapon_facing),
                                        collect_layers=True)
        self.feedback.render(crt, self.camera, self.proj_mgr.projectiles, preceding_layers=filament_layers)
        if self.destruction:
            self.destruction.render(crt, self.camera)
        if not self.is_defeated_sequence:
            render_weapon_timer(crt, self.player.arsenal)
            render_aim_reticle(crt, self.machine.input, self.camera, self.player)

        # 7. Boss HUD (Top Bar overlay)
        revealing = self.encounter_intro_remaining > 0
        if not self.is_defeated_sequence:
            self._render_boss_hud(crt)
        if revealing:
            crt.draw_text('SECTOR BOSS APPROACHING', 150, 65, color=config.COLOR_FIBO_GOLD, size='sm')

        # 8. Standard global HUD footer
        obj = Objective(
            id="defeat_sector_boss",
            title=f"{self.boss.title} DEFEATED" if self.is_defeated_sequence else f"NEUTRALIZE {self.boss.title}",
            description="Watch the warning and attack the exposed target.",
            hint=("BOSS DEFEATED" if self.boss.is_defeated else
                  f"PHASE {self.boss.current_phase}/3 // WATCH FOR ATTACKS"),
        )
        footer = ("TARGET DESTROYED" if self.destruction and not self.destruction.done else
                  "ENTER / A / CLICK NEXT   ESC / B RETURN   F2 SETTINGS" if self.is_defeated_sequence
                  else "A/D MOVE  SPACE JUMP  MOUSE AIM  LEFT FIRE  RIGHT CHARGE  F2 SETTINGS")
        render_global_hud(
            crt,
            self.machine.campaign,
            location_label=self.room.title or "SECTOR BOSS ARENA",
            footer_text=footer,
            player=self.player,
            objective=None if revealing else obj,
            threat_level=self._active_threat() if not revealing else None,
            threat_y=65 if self.boss.weak_point_exposed else 53,
            staging_cleared=True,
        )

        # 9. Defeat victory banner
        if self.is_defeated_sequence and self.story and (self.story_save_pending or not self.destruction or self.destruction.done):
            self.story.render(crt, save_pending=self.story_save_pending)
        elif self.is_defeated_sequence:
            pygame.draw.rect(crt.canvas, (7, 17, 25), NEXT_BUTTON, border_radius=3)
            crt.draw_text('ENTER / A: CONTINUE', NEXT_BUTTON.x + 10, NEXT_BUTTON.y + 8,
                          color=config.COLOR_FIBO_GOLD, size='sm')

        # 10. Player Death banner
        if self.player.is_dead:
            self._render_player_death_banner(crt)

    def _active_threat(self):
        """Announce only an actual warning or attack, never an idle boss."""
        if self.boss.is_defeated or self.player.is_dead:
            return None
        if (self.boss.phase_state == STATE_TELEGRAPH or self.boss.telegraphs):
            return "AIMING"
        if (self.boss.phase_state == STATE_ATTACK or getattr(self.boss, 'sweep_active', False)
                or any(projectile.is_active for projectile in self.boss.projectiles)):
            return "LOCKED"
        return None

    def _render_boss_hud(self, crt: Any):
        """Render boss health bar, phase markers, and weak point status."""
        bar_x = 140
        bar_y = 22
        bar_w = 220
        bar_h = 10

        # Background frame
        show_weakness = self.boss.weak_point_exposed and self.encounter_intro_remaining <= 0
        frame_h = bar_h + (30 if show_weakness else 18)
        pygame.draw.rect(crt.canvas, (10, 14, 18), (bar_x - 4, bar_y - 4, bar_w + 8, frame_h))
        pygame.draw.rect(crt.canvas, config.COLOR_CORE_STEEL, (bar_x - 4, bar_y - 4, bar_w + 8, frame_h), 1)

        # Health fill
        hp_pct = max(0.0, self.boss.health / float(self.boss.max_health))
        fill_w = int(bar_w * hp_pct)
        hp_color = config.COLOR_EHMAN_RED if hp_pct <= 0.33 else (config.COLOR_AMBER_1977 if hp_pct <= 0.66 else config.COLOR_CRT_GREEN)
        pygame.draw.rect(crt.canvas, hp_color, (bar_x, bar_y, fill_w, bar_h))
        pygame.draw.rect(crt.canvas, (40, 50, 60), (bar_x, bar_y, bar_w, bar_h), 1)

        # Phase threshold notch ticks
        tick_p2 = bar_x + int(bar_w * 2 / 3)
        tick_p3 = bar_x + int(bar_w / 3)
        pygame.draw.line(crt.canvas, (255, 255, 255), (tick_p2, bar_y - 2), (tick_p2, bar_y + bar_h + 2), 1)
        pygame.draw.line(crt.canvas, (255, 255, 255), (tick_p3, bar_y - 2), (tick_p3, bar_y + bar_h + 2), 1)

        # Boss title & phase readout
        title_str = (f"{self.boss.title} [DEFEATED]" if self.boss.is_defeated else
                     self.boss.title if self.encounter_intro_remaining > 0 else
                     f"{self.boss.title} [PHASE {self.boss.current_phase}/3]")
        if self.journey_final and not self.boss.is_defeated:
            title_str = f'{self.boss.title} [FORM {self.boss.final_stage}/2]'
        crt.draw_text(title_str, bar_x, bar_y + 11, color=config.COLOR_FIBO_GOLD, size="sm")

        # Weak point indicator
        if show_weakness:
            crt.draw_text("[!] CORE VULNERABLE", bar_x, bar_y + 22, color=(255, 80, 80), size="sm")

    def _render_defeat_banner(self, crt: Any):
        """Render victory notification banner."""
        banner_rect = pygame.Rect(80, 110, 320, 50)
        pygame.draw.rect(crt.canvas, (10, 24, 16), banner_rect)
        pygame.draw.rect(crt.canvas, config.COLOR_CRT_GREEN, banner_rect, 2)
        crt.draw_text("SECTOR BOSS NEUTRALIZED", 130, 118, color=config.COLOR_CRT_GREEN, size="lg")
        crt.draw_text("OHIO SECURED // RETURN TO BUNKER", 112, 140, color=config.COLOR_FIBO_GOLD, size="sm")

    def _render_player_death_banner(self, crt: Any):
        """Render casualty notification and retry prompt."""
        banner_rect = pygame.Rect(90, 110, 300, 50)
        pygame.draw.rect(crt.canvas, (28, 8, 8), banner_rect)
        pygame.draw.rect(crt.canvas, config.COLOR_EHMAN_RED, banner_rect, 2)
        crt.draw_text("MATEO FALLEN // CRITICAL CASUALTY", 112, 118, color=config.COLOR_EHMAN_RED, size="sm")
        crt.draw_text("SPACE / CLICK: RETRY", 102, 138, color=config.COLOR_AMBER_1977, size="sm")
