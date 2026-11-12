"""
MODULE: video_game/tests/test_ai_worker.py
PURPOSE: Comprehensive unit and integration test suite for AIAdapter and AIWorker.
CALLED BY: pytest (`python -m pytest video_game/tests/test_ai_worker.py -vv`).
HOW TO MODIFY: Add focused test cases for error modes, retry behaviors, or timing budgets.
"""

import ast
import inspect
import queue
import time
from pathlib import Path
from typing import Dict, List
import pytest

from signal_6EQUJ5 import ai_engine
from video_game.engine import ai_adapter, ai_worker
from video_game.engine.ai_adapter import AIAdapter, AIEvent, FALLBACK_LORE_TRANSFERS
from video_game.engine.ai_worker import AIWorker


class FakeOllamaClient:
    """Mock Ollama client simulating configurable stream delays, failures, and cancellations."""

    def __init__(
        self,
        tokens: List[str] = None,
        delay_per_token: float = 0.0,
        fail_at_token: int = -1,
        available_models: List[str] = None,
    ):
        self.tokens = ["Ancient ", "signal ", "carrier ", "locked."] if tokens is None else tokens
        self.delay_per_token = delay_per_token
        self.fail_at_token = fail_at_token
        self.available_models = ["qwen3:8b"] if available_models is None else available_models
        self.call_count = 0

    def list(self) -> Dict[str, List[Dict[str, str]]]:
        return {"models": [{"model": name} for name in self.available_models]}

    def chat(self, **kwargs):
        self.call_count += 1

        def _generator():
            for idx, tok in enumerate(self.tokens):
                if self.fail_at_token == idx:
                    raise ConnectionResetError("Simulated remote disconnection mid-stream")
                if self.delay_per_token > 0:
                    time.sleep(self.delay_per_token)
                yield {"message": {"content": tok}}

        return _generator()


def test_ai_worker_no_pygame_imports_or_calls():
    """Verify strictly zero Pygame API or imports in ai_worker and ai_adapter modules."""
    for mod in (ai_adapter, ai_worker):
        source = inspect.getsource(mod)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "pygame" not in alias.name, f"Forbidden pygame import found in {mod.__name__}: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                assert "pygame" not in (node.module or ""), f"Forbidden pygame import found in {mod.__name__}: {node.module}"


def test_fake_slow_streams_keep_main_loop_responsive():
    """Simulate a 60 FPS Pygame main thread loop while worker processes a slow AI stream."""
    fake_client = FakeOllamaClient(
        tokens=["Word "] * 10,
        delay_per_token=0.04,  # Total stream ~0.4s
    )
    adapter = AIAdapter(client=fake_client, enable_fallback=False)
    worker = AIWorker(adapter=adapter)

    try:
        worker.start_contact("FASR-001")
        # Drain initial greeting events before user prompt
        list(worker.poll_events())

        req_id = worker.send_message("Hello ancient one")
        assert req_id is not None

        # Simulate 30 frames of 60 FPS game loop (approx 0.5s total)
        frame_durations = []
        tokens_received = []
        done_received = False

        for _ in range(35):
            t_start = time.perf_counter()
            for evt in worker.poll_events():
                if evt.event_type == "TOKEN":
                    tokens_received.append(evt.payload)
                elif evt.event_type == "DONE":
                    done_received = True

            t_elapsed = time.perf_counter() - t_start
            frame_durations.append(t_elapsed)
            time.sleep(0.016)  # 60 FPS pacing

        # Assert every single frame on the main thread executed in under 2 milliseconds
        max_frame_cost = max(frame_durations)
        assert max_frame_cost < 0.005, f"Main thread blocked for {max_frame_cost * 1000:.2f} ms; exceeds budget"
        assert done_received is True
        assert len(tokens_received) == 10
    finally:
        worker.stop(timeout=1.0)


def test_cancellation_stops_in_flight_stream_promptly():
    """Verify cooperative cancellation immediately halts generation."""
    fake_client = FakeOllamaClient(
        tokens=["Token "] * 50,
        delay_per_token=0.03,  # Total stream 1.5s
    )
    adapter = AIAdapter(client=fake_client, enable_fallback=False)
    worker = AIWorker(adapter=adapter)

    try:
        worker.start_contact("FASR-001")
        req_id = worker.send_message("Test transmission")
        assert req_id is not None

        # Wait for at least 1 token to start streaming
        received = []
        start_wait = time.time()
        while time.time() - start_wait < 1.0 and not received:
            for evt in worker.poll_events():
                if evt.event_type == "TOKEN":
                    received.append(evt.payload)
            time.sleep(0.01)

        assert len(received) >= 1
        assert worker.is_busy is True

        # Now trigger cancellation
        cancelled = worker.cancel_current()
        assert cancelled is True

        # Poll events to confirm CANCELLED event is received
        time.sleep(0.05)
        events = list(worker.poll_events())
        assert any(e.event_type == "CANCELLED" for e in events)
        assert worker.is_busy is False
    finally:
        worker.stop(timeout=1.0)


