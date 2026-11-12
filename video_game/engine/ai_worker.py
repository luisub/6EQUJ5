"""
MODULE: video_game/engine/ai_worker.py
PURPOSE: Asynchronous, cancellable worker handling AI dialogue streaming,
         offline fallback routes, and queue events off the main game thread.
CALLED BY: CRTTerminalScene in video_game/engine/scenes/terminal.py.
HOW TO MODIFY:
  - To customize AI inference parameters -> pass custom AIAdapter instance.
  - To adjust queue bounds or timeout budgets -> configure worker constructor.
"""

import queue
import threading
import time
import uuid
from typing import Any, Iterator, Optional
from signal_6EQUJ5 import ai_engine
from .ai_adapter import AIAdapter, AIEvent, FALLBACK_LORE_TRANSFERS


class AIWorker:
    """Threaded non-blocking manager for Ollama AI streaming and offline lore fallback."""

    def __init__(
        self,
        adapter: Optional[AIAdapter] = None,
        request_limit: int = 32,
        event_limit: int = 128,
        max_exchanges: int = 12,
        start_thread: bool = True,
    ):
        self.adapter = adapter or AIAdapter()
        self.request_queue: queue.Queue = queue.Queue(maxsize=request_limit)
        self.response_queue: queue.Queue = queue.Queue(maxsize=event_limit)

        self.active_session_id: str = f"sess_{uuid.uuid4().hex[:8]}"
        self.active_civ_id: str = "FASR-001"
        self.history: Optional[ai_engine.ConversationHistory] = None

        self.is_busy: bool = False
        self.exchange_count: int = 0
        self.max_exchanges: int = max_exchanges
        self.fallback_step: int = 0

        self._request_counter: int = 0
        self._seq_counter: int = 0
        self._active_cancel_token: Optional[threading.Event] = None
        self._state_lock = threading.RLock()

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        if start_thread:
            self._thread = threading.Thread(target=self._worker_loop, daemon=True, name="AIWorkerThread")
            self._thread.start()

    def _next_request_id(self) -> str:
        with self._state_lock:
            self._request_counter += 1
            return f"req_{self.active_session_id}_{self._request_counter}"

    def _next_seq(self) -> int:
        with self._state_lock:
            self._seq_counter += 1
            return self._seq_counter

    def _emit_event(self, session_id: str, request_id: str, event_type: str, payload: Any):
        """Put an event into the bounded response queue without blocking indefinitely."""
        event = AIEvent(
            session_id=session_id,
            request_id=request_id,
            seq=self._next_seq(),
            event_type=event_type,
            payload=payload,
            timestamp=time.time(),
        )
        try:
            self.response_queue.put(event, timeout=0.1)
        except queue.Full:
            # Drop older event if saturated to make room for critical lifecycle events
            try:
                self.response_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self.response_queue.put_nowait(event)
            except queue.Full:
                pass

    def start_contact(self, civ_id: str = "FASR-001") -> str:
        """Initiate or switch contact to a target civilization, starting a new session."""
        with self._state_lock:
            # Cooperatively cancel any in-flight request
            if self._active_cancel_token:
                self._active_cancel_token.set()

            self.active_session_id = f"sess_{uuid.uuid4().hex[:8]}"
            self.active_civ_id = civ_id
            self.exchange_count = 0
            self.fallback_step = 0
            self.is_busy = False
            self.history = ai_engine.ConversationHistory(catalog_id=civ_id)

        session_id = self.active_session_id
        intro_req_id = f"init_{session_id}"

        intro = self.adapter.get_initial_greeting(civ_id)
        self._emit_event(session_id, intro_req_id, "STATUS", f"LOCK // {civ_id}")
        self._emit_event(session_id, intro_req_id, "TOKEN", f"[{civ_id}]: {intro}\n")
        self._emit_event(session_id, intro_req_id, "DONE", intro)

        return session_id

    def send_message(self, user_text: str) -> Optional[str]:
        """Submit an operator transmission to the background worker."""
        with self._state_lock:
            if self.is_busy or self.exchange_count >= self.max_exchanges:
                return None

            session_id = self.active_session_id
            civ_id = self.active_civ_id
            request_id = self._next_request_id()

            cancel_token = threading.Event()
            self._active_cancel_token = cancel_token
            self.is_busy = True
            self.exchange_count += 1

        payload_tuple = (session_id, request_id, civ_id, user_text, cancel_token)
        try:
            self.request_queue.put_nowait(payload_tuple)
            return request_id
        except queue.Full:
            with self._state_lock:
                self.is_busy = False
                self.exchange_count -= 1
            self._emit_event(session_id, request_id, "ERROR", "QUEUE_SATURATED")
            return None

    def cancel_current(self) -> bool:
        """Cooperatively cancel the current in-flight stream."""
        with self._state_lock:
            if self._active_cancel_token and not self._active_cancel_token.is_set():
                self._active_cancel_token.set()
                session_id = self.active_session_id
                req_id = f"req_{session_id}_{self._request_counter}"
                self._emit_event(session_id, req_id, "CANCELLED", "User cancelled transmission")
                self.is_busy = False
                return True
        return False

    def poll_events(self) -> Iterator[AIEvent]:
        """
        Yield all queued events for the active session.

        Events from cancelled or superseded sessions are discarded so they
        never reach the caller.
        """
        current_session = self.active_session_id
        while not self.response_queue.empty():
            try:
                event = self.response_queue.get_nowait()
            except queue.Empty:
                break

            # Discard stale events from prior sessions
            if event.session_id == current_session:
                yield event

    def stop(self, timeout: float = 1.0) -> bool:
        """
        Signal background worker to shut down within timeout budget.

        Returns True if thread successfully joined within the budget.
        """
        self._stop_event.set()
        with self._state_lock:
            if self._active_cancel_token:
                self._active_cancel_token.set()

        try:
            self.request_queue.put_nowait(("STOP", None, None, None, None))
        except queue.Full:
            pass

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
            return not self._thread.is_alive()
        return True

    def _worker_loop(self):
        """Background worker thread processing stream requests off the main game loop."""
        while not self._stop_event.is_set():
            try:
                item = self.request_queue.get(timeout=0.05)
            except queue.Empty:
                continue

            req_type = item[0]
            if req_type == "STOP":
                break

            session_id, request_id, civ_id, user_text, cancel_token = item

            # Drop request if session changed or was cancelled before start
            if session_id != self.active_session_id or cancel_token.is_set():
                with self._state_lock:
                    if session_id == self.active_session_id:
                        self.is_busy = False
                continue

            self._process_request(session_id, request_id, civ_id, user_text, cancel_token)

    def _process_request(
        self,
        session_id: str,
        request_id: str,
        civ_id: str,
        user_text: str,
        cancel_token: threading.Event,
    ):
        """Execute stream generator through the adapter with cooperative cancellation."""
        full_tokens = []
        try:
            step = self.fallback_step
            self.fallback_step += 1

            token_stream = self.adapter.stream_dialogue(
                civ_id=civ_id,
                user_text=user_text,
                history=self.history,
                cancel_token=cancel_token,
                fallback_step=step,
            )

            for token in token_stream:
                if self._stop_event.is_set() or cancel_token.is_set() or session_id != self.active_session_id:
                    self._emit_event(session_id, request_id, "CANCELLED", "".join(full_tokens))
                    return

                full_tokens.append(token)
                self._emit_event(session_id, request_id, "TOKEN", token)

            # Successfully completed full stream
            complete_text = "".join(full_tokens)
            self._emit_event(session_id, request_id, "DONE", complete_text)

        except Exception as exc:
            self._emit_event(session_id, request_id, "ERROR", str(exc))

        finally:
            with self._state_lock:
                if session_id == self.active_session_id:
                    self.is_busy = False
