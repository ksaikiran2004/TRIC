"""
TRIC - Main Orchestration Entrypoint

FILE: backend/main.py

Responsibility:
Wire together all core components of the TRIC pipeline and host the Tactical Web Server.
"""

import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from backend.config import Config
from backend.simulation.sensor_generator import generate_sensor_network
from backend.confirmation.multi_sensor_confirmation import MultiSensorConfirmation
from backend.confirmation.alert_engine import AlertEngine
from backend.simulation.simulation_controller import SimulationController
from backend.tracking.intrusion_tracker import IntrusionTracker
from backend.tracking.path_builder import PathBuilder
from backend.tracking.direction_classifier import DirectionClassifier
from backend.orchestrator.event_manager import EventManager
from backend.logging_system.incident_logger import IncidentLogger

# Initialize Web Server
app = FastAPI(title="TRIC Command Center")

# Global State for WebSockets
active_connections = []
event_manager = None
controller = None

@app.on_event("startup")
async def startup_event():
    global event_manager, controller
    
    # --- Initialize Core Components ---
    sensors = generate_sensor_network()
    confirmation = MultiSensorConfirmation()
    alert_engine = AlertEngine(sensors)
    tracker = IntrusionTracker()
    path_builder = PathBuilder()
    direction_classifier = DirectionClassifier()
    event_manager = EventManager()
    incident_logger = IncidentLogger()

    # --- Callback Definition ---
    def on_simulation_result(result):
        if result.event is None:
            return

        track = tracker.process_result(result)
        if track is None:
            return

        path = path_builder.build_path(track)
        if path is None:
            return

        direction = direction_classifier.classify(path)
        
        event_manager.process(
            tracks=[track],
            paths=[path],
            directions=[direction]
        )

        # Logging
        events = event_manager.get_active_events()
        for event in events:
            incident_logger.log_event(event)

    # --- Initialize Controller ---
    controller = SimulationController(
        sensors=sensors,
        on_result=on_simulation_result
    )
    
    # Start Simulation Engine
    controller.start()
    
    # Start the background broadcast loop to push data to the map
    asyncio.create_task(broadcast_tactical_data())

@app.on_event("shutdown")
def shutdown_event():
    if controller:
        controller.stop()

# --- WebSocket Broadcast Logic ---
async def broadcast_tactical_data():
    while True:
        if event_manager and active_connections:
            events = event_manager.get_active_events()
            for event in events:
                # Safely extract data based on your event object structure
                payload = {
                    "event_id": getattr(event, "event_id", "EVT_01"),
                    "track_id": getattr(event, "track_id", "TRK_01"),
                    "location": getattr(event, "location", [34.0, 74.0]),
                    "direction": getattr(event, "direction", "UNKNOWN"),
                    "speed": getattr(event, "speed", 0.0),
                    "status": getattr(event, "status", "ACTIVE")
                }
                # Broadcast to all connected UI dashboards
                for connection in active_connections:
                    try:
                        await connection.send_text(json.dumps(payload))
                    except:
                        pass
        await asyncio.sleep(0.5)  # Push map updates twice a second

@app.websocket("/ws/tactical")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text() # Keep connection open
    except WebSocketDisconnect:
        active_connections.remove(websocket)