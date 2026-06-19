"""
TRIC - Sensor Trigger Engine

Responsibilities:
    - Generate intrusion intensity (with realistic noise)
    - Simulate optional latency
    - Forward intrusion to AlertEngine (with safe handling)
    - Return structured simulation result
    - [NEW] Safely log confirmed events to persistent Black Box (tric.db)
"""

from typing import Optional, Literal
from dataclasses import dataclass, field
import random
import time
import uuid
import sqlite3
import os
from datetime import datetime

from backend.models.sensor_model import ConfirmedEvent
from backend.confirmation.alert_engine import AlertEngine
from backend.config import Config

# =========================================================
# TYPES
# =========================================================

SimulationType = Literal["human", "animal", "vehicle"]

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

INTENSITY_PROFILE = Config.simulation.INTENSITY_PROFILE

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
    noise_scale = max(
        Config.simulation.NOISE_FLOOR,
        Config.simulation.NOISE_SCALE_FACTOR * intensity
    )
    noise = _rng.gauss(0, noise_scale)

    intensity = max(0.0, min(1.0, intensity + noise))
    return intensity

def log_simulation_to_db(result: SimulationResult) -> None:
    """
    [NEW] Silently logs confirmed intrusion events to the SQLite logs table.
    Decoupled from main execution to prevent interference with AlertEngine.
    """
    if not result.event:
        return 

    # Dynamic path resolution to data/tric.db
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '../../'))
    db_path = os.path.join(project_root, 'data', 'tric.db')

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Guard clause to ensure table exists
        cursor.execute('''CREATE TABLE IF NOT EXISTS logs 
                          (id INTEGER PRIMARY KEY, timestamp DATETIME, sensor_id INTEGER, event_type TEXT)''')

        timestamp_str = datetime.fromtimestamp(result.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        event_type = f"INTRUSION_{result.simulation_type.upper()}"

        # Safely extract sensor IDs from the ConfirmedEvent
        sensors = getattr(result.event, 'sensors_triggered', [])
        for sensor in sensors:
            s_id = getattr(sensor, 'id', getattr(sensor, 'sensor_id', 0))
            cursor.execute("INSERT INTO logs (timestamp, sensor_id, event_type) VALUES (?, ?, ?)", 
                           (timestamp_str, s_id, event_type))

        conn.commit()
    except Exception as e:
        print(f"[DB ERROR] Failed to write to TRIC Black Box: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

# =========================================================
# CORE FUNCTIONS
# =========================================================

def simulate_intrusion(
    alert_engine: "AlertEngine" = None,
    intrusion_lat: float = 0.0,
    intrusion_lon: float = 0.0,
    simulation_type: "SimulationType" = None,
    debug: bool = False,
    simulate_latency: bool = False,
    use_gaussian_latency: bool = False,
    **kwargs
) -> SimulationResult:
    """
    Simulate a single intrusion event.
    """
    intensity = generate_intensity(simulation_type)

    latency = 0.0
    if simulate_latency:
        if use_gaussian_latency:
            latency = max(
                Config.simulation.MIN_LATENCY,
                _rng.gauss(
                    Config.simulation.GAUSSIAN_LATENCY_MEAN,
                    Config.simulation.GAUSSIAN_LATENCY_STD
                )
            )
        else:
            latency = _rng.uniform(
                Config.simulation.UNIFORM_LATENCY_MIN,
                Config.simulation.UNIFORM_LATENCY_MAX
            )
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
            sensor_count = len(getattr(event, 'sensors_triggered', []))
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

    result = SimulationResult(
        event=event,
        intensity=intensity,
        simulation_type=simulation_type,
        latitude=intrusion_lat,
        longitude=intrusion_lon,
        latency=latency,
        error=error_msg
    )

    # [NEW] Forward to persistence layer
    if event:
        log_simulation_to_db(result)

    return result

# =========================================================
# PUBLIC APIs
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
    return simulate_intrusion(
        alert_engine,
        intrusion_lat,
        intrusion_lon,
        simulation_type,
        debug=debug,
        simulate_latency=simulate_latency,
        use_gaussian_latency=use_gaussian_latency
    )