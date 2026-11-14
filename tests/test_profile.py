"""
═══════════════════════════════════════════════════════
MODULE: tests/test_profile.py
PURPOSE: Performance regression tests, frame time budget verifications,
         zero disk-IO in render loop checks, and memory leak regression guards.
CALLED BY: pytest (`pytest tests/test_profile.py -v`).
HOW TO MODIFY:
  - Add scene scenarios to test_scene_frame_budgets().
  - Update memory thresholds if base asset memory footprints change.
═══════════════════════════════════════════════════════
"""

from . import REPO_ROOT

import builtins
import gc
import os
import sys
from pathlib import Path
from typing import List

REPO_ROOT_DIR = REPO_ROOT
if str(REPO_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT_DIR))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402
import pytest  # noqa: E402
from video_game.engine import config  # noqa: E402
from video_game.engine.crt_renderer import CRTRenderer  # noqa: E402
from video_game.engine.settings import SettingsStore  # noqa: E402
from video_game.engine.state_machine import GameStateMachine  # noqa: E402
from video_game.tools.profile_game import BenchmarkProfileSession, get_process_memory_mb  # noqa: E402


@pytest.fixture(autouse=True)
def isolated_save_directory(tmp_path, monkeypatch):
    monkeypatch.setenv("SIX_GAME_SAVE_DIR", str(tmp_path / "saves"))


def test_scene_frame_budgets():
    """Verify that all major Act I scenes execute well within the 8.0ms P95 frame budget."""
    session = BenchmarkProfileSession(scale=config.DEFAULT_SCALE, headless=True)
    try:
        scenes_to_test = [
            config.STATE_BUNKER_HUB,
            config.STATE_CRT_TERMINAL,
            config.STATE_SCIENCE_LAB,
            config.STATE_FIELD_OPS,
            config.STATE_BOSS_BOUNTY,
        ]

        for scene_id in scenes_to_test:
            res = session.run_scene_benchmark(scene_id, duration_seconds=0.6, simulate_input=True)
            total_p95 = res["total_frame_time_ms"]["p95"]
            render_p95 = res["render_time_ms"]["p95"]
            update_p95 = res["update_time_ms"]["p95"]

            # Must run well within the 8.0ms 60 FPS safety budget
            assert total_p95 < 8.0, f"Scene {scene_id} Total P95 was {total_p95}ms, exceeding 8.0ms budget"
            assert render_p95 < 5.0, f"Scene {scene_id} Render P95 was {render_p95}ms, exceeding 5.0ms budget"
            assert update_p95 < 5.0, f"Scene {scene_id} Update P95 was {update_p95}ms, exceeding 5.0ms budget"
            assert res["effective_fps"] > 120.0, f"Scene {scene_id} effective FPS was {res['effective_fps']}"
    finally:
        session.close()


