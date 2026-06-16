from app.translations.messages import TRANSLATIONS


def t(key: str, lang: str = "ar") -> str:
    language_pack = TRANSLATIONS.get(lang)
    if language_pack is None:
        raise KeyError(f"Language '{lang}' is not configured.")

    current = language_pack
    for part in key.split("."):
        if part not in current:
            raise KeyError(f"Translation key '{key}' is missing for language '{lang}'.")
        current = current[part]

    if not isinstance(current, str):
        raise TypeError(f"Translation key '{key}' for language '{lang}' must resolve to a string.")

    return current
