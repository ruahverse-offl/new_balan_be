"""
Delivery Settings Service
Business logic layer for delivery_settings
"""

from decimal import Decimal
from typing import Optional, Any, Dict
from uuid import UUID
from datetime import datetime, date
import json
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.repositories.delivery_settings_repository import DeliverySettingsRepository
from app.schemas.delivery_settings_schema import (
    DeliverySettingCreateRequest,
    DeliverySettingUpdateRequest,
)
from app.services.base_service import BaseService
from app.utils.delivery_windows import delivery_schedule_public_meta

logger = logging.getLogger(__name__)


def _map_delivery_aliases_in(settings_data: Dict[str, Any]) -> Dict[str, Any]:
    """Map API field ``free_delivery_min_amount`` to DB column ``free_delivery_threshold``."""
    data = dict(settings_data)
    if "free_delivery_min_amount" in data:
        v = data.pop("free_delivery_min_amount", None)
        if v is not None:
            data["free_delivery_threshold"] = v
    return data


def _enrich_delivery_dict(settings_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Expose ``free_delivery_min_amount`` alongside ``free_delivery_threshold``."""
    d = dict(settings_dict)
    ft = d.get("free_delivery_threshold")
    d["free_delivery_min_amount"] = ft
    return d


def _to_jsonable_value(v: Any) -> Any:
    """Convert a single value to JSON-serializable type."""
    if v is None:
        return None
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (datetime, date)):
        return v.isoformat() if hasattr(v, "isoformat") else str(v)
    if isinstance(v, UUID):
        return str(v)
    if isinstance(v, dict):
        return _to_jsonable_dict(v)
    if isinstance(v, list):
        return [_to_jsonable_value(x) for x in v]
    return v


def _to_jsonable_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a settings dict to JSON-serializable types (no Decimal, no datetime objects, no UUID)."""
    return {k: _to_jsonable_value(v) for k, v in data.items()}


class DeliverySettingsService(BaseService):
    """Service for delivery_settings operations."""
    
    def __init__(self, session: AsyncSession):
        repository = DeliverySettingsRepository(session)
        super().__init__(repository, session)
    
    async def get_delivery_settings(self) -> Optional[Dict[str, Any]]:
        """Get delivery settings (singleton)."""
        settings = await self.repository.get_singleton()
        if not settings:
            return None
        settings_dict = self._model_to_dict(settings)
        # Parse JSON delivery_zones if present
        if settings_dict.get("delivery_zones"):
            try:
                settings_dict["delivery_zones"] = json.loads(settings_dict["delivery_zones"])
            except (json.JSONDecodeError, TypeError):
                settings_dict["delivery_zones"] = None
        if settings_dict.get("delivery_slot_times"):
            try:
                settings_dict["delivery_slot_times"] = json.loads(settings_dict["delivery_slot_times"])
            except (json.JSONDecodeError, TypeError):
                settings_dict["delivery_slot_times"] = []
        else:
            settings_dict["delivery_slot_times"] = []
        enriched = _enrich_delivery_dict(settings_dict)
        enriched["delivery_schedule"] = delivery_schedule_public_meta(
            bool(enriched.get("is_enabled", True)),
            enriched.get("delivery_slot_times"),
        )
        return _to_jsonable_dict(enriched)

    async def create_or_update_delivery_settings(
        self,
        data: DeliverySettingCreateRequest | DeliverySettingUpdateRequest,
        created_by: UUID,
        created_ip: str,
        updated_by: Optional[UUID] = None,
        updated_ip: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create or update delivery settings (singleton). Returns a JSON-serializable dict."""
        logger.info("Creating/updating delivery settings")
        settings_data = data.model_dump(exclude_unset=True)
        settings_data = _map_delivery_aliases_in(settings_data)

        # Convert delivery_zones to JSON string if present
        if "delivery_zones" in settings_data and settings_data["delivery_zones"]:
            settings_data["delivery_zones"] = json.dumps(settings_data["delivery_zones"])
        if "delivery_slot_times" in settings_data and settings_data["delivery_slot_times"] is not None:
            dst = settings_data["delivery_slot_times"]
            if isinstance(dst, str):
                settings_data["delivery_slot_times"] = dst
            else:
                rows = []
                for w in dst or []:
                    if hasattr(w, "model_dump"):
                        rows.append(w.model_dump())
                    elif isinstance(w, dict):
                        rows.append(w)
                    else:
                        rows.append(dict(w))
                settings_data["delivery_slot_times"] = json.dumps(rows)
        
        if isinstance(data, DeliverySettingCreateRequest):
            settings_data["is_active"] = True
        
        settings = await self.repository.create_or_update(
            settings_data, created_by, created_ip, updated_by, updated_ip
        )
        if settings is None:
            raise ValueError("Delivery settings create_or_update returned None (record may be missing)")
        settings_dict = self._model_to_dict(settings)
        # Parse JSON delivery_zones if present
        if settings_dict.get("delivery_zones"):
            try:
                settings_dict["delivery_zones"] = json.loads(settings_dict["delivery_zones"])
            except (json.JSONDecodeError, TypeError):
                settings_dict["delivery_zones"] = None
        if settings_dict.get("delivery_slot_times"):
            try:
                settings_dict["delivery_slot_times"] = json.loads(settings_dict["delivery_slot_times"])
            except (json.JSONDecodeError, TypeError):
                settings_dict["delivery_slot_times"] = []
        else:
            settings_dict["delivery_slot_times"] = []
        enriched = _enrich_delivery_dict(settings_dict)
        enriched["delivery_schedule"] = delivery_schedule_public_meta(
            bool(enriched.get("is_enabled", True)),
            enriched.get("delivery_slot_times"),
        )
        return _to_jsonable_dict(enriched)
