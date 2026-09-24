"""Compatibility bridge for moved simulation tooling.

This keeps the demo flow available while the production codebase moves to
CCTV-first orchestration.
"""

from backend.simulation import *  # noqa: F401,F403
