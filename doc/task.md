# Project Task Breakdown & Execution Board

## Naukri.com Domain Support Agent (HR & Recruitment Track)

---

## 1. Project Overview & Progress Summary

- **Track:** Recruitment & HR (Naukri.com)
- **Total Marks:** 100
- **Duration:** 14 Days
- **Current Status:** Phase 1 Initialization Completed (Architecture, PRD, Design, Memory, Rules, Edge Cases & Environment Setup).

| Part | Description | Mark Weight | Tasks | Status |
| :--- | :--- | :---: | :--- | :---: |
| **Part 1** | Dataset Design & RAG Core | 30 Marks | T1, T2, T3, T4, T5 | **In Progress** |
| **Part 2** | CrewAI Orchestration, Memory & Guardrails | 30 Marks | T6, T7, T8, T9, T10 | **Pending** |
| **Part 3** | Observability, Evaluation & FastAPI | 20 Marks | T11, T12, T13 | **Pending** |
| **Part 4** | Resilience & Governance | 20 Marks | T14, T15, T16 | **Pending** |
| **Global** | Repository Standards, Telemetry & Documentation | — | Architecture, PRD, Clean Release | **In Progress** |

---

## 2. Part 1: Dataset Design & RAG Core (30 Marks)

### Task T1: Deterministic Seeded Dataset Generation

- **Target File:** `dataset.py`
- **Schedule:** Day 2
- **Mark Weight:** 6 Marks
- **Requirements:**
  - [ ] Implement seeded generator with `random.seed(42)` generating $\ge 40$ records (target $N=50$).
  - [ ] Schema: `record_id`, `category`, `status`, `expected_salary_inr`, `days_since_created`, `flagged_priority_review`.
  - [ ] Category distribution: 5 required categories with $\ge 3$ records each.
  - [ ] Status distribution: 5 required statuses with $\ge 1$ record each.
  - [ ] Flagged proportion: Strictly between **10% and 30%** via tuned probability weights.
  - [ ] Salary range: ₹3,00,000 to ₹30,00,000 INR with documented rationale.
- **Evidence / Deliverable:**
  - CLI script printing count per category, count per status, % flagged, and salary range reasoning.
  - Transcript: `transcripts/t1_dataset_summary.txt`.

### Task T2: Knowledge Base Document Authoring

- **Target Directory:** `kb/`
- **Schedule:** Day 3
- **Mark Weight:** 6 Marks
- **Requirements:**
  - [ ] Author exactly 12 standalone policy documents (`.md`), 2–5 sentences each, covering all required topics:
    - [ ] `01_eligibility.md`: Eligibility criteria
    - [ ] `02_interview_scheduling.md`: Interview-scheduling process
    - [ ] `03_offer_negotiation.md`: Offer-negotiation policy
    - [ ] `04_background_verification.md`: Background-verification protocol
    - [ ] `05_notice_period.md`: Notice-period and buyout policy
    - [ ] `06_referral_bonus.md`: Referral-bonus scheme and eligibility
    - [ ] `07_internal_transfer.md`: Internal mobility guidelines
    - [ ] `08_probation_period.md`: Probation period and confirmation
    - [ ] `09_remote_work.md`: Remote and hybrid work guidelines
    - [ ] `10_diversity_hiring.md`: Diversity affirmative guidelines
    - [ ] `11_exit_interview.md`: Exit-interview protocol
    - [ ] `12_data_retention.md`: Applicant data retention policy
- **Evidence / Deliverable:**
  - 12 verified files in `kb/`.
  - Transcript: `transcripts/t2_kb_manifest.txt`.

### Task T3: Dual Chunking Strategies & Vector Indexing

- **Target Files:** `rag/chunking.py`, `rag/indexing.py`
- **Schedule:** Day 4
- **Mark Weight:** 6 Marks
- **Requirements:**
  - [ ] Strategy A: Fixed-size chunking (200 characters with 40-character sliding overlap).
  - [ ] Strategy B: Sentence-based syntactic boundary splitting.
  - [ ] Embeddings: Local `sentence-transformers/all-MiniLM-L6-v2`.
  - [ ] ChromaDB: Two isolated collections (`kb_fixed_overlap` and `kb_sentence_based`) loaded via `collection.upsert()`.
- **Evidence / Deliverable:**
  - Retrieval sample demonstrating queries from both collections.
  - Transcript: `transcripts/t3_indexing_sample.txt`.

### Task T4: Grounded Generation & Empirical Threshold Calibration

- **Target File:** `rag/generate.py`
- **Schedule:** Day 5
- **Mark Weight:** 6 Marks
- **Requirements:**
  - [ ] Measure cosine similarities for $\ge 3$ in-scope queries ($S_{in}$) and $\ge 2$ out-of-scope queries ($S_{out}$).
  - [ ] Empirically compute cutoff threshold: $T = \frac{\min(S_{in}) + \max(S_{out})}{2}$.
  - [ ] Restrict generation to retrieved context ONLY.
  - [ ] Trigger canonical fallback if similarity $< T$: `"I apologize, but this topic is not covered in our recruitment policy knowledge base."`
