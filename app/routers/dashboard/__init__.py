from aiogram import Router

from app.routers.dashboard.exports import router as exports_router
from app.routers.dashboard.home import router as home_router
from app.routers.dashboard.notifications import router as notifications_router
from app.routers.dashboard.other import router as other_router
from app.routers.dashboard.payment_methods import router as payment_methods_router
from app.routers.dashboard.products import router as products_router


router = Router(name="dashboard")
router.include_router(home_router)
router.include_router(products_router)
router.include_router(notifications_router)
router.include_router(other_router)
router.include_router(payment_methods_router)
router.include_router(exports_router)
