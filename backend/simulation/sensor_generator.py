"""
TRIC - Sensor Network Generator

Generates a hybrid sensor network along the border defined in:
    frontend/geo/border_line.geojson

Architecture:
Each border node contains:
    SEISMIC
    ACOUSTIC
    RADAR

Infrared sensors are deployed every N nodes.

Output:
    List[Sensor] compatible with AlertEngine
"""
import sys
import sqlite3
import os
import json
from pathlib import Path
from typing import List, Tuple
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from backend.models.sensor_model import Sensor, SensorType


# =========================================================
# CONFIGURATION
# =========================================================

DEFAULT_SENSOR_SPACING_METERS = 250

INFRARED_INTERVAL = 3

SENSOR_RADIUS = {
    SensorType.SEISMIC: 200,
    SensorType.ACOUSTIC: 300,
    SensorType.RADAR: 500,
    SensorType.INFRARED: 250,
}


# =========================================================
# GEOJSON READER
# =========================================================

def read_border_coordinates(geojson_path: Path) -> List[Tuple[float, float]]:
    """
    Extract (lat, lon) coordinates from GeoJSON border file.
    Supports LineString and MultiLineString.
    """

    with open(geojson_path, "r") as f:
        data = json.load(f)

    coords: List[Tuple[float, float]] = []

    for feature in data["features"]:
        geometry = feature["geometry"]

        if geometry["type"] == "LineString":

            for lon, lat in geometry["coordinates"]:
                coords.append((lat, lon))

        elif geometry["type"] == "MultiLineString":

            for line in geometry["coordinates"]:
                for lon, lat in line:
                    coords.append((lat, lon))

    return coords


# =========================================================
# INTERPOLATION
# =========================================================

def interpolate_point(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    fraction: float
) -> Tuple[float, float]:
    """
    Linear interpolation between two coordinates.
    """

    lat = lat1 + (lat2 - lat1) * fraction
    lon = lon1 + (lon2 - lon1) * fraction

    return lat, lon


# =========================================================
# SENSOR NODE CREATION
# =========================================================

def create_node_sensors(
    lat: float,
    lon: float,
    node_index: int
) -> List[Sensor]:
    """
    Create a cluster of sensors at a node location.
    """

    sensors: List[Sensor] = []

    base_types = [
        SensorType.SEISMIC,
        SensorType.ACOUSTIC,
        SensorType.RADAR
    ]

    for stype in base_types:

        sensors.append(
            Sensor(
                sensor_type=stype,
                latitude=lat,
                longitude=lon,
                detection_radius_m=SENSOR_RADIUS[stype]
            )
        )

    # infrared sensor deployed periodically
    if node_index % INFRARED_INTERVAL == 0:

        sensors.append(
            Sensor(
                sensor_type=SensorType.INFRARED,
                latitude=lat,
                longitude=lon,
                detection_radius_m=SENSOR_RADIUS[SensorType.INFRARED]
            )
        )

    return sensors


# =========================================================
# SENSOR GENERATION ALONG BORDER
# =========================================================

def generate_sensors_along_border(
    border_coords: List[Tuple[float, float]],
    spacing_m: float = DEFAULT_SENSOR_SPACING_METERS
) -> List[Sensor]:

    sensors: List[Sensor] = []
    node_index = 0

    last_node_lat = None
    last_node_lon = None

    for i in range(len(border_coords) - 1):

        lat1, lon1 = border_coords[i]
        lat2, lon2 = border_coords[i + 1]

        segment_length = Sensor.distance_meters(
            lat1,
            lon1,
            lat2,
            lon2
        )

        if segment_length == 0:
            continue

        # ensure endpoints included
        num_points = max(1, int(segment_length // spacing_m) + 1)

        for j in range(num_points):

            if num_points == 1:
                fraction = 0
            else:
                fraction = j / (num_points - 1)

            lat, lon = interpolate_point(
                lat1,
                lon1,
                lat2,
                lon2,
                fraction
            )

            # prevent duplicate nodes between segments
            if last_node_lat is not None:

                if Sensor.distance_meters(
                    last_node_lat,
                    last_node_lon,
                    lat,
                    lon
                ) < 1:
                    continue

            node_sensors = create_node_sensors(
                lat,
                lon,
                node_index
            )

            sensors.extend(node_sensors)

            last_node_lat = lat
            last_node_lon = lon

            node_index += 1

    return sensors


# =========================================================
# MAIN ENTRY
# =========================================================

def generate_sensor_network(
    geojson_file: str = "frontend/geo/border_line.geojson",
    spacing_m: float = DEFAULT_SENSOR_SPACING_METERS
) -> List[Sensor]:

    geojson_path = Path(geojson_file)

    if not geojson_path.exists():
        raise FileNotFoundError(
            f"Border file not found: {geojson_file}"
        )

    border_coords = read_border_coordinates(geojson_path)

    sensors = generate_sensors_along_border(
        border_coords,
        spacing_m
    )

    return sensors


# =========================================================
# DATABASE PERSISTENCE INTEGRATION
# =========================================================

def save_sensors_to_db(sensors: List[Sensor]):
    """Locks the generated tactical sensor network into persistent SQLite storage."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '../../'))
    db_path = os.path.join(project_root, 'data', 'tric.db')

    # Ensure the data directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Clear old deployment to prevent stacking ghosts on rerun
    cursor.execute("DELETE FROM sensors")

    # Extract data from Sensor objects
    sensor_data = []
    for s in sensors:
        stype_name = s.sensor_type.name if hasattr(s.sensor_type, 'name') else str(s.sensor_type)
        sensor_data.append((stype_name, 'ACTIVE', s.latitude, s.longitude))

    # Bulk insert for maximum performance
    cursor.executemany("INSERT INTO sensors (type, status, lat, lon) VALUES (?, ?, ?, ?)", sensor_data)
    
    conn.commit()
    print(f"[SUCCESS] {len(sensors)} sensors locked into the command database.")
    conn.close()


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '../../'))
    geo_path = os.path.join(project_root, 'frontend', 'geo', 'border_line.geojson')

    try:
        print(f"Reading deployment line from {geo_path}...")
        network = generate_sensor_network(geo_path)
        save_sensors_to_db(network)
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")