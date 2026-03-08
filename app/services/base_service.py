"""
Base Service
Common service operations
"""

from typing import TypeVar, Generic, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeMeta
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

TModel = TypeVar('TModel', bound=DeclarativeMeta)
TResponse = TypeVar('TResponse', bound=BaseModel)


class BaseService(Generic[TModel, TResponse]):
    """Base service with common operations."""
    
    def __init__(self, repository, session: AsyncSession):
        """
        Initialize service.
        
        Args:
            repository: Repository instance
            session: Database session
        """
        self.repository = repository
        self.session = session
    
    def _model_to_dict(self, model: TModel) -> Dict[str, Any]:
        """
        Convert SQLAlchemy model to dictionary.
        
        Args:
            model: SQLAlchemy model instance
            
        Returns:
            Dictionary representation of model
        """
        from app.utils.datetime_utils import convert_to_ist
        from datetime import datetime
        
        result = {}
        for column in model.__table__.columns:
            value = getattr(model, column.name)
            # Convert datetime values to IST if they are timezone-aware
            if isinstance(value, datetime) and value.tzinfo is not None:
                value = convert_to_ist(value)
            result[column.name] = value
        return result
    
    def _dict_to_response(self, data: Dict[str, Any], response_class: type[TResponse]) -> TResponse:
        """
        Convert dictionary to Pydantic response model.
        
        Args:
            data: Dictionary of field values
            response_class: Pydantic response model class
            
        Returns:
            Pydantic response instance
        """
        return response_class(**data)
