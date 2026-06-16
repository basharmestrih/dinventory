import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.keyboards.wallet import get_wallet_topup_methods_keyboard
from app.services.catalog.products import SupabaseConfigError
from app.services.wallets.wallets import WalletService, WalletServiceError
from app.states.wallet import WalletTopUpState
from app.translations import t


router = Router(name="wallet_menu")
wallet_service = WalletService()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "menu:wallet")
async def wallet_handler(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await _show_wallet(callback.message, callback.from_user.username, state)


@router.message(Command("wallet"))
async def wallet_command_handler(message: Message, state: FSMContext) -> None:
    await _show_wallet(message, message.from_user.username if message.from_user else None, state)


async def _show_wallet(message: Message, username: str | None, state: FSMContext) -> None:
    if not username:
        await message.answer(t("wallet.username_missing", "ar"))
        return

    try:
        wallet = await wallet_service.ensure_wallet(username)
    except SupabaseConfigError:
        await message.answer(t("sections.supabase_not_configured", "ar"))
        return
    except WalletServiceError as error:
        await message.answer(t("wallet.load_failed_with_reason", "ar").format(reason=str(error)))
        return
    except Exception as error:
        logger.warning("Unexpected wallet load failure for @%s: %s", username, error)
        await message.answer(t("wallet.load_failed_with_reason", "ar").format(reason=str(error)))
        return

    await state.clear()
    await state.set_state(WalletTopUpState.choosing_method)
    await state.update_data(wallet_username=username)
    last_deposit = "-"
    if wallet.last_deposit_at is not None:
        try:
            last_deposit = wallet.last_deposit_at.date().isoformat()
        except Exception:
            last_deposit = "-"
    await message.answer(
        (
            "بيانات المحفظة:\n"
            f"اسم المستخدم: @{wallet.username}\n"
            f"الرصيد: {wallet.balance_egp:.2f} جنيه مصري\n"
            f"آخر إيداع: {last_deposit}\n"
            "اختر طريقة الإيداع:"
        ),
        reply_markup=get_wallet_topup_methods_keyboard("ar"),
    )
