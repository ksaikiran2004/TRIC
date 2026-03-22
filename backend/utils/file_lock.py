"""
TRIC - File Lock Utility

FILE: backend/utils/file_lock.py

Responsibility:
Provide a simple, cross-platform file locking mechanism for safe concurrent access
within the same process.
"""

from contextlib import contextmanager
from threading import Lock
from typing import Dict


# Global lock registry (per-process)
_FILE_LOCKS: Dict[str, Lock] = {}
_REGISTRY_LOCK = Lock()


def _get_lock(file_path: str) -> Lock:
    """
    Retrieve or create a lock for a given file path in a thread-safe manner.
    """
    with _REGISTRY_LOCK:
        if file_path not in _FILE_LOCKS:
            _FILE_LOCKS[file_path] = Lock()
        return _FILE_LOCKS[file_path]


@contextmanager
def file_lock(file_path: str):
    """
    Context manager to provide exclusive access to a file within a process.

    Usage:
        with file_lock(path):
            # safe file operations
            ...

    Args:
        file_path: Path to the file to lock
    """
    lock = _get_lock(file_path)
    lock.acquire()
    try:
        yield
    finally:
        lock.release()