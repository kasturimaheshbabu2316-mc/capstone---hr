# Engineering, Governance & Coding Rules

## Naukri.com Domain Support Agent (HR & Recruitment Track)

---

## 1. Non-Negotiable Hard Constraints & Invariants

All contributors and AI agents working on this codebase must strictly comply with the following 10 invariants derived from [`doc/problemStatement.md`](file:///c:/Users/kastu/Desktop/capstone%20-%20hr/doc/problemStatement.md):

### Invariant 1: 100% Deterministic & Offline Execution

- The system must run entirely under `MOCK_LLM` extending `crewai.llms.base_llm.BaseLLM`.
- Zero external API keys (OpenAI, Anthropic, Cohere, etc.) are permitted.
- Zero outbound network sockets during testing or runtime execution.

### Invariant 2: Explicit Telemetry Suppression

- CrewAI telemetry makes an outbound internet call on import/runtime.
- Environment variables must be set before importing `crewai`:

  ```python
  import os
  os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
  os.environ["OTEL_SDK_DISABLED"] = "true"
  ```

- Must be explicitly documented and confirmed in `doc/README.md`.

### Invariant 3: Documentation File Placement Rule

- **All Markdown files (`.md`) must reside strictly inside the [`doc/`](file:///c:/Users/kastu/Desktop/capstone%20-%20hr/doc) directory.**
- Never create standalone `.md` files in the repository root or subfolders outside `doc/`.

### Invariant 4: Zero Binary Media Files

- One single public Git repository with **zero images, zero PDFs, zero slide decks, zero audio, and zero video files**.
- All diagrams must be generated using **Mermaid** inside Markdown documents. All schemas and tables must be plain text.

### Invariant 5: Least Autonomy Principle

- Application Layer: Only the `LookupAgent` is authorized to invoke `check_job_application_status`.
- `RetrievalAgent` is authorized for `rag_lookup` only.
- `ResponseComposer` must be wired with **zero tools**.
- Any attempt to bypass or execute an unauthorized tool must raise `SecurityGovernanceError`.

### Invariant 6: Zero PII on Persistent Storage

- Indian phone numbers (all formats) must be redacted to `[REDACTED_PHONE]` at the ingestion layer.
- Raw phone numbers must **NEVER** be written to disk, trace files, or `audit_trail.jsonl`.
- Grepping log files for phone numbers must return zero matches.

### Invariant 7: Empirical Calibration Only

- Numerical thresholds must never be hardcoded guesses (e.g. arbitrary 0.5, 0.6, or 0.7 presets).
- Similarity cutoff $T$ must be positioned mathematically between in-scope ($S_{in}$) and out-of-scope ($S_{out}$) clusters.
- Escalation threshold $\tau_{esc}$ must be computed as the 80th percentile of the generated dataset distribution.

### Invariant 8: ReAct Parser & Tool Schema Dispatch (Pitfalls A & B)

- **Pitfall A:** When parsing ReAct format, parse strictly within newly generated output tokens. Never search the full prompt or historical string for `"Observation:"`.
- **Pitfall B:** Dispatch tool calls using declared Pydantic **argument schemas** (`record_id` vs `query`), never by tool name substrings (e.g. `"lookup"`).

### Invariant 9: Autogen Structured Message Registration

- When instantiating the Autogen `RoundRobinGroupChat`, always register `custom_message_types=[StructuredMessage[Verdict]]` to prevent runtime `ValueError`.

### Invariant 10: Expected Framework Warnings

- The `LangChainDeprecationWarning` emitted by `RunnableWithMessageHistory` is an expected ecosystem signal. In accordance with problem constraints, it must **not** be silenced or hidden.

---

## 2. Python Coding & Style Guidelines

### 2.1 Code Structure & Standards

- Python Version: Target **CPython 3.12** in virtual environment [`.hr`](file:///c:/Users/kastu/Desktop/capstone%20-%20hr/.hr).
- Code Formatter: PEP 8 compliant, 4-space indentation.
- Type Annotations: Full static type hints across all function signatures, methods, and return values.

### 2.2 Schema Definitions (Pydantic v2)

- All input contracts, tool arguments, agent outputs, and API models must be defined as `pydantic.BaseModel` subclasses.
- Use explicit field validators and descriptive constraints (`ge`, `le`, `pattern`, `min_length`).

```python
class QueryInput(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000, description="Cleaned employer query")
    session_id: Optional[str] = Field(default=None, description="UUID session identifier")
```

### 2.3 Error Handling & Domain Exceptions

- Never use bare `except:` clauses.
- Catch specific exceptions (`KeyError`, `ValueError`, `WebSocketDisconnect`).
- Wrap operational failures in descriptive domain exceptions (`SecurityGovernanceError`, `BudgetExceededError`, `ContextInsufficientException`).

---

## 3. Testing & Verification Standards

### 3.1 Automated Test Suite (`tests/`)

- Every module must have a corresponding test file in `tests/`:
  - `tests/test_dataset.py`: Assert counts, weights, % flagged within 10–30%.
  - `tests/test_rag.py`: Assert chunking, embeddings, and similarity threshold.
  - `tests/test_tools.py`: Assert status lookup, escalation calculation, 80th percentile cutoff.
  - `tests/test_guardrails.py`: Assert PII masking, injection blocking, groundedness gate.
  - `tests/test_api.py`: Assert FastAPI HTTP endpoints and WebSocket disconnect recovery.
- Run tests via `pytest tests/ -v`.

### 3.2 Verification Transcripts (`transcripts/`)

- Every completed rubric task must generate an explicit verification transcript in `transcripts/` (e.g. `t1_dataset_summary.txt` to `t16_full_suite_run.txt`).
- Transcripts serve as primary submission evidence for academic evaluation.
