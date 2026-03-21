"""
TRIC - Simulation Controller

Pure orchestration layer for running intrusion simulations.
"""

import threading
import random
from typing import List, Optional, Callable

from backend.models.sensor_model import Sensor
from backend.engines.sensor_trigger_engine import simulate_intrusion, SimulationResult
from backend.config import Config


class SimulationController:
    def __init__(
        self,
        sensors: List[Sensor],
        frequency: float = Config.simulation.FREQUENCY,
        seed: Optional[int] = None,
        jitter: float = Config.simulation.JITTER,
        max_history: int = Config.buffer.MAX_HISTORY,
        border_buffer: float = Config.simulation.BORDER_BUFFER,
        on_result: Optional[Callable[[SimulationResult], None]] = None
    ):
        if not sensors:
            raise ValueError("SimulationController requires at least one sensor")

        if frequency <= 0:
            raise ValueError("frequency must be > 0")

        # Defensive copy
        self.sensors = list(sensors)

        self.frequency = frequency
        self.jitter = jitter
        self.max_history = max_history
        self.border_buffer = border_buffer
        self.on_result = on_result

        # RNG isolation
        self._rng = random.Random(seed)

        # Bounding box
        coords = [(s.latitude, s.longitude) for s in self.sensors]
        lats, lons = zip(*coords)

        self._min_lat, self._max_lat = min(lats), max(lats)
        self._min_lon, self._max_lon = min(lons), max(lons)

        # Threading primitives
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()  # True = paused

        # Thread-safe history
        self.history: List[SimulationResult] = []
        self._lock = threading.Lock()

    # =====================================================
    # CONTROL METHODS
    # =====================================================

    def start(self):
        if self._thread and self._thread.is_alive():
            return

        self._pause_event.clear()
        self._stop_event.clear()

        self._thread = threading.Thread(target=self.run_loop, daemon=True)
        self._thread.start()

    def stop(self, block: bool = True):
        self._stop_event.set()

        if block and self._thread and self._thread.is_alive():
            self._thread.join()

        self._thread = None

    def pause(self):
        if not self.is_active:
            return
        self._pause_event.set()

    def resume(self):
        if not self.is_active:
            return
        self._pause_event.clear()

    # =====================================================
    # STATE PROPERTIES
    # =====================================================

    @property
    def is_active(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def is_paused(self) -> bool:
        return self._pause_event.is_set()

    @property
    def is_running(self) -> bool:
        return self.is_active and not self._pause_event.is_set()

    # =====================================================
    # CORE EXECUTION
    # =====================================================

    def run_loop(self):
        while not self._stop_event.is_set():
            try:
                if self._pause_event.is_set():
                    while self._pause_event.is_set() and not self._stop_event.is_set():
                        self._stop_event.wait(timeout=Config.simulation.PAUSE_SLEEP)
                    continue

                self.run_step()

            except Exception as e:
                print(f"[SIMULATION ERROR] {e}")

            sleep_time = self._compute_interval()
            self._stop_event.wait(timeout=sleep_time)

    def run_step(self) -> SimulationResult:
        lat, lon = self._generate_intrusion_point()

        result: SimulationResult = simulate_intrusion(
            sensors=self.sensors,
            intrusion_lat=lat,
            intrusion_lon=lon,
            return_full=True
        )

        self._handle_result(result)
        return result

    # =====================================================
    # INTERNAL HELPERS
    # =====================================================

    def _compute_interval(self) -> float:
        if self.jitter <= 0:
            return self.frequency

        factor = 1 + self._rng.uniform(-self.jitter, self.jitter)
        return max(Config.simulation.MIN_INTERVAL, self.frequency * factor)

    def _generate_intrusion_point(self) -> tuple:
        lat = self._rng.uniform(
            self._min_lat - self.border_buffer,
            self._max_lat + self.border_buffer
        )
        lon = self._rng.uniform(
            self._min_lon - self.border_buffer,
            self._max_lon + self.border_buffer
        )
        return lat, lon

    def _handle_result(self, result: SimulationResult):
        with self._lock:
            self.history.append(result)
            if len(self.history) > self.max_history:
                self.history.pop(0)

        if self.on_result:
            try:
                self.on_result(result)
            except Exception as e:
                print(f"[HOOK ERROR] {e}")
            return

        if result.event:
            print(
                f"[CONFIRMED] {result.event.event_id} @ "
                f"({result.event.latitude:.5f}, {result.event.longitude:.5f}) "
                f"| sensors={len(result.event.sensors_involved)}"
            )
        else:
            print("[NO EVENT] Noise / insufficient confirmation")

    # =====================================================
    # UTILITIES
    # =====================================================

    def get_history(self) -> List[SimulationResult]:
        with self._lock:
            return list(self.history)

    def clear_history(self):
        with self._lock:
            self.history.clear()