"""
TRIC - Secret Demo API Routes
Hidden endpoints to trigger the simulation from a mobile device.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Literal

# Importing the simulation engine we built in Phase 2
from backend.simulation.sensor_trigger_engine import run_simulation_step_full

# Create the router
demo_router = APIRouter(prefix="/demo", tags=["Secret Demo"])

# --- Pydantic Models for Input Validation ---
class TriggerRequest(BaseModel):
    latitude: float
    longitude: float
    simulation_type: Literal["footsteps", "animal", "vehicle"]
    simulate_latency: bool = True

# --- Endpoints ---
@demo_router.post("/trigger")
async def manual_trigger(request: Request, payload: TriggerRequest):
    """
    Secret endpoint: Your phone sends coordinates here to fake an intrusion.
    """
    
    # We retrieve the live, active AlertEngine from the FastAPI app state
    # (We will set this up in run_tric.py later)
    alert_engine = getattr(request.app.state, "alert_engine", None)

    if not alert_engine:
        raise HTTPException(status_code=500, detail="AlertEngine not initialized in app state")

    try:
        # Run the simulation using the engine we built in Phase 2
        result = run_simulation_step_full(
            alert_engine=alert_engine,
            intrusion_lat=payload.latitude,
            intrusion_lon=payload.longitude,
            simulation_type=payload.simulation_type,
            simulate_latency=payload.simulate_latency,
            debug=True
        )

        # Return the clean result back to the phone to confirm it worked
        return {
            "status": "success",
            "simulation_id": result.simulation_id,
            "event_status": result.status,
            "confidence": result.confidence,
            "latency_applied": result.latency
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))