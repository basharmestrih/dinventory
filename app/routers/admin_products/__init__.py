from aiogram import Router

from app.routers.admin_products.get_product import router as get_product_router


router = Router(name="admin_products")
router.include_router(get_product_router)
