import sqlite3
import os

def init_db():
    # 1. Calculate the absolute path to the 'data' folder based on this file's location
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '../')) # Go up one level from 'backend' to root
    db_path = os.path.join(project_root, 'data', 'tric.db')
    
    # 2. Ensure the 'data' directory actually exists before trying to create the DB
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    print(f"Initializing database at: {db_path}")
    
    # 3. Connect to the correct absolute path
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # User Table (Role-based: technician vs authority)
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (id INTEGER PRIMARY KEY, username TEXT, role TEXT, password_hash TEXT)''')
    
    # Sensor Table (Status, coordinates, etc.)
    cursor.execute('''CREATE TABLE IF NOT EXISTS sensors 
                      (id INTEGER PRIMARY KEY, type TEXT, status TEXT, lat REAL, lon REAL)''')
    
    # Logs Table (Intrusion history)
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs 
                      (id INTEGER PRIMARY KEY, timestamp DATETIME, sensor_id INTEGER, event_type TEXT)''')
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("TRIC Foundation Established: Database initialized correctly in the data/ folder.")