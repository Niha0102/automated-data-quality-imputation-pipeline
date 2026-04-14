from contextlib import asynccontextmanager
import os
import pathlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.middleware import RateLimitMiddleware
from app.db.mongo import close_mongo_client
from app.db.redis import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_mongo_client()
    await close_redis()


app = FastAPI(
    title="AI Data Quality Intelligence Platform",
    version="1.0.0",
    description="Automated data quality analysis, cleaning, and reporting powered by AI.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)

# ── Routers ───────────────────────────────────────────────────────────────────
from app.api.v1 import auth, datasets, jobs, alerts, admin, reports  # noqa: E402
from app.api.v1.websocket import router as ws_router  # noqa: E402

app.include_router(auth.router, prefix="/api/v1")
app.include_router(datasets.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(ws_router)

# Serve local uploads (local dev only)
_uploads_dir = pathlib.Path(__file__).parent.parent.parent / "local_uploads"
if _uploads_dir.exists():
    app.mount("/local-files", StaticFiles(directory=str(_uploads_dir)), name="local-files")


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "service": "backend"}
