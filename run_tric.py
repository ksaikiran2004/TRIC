"""
TRIC - Main Entry Point
Initializes the FastAPI application, connects the AlertEngine, 
and hosts the API/WebSocket routes.
"""

import os
import time
import cv2
import uvicorn
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.cameras.camera_manager import CameraManager
from backend.correlation.cross_camera_linking import CrossCameraLinker
from backend.intelligence.risk_scoring import ThreatRiskScorer
from backend.intelligence.threat_validation import ThreatValidator
from backend.confirmation.alert_engine import AlertEngine
from backend.api.demo_routes import demo_router
from backend.api.websocket_manager import manager
from backend.simulation.sensor_generator import ensure_sensor_database, generate_sensor_network
from backend.vision_processor import TacticalVisionProcessor

# Initialize the App
app = FastAPI(title="TRIC Tactical Command")

TEMPLATE_DIR = Path(__file__).parent / "frontend" / "templates"

@app.get("/")
async def dashboard():
    return FileResponse(TEMPLATE_DIR / "dashboard.html")

@app.get("/api/sensors")
async def get_sensors():
    ensure_sensor_database()
    return [
        {
            "id": sensor.id,
            "type": sensor.sensor_type.value,
            "lat": sensor.latitude,
            "lon": sensor.longitude,
            "status": sensor.status.value,
        }
        for sensor in sensors
    ]


DEFAULT_VIDEO_SOURCE = os.getenv("TRIC_VIDEO_SOURCE", "rtsp://192.168.1.19:8554/")
VIDEO_SOURCE = DEFAULT_VIDEO_SOURCE
vision_engine = TacticalVisionProcessor()


def normalize_rtsp_url(source):
    """Fix malformed RTSP URLs such as host.ip.port without a port separator."""
    if not isinstance(source, str):
        return source
    text = source.strip()
    if '://' not in text:
        return text
    scheme, rest = text.split('://', 1)
    if scheme.lower() not in {'rtsp', 'http', 'https'}:
        return text
    if rest.count(':') == 0 and '.' in rest and rest.rsplit('/', 1)[0].count('.') >= 3:
        host_and_path = rest.split('/', 1)
        host = host_and_path[0]
        trailing = '/' + host_and_path[1] if len(host_and_path) > 1 else ''
        ip_part = host.rsplit('.', 1)[0]
        port_part = host.rsplit('.', 1)[1]
        if port_part.isdigit():
            return f"{scheme}://{ip_part}:{port_part}{trailing}"
    return text


def set_video_source(raw_source):
    if raw_source is None:
        raise ValueError("RTSP source cannot be empty.")

    value = str(raw_source).strip()
    if not value:
        raise ValueError("RTSP source cannot be empty.")

    normalized_source = normalize_rtsp_url(value)
    if not normalized_source or normalized_source.lower() in {"demo", "demo-video", "default"}:
        normalized_source = "demo"

    global VIDEO_SOURCE
    VIDEO_SOURCE = normalized_source
    os.environ["TRIC_VIDEO_SOURCE"] = normalized_source
    return normalized_source


def resolve_video_source():
    raw_source = os.getenv("TRIC_VIDEO_SOURCE", VIDEO_SOURCE).strip()
    raw_source = normalize_rtsp_url(raw_source)
    if not raw_source or raw_source.lower() in {"demo", "demo-video", "default"}:
        demo_path = Path(__file__).resolve().parent / "demo_video.mp4"
        if demo_path.exists():
            return str(demo_path)
        return raw_source or VIDEO_SOURCE
    return raw_source


def generate_video_frames():
    source = resolve_video_source()
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f">>> [TRIC-ERROR] Cannot open video source: {source}")
        return

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                if isinstance(source, str) and source.lower().endswith('.mp4'):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                break

            frame = cv2.resize(frame, (640, 360))
            processed_frame, _ = vision_engine.process_frame(frame)
            if processed_frame is None:
                continue

            sys_time = time.strftime("%H:%M:%S")
            source_label = 'RTSP-LINK' if isinstance(source, str) and ('http://' in source.lower() or 'rtsp://' in source.lower()) else 'UAV-07'
            cv2.putText(processed_frame, f"{source_label} // AI LIVE // T-{sys_time}",
                        (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 234, 79), 1)

            ret, jpeg = cv2.imencode(".jpg", processed_frame)
            if ret:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + jpeg.tobytes()
                    + b"\r\n"
                )
            time.sleep(0.033)
    finally:
        cap.release()


@app.get("/api/video_feed")
async def video_feed():
    return StreamingResponse(generate_video_frames(), media_type="multipart/x-mixed-replace; boundary=frame")


@app.get("/api/video_source")
async def get_video_source():
    return {"source": resolve_video_source(), "status": "ok"}


@app.post("/api/video_source")
async def update_video_source(payload: dict):
    source = (payload or {}).get("source", "").strip()
    if not source:
        raise HTTPException(status_code=400, detail="RTSP source URL is required.")
    try:
        updated_source = set_video_source(source)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"source": updated_source, "status": "updated"}

# 1. Mount Static Files (Critical for CSS and JS to load)
# Points to your 'frontend' folder at the root of the project
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# 2. Initialize the core systems
ensure_sensor_database()
sensors = generate_sensor_network()
app.state.alert_engine = AlertEngine(sensors=sensors)
app.state.camera_manager = CameraManager()
app.state.cross_camera_linker = CrossCameraLinker()
app.state.threat_risk_scorer = ThreatRiskScorer()
app.state.threat_validator = ThreatValidator()
for sensor in sensors:
    app.state.camera_manager.register_camera(
        camera_id=f"legacy-sensor-{sensor.id}",
        source=f"sensor:{sensor.sensor_type.value}",
        metadata={
            "sensor_type": sensor.sensor_type.value,
            "lat": sensor.latitude,
            "lon": sensor.longitude,
            "status": sensor.status.value,
        },
    )

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
    uvicorn.run("run_tric:app", host="0.0.0.0", port=8000, reload=True)