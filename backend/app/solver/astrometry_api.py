"""nova.astrometry.net web API implementation of SolverBackend.

Docs: https://astrometry.net/doc/net/api.html
The API is FREE. Get an API key from https://nova.astrometry.net (My Profile).

All calls POST a single form field ``request-json`` whose value is a JSON string.
File uploads use multipart/form-data with a ``request-json`` part plus a ``file`` part.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx

from app.solver.base import (
    Calibration,
    JobResults,
    RawAnnotation,
    SolveParams,
    SolverBackend,
    SubmissionState,
)


class AstrometryNetError(RuntimeError):
    pass


class AstrometryNetSolver(SolverBackend):
    def __init__(self, api_key: str, base_url: str = "https://nova.astrometry.net/api") -> None:
        if not api_key:
            raise ValueError("astrometry.net API key is required")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._session_key: str | None = None
        self._lock = asyncio.Lock()
        # Referer header helps bypass the service's anti-scraper checks.
        self._client = httpx.AsyncClient(
            timeout=60.0,
            headers={"Referer": f"{self._base_url}/login"},
        )

    # -- low level helpers -------------------------------------------------
    async def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        data = {"request-json": json.dumps(payload)}
        resp = await self._client.post(f"{self._base_url}/{path}", data=data)
        resp.raise_for_status()
        return resp.json()

    async def _get_json(self, path: str) -> dict[str, Any]:
        resp = await self._client.get(f"{self._base_url}/{path}")
        resp.raise_for_status()
        return resp.json()

    async def _ensure_session(self) -> str:
        async with self._lock:
            if self._session_key:
                return self._session_key
            result = await self._post_json("login", {"apikey": self._api_key})
            if result.get("status") != "success":
                raise AstrometryNetError(f"login failed: {result}")
            self._session_key = result["session"]
            return self._session_key

    def _build_request(self, params: SolveParams) -> dict[str, Any]:
        """Map our generic SolveParams onto astrometry.net argument names."""
        req: dict[str, Any] = {
            "publicly_visible": "y" if params.get("publicly_visible", True) else "n",
            "allow_modifications": "d",
            "allow_commercial_use": "d",
        }
        if params.get("scale_lower") is not None and params.get("scale_upper") is not None:
            req["scale_type"] = "ul"
            req["scale_lower"] = params["scale_lower"]
            req["scale_upper"] = params["scale_upper"]
            req["scale_units"] = params.get("scale_units") or "degwidth"
        if params.get("center_ra") is not None:
            req["center_ra"] = params["center_ra"]
        if params.get("center_dec") is not None:
            req["center_dec"] = params["center_dec"]
        if params.get("radius") is not None:
            req["radius"] = params["radius"]
        if params.get("downsample_factor") is not None:
            req["downsample_factor"] = params["downsample_factor"]
        return req

    # -- SolverBackend interface -------------------------------------------
    async def submit_url(self, url: str, params: SolveParams) -> str:
        session = await self._ensure_session()
        req = self._build_request(params)
        req["session"] = session
        req["url"] = url
        result = await self._post_json("url_upload", req)
        if result.get("status") != "success":
            raise AstrometryNetError(f"url_upload failed: {result}")
        return str(result["subid"])

    async def submit_file(self, path: str, filename: str, params: SolveParams) -> str:
        session = await self._ensure_session()
        req = self._build_request(params)
        req["session"] = session
        # Multipart: request-json text part + binary file part.
        with open(path, "rb") as fh:
            file_bytes = fh.read()
        files = {
            "request-json": (None, json.dumps(req), "text/plain"),
            "file": (filename, file_bytes, "application/octet-stream"),
        }
        resp = await self._client.post(f"{self._base_url}/upload", files=files)
        resp.raise_for_status()
        result = resp.json()
        if result.get("status") != "success":
            raise AstrometryNetError(f"upload failed: {result}")
        return str(result["subid"])

    async def get_submission_state(self, submission_id: str) -> SubmissionState:
        result = await self._get_json(f"submissions/{submission_id}")
        jobs = [str(j) for j in (result.get("jobs") or []) if j is not None]
        job_cals = result.get("job_calibrations") or []
        done = bool(result.get("processing_finished"))
        return SubmissionState(jobs=jobs, solved=bool(job_cals), done=done)

    async def get_job_status(self, job_id: str) -> str:
        result = await self._get_json(f"jobs/{job_id}")
        return str(result.get("status", "unknown"))

    async def get_job_results(self, job_id: str) -> JobResults:
        info = await self._get_json(f"jobs/{job_id}/info/")
        cal_raw = info.get("calibration") or {}
        calibration = Calibration(
            ra=cal_raw.get("ra"),
            dec=cal_raw.get("dec"),
            pixscale=cal_raw.get("pixscale"),
            orientation=cal_raw.get("orientation"),
            radius=cal_raw.get("radius"),
            parity=cal_raw.get("parity"),
        )
        objects_in_field = list(info.get("objects_in_field") or [])

        annotations: list[RawAnnotation] = []
        try:
            ann_raw = await self._get_json(f"jobs/{job_id}/annotations/")
            for a in ann_raw.get("annotations", []):
                annotations.append(
                    RawAnnotation(
                        kind=str(a.get("type", "unknown")),
                        names=list(a.get("names", [])),
                        pixel_x=float(a.get("pixelx", 0.0)),
                        pixel_y=float(a.get("pixely", 0.0)),
                        radius=float(a.get("radius", 0.0) or 0.0),
                    )
                )
        except (httpx.HTTPError, ValueError):
            # Annotations are best-effort; calibration is the essential result.
            pass

        return JobResults(
            calibration=calibration,
            annotations=annotations,
            objects_in_field=objects_in_field,
        )

    async def aclose(self) -> None:
        await self._client.aclose()
