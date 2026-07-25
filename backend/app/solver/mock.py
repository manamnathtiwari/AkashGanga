"""Mock solver for local development and tests (no API key required).

Returns deterministic fake calibration + annotations so the whole app flow
(upload -> solve -> annotated viewer) can be exercised offline.
"""
from __future__ import annotations

import itertools

from app.solver.base import (
    Calibration,
    JobResults,
    RawAnnotation,
    SolveParams,
    SolverBackend,
    SubmissionState,
)


class MockSolver(SolverBackend):
    def __init__(self) -> None:
        self._counter = itertools.count(1)

    async def submit_url(self, url: str, params: SolveParams) -> str:
        return str(next(self._counter))

    async def submit_file(self, path: str, filename: str, params: SolveParams) -> str:
        return str(next(self._counter))

    async def get_submission_state(self, submission_id: str) -> SubmissionState:
        return SubmissionState(jobs=[submission_id], solved=True, done=True)

    async def get_job_status(self, job_id: str) -> str:
        return "success"

    async def get_job_results(self, job_id: str) -> JobResults:
        calibration = Calibration(
            ra=170.0,
            dec=13.2,
            pixscale=1.09,
            orientation=105.7,
            radius=0.81,
            parity=1.0,
        )
        annotations = [
            RawAnnotation(kind="messier", names=["M 66"], pixel_x=400.0, pixel_y=300.0, radius=40.0),
            RawAnnotation(kind="ngc", names=["NGC 3628"], pixel_x=900.0, pixel_y=650.0, radius=55.0),
            RawAnnotation(kind="hd", names=["HD 98388"], pixel_x=1200.0, pixel_y=200.0, radius=0.0),
        ]
        return JobResults(
            calibration=calibration,
            annotations=annotations,
            objects_in_field=["M 66", "NGC 3628", "M 65"],
        )
