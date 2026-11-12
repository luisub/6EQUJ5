"""
MODULE: video_game/tools/profile_game.py
PURPOSE: Synthetic scene benchmark and CPU/peak-memory profiler for Act I.
CALLED BY: Manual verification CLI (`python -m video_game.tools.profile_game`),
           automated test suites, and milestone evidence generation.
HOW TO MODIFY: Add specialized profiling scenarios, adjust frame budgets, or export extra metrics.
"""

import argparse
import cProfile
import gc
import io
import json
import math
import os
import pstats
import platform
import resource
import sys
import time
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pygame

from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.player import PlayerInput
from video_game.engine.settings import SettingsStore, MIN_SCALE, MAX_SCALE
from video_game.engine.save_game import SaveStore
from video_game.engine.state_machine import GameStateMachine


def get_process_memory_mb() -> float:
    """Return process peak resident set size (high-water mark) in megabytes."""
    # macOS resource.getrusage returns bytes; Linux returns kilobytes
    raw_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == "darwin":
        return raw_rss / (1024.0 * 1024.0)
    return raw_rss / 1024.0


def calculate_percentiles(values: List[float]) -> Dict[str, float]:
    """Calculate min, mean, median, p95, p99, and max from a list of float values."""
    if not values:
        return {"min": 0.0, "mean": 0.0, "median": 0.0, "p95": 0.0, "p99": 0.0, "max": 0.0}
    sorted_v = sorted(values)
    n = len(sorted_v)
    mean = sum(sorted_v) / n
    median = sorted_v[n // 2]
    p95 = sorted_v[min(n - 1, int(n * 0.95))]
    p99 = sorted_v[min(n - 1, int(n * 0.99))]
    return {
        "min": round(sorted_v[0], 3),
        "mean": round(mean, 3),
        "median": round(median, 3),
        "p95": round(p95, 3),
        "p99": round(p99, 3),
        "max": round(sorted_v[-1], 3),
    }


class BenchmarkProfileSession:
    """Repeatable traversal, combat, and rendering benchmark session."""

    def __init__(self, scale: int = config.DEFAULT_SCALE, headless: bool = True):
        self.scale = scale
        self.headless = headless
        self._injected_keys = set()
        self._injected_scene = None
        self._temporary_data = tempfile.TemporaryDirectory(prefix="6equj5-profile-")
        self._driver_env = {key: os.environ.get(key) for key in ("SDL_VIDEODRIVER", "SDL_AUDIODRIVER")}
        if headless:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            os.environ["SDL_AUDIODRIVER"] = "dummy"

        try:
            pygame.init()
            self.window_surf = pygame.display.set_mode(
                (config.INTERNAL_WIDTH * scale, config.INTERNAL_HEIGHT * scale)
            )
            self.settings_store = SettingsStore(self._temporary_data.name)
            self.crt = CRTRenderer(scale=scale)
            self.machine = GameStateMachine(
                self.crt, development=True, settings_store=self.settings_store,
                save_store=SaveStore(self._temporary_data.name),
            )
        except Exception:
            self.close()
            raise

    def close(self):
        """Cleanly tear down state machine and pygame contexts."""
        if hasattr(self, "machine") and self.machine:
            self.machine.close()
        pygame.quit()
        for key, value in self._driver_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self._temporary_data.cleanup()

    def environment_metadata(self):
        """Describe observed drivers and the benchmark's limited synthetic workload."""
        mixer = pygame.mixer.get_init()
        return {
            "os": platform.platform(), "machine": platform.machine(),
            "processor": platform.processor() or "unavailable",
            "python_version": sys.version.split()[0], "pygame_version": pygame.version.ver,
            "display_driver": pygame.display.get_driver(),
            "audio_driver_setting": os.environ.get("SDL_AUDIODRIVER", "SDL default"),
            "audio_driver_actual": "dummy" if os.environ.get("SDL_AUDIODRIVER") == "dummy" and mixer else "unavailable or unknown",
            "gpu": "not detected", "ram": "not detected",
            "audio_mixer_initialized": bool(mixer),
            "requested_display_mode": "headless" if self.headless else "graphical",
            "resolution": [config.INTERNAL_WIDTH * self.scale, config.INTERNAL_HEIGHT * self.scale],
            "scale": self.scale, "settings": "fresh defaults in temporary directory",
            "ai_status": "no AI requests initiated by CLI",
            "workload": "uncapped loop, fixed 1/60 s updates, synthetic keyboard transitions; actor load sampled after each update, not controlled. Catwalk starts without repaired flag or active defense waves.",
            "memory_metric": "process peak RSS (high-water mark), not current RSS",
            "limitations": "Not a normal-input playthrough or representative release performance certification; no frame limiter sleep or live dialogue measured.",
        }

    def run_scene_benchmark(
        self,
        scene_id: str,
        duration_seconds: float = 5.0,
        simulate_input: bool = True,
        room_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute high-frequency benchmark on a target scene.
        Measures update time, render time, present time, and memory usage per frame.
        """
        gc.collect()
        initial_mem = get_process_memory_mb()

        # Switch to requested scene
        if room_override and scene_id == config.STATE_FIELD_OPS:
            self.machine.change_state(scene_id, room=room_override)
        else:
            self.machine.change_state(scene_id)

        self._reset_injected_inputs()
        load_samples = []
        update_times: List[float] = []
        render_times: List[float] = []
        present_times: List[float] = []
        total_frame_times: List[float] = []

        fixed_dt = 1.0 / 60.0
        start_time = time.perf_counter()
        elapsed = 0.0
        frame_idx = 0

        while elapsed < duration_seconds:
            frame_start = time.perf_counter()

            # 1. Simulate physical key transitions if requested
            self.machine.input.begin_frame()
            if simulate_input:
                self._inject_simulated_inputs(scene_id, frame_idx)

            # 2. Update phase
            t0 = time.perf_counter()
            self.machine.update(fixed_dt)
            t1 = time.perf_counter()
            load_samples.append(self._scene_load())
            update_ms = (t1 - t0) * 1000.0

            # 3. Render phase
            t2 = time.perf_counter()
            self.machine.render()
            t3 = time.perf_counter()
            render_ms = (t3 - t2) * 1000.0

            # 4. Present phase
            t4 = time.perf_counter()
            self.crt.present(self.window_surf)
            pygame.display.flip()
            t5 = time.perf_counter()
            present_ms = (t5 - t4) * 1000.0

            total_ms = (t5 - frame_start) * 1000.0

            update_times.append(update_ms)
            render_times.append(render_ms)
            present_times.append(present_ms)
            total_frame_times.append(total_ms)

            frame_idx += 1
            elapsed = time.perf_counter() - start_time

        final_mem = get_process_memory_mb()

        return {
            "scene_id": scene_id,
            "load_ranges": {name: {"min": min(sample[name] for sample in load_samples), "max": max(sample[name] for sample in load_samples)} for name in load_samples[0]} if load_samples else {},
            "room": room_override or "default",
            "frames_measured": frame_idx,
            "duration_measured_s": round(elapsed, 3),
            "effective_fps": round(frame_idx / max(0.001, elapsed), 1),
            "memory_start_mb": round(initial_mem, 2),
            "memory_end_mb": round(final_mem, 2),
            "memory_delta_mb": round(final_mem - initial_mem, 2),
            "update_time_ms": calculate_percentiles(update_times),
            "render_time_ms": calculate_percentiles(render_times),
            "present_time_ms": calculate_percentiles(present_times),
            "total_frame_time_ms": calculate_percentiles(total_frame_times),
        }

    def _reset_injected_inputs(self):
        """Forget keys after a scene switch; the state machine releases its input."""
        self.machine.input.release_all()
        self._injected_keys.clear()
        self._injected_scene = self.machine.current_scene

    def _inject_simulated_inputs(self, scene_id: str, frame_idx: int):
        """Send deterministic key transitions through the normal event dispatcher."""
        if self._injected_scene is not self.machine.current_scene:
            self._reset_injected_inputs()
        desired = set()
        if scene_id in (config.STATE_FIELD_OPS, config.STATE_BOSS_BOUNTY):
            desired.add(pygame.K_d if (frame_idx // 60) % 2 == 0 else pygame.K_a)
            if frame_idx % 90 < 20:
                desired.add(pygame.K_SPACE)
            if frame_idx % 120 < 15:
                desired.add(pygame.K_s)
            if frame_idx % 40 < 30:
                desired.add(pygame.K_x)
        for key in sorted(self._injected_keys - desired):
            self.machine.handle_event(pygame.event.Event(pygame.KEYUP, key=key))
        for key in sorted(desired - self._injected_keys):
            self.machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))
        self._injected_keys = desired
        if scene_id == config.STATE_CRT_TERMINAL:
            scene = self.machine.current_scene
            if hasattr(scene, "target_mhz"):
                scene.carrier_mhz = 1420.0 + 5.0 * math.sin(frame_idx * 0.05)

    def _scene_load(self):
        """Sample observable active actors after an update, where supported."""
        scene = self.machine.current_scene
        if hasattr(scene, "enemy_manager"):
            return {"enemies": len(scene.enemy_manager.enemies),
                    "enemy_projectiles": len(scene.enemy_manager.projectiles),
                    "player_projectiles": len(scene.projectile_manager.projectiles)}
        if hasattr(scene, "boss") and hasattr(scene, "proj_mgr"):
            return {"bosses_alive": int(not scene.boss.is_dead),
                    "boss_projectiles": len(scene.boss.projectiles),
                    "player_projectiles": len(scene.proj_mgr.projectiles)}
        return {}

    def run_scene_transition_leak_test(self, cycles: int = 50) -> Dict[str, Any]:
        """Rapidly cycle through all scenes and measure memory stability."""
        gc.collect()
        start_mem = get_process_memory_mb()
        scenes = [
            config.STATE_TITLE_BOOT,
            config.STATE_BUNKER_HUB,
            config.STATE_CRT_TERMINAL,
            config.STATE_SCIENCE_LAB,
            config.STATE_FIELD_OPS,
            config.STATE_BOSS_BOUNTY,
        ]

        mem_samples: List[float] = []

        for cycle in range(cycles):
            for s in scenes:
                self.machine.change_state(s)
                # Execute 2 simulated frames
                self.machine.update(0.016)
                self.machine.render()
                self.crt.present(self.window_surf)

            if cycle % 10 == 0 or cycle == cycles - 1:
                gc.collect()
                mem_samples.append(round(get_process_memory_mb(), 2))

        gc.collect()
        end_mem = get_process_memory_mb()

        return {
            "test": "scene_transition_leak",
            "cycles_completed": cycles,
            "total_transitions": cycles * len(scenes),
            "memory_start_mb": round(start_mem, 2),
            "memory_end_mb": round(end_mem, 2),
            "memory_delta_mb": round(end_mem - start_mem, 2),
            "memory_samples_mb": mem_samples,
            "leak_detected": (end_mem - start_mem) > 15.0,
        }

    def run_terminal_streaming_leak_test(self, cycles: int = 30) -> Dict[str, Any]:
        """Initiate and cancel AI worker contact sessions repeatedly."""
        gc.collect()
        start_mem = get_process_memory_mb()
        self.machine.change_state(config.STATE_CRT_TERMINAL)
        terminal_scene = self.machine.current_scene

        civ_ids = ["FASR-001", "FASR-002", "FASR-003", "FASR-007", "FASR-010"]

        for cycle in range(cycles):
            civ = civ_ids[cycle % len(civ_ids)]
            if hasattr(terminal_scene, "session") and terminal_scene.session:
                terminal_scene.session.switch_target(civ)
                terminal_scene.session.send_message("TEST PROFILER STREAM CANCELLATION")

            # Advance 5 frames to start thread worker
            for _ in range(5):
                self.machine.update(0.016)
                self.machine.render()
                self.crt.present(self.window_surf)

            # Interrupt / cancel
            if hasattr(terminal_scene, "session") and terminal_scene.session:
                terminal_scene.session.cancel_transmission()

        gc.collect()
        end_mem = get_process_memory_mb()

        return {
            "test": "terminal_streaming_cancellation_leak",
            "cycles_completed": cycles,
            "memory_start_mb": round(start_mem, 2),
            "memory_end_mb": round(end_mem, 2),
            "memory_delta_mb": round(end_mem - start_mem, 2),
            "leak_detected": (end_mem - start_mem) > 12.0,
        }

    def run_120s_comprehensive_protocol(self) -> Dict[str, Any]:
        """
        Execute a synthetic 120-second scene sweep; no dialogue is initiated.
        """
        print("Starting synthetic 120-second scene sweep...")
        start_total = time.perf_counter()
        gc.collect()
        start_mem = get_process_memory_mb()

        suite_results: Dict[str, Any] = {}

        # 1. Title & Boot (5s)
        print("  [1/6] Profiling TitleBootScene (5s)...")
        suite_results["title_boot"] = self.run_scene_benchmark(config.STATE_TITLE_BOOT, 5.0)

        # 2. Bunker Hub & Station Exploration (15s)
        print("  [2/6] Profiling BunkerHubScene (15s)...")
        suite_results["bunker_hub"] = self.run_scene_benchmark(config.STATE_BUNKER_HUB, 15.0)

        # 3. CRT Terminal & AI Streaming (20s)
        print("  [3/6] Profiling CRTTerminalScene without dialogue streaming (20s)...")
        suite_results["crt_terminal"] = self.run_scene_benchmark(config.STATE_CRT_TERMINAL, 20.0)

        # 4. Science Lab Formal Workbench (15s)
        print("  [4/6] Profiling ScienceLabScene (15s)...")
        suite_results["science_lab"] = self.run_scene_benchmark(config.STATE_SCIENCE_LAB, 15.0)

        # 5. Field Ops Traversal & Heavy Combat (35s)
        print("  [5/6] Profiling FieldOpsScene synthetic inputs (35s)...")
        # Sub-test approach trench
        res_approach = self.run_scene_benchmark(config.STATE_FIELD_OPS, 15.0, room_override="act_01/approach.json")
        # Catwalk uses a fresh campaign; defense waves are not activated.
        res_catwalk = self.run_scene_benchmark(config.STATE_FIELD_OPS, 20.0, room_override="act_01/dish_catwalk.json")
        suite_results["field_ops_approach"] = res_approach
        suite_results["field_ops_catwalk"] = res_catwalk

        # 6. Boss Greenkeeper Bounty Encounter (30s)
        print("  [6/6] Profiling BossScene Core Warden Greenkeeper (30s)...")
        suite_results["boss_bounty"] = self.run_scene_benchmark(config.STATE_BOSS_BOUNTY, 30.0)

        gc.collect()
        end_mem = get_process_memory_mb()
        total_time = time.perf_counter() - start_total

        return {
            "protocol": "120s_synthetic_scene_sweep",
            "total_duration_s": round(total_time, 2),
            "memory_start_mb": round(start_mem, 2),
            "memory_end_mb": round(end_mem, 2),
            "memory_delta_mb": round(end_mem - start_mem, 2),
            "scenes": suite_results,
        }


def format_performance_table(suite_data: Dict[str, Any]) -> str:
    """Format benchmark results into a clean markdown table."""
    lines = [
        "| Scene / Benchmark | Frames | FPS | Update P95 | Render P95 | Present P95 | Total P95 | Max Frame | Memory Δ |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    scenes = suite_data.get("scenes", {})
    for name, data in scenes.items():
        frames = data.get("frames_measured", 0)
        fps = data.get("effective_fps", 0.0)
        u_p95 = data.get("update_time_ms", {}).get("p95", 0.0)
        r_p95 = data.get("render_time_ms", {}).get("p95", 0.0)
        p_p95 = data.get("present_time_ms", {}).get("p95", 0.0)
        t_p95 = data.get("total_frame_time_ms", {}).get("p95", 0.0)
        t_max = data.get("total_frame_time_ms", {}).get("max", 0.0)
        mem_d = data.get("memory_delta_mb", 0.0)

        lines.append(
            f"| `{name}` | {frames} | **{fps}** | {u_p95}ms | {r_p95}ms | {p_p95}ms | **{t_p95}ms** | {t_max}ms | {mem_d:+.2f}MB |"
        )

    return "\n".join(lines)


def run_cpu_profiler(scene_id: str = config.STATE_FIELD_OPS, frames: int = 180, session=None) -> str:
    """Run cProfile on the game loop and return formatted top 15 hot functions."""
    owns_session = session is None
    if owns_session:
        session = BenchmarkProfileSession(scale=config.DEFAULT_SCALE, headless=True)
    profiler = cProfile.Profile()
    try:
        profiler.enable()
        session.machine.change_state(scene_id)
        session._reset_injected_inputs()
        for f in range(frames):
            session.machine.input.begin_frame()
            session._inject_simulated_inputs(scene_id, f)
            session.machine.update(0.016)
            session.machine.render()
            session.crt.present(session.window_surf)
    finally:
        profiler.disable()
        if owns_session:
            session.close()

    stream = io.StringIO()
    pstats.Stats(profiler, stream=stream).sort_stats("cumulative").print_stats(20)
    return stream.getvalue()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Act I Performance Benchmarking and Profiling Tool")
    parser.add_argument("--mode", choices=["quick", "full", "leak", "profile"], default="quick")
    parser.add_argument("--duration", type=float, default=5.0)
    parser.add_argument("--scale", type=int, default=config.DEFAULT_SCALE)
    display = parser.add_mutually_exclusive_group()
    display.add_argument("--headless", dest="headless", action="store_true", help="Force dummy SDL video and audio (default)")
    display.add_argument("--graphical", dest="headless", action="store_false", help="Use the configured SDL display and audio drivers")
    parser.set_defaults(headless=True)
    parser.add_argument("--output-dir", type=Path, help="Explicit directory for metrics.json; otherwise print only")
    args = parser.parse_args(argv)
    if not math.isfinite(args.duration) or not 0 < args.duration <= 120:
        parser.error("--duration must be finite and in (0, 120]")
    if not MIN_SCALE <= args.scale <= MAX_SCALE:
        parser.error(f"--scale must be between {MIN_SCALE} and {MAX_SCALE}")
    if args.mode != "quick" and args.duration != 5.0:
        parser.error("--duration applies only to quick mode")

    if args.output_dir is not None and (args.output_dir / "metrics.json").exists():
        raise FileExistsError(f"Metrics already exist: {args.output_dir / 'metrics.json'}")

    session = BenchmarkProfileSession(scale=args.scale, headless=args.headless)

    print("═══════════════════════════════════════════════════════════════")
    print(f" 6EQUJ5 ACT I PERFORMANCE BENCHMARK // MODE: {args.mode.upper()}")
    print(f" Platform: {sys.platform} | Python: {sys.version.split()[0]} | Pygame: {pygame.version.ver}")
    print(f" Native Canvas: {config.INTERNAL_WIDTH}x{config.INTERNAL_HEIGHT} | Window: {config.INTERNAL_WIDTH*args.scale}x{config.INTERNAL_HEIGHT*args.scale} ({args.scale}x)")
    print("═══════════════════════════════════════════════════════════════")

    report_payload: Dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "mode": args.mode, "environment": session.environment_metadata(),
    }

    try:
        if args.mode == "quick":
            print(f"\nExecuting Quick Benchmark ({args.duration}s per scene)...")
            scenes_data = {}
            for s in [config.STATE_BUNKER_HUB, config.STATE_CRT_TERMINAL, config.STATE_FIELD_OPS, config.STATE_BOSS_BOUNTY]:
                scenes_data[s.lower()] = session.run_scene_benchmark(s, duration_seconds=args.duration)
            report_payload["scenes"] = scenes_data
            print(format_performance_table(report_payload))

        elif args.mode == "full":
            results = session.run_120s_comprehensive_protocol()
            report_payload.update(results)
            print("\n" + format_performance_table(report_payload))

            leak_res = session.run_scene_transition_leak_test(50)
            leak_res.pop("leak_detected", None)
            report_payload["transition_leak"] = leak_res
            print(f"\nScene Transitions (50 cycles / 300 transitions): Start={leak_res['memory_start_mb']}MB, End={leak_res['memory_end_mb']}MB (peak RSS Δ {leak_res['memory_delta_mb']:+.2f}MB; not a leak verdict)")

            report_payload["cancellation_test"] = "skipped: CLI does not initiate AI requests"

        elif args.mode == "leak":
            leak_res = session.run_scene_transition_leak_test(100)
            leak_res.pop("leak_detected", None)
            report_payload["transition_leak"] = leak_res
            report_payload["cancellation_test"] = "skipped: CLI does not initiate AI requests"
            print(f"Scene transitions (100 cycles): peak RSS change {leak_res['memory_delta_mb']:+.2f}MB; this is not a leak verdict")

        elif args.mode == "profile":
            print("\nRunning cProfile on Field Combat Stress (180 frames)...")
            hotspots = run_cpu_profiler(config.STATE_FIELD_OPS, frames=180, session=session)
            print(hotspots[:1500])
            report_payload["hotspots"] = hotspots

        if args.output_dir is not None:
            args.output_dir.mkdir(parents=True, exist_ok=True)
            out_json = args.output_dir / "metrics.json"
            # Avoid overwriting earlier measurements even in the chosen directory.
            with out_json.open("x", encoding="utf-8") as stream:
                json.dump(report_payload, stream, indent=2)
                stream.write("\n")
            print(f"\nSaved metrics: {out_json}")
        else:
            print("\nNo metrics file written (provide --output-dir to save).")

    finally:
        session.close()


if __name__ == "__main__":
    main()
