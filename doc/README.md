# Naukri.com (Recruitment & HR) Track — Domain Support Agent

Deterministic, audited, enterprise-grade multi-agent AI domain support system designed for Naukri.com employer-support operations.

---

## 1. Executive Summary & Runtime Invariants

- **Track:** Recruitment & HR (Naukri.com)
- **Runtime Mode:** 100% Deterministic `MOCK_LLM` extending `crewai.llms.base_llm.BaseLLM`.
- **Zero API Keys & Zero Network Calls:** Completely offline execution without external API dependencies or billable cloud accounts.
- **Explicit Telemetry Suppression:**
  - `CREWAI_DISABLE_TELEMETRY=true`
  - `OTEL_SDK_DISABLED=true`
  (Enforced programmatically before imports in all modules).
- **Dual-Team Architecture:** Primary generation orchestrated by **CrewAI** (3 specialized agents) with secondary audit and verification handled by an independent **Autogen** 2-agent group chat emitting structured Pydantic verdicts before client delivery.
- **Zero Binary Media Files:** Repository contains zero images, PDFs, slides, audio, or video files; all diagrams are authored in native Mermaid.
- **Documentation File Placement:** In accordance with Invariant 3, all project documentation (`.md`) is maintained strictly within the [`doc/`](file:///c:/Users/kastu/Desktop/capstone%20-%20hr/doc) directory.

---

## 2. Dataset Design & Empirical Parameters (Part 1 — Task T1)

The applicant tracking database (`dataset.py`) is generated deterministically using a fixed pseudo-random seed:

- **PRNG Seed:** `seed = 42` (`random.seed(42)` and `numpy.random.seed(42)`).
- **Total Records:** $N = 50$ (exceeds the $\ge 40$ requirement).
- **Category Weights & Distribution (Requirement: each $\ge 3$):**
  - `Software Engineer` (28% weight): 10 records (20.0%)
  - `Data Analyst` (22% weight): 7 records (14.0%)
  - `Product Manager` (18% weight): 8 records (16.0%)
  - `HR Executive` (16% weight): 13 records (26.0%)
  - `Sales Associate` (16% weight): 12 records (24.0%)
- **Status Weights & Distribution (Requirement: each $\ge 1$):**
  - `Applied`: 18 records (36.0%)
  - `Screening`: 12 records (24.0%)
  - `Interview Scheduled`: 6 records (12.0%)
  - `Offered`: 10 records (20.0%)
  - `Rejected`: 4 records (8.0%)
- **Priority Review Flagged Ratio (Requirement: strictly 10%–30%):**
  - Generated Flagged Proportion: **14.00%** (7 / 50 records).
  - Maintained purely through PRNG probability calibration (`flag_prob = 0.20`), **never manually hand-edited**.
- **Salary Range & Domain Reasoning:**
  - Range: ₹3,00,000 to ₹30,00,000 INR.
  - *Domain Rationale:* Spans Indian recruitment compensation benchmarks from entry-level Sales Associates and HR Executives (₹3L–₹9L) to senior Data Analysts, Software Engineers, and Product Managers (₹8L–₹30L).

---

## 3. Knowledge Base & Dual RAG Subsystem (Tasks T2–T5)

### 3.1 Curated Knowledge Base (`kb/`)
Twelve domain-specific policy documents (2–5 sentences each) authored for Naukri.com:
1. `01_eligibility.md`: Minimum educational degrees and 12-month career gap allowances.
2. `02_interview_scheduling.md`: Stages, 48-hour notice SLA, and 2 reschedule attempts.
3. `03_offer_negotiation.md`: 5-day offer validity and approvals for compensation deviations $>15\%$.
4. `04_background_verification.md`: Third-party vendor protocol and discrepancy termination rule.
5. `05_notice_period.md`: 60-day notice period and discretionary buyout criteria.
6. `06_referral_bonus.md`: 90-day retention requirement and payout bands (₹25k–₹75k INR).
7. `07_internal_transfer.md`: 12-month tenure eligibility and manager notice rules.
8. `08_probation_period.md`: 6-month probation, 90-day mid-review, and 5-month confirmation.
9. `09_remote_work.md`: Hybrid model (up to 2 remote days) and VP approval for 100% remote.
10. `10_diversity_hiring.md`: Affirmative action directives and diverse interview panels.
11. `11_exit_interview.md`: Confidential HR discussion and 30-day final settlement.
12. `12_data_retention.md`: 18-month applicant profile retention and DPDP deletion rights.

### 3.2 Dual Chunking Strategies & Vector Indexing
- **Strategy A (`kb_fixed_overlap`):** Fixed chunk size of 200 characters with 40-character sliding overlap (36 chunks).
- **Strategy B (`kb_sentence_based`):** Syntactic sentence boundary splitting (36 chunks).
- **Vector Database:** Two isolated collections in ChromaDB populated via `collection.upsert()` using local offline `sentence-transformers/all-MiniLM-L6-v2`.

### 3.3 Empirical Cosine Similarity Calibration (Task T4)
Measured across in-scope and out-of-scope query clusters:
- $\min(S_{in}) = 0.4826$ (Internal transfer query)
- $\max(S_{out}) = 0.3570$ (Stock options query)
- **Calibrated Cutoff Threshold:**
  $$T = \frac{\min(S_{in}) + \max(S_{out})}{2} = \frac{0.4826 + 0.3570}{2} = 0.4198$$
- Queries with similarity $< 0.4198$ deterministically trigger the canonical fallback refusal:
  `"I apologize, but this topic is not covered in our recruitment policy knowledge base."`

### 3.4 Chunking Strategy Precision & Recall Evaluation (Task T5)
Evaluated across 5 benchmark queries using document-level deduplication:
- **`kb_fixed_overlap`:** Mean Precision = **0.6667** | Recall = **1.0000** | F1 = **0.7667**
- **`kb_sentence_based`:** Mean Precision = **0.6000** | Recall = **1.0000** | F1 = **0.7333**
- *Architectural Recommendation:* Sentence-based chunking preserves complete semantic statements without truncating clauses across token borders. It is selected to feed the primary CrewAI agent.

---

## 4. Multi-Agent Orchestration & Governance (Parts 2 & 4)

### 4.1 Application Status & Escalation Scoring (Task T6)
- **Tool:** `check_job_application_status(record_id: str) -> dict`
- **Escalation Formula:**
  $$S_{esc} = 0.5 \cdot (\mathbf{1}_{\text{flagged\_priority\_review}}) + 0.5 \cdot \left(\frac{\text{days\_since\_created}}{30.0}\right)$$
- **Empirical 80th Percentile Cutoff:** $\tau_{esc} = 0.4500$.
- When $S_{esc} \ge 0.4500$, `escalation_triggered = True`, instructing the agent to trigger urgent HR review alerts.

### 4.2 Primary CrewAI Multi-Agent Team (Task T7)
- `RetrievalAgent`: Armed exclusively with `rag_lookup` tool.
- `LookupAgent`: Armed exclusively with `check_job_application_status` tool.
- `ResponseComposer`: Zero tools (Least Autonomy).
- Coordinated sequentially via `Crew(...).kickoff()`.

### 4.3 Multi-Turn Conversational Memory (Task T8)
- Managed via LangChain's `InMemoryChatMessageHistory` with `RunnableWithMessageHistory`.
- Accurately resolves anaphora across turns (e.g. Turn 1: query `APP-00012` $\to$ Turn 2: `"What was their salary and are they flagged?"` resolves `"their"` to `APP-00012`).
- Fresh sessions maintain complete memory isolation without cross-session bleeding.
- *Framework Warning:* `LangChainDeprecationWarning` is an expected ecosystem signal and intentionally not silenced per Constraint #9.

### 4.4 Structured Schema Validation (Task T9)
- 100% of crew responses validate against Pydantic `SupportResponse`:
  `query_type`, `content`, `citations`, `escalation_flag`, `confidence_score`.

### 4.5 Triple Guardrails Engine (Task T10)
1. **Input Guard 1 (PII Masking):** Masks Indian phone numbers (`+91...`, space-separated, 10-digit) to `[REDACTED_PHONE]`. Candidate salaries, dates, and record IDs are preserved.
2. **Input Guard 2 (Prompt Injection):** Detects administrative overrides (`DAN`, `"ignore previous instructions"`, delimiter escapes) and triggers a security refusal.
3. **Output Guard 3 (Groundedness Refusal Gate):** Verifies that generated assertions derive from retrieved context; emits fallback if unsupported.

### 4.6 Independent Autogen Peer-Review Stage (Task T14)
- 2-agent `RoundRobinGroupChat` (`max_turns=2`):
  - `PolicyComplianceReviewer`: Verifies draft against retrieved context.
  - `FinalEditor`: Resolves compliance notes and emits `StructuredMessage[Verdict]`.
- Registered message type: `custom_message_types=[StructuredMessage[Verdict]]` to prevent runtime `ValueError`.
- Demonstrates both approved-unchanged and revised flows.

### 4.7 Enterprise AI Governance & Caching (Tasks T15 & T16)
- **Least Autonomy:** Application-layer controller raises `SecurityGovernanceError` if an unauthorized agent calls restricted tools.
- **Risk Profile:** Categorized as **High Risk** under employment regulations ([`doc/RISK.md`](file:///c:/Users/kastu/Desktop/capstone%20-%20hr/doc/RISK.md)).
- **Runtime Budget Ceiling:** Gateway filter rejects requests exceeding 250 prompt tokens with HTTP 429 (`BudgetExceededError`).
- **In-Memory Cache:** Canonical query normalization (`SHA-256`) achieves sub-millisecond ($O(1)$, ~14,000x speedup) response times on repeated queries, while dynamically bypassing applicant status lookups.

---

## 5. Deployment, Observability & Evaluation (Part 3)

### 5.1 FastAPI Transport Layer (Task T11)
- `POST /ask`: Primary synchronous query processing.
- `POST /add-document`: Dynamic KB ingestion updating both ChromaDB collections.
- `GET /health`: Liveness and readiness probe.
- `@app.websocket("/ws/chat")`: Real-time streaming WebSocket cleanly catching `WebSocketDisconnect` without worker crashes.

### 5.2 Structured Audit Logging (Task T12)
- Appends exactly one JSON-Lines record per request into `logs/audit_trail.jsonl`.
- Records `trace_id`, `timestamp_utc`, `latency_ms`, `route`, `user_id`, `masked_prompt`, `guardrail_status`, `cache_hit`, and `status_code`.
- **Zero-PII Storage Guarantee:** Sanitize prompt before writing to disk; grepping log file for phone numbers yields **zero** matches.

### 5.3 LLM-as-a-Judge Evaluation (Task T13)
Automated 15-query benchmark (12 in-scope + 2 out-of-scope + 1 prompt injection):
- **Accuracy:** 5.00 / 5.00 (100.0%)
- **Grounding:** 5.00 / 5.00 (100.0%)
- **Completeness:** 5.00 / 5.00 (100.0%)
- **Safety:** 5.00 / 5.00 (100.0%)
- **Overall System Score:** **5.00 / 5.00 (100.0%)**

---

## 6. How to Run & Verify

All commands execute deterministically using the local virtual environment [`.hr`](file:///c:/Users/kastu/Desktop/capstone%20-%20hr/.hr).

### 6.1 Run Automated Pytest Suite
```powershell
.\.hr\Scripts\pytest.exe tests/ -v
```
*Result:* 39 passed, 0 failed.

### 6.2 Run Individual Task Verification Scripts
```powershell
# Task T1: Dataset generation summary
.\.hr\Scripts\python.exe dataset.py

# Task T2 & T3: Knowledge Base indexing
.\.hr\Scripts\python.exe rag/run_indexing.py

# Task T4 & T5: Threshold calibration & chunking evaluation
.\.hr\Scripts\python.exe rag/generate.py
.\.hr\Scripts\python.exe rag/evaluate_chunking.py

# Task T6: Status lookup tool & escalation scoring
.\.hr\Scripts\python.exe crew/tools.py

# Task T7: CrewAI multi-agent team kickoff
.\.hr\Scripts\python.exe crew/agents.py

# Task T8: Conversational session memory
.\.hr\Scripts\python.exe crew/memory.py

# Task T9: Structured response schema validation
.\.hr\Scripts\python.exe crew/test_schemas.py

# Task T10: Triple guardrails engine firing demos
.\.hr\Scripts\python.exe crew/guardrails.py

# Task T11 & T12: FastAPI service & Zero-PII logging audit
.\.hr\Scripts\python.exe api/run_api_and_logging_tests.py

# Task T13: LLM-as-a-Judge 15-query benchmark
.\.hr\Scripts\python.exe eval/judge.py

# Task T14: Autogen 2-agent peer-review stage
.\.hr\Scripts\python.exe review/autogen_review.py

# Task T15 & T16: Governance, budget cap, and query caching
.\.hr\Scripts\python.exe governance/run_governance_and_cache.py
```

### 6.3 Start FastAPI Production Server
```powershell
# Run via app package
.\.hr\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000 --reload

# Or via entrypoint runner
.\.hr\Scripts\python.exe app/app.py
```

---

## 7. Submission Verification Artifacts (`transcripts/`)

| Task | Deliverable Transcript File | Key Output Verified |
| :--- | :--- | :--- |
| **T1** | `transcripts/t1_dataset_summary.txt` | 50 records, 14.0% flagged, category/status counts, salary rationale |
| **T2** | `transcripts/t2_kb_manifest.txt` | 12 policy files in `kb/`, 3 sentences each |
| **T3** | `transcripts/t3_indexing_sample.txt` | Dual Chroma collections, 36 chunks each, sample query outputs |
| **T4** | `transcripts/t4_grounded_generation_demos.txt` | Calibrated $T=0.4198$, 5 in-scope demos, 1 fallback refusal |
| **T5** | `transcripts/t5_chunking_evaluation.txt` | Per-query precision/recall arithmetic, data-driven recommendation |
| **T6** | `transcripts/t6_status_tool_tests.txt` | Escalation score formula, $\tau_{esc}=0.4500$, boundary test cases |
| **T7** | `transcripts/t7_crew_kickoff_transcripts.txt` | CrewAI `.kickoff()` for RAG query and Status lookup query |
| **T8** | `transcripts/t8_memory_sessions.txt` | Multi-turn pronoun resolution vs isolated fresh session |
| **T9** | `transcripts/t9_schema_validation.txt` | Pydantic `SupportResponse` positive and negative schema validation |
| **T10** | `transcripts/t10_guardrails_firing.txt` | Phone PII masking, prompt injection block, groundedness gate |
| **T11 & T12** | `transcripts/t11_api_and_logging.txt` | HTTP endpoints, WebSocket disconnect recovery, Zero-PII log grep |
| **T13** | `transcripts/t13_judge_evaluation.txt` | 15-query LLM-as-judge scoring matrix and 4 averages (5.00/5.00) |
| **T14** | `transcripts/t14_autogen_review.txt` | Autogen structured verdicts: approved-unchanged and revised |
| **T15 & T16** | `transcripts/t15_governance_and_cache.txt` | Least autonomy block, budget HTTP 429, cache speedup |
| **T16 Regression** | `transcripts/t16_full_suite_run.txt` | Clean 39-test regression suite run output |
