"""AkashGanga backend application entrypoint."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import init_db
from app.routers import auth, result_images, submissions

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    os.makedirs(settings.upload_dir, exist_ok=True)
    yield


app = FastAPI(
    title="AkashGanga API",
    description="Plate-solve astrophotos and get an annotated map of the sky.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(submissions.router, prefix="/api")
app.include_router(result_images.router, prefix="/api")

# Serve uploaded originals so the app can display them.
app.mount(
    "/media",
    StaticFiles(directory=settings.upload_dir, check_dir=False),
    name="media",
)


@app.get("/api/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok", "solver": settings.solver_backend}
