# Product Requirements Document (PRD)

## Naukri.com Domain Support Agent (HR & Recruitment Track)

---

## 1. Product Overview & Strategic Rationale

The **Naukri.com Domain Support Agent** is a multi-agent AI system built to automate enterprise employer-support operations for Naukri.com. The product resolves two mission-critical recruitment operational challenges:

1. **Recruitment Policy Consultation:** Instantaneous, authoritative answers to employer and recruiter questions regarding hiring guidelines, notice buyout policies, background verification protocols, and internal transfers from an authoritative, curated knowledge base.
2. **Applicant Tracking System (ATS) Status Intelligence:** Automated status queries for candidate job applications, enriched with an empirical escalation risk score to flag stalled or high-priority applications for urgent human HR intervention.

### Operational Constraints & Invariants

- **100% Deterministic & Offline:** The system functions entirely under a custom `MOCK_LLM` extending `crewai.llms.base_llm.BaseLLM`. Zero live network calls, zero external API keys, zero outbound telemetry.
- **Audited Dual-Team Architecture:** Primary multi-agent orchestration performed by **CrewAI** (3 specialized agents), followed by an independent peer-review stage performed by **Autogen** (2-agent group chat) emitting structured Pydantic verdicts before user delivery.
- **Enterprise AI Governance:** Least Autonomy tool binding, high-risk classification under employment regulations, and strict pre-execution token budget caps.
- **Privacy & Safety:** Real-time masking of Indian phone numbers in contact data, rule-based prompt injection detection, and groundedness refusal gates.

---

## 2. Target Personas & User Journeys

### Persona 1: Enterprise Recruiter (Primary User)

- **Role:** High-volume technical and non-technical talent acquisition specialist at a client firm using Naukri.com.
- **Goals:** Quickly check status of pending applicants without navigating complex ATS database views; clarify buyout or probation confirmation policies.
- **Pain Point:** Delayed support responses leading to candidate drop-offs during offer negotiation or background verification.

### Persona 2: Employer HR Operations Lead

- **Role:** Centralized operations manager responsible for policy compliance and recruitment SLA adherence.
- **Goals:** Ensure hiring teams adhere to internal mobility and notice buyout thresholds; identify candidate applications that require priority escalation.
- **Pain Point:** Inconsistent policy interpretation and ungrounded recruiter decisions.

### Persona 3: Naukri Platform Administrator / AI Governance Auditor

- **Role:** Platform compliance officer responsible for AI safety, auditability, and regulatory compliance.
- **Goals:** Guarantee that candidate data is never leaked (PII masking), model hallucinations are intercepted before reaching employers, and all queries are logged with trace IDs.
- **Pain Point:** Lack of transparent audit trails and unauthorized tool execution in agentic pipelines.

---

## 3. Functional Requirements (FR)

### FR1: Knowledge Base Ingestion & Dual RAG Pipeline

- The system must ingest exactly 12 required recruitment policy topics (2–5 sentences each) authored for Naukri.com.
- The system must support two distinct chunking strategies:
  - Strategy A: Fixed-size chunking (200 characters with 40-character sliding overlap).
  - Strategy B: Sentence-based syntactic splitting.
- The system must maintain two isolated collections in ChromaDB (`kb_fixed_overlap` and `kb_sentence_based`) embedded with local `sentence-transformers/all-MiniLM-L6-v2`.
- Grounded generation must be calibrated using an empirical cosine similarity cutoff $T$ positioned between in-scope ($S_{in}$) and out-of-scope ($S_{out}$) clusters.

### FR2: Deterministic Applicant Dataset Generation

- The system must generate a reproducible dataset (`JOB_APPLICATIONS`) of $\ge 40$ records (seeded with `random.seed(42)`).
- The dataset must contain all 5 required categories with $\ge 3$ records each: `Software Engineer`, `Data Analyst`, `Product Manager`, `HR Executive`, `Sales Associate`.
- The dataset must contain all 5 required statuses with $\ge 1$ record each: `Applied`, `Screening`, `Interview Scheduled`, `Offered`, `Rejected`.
- Flagged priority records (`flagged_priority_review`) must strictly comprise **10% to 30%** of total generated records.
- Expected salary values must span ₹3,00,000 to ₹30,00,000 INR with clear domain justification.

### FR3: Application Status & Escalation Scoring Tool

- The system must provide `check_job_application_status(record_id: str) -> dict`.
- The tool must compute an escalation score:
  $$S_{esc} = 0.5 \cdot (\mathbf{1}_{\text{flagged}}) + 0.5 \cdot \left(\frac{\text{days\_since\_created}}{30}\right)$$
- If $S_{esc} \ge \tau_{esc}$ (where $\tau_{esc}$ is the empirical 80th percentile of the dataset distribution), `escalation_triggered` must be set to `True`.

### FR4: CrewAI Multi-Agent Team Orchestration

- The primary system must instantiate 3 specialized CrewAI agents:
  1. `RetrievalAgent`: Policy librarian provisioned exclusively with `rag_lookup`.
  2. `LookupAgent`: ATS specialist provisioned exclusively with `check_job_application_status`.
  3. `ResponseComposer`: HR communications synthesizer provisioned with zero tools (least autonomy).
- Execution must run deterministically via `Crew(...).kickoff()`.

### FR5: Conversational State & Session Memory

