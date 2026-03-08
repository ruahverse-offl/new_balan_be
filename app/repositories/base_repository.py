"""
Base Repository
Common CRUD operations for all repositories
"""

from typing import Optional, List, Dict, Any, TypeVar, Generic
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import DeclarativeMeta
from app.utils.pagination import calculate_pagination
from app.utils.search import apply_search_filter
from app.utils.sort import apply_sort

T = TypeVar('T', bound=DeclarativeMeta)


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""
    
    def __init__(self, model: type[T], session: AsyncSession):
        """
        Initialize repository.
        
        Args:
            model: SQLAlchemy model class
            session: Database session
        """
        self.model = model
        self.session = session
    
    def _get_searchable_fields(self) -> List[str]:
        """
        Get list of searchable field names for the model.
        Override in subclasses to customize searchable fields.
        
        Returns:
            List of field names that can be searched
        """
        # Default: search in all String and Text fields
        searchable_fields = []
        for column_name, column in self.model.__table__.columns.items():
            from sqlalchemy import String, Text
            if isinstance(column.type, (String, Text)):
                searchable_fields.append(column_name)
        return searchable_fields
    
    async def create(
        self,
        data: Dict[str, Any],
        created_by: UUID,
        created_ip: str
    ) -> T:
        """
        Create a new record.
        
        Args:
            data: Dictionary of field values
            created_by: User ID who created the record
            created_ip: IP address of creator
            
        Returns:
            Created model instance
        """
        # Add audit fields
        data["created_by"] = created_by
        data["created_ip"] = created_ip
        data["is_deleted"] = False
        
        # Create instance
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance
    
    async def get_by_id(self, id: UUID) -> Optional[T]:
        """
        Get record by ID (excluding soft-deleted).
        
        Args:
            id: Record ID
            
        Returns:
            Model instance or None if not found
        """
        stmt = select(self.model).where(
            and_(
                self.model.id == id,
                self.model.is_deleted == False
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_list(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        additional_filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[T], Dict[str, Any]]:
        """
        Get list of records with pagination, search, and sort.
        
        Args:
            limit: Number of records per page
            offset: Number of records to skip
            search: Search term
            sort_by: Field name to sort by
            sort_order: Sort order ('asc' or 'desc')
            additional_filters: Dictionary of additional field filters
            
        Returns:
            Tuple of (records list, pagination metadata)
        """
        # Base query - exclude soft-deleted
        query = select(self.model).where(self.model.is_deleted == False)
        
        # Apply additional filters
        if additional_filters:
            for field_name, field_value in additional_filters.items():
                if hasattr(self.model, field_name) and field_value is not None:
                    query = query.where(getattr(self.model, field_name) == field_value)
        
        # Apply search
        if search:
            searchable_fields = self._get_searchable_fields()
            query = apply_search_filter(query, self.model, search, searchable_fields)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply sort
        query = apply_sort(query, self.model, sort_by, sort_order)
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        # Execute query
        result = await self.session.execute(query)
        records = result.scalars().all()
        
        # Calculate pagination metadata
        pagination = calculate_pagination(total, limit, offset)
        
        return list(records), pagination
    
    async def update(
        self,
        id: UUID,
        data: Dict[str, Any],
        updated_by: UUID,
        updated_ip: str
    ) -> Optional[T]:
        """
        Update a record.
        
        Args:
            id: Record ID
            data: Dictionary of fields to update
            updated_by: User ID who updated the record
            updated_ip: IP address of updater
            
        Returns:
            Updated model instance or None if not found
        """
        # Get existing record
        instance = await self.get_by_id(id)
        if not instance:
            return None
        
        # Add audit fields
        data["updated_by"] = updated_by
        data["updated_ip"] = updated_ip
        
        # Only update keys that are columns on the model (avoid AttributeError from schema extras).
        # Allow False and 0 (only skip when value is None = "not provided").
        column_names = {c.name for c in self.model.__table__.columns}
        for key, value in data.items():
            if key not in column_names:
                continue
            if value is None:
                continue
            setattr(instance, key, value)
        
        await self.session.flush()
        await self.session.refresh(instance)
        return instance
    
    async def soft_delete(
        self,
        id: UUID,
        updated_by: UUID,
        updated_ip: str
    ) -> bool:
        """
        Soft delete a record (set is_deleted = True).
        
        Args:
            id: Record ID
            updated_by: User ID who deleted the record
            updated_ip: IP address of deleter
            
        Returns:
            True if deleted, False if not found
        """
        instance = await self.get_by_id(id)
        if not instance:
            return False
        
        instance.is_deleted = True
        instance.updated_by = updated_by
        instance.updated_ip = updated_ip
        
        await self.session.flush()
        return True
