# Order Extraction Agent

A Streamlit app that extracts structured order data — customer info, line items, addresses, totals — from
unstructured input (pasted email/text or an uploaded PDF) using a local Ollama LLM, backstopped by a layer of
regex/pattern-matching for whatever the model misses. All processing is local; nothing is sent to an external
API.

## What it does

1. **LLM extraction** — the input text goes to a local Ollama model (`llama3.2:latest` by default) with a
   single prompt asking for a structured JSON response.
2. **Regex-tool refinement** — for any field the LLM left empty, a matching regex/heuristic function fills the
   gap (customer info, items, addresses, dates, financial details).
3. **Validation** — checks required fields are present and values are sane (positive quantities, valid dates,
   non-negative totals).
4. **Confidence scoring** — each field gets a score based on whether it matches the source text verbatim
   (a heuristic, not a model judgment).
5. **Assembly** — the result is packaged into a validated `Order` object with auto-calculated subtotals/totals.

For long PDFs, step 1 runs once per chunk and the results are merged, so the app isn't limited to what fits in
one prompt. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full technical breakdown.

## Use cases

- **E-commerce**: turn a customer's order email into structured data for a fulfillment system.
- **B2B purchase orders**: pull line items and terms out of a vendor's PO PDF.
- **Casual/WhatsApp orders**: parse informal, chat-style order messages.
- **Invoice/manifest processing**: extract totals and item lists from scanned or exported documents.

## Prerequisites

- **Ollama**, running locally with a model pulled:

  ```bash
  # macOS/Linux
  curl -fsSL https://ollama.com/install.sh | sh

  ollama pull llama3.2:latest
  ollama serve   # in a separate terminal, if not already running
  ```

- **Python 3.12** and [uv](https://docs.astral.sh/uv/) (recommended) or `pip`.

## Installation

Run from the repo root:

```bash
# Create and activate a virtual environment
uv venv --python=3.12
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows

# Install dependencies (this venv has no pip binary — use `uv pip`, not `pip`/`pip3`)
uv pip install -r requirements.txt
```

## Running the app

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`. In the sidebar, pick a model/temperature and click **Initialize Agent**,
then either upload a PDF or paste text and click **Generate Order JSON**.

## Programmatic usage

```python
from src.agent import OrderExtractionPipeline

pipeline = OrderExtractionPipeline()

text = "Order from John Doe, 5 laptops at $1000 each, ship to 123 Main St"
result = pipeline.extract_order(text)

if result["can_create_order"]:
    print(result["order"])
else:
    print("Missing fields:", result["missing_fields"])
```

`process_pdf(pdf_file)` does the same for a PDF path or file-like object. Both also have streaming variants
(`extract_order_streaming`, `process_pdf_streaming`) that yield progress dicts as extraction proceeds — see
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full API reference, or `usage_examples.py` for more
end-to-end examples (batch processing, database storage, confidence filtering).

## Testing

```bash
pytest tests/                  # unit tests — pure functions and mocked LLM calls, no Ollama needed
python tests/test_agent.py     # integration smoke test — runs tests/sample_inputs/*.txt through the
                                # live pipeline against a real Ollama instance
```

## Output schema

```json
{
  "can_create_order": true,
  "confidence": 0.85,
  "missing_fields": ["delivery_date"],
  "order": {
    "customer_name": "John Doe",
    "customer_email": "john@example.com",
    "customer_phone": "+1234567890",
    "items": [
      {
        "name": "Laptop Pro 15",
        "quantity": 5,
        "price": 1000.00,
        "subtotal": 5000.00
      }
    ],
    "shipping_address": "123 Main St, City, State 12345",
    "billing_address": "Same as shipping",
    "payment_terms": "Net 30",
    "order_date": "2024-01-15",
    "total_amount": 5000.00,
    "currency": "USD",
    "extras": {}
  },
  "field_confidence": {
    "customer_name": 0.95,
    "items": 0.90,
    "shipping_address": 0.80
  }
}
```

## Configuration

Settings are env-var driven via `src/config.py`:

```bash
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_MODEL="llama3.2:latest"
export LLM_TEMPERATURE="0.1"
export PDF_CHUNK_SIZE="2000"          # characters per chunk before a PDF gets split across multiple LLM calls
export DATABASE_PATH="database/orders.db"
export ENABLE_DATABASE="true"         # turns on the "Save to Database" button in the UI
export APP_ENV="production"           # development (default) | production | testing
```

A bad value raises `ValueError` on import rather than failing silently at runtime.

## Troubleshooting

**"Connection refused" / can't reach Ollama**
```bash
ollama list          # confirms Ollama is running and shows pulled models
ollama serve          # start it if not running
```

**Model not found**
```bash
ollama pull llama3.2:latest
```

**Slow extraction**
- Use a smaller model: `ollama pull llama3.2:1b`, then select it in the sidebar.
- Lower `PDF_CHUNK_SIZE` for large PDFs — smaller chunks mean smaller/faster individual LLM calls, at the cost
  of more of them.

## Customization

**Add a field to the schema** — edit `src/schema.py`:
```python
class Order(BaseModel):
    ...
    custom_field: Optional[str] = None
```
(Or use the existing `extras: Dict[str, Any]` field if you don't want a schema change.)

**Add a validation rule** — `src/tools.py`'s `validate_order_data(order: dict) -> dict` returns
`{"valid": bool, "errors": [...], "warnings": [...], "can_create_order": bool}`; add a check inside it, or add
a similar plain function and call it from `OrderExtractionPipeline._validate_extraction` in `src/agent.py`.

## Security notes

- All inference is local — `OllamaLLM` (pointed at `localhost:11434` by default) is the only network client in
  `src/`. No text ever leaves the machine.
- PDF uploads are validated (magic-byte check, size limit) before processing, via `PDFValidator` in
  `src/pdf_processor.py`.
- Database writes use parameterized queries (no raw SQL string interpolation).
- Not hardened for multi-tenant/production deployment as-is — no auth, no rate limiting.

## Project structure

```
app.py                   # Streamlit UI
usage_examples.py        # standalone scripts: batch processing, streaming, DB storage, confidence filtering
requirements.txt
CLAUDE.md                 # architecture reference for AI coding assistants
src/
├── agent.py              # OrderExtractionPipeline — orchestrates the extraction pipeline
├── pdf_processor.py       # PDF text/table extraction, chunking, upload validation
├── schema.py              # Pydantic models (Order, OrderItem, ExtractionResult)
├── tools.py                # regex/heuristic extraction, validation, confidence scoring
├── prompts.py               # the one LLM prompt template
├── config.py                 # env-var-driven settings
└── database.py                # optional SQLite persistence
tests/
├── test_tools.py           # unit tests, no Ollama
├── test_schema.py           # unit tests, no Ollama
├── test_agent_pdf_chunking.py  # unit tests, mocked LLM
├── test_agent.py             # integration smoke test, needs live Ollama
└── sample_inputs/             # sample email/order/WhatsApp-style text files
docs/
└── ARCHITECTURE.md          # deeper technical reference (data flow, components, full API)
```

## Further reading

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — full architecture and API reference
- [Ollama documentation](https://ollama.com/docs)
- [LangChain documentation](https://python.langchain.com/)
- [Streamlit documentation](https://docs.streamlit.io/)
- [Pydantic documentation](https://docs.pydantic.dev/)

## License

MIT — use and modify freely.

## Contributing

Areas that could use work: additional document formats (DOCX, Excel), non-English/non-US input support (the
regex tools currently assume `$`, `MM/DD/YYYY`-ish dates, and English labels), LLM-judged confidence scoring
as an alternative to the current substring-match heuristic.
