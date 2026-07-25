"""Pydantic request/response schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---- Auth ----
class RegisterRequest(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    display_name: str
    created_at: datetime


# ---- Submissions ----
class SolveOptions(BaseModel):
    """Optional hints forwarded to the solver to speed things up."""

    scale_lower: float | None = None
    scale_upper: float | None = None
    scale_units: str | None = None  # degwidth | arcminwidth | arcsecperpix
    center_ra: float | None = None
    center_dec: float | None = None
    radius: float | None = None
    downsample_factor: float | None = None
    publicly_visible: bool = True


class UrlSubmissionRequest(BaseModel):
    url: str
    options: SolveOptions = SolveOptions()


class AnnotationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    kind: str
    names: list[str]
    display_name: str | None
    pixel_x: float
    pixel_y: float
    radius: float


class SubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    error: str | None
    original_filename: str | None
    source_url: str | None
    image_url: str | None = None
    annotated_image_url: str | None = None
    redgreen_image_url: str | None = None
    extraction_image_url: str | None = None
    solver_job_id: str | None = None
    ra: float | None
    dec: float | None
    pixscale: float | None
    orientation: float | None
    radius: float | None
    parity: float | None
    created_at: datetime
    updated_at: datetime


class SubmissionDetailResponse(SubmissionResponse):
    annotations: list[AnnotationResponse] = []
    objects_in_field: list[str] = []
