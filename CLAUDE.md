# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Streamlit app that extracts structured order data (customer, items, addresses, totals) from unstructured
input — pasted text/email or uploaded PDF — using a local Ollama LLM (`llama3.2:latest`) via LangChain, with
regex/pattern-matching tools as a refinement/fallback layer. All processing is local; no external API calls.

Source lives in `src/` at the repo root as a proper package (relative imports throughout); `app.py` and
`usage_examples.py` are entry-point scripts at the repo root that import from it as `src.<module>`; tests and
their fixtures live in `tests/`. (Older docs under `docs/` and `README.md` still describe a nested
`Full_order_agent_application/` layout from before the Aug 2026 restructure — the repo root is now that
directory.)

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

Only step 1 calls the LLM. Steps 2–5 are deterministic Python — no model call in the loop. Despite the
`OrderExtractionAgent` name and `agent.py` importing LangChain agent machinery (`AgentAction`, `AgentFinish`,
`PromptTemplate`, `StreamingStdOutCallbackHandler`, `AGENT_TOOLS`, `SYSTEM_PROMPT`), none of those are actually
used anywhere in the file — there is no `AgentExecutor`, no tool-calling loop; tools are invoked directly by
name from `_refine_with_tools`. Don't assume agentic/tool-choosing behavior when editing this file. Similarly,
`prompts.py` defines eleven prompt templates but `get_extraction_prompt()` (wrapping `EXTRACTION_PROMPT`) is
the only one ever called — `VALIDATION_PROMPT`, `CONFIDENCE_ASSESSMENT_PROMPT`, `MISSING_FIELDS_PROMPT`, etc.
are unused, and the `confidence_scores` field the extraction prompt asks the LLM to self-report is requested
in the JSON contract but never read back (confidence is computed independently by `calculate_confidence`, a
substring-match heuristic against the source text).

`process_pdf()` routes through `pdf_processor.PDFProcessor` (PyPDF2 + pdfplumber dual-strategy text
extraction, paragraph/sentence-aware chunking, table extraction) before feeding into `extract_order()`. Chunks
are computed but not used for extraction — the full cleaned text goes into one LLM prompt regardless of
length; `num_chunks` only ever surfaces as a metadata count.

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

**UI** (`app.py`): Streamlit single-page app at the repo root; imports `src.agent.OrderExtractionAgent` and
`src.pdf_processor.PDFValidator` after inserting its own directory onto `sys.path`.

**Config** (`src/config.py`): defines a `Config` class read entirely from env vars, with
`Development/Production/TestingConfig` subclasses selected via `APP_ENV`, and self-validates on import
(raises `ValueError` on bad values). Currently not imported by any other module — `agent.py`, `app.py`, and
`database.py` all take their settings as constructor args/defaults instead. Wire through `Config` rather than
adding new hardcoded defaults if you're touching settings.

## Next steps

Not committed to, but the natural next changes based on gaps found while writing up the architecture:

- **Wire `Config` through** — `agent.py`/`app.py`/`database.py` each hardcode their own defaults
  (`llama3.2:latest`, `0.1`, `http://localhost:11434`, ...) that happen to agree with `Config`'s today but
  aren't sourced from it. Lowest-risk first step: have `OrderExtractionAgent.__init__` default from
  `Config` instead of literals.
- **Delete or actually use the dead LangChain agent imports** in `agent.py` (`AgentAction`, `AgentFinish`,
  `PromptTemplate`, `StreamingStdOutCallbackHandler`, `AGENT_TOOLS`, `SYSTEM_PROMPT`) — either remove them, or
  if a real tool-calling `AgentExecutor` is wanted, that's a bigger design change (the model would choose
  which tool to call, which changes the confidence/validation story too).
- **Prune unused prompt templates** in `prompts.py` (ten of eleven) or start using them — e.g. wiring
  `VALIDATION_PROMPT`/`CONFIDENCE_ASSESSMENT_PROMPT` as an actual second LLM pass instead of the current
  substring-match heuristic, if LLM-judged confidence is wanted.
- **Add unit tests for `tools.py` and `schema.py`** that don't need Ollama running — the regex extractors and
  Pydantic validators are pure functions and currently have zero coverage; `tests/test_agent.py` only smoke-
  tests the full pipeline against a live model.
- **Either wire PDF chunking into extraction or drop it** — `_create_chunks` is built but `process_pdf` sends
  full document text in one prompt regardless of length. Long PDFs have no context-length guardrail today.
- **Internationalize the regex tools** if non-US input matters — currency/date/keyword patterns in `tools.py`
  currently assume `$`, `MM/DD/YYYY`-ish dates, and English labels like `"ship to:"`/`"net 30"`.
- **Sync `docs/` and `README.md`** to the current flat repo-root layout — they still describe the pre-restructure
  nested `Full_order_agent_application/` structure.
