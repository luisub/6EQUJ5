"""
═══════════════════════════════════════════════════════
MODULE: tests/test_engine_boot.py
PURPOSE: Automated Phase 1 smoke tests for CRTRenderer and GameStateMachine.
CALLED BY: pytest (`pytest tests/ -v`).
HOW TO MODIFY:
  - Add scene-specific assertions to test_state_machine_all_scenes_and_mandela_shift().
═══════════════════════════════════════════════════════
"""

from . import FIXTURES_DIR

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402
import pytest  # noqa: E402
from video_game.engine import config  # noqa: E402
from video_game.engine.crt_renderer import CRTRenderer  # noqa: E402
from video_game.tools.preview_assets import export_previews  # noqa: E402
from video_game.engine.state_machine import GameStateMachine  # noqa: E402
from video_game.main import run_game  # noqa: E402


@pytest.fixture(autouse=True)
def isolated_save_directory(tmp_path, monkeypatch):
    monkeypatch.setenv("SIX_GAME_SAVE_DIR", str(tmp_path / "saves"))


def test_crt_renderer_and_scaling():
    """Verify logical and native surfaces, window scaling, and panel/text rendering."""
    pygame.init()
    window_surface = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    crt = CRTRenderer(scale=config.DEFAULT_SCALE)
    assert crt.canvas.get_size() == (480, 270)
    assert crt.render_surface.get_size() == (960, 540)
    assert (crt.win_w, crt.win_h) == (1920, 1080)
    crt.clear(config.COLOR_VOID_BLACK)
    crt.draw_panel((10, 10, 120, 50), title="TEST PANEL")
    crt.draw_text("6EQUJ5", 20, 28, color=config.COLOR_CRT_GREEN)
    crt.trigger_glitch(duration_ms=100, intensity=3)
    crt.update(0.016)
    crt.present(window_surface)
    pygame.quit()


def test_state_machine_all_scenes_and_mandela_shift():
    """Verify all 6 scenes render cleanly and Mandela timeline shift toggles state."""
    pygame.init()
    window_surface = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    crt = CRTRenderer(scale=config.DEFAULT_SCALE)
    machine = GameStateMachine(crt)
    assert machine.campaign.state.unlocked_weapons == ["maser_1420"]
    assert machine.campaign.state.extracted_fragments == []
    assert machine.campaign.state.validation_records == []
    all_states = (
        config.STATE_TITLE_BOOT,
        config.STATE_BUNKER_HUB,
        config.STATE_CRT_TERMINAL,
        config.STATE_SCIENCE_LAB,
        config.STATE_FIELD_OPS,
        config.STATE_BOSS_BOUNTY,
    )
    for state_name in all_states:
        machine.change_state(state_name)
        assert machine.current_state_name == state_name
        machine.update(0.016)
        machine.render()
        crt.present(window_surface)
    assert machine.campaign["timeline_mode"] == "2029_CORE"
    machine.toggle_timeline()
    assert machine.campaign["timeline_mode"] == "1977_ANALOG"
    machine.toggle_timeline()
    assert machine.campaign["timeline_mode"] == "2029_CORE"
    assert len(set(machine.campaign.state.applied_event_ids)) == 2
    pygame.quit()


def test_preview_export_uses_selected_directory(tmp_path):
    """Preview images are generated in a caller-selected temporary directory."""
    paths = export_previews(tmp_path)
    assert len(paths) == 3
    assert all(path.parent == tmp_path and path.is_file() for path in paths)
    assert [pygame.image.load(str(path)).get_size() for path in paths] == [
        (960, 540), (1920, 1080), (1920, 1080)
    ]


def test_main_loop_smoke():
    """Verify main loop runs 5 frames and exits cleanly."""
    frames = run_game(max_frames=5)
    assert frames == 5


def test_keyboard_navigation_lifecycle_and_deferred_transitions(monkeypatch):
    pygame.init()
    pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    machine = GameStateMachine(CRTRenderer(), development=True)
    title = machine.current_scene
    original_handler = title.handle_event
    observations = []

    def title_handler(event):
        original_handler(event)
        observations.append(machine.current_state_name)

    monkeypatch.setattr(title, "handle_event", title_handler)
    machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    assert observations == [config.STATE_TITLE_BOOT]
    assert machine.current_state_name == config.STATE_BUNKER_HUB
    hub = machine.current_scene
    machine.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_RETURN))
    machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN))
    machine.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_DOWN))
    assert hub.opening_story is None
    initial_x = hub.mateo_x
    exits, entries = [], []
    terminal = machine.scenes[config.STATE_CRT_TERMINAL]
    monkeypatch.setattr(hub, "on_exit", lambda: exits.append("hub"))
    monkeypatch.setattr(hub, "on_enter", lambda **kwargs: entries.append("hub"))
    monkeypatch.setattr(terminal, "on_exit", lambda: exits.append("terminal"))
    monkeypatch.setattr(terminal, "on_enter", lambda **kwargs: entries.append("terminal"))
    for _ in range(10):
        machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
        assert machine.current_state_name == config.STATE_CRT_TERMINAL
        machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        assert machine.current_state_name == config.STATE_BUNKER_HUB
    assert exits.count("hub") == exits.count("terminal") == 10
    assert entries.count("hub") == entries.count("terminal") == 10
    assert machine.current_scene is hub and hub.mateo_x == initial_x
    for key, state in ((pygame.K_l, config.STATE_SCIENCE_LAB), (pygame.K_f, config.STATE_FIELD_OPS),
                       (pygame.K_b, config.STATE_BOSS_BOUNTY)):
        machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))
        assert machine.current_state_name == state
        machine.render()
        machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        assert machine.current_state_name == config.STATE_BUNKER_HUB
    machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_c))
    machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_o))
    machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_v))
    machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_q))
    assert (hub.civ_idx, hub.outfit_idx, hub.view_mode) == (1, 1, 1)
    assert machine.campaign["timeline_mode"] == "1977_ANALOG"
    assert len(machine.campaign.state.applied_event_ids) == 1
    update_observations = []

    def request_from_update(dt_seconds):
        machine.change_state(config.STATE_CRT_TERMINAL)
        update_observations.append(machine.current_state_name)

    monkeypatch.setattr(hub, "update", request_from_update)
    machine.update(0.016)
    assert update_observations == [config.STATE_BUNKER_HUB]
    assert machine.current_state_name == config.STATE_CRT_TERMINAL
    machine.change_state(config.STATE_BUNKER_HUB)
    machine.close()
    machine.close()
    assert exits.count("hub") == 15
    pygame.quit()


