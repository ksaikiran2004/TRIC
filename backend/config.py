"""
TRIC - Backend Config Interface

Responsibilities:
    - Provide unified access to all configuration settings
    - Act as a bridge between settings and backend modules
    - Keep configuration usage clean and consistent
"""

from config.settings import (
    SimulationConfig,
    TrackingConfig,
    DirectionConfig,
    EventConfig,
    LoggingConfig,
    SystemPaths,
    BufferConfig
)


class Config:
    """
    Central configuration access layer.
    """

    simulation = SimulationConfig
    tracking = TrackingConfig
    direction = DirectionConfig
    event = EventConfig
    logging = LoggingConfig
    paths = SystemPaths
    buffer = BufferConfig