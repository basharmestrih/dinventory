ADOBE_PRODUCT_KEYWORD = "adobe creative cloud"

ADOBE_DURATION_OPTIONS = (
    "1_month",
    "2_months",
    "6_months",
    "12_months",
)

ADOBE_DURATION_LABELS = {
    "1_month": "شهر واحد\n25 جنيه مصري",
    "2_months": "شهرين\n40 جنيه مصري",
    "6_months": "6 أشهر\n100 جنيه مصري",
    "12_months": "12 شهر\n350 جنيه مصري",
}

ADOBE_DURATION_PRICES = {
    "1_month": "25",
    "2_months": "40",
    "6_months": "100",
    "12_months": "350",
}

ADOBE_ACTION_EXTEND = "extend"
ADOBE_ACTION_ASSIGN = "assign"

ADOBE_ACTION_LABELS = {
    ADOBE_ACTION_EXTEND: "تمديد",
    ADOBE_ACTION_ASSIGN: "اشتراك جديد",
}


def is_adobe_product(title: object) -> bool:
    return ADOBE_PRODUCT_KEYWORD in str(title or "").strip().lower()


def get_duration_label(key: str) -> str:
    return ADOBE_DURATION_LABELS.get(key, key)


def get_duration_price(key: str) -> str | None:
    return ADOBE_DURATION_PRICES.get(key)


def get_action_label(action: str | None) -> str | None:
    if not action:
        return None

    return ADOBE_ACTION_LABELS.get(action, action)
