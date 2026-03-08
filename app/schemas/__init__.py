"""
Schemas Layer
Pydantic models for request/response validation
"""

# Common schemas
from app.schemas.common import (
    PaginationResponse,
    ListResponse,
    ErrorDetail,
    ErrorResponse,
    BaseCreateRequest,
    BaseUpdateRequest,
    BaseResponse
)

# Roles schemas
from app.schemas.roles_schema import (
    RoleCreateRequest,
    RoleUpdateRequest,
    RoleResponse,
    RoleListResponse
)

# Permissions schemas
from app.schemas.permissions_schema import (
    PermissionCreateRequest,
    PermissionUpdateRequest,
    PermissionResponse,
    PermissionListResponse
)

# Role Permissions schemas
from app.schemas.role_permissions_schema import (
    RolePermissionCreateRequest,
    RolePermissionUpdateRequest,
    RolePermissionResponse,
    RolePermissionListResponse
)

# Users schemas
from app.schemas.users_schema import (
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse,
    UserListResponse
)

# Pharmacist Profiles schemas
from app.schemas.pharmacist_profiles_schema import (
    PharmacistProfileCreateRequest,
    PharmacistProfileUpdateRequest,
    PharmacistProfileResponse,
    PharmacistProfileListResponse
)

# Therapeutic Categories schemas
from app.schemas.therapeutic_categories_schema import (
    TherapeuticCategoryCreateRequest,
    TherapeuticCategoryUpdateRequest,
    TherapeuticCategoryResponse,
    TherapeuticCategoryListResponse
)

# Medicines schemas
from app.schemas.medicines_schema import (
    MedicineCreateRequest,
    MedicineUpdateRequest,
    MedicineResponse,
    MedicineListResponse
)

# Medicine Compositions schemas
from app.schemas.medicine_compositions_schema import (
    MedicineCompositionCreateRequest,
    MedicineCompositionUpdateRequest,
    MedicineCompositionResponse,
    MedicineCompositionListResponse
)

# Medicine Brands schemas
from app.schemas.medicine_brands_schema import (
    MedicineBrandCreateRequest,
    MedicineBrandUpdateRequest,
    MedicineBrandResponse,
    MedicineBrandListResponse
)

# Product Batches schemas
from app.schemas.product_batches_schema import (
    ProductBatchCreateRequest,
    ProductBatchUpdateRequest,
    ProductBatchResponse,
    ProductBatchListResponse
)

# Inventory Transactions schemas
from app.schemas.inventory_transactions_schema import (
    InventoryTransactionCreateRequest,
    InventoryTransactionUpdateRequest,
    InventoryTransactionResponse,
    InventoryTransactionListResponse
)

# Orders schemas
from app.schemas.orders_schema import (
    OrderCreateRequest,
    OrderUpdateRequest,
    OrderResponse,
    OrderListResponse
)

# Payments schemas
from app.schemas.payments_schema import (
    PaymentCreateRequest,
    PaymentUpdateRequest,
    PaymentResponse,
    PaymentListResponse
)

__all__ = [
    # Common
    "PaginationResponse",
    "ListResponse",
    "ErrorDetail",
    "ErrorResponse",
    "BaseCreateRequest",
    "BaseUpdateRequest",
    "BaseResponse",
    # Roles
    "RoleCreateRequest",
    "RoleUpdateRequest",
    "RoleResponse",
    "RoleListResponse",
    # Permissions
    "PermissionCreateRequest",
    "PermissionUpdateRequest",
    "PermissionResponse",
    "PermissionListResponse",
    # Role Permissions
    "RolePermissionCreateRequest",
    "RolePermissionUpdateRequest",
    "RolePermissionResponse",
    "RolePermissionListResponse",
    # Users
    "UserCreateRequest",
    "UserUpdateRequest",
    "UserResponse",
    "UserListResponse",
    # Pharmacist Profiles
    "PharmacistProfileCreateRequest",
    "PharmacistProfileUpdateRequest",
    "PharmacistProfileResponse",
    "PharmacistProfileListResponse",
    # Therapeutic Categories
    "TherapeuticCategoryCreateRequest",
    "TherapeuticCategoryUpdateRequest",
    "TherapeuticCategoryResponse",
    "TherapeuticCategoryListResponse",
    # Medicines
    "MedicineCreateRequest",
    "MedicineUpdateRequest",
    "MedicineResponse",
    "MedicineListResponse",
    # Medicine Compositions
    "MedicineCompositionCreateRequest",
    "MedicineCompositionUpdateRequest",
    "MedicineCompositionResponse",
    "MedicineCompositionListResponse",
    # Medicine Brands
    "MedicineBrandCreateRequest",
    "MedicineBrandUpdateRequest",
    "MedicineBrandResponse",
    "MedicineBrandListResponse",
    # Product Batches
    "ProductBatchCreateRequest",
    "ProductBatchUpdateRequest",
    "ProductBatchResponse",
    "ProductBatchListResponse",
    # Inventory Transactions
    "InventoryTransactionCreateRequest",
    "InventoryTransactionUpdateRequest",
    "InventoryTransactionResponse",
    "InventoryTransactionListResponse",
    # Orders
    "OrderCreateRequest",
    "OrderUpdateRequest",
    "OrderResponse",
    "OrderListResponse",
    # Payments
    "PaymentCreateRequest",
    "PaymentUpdateRequest",
    "PaymentResponse",
    "PaymentListResponse",
]