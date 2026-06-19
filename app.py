from flask import Flask, jsonify, render_template, send_from_directory
import sqlite3
import os

# Explicitly wire Flask to your new MVC folder structure
app = Flask(__name__, 
            template_folder='frontend/templates',
            static_folder='frontend/static')

def get_db_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'tric.db'))

# Route 1: Serve the Tactical Dashboard
@app.route('/')
def index():
    return render_template('dashboard.html')

# Route 2: API Bridge for the Black Box
@app.route('/api/sensors')
def api_get_sensors():
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT id, type, lat, lon FROM sensors")
        rows = cursor.fetchall()
        conn.close()

        sensors = []
        for row in rows:
            sensors.append({
                "id": row[0],
                "type": row[1],
                "lat": row[2],
                "lon": row[3],
                "status": "ONLINE"
            })
        return jsonify(sensors)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route 3: Live Video Streaming Protocol
@app.route('/api/video_feed')
def video_feed():
    from backend.surveillance.camera_stream_handler import TacticalCameraStream
    from flask import Response
    streamer = TacticalCameraStream()
    return Response(streamer.generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# ==========================================
# Route 4: OFFLINE TILE SERVER (AIR-GAPPED)
# ==========================================
@app.route('/offline_map/<z>/<x>/<y>.png')
def offline_map(z, x, y):
    """Intercepts map requests and serves them directly from your hard drive."""
    tile_dir = os.path.join(os.path.dirname(__file__), 'data', 'offline_tiles', str(z), str(x))
    filename = f"{y}.png"
    
    # If tile doesn't exist yet, return a black dummy tile so the UI doesn't crash
    if not os.path.exists(os.path.join(tile_dir, filename)):
        return send_from_directory(os.path.join(os.path.dirname(__file__), 'frontend', 'static', 'assets'), 'black_tile.png')
        
    return send_from_directory(tile_dir, filename)

if __name__ == '__main__':
    print(">>> TRIC TACTICAL SERVER ONLINE: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)