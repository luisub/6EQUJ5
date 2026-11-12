"""MODULE: video_game/tests/test_pointer_controller_input.py
PURPOSE: Verify pointer and mapped-controller action transitions and focus reset.
CALLED BY: pytest video_game/tests/test_pointer_controller_input.py.
HOW TO MODIFY: Use Pygame events; retain keyboard-charge and device isolation checks.
"""
import pygame
import pytest

from video_game.engine.input import InputManager


@pytest.fixture
def connected_controller(monkeypatch):
    """Simulate SDL device enumeration while exercising actual Pygame events."""
    from pygame._sdl2 import controller

    class Joy:
        def __init__(self, index):
            self.index = index

        def get_instance_id(self):
            return 100 + self.index

    class Device:
        def __init__(self, index):
            self.index = index
            self.closed = False

        def quit(self):
            self.closed = True

    monkeypatch.setattr(controller, 'get_init', lambda: True)
    monkeypatch.setattr(controller, 'is_controller', lambda index: index in (0, 1))
    monkeypatch.setattr(controller, 'Controller', Device)
    monkeypatch.setattr(pygame.joystick, 'Joystick', Joy)
    mapper = InputManager()
    mapper.handle_event(pygame.event.Event(pygame.CONTROLLERDEVICEADDED, device_index=0))
    return mapper


def event(kind, **values):
    return pygame.event.Event(kind, **values)


def test_mouse_auto_fire_edges_are_distinct_from_keyboard_charge():
    mapper = InputManager()
    press = event(pygame.MOUSEBUTTONDOWN, button=1, pos=(712, 333))
    mapper.handle_event(press)
    mapper.handle_event(press)  # Scene and machine may deliver the same physical event.
    assert mapper.pressed('auto_fire') and mapper.held('auto_fire')
    assert not mapper.pressed('fire') and not mapper.held('fire')
    assert mapper.mouse_position == (712, 333) and mapper.aim_source == 'mouse'
    mapper.begin_frame()
    mapper.handle_event(event(pygame.KEYDOWN, key=pygame.K_x))
    mapper.handle_event(event(pygame.MOUSEBUTTONUP, button=1, pos=(714, 335)))
    assert mapper.pressed('fire') and mapper.held('fire')
    assert mapper.released('auto_fire') and not mapper.released('fire')
    mapper.begin_frame()
    mapper.handle_event(event(pygame.KEYUP, key=pygame.K_x))
    assert mapper.released('fire') and not mapper.held('fire')


def test_mouse_right_charges_and_normal_release_remains_an_edge():
    mapper = InputManager()
    mapper.handle_event(event(pygame.MOUSEBUTTONDOWN, button=3, pos=(40, 50)))
    assert mapper.pressed('fire') and mapper.held('fire') and not mapper.held('auto_fire')
    mapper.begin_frame()
    mapper.handle_event(event(pygame.MOUSEMOTION, pos=(41, 51), rel=(1, 1), buttons=(0, 0, 1)))
    mapper.handle_event(event(pygame.KEYDOWN, key=pygame.K_a))
    assert mapper.charge_reset_generation == 0  # Mouse + keyboard are a single desktop input set.
    mapper.handle_event(event(pygame.MOUSEBUTTONUP, button=3, pos=(41, 51)))
    assert mapper.released('fire') and not mapper.held('fire')


