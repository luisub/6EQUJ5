"""
MODULE: video_game/engine/input.py
PURPOSE: Map keyboard, pointer and SDL-mapped controller events to actions.
CALLED BY: The game state machine and gameplay scenes.
HOW TO MODIFY: Keep device edges idempotent, charge separate and focus reset safe.
"""

import math
import pygame


KEY_BINDINGS = {
    "move_left": (pygame.K_a, pygame.K_LEFT),
    "move_right": (pygame.K_d, pygame.K_RIGHT),
    "jump": (pygame.K_w, pygame.K_UP, pygame.K_SPACE),
    "crouch": (pygame.K_s, pygame.K_DOWN, pygame.K_c),
    "fire": (pygame.K_x, pygame.K_j, pygame.K_LCTRL),
    "ability": (pygame.K_k, pygame.K_LALT),
    "dash": (pygame.K_LSHIFT,),
    "grapple": (pygame.K_g,),
    "cycle_weapon": (pygame.K_q, pygame.K_1),
    "cycle_ability": (pygame.K_r, pygame.K_2),
    "interact": (pygame.K_e,),
    "pause": (pygame.K_F2,),
    "confirm": (pygame.K_RETURN, pygame.K_SPACE),
    "cancel": (pygame.K_ESCAPE,),
    "save": (pygame.K_F5,),
    "auto_fire": (),
    "dossier": (),
}

# SDL's standard controller mapping names physical locations, not vendor labels.
CONTROLLER_BUTTON_BINDINGS = {
    pygame.CONTROLLER_BUTTON_DPAD_LEFT: ("move_left",),
    pygame.CONTROLLER_BUTTON_DPAD_RIGHT: ("move_right",),
    pygame.CONTROLLER_BUTTON_DPAD_UP: ("jump",),
    pygame.CONTROLLER_BUTTON_DPAD_DOWN: ("crouch",),
    pygame.CONTROLLER_BUTTON_A: ("jump", "confirm"),
    pygame.CONTROLLER_BUTTON_B: ("dash", "cancel"),
    pygame.CONTROLLER_BUTTON_X: ("interact",),
    pygame.CONTROLLER_BUTTON_Y: ("grapple",),
    pygame.CONTROLLER_BUTTON_LEFTSHOULDER: ("cycle_weapon",),
    pygame.CONTROLLER_BUTTON_RIGHTSHOULDER: ("ability",),
    pygame.CONTROLLER_BUTTON_START: ("pause",),
    pygame.CONTROLLER_BUTTON_BACK: ("dossier",),
}


