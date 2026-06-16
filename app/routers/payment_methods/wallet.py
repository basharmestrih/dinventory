from decimal import Decimal

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.routers.payment_methods.admin_notifications import notify_admins_about_order
from app.routers.payment_methods.helpers import (
    notify_customer_about_processed_order,
    process_paid_order,
)
from app.services.orders.orders import OrderService, OrderServiceError
from app.services.payments.payment_methods import PAYMENT_METHOD_WALLET, is_payment_method_enabled
from app.services.catalog.products import SupabaseConfigError
from app.services.wallets.wallets import WalletService, WalletServiceError
from app.states.purchase import PurchaseState
from app.translations import t


router = Router(name="payment_wallet")
order_service = OrderService()
wallet_service = WalletService()


@router.callback_query(F.data == "payment:wallet", PurchaseState.choosing_payment_method)
async def wallet_handler(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_payment_method_enabled(PAYMENT_METHOD_WALLET):
        await callback.answer()
        await callback.message.answer(t("purchase.payment_method_disabled", "ar"))
        return

    await callback.answer()

    username = callback.from_user.username
    if not username:
        await callback.message.answer(t("wallet.username_missing", "ar"))
        return

    data = await state.get_data()
    total = Decimal(str(data.get("total") or "0"))

    if data.get("uses_manual_activation_emails") and not data.get("email"):
        await callback.message.answer(t("purchase.ask_assignment_email", "ar"))
        await state.set_state(PurchaseState.waiting_for_assignment_email)
        return

    try:
        wallet = await wallet_service.ensure_wallet(username)
    except SupabaseConfigError:
        await callback.message.answer(t("sections.supabase_not_configured", "ar"))
        return
    except WalletServiceError as error:
        await callback.message.answer(str(error))
        return

    if wallet.balance_egp < total:
        await callback.message.answer(
            "رصيد المحفظة غير كاف لإتمام الطلب.\n"
            f"الإجمالي المطلوب: {total:.2f} جنيه مصري\n"
            f"الرصيد الحالي: {wallet.balance_egp:.2f} جنيه مصري"
        )
        return

    try:
        await wallet_service.deduct_purchase_amount(username, total)
    except SupabaseConfigError:
        await callback.message.answer(t("sections.supabase_not_configured", "ar"))
        return
    except WalletServiceError as error:
        await callback.message.answer(str(error))
        return

    created_order = None
    try:
        await state.update_data(payment_method="Wallet")
        created_order = await order_service.create_order(
            await state.get_data(),
            transaction_id=None,
            customer=callback.from_user,
        )
        await callback.message.answer(
            "جاري معالجة الطلب"
        )
        updated_order, product, error_message, order_action_label = await process_paid_order(created_order)
    except SupabaseConfigError:
        await wallet_service.apply_topup(username, total)
        await callback.message.answer(t("sections.supabase_not_configured", "ar"))
        return
    except (OrderServiceError, WalletServiceError) as error:
        await wallet_service.apply_topup(username, total)
        await callback.message.answer(str(error))
        return
    except Exception:
        await wallet_service.apply_topup(username, total)
        await callback.message.answer(t("purchase.order_create_failed", "ar"))
        return

    if updated_order is None:
        await wallet_service.apply_topup(username, total)
        if created_order is not None:
            try:
                await order_service.update_order_status(created_order.id, "Rejected")
            except Exception:
                pass
        await callback.message.answer(error_message or t("purchase.order_create_failed", "ar"))
        return

    if updated_order.status == "ActivationPending" and callback.message is not None:
        try:
            await notify_admins_about_order(callback.message, updated_order)
        except Exception:
            pass

    await state.clear()
    await notify_customer_about_processed_order(
        context=callback,
        updated_order=updated_order,
        product=product,
        order_action_label=order_action_label,
    )
