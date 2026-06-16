from __future__ import annotations

import asyncio
import logging
import json
from pathlib import Path
import tempfile

from app.config import settings
from app.services.exports.dashboard_exports import DashboardExportService
from app.services.exports.exporter import build_rows_excel


logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXPORT_DIR = PROJECT_ROOT / "exports" / "drive_sheets"
DRIVE_MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
DRIVE_SCOPES = ("https://www.googleapis.com/auth/drive",)

ORDERS_HEADERS = [
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
]

WALLET_TOPUPS_HEADERS = [
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
]


class DriveSheetsToolError(RuntimeError):
    """Raised when Drive sheets export cannot be synced."""


async def sync_drive_sheets() -> None:
    export_dir = _get_export_dir()
    export_service = DashboardExportService()
    orders_rows, topups_rows = await asyncio.gather(
        export_service.fetch_orders_rows(),
        export_service.fetch_wallet_topups_rows(),
    )

    orders_file = build_rows_excel(
        orders_rows,
        ORDERS_HEADERS,
        "Orders",
        "orders",
        export_dir,
    )
    topups_file = build_rows_excel(
        topups_rows,
        WALLET_TOPUPS_HEADERS,
        "WalletTopups",
        "wallet_topups",
        export_dir,
    )

    await asyncio.to_thread(
        _upload_files_to_drive,
        {
            "Orders.xlsx": orders_file,
            "WalletTopups.xlsx": topups_file,
        },
    )


def _get_export_dir() -> Path:
    """
    Prefer project exports folder, but fall back to OS temp dir if Windows
    blocks writes (e.g. Controlled folder access / AV locks).
    """
    try:
        DEFAULT_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        probe = DEFAULT_EXPORT_DIR / ".write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return DEFAULT_EXPORT_DIR
    except Exception:
        fallback = Path(tempfile.gettempdir()) / "dinventory" / "drive_sheets"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


async def sync_drive_sheets_safely(reason: str = "") -> None:
    try:
        await sync_drive_sheets()
        logger.info("Drive sheets sync completed: reason=%s", reason or "-")
    except Exception as error:
        logger.exception("Drive sheets sync failed: reason=%s error=%s", reason or "-", error)


def schedule_drive_sheets_sync(reason: str = "") -> None:
    try:
        asyncio.get_running_loop().create_task(sync_drive_sheets_safely(reason))
    except RuntimeError:
        asyncio.run(sync_drive_sheets_safely(reason))


def _upload_files_to_drive(files: dict[str, Path]) -> None:
    drive_service = _build_drive_service()
    folder_id = settings.google_drive_dinventory_folder_id
    if not folder_id:
        raise DriveSheetsToolError("Google Drive Dinventory folder id is missing.")

    auth_mode = (settings.google_drive_auth_mode or "service_account").strip().lower()
    logger.info("Drive sheets upload started: auth_mode=%s folder_id=%s", auth_mode, folder_id)
    service_account_email: str | None = None
    if auth_mode in {"service_account", "service-account", "sa"}:
        credentials_path = _resolve_credentials_path(settings.google_service_account_json_path)
        service_account_email = _read_service_account_email(credentials_path)

    _assert_drive_folder_writable(
        drive_service=drive_service,
        folder_id=folder_id,
        service_account_email=service_account_email,
    )

    for drive_name, file_path in files.items():
        _replace_drive_file(
            drive_service=drive_service,
            folder_id=folder_id,
            drive_name=drive_name,
            file_path=file_path,
        )


def _build_drive_service():
    try:
        from googleapiclient.discovery import build
    except ImportError as error:
        raise DriveSheetsToolError(
            "Google Drive dependencies are missing. Run: pip install -r requirements.txt"
        ) from error

    auth_mode = (settings.google_drive_auth_mode or "service_account").strip().lower()
    if auth_mode in {"oauth", "user_oauth", "user-oauth"}:
        credentials = _build_oauth_credentials()
        return build("drive", "v3", credentials=credentials, cache_discovery=False)

    credentials = _build_service_account_credentials()
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def _build_service_account_credentials():
    try:
        from google.oauth2 import service_account
    except ImportError as error:
        raise DriveSheetsToolError(
            "Google Drive dependencies are missing. Run: pip install -r requirements.txt"
        ) from error

    credentials_path = _resolve_credentials_path(settings.google_service_account_json_path)
    if not credentials_path.is_file():
        raise DriveSheetsToolError(f"Google service account JSON was not found: {credentials_path}")

    return service_account.Credentials.from_service_account_file(
        str(credentials_path),
        scopes=DRIVE_SCOPES,
    )


def _build_oauth_credentials():
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
    except ImportError as error:
        raise DriveSheetsToolError(
            "Google Drive OAuth dependencies are missing. Run: pip install -r requirements.txt"
        ) from error

    client_secrets_path = _resolve_credentials_path(settings.google_oauth_client_secrets_path)
    if not client_secrets_path.is_file():
        raise DriveSheetsToolError(
            f"Google OAuth client secrets JSON was not found: {client_secrets_path}"
        )

    token_path = _resolve_credentials_path(settings.google_oauth_token_path)
    creds: Credentials | None = None

    if token_path.is_file():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), scopes=DRIVE_SCOPES)
        except Exception:
            creds = None

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        _write_oauth_token(token_path, creds)
        return creds

    if creds and creds.valid:
        return creds

    flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets_path), scopes=DRIVE_SCOPES)
    oauth_flow = (settings.google_oauth_flow or "console").strip().lower()
    if oauth_flow == "local_server":
        creds = flow.run_local_server(port=0)
    else:
        # google-auth-oauthlib added `run_console()` in newer versions.
        # Older versions can still complete an "interactive console" auth by using the local server flow
        # without opening a browser (it prints the URL instead).
        if hasattr(flow, "run_console"):
            creds = flow.run_console()
        else:
            creds = flow.run_local_server(port=0, open_browser=False)

    _write_oauth_token(token_path, creds)
    return creds


