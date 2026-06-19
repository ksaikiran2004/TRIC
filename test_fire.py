import os
import sys
import sqlite3

# Ensure Python can see your backend modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.confirmation.alert_engine import AlertEngine
from backend.simulation.sensor_trigger_engine import run_simulation_step_full
from backend.models.sensor_model import Sensor, SensorType

print("\n=== TRIC SYSTEM: TACTICAL TEST FIRE ===")

def load_sensors_from_db():
    """Pulls the 277 deployed sensors from the Black Box so the AlertEngine can see them."""
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'tric.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, type, lat, lon FROM sensors")
    rows = cursor.fetchall()
    conn.close()

    sensors = []
    for row in rows:
        s_id, s_type_str, lat, lon = row
        try:
            s_type = SensorType[s_type_str]
        except KeyError:
            continue
            
        s = Sensor(sensor_type=s_type, latitude=lat, longitude=lon, detection_radius_m=300)
        s.id = s_id 
        sensors.append(s)
    return sensors

try:
    # 1. Load the tactical network
    print("Loading deployed sensors from Black Box...")
    deployed_sensors = load_sensors_from_db()
    
    if not deployed_sensors:
        print("[ERROR] No sensors found! Did you run sensor_generator.py?")
        sys.exit(1)
        
    print(f"Loaded {len(deployed_sensors)} sensors into memory.")

    # 2. Boot up your core Alert Engine
    print("Booting AlertEngine...")
    alert_engine = AlertEngine(sensors=deployed_sensors)
    
    # 3. Pick a test coordinate EXACTLY where your first sensor is
    test_lat = deployed_sensors[0].latitude
    test_lon = deployed_sensors[0].longitude
    
    print(f"Spawning 'HUMAN' target directly on Node #1 at ({test_lat}, {test_lon})...")
    print("Firing sensor trigger engine...\n")
    
    # 4. Run the full simulation step (CHANGED "footsteps" to "human")
    result = run_simulation_step_full(
        alert_engine=alert_engine,
        intrusion_lat=test_lat,
        intrusion_lon=test_lon,
        simulation_type="human",  # <--- THIS WAS THE FIX
        debug=True 
    )
    
    print("\n=== TEST COMPLETE ===")
    if result.status == "CONFIRMED":
        print(">>> SUCCESS: Intrusion Confirmed! Check 'tric.db' logs table.")
    else:
        print(f">>> SYSTEM REJECTED THE EVENT. Error/Status: {result.error}")
        
except Exception as e:
    print(f"\n[CRITICAL ERROR] Test fire failed: {e}")