def test_terminal_and_inspector_do_not_reload_warmed_images(monkeypatch):
    pygame.init()
    pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    original = pygame.image.load
    loads = []

    def count_load(path):
        loads.append(str(path))
        return original(path)

    monkeypatch.setattr(pygame.image, "load", count_load)
    machine = GameStateMachine(CRTRenderer())
    hub = machine.scenes[config.STATE_BUNKER_HUB]
    machine.change_state(config.STATE_BUNKER_HUB)
    hub.view_mode = 1
    machine.render()
    machine.change_state(config.STATE_CRT_TERMINAL)
    machine.render()
    warmed = list(loads)

    def unexpected_resolve(path):
        raise AssertionError(f"A warmed asset was resolved again: {path}")

    monkeypatch.setattr(machine.assets, "_resolve", unexpected_resolve)
    for _ in range(10):
        machine.render()
        machine.change_state(config.STATE_BUNKER_HUB)
        machine.render()
        machine.change_state(config.STATE_CRT_TERMINAL)
    assert loads == warmed
    assert len([p for p in loads if "fasr-001_" in p]) == 3
    machine.close()
    pygame.quit()


def test_seconds_match_recorded_timing_at_30_60_and_120_fps(monkeypatch):
    import json
    import pytest

    fixtures = FIXTURES_DIR / "scene_timing"
    baseline = json.loads((fixtures / "baseline_timing.json").read_text())
    trajectories = json.loads((fixtures / "baseline_trajectories.json").read_text())
    pygame.init()
    pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    for fps in (30, 60, 120):
        machine = GameStateMachine(CRTRenderer())
        title = machine.current_scene
        for _ in range(fps):
            machine.update(1 / fps)
        assert title.elapsed_seconds * 1000 == pytest.approx(baseline[str(fps)]["title_ms"])
        machine.change_state(config.STATE_BUNKER_HUB)
        hub = machine.current_scene
        machine.toggle_timeline()
        machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
        for _ in range(fps // 10):
            machine.update(1 / fps)
        assert machine.crt.glitch_timer_ms == pytest.approx(180)
        for _ in range(fps - fps // 10):
            machine.update(1 / fps)
        assert hub.mateo_x == pytest.approx(baseline[str(fps)]["mateo_x"])
        assert hub.anim_seconds * 1000 == pytest.approx(baseline[str(fps)]["anim_ms"])
        assert hub.pose_idx == baseline[str(fps)]["pose"]
        assert machine.crt.glitch_timer_ms == baseline[str(fps)]["glitch_ms"]
        assert machine.campaign["timeline_mode"] == baseline[str(fps)]["timeline"]
        machine.close()
        machine = GameStateMachine(CRTRenderer())
        machine.change_state(config.STATE_BUNKER_HUB)
        hub = machine.current_scene
        machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
        for frame, expected in enumerate(trajectories[str(fps)]):
            if frame == fps:
                machine.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_RIGHT))
            machine.update(expected["dt_ms"] / 1000.0)
            assert hub.pose_idx == expected["pose"]
            assert hub.mateo_x == pytest.approx(expected["x"])
        machine.close()
    pygame.quit()


def test_missing_or_invalid_required_assets_are_actionable(tmp_path, monkeypatch):
    import json
    import shutil
    import pytest
    from video_game.engine.assets import AssetCache, AssetLoadError

    asset_root = tmp_path / "assets"
    shutil.copytree(config.ASSETS_DIR, asset_root)
    missing = asset_root / "bunker/03_equipment.png"
    missing.unlink()
    monkeypatch.setattr(config, "ASSETS_DIR", asset_root)
    with pytest.raises(AssetLoadError, match="03_equipment.png"):
        run_game(max_frames=1)
    assert not pygame.get_init()
    manifest = asset_root / "civilizations/manifest.json"
    data = json.loads(manifest.read_text())
    data["FASR-001"]["face_png"] = "../../outside.png"
    manifest.write_text(json.dumps(data))
    pygame.init()
    pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    with pytest.raises(AssetLoadError, match="path must stay inside"):
        AssetCache(asset_root).civilization("FASR-001", "face")
    data["FASR-001"]["face_png"] = "fasr-001_face.png"
    manifest.write_text(json.dumps(data))
    pygame.image.save(pygame.Surface((1, 1)), str(asset_root / "civilizations/fasr-001_face.png"))
    with pytest.raises(AssetLoadError, match="Invalid size.*fasr-001_face.png"):
        AssetCache(asset_root).civilization("FASR-001", "face")
    pygame.quit()
