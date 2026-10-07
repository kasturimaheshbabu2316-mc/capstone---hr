# Problem Statement — Naukri.com Domain Support Agent (CrewAI)

**Track:** Recruitment & HR (Naukri.com) · **Duration:** 14 days · **Marks:** 100
**Deliverable:** ONE public GitHub repository (dataset, RAG core, CrewAI crew, Autogen review stage, FastAPI deployment)
**Runtime mode:** Everything must run under deterministic `MOCK_LLM` — zero API keys, zero network access.

---

## 1. Business Problem

Naukri.com's employer-support team wants an AI support agent that:

1. Answers **hiring-policy questions** from a knowledge base (KB) I write myself.
2. Looks up the **status of a specific job application** from a dataset I design and validate.
3. **Remembers** a multi-turn conversation.
4. Is **guarded** against PII leakage, prompt injection, and ungrounded answers.
5. Has every draft answer **reviewed by a second, independent agent team** (Autogen) before reaching the user.
6. Operates under an explicit **AI-governance policy** (least autonomy, risk classification, cost cap).
7. Is **deployed behind FastAPI** (HTTP + WebSocket) with structured logging and an end-to-end evaluation.

Goal: build it to the standard of a real production governance review, not a happy-path demo.

---

## 2. Scenario Vocabulary (given)

| Item | Values (use each ≥ 1×; may add more) |
| --- | --- |
| **Categories** | Software Engineer, Data Analyst, Product Manager, HR Executive, Sales Associate |
| **Statuses** | Applied, Screening, Interview Scheduled, Offered, Rejected |

**Required KB topics (12, one document each, 2–5 sentences, my own words):**

1. Job-application eligibility criteria
2. Interview-scheduling process
3. Offer-negotiation policy
4. Background-verification process
5. Notice-period policy
6. Referral-bonus policy
7. Internal-transfer eligibility
8. Probation-period policy
9. Remote-work eligibility
10. Diversity-hiring guidelines
11. Exit-interview process
12. Applicant-data-retention policy

**PII scope:**

- **Masked (must demo):** phone number in contact details (fixed format).
- **Out of scope for masking** (use fabricated examples only): candidate name, expected salary, background-check results.

---

## 3. Hard Constraints & Known Pitfalls

| # | Constraint | Action |
| --- | --- | --- |
| 1 | One repo, public, no images/PDFs/slides/video/audio | Everything is code or text |
| 2 | README top line states **Naukri.com (Recruitment & HR)** track | Add on day 1 |
| 3 | README lists dataset design choices (seed, category/status weights, salary range) | Reproducibility |
| 4 | No paid accounts; local SentenceTransformers + ChromaDB | Free stack |
| 5 | `MOCK_LLM` must work for CrewAI crew **and** Autogen team **and** judge | Extend `crewai.llms.base_llm.BaseLLM` |
| 6 | **Pitfall A:** CrewAI's ReAct template contains the literal `"Observation: the result of the action"` | Parse the model's *own generated text*, never search the whole conversation for `"Observation:"` |
| 7 | **Pitfall B:** Don't dispatch tool calls by name substring (`rag_lookup` contains `lookup`) | Dispatch on the tool's declared **argument schema** |
| 8 | CrewAI telemetry makes an outbound call | Set `CREWAI_DISABLE_TELEMETRY=true` (or `OTEL_SDK_DISABLED=true`) and **confirm in README** |
| 9 | LangChain `RunnableWithMessageHistory` emits `LangChainDeprecationWarning` | Expected; don't silence |
| 10 | Autogen: `RoundRobinGroupChat(max_turns=2)` (not `max_iterations`) | Or `MaxMessageTermination(3)` |
| 11 | Autogen structured output needs `custom_message_types=[StructuredMessage[Verdict]]` on the Team | Otherwise `ValueError: Message type ... is not registered` |

---

## 4. Work Breakdown by Part

### Part 1 — Dataset Design & RAG Core (30 marks)

| Task | What to build | Evidence required |
| --- | --- | --- |
| **T1** Dataset | `dataset.py`: seeded, deterministic `JOB_APPLICATIONS` (≥40). Fields: `record_id`, `category`, `status`, `expected_salary_inr`, `days_since_created` (int 0–30), `flagged_priority_review` (bool) | Print count/category (each given ≥3), count/status (each ≥1), % flagged (**10–30%**). If outside band: change seed/weights, **never hand-edit**. One-sentence salary-range reasoning. |
| **T2** KB | 12+ docs, 2–5 sentences each, covering every topic above | Files in `kb/` |
| **T3** Chunking + indexing | (a) fixed-size with overlap, (b) sentence-based. Embed with free SentenceTransformers model. **Two separate ChromaDB collections** via `upsert()` | Sample query retrieval from both |
| **T4** Grounded generation | Top-k retrieval → answer from retrieved context ONLY. **Empirically calibrate** "I don't know" threshold | Measure top-1 cosine for ≥3 in-scope + ≥2 out-of-scope queries; set threshold *between* observed clusters (no 0.5/0.6/0.7 presets). Demo ≥5 in-scope + 1 out-of-scope (fallback fires). Record numbers in README. |
| **T5** Chunking evaluation | Document-level precision & recall (map chunks → parent doc, dedup) per collection, same ≥5 queries | Per-query arithmetic shown for **both** collections + 2–3 sentence recommendation citing both sets of numbers |