def test_zero_disk_io_during_active_render(monkeypatch):
    """Verify that steady-state rendering and updating triggers zero disk opens."""
    session = BenchmarkProfileSession(scale=config.DEFAULT_SCALE, headless=True)
    try:
        # Load and stabilize field ops scene first
        session.machine.change_state(config.STATE_FIELD_OPS)
        for _ in range(5):
            session.machine.update(0.016)
            session.machine.render()
            session.crt.present(session.window_surf)

        # Intercept builtins.open
        original_open = builtins.open
        opened_files: List[str] = []

        def spy_open(file, *args, **kwargs):
            opened_files.append(str(file))
            return original_open(file, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", spy_open)

        # Run 30 active frames with player locomotion, jumping, shooting
        for frame in range(30):
            session._inject_simulated_inputs(config.STATE_FIELD_OPS, frame)
            session.machine.update(0.016)
            session.machine.render()
            session.crt.present(session.window_surf)

        # Assert no files were opened during the active game loop
        assert len(opened_files) == 0, f"Unexpected disk I/O in render loop: {opened_files}"
    finally:
        session.close()


def test_rapid_scene_transition_memory_stability():
    """Verify memory remains bounded across rapid scene switches."""
    session = BenchmarkProfileSession(scale=config.DEFAULT_SCALE, headless=True)
    try:
        leak_res = session.run_scene_transition_leak_test(cycles=15)
        assert not leak_res["leak_detected"], f"Scene transition leak detected: {leak_res}"
        assert leak_res["memory_delta_mb"] < 10.0, (
            f"Excessive memory growth across transitions: {leak_res['memory_delta_mb']} MB"
        )
    finally:
        session.close()


def test_authored_contact_lifecycle_stability():
    """Verify repeated authored exchanges and scene reentry remain bounded."""
    session = BenchmarkProfileSession(scale=config.DEFAULT_SCALE, headless=True)
    try:
        result = session.run_contact_lifecycle_leak_test(cycles=10)
        assert result["cycles_completed"] == 10
        assert result["exchanges_completed"] == 10
        assert session.machine.current_state_name == config.STATE_BUNKER_HUB
        for civ_id in ("FASR-001", "FASR-002", "FASR-003", "FASR-007", "FASR-010"):
            assert session.machine.contact_session.exchange_counts[civ_id] == 2
        assert not result["leak_detected"], f"Contact lifecycle leak detected: {result}"
        assert result["memory_delta_mb"] < 10.0, (
            f"Excessive memory growth across contact cycles: {result['memory_delta_mb']} MB"
        )
    finally:
        session.close()


def test_cli_isolates_state_and_requires_explicit_output(tmp_path, monkeypatch, capsys):
    """A short real run neither touches player data nor writes unrequested metrics."""
    from video_game.tools import profile_game
    player_dir = tmp_path / "player"
    player_dir.mkdir()
    settings = player_dir / "settings.json"
    settings.write_text('untouched', encoding="utf-8")
    monkeypatch.setenv("SIX_GAME_SAVE_DIR", str(player_dir))
    monkeypatch.chdir(tmp_path)
    profile_game.main(["--headless", "--duration", "0.01", "--scale", "1"])
    assert settings.read_text(encoding="utf-8") == 'untouched'
    assert list(player_dir.iterdir()) == [settings]
    assert not (tmp_path / "metrics.json").exists()
    assert "No metrics file written" in capsys.readouterr().out

    output = tmp_path / "results"
    profile_game.main(["--headless", "--duration", "0.01", "--scale", "1", "--output-dir", str(output)])
    import json
    result = json.loads((output / "metrics.json").read_text())
    assert result["environment"]["display_driver"] == "dummy"
    assert result["environment"]["audio_driver_setting"] == "dummy"
    assert "no AI requests" in result["environment"]["ai_status"]
    assert "synthetic" in result["environment"]["workload"]
    assert result["scenes"]
    assert "enemies" in result["scenes"][config.STATE_FIELD_OPS.lower()]["load_ranges"]
    before = (output / "metrics.json").read_bytes()
    with pytest.raises(FileExistsError):
        profile_game.main(["--headless", "--duration", "0.01", "--scale", "1", "--output-dir", str(output)])
    assert (output / "metrics.json").read_bytes() == before


@pytest.mark.parametrize("options", [
    ["--duration", "0"], ["--duration", "nan"], ["--duration", "inf"],
    ["--duration", "121"], ["--scale", "0"], ["--scale", "5"],
    ["--headless", "--graphical"], ["--mode", "full", "--duration", "1"],
])
def test_cli_rejects_invalid_options_before_initialization(options, monkeypatch):
    from video_game.tools import profile_game
    monkeypatch.setattr(profile_game, "BenchmarkProfileSession", lambda **kw: pytest.fail("initialized"))
    with pytest.raises(SystemExit) as error:
        profile_game.main(options)
    assert error.value.code == 2


def test_graphical_option_is_forwarded(monkeypatch):
    from video_game.tools import profile_game
    class Stop(Exception):
        pass
    def capture(**kwargs):
        assert kwargs["headless"] is False
        raise Stop
    monkeypatch.setattr(profile_game, "BenchmarkProfileSession", capture)
    with pytest.raises(Stop):
        profile_game.main(["--graphical"])


def test_synthetic_keys_move_and_fire_in_real_field(monkeypatch):
    session = BenchmarkProfileSession(scale=1, headless=True)
    try:
        session.machine.change_state(config.STATE_FIELD_OPS)
        scene = session.machine.current_scene
        start_x = scene.player.x
        shots = []
        spawn = scene.projectile_manager.spawn
        def record_spawn(*args, **kwargs):
            result = spawn(*args, **kwargs)
            shots.append(result)
            return result
        monkeypatch.setattr(scene.projectile_manager, "spawn", record_spawn)
        for frame in range(45):
            session.machine.input.begin_frame()
            session._inject_simulated_inputs(config.STATE_FIELD_OPS, frame)
            session.machine.update(1 / 60)
        assert abs(scene.player.x - start_x) > 1
        assert shots, "synthetic fire did not spawn a projectile"
        session.machine.change_state(config.STATE_BOSS_BOUNTY)
        # Boss input is intentionally locked during the authored introduction.
        intro_frame = 0
        while session.machine.current_scene.encounter_intro_remaining > 0:
            session.machine.input.begin_frame()
            session._inject_simulated_inputs(config.STATE_BOSS_BOUNTY, intro_frame)
            assert not session.machine.input.held("fire")
            session.machine.update(1 / 60)
            intro_frame += 1
        session.machine.input.begin_frame()
        session._inject_simulated_inputs(config.STATE_BOSS_BOUNTY, 0)
        assert session.machine.input.pressed("fire")
        assert session.machine.input.held("move_right")
    finally:
        session.close()


def test_cpu_profiler_closes_owned_session_on_error(monkeypatch):
    from video_game.tools import profile_game
    class BrokenMachine:
        def change_state(self, scene_id):
            raise RuntimeError("failure")
    class Session:
        machine = BrokenMachine()
        closed = False
        def close(self):
            self.closed = True
    session = Session()
    monkeypatch.setattr(profile_game, "BenchmarkProfileSession", lambda **kwargs: session)
    with pytest.raises(RuntimeError, match="failure"):
        profile_game.run_cpu_profiler(frames=1)
    assert session.closed
