"""Unit tests for tools.py (Task T6)."""

import pytest
import json
from crew.tools import (
    check_job_application_status_fn,
    check_job_application_status_tool,
    rag_lookup_fn,
    rag_lookup_tool,
)
from dataset import ESCALATION_THRESHOLD_80TH


def test_status_tool_existing_record():
    res = check_job_application_status_fn("APP-00001")
    assert res["record_id"] == "APP-00001"
    assert res["status"] in ["Applied", "Screening", "Interview Scheduled", "Offered", "Rejected"]
    assert res["expected_salary_inr"] >= 300000
    assert 0.0 <= res["escalation_score"] <= 1.0
    assert isinstance(res["escalation_triggered"], bool)


def test_status_tool_non_existent_record():
    res = check_job_application_status_fn("APP-99999")
    assert res["status"] == "Not Found"
    assert res["escalation_score"] == 0.0
    assert res["escalation_triggered"] is False
    assert "does not exist" in res["reasoning"]


def test_status_tool_schema_declaration():
    assert hasattr(check_job_application_status_tool, "args_schema")
    fields = check_job_application_status_tool.args_schema.model_fields.keys()
    assert "record_id" in fields


def test_rag_tool_schema_declaration():
    assert hasattr(rag_lookup_tool, "args_schema")
    fields = rag_lookup_tool.args_schema.model_fields.keys()
    assert "query" in fields


def test_rag_tool_execution():
    res = rag_lookup_fn("notice period policy")
    assert res["found"] is True
    assert len(res["results"]) > 0
    assert "05_notice_period.md" in str(res)