def test_controller_mapping_deadzone_source_and_disconnect_isolation(connected_controller):
    mapper = connected_controller
    axis = lambda axis, value: event(pygame.CONTROLLERAXISMOTION, instance_id=100, axis=axis, value=value)
    mapper.handle_event(event(pygame.KEYDOWN, key=pygame.K_d))
    mapper.handle_event(axis(pygame.CONTROLLER_AXIS_LEFTX, 28000))
    mapper.handle_event(axis(pygame.CONTROLLER_AXIS_RIGHTX, 1000))
    assert mapper.held('move_right') and mapper.controller_aim is None
    mapper.handle_event(axis(pygame.CONTROLLER_AXIS_RIGHTX, 24000))
    mapper.handle_event(axis(pygame.CONTROLLER_AXIS_RIGHTY, -18000))
    assert mapper.aim_source == 'controller'
    assert mapper.controller_aim == pytest.approx((0.8, -0.6), abs=0.001)
    mapper.handle_event(axis(pygame.CONTROLLER_AXIS_TRIGGERRIGHT, 20000))
    mapper.handle_event(event(pygame.CONTROLLERBUTTONDOWN, instance_id=100, button=pygame.CONTROLLER_BUTTON_A))
    assert mapper.held('auto_fire') and mapper.held('jump') and mapper.held('confirm')
    mapper.handle_event(event(pygame.MOUSEBUTTONDOWN, button=1, pos=(300, 220)))
    assert mapper.aim_source == 'mouse'
    mapper.begin_frame()
    mapper.handle_event(event(pygame.CONTROLLERDEVICEREMOVED, instance_id=100))
    assert mapper.held('move_right')  # Keyboard contribution survived.
    assert mapper.held('auto_fire') and not mapper.released('auto_fire')  # Mouse still held.
    assert not mapper.held('jump') and mapper.released('jump')
    assert mapper.aim_source == 'mouse' and mapper.controller_aim is None


def test_controller_handoff_and_focus_reset_never_emit_fire_release(connected_controller):
    mapper = connected_controller
    mapper.handle_event(event(pygame.CONTROLLERAXISMOTION, instance_id=100,
                              axis=pygame.CONTROLLER_AXIS_RIGHTY, value=-32768))
    assert mapper.aim_source == 'controller' and mapper.controller_aim == (0.0, -1.0)
    mapper.handle_event(event(pygame.CONTROLLERAXISMOTION, instance_id=100,
                              axis=pygame.CONTROLLER_AXIS_TRIGGERRIGHT, value=32767))
    mapper.handle_event(event(pygame.KEYDOWN, key=pygame.K_x))
    mapper.handle_event(event(pygame.MOUSEBUTTONDOWN, button=1, pos=(10, 20)))
    mapper.release_all()
    for action in ('fire', 'auto_fire', 'move_left', 'jump'):
        assert not mapper.held(action) and not mapper.pressed(action) and not mapper.released(action)
    assert mapper.aim_source is None and mapper.mouse_position is None and mapper.controller_aim is None
    mapper.handle_event(event(pygame.CONTROLLERAXISMOTION, instance_id=100,
                              axis=pygame.CONTROLLER_AXIS_RIGHTX, value=20000))
    assert mapper.aim_source == 'controller' and mapper.controller_aim == (1.0, 0.0)


def test_hotplug_duplicate_idempotence_and_close(connected_controller):
    mapper = connected_controller
    device = mapper._controllers[100]
    mapper.handle_event(event(pygame.CONTROLLERDEVICEADDED, device_index=0))
    assert mapper._controllers[100] is device and not device.closed
    down = event(pygame.CONTROLLERBUTTONDOWN, instance_id=100, button=pygame.CONTROLLER_BUTTON_START)
    mapper.handle_event(down)
    mapper.handle_event(down)
    assert mapper.held('pause') and mapper.pressed('pause')
    mapper.begin_frame()
    mapper.handle_event(down)
    assert not mapper.pressed('pause')
    mapper.close_controllers()
    assert device.closed and not mapper.held('pause')
    mapper.close_controllers()


def test_controller_final_map_and_disconnect_cancels_charge(connected_controller):
    mapper = connected_controller
    axis = lambda axis, value: event(pygame.CONTROLLERAXISMOTION, instance_id=100, axis=axis, value=value)
    mapper.handle_event(axis(pygame.CONTROLLER_AXIS_TRIGGERLEFT, 20000))
    assert mapper.pressed('fire') and mapper.held('fire') and not mapper.held('ability')
    mapper.begin_frame()
    mapper.handle_event(event(pygame.CONTROLLERBUTTONDOWN, instance_id=100,
                              button=pygame.CONTROLLER_BUTTON_LEFTSHOULDER))
    mapper.handle_event(event(pygame.CONTROLLERBUTTONDOWN, instance_id=100,
                              button=pygame.CONTROLLER_BUTTON_RIGHTSHOULDER))
    mapper.handle_event(event(pygame.CONTROLLERBUTTONDOWN, instance_id=100, button=pygame.CONTROLLER_BUTTON_BACK))
    assert mapper.pressed('cycle_weapon') and mapper.pressed('ability') and mapper.pressed('dossier')
    generation = mapper.charge_reset_generation
    mapper.begin_frame()
    mapper.handle_event(event(pygame.CONTROLLERDEVICEREMOVED, instance_id=100))
    assert mapper.charge_reset_generation == generation + 1
    assert not mapper.held('fire') and not mapper.released('fire')


