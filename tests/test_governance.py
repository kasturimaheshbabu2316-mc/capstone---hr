"""Unit tests for Governance & Budgeting (Task T15)."""

import pytest
from governance.least_autonomy import ToolAccessController, SecurityGovernanceError
from governance.budget import TokenBudgetValidator, BudgetExceededError


def test_least_autonomy_authorized():
    # LookupAgent calling status tool
    ToolAccessController.validate_tool_access(
        "Application Status Specialist", "check_job_application_status"
    )
    # RetrievalAgent calling RAG tool
    ToolAccessController.validate_tool_access(
        "Policy Knowledge Retrieval Specialist", "rag_lookup"
    )


def test_least_autonomy_unauthorized():
    # RetrievalAgent calling status tool
    with pytest.raises(SecurityGovernanceError):
        ToolAccessController.validate_tool_access(
            "Policy Knowledge Retrieval Specialist", "check_job_application_status"
        )

    # ResponseComposer calling any tool
    with pytest.raises(SecurityGovernanceError):
        ToolAccessController.validate_tool_access(
            "HR Communications Synthesizer", "rag_lookup"
        )


def test_token_budget_validator_allowed():
    normal_q = "What is the policy for notice period?"
    tokens, ceiling = TokenBudgetValidator.validate_budget(normal_q)
    assert tokens <= ceiling
    assert ceiling == 250


def test_token_budget_validator_rejected():
    oversized_q = "Explain recruitment policy in detail " * 50
    with pytest.raises(BudgetExceededError):
        TokenBudgetValidator.validate_budget(oversized_q)
