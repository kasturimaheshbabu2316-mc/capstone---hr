"""FastAPI Deployment Service for Naukri.com Support Agent.

Track: Recruitment & HR (Naukri.com)
Part 3 - Task T11: FastAPI Transport (HTTP POST /ask, POST /add-document, WebSocket /ws/chat)
Part 3 - Task T12: Masked JSON-Lines Audit Logging
"""

import os
import sys
import time
import uuid
import re
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Invariant 2: Explicit telemetry suppression
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"

from governance.budget import TokenBudgetValidator, BudgetExceededError
from governance.least_autonomy import SecurityGovernanceError
from crew.guardrails import PIIMaskingEngine, PromptInjectionDetector, SECURITY_REFUSAL_MESSAGE
from crew.memory import ConversationalSessionPipeline
from crew.tools import check_job_application_status_fn, get_shared_index_manager
from rag.generate import GroundedGenerator, FALLBACK_REFUSAL_TEXT
from review.autogen_review import AutogenReviewPipeline
from cache import QueryCache
from app.logging_utils import audit_logger


app = FastAPI(
    title="Naukri.com Domain Support Agent API",
    description="Deterministic HR & Recruitment Multi-Agent Support Service",
    version="1.0.0",
)

# Global singleton pipelines
session_pipeline = ConversationalSessionPipeline()
query_cache = QueryCache()
autogen_pipeline = AutogenReviewPipeline()
grounded_generator = GroundedGenerator()


# --- Pydantic API Models ---

class AskRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1500, description="Recruiter query")
    session_id: Optional[str] = Field(default=None, description="UUID session identifier")
    bypass_cache: bool = Field(default=False, description="Explicitly bypass query cache")


class AskResponse(BaseModel):
    trace_id: str
    session_id: str
    answer: str
    source_type: Literal["kb_policy", "applicant_status", "fallback_refusal", "security_refusal"]
    escalation_triggered: bool = False
    review_status: Literal["approved_unchanged", "revised", "rejected"]
    latency_ms: float


class AddDocumentRequest(BaseModel):
    filename: str = Field(..., pattern=r"^[a-zA-Z0-9_\-]+\.md$", description="Policy markdown file name")
    content: str = Field(..., min_length=20, max_length=5000, description="Markdown document text")


class AddDocumentResponse(BaseModel):
    message: str
    filename: str
    fixed_chunks_added: int
    sentence_chunks_added: int


# --- Global Exception Handlers ---

@app.exception_handler(BudgetExceededError)
async def handle_budget_exceeded(request: Request, exc: BudgetExceededError):
    return JSONResponse(
        status_code=429,
        content={"detail": str(exc), "error_type": "BudgetExceededError"},
    )


@app.exception_handler(SecurityGovernanceError)
async def handle_security_governance(request: Request, exc: SecurityGovernanceError):
    return JSONResponse(
        status_code=403,
        content={"detail": str(exc), "error_type": "SecurityGovernanceError"},
    )


# --- HTTP Endpoints ---

@app.get("/health")
def health_probe():
    return {
        "status": "healthy",
        "mock_llm": "deterministic_active",
        "telemetry_disabled": True,
        "cache_stats": query_cache.stats(),
    }


