"""
TRIC - Main Entry Point
Initializes the FastAPI application, connects the AlertEngine, 
and hosts the API/WebSocket routes.
"""

import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.confirmation.alert_engine import AlertEngine
from backend.api.demo_routes import demo_router
from backend.api.websocket_manager import manager
from backend.simulation.sensor_generator import generate_sensor_network

# Initialize the App
app = FastAPI(title="TRIC Tactical Command")

# 1. Mount Static Files (Critical for CSS and JS to load)
# Points to your 'frontend' folder at the root of the project
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# 2. Initialize the core systems
sensors = generate_sensor_network()
app.state.alert_engine = AlertEngine(sensors=sensors)

# 3. Include our routes
app.include_router(demo_router)

# 4. WebSocket Endpoint
@app.websocket("/ws/tactical")
async def tactical_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except Exception:
        manager.disconnect(websocket)

if __name__ == "__main__":
    # Ensure this points to the correct file name (e.g., 'backend.main:app')
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)