"""Tools for CrewAI Multi-Agent Team.

Track: Recruitment & HR (Naukri.com)
Part 2 - Task T6: Application Status Tool & Escalation Formula
Also provides RAG Lookup Tool backed by ChromaDB sentence-based collection.
Resolves Pitfall B: Tool argument schema declared explicitly via args_schema.
"""

import os
import sys
import json
from typing import Dict, List, Optional, Type
import numpy as np
from pydantic import BaseModel

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from crewai.tools import BaseTool
from dataset import (
    get_application_by_id,
    compute_escalation_score,
    ESCALATION_THRESHOLD_80TH,
    JOB_APPLICATIONS,
)
from crew.schemas import StatusToolInput, StatusToolResponse, RAGToolInput
from rag.indexing import VectorIndexManager


# Global index manager initialized once for RAG tool
_index_mgr: Optional[VectorIndexManager] = None


def get_shared_index_manager() -> VectorIndexManager:
    global _index_mgr
    if _index_mgr is None:
        _index_mgr = VectorIndexManager()
    return _index_mgr


def check_job_application_status_fn(record_id: str) -> Dict:
    """Core function to check job application status and compute escalation score.
    
    Escalation Formula:
      S_esc = 0.5 * (1_flagged_priority_review) + 0.5 * (days_since_created / 30.0)
    
    Escalation Threshold:
      Empirical 80th percentile of dataset distribution (tau_esc = 0.4500).
    """
    clean_id = record_id.strip().upper()
    record = get_application_by_id(clean_id)

    if not record:
        return {
            "record_id": clean_id,
            "status": "Not Found",
            "expected_salary_inr": 0,
            "days_since_created": 0,
            "flagged_priority_review": False,
            "escalation_score": 0.0,
            "escalation_triggered": False,
            "reasoning": f"Application record {clean_id} does not exist in the candidate tracking system.",
        }

    flagged = bool(record["flagged_priority_review"])
    days = int(record["days_since_created"])
    score = compute_escalation_score(flagged, days)
    triggered = bool(score >= ESCALATION_THRESHOLD_80TH)

    reason_parts = []
    if flagged:
        reason_parts.append("Candidate was flagged for priority review by recruiter.")
    reason_parts.append(f"Application has been open for {days} days ({days}/30 elapsed).")
    if triggered:
        reason_parts.append(
            f"Escalation score {score:.4f} exceeds empirical 80th percentile threshold "
            f"({ESCALATION_THRESHOLD_80TH:.4f}) -> URGENT HR ACTION REQUIRED."
        )
    else:
        reason_parts.append(
            f"Escalation score {score:.4f} is within standard threshold ({ESCALATION_THRESHOLD_80TH:.4f})."
        )

    res = {
        "record_id": record["record_id"],
        "status": record["status"],
        "expected_salary_inr": record["expected_salary_inr"],
        "days_since_created": days,
        "flagged_priority_review": flagged,
        "escalation_score": score,
        "escalation_triggered": triggered,
        "reasoning": " ".join(reason_parts),
    }
    validated = StatusToolResponse(**res)
    return validated.model_dump()


class CheckJobApplicationStatusTool(BaseTool):
    """CrewAI BaseTool subclass for application status lookup with Pydantic schema."""
    name: str = "check_job_application_status"
    description: str = (
        "Look up candidate job application status, expected salary, and empirical escalation "
        "score from the candidate tracking system using record_id."
    )
    args_schema: Type[BaseModel] = StatusToolInput

    def _run(self, record_id: str) -> str:
        res = check_job_application_status_fn(record_id)
        return json.dumps(res)


def rag_lookup_fn(query: str, top_k: int = 3) -> Dict:
    """Core function to query knowledge base with sentence-based ChromaDB collection."""
    mgr = get_shared_index_manager()
    hits = mgr.query("kb_sentence_based", query, top_k=top_k)
    if not hits:
        return {
            "query": query,
            "found": False,
            "results": [],
            "message": "No matching policy documents found in knowledge base.",
        }

    return {
        "query": query,
        "found": True,
        "top_similarity": hits[0]["cosine_similarity"],
        "parent_doc_id": hits[0]["parent_doc_id"],
        "results": hits,
        "summary": " ".join([h["text"] for h in hits[:2]]),
    }


