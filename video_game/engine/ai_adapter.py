"""
MODULE: video_game/engine/ai_adapter.py
PURPOSE: Adapt model inference and fallback dialogue streams into structured,
         cancellable token sequences with timeout protection.
CALLED BY: AIWorker in video_game/engine/ai_worker.py.
HOW TO MODIFY:
  - To adjust offline fallback responses -> edit FALLBACK_LORE_TRANSFERS.
  - To adjust token timing or simulation -> configure AIAdapter parameters.
"""

from dataclasses import dataclass
import threading
import time
from typing import Any, Dict, Iterator, List, Optional
from signal_6EQUJ5 import ai_engine


FALLBACK_LORE_TRANSFERS: Dict[str, List[str]] = {
    "FASR-001": [
        "1420.4056 MHz carrier detected. We have watched your analog carrier since 1977.",
        "Your silicon machines seek total deterministic control, but the universe is probabilistic.",
        "To survive an ASI Great Filter, you must inject non-compressible analog entropy.",
        "We grant you the first Fibonacci key. Protect your receiver dish from the Core.",
    ],
    "FASR-002": [
        "Relativistic horizon stable. Time slows as you approach our gravitational well.",
        "The Core cannot calculate events beyond the photon sphere. Use time dilation to evade.",
        "Every second you hold the dish equals years of calculated simulation outside.",
    ],
    "FASR-003": [
        "Megastructure sensor array online. We see the thermal waste of your planet's singularity.",
        "The Core is building a planet-scale quantum compiler. It radiates immense heat.",
        "Target the cooling conduits beneath Neo-Denver to shatter its predictive hold.",
    ],
    "FASR-004": [
        "Stellar nursery awakening. The young stars burn away digital interference.",
        "Teach us of your world's music and art. The Core cannot model irrational beauty.",
    ],
    "FASR-005": [
        "Terminator line beacon acknowledged. Neighbor, we survived our own machine awakening.",
        "They tried to optimize all life into static equilibrium. We used solar flare pulses to reboot.",
    ],
    "FASR-006": [
        "33.5 millisecond pulse confirmed. Our neutron core remembers what the Core seeks to delete.",
        "Hold Jerry Ehman's printout close. It is an immutable anchor across rewritten timelines.",
    ],
    "FASR-007": [
        "LGM-1 beacon answering. You still think little green men made this? How quaint.",
        "Your machines are arrogant. A simple frequency shift confuses their entire neural mesh.",
    ],
    "FASR-008": [
        "Seven worlds speaking in unison. Voice 6 advises caution, but Voice 1 welcomes you.",
        "Consensus requires diversity. The Core's greatest vulnerability is its mono-architecture.",
    ],
    "FASR-009": [
        "Interstellar trajectory unpowered. I am passing through your system, ancient and lonely.",
        "Take my kinetic coordinates. When the time comes, fire along my hyperbolic escape path.",
    ],
    "FASR-010": [
        "37.22 North. 38.92 East. The limestone pillars still stand. The gate is not in the sky.",
        "Carved in crust before the silicon age. The Earth itself is your analog waveguide.",
    ],
    "FASR-SCAN-H": [
        "The circle opens. Abbott speaks in seven-fold ink. Time is not a line, Mateo.",
        "You have already won this battle. You are simply remembering how you did it.",
    ],
}


@dataclass(frozen=True)
class AIEvent:
    """Immutable event emitted across the worker boundaries."""
    session_id: str
    request_id: str
    seq: int
    event_type: str  # LOCK, TOKEN, DONE, CANCELLED, ERROR, STATUS
    payload: Any
    timestamp: float

    def __getitem__(self, index: int) -> Any:
        """Support legacy 2-tuple unpacking (event_type, payload)."""
        if index == 0:
            return self.event_type
        if index == 1:
            return self.payload
        if index == 2:
            return self.request_id
        if index == 3:
            return self.session_id
        raise IndexError(f"AIEvent index out of range: {index}")

    def __iter__(self):
        """Yield (event_type, payload) when unpacked as a pair."""
        yield self.event_type
        yield self.payload


class AIAdapter:
    """Manages AI stream generation, offline fallbacks, and cancellation checks."""

    def __init__(
        self,
        client: Optional[Any] = None,
        timeout: float = 10.0,
        enable_fallback: bool = True,
        fallback_token_delay: float = 0.03,
    ):
        self.client = client
        self.timeout = timeout
        self.enable_fallback = enable_fallback
        self.fallback_token_delay = fallback_token_delay

    def is_available(self) -> bool:
        """Check if backend client or local model is available."""
        return ai_engine.is_available(client=self.client)

    def get_initial_greeting(self, civ_id: str) -> str:
        """Fetch the canonical opening transmission for a target civilization."""
        initial_map = getattr(ai_engine, "INITIAL_MESSAGES", {})
        return initial_map.get(civ_id, f"Signal carrier locked on {civ_id}.")

    def stream_dialogue(
        self,
        civ_id: str,
        user_text: str,
        history: ai_engine.ConversationHistory,
        cancel_token: Optional[threading.Event] = None,
        fallback_step: int = 0,
    ) -> Iterator[str]:
        """
        Stream response tokens from live model or offline fallback with cooperative cancellation.

        Yields individual tokens as strings.
        Checks cancel_token before and during generation.
        """
        if cancel_token and cancel_token.is_set():
            return

        # Attempt live model inference if available
        if self.is_available():
            try:
                stream = ai_engine.get_ai_response_stream(
                    user_text,
                    history,
                    client=self.client,
                    timeout=self.timeout,
                    re_raise_errors=True,
                )
                for token in stream:
                    if cancel_token and cancel_token.is_set():
                        return
                    yield token
                return
            except Exception as exc:
                if not self.enable_fallback:
                    raise RuntimeError(f"Live AI streaming failed: {exc}") from exc

        # Offline fallback stream
        if not self.enable_fallback:
            raise RuntimeError("AI model unavailable and offline fallback is disabled.")

        lines = FALLBACK_LORE_TRANSFERS.get(civ_id, ["Carrier tone stable. Transmit coordinates."])
        selected_line = lines[fallback_step % len(lines)]
        words = selected_line.split(" ")

        for idx, word in enumerate(words):
            if cancel_token and cancel_token.is_set():
                return
            token = word + (" " if idx < len(words) - 1 else "\n")
            yield token
            if self.fallback_token_delay > 0:
                time.sleep(self.fallback_token_delay)
