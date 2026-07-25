"""Background solve pipeline: submit to solver, poll, persist results.

Runs as a FastAPI background task. Opens its own DB session because it lives
outside the request lifecycle.
"""
from __future__ import annotations

import asyncio
import logging
import os

from app.database import SessionLocal
from app.enrich.star_names import enrich_annotations
from app.models import Annotation, Submission, SubmissionStatus
from app.preprocess import preprocess_image
from app.solver.base import SolveParams
from app.solver.factory import get_solver

logger = logging.getLogger("akashganga.worker")

_POLL_INTERVAL_SECONDS = 5
_MAX_POLLS = 120  # ~10 minutes


async def run_solve(submission_id: int, params: dict) -> None:
    solver = get_solver()
    async with SessionLocal() as session:
        submission = await session.get(Submission, submission_id)
        if submission is None:
            logger.warning("submission %s vanished before solving", submission_id)
            return

        try:
            solve_params = SolveParams(params)

            # 1. Submit to the solver backend.
            if submission.source_url:
                solver_sub_id = await solver.submit_url(submission.source_url, solve_params)
            elif submission.stored_path:
                # Auto-preprocess dark / oversized phone photos before submission.
                ready_path = preprocess_image(submission.stored_path)
                try:
                    solver_sub_id = await solver.submit_file(
                        ready_path,
                        submission.original_filename or "image",
                        solve_params,
                    )
                finally:
                    # Clean up temp file if preprocessing created one.
                    if ready_path != submission.stored_path and os.path.exists(ready_path):
                        os.unlink(ready_path)
            else:
                raise ValueError("submission has neither URL nor stored file")

            submission.solver_submission_id = solver_sub_id
            submission.status = SubmissionStatus.submitted
            await session.commit()

            # 2. Poll for a job.
            job_id = await _wait_for_job(solver, solver_sub_id)
            if job_id is None:
                submission.status = SubmissionStatus.failed
                submission.error = "No solving job was created (image may be unsolvable)."
                await session.commit()
                return

            submission.solver_job_id = job_id
            submission.status = SubmissionStatus.solving
            await session.commit()

            # 3. Poll job status until success/failure.
            final_status = await _wait_for_job_status(solver, job_id)
            if final_status != "success":
                submission.status = SubmissionStatus.failed
                submission.error = "The image could not be solved."
                await session.commit()
                return

            # 4. Fetch + persist results.
            results = await solver.get_job_results(job_id)
            cal = results.calibration
            if cal is not None:
                submission.ra = cal.ra
                submission.dec = cal.dec
                submission.pixscale = cal.pixscale
                submission.orientation = cal.orientation
                submission.radius = cal.radius
                submission.parity = cal.parity

            submission.objects_in_field = list(results.objects_in_field)

            for enriched in enrich_annotations(results.annotations):
                session.add(Annotation(submission_id=submission.id, **enriched))

            submission.status = SubmissionStatus.success
            await session.commit()
            logger.info("submission %s solved (job %s)", submission_id, job_id)

        except Exception as exc:  # noqa: BLE001 - record any failure for the user
            logger.exception("solve failed for submission %s", submission_id)
            await session.rollback()
            submission = await session.get(Submission, submission_id)
            if submission is not None:
                submission.status = SubmissionStatus.failed
                submission.error = str(exc)[:500]
                await session.commit()


async def _wait_for_job(solver, solver_sub_id: str) -> str | None:
    # nova.astrometry.net can set processing_finished BEFORE populating the jobs
    # list.  We keep polling for up to _DONE_GRACE_POLLS extra cycles after
    # processing_finished is first seen so we don't bail out too early.
    _DONE_GRACE_POLLS = 6   # 6 × 5 s = 30 s grace window
    done_count = 0
    for _ in range(_MAX_POLLS):
        state = await solver.get_submission_state(solver_sub_id)
        if state.jobs:
            return state.jobs[0]
        if state.done:
            done_count += 1
            if done_count >= _DONE_GRACE_POLLS:
                return None   # gave up waiting for job after grace window
        await asyncio.sleep(_POLL_INTERVAL_SECONDS)
    return None


async def _wait_for_job_status(solver, job_id: str) -> str:
    for _ in range(_MAX_POLLS):
        status = await solver.get_job_status(job_id)
        if status in ("success", "failure"):
            return status
        await asyncio.sleep(_POLL_INTERVAL_SECONDS)
    return "failure"
