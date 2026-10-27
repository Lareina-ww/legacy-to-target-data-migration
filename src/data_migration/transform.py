from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re


DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
COUNTRY_ALIASES = {"UK": "GB"}


def clean_text(value: str) -> str:
    return " ".join((value or "").strip().split())


def parse_date(value: str) -> str:
    cleaned = clean_text(value)
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, date_format).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"unsupported or invalid date: {value!r}")


def parse_amount_cents(value: str) -> int:
    cleaned = clean_text(value).replace(",", "")
    try:
        amount = Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(f"invalid amount: {value!r}") from exc
    if amount < 0:
        raise ValueError(f"amount must be non-negative: {value!r}")
    return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def transform_customer(row: dict[str, str]) -> dict[str, object]:
    customer_id = clean_text(row.get("legacy_customer_id", "")).upper()
    name = clean_text(row.get("full_name", ""))
    email = clean_text(row.get("email", "")).lower()
    country = clean_text(row.get("country_code", "")).upper()
    country = COUNTRY_ALIASES.get(country, country)
    status = clean_text(row.get("status", "")).lower()

    if not customer_id:
        raise ValueError("missing customer identifier")
    if not name:
        raise ValueError("missing customer name")
    if not email or not EMAIL_PATTERN.match(email):
        raise ValueError("missing or invalid email")
    if len(country) != 2 or not country.isalpha():
        raise ValueError(f"invalid country code: {country!r}")
    if status not in {"active", "inactive"}:
        raise ValueError(f"unsupported customer status: {status!r}")

    return {
        "customer_id": customer_id,
        "customer_name": name,
        "email": email,
        "country": country,
        "created_at": parse_date(row.get("created_date", "")),
        "is_active": 1 if status == "active" else 0,
    }


def transform_transaction(
    row: dict[str, str], valid_customer_ids: set[str]
) -> dict[str, object]:
    transaction_id = clean_text(row.get("legacy_txn_id", "")).upper()
    customer_id = clean_text(row.get("legacy_customer_id", "")).upper()
    status = clean_text(row.get("status", "")).lower()

    if not transaction_id:
        raise ValueError("missing transaction identifier")
    if customer_id not in valid_customer_ids:
        raise ValueError(f"customer was not migrated: {customer_id!r}")
    if status not in {"completed", "paid", "settled"}:
        raise ValueError(f"unsupported transaction status: {status!r}")

    return {
        "transaction_id": transaction_id,
        "customer_id": customer_id,
        "transaction_date": parse_date(row.get("transaction_date", "")),
        "amount_cents": parse_amount_cents(row.get("amount_eur", "")),
        "transaction_status": "SETTLED",
    }

