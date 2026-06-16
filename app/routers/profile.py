from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.services.catalog.products import SupabaseConfigError
from app.services.users.users import UserService, UserServiceError
from app.translations import t


router = Router(name="profile")
user_service = UserService()


@router.callback_query(F.data == "menu:profile")
async def profile_handler(callback: CallbackQuery) -> None:
    await callback.answer()

    username = callback.from_user.username
    if not username:
        await callback.message.answer(t("profile.username_missing", "ar"))
        return

    try:
        user_profile = await user_service.fetch_user_by_username(username)
    except SupabaseConfigError:
        await callback.message.answer(t("sections.supabase_not_configured", "ar"))
        return
    except UserServiceError as error:
        await callback.message.answer(
            t("profile.load_failed_with_reason", "ar").format(reason=str(error))
        )
        return
    except Exception:
        await callback.message.answer(t("profile.load_failed", "ar"))
        return

    if user_profile is None:
        await callback.message.answer(
            t("profile.not_found", "ar").format(username=username)
        )
        return

    await callback.message.answer(
        t("profile.details", "ar").format(
            id=user_profile.id,
            username=user_profile.username,
            total_spent=f"{user_profile.total_spent:.2f}",
            last_spent_order=user_profile.last_spent_order or "-",
        )
    )