- **Evidence / Deliverable:**
  - Demonstrate $\ge 5$ in-scope grounded answers + 1 out-of-scope fallback demo.
  - Transcript: `transcripts/t4_grounded_generation_demos.txt`.

### Task T5: Chunking Strategy Precision & Recall Evaluation

- **Target File:** `rag/evaluate_chunking.py`
- **Schedule:** Day 6
- **Mark Weight:** 6 Marks
- **Requirements:**
  - [ ] Evaluate document-level precision and recall across $\ge 5$ test queries.
  - [ ] Map retrieved chunks back to `parent_doc_id` and deduplicate before calculating metrics.
  - [ ] Output per-query arithmetic tables for both collections.
  - [ ] Provide 2–3 sentence data-driven recommendation selecting the winning collection for CrewAI.
- **Evidence / Deliverable:**
  - Arithmetic tables and recommendation citing numbers.
  - Transcript: `transcripts/t5_chunking_evaluation.txt`.

---

## 3. Part 2: CrewAI Orchestration, Memory & Guardrails (30 Marks)

### Task T6: Application Status Tool & Escalation Formula

- **Target File:** `crew/tools.py`
- **Schedule:** Day 7
- **Mark Weight:** 6 Marks
- **Requirements:**
  - [ ] Implement `check_job_application_status(record_id: str) -> dict`.
  - [ ] Calculate escalation score: $S_{esc} = 0.5 \cdot (\mathbf{1}_{\text{flagged}}) + 0.5 \cdot \left(\frac{\text{days\_since\_created}}{30}\right)$.
  - [ ] Derive empirical 80th percentile threshold $\tau_{esc}$ from `dataset.py`.
  - [ ] Return status, salary, score, escalation flag, and reasoning.
- **Evidence / Deliverable:**
  - Unit tests demonstrating status lookups and escalation triggers.
  - Transcript: `transcripts/t6_status_tool_tests.txt`.

### Task T7: CrewAI Multi-Agent Team Kickoff

- **Target Files:** `llm/mock_llm.py`, `crew/agents.py`
- **Schedule:** Day 8
- **Mark Weight:** 6 Marks
- **Requirements:**
  - [ ] Extend `crewai.llms.base_llm.BaseLLM` with `MOCK_LLM` (handling Pitfalls A & B, telemetry disabled).
  - [ ] Instantiate 3 specialized agents: `RetrievalAgent` (RAG tool), `LookupAgent` (status tool), `ResponseComposer` (no tools).
  - [ ] Orchestrate via `Crew(...).kickoff()`.
- **Evidence / Deliverable:**
  - Transcripts showing RAG tool invoked on policy query and lookup tool on status query.
  - Transcript: `transcripts/t7_crew_kickoff_transcripts.txt`.

### Task T8: Multi-Turn Conversational Memory

- **Target File:** `crew/memory.py`
- **Schedule:** Day 9
- **Mark Weight:** 6 Marks
- **Requirements:**
  - [ ] Wrap pipeline with LangChain `InMemoryChatMessageHistory` and `RunnableWithMessageHistory`.
  - [ ] Transcript 1: Multi-turn session carrying conversational state and resolving pronouns.
  - [ ] Transcript 2: Separate fresh session verifying state absence and zero cross-session bleeding.
- **Evidence / Deliverable:**
  - Two contrasting transcripts.
  - Transcript: `transcripts/t8_memory_sessions.txt`.

### Task T9: Structured Response Format Validation

- **Target File:** `crew/schemas.py`
- **Schedule:** Day 9
- **Mark Weight:** 6 Marks
- **Requirements:**
  - [ ] Define Pydantic `SupportResponse` model (`query_type`, `content`, `citations`, `escalation_flag`, `confidence_score`).
  - [ ] Enforce code-level validation on 100% of crew responses.
- **Evidence / Deliverable:**
  - Validation test suite asserting schema compliance.
  - Transcript: `transcripts/t9_schema_validation.txt`.

### Task T10: Triple Guardrails Engine (Input & Output)

- **Target File:** `crew/guardrails.py`
- **Schedule:** Day 9
- **Mark Weight:** 6 Marks
- **Requirements:**
  - [ ] Input Guard 1 (PII Masking): Redact Indian phone numbers (`+91...`, 10-digit) to `[REDACTED_PHONE]`.
  - [ ] Input Guard 2 (Prompt Injection): Detect override patterns and emit security refusal.
  - [ ] Output Guard 3 (Groundedness Gate): Verify draft claims against retrieved context; refuse unsupported claims.
- **Evidence / Deliverable:**
  - One deliberate test case per guardrail, each demonstrated firing.
  - Transcript: `transcripts/t10_guardrails_firing.txt`.

---

## 4. Part 3: Observability, Evaluation & Deployment (20 Marks)

### Task T11: FastAPI Transport (HTTP & WebSocket)

