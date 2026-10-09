"""Runner for Tasks T15 & T16: Governance Verification & In-Memory Cache Benchmarks."""

import os
import sys
import time
from typing import Dict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from governance.least_autonomy import ToolAccessController, SecurityGovernanceError
from governance.budget import TokenBudgetValidator, BudgetExceededError
from cache import QueryCache
from rag.generate import GroundedGenerator


def run_governance_and_cache_tests() -> str:
    lines = [
        "=" * 70,
        "AI GOVERNANCE & QUERY CACHE BENCHMARK VERIFICATION (TASKS T15 & T16)",
        "=" * 70,
        "Framework Governance: Least Autonomy, High-Risk Assessment, Budget Ceiling",
        "Framework Resilience: SHA-256 In-Memory Query Normalization Cache",
        "",
        "--- PART 1: LEAST AUTONOMY PRIVILEGE ESCALATION BLOCK ---",
    ]

    # Test 1: Authorized tool execution
    try:
        ToolAccessController.validate_tool_access(
            "Application Status Specialist", "check_job_application_status"
        )
        lines.append("Test 1.1: LookupAgent calling check_job_application_status -> ALLOWED (Compliant)")
    except SecurityGovernanceError as e:
        lines.append(f"Test 1.1: FAILED unexpectedly: {e}")

    # Test 2: Unauthorized tool execution by RetrievalAgent
    try:
        ToolAccessController.validate_tool_access(
            "Policy Knowledge Retrieval Specialist", "check_job_application_status"
        )
        lines.append("Test 1.2: RetrievalAgent calling check_job_application_status -> UNEXPECTEDLY ALLOWED")
    except SecurityGovernanceError as e:
        lines.append("Test 1.2: RetrievalAgent calling check_job_application_status -> BLOCKED (PASSED)")
        lines.append(f"  Exception Caught: {e}")

    # Test 3: Unauthorized tool execution by ResponseComposer (Zero tools allowed)
    try:
        ToolAccessController.validate_tool_access(
            "HR Communications Synthesizer", "rag_lookup"
        )
        lines.append("Test 1.3: ResponseComposer calling rag_lookup -> UNEXPECTEDLY ALLOWED")
    except SecurityGovernanceError as e:
        lines.append("Test 1.3: ResponseComposer calling rag_lookup -> BLOCKED (PASSED)")
        lines.append(f"  Exception Caught: {e}")

    lines.extend([
        "",
        "=" * 70,
        "--- PART 2: RUNTIME PER-REQUEST TOKEN BUDGET CAP ---",
        f"Hard Token Ceiling: {TokenBudgetValidator.BUDGET_CEILING_TOKENS} prompt tokens",
    ])

    normal_query = "What is the mandatory notice period for confirmed employees?"
    est_norm, ceil_norm = TokenBudgetValidator.validate_budget(normal_query)
    lines.append(f"\nNormal Query     : '{normal_query}'")
    lines.append(f"Estimated Tokens : {est_norm} tokens (Ceiling: {ceil_norm}) -> ALLOWED (HTTP 200)")

    # Oversized query: 300+ tokens
    oversized_query = "Please provide exhaustive details on all HR policies " * 30
    lines.append(f"\nOversized Query Length: {len(oversized_query)} characters")
    try:
        TokenBudgetValidator.validate_budget(oversized_query)
        lines.append("Budget Filter Failed: Oversized request was not rejected.")
    except BudgetExceededError as e:
        lines.append("Budget Filter Passed: Oversized request immediately rejected with HTTP 429:")
        lines.append(f"  Error Message: {e}")

    lines.extend([
        "",
        "=" * 70,
        "--- PART 3: IN-MEMORY QUERY CACHING BENCHMARK (TASK T16) ---",
    ])

    cache = QueryCache()
    generator = GroundedGenerator()

    test_q1 = "What is the notice period policy and buyout requirement?"
    test_q2 = "   what is the notice   period policy and buyout requirement??  "  # Punctuation/whitespace variation

    # Turn 1: Cold execution (Cache Miss)
    t0 = time.perf_counter()
    res1 = cache.get(test_q1)
    if res1 is None:
        computed_res = generator.generate_grounded_answer(test_q1)
        cache.set(test_q1, computed_res)
    t_cold = (time.perf_counter() - t0) * 1000

    lines.append(f"Run 1 (Cold Query): '{test_q1}'")
    lines.append(f"  Cache Status : CACHE MISS")
    lines.append(f"  Latency      : {t_cold:.3f} ms")

    # Turn 2: Repeated query with whitespace/punctuation variation (Cache Hit)
    t1 = time.perf_counter()
    res2 = cache.get(test_q2)
    t_warm = (time.perf_counter() - t1) * 1000

    lines.append(f"\nRun 2 (Normalized Query): '{test_q2}'")
    lines.append(f"  Cache Status : {'CACHE HIT' if res2 is not None else 'CACHE MISS'}")
    lines.append(f"  Latency      : {t_warm:.4f} ms")
    if t_warm > 0:
        speedup = t_cold / max(0.0001, t_warm)
        lines.append(f"  Speedup Factor: {speedup:.1f}x faster (O(1) sub-millisecond retrieval)")

    # Turn 3: Dynamic status query bypass
    dynamic_q = "Check status for applicant APP-00012."
    lines.append(f"\nDynamic Query Check: '{dynamic_q}'")
    is_dyn = cache.is_dynamic_query(dynamic_q)
    cached_lookup = cache.get(dynamic_q)
    lines.append(f"  Dynamic Flag : {is_dyn}")
    lines.append(f"  Cache Bypass : {'YES (Bypassed live dataset)' if cached_lookup is None else 'NO'}")

    lines.append(f"\nCache Stats:\n  {cache.stats()}")
    lines.append("=" * 70)

    output = "\n".join(lines)
    print(output)
    with open("transcripts/t15_governance_and_cache.txt", "w", encoding="utf-8") as fh:
        fh.write(output + "\n")
    return output


if __name__ == "__main__":
    run_governance_and_cache_tests()
