from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.models.product import Product
from app.services.payments.payment_methods import get_payment_methods_status
from app.translations import t


def get_dashboard_keyboard(lang: str = "ar") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("dashboard.buttons.products_management", lang),
                    callback_data="dashboard:section:products",
                ),
                InlineKeyboardButton(
                    text=t("dashboard.buttons.broadcast_management", lang),
                    callback_data="dashboard:section:notifications",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t("dashboard.buttons.payment_methods", lang),
                    callback_data="dashboard:section:payment_methods",
                ),
                InlineKeyboardButton(
                    text=t("dashboard.buttons.sales_reports", lang),
                    callback_data="dashboard:section:sales",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("dashboard.buttons.other", lang),
                    callback_data="dashboard:section:other",
                )
            ],
            [InlineKeyboardButton(text=t("buttons.back_to_menu", lang), callback_data="menu:home")],
        ]
    )


def get_dashboard_section_keyboard(section: str, lang: str = "ar") -> InlineKeyboardMarkup:
    section_rows: dict[str, list[list[InlineKeyboardButton]]] = {
        "products": [
            [InlineKeyboardButton(text=t("dashboard.buttons.add_product", lang), callback_data="dashboard:add")],
            [InlineKeyboardButton(text=t("dashboard.buttons.edit_product", lang), callback_data="dashboard:edit")],
            [InlineKeyboardButton(text=t("dashboard.buttons.delete_product", lang), callback_data="dashboard:delete")],
            [InlineKeyboardButton(text="الحصول على منتج", callback_data="admin_products:list")],
        ],
        "notifications": [
            [
                InlineKeyboardButton(
                    text=t("dashboard.buttons.broadcast_notification", lang),
                    callback_data="dashboard:broadcast",
                )
            ],
        ],
        "payment_methods": _build_payment_methods_rows(lang),
        "sales": [
            [InlineKeyboardButton(text=t("dashboard.buttons.export_products", lang), callback_data="dashboard:export")],
            [
                InlineKeyboardButton(
                    text=t("dashboard.buttons.export_product_revenue", lang),
                    callback_data="dashboard:export:product_revenue",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("dashboard.buttons.export_payment_method_usage", lang),
                    callback_data="dashboard:export:payment_method_usage",
                )
            ],
            [InlineKeyboardButton(text=t("dashboard.buttons.export_users", lang), callback_data="dashboard:export:users")],
            [InlineKeyboardButton(text=t("dashboard.buttons.export_orders", lang), callback_data="dashboard:export:orders")],
            [InlineKeyboardButton(text=t("dashboard.buttons.export_wallet_topups", lang), callback_data="dashboard:export:wallet_topups")],
        ],
        "other": [
            [
                InlineKeyboardButton(
                    text=t("dashboard.buttons.adjust_wallet_balance", lang),
                    callback_data="dashboard:other:adjust_wallet_balance",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("dashboard.buttons.change_egp_exchange_rate", lang),
                    callback_data="dashboard:other:change_egp_exchange_rate",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("dashboard.buttons.set_special_products", lang),
                    callback_data="dashboard:other:set_special_products",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("dashboard.buttons.change_instapay_phone_number", lang),
                    callback_data="dashboard:other:change_instapay_phone_number",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("dashboard.buttons.change_binance_id", lang),
                    callback_data="dashboard:other:change_binance_id",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("dashboard.buttons.change_support_username", lang),
                    callback_data="dashboard:other:change_support_username",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("dashboard.buttons.change_support_whatsapp_phone", lang),
                    callback_data="dashboard:other:change_support_whatsapp_phone",
                )
            ],
            # Review-message editing buttons temporarily disabled.
            # [
            #     InlineKeyboardButton(
            #         text=t("dashboard.buttons.change_order_approved_message", lang),
            #         callback_data="dashboard:other:review_message:order_approved",
            #     )
            # ],
            # [
            #     InlineKeyboardButton(
            #         text=t("dashboard.buttons.change_order_rejected_message", lang),
            #         callback_data="dashboard:other:review_message:order_rejected",
            #     )
            # ],
            # [
            #     InlineKeyboardButton(
            #         text=t("dashboard.buttons.change_wallet_topup_approved_message", lang),
            #         callback_data="dashboard:other:review_message:wallet_topup_approved",
            #     )
            # ],
            # [
            #     InlineKeyboardButton(
            #         text=t("dashboard.buttons.change_wallet_topup_rejected_message", lang),
            #         callback_data="dashboard:other:review_message:wallet_topup_rejected",
            #     )
            # ],
        ],
    }
    rows = section_rows[section][:]
    rows.append([InlineKeyboardButton(text=t("buttons.back_to_dashboard", lang), callback_data="dashboard:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_account_type_keyboard(lang: str = "ar") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="حساب شخصي",
                    callback_data="dashboard:add:account_type:personal",
                ),
                InlineKeyboardButton(
                    text="حساب جديد",
                    callback_data="dashboard:add:account_type:new",
                ),
            ]
        ]
    )


