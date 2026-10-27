import pytest

from data_migration.transform import (
    parse_amount_cents,
    parse_date,
    transform_customer,
    transform_transaction,
)


def test_parse_date_normalises_supported_formats() -> None:
    assert parse_date("15/01/2024") == "2024-01-15"
    assert parse_date("2024/02/05") == "2024-02-05"


def test_parse_amount_converts_euro_value_to_integer_cents() -> None:
    assert parse_amount_cents("1,250.50") == 125050


def test_customer_transformation_standardises_fields() -> None:
    result = transform_customer(
        {
            "legacy_customer_id": " c001 ",
            "full_name": " Alice   van Dijk ",
            "email": "ALICE@example.com",
            "country_code": "nl",
            "created_date": "2024-01-15",
            "status": "Active",
        }
    )
    assert result["customer_id"] == "C001"
    assert result["customer_name"] == "Alice van Dijk"
    assert result["email"] == "alice@example.com"
    assert result["country"] == "NL"


def test_transaction_rejects_unknown_customer() -> None:
    with pytest.raises(ValueError, match="customer was not migrated"):
        transform_transaction(
            {
                "legacy_txn_id": "T1",
                "legacy_customer_id": "C999",
                "transaction_date": "2024-02-01",
                "amount_eur": "10.00",
                "status": "completed",
            },
            {"C001"},
        )

