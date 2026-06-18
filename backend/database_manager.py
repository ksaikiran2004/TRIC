import sqlite3

def init_db():
    conn = sqlite3.connect('tric.db')
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
    print("TRIC Foundation Established: Database initialized.")