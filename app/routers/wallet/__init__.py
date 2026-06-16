from aiogram import Router

from app.routers.wallet.binance import router as binance_router
from app.routers.wallet.common import router as common_router
from app.routers.wallet.ewallet import router as ewallet_router
from app.routers.wallet.instapay import router as instapay_router
from app.routers.wallet.menu import router as menu_router


router = Router(name="wallet")
router.include_router(menu_router)
router.include_router(ewallet_router)
router.include_router(instapay_router)
router.include_router(binance_router)
router.include_router(common_router)
