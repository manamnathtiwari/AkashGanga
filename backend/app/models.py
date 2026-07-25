"""Database models for AkashGanga."""
from __future__ import annotations

import enum
import os
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SubmissionStatus(str, enum.Enum):
    pending = "pending"       # created, not yet sent to solver
    submitted = "submitted"   # accepted by solver, awaiting jobs
    solving = "solving"       # a job is running
    success = "success"       # solved
    failed = "failed"         # no solution / error


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(120))
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    submissions: Mapped[list["Submission"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    # Source of the image.
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    stored_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus), default=SubmissionStatus.pending, index=True
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Identifiers returned by the solver backend.
    solver_submission_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    solver_job_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Calibration results (WCS summary) once solved.
    ra: Mapped[float | None] = mapped_column(Float, nullable=True)
    dec: Mapped[float | None] = mapped_column(Float, nullable=True)
    pixscale: Mapped[float | None] = mapped_column(Float, nullable=True)  # arcsec/pixel
    orientation: Mapped[float | None] = mapped_column(Float, nullable=True)  # degrees
    radius: Mapped[float | None] = mapped_column(Float, nullable=True)  # degrees
    parity: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Names of known objects the solver found in the field.
    objects_in_field: Mapped[list] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    user: Mapped[User] = relationship(back_populates="submissions")
    annotations: Mapped[list["Annotation"]] = relationship(
        back_populates="submission", cascade="all, delete-orphan"
    )

    @property
    def image_url(self) -> str | None:
        """Where the app can fetch the original image."""
        if self.source_url:
            return self.source_url
        if self.stored_path:
            return f"/media/{os.path.basename(self.stored_path)}"
        return None

    @property
    def annotated_image_url(self) -> str | None:
        if self.solver_job_id:
            return f"/api/jobs/{self.solver_job_id}/annotated_image"
        return None

    @property
    def redgreen_image_url(self) -> str | None:
        if self.solver_job_id:
            return f"/api/jobs/{self.solver_job_id}/red_green_image"
        return None

    @property
    def extraction_image_url(self) -> str | None:
        if self.solver_job_id:
            return f"/api/jobs/{self.solver_job_id}/extraction_image"
        return None


class Annotation(Base):
    """A known object detected in the field, positioned in image pixel coords."""

    __tablename__ = "annotations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE"), index=True
    )

    kind: Mapped[str] = mapped_column(String(32))  # e.g. star, ngc, ic, messier, hd, bright_star
    names: Mapped[list] = mapped_column(JSON, default=list)  # catalog names
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)  # proper/common name
    pixel_x: Mapped[float] = mapped_column(Float)
    pixel_y: Mapped[float] = mapped_column(Float)
    radius: Mapped[float] = mapped_column(Float, default=0.0)

    submission: Mapped[Submission] = relationship(back_populates="annotations")
