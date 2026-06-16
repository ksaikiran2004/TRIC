"""
TRIC - Main Entry Point
Initializes the FastAPI application, connects the AlertEngine, 
and hosts the API/WebSocket routes.
"""

import uvicorn
from fastapi import FastAPI
from backend.confirmation.alert_engine import AlertEngine
from backend.api.demo_routes import demo_router
from backend.api.websocket_manager import manager
from backend.simulation.sensor_generator import generate_sensor_network

# Initialize the App
app = FastAPI(title="TRIC Tactical Command")

# Initialize the core systems
# Note: In a production environment, you'd load sensors from a database
sensors = generate_sensor_network()
app.state.alert_engine = AlertEngine(sensors=sensors)

# Include our routes
app.include_router(demo_router)

# WebSocket Endpoint
@app.websocket("/ws/tactical")
async def tactical_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except:
        manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run("run_tric:app", host="0.0.0.0", port=8000, reload=True)