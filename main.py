"""
FastAPI Application Entry Point
"""
# (touch to trigger uvicorn --reload)
import logging
import traceback
from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes import api_router
from app.config import get_settings
from app.db.db_connection import DatabaseConnection
from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title="Medical Shop Pharmacy API",
    description="Backend API for Medical Shop Pharmacy Management System",
    version="1.0.0",
)

# Request correlation ID middleware (X-Request-ID)
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# CORS (configurable via env; lock down in production)
_cors_origins = settings.cors_origins_list
_allow_all_origins = len(_cors_origins) == 1 and _cors_origins[0] == "*"

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    # If allow_origins is ["*"], credentials MUST be false (per spec; browsers will reject otherwise)
    allow_credentials=(False if _allow_all_origins else bool(settings.CORS_ALLOW_CREDENTIALS)),
    allow_methods=settings.cors_methods_list,
    allow_headers=settings.cors_headers_list,
    expose_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database connection and create tables on startup."""
    try:
        print("[INFO] Initializing database connection...")
        DatabaseConnection.initialize()

        # Test the actual connection
        print("[INFO] Testing database connection...")
        is_connected = await DatabaseConnection.is_connected()
        if not is_connected:
            print("[WARN] Database connection test failed - check credentials")
            raise Exception("Database connection test failed")

        print("[OK] Database connection verified successfully!")

        # Create tables if they don't exist
        await DatabaseConnection.create_tables()

        # Run migrations (e.g. add doctor_id to appointments if missing)
        from app.db.migrations import run_migrations
        await run_migrations(DatabaseConnection.get_engine())

    except Exception as e:
        print(f"[ERROR] Failed to initialize database: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown."""
    await DatabaseConnection.close()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Medical Shop Pharmacy API", "status": "healthy"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    is_connected = await DatabaseConnection.is_connected()
    return {
        "status": "healthy" if is_connected else "unhealthy",
        "database": "connected" if is_connected else "disconnected"
    }


# Global exception handler so 500 errors return JSON with CORS headers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    req_id = getattr(getattr(request, "state", None), "request_id", None)
    logger.error(f"Unhandled error (request_id={req_id}): {exc}\n{traceback.format_exc()}")
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


# Include all API routes
app.include_router(api_router)

# Serve stored files at /storage (e.g. /storage/medicine/xxx.jpg). Use LOCAL_STORAGE_PATH.
_storage_path = Path(get_settings().LOCAL_STORAGE_PATH)
if _storage_path.exists():
    app.mount("/storage", StaticFiles(directory=str(_storage_path)), name="storage")
