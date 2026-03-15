"""
Storage Service
Handles file uploads for local and Azure Blob storage backends.

For now prescriptions (and other uploads) are stored on LOCAL STORAGE (disk) only;
the DB stores only metadata (file_url, file_name, etc.). A storage bucket (e.g. S3/Azure)
can be enabled later via STORAGE_BACKEND=azure.
"""

import os
import uuid
from pathlib import Path
from fastapi import UploadFile
from app.config import get_settings


class StorageService:
    """Service for file storage operations."""

    def __init__(self):
        self.settings = get_settings()

    async def save_file(self, file: UploadFile, subdirectory: str = "") -> dict:
        """
        Save an uploaded file to the configured storage backend.

        Returns:
            dict with file_url, file_name, file_size, file_type
        """
        if self.settings.STORAGE_BACKEND == "azure":
            return await self._save_to_azure(file, subdirectory)
        return await self._save_locally(file, subdirectory)

    async def _save_locally(self, file: UploadFile, subdirectory: str) -> dict:
        """Save file to local filesystem (e.g. ./storage/prescriptions/). No DB blob; no cloud."""
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

        return {
            "file_url": file_url,
            "file_name": file.filename or filename,
            "file_size": len(content),
            "file_type": file.content_type or "application/octet-stream"
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
            "file_type": file.content_type or "application/octet-stream"
        }