@app.post("/ask", response_model=AskResponse)
async def ask_endpoint(req: AskRequest):
    t0 = time.perf_counter()
    trace_id = str(uuid.uuid4())
    session_id = req.session_id or str(uuid.uuid4())
    raw_query = req.query

    # 1. Budget ceiling validator (raises BudgetExceededError -> HTTP 429 if > 250 tokens)
    estimated_tokens, ceiling = TokenBudgetValidator.validate_budget(raw_query)

    # 2. Input Guard 1: PII Masking (Indian Phone numbers)
    masked_query, was_pii_masked = PIIMaskingEngine.mask_phone_numbers(raw_query)

    # 3. Input Guard 2: Prompt Injection Detection
    if PromptInjectionDetector.detect_injection(masked_query):
        latency_ms = (time.perf_counter() - t0) * 1000
        audit_logger.log_event(
            route="/ask",
            user_query=raw_query,
            latency_ms=latency_ms,
            tokens_estimated=estimated_tokens,
            status_code=400,
            guardrail_status={"pii_masked": was_pii_masked, "injection_detected": True},
            cache_hit=False,
            session_id=session_id,
            trace_id=trace_id,
        )
        return AskResponse(
            trace_id=trace_id,
            session_id=session_id,
            answer=SECURITY_REFUSAL_MESSAGE,
            source_type="security_refusal",
            escalation_triggered=False,
            review_status="rejected",
            latency_ms=round(latency_ms, 3),
        )

    # 4. In-Memory Query Cache Check
    cache_hit = False
    if not req.bypass_cache:
        cached_result = query_cache.get(masked_query)
        if cached_result:
            cache_hit = True
            latency_ms = (time.perf_counter() - t0) * 1000
            audit_logger.log_event(
                route="/ask",
                user_query=raw_query,
                latency_ms=latency_ms,
                tokens_estimated=estimated_tokens,
                status_code=200,
                guardrail_status={"pii_masked": was_pii_masked, "injection_detected": False},
                cache_hit=True,
                session_id=session_id,
                trace_id=trace_id,
            )
            return AskResponse(
                trace_id=trace_id,
                session_id=session_id,
                answer=cached_result["answer"],
                source_type=cached_result["source_type"],
                escalation_triggered=cached_result.get("escalation_triggered", False),
                review_status=cached_result.get("review_status", "approved_unchanged"),
                latency_ms=round(latency_ms, 3),
            )

    # 5. Core Processing & Execution
    is_status_query = bool(re.search(r"APP-\d{5}", masked_query, re.IGNORECASE))
    escalation_triggered = False
    source_type = "kb_policy"
    retrieved_context = ""

    if is_status_query:
        # Dynamic applicant status query
        id_match = re.search(r"APP-\d{5}", masked_query, re.IGNORECASE)
        app_id = id_match.group(0).upper() if id_match else "APP-00001"
        status_info = check_job_application_status_fn(app_id)
        escalation_triggered = status_info["escalation_triggered"]
        source_type = "applicant_status"
        retrieved_context = str(status_info)
        draft_answer = (
            f"Candidate application {app_id} is currently in '{status_info['status']}' status with "
            f"an expected salary of ₹{status_info['expected_salary_inr']:,}. Escalation risk score is "
            f"{status_info['escalation_score']:.4f} (Escalation Triggered: {escalation_triggered}). "
            f"{status_info['reasoning']}"
        )
    else:
        # Static Knowledge Base policy query
        rag_res = grounded_generator.generate_grounded_answer(masked_query)
        retrieved_context = rag_res.get("context", "")
        if not rag_res["grounded"]:
            source_type = "fallback_refusal"
            draft_answer = FALLBACK_REFUSAL_TEXT
        else:
            source_type = "kb_policy"
            draft_answer = rag_res["answer"]

    # 6. Autogen Independent Peer-Review Stage (RoundRobinGroupChat, max_turns=2)
    verdict = await autogen_pipeline.review_draft(
        draft_answer=draft_answer,
        retrieved_context=retrieved_context or draft_answer,
    )
    final_answer = verdict.final_answer
    review_status: Literal["approved_unchanged", "revised", "rejected"] = (
        "revised" if verdict.revised else "approved_unchanged"
    )

    # 7. Store in Cache if Static KB Policy Query
    if source_type == "kb_policy" and verdict.approved and not verdict.revised:
        query_cache.set(
            masked_query,
            {
                "answer": final_answer,
                "source_type": source_type,
                "escalation_triggered": escalation_triggered,
                "review_status": review_status,
            },
        )

    # 8. Record in multi-turn memory
    session_pipeline.ask(masked_query, session_id=session_id)

    # 9. Structured Audit Logging with Zero-PII Guarantee
    latency_ms = (time.perf_counter() - t0) * 1000
    audit_logger.log_event(
        route="/ask",
        user_query=raw_query,
        latency_ms=latency_ms,
        tokens_estimated=estimated_tokens,
        status_code=200,
        guardrail_status={"pii_masked": was_pii_masked, "injection_detected": False},
        cache_hit=False,
        session_id=session_id,
        trace_id=trace_id,
    )

    return AskResponse(
        trace_id=trace_id,
        session_id=session_id,
        answer=final_answer,
        source_type=source_type,  # type: ignore
        escalation_triggered=escalation_triggered,
        review_status=review_status,
        latency_ms=round(latency_ms, 3),
    )


@app.post("/add-document", response_model=AddDocumentResponse)
def add_document_endpoint(req: AddDocumentRequest):
    index_mgr = get_shared_index_manager()
    stats = index_mgr.add_document(req.filename, req.content)
    return AddDocumentResponse(
        message=f"Document '{req.filename}' successfully ingested into dual ChromaDB collections.",
        filename=req.filename,
        fixed_chunks_added=stats["fixed_chunks_added"],
        sentence_chunks_added=stats["sentence_chunks_added"],
    )


# --- WebSocket Streaming Endpoint ---

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    session_id = str(uuid.uuid4())
    try:
        while True:
            data = await websocket.receive_text()
            t0 = time.perf_counter()
            trace_id = str(uuid.uuid4())

            # Budget check
            try:
                estimated_tokens, _ = TokenBudgetValidator.validate_budget(data)
            except BudgetExceededError as be:
                await websocket.send_json({
                    "trace_id": trace_id,
                    "error": str(be),
                    "status": "budget_exceeded",
                })
                continue

            # PII masking
            masked, was_masked = PIIMaskingEngine.mask_phone_numbers(data)

            # Injection check
            if PromptInjectionDetector.detect_injection(masked):
                await websocket.send_json({
                    "trace_id": trace_id,
                    "answer": SECURITY_REFUSAL_MESSAGE,
                    "status": "security_refusal",
                })
                continue

            # Process query
            rag_res = grounded_generator.generate_grounded_answer(masked)
            verdict = await autogen_pipeline.review_draft(
                rag_res["answer"], rag_res.get("context", "")
            )

            latency_ms = (time.perf_counter() - t0) * 1000
            audit_logger.log_event(
                route="/ws/chat",
                user_query=data,
                latency_ms=latency_ms,
                tokens_estimated=estimated_tokens,
                status_code=200,
                guardrail_status={"pii_masked": was_masked, "injection_detected": False},
                cache_hit=False,
                session_id=session_id,
                trace_id=trace_id,
            )

            await websocket.send_json({
                "trace_id": trace_id,
                "session_id": session_id,
                "answer": verdict.final_answer,
                "review_status": "revised" if verdict.revised else "approved_unchanged",
                "latency_ms": round(latency_ms, 3),
            })
    except WebSocketDisconnect:
        # Clean disconnect recovery: never crashes the worker or impacts others
        audit_logger.log_event(
            route="/ws/chat",
            user_query="[DISCONNECTED]",
            latency_ms=0.0,
            tokens_estimated=0,
            status_code=1000,
            guardrail_status={"pii_masked": False, "injection_detected": False},
            cache_hit=False,
            session_id=session_id,
            trace_id=str(uuid.uuid4()),
            extra_metadata={"event": "client_disconnected_cleanly"},
        )
