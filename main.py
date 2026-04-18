"""
FastAPI Application Entry Point
"""

import asyncio
import logging
import traceback
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.db.db_connection import DatabaseConnection
from app.routes import api_router

logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title="Medical Shop Pharmacy API",
    description="Backend API for Medical Shop Pharmacy Management System",
    version="1.0.0",
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


_cors_origins = settings.cors_origins_list
_allow_all_origins = len(_cors_origins) == 1 and _cors_origins[0] == "*"

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=(False if _allow_all_origins else bool(settings.CORS_ALLOW_CREDENTIALS)),
    allow_methods=settings.cors_methods_list,
    allow_headers=settings.cors_headers_list,
    expose_headers=["*"],
)


async def _init_db_background() -> None:
    """Connect and create tables after the server is listening (avoids Cloud Run timeout)."""
    await asyncio.sleep(2)
    try:
        connected = await DatabaseConnection.is_connected()
        if not connected:
            logger.warning("Database connection check failed — see logs above")
            return
        await DatabaseConnection.create_tables()
        logger.info("Database connected and tables ensured")
    except Exception as exc:
        logger.error("Background database initialization failed: %s", exc, exc_info=True)


@app.on_event("startup")
async def startup_event() -> None:
    """Create the SQLAlchemy engine immediately; verify DB in a background task."""
    try:
        DatabaseConnection.initialize()
        asyncio.create_task(_init_db_background())
        logger.info("Application started; database initialization running in background")
    except Exception as exc:
        logger.error("Failed to create database engine: %s", exc, exc_info=True)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await DatabaseConnection.close()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Medical Shop Pharmacy API", "status": "healthy"}


@app.get("/health")
async def health_check():
    """Health check with database connectivity"""
    is_connected = await DatabaseConnection.is_connected()
    return {
        "status": "healthy" if is_connected else "unhealthy",
        "database": "connected" if is_connected else "disconnected",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    req_id = getattr(getattr(request, "state", None), "request_id", None)
    logger.error("Unhandled error (request_id=%s): %s\n%s", req_id, exc, traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}", "request_id": req_id},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
            "X-Request-ID": req_id or "",
        },
    )


app.include_router(api_router)

# Local file serving only; Cloud Run uses GCS + signed URLs (no /storage mount).
if get_settings().STORAGE_BACKEND == "local":
    _storage_path = Path(get_settings().LOCAL_STORAGE_PATH).resolve()
    _storage_path.mkdir(parents=True, exist_ok=True)
    app.mount("/storage", StaticFiles(directory=str(_storage_path)), name="storage")
