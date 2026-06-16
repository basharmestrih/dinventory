from aiogram import F, Router
from aiogram.types import BufferedInputFile, CallbackQuery

from app.routers.dashboard.shared import EXPORT_DIR, dashboard_export_service, is_admin, product_service
from app.services.exports.dashboard_exports import DashboardExportServiceError
from app.services.exports.exporter import build_products_excel, build_rows_excel
from app.services.catalog.products import SupabaseConfigError
from app.translations import t


router = Router(name="dashboard_exports")


@router.callback_query(F.data == "dashboard:export")
async def dashboard_export_handler(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(t("dashboard.messages.access_denied", "ar"), show_alert=True)
        return

    try:
        products = await product_service.fetch_products()
    except SupabaseConfigError:
        await callback.message.answer(t("sections.supabase_not_configured", "ar"))
        return
    except Exception:
        await callback.message.answer(t("dashboard.messages.export_failed", "ar"))
        return

    if not products:
        await callback.message.answer(t("sections.no_products", "ar"))
        return

    file_path = build_products_excel(products, EXPORT_DIR)
    file_bytes = file_path.read_bytes()

    await callback.answer()
    await callback.message.answer_document(
        BufferedInputFile(file_bytes, filename="products.xlsx"),
        caption=t("dashboard.messages.export_ready", "ar"),
    )

    file_path.unlink(missing_ok=True)


@router.callback_query(F.data == "dashboard:export:product_revenue")
async def dashboard_export_product_revenue_handler(callback: CallbackQuery) -> None:
    await export_dashboard_rows(
        callback=callback,
        fetcher=dashboard_export_service.fetch_product_revenue_rows,
        headers=["id", "product_title", "total_revenue", "total_sold_count", "created_at"],
        file_name="product_revenue.xlsx",
        file_prefix="product_revenue",
        sheet_name="ProductRevenue",
        empty_message=t("dashboard.messages.no_product_revenue", "ar"),
    )


@router.callback_query(F.data == "dashboard:export:payment_method_usage")
async def dashboard_export_payment_method_usage_handler(callback: CallbackQuery) -> None:
    await export_dashboard_rows(
        callback=callback,
        fetcher=dashboard_export_service.fetch_payment_method_usage_rows,
        headers=["id", "payment_method", "usage_count", "created_at"],
        file_name="payment_method_usage.xlsx",
        file_prefix="payment_method_usage",
        sheet_name="PaymentMethodUsage",
        empty_message=t("dashboard.messages.no_payment_method_usage", "ar"),
    )



@router.callback_query(F.data == "dashboard:export:users")
async def dashboard_export_users_handler(callback: CallbackQuery) -> None:
    await export_dashboard_rows(
        callback=callback,
        fetcher=dashboard_export_service.fetch_users_rows,
        headers=["id", "username", "total_spent", "last_spent_order", "created_at"],
        file_name="users.xlsx",
        file_prefix="users",
        sheet_name="Users",
        empty_message=t("dashboard.messages.no_users", "ar"),
    )


@router.callback_query(F.data == "dashboard:export:orders")
async def dashboard_export_orders_handler(callback: CallbackQuery) -> None:
    await export_dashboard_rows(
        callback=callback,
        fetcher=dashboard_export_service.fetch_orders_rows,
        headers=[
            "id",
            "product_id",
            "product_title",
            "product_description",
            "unit_price",
            "quantity",
            "total",
            "payment_method",
            "transaction_id",
            "status",
            "customer_name",
            "customer_username",
            "customer_telegram_id",
            "created_at",
        ],
        file_name="orders.xlsx",
        file_prefix="orders",
        sheet_name="Orders",
        empty_message=t("dashboard.messages.no_orders", "ar"),
    )


@router.callback_query(F.data == "dashboard:export:wallet_topups")
async def dashboard_export_wallet_topups_handler(callback: CallbackQuery) -> None:
    await export_dashboard_rows(
        callback=callback,
        fetcher=dashboard_export_service.fetch_wallet_topups_rows,
        headers=[
            "id",
            "username",
            "amount",
            "currency",
            "payment_method",
            "transaction_id",
            "payment_proof_file_id",
            "payment_proof_type",
            "customer_name",
            "customer_username",
            "customer_telegram_id",
            "status",
            "created_at",
        ],
        file_name="wallet_topups.xlsx",
        file_prefix="wallet_topups",
        sheet_name="WalletTopups",
        empty_message=t("dashboard.messages.no_wallet_topups", "ar"),
    )


async def export_dashboard_rows(
    callback: CallbackQuery,
    fetcher,
    headers: list[str],
    file_name: str,
    file_prefix: str,
    sheet_name: str,
    empty_message: str,
) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(t("dashboard.messages.access_denied", "ar"), show_alert=True)
        return

    try:
        rows = await fetcher()
    except SupabaseConfigError:
        await callback.message.answer(t("sections.supabase_not_configured", "ar"))
        return
    except DashboardExportServiceError as error:
        await callback.message.answer(
            t("dashboard.messages.export_failed_with_reason", "ar").format(reason=str(error))
        )
        return
    except Exception:
        await callback.message.answer(t("dashboard.messages.export_failed", "ar"))
        return

    if not rows:
        await callback.message.answer(empty_message)
        return

    file_path = build_rows_excel(
        rows=rows,
        headers=headers,
        sheet_name=sheet_name,
        file_prefix=file_prefix,
        export_dir=EXPORT_DIR,
    )
    file_bytes = file_path.read_bytes()

    await callback.answer()
    await callback.message.answer_document(
        BufferedInputFile(file_bytes, filename=file_name),
        caption=t("dashboard.messages.export_ready", "ar"),
    )

    file_path.unlink(missing_ok=True)
