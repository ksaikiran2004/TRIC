"""
TRIC - Global Settings

Responsibilities:
    - Centralize all configurable parameters
    - Provide clean access across modules
    - Ensure consistency and scalability
"""

from pathlib import Path


# ------------------------------------------------------------------
# System Paths
# ------------------------------------------------------------------

class SystemPaths:
    BASE_DIR = Path("data")
    INCIDENTS_DIR = BASE_DIR / "incidents"


# ------------------------------------------------------------------
# Simulation Settings
# ------------------------------------------------------------------

class SimulationConfig:
    FREQUENCY_HZ = 2.0          # updates per second
    JITTER = 0.2                # randomness in movement
    LATENCY_SEC = 0.0           # simulated delay
    MAX_ENTITIES = 10           # number of simulated intrusions


# ------------------------------------------------------------------
# Tracking Settings
# ------------------------------------------------------------------

class TrackingConfig:
    MAX_TRACK_AGE_SEC = 10.0        # remove inactive tracks
    MIN_POINTS_FOR_PATH = 2         # minimum events to form path
    MAX_HISTORY_POINTS = 50         # memory control


# ------------------------------------------------------------------
# Direction Settings
# ------------------------------------------------------------------

class DirectionConfig:
    MIN_MOVEMENT_DISTANCE = 0.5     # meters threshold
    STATIONARY_THRESHOLD = 0.2      # below → stationary
    SMOOTHING_WINDOW = 3            # points used for smoothing


# ------------------------------------------------------------------
# Event Settings
# ------------------------------------------------------------------

class EventConfig:
    CONFIDENCE_THRESHOLD = 0.5      # minimum valid event
    INACTIVE_TIMEOUT_SEC = 5.0      # mark event inactive
    MAX_EVENT_AGE_SEC = 30.0        # cleanup threshold


# ------------------------------------------------------------------
# Logging Settings
# ------------------------------------------------------------------

class LoggingConfig:
    ENABLE_FILE_LOGGING = True
    METADATA_VERSION = 1
    WRITE_INDENT = 4                # JSON formatting


# ------------------------------------------------------------------
# Performance / Buffer Settings
# ------------------------------------------------------------------

class BufferConfig:
    EVENT_BUFFER_SIZE = 100
    TRACK_BUFFER_SIZE = 100