def get_dashboard_products_keyboard(
    products: list[Product],
    action: str,
    lang: str = "ar",
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{product.title} ({product.quantity})",
                callback_data=f"dashboard:{action}:{product.id}",
            )
        ]
        for product in products
    ]
    rows.append([InlineKeyboardButton(text=t("buttons.back_to_dashboard", lang), callback_data="dashboard:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_product_edit_fields_keyboard(lang: str = "ar", *, can_edit_credentials: bool = False) -> InlineKeyboardMarkup:
    rows = [
            [
                InlineKeyboardButton(
                    text=t("dashboard.buttons.edit_name", lang),
                    callback_data="dashboard:edit_field:title",
                ),
                InlineKeyboardButton(
                    text=t("dashboard.buttons.edit_description", lang),
                    callback_data="dashboard:edit_field:description",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t("dashboard.buttons.edit_quantity", lang),
                    callback_data="dashboard:edit_field:quantity",
                ),
                InlineKeyboardButton(
                    text=t("dashboard.buttons.edit_supplier_price", lang),
                    callback_data="dashboard:edit_field:supplier_price",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t("dashboard.buttons.edit_price", lang),
                    callback_data="dashboard:edit_field:price",
                ),
            ],
        ]

    if can_edit_credentials:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t("dashboard.buttons.edit_credentials", lang),
                    callback_data="dashboard:edit_field:credentials",
                ),
            ]
        )

    rows.extend(
        [
            [
                InlineKeyboardButton(
                    text=t("dashboard.buttons.finish_editing", lang),
                    callback_data="dashboard:edit_field:finish",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t("buttons.back_to_dashboard", lang),
                    callback_data="dashboard:home",
                ),
            ],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _build_payment_methods_rows(lang: str) -> list[list[InlineKeyboardButton]]:
    statuses = get_payment_methods_status()
    methods = (
        ("wallet", "dashboard.buttons.wallet_method"),
        ("ewallet", "dashboard.buttons.e_wallet"),
        ("fawry", "dashboard.buttons.fawry_method"),
        ("instapay", "dashboard.buttons.instapay_method"),
        ("binance", "dashboard.buttons.binance_method"),
    )
    rows: list[list[InlineKeyboardButton]] = []

    for method, translation_key in methods:
        status_key = "dashboard.buttons.enabled" if statuses.get(method, False) else "dashboard.buttons.disabled"
        status_icon_key = (
            "dashboard.buttons.enabled_icon"
            if statuses.get(method, False)
            else "dashboard.buttons.disabled_icon"
        )
        rows.append(
            [
                InlineKeyboardButton(
                    text=(
                        f"{t(translation_key, lang)}"
                        f" | {t('dashboard.buttons.status_label', lang)}: "
                        f"{t(status_icon_key, lang)} {t(status_key, lang)}"
                    ),
                    callback_data=f"dashboard:payment_methods:noop:{method}",
                )
            ]
        )
        rows.append(
            [
                InlineKeyboardButton(
                    text=t("dashboard.buttons.enable", lang),
                    callback_data=f"dashboard:payment_methods:enable:{method}",
                ),
                InlineKeyboardButton(
                    text=t("dashboard.buttons.disable", lang),
                    callback_data=f"dashboard:payment_methods:disable:{method}",
                ),
            ]
        )

    return rows


def get_wallet_users_keyboard(users: list[tuple[str, str]], lang: str = "ar") -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"@{username} | {balance}",
                callback_data=f"dashboard:other:wallet_user:{username}",
            )
        ]
        for username, balance in users
    ]
    rows.append([InlineKeyboardButton(text=t("buttons.back_to_dashboard", lang), callback_data="dashboard:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_wallet_balance_action_keyboard(username: str, lang: str = "ar") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("dashboard.buttons.add_balance", lang),
                    callback_data=f"dashboard:other:wallet_balance:add:{username}",
                ),
                InlineKeyboardButton(
                    text=t("dashboard.buttons.cut_balance", lang),
                    callback_data=f"dashboard:other:wallet_balance:cut:{username}",
                ),
            ],
            [InlineKeyboardButton(text=t("buttons.back_to_dashboard", lang), callback_data="dashboard:home")],
        ]
    )
