"""
Payments Service
Business logic layer for payments
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.repositories.payments_repository import PaymentsRepository
from app.schemas.payments_schema import (
    PaymentCreateRequest,
    PaymentUpdateRequest,
    PaymentResponse,
    PaymentListResponse
)
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class PaymentsService(BaseService):
    """Service for payments operations."""
    
    def __init__(self, session: AsyncSession):
        repository = PaymentsRepository(session)
        super().__init__(repository, session)
    
    async def create_payment(
        self,
        data: PaymentCreateRequest,
        created_by: UUID,
        created_ip: str
    ) -> PaymentResponse:
        """Create a new payment."""
        logger.info(f"Creating payment for order: {data.order_id}")
        payment_data = data.model_dump()
        payment = await self.repository.create(payment_data, created_by, created_ip)
        payment_dict = self._model_to_dict(payment)
        return PaymentResponse(**payment_dict)
    
    async def get_payment_by_id(self, payment_id: UUID) -> Optional[PaymentResponse]:
        """Get payment by ID."""
        payment = await self.repository.get_by_id(payment_id)
        if not payment:
            return None
        payment_dict = self._model_to_dict(payment)
        return PaymentResponse(**payment_dict)
    
    async def get_payments_list(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None
    ) -> PaymentListResponse:
        """Get list of payments with pagination, search, and sort."""
        payments, pagination = await self.repository.get_list(
            limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order
        )
        payment_responses = [
            PaymentResponse(**self._model_to_dict(p)) for p in payments
        ]
        return PaymentListResponse(
            items=payment_responses,
            pagination=PaginationResponse(**pagination)
        )
    
    async def update_payment(
        self,
        payment_id: UUID,
        data: PaymentUpdateRequest,
        updated_by: UUID,
        updated_ip: str
    ) -> Optional[PaymentResponse]:
        """Update a payment."""
        logger.info(f"Updating payment: {payment_id}")
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        payment = await self.repository.update(payment_id, update_data, updated_by, updated_ip)
        if not payment:
            return None
        payment_dict = self._model_to_dict(payment)
        return PaymentResponse(**payment_dict)
    
    async def delete_payment(
        self,
        payment_id: UUID,
        updated_by: UUID,
        updated_ip: str
    ) -> bool:
        """Soft delete a payment."""
        logger.info(f"Deleting payment: {payment_id}")
        return await self.repository.soft_delete(payment_id, updated_by, updated_ip)
