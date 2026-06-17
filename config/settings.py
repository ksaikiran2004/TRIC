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
    MODELS_DIR = BASE_DIR / "models"


# ------------------------------------------------------------------
# Simulation Settings
# ------------------------------------------------------------------

class SimulationConfig:
    FREQUENCY_HZ = 2.0          # updates per second
    JITTER = 0.2                # randomness in movement
    LATENCY_SEC = 0.0           # simulated delay
    MAX_ENTITIES = 10           # number of simulated intrusions
    UPDATE_INTERVAL = 1.0       # (Added for legacy sim compatibility)
    INTENSITY_PROFILE = "standard"
    BORDER_BUFFER = 50.0

# ------------------------------------------------------------------
# Tracking Settings
# ------------------------------------------------------------------

class TrackingConfig:
    MAX_TRACK_AGE_SEC = 10.0        # remove inactive tracks
    MIN_POINTS_FOR_PATH = 2         # minimum events to form path
    MAX_HISTORY_POINTS = 50         # memory control
    
    # Required by IntrusionTracker
    DISTANCE_THRESHOLD = 50.0       # Max distance in meters between consecutive events
    TIME_THRESHOLD = 15.0           # Max time in seconds before a track goes inactive


# ------------------------------------------------------------------
# Direction Settings
# ------------------------------------------------------------------

class DirectionConfig:
    MIN_MOVEMENT_DISTANCE = 0.5     # meters threshold
    STATIONARY_THRESHOLD = 0.2      # below → stationary
    SMOOTHING_WINDOW = 3            # points used for smoothing
    
    # Required by DirectionClassifier
    MIN_DISTANCE = 5.0              
    MIN_SPEED = 0.5                
    CONFIDENCE_DISTANCE = 20.0     
    USE_BEARING_STABILITY_GUARD = True
    USE_CONFIDENCE_FLOOR = True
    CONFIDENCE_FLOOR = 0.2


# ------------------------------------------------------------------
# Event Settings
# ------------------------------------------------------------------

class EventConfig:
    CONFIDENCE_THRESHOLD = 0.5      # minimum valid event
    INACTIVE_TIMEOUT_SEC = 5.0      # mark event inactive
    MAX_EVENT_AGE_SEC = 30.0        # cleanup threshold
    
    # Required by EventManager
    MAX_CONFIDENCE = 1.0
    SPEED_NORMALIZER = 5.0          


# ------------------------------------------------------------------
# Logging Settings
# ------------------------------------------------------------------

class LoggingConfig:
    ENABLE_FILE_LOGGING = True
    METADATA_VERSION = 1
    WRITE_INDENT = 4                # JSON formatting
    
    # Required by IncidentLogger
    TEMP_FILE_SUFFIX = ".tmp"
    JSON_INDENT = 4


# ------------------------------------------------------------------
# Performance / Buffer Settings
# ------------------------------------------------------------------

class BufferConfig:
    EVENT_BUFFER_SIZE = 100
    TRACK_BUFFER_SIZE = 100
    MAX_QUEUE_SIZE = 1000
    MAX_HISTORY = 50