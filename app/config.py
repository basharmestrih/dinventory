from dataclasses import dataclass
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(slots=True)
class Settings:
    bot_token: str
    zeno_bank_api_key: str | None = None
    fawaterk_api_key: str | None = None
    binance_id: str | None = None
    support_username: str | None = None
    support_whatsapp_phone: str | None = None
    supabase_url: str | None = None
    supabase_key: str | None = None
    supabase_products_table: str = "products"
    supabase_orders_table: str = "Orders"
    supabase_product_revenue_table: str = "ProductRevenueTable"
    supabase_payment_method_usage_table: str = "PaymenyMethodUsage"
    supabase_daily_revenue_table: str = "DailyRevenueTable"
    supabase_users_table: str = "Users"
    supabase_wallet_table: str = "Wallet"
    supabase_wallet_topups_table: str = "WalletTopups"
    supabase_users_telegram_id_column: str = "telegram_id"
    admin_user_ids: tuple[int, ...] = ()
    admin_group_chat_id: int | None = None
    instapay_phone_number: str | None = None
    zeno_webhook_enabled: bool = False
    zeno_webhook_host: str = "0.0.0.0"
    zeno_webhook_port: int = 8080
    default_language: str = "ar"
    google_drive_auth_mode: str = "service_account"  # service_account | oauth
    google_service_account_json_path: str = "onyx-sequence-495923-u6-c721f52f1910.json"
    google_drive_dinventory_folder_id: str = "1hW-tFkGFQesB86oo-Plv4Oz1qw-7ZGZh"
    google_oauth_client_secrets_path: str = (
        "client_secret_787218201261-is11fuldvh3shs8a05cq53dvg9dtu9eq.apps.googleusercontent.com.json"
    )
    google_oauth_token_path: str = "google_oauth_token.json"
    google_oauth_flow: str = "console"  # console | local_server


def _get_bot_token() -> str:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise ValueError("BOT_TOKEN is missing. Add it to your .env file.")
    return token


def _get_admin_user_ids() -> tuple[int, ...]:
    raw_value = os.getenv("ADMIN_USER_IDS", "").strip()
    if not raw_value:
        return ()

    user_ids: list[int] = []
    for item in raw_value.split(","):
        value = item.strip()
        if value:
            user_ids.append(int(value))

    return tuple(user_ids)


def _get_admin_group_chat_id() -> int | None:
    raw_value = os.getenv("ADMIN_GROUP_CHAT_ID", "").strip()
    if not raw_value:
        return None

    return int(raw_value)


def _get_bool(name: str, default: bool = False) -> bool:
    raw_value = os.getenv(name, "").strip().lower()
    if not raw_value:
        return default

    return raw_value in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return default

    return int(raw_value)


settings = Settings(
    bot_token=_get_bot_token(),
    zeno_bank_api_key=os.getenv("ZENO_BANK_API_KEY", "").strip() or None,
    fawaterk_api_key=os.getenv("FAWATERK_API_KEY", "").strip() or None,
    binance_id=os.getenv("BINANCE_ID", "").strip() or None,
    support_username=os.getenv("SUPPORT_USERNAME", "").strip() or None,
    support_whatsapp_phone=os.getenv("SUPPORT_WHATSAPP_PHONE", "").strip() or None,
    supabase_url=os.getenv("SUPABASE_URL", "").strip() or None,
    supabase_key=os.getenv("SUPABASE_KEY", "").strip() or None,
    supabase_products_table=os.getenv("SUPABASE_PRODUCTS_TABLE", "products").strip() or "products",
    supabase_orders_table=os.getenv("SUPABASE_ORDERS_TABLE", "Orders").strip() or "Orders",
    supabase_product_revenue_table=os.getenv("SUPABASE_PRODUCT_REVENUE_TABLE", "ProductRevenueTable").strip() or "ProductRevenueTable",
    supabase_payment_method_usage_table=os.getenv("SUPABASE_PAYMENT_METHOD_USAGE_TABLE", "PaymentMethodUsage").strip() or "PaymenyMethodUsage",
    supabase_daily_revenue_table=os.getenv("SUPABASE_DAILY_REVENUE_TABLE", "DailyRevenueTable").strip() or "DailyRevenueTable",
    supabase_users_table=os.getenv("SUPABASE_USERS_TABLE", "Users").strip() or "Users",
    supabase_wallet_table=os.getenv("SUPABASE_WALLET_TABLE", "Wallet").strip() or "Wallet",
    supabase_wallet_topups_table=os.getenv("SUPABASE_WALLET_TOPUPS_TABLE", "WalletTopups").strip() or "WalletTopups",
    supabase_users_telegram_id_column=os.getenv("SUPABASE_USERS_TELEGRAM_ID_COLUMN", "telegram_id").strip() or "telegram_id",
    admin_user_ids=_get_admin_user_ids(),
    admin_group_chat_id=_get_admin_group_chat_id(),
    instapay_phone_number=os.getenv("INSTAPAY_PHONE_NUMBER", "").strip() or None,
    zeno_webhook_enabled=_get_bool("ZENO_WEBHOOK_ENABLED"),
    zeno_webhook_host=os.getenv("ZENO_WEBHOOK_HOST", "0.0.0.0").strip() or "0.0.0.0",
    zeno_webhook_port=_get_int("ZENO_WEBHOOK_PORT", 8080),
    google_drive_auth_mode=(
        os.getenv("GOOGLE_DRIVE_AUTH_MODE", "service_account").strip().lower() or "service_account"
    ),
    google_service_account_json_path=(
        os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_PATH", "onyx-sequence-495923-u6-c721f52f1910.json").strip()
        or "onyx-sequence-495923-u6-c721f52f1910.json"
    ),
    google_drive_dinventory_folder_id=(
        os.getenv("GOOGLE_DRIVE_DINVENTORY_FOLDER_ID", "1hW-tFkGFQesB86oo-Plv4Oz1qw-7ZGZh").strip()
        or "1hW-tFkGFQesB86oo-Plv4Oz1qw-7ZGZh"
    ),
    google_oauth_client_secrets_path=(
        os.getenv(
            "GOOGLE_OAUTH_CLIENT_SECRETS_PATH",
            "client_secret_787218201261-is11fuldvh3shs8a05cq53dvg9dtu9eq.apps.googleusercontent.com.json",
        ).strip()
        or "client_secret_787218201261-is11fuldvh3shs8a05cq53dvg9dtu9eq.apps.googleusercontent.com.json"
    ),
    google_oauth_token_path=(
        os.getenv("GOOGLE_OAUTH_TOKEN_PATH", "google_oauth_token.json").strip()
        or "google_oauth_token.json"
    ),
    google_oauth_flow=(os.getenv("GOOGLE_OAUTH_FLOW", "console").strip().lower() or "console"),
)
