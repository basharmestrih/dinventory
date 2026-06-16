from aiogram import Dispatcher

from app.routers.admin_products import router as admin_products_router
from app.routers.api_link import router as api_link_router
from app.routers.buy import router as buy_router
from app.routers.dashboard import router as dashboard_router
from app.routers.history import router as history_router
from app.routers.payment_methods import router as payment_methods_router
from app.routers.profile import router as profile_router
from app.routers.selected_product import router as selected_product_router
from app.routers.start import router as start_router
from app.routers.support import router as support_router
from app.routers.wallet import router as wallet_router


def register_routers(dp: Dispatcher) -> None:
    dp.include_router(start_router)
    dp.include_router(dashboard_router)
    dp.include_router(admin_products_router)
    dp.include_router(buy_router)
    dp.include_router(selected_product_router)
    dp.include_router(payment_methods_router)
    dp.include_router(profile_router)
    dp.include_router(history_router)
    dp.include_router(wallet_router)
    dp.include_router(support_router)
    dp.include_router(api_link_router)
