"""
Send FCM HTTP v1 messages using a Google service account (Firebase Cloud Messaging).

All device tokens stored in ``M_notification_settings.expo_push_token`` are treated
as FCM registration tokens. The column name is historical.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import httpx
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import service_account

from app.config import get_settings

logger = logging.getLogger(__name__)

_FCM_SCOPE = "https://www.googleapis.com/auth/firebase.messaging"


def _service_account_path() -> Optional[Path]:
    settings = get_settings()
    p = settings.resolved_fcm_credentials_path()
    if p and p.is_file():
        return p
    # fallback to GCS credentials only if FCM_CREDENTIALS_PATH is not set
    p = settings.resolved_google_application_credentials_path()
    return p if p and p.is_file() else None


def _sync_access_token_and_project() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Load credentials for FCM scope from FCM_CREDENTIALS_PATH service account JSON.

    Returns:
        Tuple of (access_token, project_id, error_message). On success error is None.
    """
    path = _service_account_path()
    if not path:
        return None, None, "FCM: no service account JSON (set FCM_CREDENTIALS_PATH)"

    try:
        creds = service_account.Credentials.from_service_account_file(
            str(path),
            scopes=[_FCM_SCOPE],
        )
        creds.refresh(GoogleAuthRequest())
        token = creds.token
        project = creds.project_id
        if not token or not project:
            return None, None, "FCM: missing token or project_id after credential refresh"
        return token, project, None
    except Exception as exc:  # noqa: BLE001
        logger.warning("FCM credential load failed: %s", exc)
        return None, None, f"FCM: credential error: {exc}"


async def send_fcm_notification(
    *,
    device_token: str,
    title: str,
    body: str,
    data: Dict[str, str],
    android_channel_id: str = "delivery_default",
) -> Dict[str, Any]:
    """
    Send one FCM HTTP v1 message to a device registration token.

    ``data`` values are coerced to strings as required by FCM.

    Returns:
        Dict with keys: ok (bool), status (str), message (str), http_status (optional int).
    """
    token, project, err = await asyncio.to_thread(_sync_access_token_and_project)
    if err or not token or not project:
        return {"ok": False, "status": "error", "message": err or "FCM unavailable"}

    url = f"https://fcm.googleapis.com/v1/projects/{project}/messages:send"
    str_data = {k: str(v) for k, v in data.items()}
    payload: Dict[str, Any] = {
        "message": {
            "token": device_token.strip(),
            "notification": {"title": title, "body": body},
            "data": str_data,
            "android": {
                "priority": "HIGH",
                "notification": {"channel_id": android_channel_id},
            },
        }
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
        try:
            body_json = resp.json()
        except Exception:
            body_json = {"raw": resp.text[:2000]}
        if 200 <= resp.status_code < 300:
            return {"ok": True, "status": "ok", "message": "sent", "http_status": resp.status_code, "body": body_json}
        err_msg = body_json.get("error", {}).get("message") if isinstance(body_json, dict) else str(body_json)
        return {
            "ok": False,
            "status": "error",
            "message": str(err_msg or resp.reason_phrase)[:2000],
            "http_status": resp.status_code,
            "body": body_json,
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("FCM HTTP request failed: %s", exc)
        return {"ok": False, "status": "error", "message": str(exc)[:2000]}
