# Architecture

Technical reference for how the extraction pipeline works and how to call it programmatically. For setup and
basic usage, see the [main README](../README.md). This file is the human-readable companion to
[`CLAUDE.md`](../CLAUDE.md), which covers the same ground more tersely for AI coding assistants working in
this repo — if the two ever disagree, trust `CLAUDE.md` as the more actively maintained one.

## System overview

A fixed, five-step pipeline turns unstructured text (pasted, or extracted from a PDF) into a validated `Order`
object. Only the first step calls the LLM; the rest is deterministic Python. There is no agentic tool-choosing
loop — despite `agent.py`'s filename and LangChain's `OllamaLLM` client being used for inference, nothing here
decides which tool to call at runtime. The pipeline is orchestrated by a single class,
`OrderExtractionPipeline` (`src/agent.py`), and one generator (`_run_pipeline_streaming`) implements steps 2–6
for every entry point — batch and streaming, text and PDF — so there's exactly one place to change pipeline
behavior.

```
                         ┌───────────────┐
                         │  User Input   │
                         │  PDF or text  │
                         └───────┬───────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
            ┌───────▼───────┐                 │
            │ PDF Processor │                 │
            │ text+table    │                 │
            │ extraction,   │                 │
            │ chunking      │                 │
            └───────┬───────┘                 │
                    │                         │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ 1. LLM extraction        │  ← only step that calls Ollama
                    │    one prompt per chunk  │    (once per chunk for long PDFs,
                    │    for long PDFs, merged │     merged: first non-empty value
                    └────────────┬────────────┘     wins per field, items concatenated
                                 │                    + deduped)
                                 ▼
                    ┌─────────────────────────┐
                    │ 2. Regex-tool refinement │  ← fills fields the LLM left empty
                    └────────────┬────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │ 3. Validation            │  ← required fields, sane values
                    └────────────┬────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │ 4. Confidence scoring    │  ← substring-match heuristic
                    └────────────┬────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │ 5. Assembly              │  ← Pydantic Order + ExtractionResult
                    └────────────┬────────────┘
                                 │
                        ┌────────┴────────┐
                        ▼                 ▼
                 Streamlit UI      Database (optional,
                 JSON download     ENABLE_DATABASE=true)
```

## Key components

### `OrderExtractionPipeline` (`src/agent.py`)

The orchestrator. Entry points:

| Method | Shape | Use for |
|---|---|---|
| `extract_order(text, source_type="text")` | returns a dict | one-shot text/email extraction |
| `extract_order_streaming(text, source_type="text")` | generator, yields progress dicts | UI progress bars |
| `process_pdf(pdf_file)` | returns a dict | one-shot PDF extraction |
| `process_pdf_streaming(pdf_file)` | generator, yields progress dicts | UI progress bars for PDFs, including per-chunk progress on long documents |

All four share `_run_pipeline_streaming` for steps 2–6; the batch variants (`extract_order`, `process_pdf`)
just drain their streaming counterpart and return its final event via a small `_last()` helper. Streaming
events look like:

```python
{"status": "starting", "message": str}
{"status": "extracting" | "refining" | "validating" | "scoring" | "finalizing", "message": str}
{"status": "progress", "data": dict, "step": int, "total_steps": 5}
{"status": "complete", "result": dict}
{"status": "error", "error": str}
```

### `PDFProcessor` (`src/pdf_processor.py`)

