from aiogram import Router

from app.routers.payment_methods.binance import router as binance_router
from app.routers.payment_methods.common import router as common_router
from app.routers.payment_methods.ewallet import router as ewallet_router
from app.routers.payment_methods.helpers.customer_notifications import (
    router as customer_notifications_router,
)
from app.routers.payment_methods.instapay import router as instapay_router
from app.routers.payment_methods.wallet import router as wallet_router


router = Router(name="payment_methods")
router.include_router(wallet_router)
router.include_router(ewallet_router)
router.include_router(instapay_router)
router.include_router(binance_router)
router.include_router(common_router)
router.include_router(customer_notifications_router)
