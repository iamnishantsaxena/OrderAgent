"""
Unit tests for the regex/heuristic tools in src/tools.py.
Pure functions, no Ollama required: run with `pytest tests/test_tools.py`.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.tools import (
    extract_customer_info, extract_items, extract_addresses,
    extract_dates, extract_financial_info, validate_order_data,
    calculate_confidence, normalize_date, is_valid_date
)


def run(t, **kwargs):
    return json.loads(t.invoke(kwargs))


def test_extract_customer_info_finds_email_phone_name_company():
    text = "From: John Smith\nEmail: john@example.com\nPhone: 555-123-4567\nCompany: Acme Corp"
    result = run(extract_customer_info, text=text)
    assert result["customer_email"] == "john@example.com"
    assert result["customer_phone"] == "555-123-4567"
    assert result["customer_name"] == "John Smith"
    assert result["company_name"] == "Acme Corp"


def test_extract_customer_info_empty_text_returns_nulls():
    result = run(extract_customer_info, text="no useful information here")
    assert result["customer_email"] is None
    assert result["customer_name"] is None


def test_extract_items_pattern_at_price():
    result = run(extract_items, text="5 laptops at $1000 each")
    assert len(result) == 1
    assert result[0]["quantity"] == 5.0
    assert result[0]["price"] == 1000.0


def test_extract_items_pattern_x_dash_price():
    result = run(extract_items, text="10x Widget A - $25.00")
    assert len(result) == 1
    assert result[0]["quantity"] == 10.0
    assert result[0]["name"] == "Widget A"
    assert result[0]["price"] == 25.0


def test_extract_items_no_items_returns_empty_list():
    result = run(extract_items, text="Thanks for your inquiry, no order yet.")
    assert result == []


def test_extract_addresses_ship_to_and_bill_to():
    text = "Ship to: 123 Main St, City, State 12345\nBill to: 456 Oak Ave, Town, State 67890"
    result = run(extract_addresses, text=text)
    assert "123 Main St" in result["shipping_address"]
    assert "456 Oak Ave" in result["billing_address"]


def test_extract_addresses_billing_same_as_shipping():
    text = "Ship to: 123 Main St, City, State 12345\nBilling: same as shipping"
    result = run(extract_addresses, text=text)
    assert result["billing_address"] == result["shipping_address"]


def test_extract_dates_normalizes_to_iso():
    text = "Order Date: 01/15/2024\nDelivery Date: 2024-02-01"
    result = run(extract_dates, text=text)
    assert result["order_date"] == "2024-01-15"
    assert result["delivery_date"] == "2024-02-01"


def test_extract_financial_info_total_currency_terms():
    text = "Subtotal: $100.00\nTax: $8.00\nTotal: $108.00\nPayment terms: Net 30"
    result = run(extract_financial_info, text=text)
    assert result["total_amount"] == 108.0
    assert result["subtotal"] == 100.0
    assert result["tax_amount"] == 8.0
    assert result["currency"] == "USD"
    assert result["payment_terms"] == "Net 30"


def test_validate_order_data_flags_missing_customer_and_items():
    result = run(validate_order_data, order_json=json.dumps({"customer_name": None, "items": []}))
    assert result["valid"] is False
    assert any("customer" in e.lower() for e in result["errors"])
    assert any("item" in e.lower() for e in result["errors"])


def test_validate_order_data_passes_complete_order():
    order = {
        "customer_name": "John Doe",
        "items": [{"name": "Widget", "quantity": 2, "price": 10.0}]
    }
    result = run(validate_order_data, order_json=json.dumps(order))
    assert result["valid"] is True
    assert result["errors"] == []


def test_validate_order_data_invalid_json():
    result = json.loads(validate_order_data.invoke({"order_json": "not json"}))
    assert result["valid"] is False


def test_calculate_confidence_exact_match_scores_high():
    text = "Customer: John Doe"
    result = run(calculate_confidence, extracted_data=json.dumps({"customer_name": "John Doe"}), original_text=text)
    assert result["field_confidence"]["customer_name"] == 0.9


def test_calculate_confidence_empty_field_scores_zero():
    result = run(calculate_confidence, extracted_data=json.dumps({"customer_name": None}), original_text="anything")
    assert result["field_confidence"]["customer_name"] == 0.0


def test_normalize_date_handles_various_formats():
    assert normalize_date("01/15/2024") == "2024-01-15"
    assert normalize_date("not a date") == "not a date"


def test_is_valid_date():
    assert is_valid_date("2024-01-15") is True
    assert is_valid_date("not a date") is False


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