def test_device_handoff_and_explicit_invalidation_signal_without_releasing_fire(connected_controller):
    mapper = connected_controller
    mapper.handle_event(event(pygame.KEYDOWN, key=pygame.K_x))
    mapper.begin_frame()
    initial = mapper.charge_reset_generation
    mapper.handle_event(event(pygame.CONTROLLERBUTTONDOWN, instance_id=100, button=pygame.CONTROLLER_BUTTON_A))
    assert mapper.charge_reset_generation == initial + 1
    assert mapper.held('fire') and not mapper.released('fire')
    mapper.invalidate_charge()  # Caller can invalidate on a profile change without fabricating a release.
    assert mapper.charge_reset_generation == initial + 2 and mapper.held('fire')
    mapper.release_all()
    assert mapper.charge_reset_generation == initial + 3
    assert not mapper.held('fire') and not mapper.released('fire')


def test_controller_remap_clears_only_its_controls_without_charged_release(connected_controller):
    mapper = connected_controller
    mapper.handle_event(event(pygame.MOUSEBUTTONDOWN, button=1, pos=(10, 20)))
    mapper.handle_event(event(pygame.KEYDOWN, key=pygame.K_a))
    mapper.handle_event(event(pygame.CONTROLLERAXISMOTION, instance_id=100,
                              axis=pygame.CONTROLLER_AXIS_LEFTX, value=32767))
    mapper.handle_event(event(pygame.CONTROLLERAXISMOTION, instance_id=100,
                              axis=pygame.CONTROLLER_AXIS_TRIGGERLEFT, value=32767))
    mapper.handle_event(event(pygame.CONTROLLERAXISMOTION, instance_id=100,
                              axis=pygame.CONTROLLER_AXIS_RIGHTX, value=-32768))
    assert mapper.held('move_right') and mapper.held('fire') and mapper.controller_aim == (-1.0, 0.0)
    generation = mapper.charge_reset_generation
    mapper.begin_frame()
    mapper.handle_event(event(pygame.CONTROLLERDEVICEREMAPPED, instance_id=100))
    assert mapper.charge_reset_generation == generation + 1
    assert mapper.held('move_left') and mapper.held('auto_fire')
    assert not mapper.held('move_right') and not mapper.held('fire') and not mapper.released('fire')
    assert mapper.controller_aim is None and mapper.aim_source is None
    assert 100 in mapper._controllers


def test_signed_stick_extrema_and_sdl_small_integer_deadzone(connected_controller):
    mapper = connected_controller
    def axis(value):
        mapper.handle_event(event(pygame.CONTROLLERAXISMOTION, instance_id=100,
                                  axis=pygame.CONTROLLER_AXIS_LEFTX, value=value))
    axis(-32768)
    assert mapper.held('move_left') and not mapper.held('move_right')
    axis(1)
    assert not mapper.held('move_left') and not mapper.held('move_right')
    axis(32767)
    assert not mapper.held('move_left') and mapper.held('move_right')


def test_deadzone_validation_and_safe_uninitialized_start(monkeypatch):
    with pytest.raises(ValueError):
        InputManager(controller_deadzone=1.0)
    mapper = InputManager(controller_deadzone=0.25)
    monkeypatch.setattr(pygame, 'get_init', lambda: False)
    mapper.initialize_controllers()
    mapper.close_controllers()
    assert mapper.controller_aim is None and mapper.aim_source is None
