"""
Generic file upload and list API.
Saves files to LOCAL_STORAGE_PATH/<category>/ (default: <workspace>/storage/devstorage/medicine|prescription|others),
Azure Blob, or Google Cloud Storage when STORAGE_BACKEND=gcs.

For GCS, DB stores object keys like medicines/<uuid>.jpg; browsers open images via GET /storage/signed?path=...
"""

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, status, UploadFile
from fastapi.responses import RedirectResponse

from app.config import get_settings
from app.utils.auth import get_current_user_id
from app.utils.storage import StorageService, generate_gcs_signed_url

router = APIRouter(prefix="/api/v1", tags=["upload"])

ALLOWED_CONTENT_PREFIXES = ("image/", "application/pdf", "text/")
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    category: str = Form(..., pattern="^(medicine|prescription|others)$"),
    _user_id: UUID = Depends(get_current_user_id),
):
    """
    Upload a file to a category folder (medicine, prescription, others).
    Requires JWT. Returns filename, stored_as (relative path), and url for frontend.
    """
    if not (file.content_type and file.content_type.startswith(ALLOWED_CONTENT_PREFIXES)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Allowed: image/*, application/pdf, text/*",
        )
    if category == "medicine" and not (file.content_type and file.content_type.startswith("image/")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Medicine uploads must be images (image/*).",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum ({MAX_FILE_SIZE // (1024*1024)}MB)",
        )
    await file.seek(0)

    storage_service = StorageService()
    try:
        info = await storage_service.save_file(file, subdirectory=category)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Save failed: {str(e)}",
        )

    if info.get("stored_key"):
        stored_relative = info["stored_key"]
    elif info["file_url"].startswith("/storage/"):
        stored_relative = info["file_url"].replace("/storage/", "", 1)
    else:
        stored_relative = f"{category}/{Path(info['file_url']).name}"

    return {
        "filename": info["file_name"],
        "stored_as": stored_relative,
        "url": info["file_url"],
        "file_size": info["file_size"],
        "file_type": info["file_type"],
    }


@router.get("/files/{category}/")
async def list_files(category: str):
    """List stored filenames in a category (medicine, prescription, others)."""
    if category not in ("medicine", "prescription", "others"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid category")
    settings = get_settings()
    dir_path = Path(settings.LOCAL_STORAGE_PATH) / category
    if not dir_path.is_dir():
        return {"files": []}
    files = [f.name for f in dir_path.iterdir() if f.is_file()]
    return {"files": files}


_GCS_SIGNED_PREFIXES = ("medicines/", "prescriptions/", "others/")


@router.get("/storage/signed")
async def redirect_to_signed_storage(
    path: str = Query(
        ...,
        description="GCS object key, e.g. medicines/uuid.jpg",
        alias="path",
    ),
):
    """
    Redirect to a time-limited GCS signed URL so <img src> and <a href> work for private buckets.
    Allowed prefixes: medicines/, prescriptions/, others/
    """
    settings = get_settings()
    if settings.STORAGE_BACKEND != "gcs" or not settings.GCS_BUCKET_NAME:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GCS storage is not configured",
        )
    key = (path or "").strip()
    if not key or ".." in key or key.startswith("/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid path")
    if not any(key.startswith(p) for p in _GCS_SIGNED_PREFIXES):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported object path")

    try:
        signed = generate_gcs_signed_url(
            settings.GCS_BUCKET_NAME,
            key,
            expiration_minutes=60,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not sign URL: {str(e)}",
        ) from e

    return RedirectResponse(url=signed, status_code=302)
