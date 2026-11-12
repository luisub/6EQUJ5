"""PURPOSE: Connect field reality rooms, relay controls and durable room snapshots.
CALLED BY: FieldOpsScene lifecycle, input, update and rendering.
HOW TO MODIFY: Keep room mutations in MandelaWorld/TemporalRelay and save through Campaign.
"""
from copy import deepcopy
import pygame
from .mandela_world import MandelaWorld
from .temporal_relay import TemporalRelay
from .ui.text import wrap_text_chars


class FieldReality:
    """Own the active room's reality controller, relay panel and save boundary."""

    def __init__(self, scene):
        self.scene = scene
        self.world = None
        self.relay = None
        self.panel_open = False
        self.message_index = 0

    def load(self):
        s = self.scene
        self.world = None
        self.relay = None
        self.panel_open = False
        if s.room.room_id not in ('act_01_mandela_test', 'act_04_dodleston_relay'):
            return
        self.world = MandelaWorld(s.room, campaign=s.machine.campaign)
        saved = s.machine.campaign.state.world_states.get(s.room.room_id, {})
        if saved.get('collision_layers'):
            s.room.timeline_collision_layers = deepcopy(saved['collision_layers'])
        for obj in s.room.objects:
            obj.properties.update(saved.get('objects', {}).get(obj.id, {}))
        if saved.get('world'):
            self.world.from_dict(saved['world'])
        if s.room.room_id == 'act_04_dodleston_relay':
            self.relay = TemporalRelay(s.machine.campaign)

    def persist(self):
        if self.world is None:
            return
        s = self.scene
        snapshot = {'world': self.world.to_dict(),
                    'collision_layers': deepcopy(s.room.timeline_collision_layers),
                    'objects': {obj.id: deepcopy(obj.properties) for obj in s.room.objects}}
        if self.relay:
            snapshot['relay'] = self.relay.to_dict()
        s.machine.campaign.store_world_state(s.room.room_id, snapshot)

    def handle_event(self, event):
        if not self.world or event.type != pygame.KEYDOWN:
            return False
        s = self.scene
        if self.panel_open:
            if event.key in (pygame.K_ESCAPE, pygame.K_e):
                self.panel_open = False
            elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                self.message_index += -1 if event.key == pygame.K_LEFT else 1
            elif event.key == pygame.K_r:
                self.relay.recalibrate_puzzles(self.world, s.player)
                self.persist()
                s.machine.save_checkpoint()
            elif event.key in (pygame.K_1, pygame.K_2):
                actions = self.relay.get_available_actions()
                index = event.key - pygame.K_1
                if index < len(actions):
                    ok, msg = self.relay.apply_action(actions[index].id, self.world, s.player)
                    s.objective_tracker.post_notification('RELAY', msg, 'success' if ok else 'warning')
                    self.persist()
                    s.machine.save_checkpoint()
            return True
        if event.key == pygame.K_t:
            target = '1977_ANALOG' if self.world.active_timeline == '2029_CORE' else '2029_CORE'
            result = self.world.swap_timeline(target, s.player, actors=[e for e in s.enemy_manager.enemies if not e.is_dead])
            s.objective_tracker.post_notification('TIMELINE', result.reason, 'success' if result.success else 'warning')
            if result.success:
                self.persist()
                s.machine.save_checkpoint()
            return True
        if event.key == pygame.K_e and self.relay and abs(s.player.x - 96) < 56:
            self.panel_open = True
            s.machine.input.release_all()
            s.keys_held.clear()
            return True
        return False

    def update(self, dt):
        if not self.world:
            return
        s = self.scene
        self.world.update(dt, s.player)
        for obj in s.room.get_objects_for_timeline(self.world.active_timeline):
            if obj.type != 'pickup' or not s.player.rect.colliderect(pygame.Rect(obj.x, obj.y, obj.width, obj.height)):
                continue
            if obj.properties.get('spawned', True) is False:
                continue
            if self.world.collect_pickup(obj.id, s.player) is not None:
                self.persist()
                s.machine.save_checkpoint()

    def render_panel(self, crt):
        if not self.panel_open:
            return
        crt.draw_panel((10, 52, 460, 190), title='DODLESTON RELAY // 1985 / 2029 / 2031')
        messages = self.relay.get_visible_messages()
        msg = messages[self.message_index % len(messages)]
        for i, line in enumerate(wrap_text_chars(f'{msg.era}: {msg.text}', 67)[:8]):
            crt.draw_text(line, 18, 70 + i * 11)
        for i, action in enumerate(self.relay.get_available_actions()):
            crt.draw_text(f'[{i+1}] {action.label[:62]}', 18, 166 + i * 12)
        crt.draw_text('[LEFT/RIGHT] MESSAGES  [R] RECOVER  [E/ESC] CLOSE', 18, 222)
