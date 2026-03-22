"""
TRIC - Geographic Utilities

FILE: backend/utils/geo_utils.py

Responsibility:
Provide reusable geographic calculations such as distance and radius checks.
"""

import math

from backend.config import Config


def haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:
    """
    Calculate the great-circle distance between two points on Earth
    using the Haversine formula.

    Args:
        lat1, lon1: Latitude and longitude of point 1 (in degrees)
        lat2, lon2: Latitude and longitude of point 2 (in degrees)

    Returns:
        Distance in meters
    """

    # Convert degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Haversine formula
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Earth radius from config
    radius = Config.paths.EARTH_RADIUS_M

    distance = radius * c
    return distance


def is_within_radius(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    radius_m: float
) -> bool:
    """
    Check if two geographic points are within a given radius.

    Args:
        lat1, lon1: First point (degrees)
        lat2, lon2: Second point (degrees)
        radius_m: Radius in meters

    Returns:
        True if within radius, else False
    """

    distance = haversine_distance(lat1, lon1, lat2, lon2)
    return distance <= radius_m