def _write_oauth_token(token_path: Path, creds) -> None:
    try:
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding="utf-8")
    except Exception as error:
        raise DriveSheetsToolError(
            f"Failed to write OAuth token file: {token_path}. Error: {error}"
        ) from error


def _assert_drive_folder_writable(*, drive_service, folder_id: str, service_account_email: str | None) -> None:
    try:
        from googleapiclient.errors import HttpError
    except ImportError as error:
        raise DriveSheetsToolError(
            "Google Drive dependencies are missing. Run: pip install -r requirements.txt"
        ) from error

    try:
        folder = (
            drive_service.files()
            .get(
                fileId=folder_id,
                fields="id,name,mimeType",
                supportsAllDrives=True,
            )
            .execute()
        )
    except HttpError as error:
        auth_mode = (settings.google_drive_auth_mode or "service_account").strip().lower()
        authed_user = _try_get_authed_user_email(drive_service)
        if auth_mode in {"oauth", "user_oauth", "user-oauth"}:
            email_hint = (
                f" Ensure the folder is shared with the OAuth user ({authed_user})."
                if authed_user
                else " Ensure the folder is shared with the Google account you authorized."
            )
        else:
            email_hint = (
                f" Share the folder with the service account ({service_account_email})."
                if service_account_email
                else ""
            )
        raise DriveSheetsToolError(
            f"Cannot access Google Drive folder id={folder_id}.{email_hint} "
            "Ensure the account has at least Editor access and, if the folder is in a Shared drive, "
            "add the account as a member."
        ) from error

    if str(folder.get("mimeType") or "") != "application/vnd.google-apps.folder":
        raise DriveSheetsToolError(
            f"GOOGLE_DRIVE_DINVENTORY_FOLDER_ID must point to a folder. "
            f"Got mimeType={folder.get('mimeType')!r} name={folder.get('name')!r} id={folder_id}."
        )
    logger.info(
        "Drive folder OK: id=%s name=%s",
        folder_id,
        (folder.get("name") or "-"),
    )


def _try_get_authed_user_email(drive_service) -> str | None:
    try:
        about = (
            drive_service.about()
            .get(fields="user(emailAddress)", supportsAllDrives=True)
            .execute()
        )
        user = about.get("user") or {}
        email = user.get("emailAddress")
        return str(email).strip() if email else None
    except Exception:
        return None


def _replace_drive_file(*, drive_service, folder_id: str, drive_name: str, file_path: Path) -> None:
    try:
        from googleapiclient.http import MediaFileUpload
        from googleapiclient.errors import HttpError
    except ImportError as error:
        raise DriveSheetsToolError(
            "Google Drive dependencies are missing. Run: pip install -r requirements.txt"
        ) from error

    media = MediaFileUpload(str(file_path), mimetype=DRIVE_MIME_XLSX, resumable=False)
    existing_file_id = _find_drive_file_id(drive_service, folder_id, drive_name)

    try:
        if existing_file_id:
            result = drive_service.files().update(
                fileId=existing_file_id,
                media_body=media,
                body={"name": drive_name, "mimeType": DRIVE_MIME_XLSX},
                fields="id,name",
                supportsAllDrives=True,
            ).execute()
            logger.info(
                "Drive file updated: folder_id=%s name=%s id=%s local=%s",
                folder_id,
                drive_name,
                result.get("id"),
                file_path.name,
            )
            return

        result = drive_service.files().create(
            body={
                "name": drive_name,
                "parents": [folder_id],
                "mimeType": DRIVE_MIME_XLSX,
            },
            media_body=media,
            fields="id,name",
            supportsAllDrives=True,
        ).execute()
        logger.info(
            "Drive file created: folder_id=%s name=%s id=%s local=%s",
            folder_id,
            drive_name,
            result.get("id"),
            file_path.name,
        )
    except HttpError as error:
        # Common service-account limitation: cannot write into "My Drive" due to no storage quota.
        if "Service Accounts do not have storage quota" in str(error) or "storageQuotaExceeded" in str(error):
            raise DriveSheetsToolError(
                "Google Drive rejected the upload because service accounts do not have storage quota in 'My Drive'. "
                "Move the target folder to a Shared drive and add the service account as a member, "
                "or switch to user OAuth (or domain-wide delegation with impersonation) for uploads."
            ) from error
        raise


def _find_drive_file_id(drive_service, folder_id: str, drive_name: str) -> str | None:
    escaped_name = drive_name.replace("\\", "\\\\").replace("'", "\\'")
    response = drive_service.files().list(
        q=f"name = '{escaped_name}' and '{folder_id}' in parents and trashed = false",
        spaces="drive",
        fields="files(id,name)",
        pageSize=10,
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
    ).execute()

    files = response.get("files") or []
    if not files:
        return None

    return str(files[0]["id"])


def _resolve_credentials_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path

    return PROJECT_ROOT / path


def _read_service_account_email(credentials_path: Path) -> str | None:
    try:
        raw = credentials_path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except Exception:
        return None

    email = data.get("client_email")
    return str(email).strip() if email else None
