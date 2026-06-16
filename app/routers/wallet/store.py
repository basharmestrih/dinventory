from decimal import Decimal

from app.models.wallet_topup import WalletTopUpRequest
from app.services.wallets.topups import WalletTopUpService

wallet_topup_service = WalletTopUpService()


async def create_wallet_topup_request(
    *,
    username: str,
    amount: Decimal,
    currency: str,
    payment_method: str,
    transaction_id: str,
    payment_proof_file_id: str = "",
    payment_proof_type: str = "",
    customer_name: str,
    customer_username: str,
    customer_telegram_id: int | None,
) -> WalletTopUpRequest:
    return await wallet_topup_service.create_topup(
        username=username,
        amount=amount,
        currency=currency,
        payment_method=payment_method,
        transaction_id=transaction_id,
        payment_proof_file_id=payment_proof_file_id,
        payment_proof_type=payment_proof_type,
        customer_name=customer_name,
        customer_username=customer_username,
        customer_telegram_id=customer_telegram_id,
    )


async def get_wallet_topup_request(request_id: str) -> WalletTopUpRequest | None:
    return await wallet_topup_service.fetch_topup_by_id(request_id)


async def update_wallet_topup_transaction_id(request_id: str, transaction_id: str) -> WalletTopUpRequest | None:
    return await wallet_topup_service.update_transaction_id(request_id, transaction_id)


async def update_wallet_topup_status(request_id: str, status: str) -> WalletTopUpRequest | None:
    return await wallet_topup_service.update_status(request_id, status)
