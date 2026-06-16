from io import BytesIO

import qrcode


def split_name(full_name: str) -> tuple[str, str]:
    parts = [part for part in full_name.split() if part]
    if not parts:
        return "Customer", "User"
    if len(parts) == 1:
        return parts[0], parts[0]
    return parts[0], " ".join(parts[1:])


def build_qr_code_image(payload: str) -> bytes:
    qr_image = qrcode.make(payload)
    buffer = BytesIO()
    qr_image.save(buffer, format="PNG")
    return buffer.getvalue()


def is_valid_phone(phone: str) -> bool:
    normalized = phone.replace(" ", "").replace("-", "")
    if not normalized.isdigit():
        return False
    return normalized.startswith("0") and len(normalized) == 11