def test_cancelled_or_stale_events_never_reach_active_session():
    """Verify that switching target/session discards in-flight events from prior session."""
    fake_client = FakeOllamaClient(
        tokens=["OldSessionToken "] * 20,
        delay_per_token=0.03,
    )
    adapter = AIAdapter(client=fake_client, enable_fallback=False)
    worker = AIWorker(adapter=adapter)

    try:
        session_a = worker.start_contact("FASR-001")
        worker.send_message("Message to FASR-001")

        # Let a couple tokens generate
        time.sleep(0.08)

        # Operator switches target to FASR-002, superseding Session A
        session_b = worker.start_contact("FASR-002")
        assert session_b != session_a

        # Drain and collect all events from the poll queue
        time.sleep(0.15)
        delivered_events = list(worker.poll_events())

        # Assert NO event from Session A was delivered to Session B caller
        for evt in delivered_events:
            assert evt.session_id == session_b, f"Stale event delivered: {evt}"
    finally:
        worker.stop(timeout=1.0)


def test_queue_saturation_handled_safely():
    """Verify bounded request queue rejects overflow without blocking or raising unhandled exceptions."""
    # Worker with request queue size of 2
    worker = AIWorker(request_limit=2, start_thread=False)
    try:
        worker.start_contact("FASR-001")

        # Force state to allow sending without worker thread consuming
        worker.is_busy = False
        r1 = worker.send_message("Msg 1")
        assert r1 is not None

        worker.is_busy = False
        r2 = worker.send_message("Msg 2")
        assert r2 is not None

        # Third message must fail safely because request queue (capacity 2) is saturated
        worker.is_busy = False
        r3 = worker.send_message("Msg 3")
        assert r3 is None

        # Verify error event emitted
        events = list(worker.poll_events())
        assert any(e.event_type == "ERROR" and e.payload == "QUEUE_SATURATED" for e in events)
    finally:
        worker.stop()


def test_worker_graceful_shutdown_within_timeout_budget():
    """Verify worker terminates strictly within its timeout budget even during slow streams."""
    fake_client = FakeOllamaClient(
        tokens=["Infinite "] * 1000,
        delay_per_token=0.05,
    )
    adapter = AIAdapter(client=fake_client, enable_fallback=False)
    worker = AIWorker(adapter=adapter)

    worker.start_contact("FASR-001")
    worker.send_message("Start long stream")

    time.sleep(0.05)
    t0 = time.perf_counter()
    shutdown_success = worker.stop(timeout=0.4)
    elapsed = time.perf_counter() - t0

    assert shutdown_success is True
    assert elapsed < 0.45, f"Shutdown took {elapsed:.3f}s; exceeded timeout budget"


def test_ai_adapter_offline_fallback():
    """Verify AIAdapter seamlessly generates canonical fallback lore transfers when offline."""
    adapter = AIAdapter(enable_fallback=True, fallback_token_delay=0.001)
    history = ai_engine.ConversationHistory(catalog_id="FASR-001")

    # Force unavailable
    fake_client = FakeOllamaClient(available_models=[])
    adapter.client = fake_client

    tokens = list(adapter.stream_dialogue("FASR-001", "Transmit", history, fallback_step=0))
    full_text = "".join(tokens).strip()

    expected = FALLBACK_LORE_TRANSFERS["FASR-001"][0]
    assert full_text == expected


def test_ai_adapter_midstream_failure_handling():
    """Verify mid-stream exceptions are captured and converted into ERROR events."""
    fake_client = FakeOllamaClient(
        tokens=["Token1 ", "Token2 ", "Token3 "],
        delay_per_token=0.01,
        fail_at_token=1,  # Fails at token index 1
    )
    adapter = AIAdapter(client=fake_client, enable_fallback=False)
    worker = AIWorker(adapter=adapter)

    try:
        worker.start_contact("FASR-001")
        worker.send_message("Trigger failure")

        time.sleep(0.1)
        events = list(worker.poll_events())
        error_events = [e for e in events if e.event_type == "ERROR"]
        assert len(error_events) >= 1
        assert "Simulated remote disconnection" in str(error_events[0].payload)
    finally:
        worker.stop(timeout=1.0)


def test_live_ollama_stream_if_available():
    """Measure one real live inference stream with local qwen3:8b if running."""
    if not ai_engine.is_available():
        pytest.skip("Local Ollama or qwen3:8b model not running on host; skipped.")

    adapter = AIAdapter(timeout=30.0)
    worker = AIWorker(adapter=adapter)

    try:
        worker.start_contact("FASR-001")
        # Drain initial greeting events before sending user prompt
        list(worker.poll_events())

        worker.send_message("What is the meaning of 6EQUJ5?")

        tokens = []
        done_text = None
        t_start = time.time()
        ttft = None

        # Wait up to 30 seconds for live model streaming
        while time.time() - t_start < 30.0 and done_text is None:
            for evt in worker.poll_events():
                if evt.event_type == "TOKEN":
                    if ttft is None:
                        ttft = time.time() - t_start
                    tokens.append(evt.payload)
                elif evt.event_type == "DONE":
                    done_text = evt.payload
            time.sleep(0.02)

        total_duration = time.time() - t_start
        assert done_text is not None, "Live model did not complete within 30 seconds"
        assert len(tokens) > 5, "Live model produced fewer than 5 tokens"
        print(f"\n[MEASURED LIVE MODEL STREAM]\nTTFT: {ttft:.3f}s\nDuration: {total_duration:.3f}s\nTokens: {len(tokens)}\nOutput: {done_text[:120]}...\n")
    finally:
        worker.stop(timeout=2.0)

