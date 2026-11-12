"""
MODULE: video_game/engine/labs/__init__.py
PURPOSE: Package initialization for science workbenches.
CALLED BY: video_game.engine.
HOW TO MODIFY: Export public workbench interfaces without wildcard imports.
"""

from video_game.engine.labs.biosecurity import (
    BiosecurityValidationWorkbench,
    BiosecurityPathogenModel,
    BiosecuritySimulationResult,
    AllocationControls,
    PathogenObservation,
)
from video_game.engine.labs.formal import FormalValidationWorkbench
from video_game.engine.labs.neuro import (
    ConnectomeValidationWorkbench,
    ConnectomeCircuitModel,
    CircuitSimulationResult,
)
from video_game.engine.labs.quantum import (
    QuantumValidationWorkbench,
    QuantumInterferenceModel,
    SimulationResult,
)

__all__ = [
    "FormalValidationWorkbench",
    "QuantumValidationWorkbench",
    "QuantumInterferenceModel",
    "SimulationResult",
    "ConnectomeValidationWorkbench",
    "ConnectomeCircuitModel",
    "CircuitSimulationResult",
    "BiosecurityValidationWorkbench",
    "BiosecurityPathogenModel",
    "BiosecuritySimulationResult",
    "AllocationControls",
    "PathogenObservation",
]