- The system must maintain multi-turn conversational context using LangChain's `InMemoryChatMessageHistory` with `RunnableWithMessageHistory`.
- The system must accurately resolve pronouns across turns (e.g. `"What was their salary?"` following a status query).
- Separate sessions must maintain complete memory isolation with zero cross-session bleeding.

### FR6: Structured Output Enforcement

- Every CrewAI response must be strictly validated against the Pydantic `SupportResponse` schema containing `query_type`, `content`, `citations`, `escalation_flag`, and `confidence_score`.

### FR7: Enterprise Guardrails (Input & Output)

- **Input Guard 1 (PII Masking):** Automatically detect and mask Indian phone numbers (`+91...`, space-separated, 10-digit) to `[REDACTED_PHONE]`. Synthetic salaries and candidate names must be preserved.
- **Input Guard 2 (Prompt Injection):** Detect system overrides, jailbreak strings, and delimiter escapes; immediately halt and emit a security refusal.
- **Output Guard 3 (Groundedness Gate):** Refuse to answer queries where retrieved context similarity $< T$ or context does not support the claim.

### FR8: Independent Autogen Peer-Review Stage

- Following CrewAI drafting, every draft response and original retrieved context must be audited by an independent 2-agent Autogen group chat (`RoundRobinGroupChat`, `max_turns=2`).
- Agents: `PolicyComplianceReviewer` (audits grounding and compliance) and `FinalEditor` (synthesizes verdict and corrections).
- Output: Strict Pydantic `Verdict` (`approved: bool`, `revised: bool`, `final_answer: str`, `reason: str`) wrapped in `StructuredMessage[Verdict]` with registered custom message types.

### FR9: AI Governance & Gateway Controls

- **Least Autonomy Enforcement:** Enforce role-based tool restrictions at the application layer. Unauthorized tool wiring or execution must raise `SecurityGovernanceError`.
- **Runtime Budget Ceiling:** Gateway filter estimating prompt tokens ($E_{tokens} = \lceil \text{chars}/4 \rceil$). If $> 250$ tokens, reject immediately with HTTP 429.
- **AI Risk Profile:** Categorized as **High Risk** under recruitment AI regulations, supported by a formal risk assessment.

### FR10: High-Performance Transport & Streaming

- Synchronous HTTP endpoints: `POST /ask` and `POST /add-document`.
- Real-time streaming WebSocket endpoint: `@app.websocket("/ws/chat")`.
- Resilient disconnect recovery: Catch `WebSocketDisconnect` cleanly without process crashes or resource leaks.

### FR11: Zero-PII Structured Audit Logging

- Emits one JSON-Lines record per request into `logs/audit_trail.jsonl`.
- Logs include `trace_id`, `timestamp_utc`, `latency_ms`, `route`, `user_id`, `masked_prompt`, `guardrail_status`, `cache_hit`, and `status_code`.
- Raw phone numbers must never touch disk under any circumstance.

### FR12: In-Memory Query Caching

- Grounded KB queries must be cached in memory using canonical query normalization and `SHA-256` hashing.
- Dynamic applicant status queries must bypass cache.
- Telemetry must measure and verify sub-millisecond $O(1)$ response times on cache hits.

---

## 4. Non-Functional Requirements (NFR)

### NFR1: Determinism & Offline Operation

- 100% of pipeline tests and benchmarks must pass without an internet connection or external API keys.
- Outbound telemetry must be suppressed via `CREWAI_DISABLE_TELEMETRY=true` and `OTEL_SDK_DISABLED=true`.

### NFR2: Latency & Performance

- In-memory cache hits must return within $< 1$ millisecond.
- Cold query execution through CrewAI and Autogen under `MOCK_LLM` must complete within $< 500$ milliseconds.

### NFR3: Availability & Fault Tolerance

- Mid-conversation WebSocket disconnections must not degrade server performance or crash worker threads.
- Server must recover gracefully from malformed JSON payloads and invalid schema arguments.

### NFR4: Precision & Retrieval Quality

- Both chunking strategies must be evaluated for document-level precision and recall with deduplicated parent doc IDs.
- The winning strategy must demonstrate higher harmonic mean (F1 score) across the benchmark query suite.

---

## 5. 100-Mark Rubric Verification Mapping

| Part | Marks | Key PRD Requirements Verified |
| :--- | :---: | :--- |
| **Part 1: Dataset & RAG Core** | **30 Marks** | `dataset.py` ($\ge 40$ records, 10–30% flagged, choices justified), 12 KB docs, dual Chroma collections via `upsert()`, empirical threshold $T$, precision/recall arithmetic tables. |
| **Part 2: CrewAI, Memory & Guardrails** | **30 Marks** | Status tool with $S_{esc}$ and 80th percentile threshold, 3 CrewAI agents via `.kickoff()`, multi-turn memory + isolated session, `SupportResponse` schema, 3 firing guardrail demos. |
| **Part 3: Deployment & Evaluation** | **20 Marks** | FastAPI HTTP endpoints, WebSocket surviving disconnect, zero-PII JSON-Lines logging with trace IDs, 15-query LLM judge scoring (Accuracy, Grounding, Completeness, Safety). |
| **Part 4: Resilience & Governance** | **20 Marks** | Autogen review with structured verdicts (approved + revised demos), Least Autonomy block, High-Risk doc, budget cap HTTP 429 rejection, query cache before/after evidence. |
| **Total** | **100 Marks** | **Fully Satisfied & Documented in `doc/`** |
