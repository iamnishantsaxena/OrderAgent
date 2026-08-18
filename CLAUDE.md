# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Streamlit app that extracts structured order data (customer, items, addresses, totals) from unstructured
input — pasted text/email or uploaded PDF — using a local Ollama LLM (`llama3.2:latest`) via LangChain, with
regex/pattern-matching tools as a refinement/fallback layer. All processing is local; no external API calls.

Source lives in `src/` at the repo root as a proper package (relative imports throughout); `app.py` and
`usage_examples.py` are entry-point scripts at the repo root that import from it as `src.<module>`; tests and
their fixtures live in `tests/`. `README.md` and `docs/ARCHITECTURE.md` are the human-facing docs — kept in
sync with the current flat repo-root layout; this file is the terser AI-assistant-facing equivalent.

## Setup & running

Run from the repo root — `app.py` and `usage_examples.py` insert their own directory onto `sys.path` so `src`
resolves as a package from there; they are not designed to be installed.

```bash
# Ollama must be running with the model pulled
ollama pull llama3.2:latest
ollama serve            # separate terminal

# Env: uv-managed venv at repo root (.venv), Python 3.12 — it's a bare venv with no pip binary,
# so use `uv pip`, not `pip`/`pip3`, once activated
source .venv/bin/activate
uv pip install -r requirements.txt

# Run the app
streamlit run app.py    # http://localhost:8501
```

Config is env-var driven via `src/config.py` (`Config` class reads `OLLAMA_BASE_URL`, `OLLAMA_MODEL`,
`LLM_TEMPERATURE`, `PDF_CHUNK_SIZE`, `DATABASE_PATH`, `ENABLE_DATABASE`, `APP_ENV`, etc.). `APP_ENV` selects
between `DevelopmentConfig` / `ProductionConfig` / `TestingConfig`. Config validates itself on import and
raises `ValueError` if invalid — a bad env var value breaks module import, not just runtime.

## Tests

```bash
pytest tests/                  # tests/test_tools.py, test_schema.py, test_agent_pdf_chunking.py —
                                # pure-function/mocked, no Ollama needed, safe for a tight edit loop

python tests/test_agent.py     # runs every *.txt in tests/sample_inputs/ through the live pipeline,
                                # writes results to tests/test_outputs/ (requires Ollama running)
```

`test_agent.py` is a script, not a pytest suite — there's no assertions, just extraction + a pass/fail summary
based on whether each file raised. It calls the real LLM, so it's an integration smoke test, not something to
run in a tight edit loop. The other three files are real `pytest` unit tests: `test_tools.py`/`test_schema.py`
cover the regex extractors and Pydantic validators directly (no Ollama), and `test_agent_pdf_chunking.py`
covers the chunk-merge/dedupe logic in `agent.py` with `_extract_with_llm` monkeypatched.

## Architecture

Extraction pipeline, run by `OrderExtractionPipeline` in `src/agent.py`. `_run_pipeline_streaming()` is the
single generator implementation of steps 2–6 below — `extract_order()` (batch), `extract_order_streaming()`
(yields progress dicts), and `process_pdf()`/`process_pdf_streaming()` (PDF input) all route through it, so
there is exactly one place to edit when touching the pipeline, not several hand-kept-in-sync copies.