Dual-strategy text extraction — PyPDF2 first, falling back to pdfplumber if the result looks too thin (< 50
chars) — plus table extraction and paragraph/sentence-aware chunking (splits on `\n\n`, then on sentence
punctuation, with configurable overlap between chunks so context isn't lost at a cut point). When
`process_pdf`/`process_pdf_streaming` see more than one chunk, they run the LLM extraction prompt once per
chunk and merge the results (see the diagram above); table text gets folded into the last chunk so it stays
visible to the model. `PDFValidator` (same module) checks the file's magic bytes and size before any of this
runs.

### `tools.py`

Plain Python functions — no LangChain `@tool` decoration, no JSON-string protocol — called directly by name
from `_refine_with_tools`/`_validate_extraction`/`_calculate_confidence` in `agent.py`:

- `extract_customer_info(text) -> dict` — email/phone regex, name/company via keyword labels (`from:`,
  `customer:`, `company:`, etc.)
- `extract_items(text) -> list[dict]` — four fallback patterns, from `"5 laptops at $1000 each"` to a bare
  `"10 widgets"` with no price
- `extract_addresses(text) -> dict` — keyword-labeled shipping/billing blocks; copies shipping to billing if
  the text says "same as shipping"
- `extract_dates(text) -> dict` — several date formats, normalized to `YYYY-MM-DD` via `dateutil`
- `extract_financial_info(text) -> dict` — totals, subtotal, tax, currency symbol/code, payment terms
  (`net 30`, `cash on delivery`, etc.)
- `validate_order_data(order: dict) -> dict` — business-rule checks, returns
  `{"valid", "errors", "warnings", "can_create_order"}`
- `calculate_confidence(data: dict, original_text: str) -> dict` — see [Confidence scoring](#confidence-scoring) below

`AGENT_TOOLS` is just the list of all seven — a naming leftover from when they were LangChain tools; nothing
agentic consumes it now.

**Known limitation:** these patterns assume US-formatted input (`$`, `MM/DD/YYYY`-ish dates, English labels).
Non-US input falls back silently to whatever the LLM produced alone.

### `schema.py`

Pydantic v2 models:

- **`OrderItem`** — `name`, `quantity`, `unit`, `price`, `subtotal`, `description`, `sku`. `subtotal`
  auto-calculates from `price * quantity` via a `model_validator(mode='after')`, but only if not already set —
  a value the LLM extracted correctly is never overridden.
- **`Order`** — customer info, `items: List[OrderItem]`, addresses, dates, financial fields, references,
  notes, `extras: Dict[str, Any]` (escape hatch for anything not in the schema). `total_amount` similarly
  auto-calculates from `subtotal + tax - discount + shipping` only if not already set.
- **`ExtractionResult`** — wraps an `Order` with `can_create_order`, `confidence`, `missing_fields`,
  `field_confidence`, `warnings`, `extraction_metadata`.

No field is Pydantic-`required` — `Order()` with no arguments is valid (this is what `_create_error_result`
returns on failure). "Required" is a business-rule concept, not a schema one: `CRITICAL_FIELDS` in `schema.py`
(`customer_name`/`company_name`, `items`) is what `validate_order_completeness()` checks to decide
`can_create_order`.

### `prompts.py`

One template, `EXTRACTION_PROMPT`, wrapped by `get_extraction_prompt(text)`. Asks for customer info, items,
addresses, dates, payment terms, and reference numbers as a single JSON object. (An earlier version also asked
the model to self-report per-field confidence scores; that was removed since the value was never read back —
confidence is computed independently, see below.)

### `config.py`

A `Config` class reading everything from env vars (`OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `LLM_TEMPERATURE`,
`PDF_CHUNK_SIZE`, `PDF_CHUNK_OVERLAP`, `DATABASE_PATH`, `ENABLE_DATABASE`, `APP_ENV`, ...), with
`Development`/`Production`/`TestingConfig` subclasses selected via `APP_ENV`. Validates itself on import —
an invalid value raises `ValueError` at import time, not at first use. `OrderExtractionPipeline.__init__` and
`OrderDatabase.__init__` default from it; `app.py`'s model/temperature sidebar widgets deliberately stay
UI-driven rather than `Config`-driven, since those are meant to be adjusted per session.

### `database.py` (optional)

SQLite persistence via the standard library `sqlite3` (no ORM, despite SQLAlchemy being in `requirements.txt`
for other reasons) — three tables: `orders`, `order_items`, `extraction_logs`. Gated by
`Config.ENABLE_DATABASE`; `app.py` has a "Save to Database" button that's disabled when the flag is off.
`OrderDatabase.save_order(extraction_result: dict) -> int` takes the full result dict from
`extract_order`/`process_pdf` and handles all the field mapping internally.

```sql
orders          -- id, order_number, customer_name, financial fields, can_create_order,
                -- confidence, source_type, created_at, full order_json + extraction_result
order_items     -- id, order_id (FK), item_name, quantity, unit, price, subtotal, sku
extraction_logs -- input_type, input_length, success, error_message, processing_time, created_at
                -- (log_extraction() exists but nothing currently calls it automatically)
```

Other methods: `get_order(id)`, `search_orders(customer_name=, start_date=, end_date=, min_amount=,
max_amount=, limit=)`, `get_statistics()` (total/valid order counts, total value, average confidence, orders
in the last 7 days), `close()`.

## Confidence scoring

`calculate_confidence` is a substring-match heuristic, not a model judgment:

- empty/`None` value → `0.0`
- non-empty list → `0.8`
- value appears verbatim (case-insensitive) in the source text → `0.9`
- anything else non-empty → `0.6`

Overall confidence weights `HIGH_CONFIDENCE_FIELDS` (`customer_name`, `customer_email`, `items`,
`total_amount`) 2x against everything else at 1x, then averages.

This is cheap and fully explainable — you can point at the exact substring that earned a score — but it
rewards verbatim copying over correct interpretation: a date correctly reformatted from "Jan 15, 2024" to
"2024-01-15" scores lower than a hallucinated value that happens to also appear elsewhere in the source text.
Improving this (e.g. an actual LLM-judged second pass) is a real design change with a latency/cost trade-off,
not a drop-in fix.

## Error handling

Every pipeline stage is wrapped so a failure degrades to a well-formed error result rather than an unhandled
exception:

- Step 1 (LLM call or JSON parse failure) is caught in `extract_order`/`extract_order_streaming`'s own
  try/except, independent of steps 2–6.
- Steps 2–6 (including a `Pydantic ValidationError` from `_build_order`) are caught inside
  `_run_pipeline_streaming` itself, so both the batch and streaming entry points get identical error
  conversion.
- Either failure produces `_create_error_result(message)`: `can_create_order: false`, `confidence: 0.0`,
  `missing_fields` set to `CRITICAL_FIELDS`, an empty `Order()`, and the error message in `warnings`.
- A malformed LLM JSON response (steps `_extract_json_from_response`/`json.loads`) doesn't raise at all — it
  degrades to `{"customer_name": None, "items": [], "raw_response": <text>}` and lets steps 2–4 attempt to
  fill in from there via the regex tools.

There's no retry — a bad LLM response on the first attempt isn't re-prompted.

## Testing

- `tests/test_tools.py`, `tests/test_schema.py` — pure-function unit tests, no Ollama needed.
- `tests/test_agent_pdf_chunking.py` — unit tests for the chunk-merge/dedupe logic, with `_extract_with_llm`
  monkeypatched (no Ollama needed).
- `tests/test_agent.py` — integration smoke test; runs every `*.txt` in `tests/sample_inputs/` through the
  live pipeline against a real Ollama instance, writes results to `tests/test_outputs/`. No assertions — just
  checks nothing raised.

Run `pytest tests/` for the first three; they're fast and safe for a tight edit loop.

## Extending

**Add a field**: add it to `Order`/`OrderItem` in `schema.py` (or just use the existing `extras: Dict[str,
Any]` field).

**Add an extraction tool**: write a plain function in `tools.py` (`text -> dict`, matching the existing ones),
call it from `_refine_with_tools` in `agent.py` for whichever field it fills.

**Add a validation rule**: extend `validate_order_data` in `tools.py`, or add a similar function and call it
from `_validate_extraction`.

## API reference

### `OrderExtractionPipeline`

```python
from src.agent import OrderExtractionPipeline

pipeline = OrderExtractionPipeline(
    model_name="llama3.2:latest",       # defaults from Config if omitted
    temperature=0.1,
    ollama_base_url="http://localhost:11434",
    verbose=True
)
```

```python
result = pipeline.extract_order(input_text, source_type="text")
# {
#   "can_create_order": bool,
#   "confidence": float,
#   "missing_fields": list[str],
#   "order": {...},              # full Order.model_dump()
#   "field_confidence": {...},
#   "warnings": list[str],
#   "extraction_metadata": {"source_type", "model", "timestamp", "steps", ["pdf_info" for PDFs]}
# }
```

```python
for update in pipeline.extract_order_streaming(input_text):
    if update["status"] == "progress":
        print(f"step {update['step']}/{update['total_steps']}")
    elif update["status"] == "complete":
        result = update["result"]
    elif update["status"] == "error":
        print(update["error"])
```

```python
result = pipeline.process_pdf("invoice.pdf")               # path, or a Streamlit-style file-like object
for update in pipeline.process_pdf_streaming(pdf_file):     # same event shape as extract_order_streaming,
    ...                                                     # plus per-chunk progress for long PDFs
```

### `PDFProcessor`

```python
from src.pdf_processor import PDFProcessor

processor = PDFProcessor(chunk_size=2000, chunk_overlap=200)
result = processor.process_pdf(pdf_file)
# {"text", "metadata", "chunks", "tables", "total_length", "num_chunks", "success"}
```

### `OrderDatabase`

```python
from src.database import OrderDatabase

db = OrderDatabase("database/orders.db")
order_id = db.save_order(extraction_result)     # extraction_result = output of extract_order()/process_pdf()
order = db.get_order(order_id)
orders = db.search_orders(customer_name="Acme", min_amount=100.0, limit=50)
stats = db.get_statistics()
db.close()
```

### Tools

```python
from src.tools import extract_customer_info, extract_items, validate_order_data, calculate_confidence

customer = extract_customer_info(text)          # -> dict
items = extract_items(text)                     # -> list[dict]
validation = validate_order_data(order_dict)     # -> dict
scores = calculate_confidence(order_dict, text)  # -> dict
```

### Complete example

```python
from src.agent import OrderExtractionPipeline
from src.database import OrderDatabase

pipeline = OrderExtractionPipeline()
db = OrderDatabase()

text = """
Purchase Order #12345
From: Tech Solutions Inc.
Contact: Sarah Chen (sarah@techsolutions.com)

Items:
- 10 Laptops @ $1200 = $12,000
- 10 Mice @ $50 = $500

Total: $12,500
Ship to: 123 Tech Ave, San Francisco, CA 94105
Payment: Net 30
"""

result = pipeline.extract_order(text)

if result["can_create_order"]:
    order = result["order"]
    print(f"{order['customer_name']}: {len(order['items'])} items, ${order['total_amount']}")
    order_id = db.save_order(result)
else:
    print("Missing:", result["missing_fields"], "Warnings:", result["warnings"])

db.close()
```

## Known limitations

- No retry on a malformed LLM response — see [Error handling](#error-handling).
- Regex tools assume US-formatted input (currency, dates, English labels).
- Confidence scoring is a substring-match heuristic, not a calibrated score.
- Single-threaded, local-only; no horizontal scaling story.
- `extraction_logs` table exists in the database schema but nothing calls `log_extraction()` automatically.
