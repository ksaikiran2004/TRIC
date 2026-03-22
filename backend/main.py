"""
TRIC - Main Orchestration Entrypoint

FILE: backend/main.py

Responsibility:
Wire together all core components of the TRIC pipeline and start execution.

Pipeline:
Simulation → Confirmation → Tracking → Path → Direction → Event → Logging
"""

import time

from backend.config import Config

from backend.simulation.sensor_generator import SensorGenerator
from backend.confirmation.multi_sensor_confirmation import MultiSensorConfirmation
from backend.alert.alert_engine import AlertEngine
from backend.simulation.simulation_controller import SimulationController
from backend.tracking.intrusion_tracker import IntrusionTracker
from backend.tracking.path_builder import PathBuilder
from backend.tracking.direction_classifier import DirectionClassifier
from backend.orchestrator.event_manager import EventManager
from backend.logging_system.incident_logger import IncidentLogger


def main():
    # --- Initialize Sensors ---
    sensor_generator = SensorGenerator()
    sensors = sensor_generator.load_or_generate()

    # --- Initialize Core Components ---
    confirmation = MultiSensorConfirmation()
    alert_engine = AlertEngine(confirmation)

    tracker = IntrusionTracker()
    path_builder = PathBuilder()
    direction_classifier = DirectionClassifier()
    event_manager = EventManager()
    incident_logger = IncidentLogger()

    # --- Callback Definition ---
    def on_simulation_result(result):
        if result.event is None:
            return

        # Tracking
        track = tracker.process_result(result)
        if track is None:
            return

        # Path Building
        path = path_builder.build_path(track)
        if path is None:
            return

        # Direction Classification
        direction = direction_classifier.classify(path)

        # Event Processing (batch API)
        event_manager.process(
            tracks=[track],
            paths=[path],
            directions=[direction]
        )

        # Fetch active events for logging
        events = event_manager.get_active_events()
        for event in events:
            incident_logger.log_event(event)

    # --- Initialize Controller with callback ---
    controller = SimulationController(
        sensors=sensors,
        on_result=on_simulation_result
    )

    # --- Start Simulation ---
    controller.start()

    # --- Keep Process Alive ---
    try:
        while True:
            time.sleep(Config.simulation.MAIN_LOOP_SLEEP)
    except KeyboardInterrupt:
        controller.stop()


if __name__ == "__main__":
    main()