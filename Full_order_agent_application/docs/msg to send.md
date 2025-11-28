Hello — thanks again for the assignment and for reviewing my project. I built an agentic Order Extraction system (link to repo below) designed to extract structured order data (customer, line items, prices, dates, addresses, and totals) from unstructured inputs (emails, PDFs, and text). I initially implemented the initial prototype using LangChain + a local Ollama LLM, not ConnectOnion, so I’ve noted how to adapt it to ConnectOnion towards the bottom of this message.

Repository (source): https://github.com/<YOUR-USERNAME>/<YOUR-REPO> <-- replace with actual link

What I built (high level)
A multi-format order extraction agent that accepts text, emails, and PDFs.
Modular toolset for extraction (customer info, items, addresses, dates, amounts), validation, and confidence scoring.
PDF chunking and table extraction pipeline so complex PDFs become reliably parsable.
Streamlit-based UI for interactive testing and real-time streaming output.
Unit tests / sample inputs to validate the agent end-to-end.
Key design decisions — what I did and why 🔧
Separation of concerns (tools + prompts + orchestration)
Tools implemented as isolated functions (tools.py) that independently extract specific fields. This keeps behavior testable and makes it easy to reuse or replace tools.
Schema-driven output and validation
Strongly-typed schema (Pydantic-like models) for the order object and validation functions to ensure consistent, machine-readable output.

Local LLM with Ollama
I used a local LLM (Ollama Llama3.2) to keep inference local, reduce external API costs, and avoid sending sensitive content offsite. This also simplifies reproducibility (same model files locally) and gives low-latency control.
Confidence scoring & validation
Each field has a confidence score and there is a final “can_create_order” gate that checks critical fields — useful for integrating with downstream workflows or human review queues.
Stream/UX considerations
Streaming extraction results back to the UI for better user experience and faster debugging feedback.
Reusability & testability
Clear test harnesses + sample files to reproduce common cases quickly, enabling CI-friendly testing.

Why I chose a local LLM (short, focused)
Data privacy: all processing stays on the developer's machine — safer for real customer documents.
Cost & repeatability: local models avoid per-call charges and give reproducible behavior across runs.
Offline capability & latency: local inference lowers roundtrip time and allows offline testing.
If you’d prefer cloud-hosted models or a managed LLM for production, that’s easy to switch to later.

What I learned while building this
Prompt design matters: crafting extraction prompts with required JSON output dramatically improves structured parsing.
PDF processing is tricky: chunking strategy and table formatting required iterative tuning for better extraction.
Tool orchestration improves robustness: breaking tasks into smaller tools reduces hallucination and improves recoverability.
Streaming + observability helps debugging: the step logs and streaming progress make it much easier to triage failures and edge cases.
Next steps / how I’d adapt this to ConnectOnion (minimal work)

Quick wins:
Add a thin ConnectOnion wrapper that exposes the existing public methods as ConnectOnion tools (example: co_agent.py) — keeps existing logic and lets you “serve” a ConnectOnion agent quickly.
Add a CI-friendly script and README instructions to run co status to get the agent address for the assignment.
Deeper integration:
Optionally port the orchestration logic to ConnectOnion methods and add ConnectOnion plugins for traceability and debugging.
Add a tiny connectonion-based E2E sample script so reviewers can call the agent via ConnectOnion directly.

If you’d like, I can fully port the agent core to ConnectOnion agent instead and resubmit the project. 

Thanks again for your time — I’d be happy to make the minimal “ConnectOnion wrapper + README” change so you can run co status and get an agent address for the assignment. Please let me know if you'd prefer I make that change now.

Best,
Nishant Saxena