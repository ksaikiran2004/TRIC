"""
TRIC - Trinetra Rapid Interception Command
Path Tracking & Direction Models
"""

import math
from typing import List, Optional
from dataclasses import dataclass, field

@dataclass
class PathPoint:
    latitude: float
    longitude: float
    timestamp: float
    sensor_id: str

@dataclass
class IntrusionPath:
    target_id: str  # Links to the TacticalAlert ID
    points: List[PathPoint] = field(default_factory=list)
    is_active: bool = True
    
    def add_point(self, lat: float, lon: float, timestamp: float, sensor_id: str):
        """Appends a new verified sensor hit to the target's path"""
        self.points.append(PathPoint(lat, lon, timestamp, sensor_id))
        
    def get_current_heading(self) -> str:
        """Calculates the cardinal direction of movement based on the last two points"""
        if len(self.points) < 2:
            return "CALCULATING..."
            
        p1 = self.points[-2]
        p2 = self.points[-1]
        
        d_lon = p2.longitude - p1.longitude
        d_lat = p2.latitude - p1.latitude
        
        angle = math.atan2(d_lon, d_lat)
        degrees = math.degrees(angle)
        if degrees < 0:
            degrees += 360
            
        # Map degrees to 8-point compass directions for the tactical UI
        compass_brackets = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        index = int((degrees + 22.5) // 45) % 8
        return compass_brackets[index]

    def to_dict(self):
        """Prepares the live path data for WebSocket transmission to the frontend map"""
        return {
            "target_id": self.target_id,
            "is_active": self.is_active,
            "current_heading": self.get_current_heading(),
            "path_coordinates": [{"lat": p.latitude, "lng": p.longitude} for p in self.points]
        }