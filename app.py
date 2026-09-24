# TRIC C4ISR - TACTICAL ORCHESTRATOR (CORE SERVER)
import os
import cv2
import sqlite3
import time
from flask import Flask, jsonify, render_template, send_from_directory, Response, request

from backend.cameras.camera_manager import CameraManager
from backend.correlation.cross_camera_linking import CrossCameraLinker
from backend.evidence.blockchain_audit import BlockchainAuditLogger
from backend.intelligence.risk_scoring import ThreatRiskScorer
from backend.intelligence.threat_validation import ThreatValidator

# Import the new YOLO Vision Engine
from backend.simulation.sensor_generator import ensure_sensor_database
from backend.vision_processor import TacticalVisionProcessor

DEFAULT_VIDEO_SOURCE = os.getenv('TRIC_VIDEO_SOURCE', 'rtsp://192.168.1.19:8554/')
VIDEO_SOURCE = DEFAULT_VIDEO_SOURCE


def normalize_rtsp_url(source):
    """Fix common malformed RTSP URLs like rtsp://host.ip.port/ -> rtsp://host:port/."""
    if not isinstance(source, str):
        return source

    text = source.strip()
    if '://' not in text:
        return text

    scheme, rest = text.split('://', 1)
    if scheme.lower() not in {'rtsp', 'http', 'https'}:
        return text

    # Fix common malformed addresses such as rtsp://172.16.28.67.8554/
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
    """Set the live RTSP/HTTP source used by the drone feed and AI pipeline."""
    if raw_source is None:
        raise ValueError('RTSP source cannot be empty.')

    value = str(raw_source).strip()
    if not value:
        raise ValueError('RTSP source cannot be empty.')

    normalized_source = normalize_rtsp_url(value)
    if not normalized_source or normalized_source.lower() in {'demo', 'demo-video', 'default'}:
        normalized_source = 'demo'

    global VIDEO_SOURCE
    VIDEO_SOURCE = normalized_source
    os.environ['TRIC_VIDEO_SOURCE'] = normalized_source
    return normalized_source


def resolve_video_source():
    """
    Resolve the active camera feed source.

    Supported values:
      - unset / demo / default -> local demo video
      - 0 / webcam -> local webcam
      - URL like rtsp://... or http://... -> IP camera / drone stream
      - local file path -> any mp4 or image/video file
    """
    demo_path = os.path.join(os.path.dirname(__file__), 'demo_video.mp4')
    raw_source = os.getenv('TRIC_VIDEO_SOURCE', VIDEO_SOURCE).strip()
    raw_source = normalize_rtsp_url(raw_source)

    if not raw_source or raw_source.lower() in {'demo', 'demo-video', 'default'}:
        return demo_path if os.path.exists(demo_path) else DEFAULT_VIDEO_SOURCE

    source = raw_source.lower()
    if source in {'0', 'webcam', 'camera', 'local-webcam'}:
        return 0

    if os.path.exists(raw_source):
        return raw_source

    return raw_source

# Explicitly wire Flask to the strict MVC folder structure
app = Flask(__name__, 
            template_folder='frontend/templates',
            static_folder='frontend/static')

# Initialize the AI Engine globally so it doesn't reload on every frame
print(">>> [TRIC-CORE] BOOTING AI VISION SUBSYSTEM...")
vision_engine = TacticalVisionProcessor()
camera_manager = CameraManager()
cross_camera_linker = CrossCameraLinker()
blockchain_logger = BlockchainAuditLogger()
threat_risk_scorer = ThreatRiskScorer()
threat_validator = ThreatValidator()

def get_db_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'tric.db'))


ensure_sensor_database(db_path=get_db_path())

# ==========================================
# ROUTE 1: PRIMARY DASHBOARD UI
# ==========================================
@app.route('/')
def index():
    return render_template('dashboard.html')

# ==========================================
# ROUTE 2: SENSOR GRID API
# ==========================================
@app.route('/api/sensors')
def api_get_sensors():
    try:
        ensure_sensor_database(db_path=get_db_path())
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT id, type, lat, lon FROM sensors")
        rows = cursor.fetchall()
        conn.close()

        sensors = [{"id": r[0], "type": r[1], "lat": r[2], "lon": r[3], "status": "ONLINE"} for r in rows]
        return jsonify(sensors)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# ROUTE 3: AI-PROCESSED UAV VIDEO STREAM
# ==========================================
@app.route('/api/video_feed')
def video_feed():
    def generate_stream():
        source = resolve_video_source()
        cap = cv2.VideoCapture(source)

        if not cap.isOpened():
            print(f">>> [TRIC-ERROR] FATAL: Cannot open video source: {source}")
            return

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                if isinstance(source, str) and source.lower().endswith('.mp4'):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                break

            # 1. Optimize frame resolution for the Flask bridge (Prevents bandwidth choke)
            frame = cv2.resize(frame, (640, 360))

            # 2. Execute YOLO AI Inference
            processed_frame, telemetry = vision_engine.process_frame(frame)

            # 3. Bake in System Timestamps
            sys_time = time.strftime("%H:%M:%S")
            source_label = 'PHONE-STREAM' if isinstance(source, str) and ('http://' in source.lower() or 'rtsp://' in source.lower()) else 'UAV-07'
            cv2.putText(processed_frame, f"{source_label} // UPLINK SECURE // T-{sys_time}",
                        (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 234, 79), 1)

            # 4. Encode to JPEG for HTTP Multipart Streaming
            ret, buffer = cv2.imencode('.jpg', processed_frame)
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

            # Throttle to ~30 FPS to prevent CPU burnout
            time.sleep(0.033)

    return Response(generate_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/video_source', methods=['GET'])
def api_get_video_source():
    return jsonify({"source": resolve_video_source(), "status": "ok"})


@app.route('/api/video_source', methods=['POST'])
def api_set_video_source():
    payload = request.get_json(silent=True) or {}
    source = payload.get('source', '').strip()
    if not source:
        return jsonify({"error": "RTSP source URL is required."}), 400

    try:
        updated_source = set_video_source(source)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify({"source": updated_source, "status": "updated"})

# ==========================================
# ROUTE 4: AIR-GAPPED MAP TILE SERVER
# ==========================================
@app.route('/offline_map/<z>/<x>/<y>.png')
def offline_map(z, x, y):
    """Intercepts map requests and serves them securely from the local hard drive."""
    tile_dir = os.path.join(os.path.dirname(__file__), 'data', 'offline_tiles', str(z), str(x))
    filename = f"{y}.png"
    
    if not os.path.exists(os.path.join(tile_dir, filename)):
        return send_from_directory(os.path.join(os.path.dirname(__file__), 'frontend', 'static', 'assets'), 'black_tile.png')
        
    return send_from_directory(tile_dir, filename)


if __name__ == '__main__':
    print("===================================================")
    print(">>> TRIC COMMAND ORCHESTRATOR ONLINE")
    print(">>> LOCAL HOST: http://127.0.0.1:5000")
    print("===================================================")
    app.run(host='0.0.0.0', port=5000, debug=False) # debug=False prevents YOLO from loading twice