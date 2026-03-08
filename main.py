"""
FastAPI Application Entry Point
"""
# (touch to trigger uvicorn --reload)
import logging
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routes import api_router
from app.db.db_connection import DatabaseConnection
from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title="Medical Shop Pharmacy API",
    description="Backend API for Medical Shop Pharmacy Management System",
    version="1.0.0"
)

# CORS — allow any origin/port/URL (no CORS errors from frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
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
    logger.error(f"Unhandled error: {exc}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )


# Include all API routes
app.include_router(api_router)
