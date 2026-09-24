"""Backward-compatible simulation exports.

Simulation remains a demo/testing concern in the current refactor; the
production runtime should treat it as extension tooling rather than a live
CCTV intelligence dependency.
"""

from .sensor_generator import ensure_sensor_database, generate_sensor_network
from .simulation_controller import SimulationController

__all__ = ["ensure_sensor_database", "generate_sensor_network", "SimulationController"]
