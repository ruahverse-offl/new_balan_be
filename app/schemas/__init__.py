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

# Users schemas
from app.schemas.users_schema import (
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse,
    UserListResponse
)

# Medicine categories + shared brands
from app.schemas.medicine_categories_schema import (
    MedicineCategoryCreateRequest,
    MedicineCategoryUpdateRequest,
    MedicineCategoryResponse,
    MedicineCategoryListResponse,
)
from app.schemas.brands_schema import (
    BrandCreateRequest,
    BrandUpdateRequest,
    BrandResponse,
    BrandListResponse,
)

# Medicines schemas
from app.schemas.medicines_schema import (
    MedicineCreateRequest,
    MedicineUpdateRequest,
    MedicineResponse,
    MedicineListResponse
)

# Medicine Brands schemas
from app.schemas.medicine_brands_schema import (
    MedicineBrandCreateRequest,
    MedicineBrandUpdateRequest,
    MedicineBrandResponse,
    MedicineBrandListResponse
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

# Notification schemas
from app.schemas.notification_master_schema import (
    NotificationMasterCreateRequest,
    NotificationMasterUpdateRequest,
    NotificationMasterResponse,
    NotificationMasterListResponse,
)
from app.schemas.notification_settings_schema import (
    MeNotificationSettingRegisterRequest,
    MeNotificationSettingRevokeRequest,
    MeNotificationSettingRevokeResponse,
    NotificationSettingCreateRequest,
    NotificationSettingUpdateRequest,
    NotificationSettingResponse,
    NotificationSettingListResponse,
)
from app.schemas.notification_logs_schema import (
    NotificationLogCreateRequest,
    NotificationLogUpdateRequest,
    NotificationLogResponse,
    NotificationLogListResponse,
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
    # Users
    "UserCreateRequest",
    "UserUpdateRequest",
    "UserResponse",
    "UserListResponse",
    # Medicine categories & brands
    "MedicineCategoryCreateRequest",
    "MedicineCategoryUpdateRequest",
    "MedicineCategoryResponse",
    "MedicineCategoryListResponse",
    "BrandCreateRequest",
    "BrandUpdateRequest",
    "BrandResponse",
    "BrandListResponse",
    # Medicines
    "MedicineCreateRequest",
    "MedicineUpdateRequest",
    "MedicineResponse",
    "MedicineListResponse",
    # Medicine Brands
    "MedicineBrandCreateRequest",
    "MedicineBrandUpdateRequest",
    "MedicineBrandResponse",
    "MedicineBrandListResponse",
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
    # Notifications
    "NotificationMasterCreateRequest",
    "NotificationMasterUpdateRequest",
    "NotificationMasterResponse",
    "NotificationMasterListResponse",
    "MeNotificationSettingRegisterRequest",
    "MeNotificationSettingRevokeRequest",
    "MeNotificationSettingRevokeResponse",
    "NotificationSettingCreateRequest",
    "NotificationSettingUpdateRequest",
    "NotificationSettingResponse",
    "NotificationSettingListResponse",
    "NotificationLogCreateRequest",
    "NotificationLogUpdateRequest",
    "NotificationLogResponse",
    "NotificationLogListResponse",
]