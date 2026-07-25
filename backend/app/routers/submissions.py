"""Submission routes: create (URL or file upload), list, detail."""
from __future__ import annotations

import os
import uuid

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_session
from app.deps import get_current_user
from app.models import Submission, SubmissionStatus, User
from app.schemas import (
    SubmissionDetailResponse,
    SubmissionResponse,
    UrlSubmissionRequest,
)
from app.worker import run_solve

router = APIRouter(prefix="/submissions", tags=["submissions"])
settings = get_settings()

_ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".gif", ".tif", ".tiff", ".fits", ".fit", ".fz"}


@router.post("/url", response_model=SubmissionResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_url(
    payload: UrlSubmissionRequest,
    background: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Submission:
    submission = Submission(
        user_id=current_user.id,
        source_url=payload.url,
        status=SubmissionStatus.pending,
    )
    session.add(submission)
    await session.commit()
    await session.refresh(submission)

    background.add_task(run_solve, submission.id, payload.options.model_dump())
    return submission


@router.post("/upload", response_model=SubmissionResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_upload(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    publicly_visible: bool = Form(True),
    scale_lower: float | None = Form(None),
    scale_upper: float | None = Form(None),
    scale_units: str | None = Form(None),
    downsample_factor: float | None = Form(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Submission:
    filename = file.filename or "image"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in _ALLOWED_EXT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'.",
        )

    os.makedirs(settings.upload_dir, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}{ext}"
    stored_path = os.path.join(settings.upload_dir, stored_name)
    with open(stored_path, "wb") as out:
        while chunk := await file.read(1024 * 1024):
            out.write(chunk)

    submission = Submission(
        user_id=current_user.id,
        original_filename=filename,
        stored_path=stored_path,
        status=SubmissionStatus.pending,
    )
    session.add(submission)
    await session.commit()
    await session.refresh(submission)

    options = {
        "publicly_visible": publicly_visible,
        "scale_lower": scale_lower,
        "scale_upper": scale_upper,
        "scale_units": scale_units,
        "downsample_factor": downsample_factor,
    }
    background.add_task(run_solve, submission.id, options)
    return submission


@router.get("", response_model=list[SubmissionResponse])
async def list_submissions(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[Submission]:
    result = await session.scalars(
        select(Submission)
        .where(Submission.user_id == current_user.id)
        .order_by(Submission.created_at.desc())
    )
    return list(result)


@router.get("/{submission_id}", response_model=SubmissionDetailResponse)
async def get_submission(
    submission_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SubmissionDetailResponse:
    submission = await session.get(Submission, submission_id)
    if submission is None or submission.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    # Eager-load annotations.
    await session.refresh(submission, attribute_names=["annotations"])

    detail = SubmissionDetailResponse.model_validate(submission)
    detail.objects_in_field = list(submission.objects_in_field or [])
    return detail
