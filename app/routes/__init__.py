"""
Routes Layer
API route handlers
"""

from fastapi import APIRouter

# Import all routers
from app.routes.roles_router import router as roles_router
from app.routes.permissions_router import router as permissions_router
from app.routes.role_permissions_router import router as role_permissions_router
from app.routes.users_router import router as users_router
from app.routes.pharmacist_profiles_router import router as pharmacist_profiles_router
from app.routes.therapeutic_categories_router import router as therapeutic_categories_router
from app.routes.medicines_router import router as medicines_router
from app.routes.medicine_compositions_router import router as medicine_compositions_router
from app.routes.medicine_brands_router import router as medicine_brands_router
from app.routes.product_batches_router import router as product_batches_router
from app.routes.inventory_transactions_router import router as inventory_transactions_router
from app.routes.orders_router import router as orders_router
from app.routes.payments_router import router as payments_router

# Import dashboard routers
from app.routes.dashboards.inventory_dashboard_router import router as inventory_dashboard_router
from app.routes.dashboards.finance_dashboard_router import router as finance_dashboard_router
from app.routes.dashboards.orders_dashboard_router import router as orders_dashboard_router
from app.routes.dashboards.sales_dashboard_router import router as sales_dashboard_router

# Import new routers (Clinic & Polyclinic)
from app.routes.doctors_router import router as doctors_router
from app.routes.appointments_router import router as appointments_router
from app.routes.polyclinic_tests_router import router as polyclinic_tests_router
from app.routes.test_bookings_router import router as test_bookings_router

# Import new routers (Pharmacy Additional)
from app.routes.product_categories_router import router as product_categories_router
from app.routes.coupons_router import router as coupons_router
from app.routes.coupon_usages_router import router as coupon_usages_router
from app.routes.delivery_settings_router import router as delivery_settings_router
from app.routes.marquee_settings_router import router as marquee_settings_router
from app.routes.delivery_slots_router import router as delivery_slots_router
from app.routes.order_items_router import router as order_items_router
from app.routes.auth_router import router as auth_router
from app.routes.prescriptions_router import router as prescriptions_router
from app.routes.insurance_enquiries_router import router as insurance_enquiries_router
from app.routes.razorpay_router import router as razorpay_router
from app.routes.addresses_router import router as addresses_router

# Create main API router
api_router = APIRouter()

# Include all routers
api_router.include_router(roles_router)
api_router.include_router(permissions_router)
api_router.include_router(role_permissions_router)
api_router.include_router(users_router)
api_router.include_router(pharmacist_profiles_router)
api_router.include_router(therapeutic_categories_router)
api_router.include_router(medicines_router)
api_router.include_router(medicine_compositions_router)
api_router.include_router(medicine_brands_router)
api_router.include_router(product_batches_router)
api_router.include_router(inventory_transactions_router)
api_router.include_router(orders_router)
api_router.include_router(payments_router)

# Include dashboard routers
api_router.include_router(inventory_dashboard_router)
api_router.include_router(finance_dashboard_router)
api_router.include_router(orders_dashboard_router)
api_router.include_router(sales_dashboard_router)

# Include new routers (Clinic & Polyclinic)
api_router.include_router(doctors_router)
api_router.include_router(appointments_router)
api_router.include_router(polyclinic_tests_router)
api_router.include_router(test_bookings_router)

# Include new routers (Pharmacy Additional)
api_router.include_router(product_categories_router)
api_router.include_router(coupons_router)
api_router.include_router(coupon_usages_router)
api_router.include_router(delivery_settings_router)
api_router.include_router(marquee_settings_router)
api_router.include_router(delivery_slots_router)
api_router.include_router(order_items_router)
api_router.include_router(auth_router)
api_router.include_router(prescriptions_router)
api_router.include_router(insurance_enquiries_router)
api_router.include_router(razorpay_router)
api_router.include_router(addresses_router)

__all__ = [
    "api_router",
    "roles_router",
    "permissions_router",
    "role_permissions_router",
    "users_router",
    "pharmacist_profiles_router",
    "therapeutic_categories_router",
    "medicines_router",
    "medicine_compositions_router",
    "medicine_brands_router",
    "product_batches_router",
    "inventory_transactions_router",
    "orders_router",
    "payments_router",
    "doctors_router",
    "appointments_router",
    "polyclinic_tests_router",
    "test_bookings_router",
    "product_categories_router",
    "coupons_router",
    "coupon_usages_router",
    "delivery_settings_router",
    "marquee_settings_router",
    "delivery_slots_router",
    "order_items_router",
    "insurance_enquiries_router",
    "razorpay_router",
    "addresses_router",
]