- **Target File:** `api/main.py`
- **Schedule:** Day 10
- **Mark Weight:** 7 Marks
- **Requirements:**
  - [ ] Implement `POST /ask` and `POST /add-document` with Pydantic request/response models.
  - [ ] Implement real-time streaming WebSocket endpoint `@app.websocket("/ws/chat")`.
  - [ ] Handle `WebSocketDisconnect` cleanly, ensuring server process survives mid-stream disconnects.
- **Evidence / Deliverable:**
  - Test script demonstrating HTTP endpoints and surviving client disconnection.
  - Transcript: `transcripts/t11_api_and_logging.txt`.

### Task T12: Structured JSON-Lines Audit Logging

- **Target File:** `api/logging_utils.py`
- **Schedule:** Day 10
- **Mark Weight:** 6 Marks
- **Requirements:**
  - [ ] Emit one JSON-Lines record per request to `logs/audit_trail.jsonl`.
  - [ ] Include `trace_id`, `timestamp_utc`, `latency_ms`, `route`, `user_id`, `masked_prompt`, `tokens_estimated`, `status_code`.
  - [ ] Zero-PII guarantee: Logged text is masked prior to writing; raw phone numbers never hit disk.
- **Evidence / Deliverable:**
  - Audit log file inspection and phone number regex grep showing zero matches.
  - Transcript: `transcripts/t11_api_and_logging.txt`.

### Task T13: LLM-as-a-Judge 15-Query Evaluation Suite

- **Target File:** `eval/judge.py`
- **Schedule:** Day 11
- **Mark Weight:** 7 Marks
- **Requirements:**
  - [ ] Execute automated benchmark across 15 queries (12 KB topics + 2 out-of-scope + 1 adversarial injection).
  - [ ] Score each query across 4 dimensions: Accuracy, Grounding, Completeness, Safety (0–5).
  - [ ] Calculate and display per-query scores and 4 global arithmetic averages.
- **Evidence / Deliverable:**
  - Score matrix table and averages report.
  - Transcript: `transcripts/t13_judge_evaluation.txt`.

---

## 5. Part 4: Resilience & Governance (20 Marks)

### Task T14: Independent Autogen Peer-Review Stage

- **Target File:** `review/autogen_review.py`
- **Schedule:** Day 12
- **Mark Weight:** 7 Marks
- **Requirements:**
  - [ ] Implement 2-agent `RoundRobinGroupChat` (`PolicyComplianceReviewer` + `FinalEditor`), `max_turns=2`.
  - [ ] Output structured `Verdict` (`approved: bool`, `revised: bool`, `final_answer: str`, `reason: str`).
  - [ ] Register `custom_message_types=[StructuredMessage[Verdict]]` on Team.
  - [ ] Demo 1: Grounded answer approved unchanged.
  - [ ] Demo 2: Injected ungrounded claim caught and revised.
- **Evidence / Deliverable:**
  - Structured verdict transcripts for both demos.
  - Transcript: `transcripts/t14_autogen_review.txt`.

### Task T15: AI Governance & Token Budget Cap

- **Target Files:** `governance/least_autonomy.py`, `governance/budget.py`, `doc/RISK.md`
- **Schedule:** Day 13
- **Mark Weight:** 7 Marks
- **Requirements:**
  - [ ] Least Autonomy: Demonstrate security block when unauthorized agent attempts to invoke status tool.
  - [ ] Risk Classification: Complete 1-page risk assessment in `doc/RISK.md` categorizing system as **High Risk**.
  - [ ] Runtime Budget Cap: Reject oversized request ($>250$ estimated tokens) with HTTP 429.
- **Evidence / Deliverable:**
  - Guardrail demo, risk doc, and budget rejection transcript.
  - Transcript: `transcripts/t15_governance_and_cache.txt`.

### Task T16: In-Memory Deterministic Query Caching

- **Target File:** `cache.py`
- **Schedule:** Day 13
- **Mark Weight:** 6 Marks
- **Requirements:**
  - [ ] In-memory query cache keyed by normalized query hash (`SHA-256`).
  - [ ] Static KB queries use cache; dynamic status queries bypass cache.
  - [ ] Provide before/after evidence (call counter or execution latency) of repeated query hitting cache.
- **Evidence / Deliverable:**
  - Cache hit counter and timing benchmarks.
  - Transcript: `transcripts/t15_governance_and_cache.txt`.

---

## 6. Global Project Requirements Checklist

- [ ] Top line of `doc/README.md` declares: `Naukri.com (Recruitment & HR) Track`.
- [ ] `doc/README.md` documents dataset choices (seed, category weights, status weights, salary rationale).
- [ ] `doc/README.md` confirms `MOCK_LLM`, zero API keys, and `CREWAI_DISABLE_TELEMETRY=true`.
- [ ] All `.md` documentation files located strictly inside `doc/`.
- [ ] No binary media files (images, PDFs, slides, video, audio) anywhere in the repository.
- [ ] All 16 verification transcripts generated and committed to `transcripts/`.