1. **LLM extraction** (`_extract_with_llm`) — sends `prompts.get_extraction_prompt(text)` to Ollama, parses
   JSON out of the response (handles ```json fences, falls back to brace-matching). For PDFs longer than
   `PDF_CHUNK_SIZE`, `_extract_with_llm_chunked_streaming` runs this once per chunk (via
   `PDFProcessor._create_chunks`, paragraph/sentence-aware) and merges the results — first non-empty value
   wins per scalar field, items are concatenated and deduped by `(name, quantity, price)`, table text is
   folded into the last chunk so it stays visible to the model.
2. **Tool-based refinement** (`_refine_with_tools`) — for any field the LLM extraction left empty, calls the
   matching regex/heuristic function from `tools.py` (`extract_customer_info`, `extract_items`,
   `extract_addresses`, `extract_dates`, `extract_financial_info`) and merges in non-empty results. These are
   plain functions taking/returning dicts — no LangChain `@tool` decoration, no JSON-string round-trip; they're
   called directly by name, never through an `AgentExecutor`. `AGENT_TOOLS` in `tools.py` is just the list of
   all of them plus `validate_order_data` and `calculate_confidence` (the name is legacy — nothing agentic ever
   consumed it, and nothing does now).
3. **Validation** (`_validate_extraction`) — `tools.validate_order_data`, business-rule checks.
4. **Confidence scoring** (`_calculate_confidence`) — `tools.calculate_confidence`; weighted by
   `HIGH_CONFIDENCE_FIELDS` in `schema.py` (critical fields count 2x). This is a substring-match heuristic
   against the source text, not an LLM judgment — the prompt no longer asks the model to self-report
   confidence (that field used to be requested but never read back, so it was removed from
   `EXTRACTION_PROMPT`).
5. **Assembly** (`_build_order`) — builds a `schema.Order` (Pydantic model), wraps in `schema.ExtractionResult`
   along with `can_create_order` (from `schema.validate_order_completeness`), overall confidence, missing
   fields, and `extraction_metadata` (per-step timing/log, source type, model name, and — for PDFs —
   `pdf_info`: page/chunk/table counts).

Only step 1 calls the LLM (once per chunk for long PDFs, once otherwise). Steps 2–5 are deterministic Python —
no model call in the loop. `prompts.py` now defines only `EXTRACTION_PROMPT`/`get_extraction_prompt()` — the
ten other templates that used to exist (`VALIDATION_PROMPT`, `CONFIDENCE_ASSESSMENT_PROMPT`,
`MISSING_FIELDS_PROMPT`, etc.) were unused and have been deleted, not just left dead.

All cross-module imports inside `src/` are relative (`from .schema import ...`, `from .tools import ...`) —
`src/agent.py` is the only module that reaches across siblings, importing `schema`, `tools`, `prompts`, and
`pdf_processor`. Keep new intra-`src/` imports relative; nothing outside `src/` should import from inside it
except via `from src.<module> import ...`.

**Schema** (`schema.py`): `Order` and `OrderItem` are Pydantic models with `model_validator(mode='after')`
auto-calculation — `OrderItem.subtotal` from `price * quantity`, `Order.total_amount` from
`subtotal + tax + shipping - discount`. Both only fill in when the field wasn't already provided by
extraction. `extras: Dict[str, Any]` is the escape hatch for fields not in the schema. Uses Pydantic v2's
`model_config = ConfigDict(...)`, not the deprecated `class Config`.

**Database** (`database.py`, optional): SQLite persistence, gated by `Config.ENABLE_DATABASE`
(`ENABLE_DATABASE=true` env var). Wired into the UI — `app.py` has a "Save to Database" button next to the
JSON download button, disabled when `ENABLE_DATABASE` is off. `OrderDatabase.save_order(extraction_result)`
takes the full result dict and handles all the field mapping internally; also exercised via
`usage_examples.py`'s example 4. Still optional, not a required part of the pipeline.

**UI** (`app.py`): Streamlit single-page app at the repo root; imports `src.agent.OrderExtractionPipeline`,
`src.pdf_processor.PDFValidator`, `src.database.OrderDatabase`, and `src.config.config` after inserting its own
directory onto `sys.path`. Both the paste-text and upload-PDF input paths drive the same streaming-progress
loop (`extract_order_streaming`/`process_pdf_streaming` yield identically-shaped events), so a long PDF now
shows real per-chunk progress instead of a fake jump to 100%.

**Config** (`src/config.py`): defines a `Config` class read entirely from env vars, with
`Development/Production/TestingConfig` subclasses selected via `APP_ENV`, and self-validates on import
(raises `ValueError` on bad values). Wired through `OrderExtractionPipeline.__init__` (model/temperature/
Ollama URL/PDF chunk size defaults) and `OrderDatabase.__init__` (default `db_path`). `app.py`'s model/
temperature sidebar widgets deliberately stay UI-driven rather than `Config`-driven — those are meant to be
user-adjustable per session. Wire through `Config` rather than adding new hardcoded defaults if you're
touching settings elsewhere.

## Next steps

Not committed to, but the natural next changes based on gaps found while writing up the architecture:

- **Internationalize the regex tools** if non-US input matters — currency/date/keyword patterns in `tools.py`
  currently assume `$`, `MM/DD/YYYY`-ish dates, and English labels like `"ship to:"`/`"net 30"`.
- **`AGENT_TOOLS`'s name is a minor misnomer now** — it's a list of plain functions, not LangChain tools, and
  nothing agentic consumes it. Low-priority rename candidate (e.g. `EXTRACTION_TOOLS`) if it comes up
  organically; not worth a dedicated pass on its own.
- **Confidence scoring is still a cheap heuristic**, not a calibrated score — rewards verbatim copying over
  correct interpretation (see `_calculate_confidence` in `agent.py`). Improving it (e.g. an actual LLM-judged
  second pass) is a real design change with a latency/cost trade-off, not a drop-in fix — no prompt template
  for it currently exists since the unused ones were deleted.
