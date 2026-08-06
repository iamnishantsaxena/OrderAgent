# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Streamlit app that extracts structured order data (customer, items, addresses, totals) from unstructured
input — pasted text/email or uploaded PDF — using a local Ollama LLM (`llama3.2:latest`) via LangChain, with
regex/pattern-matching tools as a refinement/fallback layer. All processing is local; no external API calls.

Source lives in `Full_order_agent_application/src/` as a proper package (relative imports throughout);
`app.py` and `usage_examples.py` are entry-point scripts at `Full_order_agent_application/` root that import
from it as `src.<module>`; tests and their fixtures live in `Full_order_agent_application/tests/`. This
matches the layout `README.md`/`docs/` describe.

## Setup & running

Must run from inside `Full_order_agent_application/` — `app.py` and `usage_examples.py` insert their own
directory onto `sys.path` so `src` resolves as a package from there; they are not designed to run from the
repo root or be installed.

```bash
cd Full_order_agent_application

# Ollama must be running with the model pulled
ollama pull llama3.2:latest
ollama serve            # separate terminal

# Env: uv-managed venv at repo root (.venv), Python 3.12
uv pip install -r ../requirements.txt

# Run the app
streamlit run app.py    # http://localhost:8501
```

Config is env-var driven via `Full_order_agent_application/config.py` (`Config` class reads `OLLAMA_BASE_URL`,
`OLLAMA_MODEL`, `LLM_TEMPERATURE`, `PDF_CHUNK_SIZE`, `DATABASE_PATH`, `ENABLE_DATABASE`, `APP_ENV`, etc.).
`APP_ENV` selects between `DevelopmentConfig` / `ProductionConfig` / `TestingConfig`. Config validates itself
on import and raises `ValueError` if invalid — a bad env var value breaks module import, not just runtime.

## Tests

```bash
cd Full_order_agent_application
python tests/test_agent.py     # runs every *.txt in tests/sample_inputs/ through the live agent,
                                # writes results to tests/test_outputs/ (requires Ollama running)
```

This is a script, not a pytest suite — there's no `pytest.ini`/`pyproject.toml` and no assertions, just
extraction + a pass/fail summary based on whether each file raised. It calls the real LLM, so it's an
integration smoke test, not something to run in a tight edit loop.

## Architecture

Extraction pipeline, orchestrated by `OrderExtractionAgent` in `src/agent.py`:

1. **LLM extraction** (`_extract_with_llm`) — sends `prompts.get_extraction_prompt(text)` to Ollama, parses
   JSON out of the response (handles ```json fences, falls back to brace-matching).
2. **Tool-based refinement** (`_refine_with_tools`) — for any field the LLM extraction left empty, calls the
   matching regex/heuristic tool from `tools.py` (`extract_customer_info`, `extract_items`,
   `extract_addresses`, `extract_dates`, `extract_financial_info`) and merges in non-empty results. Tools are
   independent, idempotent, LangChain `@tool`-decorated functions; `AGENT_TOOLS` in `tools.py` is the list of
   all of them plus `validate_order_data` and `calculate_confidence`.
3. **Validation** (`_validate_extraction`) — `tools.validate_order_data`, business-rule checks.
4. **Confidence scoring** (`_calculate_confidence`) — `tools.calculate_confidence`; weighted by
   `HIGH_CONFIDENCE_FIELDS` in `schema.py` (critical fields count 2x).
5. **Assembly** (`_build_order`) — builds a `schema.Order` (Pydantic model), wraps in `schema.ExtractionResult`
   along with `can_create_order` (from `schema.validate_order_completeness`), overall confidence, missing
   fields, and `extraction_metadata` (per-step timing/log, source type, model name).

`extract_order_streaming()` is the same pipeline as a generator yielding progress dicts (`status`, `step`,
`total_steps`) for the Streamlit UI's live updates — keep both methods in sync when touching the pipeline.

`process_pdf()` routes through `pdf_processor.PDFProcessor` (PyPDF2 + pdfplumber dual-strategy text
extraction, paragraph/sentence-aware chunking, table extraction) before feeding into `extract_order()`.

All cross-module imports inside `src/` are relative (`from .schema import ...`, `from .tools import ...`) —
`src/agent.py` is the only module that reaches across siblings, importing `schema`, `tools`, `prompts`, and
`pdf_processor`. Keep new intra-`src/` imports relative; nothing outside `src/` should import from inside it
except via `from src.<module> import ...`.

**Schema** (`schema.py`): `Order` and `OrderItem` are Pydantic models with `model_validator(mode='after')`
auto-calculation — `OrderItem.subtotal` from `price * quantity`, `Order.total_amount` from
`subtotal + tax + shipping - discount`. Both only fill in when the field wasn't already provided by
extraction. `extras: Dict[str, Any]` is the escape hatch for fields not in the schema.

**Database** (`database.py`, optional): SQLite persistence, gated by `Config.ENABLE_DATABASE`
(`ENABLE_DATABASE=true` env var). Not wired into the default extraction flow (`app.py` never calls it) — it's
only exercised via `usage_examples.py`'s example 4. Treat it as available-but-optional, not a required part of
the pipeline.

**UI** (`app.py`): Streamlit single-page app at `Full_order_agent_application/app.py`; imports
`src.agent.OrderExtractionAgent` and `src.pdf_processor.PDFValidator` after inserting its own directory onto
`sys.path`.

**Config** (`src/config.py`): defines a `Config` class read entirely from env vars, with
`Development/Production/TestingConfig` subclasses selected via `APP_ENV`, and self-validates on import
(raises `ValueError` on bad values). Currently not imported by any other module — `agent.py`, `app.py`, and
`database.py` all take their settings as constructor args/defaults instead. Wire through `Config` rather than
adding new hardcoded defaults if you're touching settings.