class InputManager:
    """Aggregate per-device action transitions; same events can be dispatched twice."""

    def __init__(self, bindings=None, *, controller_deadzone=0.2):
        if not 0.0 <= controller_deadzone < 1.0:
            raise ValueError("controller_deadzone must be in [0, 1)")
        self.bindings = dict(KEY_BINDINGS if bindings is None else bindings)
        self.controller_deadzone = float(controller_deadzone)
        self._keys = set()
        self._handoff_key_actions = {}
        self._mouse_buttons = set()
        self._controllers = {}  # SDL instance id -> open Controller
        self._controller_state = {}  # SDL instance id -> {buttons, axes}
        self._held = set()
        self._pressed = set()
        self._released = set()
        self.mouse_position = None
        self.aim_source = None
        self._aim_controller = None
        self.charge_reset_generation = 0
        self._active_device = None

    def invalidate_charge(self):
        """Signal cancellation without inventing a physical fire-release event."""
        self.charge_reset_generation += 1

    def _select_device(self, device):
        # Keyboard and mouse form one complementary desktop control set.
        if self._active_device is not None and self._active_device != device:
            self.invalidate_charge()
        self._active_device = device

    @staticmethod
    def _axis_value(value):
        # Mapped SDL controller events carry signed 16-bit integers. Accept a
        # normalized float as well for adapters, without treating integer 1 as full-scale.
        normalized = float(value) / 32767.0 if isinstance(value, int) else float(value)
        return max(-1.0, min(1.0, normalized))

    @property
    def controller_aim(self):
        state = self._controller_state.get(self._aim_controller)
        if state is None:
            return None
        x = state["axes"].get(pygame.CONTROLLER_AXIS_RIGHTX, 0.0)
        y = state["axes"].get(pygame.CONTROLLER_AXIS_RIGHTY, 0.0)
        length = math.hypot(x, y)
        if length <= self.controller_deadzone:
            return None
        return (x / length, y / length)

    def initialize_controllers(self):
        """Open present SDL-mapped controllers; safe before SDL init or without devices."""
        if not pygame.get_init():
            return
        try:
            from pygame._sdl2 import controller
            if not controller.get_init():
                controller.init()
            for index in range(controller.get_count()):
                self._open_controller(index)
        except (ImportError, pygame.error):
            return

    def _open_controller(self, index):
        try:
            from pygame._sdl2 import controller
            if not controller.get_init() or not controller.is_controller(index):
                return
            # Identify before opening so duplicated device-added delivery is harmless.
            joystick = pygame.joystick.Joystick(index)
            instance = joystick.get_instance_id()
            if instance in self._controllers:
                return
            device = controller.Controller(index)
            self._controllers[instance] = device
            self._controller_state[instance] = {"buttons": set(), "axes": {}}
        except (ImportError, pygame.error, IndexError, ValueError):
            return

    def _remove_controller(self, instance):
        before = self._held.copy()
        fire_was_released = "fire" in self._released
        device = self._controllers.pop(instance, None)
        self._controller_state.pop(instance, None)
        if device is not None:
            self.invalidate_charge()
            try:
                device.quit()
            except pygame.error:
                pass
        if self._active_device == ("controller", instance):
            self._active_device = None
        if self._aim_controller == instance:
            self._aim_controller = None
            if self.aim_source == "controller":
                self.aim_source = None
        self._apply_edges(before)
        # A disconnected trigger is a cancellation, not a charged shot release.
        if not fire_was_released:
            self._released.discard("fire")

    def close_controllers(self):
        """Close only controllers opened by this mapper, leaving other devices untouched."""
        for instance in tuple(self._controllers):
            self._remove_controller(instance)

    def _remap_controller(self, instance):
        """Neutralize old mapped controls; disconnect-like charge cancellation is not a release."""
        state = self._controller_state.get(instance)
        if state is None:
            return
        before = self._held.copy()
        fire_was_released = "fire" in self._released
        state["buttons"].clear()
        state["axes"].clear()
        self.invalidate_charge()
        if self._aim_controller == instance:
            self._aim_controller = None
            if self.aim_source == "controller":
                self.aim_source = None
        if self._active_device == ("controller", instance):
            self._active_device = None
        self._apply_edges(before)
        if not fire_was_released:
            self._released.discard("fire")

    def begin_frame(self):
        self._pressed.clear()
        self._released.clear()

    def _held_actions(self):
        actions = {action for action, keys in self.bindings.items()
                   if any(key in self._keys and
                          (key not in self._handoff_key_actions or
                           action in self._handoff_key_actions[key]) for key in keys)}
        if 1 in self._mouse_buttons:
            actions.add("auto_fire")
        if 3 in self._mouse_buttons:
            actions.add("fire")
        for state in self._controller_state.values():
            for button in state["buttons"]:
                actions.update(CONTROLLER_BUTTON_BINDINGS.get(button, ()))
            axes = state["axes"]
            movement = axes.get(pygame.CONTROLLER_AXIS_LEFTX, 0.0)
            if movement < -self.controller_deadzone:
                actions.add("move_left")
            elif movement > self.controller_deadzone:
                actions.add("move_right")
            if axes.get(pygame.CONTROLLER_AXIS_TRIGGERRIGHT, 0.0) > 0.5:
                actions.add("auto_fire")
            if axes.get(pygame.CONTROLLER_AXIS_TRIGGERLEFT, 0.0) > 0.5:
                actions.add("fire")
        return actions

    def _apply_edges(self, before):
        after = self._held_actions()
        self._pressed.update(after - before)
        self._released.update(before - after)
        self._held = after

    def handle_event(self, event):
        if event.type == pygame.CONTROLLERDEVICEADDED:
            self._open_controller(event.device_index)
            return
        if event.type == pygame.CONTROLLERDEVICEREMOVED:
            instance = getattr(event, "instance_id", getattr(event, "which", None))
            self._remove_controller(instance)
            return
        if event.type == pygame.CONTROLLERDEVICEREMAPPED:
            instance = getattr(event, "instance_id", getattr(event, "which", None))
            self._remap_controller(instance)
            return
        before = self._held.copy()
        if event.type == pygame.KEYDOWN:
            event.input_fresh = event.key not in self._keys
            self._select_device("desktop")
            self._keys.add(event.key)
        elif event.type == pygame.KEYUP:
            self._keys.discard(event.key)
            self._handoff_key_actions.pop(event.key, None)
        elif event.type == pygame.MOUSEMOTION:
            self._select_device("desktop")
            self.mouse_position = tuple(event.pos)
            self.aim_source = "mouse"
        elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            self.mouse_position = tuple(event.pos)
            if event.type == pygame.MOUSEBUTTONDOWN:
                event.input_fresh = event.button not in self._mouse_buttons
                self._select_device("desktop")
                self.aim_source = "mouse"
                self._mouse_buttons.add(event.button)
            else:
                self._mouse_buttons.discard(event.button)
        elif event.type in (pygame.CONTROLLERAXISMOTION, pygame.CONTROLLERBUTTONDOWN, pygame.CONTROLLERBUTTONUP):
            instance = getattr(event, "instance_id", getattr(event, "which", None))
            state = self._controller_state.get(instance)
            if state is None:
                return
            if event.type == pygame.CONTROLLERAXISMOTION:
                state["axes"][event.axis] = self._axis_value(event.value)
                trigger = event.axis in (pygame.CONTROLLER_AXIS_TRIGGERLEFT, pygame.CONTROLLER_AXIS_TRIGGERRIGHT)
                threshold = 0.5 if trigger else self.controller_deadzone
                if abs(state["axes"][event.axis]) > threshold:
                    self._select_device(("controller", instance))
                if event.axis in (pygame.CONTROLLER_AXIS_RIGHTX, pygame.CONTROLLER_AXIS_RIGHTY):
                    x = state["axes"].get(pygame.CONTROLLER_AXIS_RIGHTX, 0.0)
                    y = state["axes"].get(pygame.CONTROLLER_AXIS_RIGHTY, 0.0)
                    if math.hypot(x, y) > self.controller_deadzone:
                        self._aim_controller = instance
                        self.aim_source = "controller"
            elif event.type == pygame.CONTROLLERBUTTONDOWN:
                self._select_device(("controller", instance))
                state["buttons"].add(event.button)
            else:
                state["buttons"].discard(event.button)
        else:
            return
        self._apply_edges(before)

    def consume_key(self, key):
        """Consume a context-handled key without cancelling other devices.

        A scene calls this after handling Up as an interaction, so that the
        same press cannot also start a jump. Other held jump inputs survive.
        """
        if key not in self._keys:
            return
        before = self._held.copy()
        self._keys.discard(key)
        after = self._held_actions()
        self._pressed.difference_update(before - after)
        self._held = after

    def snapshot_forward_handoff(self, direction=1):
        """Capture held travel/repeat inputs and aim for a walking room handoff."""
        movement = "move_right" if direction > 0 else "move_left"
        allowed = {movement, "auto_fire"}
        keys = {key: frozenset(action for action in allowed
                               if key in self.bindings.get(action, ()))
                for key in self._keys}
        keys = {key: actions for key, actions in keys.items() if actions}
        controllers = {}
        for instance, state in self._controller_state.items():
            axes = state["axes"]
            kept_axes = {}
            if axes.get(pygame.CONTROLLER_AXIS_LEFTX, 0.0) * direction > self.controller_deadzone:
                kept_axes[pygame.CONTROLLER_AXIS_LEFTX] = axes[pygame.CONTROLLER_AXIS_LEFTX]
            if axes.get(pygame.CONTROLLER_AXIS_TRIGGERRIGHT, 0.0) > 0.5:
                kept_axes[pygame.CONTROLLER_AXIS_TRIGGERRIGHT] = axes[pygame.CONTROLLER_AXIS_TRIGGERRIGHT]
            if self.aim_source == "controller" and self._aim_controller == instance:
                for axis in (pygame.CONTROLLER_AXIS_RIGHTX, pygame.CONTROLLER_AXIS_RIGHTY):
                    if axis in axes:
                        kept_axes[axis] = axes[axis]
            buttons = {button for button in state["buttons"]
                       if CONTROLLER_BUTTON_BINDINGS.get(button, ()) == (movement,)}
            if kept_axes or buttons:
                controllers[instance] = {"buttons": buttons, "axes": kept_axes}
        return {"keys": keys, "mouse_left": 1 in self._mouse_buttons,
                "mouse_position": self.mouse_position if self.aim_source == "mouse" else None,
                "aim_source": self.aim_source, "aim_controller": self._aim_controller,
                "controllers": controllers, "active_device": self._active_device}

    def restore_forward_handoff(self, snapshot):
        """Restore a snapshot after release_all, as held only, never as action edges."""
        self._keys.update(snapshot["keys"])
        self._handoff_key_actions.update(snapshot["keys"])
        if snapshot["mouse_left"]:
            self._mouse_buttons.add(1)
        for instance, saved in snapshot["controllers"].items():
            state = self._controller_state.get(instance)
            if state is not None:
                state["buttons"].update(saved["buttons"])
                state["axes"].update(saved["axes"])
        self.mouse_position = snapshot["mouse_position"]
        self.aim_source = snapshot["aim_source"]
        self._aim_controller = snapshot["aim_controller"]
        if self.aim_source == "controller" and self._aim_controller not in self._controller_state:
            self.aim_source = self._aim_controller = None
        self._active_device = snapshot["active_device"]
        self._held = self._held_actions()
        self._pressed.clear()
        self._released.clear()

    def release_all(self):
        """Neutralize all devices and stale action edges without firing on release."""
        self.invalidate_charge()
        self._keys.clear()
        self._handoff_key_actions.clear()
        self._mouse_buttons.clear()
        for state in self._controller_state.values():
            state["buttons"].clear()
            state["axes"].clear()
        self._pressed.clear()
        self._released.clear()
        self._held.clear()
        self.mouse_position = None
        self.aim_source = None
        self._aim_controller = None
        self._active_device = None

    def pressed(self, action):
        return action in self._pressed

    def has_action(self, action):
        return action in self.bindings or action == "auto_fire"

    def held(self, action):
        return action in self._held

    def released(self, action):
        return action in self._released
