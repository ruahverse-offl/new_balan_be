"""
Routes Layer
API route handlers
"""

from fastapi import APIRouter

# Import all routers
from app.routes.roles_router import router as roles_router
from app.routes.users_router import router as users_router
from app.routes.medicine_categories_router import router as medicine_categories_router
from app.routes.brands_router import router as brands_router
from app.routes.medicines_router import router as medicines_router
from app.routes.medicine_brands_router import router as medicine_brands_router
from app.routes.orders_router import router as orders_router
from app.routes.payments_router import router as payments_router

# Import new routers (Clinic & Polyclinic)
from app.routes.doctors_router import router as doctors_router
from app.routes.appointments_router import router as appointments_router
from app.routes.polyclinic_tests_router import router as polyclinic_tests_router
from app.routes.test_bookings_router import router as test_bookings_router

# Import new routers (Pharmacy Additional)
from app.routes.coupons_router import router as coupons_router
from app.routes.coupon_usages_router import router as coupon_usages_router
from app.routes.delivery_settings_router import router as delivery_settings_router
from app.routes.marquee_settings_router import router as marquee_settings_router
from app.routes.order_items_router import router as order_items_router
from app.routes.auth_router import router as auth_router
from app.routes.razorpay_router import router as razorpay_router
from app.routes.addresses_router import router as addresses_router
from app.routes.upload_router import router as upload_router
from app.routes.inventory_router import router as inventory_router
from app.routes.modules_router import router as modules_router
from app.routes.rbac_matrix_router import router as rbac_matrix_router
from app.routes.me_router import router as me_router

# Import notification routers
from app.routes.notification_master_router import router as notification_master_router
from app.routes.notification_settings_router import router as notification_settings_router
from app.routes.notification_logs_router import router as notification_logs_router

# Create main API router
api_router = APIRouter()

# Include all routers
api_router.include_router(me_router)
api_router.include_router(roles_router)
api_router.include_router(users_router)
api_router.include_router(medicine_categories_router)
api_router.include_router(brands_router)
api_router.include_router(medicines_router)
api_router.include_router(medicine_brands_router)
api_router.include_router(orders_router)
api_router.include_router(payments_router)

# Include new routers (Clinic & Polyclinic)
api_router.include_router(doctors_router)
api_router.include_router(appointments_router)
api_router.include_router(polyclinic_tests_router)
api_router.include_router(test_bookings_router)

# Include new routers (Pharmacy Additional)
api_router.include_router(coupons_router)
api_router.include_router(coupon_usages_router)
api_router.include_router(delivery_settings_router)
api_router.include_router(marquee_settings_router)
api_router.include_router(order_items_router)
api_router.include_router(auth_router)
api_router.include_router(razorpay_router)
api_router.include_router(addresses_router)
api_router.include_router(upload_router)
api_router.include_router(inventory_router)
api_router.include_router(modules_router)
api_router.include_router(rbac_matrix_router)

# Include notification routers
api_router.include_router(notification_master_router)
api_router.include_router(notification_settings_router)
api_router.include_router(notification_logs_router)

__all__ = [
    "api_router",
    "roles_router",
    "users_router",
    "medicine_categories_router",
    "brands_router",
    "medicines_router",
    "medicine_brands_router",
    "orders_router",
    "payments_router",
    "doctors_router",
    "appointments_router",
    "polyclinic_tests_router",
    "test_bookings_router",
    "coupons_router",
    "coupon_usages_router",
    "delivery_settings_router",
    "marquee_settings_router",
    "order_items_router",
    "razorpay_router",
    "addresses_router",
    "upload_router",
    "inventory_router",
    "modules_router",
    "rbac_matrix_router",
    "notification_master_router",
    "notification_settings_router",
    "notification_logs_router",
]
