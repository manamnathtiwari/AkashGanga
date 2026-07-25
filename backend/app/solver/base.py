"""Solver backend abstraction.

The rest of the app depends only on this interface, so we can swap the free
nova.astrometry.net web API for a self-hosted solve-field engine later without
touching routers or the database layer.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field


@dataclass
class Calibration:
    ra: float | None = None
    dec: float | None = None
    pixscale: float | None = None      # arcsec / pixel
    orientation: float | None = None   # degrees
    radius: float | None = None        # degrees
    parity: float | None = None


@dataclass
class RawAnnotation:
    kind: str                          # star, ngc, ic, messier, hd, ...
    names: list[str]
    pixel_x: float
    pixel_y: float
    radius: float = 0.0


@dataclass
class JobResults:
    calibration: Calibration | None = None
    annotations: list[RawAnnotation] = field(default_factory=list)
    objects_in_field: list[str] = field(default_factory=list)


@dataclass
class SubmissionState:
    jobs: list[str] = field(default_factory=list)
    solved: bool = False
    done: bool = False  # processing finished (may be failure)


class SolveParams(dict):
    """Loose bag of solver hints (scale, center, downsample, ...)."""


class SolverBackend(abc.ABC):
    """Interface every solver implementation must satisfy."""

    @abc.abstractmethod
    async def submit_url(self, url: str, params: SolveParams) -> str:
        """Submit an image URL; return a solver submission id."""

    @abc.abstractmethod
    async def submit_file(self, path: str, filename: str, params: SolveParams) -> str:
        """Submit a local image file; return a solver submission id."""

    @abc.abstractmethod
    async def get_submission_state(self, submission_id: str) -> SubmissionState:
        """Poll a submission for its jobs / completion state."""

    @abc.abstractmethod
    async def get_job_status(self, job_id: str) -> str:
        """Return 'success', 'solving', 'failure', or 'unknown'."""

    @abc.abstractmethod
    async def get_job_results(self, job_id: str) -> JobResults:
        """Fetch calibration + annotations for a finished job."""

    async def aclose(self) -> None:  # optional cleanup hook
        return None