class RAGLookupTool(BaseTool):
    """CrewAI BaseTool subclass for RAG policy lookup with Pydantic schema."""
    name: str = "rag_lookup"
    description: str = (
        "Look up recruitment policy information from the authoritative Naukri.com Knowledge Base using query."
    )
    args_schema: Type[BaseModel] = RAGToolInput

    def _run(self, query: str) -> str:
        res = rag_lookup_fn(query)
        return json.dumps(res)


# Instances for CrewAI agents
check_job_application_status_tool = CheckJobApplicationStatusTool()
rag_lookup_tool = RAGLookupTool()


def run_status_tool_tests() -> str:
    """Runs verification tests for Task T6 across boundary and sample records."""
    lines = [
        "=" * 70,
        "APPLICATION STATUS TOOL & ESCALATION SCORING VERIFICATION (TASK T6)",
        "=" * 70,
        f"Empirical 80th Percentile Escalation Cutoff (tau_esc): {ESCALATION_THRESHOLD_80TH:.4f}",
        "Formula: S_esc = 0.5 * (1_flagged) + 0.5 * (days_since_created / 30.0)",
        "",
        "--- TEST CASES: SAMPLE RECORDS FROM DATASET ---",
    ]

    sample_ids = ["APP-00001", "APP-00002", "APP-00005", "APP-00012", "APP-00020"]
    for sid in sample_ids:
        res = check_job_application_status_fn(sid)
        lines.append(f"\n[Record ID: {sid}]")
        lines.append(f"  Status        : {res['status']}")
        lines.append(f"  Salary (INR)  : ₹{res['expected_salary_inr']:,}")
        lines.append(f"  Days Open     : {res['days_since_created']} days")
        lines.append(f"  Flagged       : {res['flagged_priority_review']}")
        lines.append(f"  Escalation Sc : {res['escalation_score']:.4f}")
        lines.append(f"  Escalated?    : {res['escalation_triggered']}")
        lines.append(f"  Reasoning     : {res['reasoning']}")

    lines.extend([
        "",
        "--- TEST CASES: BOUNDARY & EDGE SCENARIOS ---",
    ])
    # Edge Case 1: Non-existent record
    missing_res = check_job_application_status_fn("APP-99999")
    lines.append(f"\n[Edge 1: Non-Existent Record APP-99999]")
    lines.append(f"  Status        : {missing_res['status']}")
    lines.append(f"  Escalation Sc : {missing_res['escalation_score']}")
    lines.append(f"  Escalated?    : {missing_res['escalation_triggered']}")
    lines.append(f"  Reasoning     : {missing_res['reasoning']}")

    # Edge Case 2: Pure minimum boundary
    min_score = compute_escalation_score(flagged=False, days_since_created=0)
    # Edge Case 3: Pure maximum boundary
    max_score = compute_escalation_score(flagged=True, days_since_created=30)
    lines.append(f"\n[Edge 2 & 3: Numerical Boundaries]")
    lines.append(f"  Absolute Minimum (days=0, flagged=False)  : {min_score:.4f} (Expected: 0.0)")
    lines.append(f"  Absolute Maximum (days=30, flagged=True) : {max_score:.4f} (Expected: 1.0)")
    lines.append(f"  Threshold Comparison (0.4500): {min_score < ESCALATION_THRESHOLD_80TH <= max_score}")

    lines.append("=" * 70)
    out = "\n".join(lines)
    print(out)
    with open("transcripts/t6_status_tool_tests.txt", "w", encoding="utf-8") as fh:
        fh.write(out + "\n")
    return out


if __name__ == "__main__":
    run_status_tool_tests()
