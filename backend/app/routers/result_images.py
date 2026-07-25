"""Proxy result overlay images from nova.astrometry.net to the app.

Three image types per solved job:
  annotated  – original image with constellation lines, object labels, quad
  red_green  – red=solver-detected sources, green=index catalog stars
  extraction – blue circles on detected sources (star extraction preview)
"""
from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.config import get_settings

router = APIRouter(prefix="/jobs", tags=["result-images"])

_IMAGE_ENDPOINTS = {
    "annotated": "annotated_display",
    "red_green": "red_green_image_display",
    "extraction": "extraction_image_display",
}

_BASE = "https://nova.astrometry.net"
_HEADERS = {"Referer": "https://nova.astrometry.net/api/login"}


async def _proxy_image(job_id: str, endpoint_key: str) -> StreamingResponse:
    path = _IMAGE_ENDPOINTS[endpoint_key]
    url = f"{_BASE}/{path}/{job_id}"
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(url, headers=_HEADERS)
    if resp.status_code == 404:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Image not ready or job not found")
    if resp.status_code != 200:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail=f"Upstream returned {resp.status_code}")
    ct = resp.headers.get("content-type", "image/png")
    return StreamingResponse(iter([resp.content]), media_type=ct)


@router.get("/{job_id}/annotated_image")
async def annotated_image(job_id: str) -> StreamingResponse:
    """Original image with constellation lines, object labels, quad overlay."""
    return await _proxy_image(job_id, "annotated")


@router.get("/{job_id}/red_green_image")
async def red_green_image(job_id: str) -> StreamingResponse:
    """Red = solver-detected stars. Green = index-catalog stars."""
    return await _proxy_image(job_id, "red_green")


@router.get("/{job_id}/extraction_image")
async def extraction_image(job_id: str) -> StreamingResponse:
    """Blue circles on every detected source (star extraction preview)."""
    return await _proxy_image(job_id, "extraction")
