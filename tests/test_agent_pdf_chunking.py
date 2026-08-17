"""
Unit tests for chunked PDF extraction in src/agent.py (_extract_with_llm_chunked,
_dedupe_items). No Ollama required: _extract_with_llm is monkeypatched.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agent import OrderExtractionAgent


def make_agent():
    # OrderExtractionAgent.__init__ only configures the client, no network call
    return OrderExtractionAgent()


def test_dedupe_items_drops_exact_repeats():
    agent = make_agent()
    items = [
        {"name": "Widget", "quantity": 2, "price": 10.0},
        {"name": "Widget", "quantity": 2, "price": 10.0},  # duplicate from chunk overlap
        {"name": "Gadget", "quantity": 1, "price": 5.0},
    ]
    result = agent._dedupe_items(items)
    assert result == [
        {"name": "Widget", "quantity": 2, "price": 10.0},
        {"name": "Gadget", "quantity": 1, "price": 5.0},
    ]


def test_extract_with_llm_chunked_merges_fields_and_concatenates_items():
    agent = make_agent()

    per_chunk_results = {
        "chunk0": {"customer_name": "Jane Doe", "items": [{"name": "Widget", "quantity": 2, "price": 10.0}]},
        "chunk1": {"customer_name": None, "total_amount": 500.0, "items": [{"name": "Gadget", "quantity": 1, "price": 5.0}]},
    }
    agent._extract_with_llm = lambda text: per_chunk_results[text]

    chunks = [
        {"chunk_id": 0, "text": "chunk0"},
        {"chunk_id": 1, "text": "chunk1"},
    ]
    merged = agent._extract_with_llm_chunked(chunks)

    assert merged["customer_name"] == "Jane Doe"  # first non-empty wins
    assert merged["total_amount"] == 500.0  # picked up from later chunk
    assert merged["items"] == [
        {"name": "Widget", "quantity": 2, "price": 10.0},
        {"name": "Gadget", "quantity": 1, "price": 5.0},
    ]


def test_extract_with_llm_chunked_first_chunk_value_not_overwritten():
    agent = make_agent()

    per_chunk_results = {
        "chunk0": {"customer_name": "Jane Doe", "items": []},
        "chunk1": {"customer_name": "Someone Else", "items": []},
    }
    agent._extract_with_llm = lambda text: per_chunk_results[text]

    chunks = [{"chunk_id": 0, "text": "chunk0"}, {"chunk_id": 1, "text": "chunk1"}]
    merged = agent._extract_with_llm_chunked(chunks)

    assert merged["customer_name"] == "Jane Doe"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
