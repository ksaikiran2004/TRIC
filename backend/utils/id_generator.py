"""
TRIC - ID Generator Utilities

FILE: backend/utils/id_generator.py

Responsibility:
Provide standardized ID generation functions across the system.
"""

import uuid


def generate_id() -> str:
    """
    Generate a unique UUID4-based string ID.

    Returns:
        UUID string
    """
    return str(uuid.uuid4())


def generate_prefixed_id(prefix: str) -> str:
    """
    Generate a prefixed UUID4-based string ID.

    Args:
        prefix: Prefix string (e.g., "event")

    Returns:
        Prefixed ID string (e.g., "event_<uuid>")
    """
    return f"{prefix}_{uuid.uuid4()}"