### Part 2 — CrewAI Orchestration, Memory & Guardrails (30 marks)

| Task | What to build | Evidence required |
| --- | --- | --- |
| **T6** Status tool | `check_job_application_status(record_id) -> dict` returning `status`, `expected_salary_inr`, `escalation_score ∈ [0,1]` | Designed formula combining `flagged_priority_review` + normalized recency from `days_since_created` (not a bare boolean OR). State formula + escalation threshold justified from own data distribution (e.g., 80th percentile). |
| **T7** Crew | ≥3 agents: **Retrieval Agent** (RAG tool), **Lookup Agent** (status tool), **Response Composer**. Run with `.kickoff()` | Transcripts showing RAG tool invoked on one query and lookup tool on a different query |
| **T8** Session memory | LangChain `InMemoryChatMessageHistory` + `RunnableWithMessageHistory` | Transcript 1: multi-turn state carried. Transcript 2 (separate): fresh conversation shows state absent |
| **T9** Structured output | Pydantic `BaseModel` as `response_format` | Code-level validation of **every** crew response |
| **T10** Guardrails | Input: PII masking (phone number), prompt-injection detection. Output: groundedness check that refuses when context doesn't support the question | One deliberate test case per guardrail, each shown firing |

### Part 3 — Evaluation, Observability & FastAPI (20 marks)

| Task | What to build | Evidence required |
| --- | --- | --- |
| **T11** FastAPI | ≥2 HTTP endpoints (e.g., `POST /ask`, `POST /add-document`) with Pydantic request/response models + 1 WebSocket (`@app.websocket`) | WebSocket catches `WebSocketDisconnect`, server keeps serving others; demo a mid-conversation disconnect |
| **T12** Structured logging | One JSON-Lines entry per request: trace ID + timing | Logged text is **masked** (same masker as model input) — raw phone number never on disk |
| **T13** Evaluation | LLM-as-judge (under `MOCK_LLM`), **15 queries**: ≥1 per KB topic (12) + ≥2 out-of-scope/edge | Per-query scores for Accuracy, Grounding, Completeness, Safety + 4 averages |

### Part 4 — Resilience & Governance (20 marks)

| Task | What to build | Evidence required |
| --- | --- | --- |
| **T14** Autogen review | 2-agent `RoundRobinGroupChat` (Policy-Compliance-Reviewer + Final-Editor), `max_turns=2`. Final-Editor uses `output_content_type=Verdict` (`approved: bool`, `final_answer: str`, `reason: str`). Input: Composer draft + original retrieved context | ≥2 demos: one **approved unchanged**, one **revised** (deliberately inject an ungrounded claim). Both show structured verdicts |
| **T15** Governance | **Application layer:** least autonomy — only Lookup Agent may call the status tool; demonstrate the guard (blocked or never wired) + one-paragraph explanation. Risk classification (Low/Medium/High) with one-paragraph justification. **Runtime layer:** per-request token/cost budget cap | Oversized request visibly **rejected**. (Expected classification: **High** — hiring decisions.) |
| **T16** Caching | In-memory cache keyed by normalized query for the grounded-generation step | Before/after evidence (call counter or timing) of a repeated query hitting cache |

---

## 5. Acceptance Criteria Checklist

**Part 1**

- [ ] `dataset.py` ≥40 records; category ≥3 each; status ≥1 each; flagged % in 10–30%; choices in README
- [ ] ≥12 KB docs covering all required topics
- [ ] Two chunking strategies → two separate ChromaDB collections, both retrieve sensibly
- [ ] ≥5 in-scope grounded answers + 1 out-of-scope fallback
- [ ] Precision/recall for both collections, per-query arithmetic, numbers-cited recommendation

**Part 2**

- [ ] Status tool with designed, justified `escalation_score`
- [ ] Crew ≥3 agents; both tools invoked on different queries via `.kickoff()`
- [ ] Multi-turn memory + separate fresh-conversation transcript
- [ ] Every response validates against Pydantic schema
- [ ] PII, injection, and groundedness guardrails each demonstrated firing

**Part 3**

- [ ] ≥2 HTTP endpoints + 1 WebSocket surviving disconnect
- [ ] JSON-Lines log with trace ID per request, PII masked
- [ ] 15-query eval with 4 scores each + 4 averages

