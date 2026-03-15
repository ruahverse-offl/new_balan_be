"""
Local prescription storage (no database).
Saves prescription metadata to a JSON manifest file next to the uploaded files.
Use this for now; switch to DB or storage bucket later.
"""

import json
import logging
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

MANIFEST_FILENAME = "manifest.json"


def _get_manifest_path(storage_base: str) -> Path:
    return Path(storage_base) / "prescriptions" / MANIFEST_FILENAME


def _ensure_manifest_dir(manifest_path: Path) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)


def _load_manifest(manifest_path: Path) -> dict:
    if not manifest_path.exists():
        return {}
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning("Could not load prescription manifest: %s", e)
        return {}


def _save_manifest(manifest_path: Path, data: dict) -> None:
    _ensure_manifest_dir(manifest_path)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def save_prescription_to_manifest(
    storage_base: str,
    prescription_id: str,
    customer_id: str,
    file_url: str,
    file_name: str,
    file_size: int,
    file_type: str,
    created_by: str,
    created_ip: str,
    order_id: str | None = None,
) -> None:
    """Append one prescription entry to the local manifest (no DB)."""
    manifest_path = _get_manifest_path(storage_base)
    data = _load_manifest(manifest_path)
    data[prescription_id] = {
        "customer_id": customer_id,
        "order_id": order_id,
        "file_url": file_url,
        "file_name": file_name,
        "file_size": file_size,
        "file_type": file_type,
        "status": "PENDING",
        "reviewed_by": None,
        "review_notes": None,
        "rejection_reason": None,
        "created_by": created_by,
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
        "created_ip": created_ip,
        "updated_by": None,
        "updated_at": None,
        "updated_ip": None,
        "is_deleted": False,
    }
    _save_manifest(manifest_path, data)
    logger.info("Saved prescription %s to local manifest", prescription_id)


def get_prescription_from_manifest(storage_base: str, prescription_id: str) -> dict | None:
    """Return prescription metadata from manifest, or None if not found."""
    manifest_path = _get_manifest_path(storage_base)
    data = _load_manifest(manifest_path)
    return data.get(prescription_id)
