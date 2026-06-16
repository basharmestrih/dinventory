from supabase import Client, create_client

from app.config import settings
from app.services.catalog.products import SupabaseConfigError


class PaymentMethodUsageServiceError(RuntimeError):
    """Raised when the payment method usage record fails."""


class PaymentMethodUsageService:
    def __init__(self) -> None:
        self._client: Client | None = None

    def _get_client(self) -> Client:
        if self._client is not None:
            return self._client

        if not settings.supabase_url or not settings.supabase_key:
            raise SupabaseConfigError("Supabase credentials are missing.")

        self._client = create_client(settings.supabase_url, settings.supabase_key)
        return self._client

    async def record_usage(self, payment_method: str) -> None:
        client = self._get_client()
        payload = {
            "payment_method": payment_method,
            "usage_count": 1,
        }
        try:
            client.table(settings.supabase_payment_method_usage_table).insert(payload).execute()
        except Exception as error:
            raise PaymentMethodUsageServiceError(str(error)) from error
