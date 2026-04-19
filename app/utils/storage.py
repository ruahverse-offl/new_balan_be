"""
Storage Service
Handles file uploads for local, Azure Blob, and Google Cloud Storage backends.

The DB stores only paths/keys (e.g. medicine/uuid.jpg or medicines/uuid.jpg for GCS).
For GCS private buckets, browsers load images via GET /api/v1/storage/signed?path=...
which redirects to a short-lived signed URL.
"""

import asyncio
import logging
import uuid
from datetime import timedelta
from pathlib import Path

from fastapi import UploadFile

from app.config import get_settings

logger = logging.getLogger(__name__)


def get_gcs_storage_client():
    """
    Google Cloud Storage client: explicit JSON key when present, else Application Default Credentials.

    - If ``GOOGLE_APPLICATION_CREDENTIALS`` resolves to an **existing** file → service account key.
    - If the path is set but the file is missing (e.g. prod ``/secrets/...`` copied into local ``.env``) →
      log a warning and use ``storage.Client()`` (ADC), same as Cloud Run without a key file.
    - If ``GOOGLE_APPLICATION_CREDENTIALS`` is unset → ``storage.Client()`` (ADC).
    """
    from google.cloud import storage
    from google.oauth2 import service_account

    settings = get_settings()
    path = settings.resolved_google_application_credentials_path()
    if path is not None:
        if path.is_file():
            credentials = service_account.Credentials.from_service_account_file(str(path))
            return storage.Client(credentials=credentials)
        logger.warning(
            "GOOGLE_APPLICATION_CREDENTIALS points to a missing file (%s); using Application Default Credentials. "
            "Unset GOOGLE_APPLICATION_CREDENTIALS or fix the path; use STORAGE_BACKEND=local to skip GCS entirely.",
            path,
        )
    return storage.Client()


def gcs_blob_prefix_for_category(subdirectory: str) -> str:
    """Map upload category folder to GCS object prefix (matches sample: medicines/, prescriptions/)."""
    return {
        "medicine": "medicines",
        "prescription": "prescriptions",
        "others": "others",
    }.get(subdirectory, subdirectory)


def generate_gcs_signed_url(
    bucket_name: str,
    object_path: str,
    *,
    expiration_minutes: int = 60,
    method: str = "GET",
) -> str:
    """
    Build a v4 signed URL for a private GCS object. Requires credentials that can sign
    (service account key or ADC with signBlob permission).
    """
    client = get_gcs_storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_path)
    return blob.generate_signed_url(
        expiration=timedelta(minutes=expiration_minutes),
        method=method,
        version="v4",
    )


class StorageService:
    """Service for file storage operations."""

    def __init__(self):
        self.settings = get_settings()

    async def save_file(self, file: UploadFile, subdirectory: str = "") -> dict:
        """
        Save an uploaded file to the configured storage backend.

        Returns:
            dict with file_url, file_name, file_size, file_type, stored_key (relative path / object key)
        """
        if self.settings.STORAGE_BACKEND == "azure":
            return await self._save_to_azure(file, subdirectory)
        if self.settings.STORAGE_BACKEND == "gcs":
            return await self._save_to_gcs(file, subdirectory)
        return await self._save_locally(file, subdirectory)

    async def _save_locally(self, file: UploadFile, subdirectory: str) -> dict:
        """Save file under LOCAL_STORAGE_PATH/<subdirectory>/ (e.g. .../storage/devstorage/prescription/). No DB blob; no cloud."""
        storage_path = Path(self.settings.LOCAL_STORAGE_PATH)
        if subdirectory:
            storage_path = storage_path / subdirectory
        storage_path.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        ext = Path(file.filename).suffix if file.filename else ""
        filename = f"{uuid.uuid4()}{ext}"
        file_path = storage_path / filename

        # Read and write file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        file_url = f"/storage/{subdirectory}/{filename}" if subdirectory else f"/storage/{filename}"
        stored_key = f"{subdirectory}/{filename}" if subdirectory else filename

        return {
            "file_url": file_url,
            "file_name": file.filename or filename,
            "file_size": len(content),
            "file_type": file.content_type or "application/octet-stream",
            "stored_key": stored_key,
        }

    async def _save_to_azure(self, file: UploadFile, subdirectory: str) -> dict:
        """Save file to Azure Blob Storage."""
        from azure.storage.blob import BlobServiceClient

        ext = Path(file.filename).suffix if file.filename else ""
        blob_name = f"{subdirectory}/{uuid.uuid4()}{ext}" if subdirectory else f"{uuid.uuid4()}{ext}"

        content = await file.read()

        connection_string = self.settings.AZURE_STORAGE_CONNECTION_STRING
        container_name = self.settings.AZURE_STORAGE_CONTAINER_NAME

        blob_service = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service.get_blob_client(container=container_name, blob=blob_name)
        blob_client.upload_blob(content, overwrite=True, content_settings={
            "content_type": file.content_type or "application/octet-stream"
        })

        file_url = blob_client.url

        return {
            "file_url": file_url,
            "file_name": file.filename or blob_name,
            "file_size": len(content),
            "file_type": file.content_type or "application/octet-stream",
            "stored_key": blob_name,
        }

    async def _save_to_gcs(self, file: UploadFile, subdirectory: str) -> dict:
        """Upload bytes to GCS; return HTTPS signed URL for immediate preview plus stored_key."""
        bucket_name = self.settings.GCS_BUCKET_NAME
        if not bucket_name:
            raise ValueError("GCS_BUCKET_NAME is required when STORAGE_BACKEND=gcs")

        ext = Path(file.filename).suffix if file.filename else ""
        folder = gcs_blob_prefix_for_category(subdirectory)
        blob_name = f"{folder}/{uuid.uuid4()}{ext}"
        content = await file.read()
        content_type = file.content_type or "application/octet-stream"

        def _upload_and_sign() -> tuple[str, str]:
            client = get_gcs_storage_client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.upload_from_string(content, content_type=content_type)
            signed = blob.generate_signed_url(
                expiration=timedelta(days=7),
                method="GET",
                version="v4",
            )
            return signed, blob_name

        try:
            file_url, _ = await asyncio.to_thread(_upload_and_sign)
        except Exception as e:
            logger.exception("GCS upload failed: %s", e)
            raise

        return {
            "file_url": file_url,
            "file_name": file.filename or blob_name,
            "file_size": len(content),
            "file_type": content_type,
            "stored_key": blob_name,
        }
