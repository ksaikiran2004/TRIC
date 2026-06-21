# TRIC C4ISR - TACTICAL ORCHESTRATOR (CORE SERVER)
import os
import cv2
import sqlite3
import time
from flask import Flask, jsonify, render_template, send_from_directory, Response

# Import the new YOLO Vision Engine
from backend.vision_processor import TacticalVisionProcessor

# Explicitly wire Flask to the strict MVC folder structure
app = Flask(__name__, 
            template_folder='frontend/templates',
            static_folder='frontend/static')

# Initialize the AI Engine globally so it doesn't reload on every frame
print(">>> [TRIC-CORE] BOOTING AI VISION SUBSYSTEM...")
vision_engine = TacticalVisionProcessor()

def get_db_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'tric.db'))

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
        # Load the local MP4 drone footage
        video_path = os.path.join(os.path.dirname(__file__), 'demo_video.mp4')
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f">>> [TRIC-ERROR] FATAL: Cannot find {video_path}")
            return
            
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                # Loop the video continuously for demonstration purposes
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            
            # 1. Optimize frame resolution for the Flask bridge (Prevents bandwidth choke)
            frame = cv2.resize(frame, (640, 360))
            
            # 2. Execute YOLO AI Inference
            processed_frame, telemetry = vision_engine.process_frame(frame)
            
            # 3. Bake in System Timestamps
            sys_time = time.strftime("%H:%M:%S")
            cv2.putText(processed_frame, f"UAV-07 // UPLINK SECURE // T-{sys_time}", 
                        (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 234, 79), 1)
            
            # 4. Encode to JPEG for HTTP Multipart Streaming
            ret, buffer = cv2.imencode('.jpg', processed_frame)
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            
            # Throttle to ~30 FPS to prevent CPU burnout
            time.sleep(0.033)
            
    return Response(generate_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

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