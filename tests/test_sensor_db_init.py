import sqlite3

from backend.simulation.sensor_generator import ensure_sensor_database


def test_ensure_sensor_database_populates_empty_db(tmp_path):
    db_path = tmp_path / "tric.db"

    ensure_sensor_database(db_path=str(db_path))

    conn = sqlite3.connect(db_path)
    try:
        count = conn.execute("SELECT COUNT(*) FROM sensors").fetchone()[0]
        sample = conn.execute("SELECT id, type, status, lat, lon FROM sensors LIMIT 1").fetchone()
    finally:
        conn.close()

    assert count > 0, "sensor table should be populated with generated sensors"
    assert sample is not None
    assert sample[1] in {"seismic", "acoustic", "radar", "infrared"}
    assert sample[3] is not None and sample[4] is not None
