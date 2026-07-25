"""Selects and builds the configured solver backend.

The rest of the app calls :func:`get_solver`; swapping to a self-hosted
solve-field engine later only means adding a new branch here.
"""
from __future__ import annotations

from functools import lru_cache

from app.config import get_settings
from app.solver.astrometry_api import AstrometryNetSolver
from app.solver.base import SolverBackend
from app.solver.mock import MockSolver


@lru_cache
def get_solver() -> SolverBackend:
    settings = get_settings()
    backend = settings.solver_backend.lower()
    if backend == "astrometry_net" and settings.astrometry_api_key:
        return AstrometryNetSolver(
            api_key=settings.astrometry_api_key,
            base_url=settings.astrometry_base_url,
        )
    # Fallback: no key configured, or explicitly requested mock.
    return MockSolver()
