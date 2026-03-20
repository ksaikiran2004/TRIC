"""
TRIC - Sensor Trigger Engine

Responsibilities:
    - Generate intrusion intensity (with realistic noise)
    - Simulate optional latency
    - Forward intrusion to AlertEngine (with safe handling)
    - Return structured simulation result
"""

from typing import Optional, Literal
from dataclasses import dataclass, field
import random
import time
import uuid

from backend.models.sensor_model import ConfirmedEvent
from backend.alert.alert_engine import AlertEngine


# =========================================================
# TYPES
# =========================================================

SimulationType = Literal["footsteps", "animal", "vehicle"]


@dataclass
class SimulationResult:
    event: Optional[ConfirmedEvent]
    intensity: float
    simulation_type: SimulationType
    latitude: float
    longitude: float
    timestamp: float = field(default_factory=lambda: time.time())
    simulation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    latency: float = 0.0
    error: Optional[str] = None

    @property
    def status(self) -> str:
        return "CONFIRMED" if self.event else "REJECTED"

    @property
    def confidence(self) -> float:
        return self.event.confidence_score if self.event else 0.0


# =========================================================
# RNG (Isolated for reproducibility)
# =========================================================

_rng = random.Random()


def set_seed(seed: int) -> None:
    _rng.seed(seed)


# =========================================================
# CONSTANTS
# =========================================================

INTENSITY_PROFILE = {
    "footsteps": (0.2, 0.4),
    "animal": (0.4, 0.7),
    "vehicle": (0.7, 1.0),
}


# =========================================================
# UTILITIES
# =========================================================

def generate_intensity(simulation_type: SimulationType) -> float:
    """
    Generate signal intensity with signal-dependent Gaussian noise + floor.
    """
    if simulation_type not in INTENSITY_PROFILE:
        raise ValueError(f"Invalid simulation type: {simulation_type}")

    low, high = INTENSITY_PROFILE[simulation_type]
    intensity = _rng.uniform(low, high)

    # Noise floor + scaling
    noise_scale = max(0.01, 0.02 * intensity)
    noise = _rng.gauss(0, noise_scale)

    intensity = max(0.0, min(1.0, intensity + noise))
    return intensity


# =========================================================
# CORE FUNCTIONS
# =========================================================

def simulate_intrusion(
    alert_engine: AlertEngine,
    intrusion_lat: float,
    intrusion_lon: float,
    simulation_type: SimulationType,
    debug: bool = False,
    simulate_latency: bool = False,
    use_gaussian_latency: bool = False,
) -> SimulationResult:
    """
    Simulate a single intrusion event.
    """
    intensity = generate_intensity(simulation_type)

    latency = 0.0
    if simulate_latency:
        if use_gaussian_latency:
            latency = max(0.01, _rng.gauss(0.1, 0.03))
        else:
            latency = _rng.uniform(0.05, 0.2)
        time.sleep(latency)

    error_msg: Optional[str] = None

    try:
        event = alert_engine.process_intrusion(
            intrusion_lat,
            intrusion_lon,
            intensity
        )
    except Exception as e:
        error_msg = str(e)
        if debug:
            print(f"[ERROR] AlertEngine failure: {error_msg}")
        event = None

    if debug:
        if event:
            sensor_count = len(event.sensors_triggered)
            status = f"CONFIRMED ({sensor_count} sensors)"
        else:
            status = "REJECTED"

        print(
            f"[SIM] {simulation_type} @ "
            f"({intrusion_lat:.5f}, {intrusion_lon:.5f}) | "
            f"intensity={intensity:.3f} | "
            f"latency={latency:.3f}s | "
            f"status={status}"
        )

    return SimulationResult(
        event=event,
        intensity=intensity,
        simulation_type=simulation_type,
        latitude=intrusion_lat,
        longitude=intrusion_lon,
        latency=latency,
        error=error_msg
    )


# =========================================================
# PUBLIC APIs (Split Cleanly)
# =========================================================

def run_simulation_step_event(
    alert_engine: AlertEngine,
    intrusion_lat: float,
    intrusion_lon: float,
    simulation_type: SimulationType,
    debug: bool = False,
    simulate_latency: bool = False,
    use_gaussian_latency: bool = False,
) -> Optional[ConfirmedEvent]:
    """
    Returns only the ConfirmedEvent (simple API).
    """
    return simulate_intrusion(
        alert_engine,
        intrusion_lat,
        intrusion_lon,
        simulation_type,
        debug=debug,
        simulate_latency=simulate_latency,
        use_gaussian_latency=use_gaussian_latency
    ).event


def run_simulation_step_full(
    alert_engine: AlertEngine,
    intrusion_lat: float,
    intrusion_lon: float,
    simulation_type: SimulationType,
    debug: bool = False,
    simulate_latency: bool = False,
    use_gaussian_latency: bool = False,
) -> SimulationResult:
    """
    Returns full SimulationResult (advanced API).
    """
    return simulate_intrusion(
        alert_engine,
        intrusion_lat,
        intrusion_lon,
        simulation_type,
        debug=debug,
        simulate_latency=simulate_latency,
        use_gaussian_latency=use_gaussian_latency
    )