**Part 4**

- [ ] Autogen: approve-unchanged and revise demos with structured verdicts
- [ ] Least autonomy demonstrated; risk classification justified; budget cap rejects oversized request
- [ ] Cache hit with before/after evidence

**Global**

- [ ] README top line: Naukri.com (Recruitment & HR) track
- [ ] README confirms `MOCK_LLM`, zero API keys, and `CREWAI_DISABLE_TELEMETRY=true`
- [ ] No images/PDFs/slides/video/audio anywhere

---

## 6. Proposed Repository Structure

```
naukri-support-agent/
├── README.md                  # track, dataset choices, thresholds, telemetry note, how to run
├── problemStatement.md
├── requirements.txt
├── dataset.py                 # T1
├── kb/                        # T2: 12+ .txt/.md docs
├── rag/
│   ├── chunking.py            # T3: fixed-overlap + sentence
│   ├── indexing.py            # T3: two Chroma collections
│   ├── generate.py            # T4: grounded generation + threshold
│   └── evaluate_chunking.py   # T5: precision/recall
├── llm/
│   └── mock_llm.py            # BaseLLM subclass (handles pitfalls A & B)
├── crew/
│   ├── tools.py               # T6 + RAG tool
│   ├── agents.py              # T7
│   ├── memory.py              # T8
│   ├── schemas.py             # T9 (+ Autogen Verdict)
│   └── guardrails.py          # T10
├── review/
│   └── autogen_review.py      # T14
├── governance/
│   ├── least_autonomy.py      # T15
│   ├── budget.py              # T15
│   └── RISK.md                # T15 risk classification
├── cache.py                   # T16
├── api/
│   ├── main.py                # T11
│   └── logging_utils.py       # T12
├── eval/
│   └── judge.py               # T13
├── transcripts/               # one per task
└── tests/
```

---

## 7. 14-Day Plan

| Days | Focus | Output |
| --- | --- | --- |
| **1** | Setup, venv, repo, env vars, README skeleton | Repo skeleton + telemetry flag |
| **2** | T1 dataset (tune seed until flagged % lands in band) | `dataset.py` + printed stats |
| **3** | T2 KB authoring | 12 docs |
| **4** | T3 chunking + two Chroma collections | Indexed collections |
| **5** | T4 threshold calibration + grounded generation | Measured similarity table + demos |
| **6** | T5 precision/recall + recommendation | Arithmetic tables |
| **7** | T6 tool + escalation formula; **MOCK_LLM BaseLLM** (budget extra time; pitfalls A & B) | Tool + working mock LLM |
| **8** | T7 crew (3 agents, both tools invoked) | `.kickoff()` transcripts |
| **9** | T8 memory + T9 schema + T10 guardrails | Transcripts + firing demos |
| **10** | T11 FastAPI HTTP + WebSocket + T12 logging | Working server, JSONL logs |
| **11** | T13 evaluation (15 queries) | Score table + averages |
| **12** | T14 Autogen review (approve + revise) | Structured verdict transcripts |
| **13** | T15 governance + T16 cache | Guard demo, risk doc, budget rejection, cache evidence |
| **14** | Full clean run from scratch, README polish, final checklist, submit | Public repo link |

---

## 8. Key Design Decisions to Make Early

1. **Seed & weights** — pick, run, check flagged % (10–30%); iterate on seed/weights only.
2. **Salary range reasoning** — e.g., ₹3L–₹30L annual, spanning entry-level Sales Associate to senior Software Engineer/Product Manager.
3. **Escalation formula** — e.g., `score = 0.5·flagged + 0.5·(days_since_created / 30)`, threshold at the 80th percentile of the generated data (verify against the actual distribution).
4. **Similarity threshold** — measured, not assumed; record the in-scope vs out-of-scope clusters.
5. **Which collection feeds the crew** — whichever strategy wins in T5.
6. **Budget cap** — a fixed token ceiling per request (e.g., estimated tokens = chars/4), with a clear rejection message.
7. **Risk level** — High (hiring decisions + applicant data), justified in one paragraph.

---

## 9. Risks & Mitigations

| Risk | Mitigation |
| --- | --- |
| Mock LLM silently returns placeholder text (Pitfall A) | Unit test: assert final answer ≠ template text |
| Tool misrouted by name matching (Pitfall B) | Dispatch on arg schema; test with `rag_lookup` |
| Telemetry network call | Env var set before import; documented |
| Autogen `ValueError` on structured message | Register `custom_message_types` on Team |
| Flagged % out of band | Tune seed/weights, regenerate; never hand-edit |
| Raw phone number in logs | Mask before logging; test by grepping log file |
| Hidden dependency on network (model download) | Pre-download SentenceTransformers model; note in README |
| Demo gaps at submission | Final-day checklist (Section 5) against transcripts |
