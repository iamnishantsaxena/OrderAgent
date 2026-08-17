"""
Unit tests for the Pydantic models and helpers in src/schema.py.
Pure functions, no Ollama required: run with `pytest tests/test_schema.py`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.schema import (
    Order, OrderItem, validate_order_completeness, calculate_overall_confidence
)


def test_order_item_subtotal_auto_calculated():
    item = OrderItem(name="Widget", quantity=3, price=10.0)
    assert item.subtotal == 30.0


def test_order_item_subtotal_not_overridden_when_provided():
    item = OrderItem(name="Widget", quantity=3, price=10.0, subtotal=999.0)
    assert item.subtotal == 999.0


def test_order_total_amount_auto_calculated():
    order = Order(subtotal=100.0, tax_amount=8.0, shipping_cost=5.0, discount=3.0)
    assert order.total_amount == 110.0


def test_order_total_amount_not_overridden_when_provided():
    order = Order(subtotal=100.0, tax_amount=8.0, total_amount=999.0)
    assert order.total_amount == 999.0


def test_validate_order_completeness_missing_everything():
    order = Order()
    is_valid, missing = validate_order_completeness(order)
    assert is_valid is False
    assert "customer_name or company_name" in missing
    assert "items" in missing


def test_validate_order_completeness_valid_order():
    order = Order(customer_name="Jane Doe", items=[OrderItem(name="Widget", quantity=1)])
    is_valid, missing = validate_order_completeness(order)
    assert is_valid is True
    assert missing == []


def test_calculate_overall_confidence_weights_critical_fields():
    # customer_name is a HIGH_CONFIDENCE_FIELD (weight 2), notes is not (weight 1)
    result = calculate_overall_confidence({"customer_name": 1.0, "notes": 0.0})
    assert result == round((1.0 * 2 + 0.0 * 1) / 3, 2)


def test_calculate_overall_confidence_empty_returns_zero():
    assert calculate_overall_confidence({}) == 0.0


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
