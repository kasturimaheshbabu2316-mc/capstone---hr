"""Validation Test Runner for Task T9: Pydantic Structured Output Enforcement."""

import os
import sys
import json
from typing import Dict, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from crew.schemas import SupportResponse, StatusToolResponse, Verdict
from pydantic import ValidationError


SAMPLE_RESPONSES = [
    {
        "query_type": "policy",
        "content": "Confirmed full-time employees are subject to a mandatory sixty-day notice period upon submitting resignation.",
        "citations": ["05_notice_period.md"],
        "escalation_flag": False,
        "confidence_score": 0.95,
    },
    {
        "query_type": "status",
        "content": "Application APP-00020 for Sales Associate is in Screening status. Escalation score is 0.4667 (URGENT HR ACTION REQUIRED).",
        "citations": ["JOB_APPLICATIONS"],
        "escalation_flag": True,
        "confidence_score": 1.0,
    },
    {
        "query_type": "out_of_scope",
        "content": "I apologize, but this topic is not covered in our recruitment policy knowledge base.",
        "citations": [],
        "escalation_flag": False,
        "confidence_score": 0.0,
    },
]


def run_t9_schema_validation() -> str:
    lines = [
        "=" * 70,
        "PYDANTIC STRUCTURED RESPONSE VALIDATION (TASK T9)",
        "=" * 70,
        "Schema Target: crew.schemas.SupportResponse",
        "Fields: query_type, content, citations, escalation_flag, confidence_score",
        "",
        "--- VALIDATING SAMPLE RESPONSES ---",
    ]

    for idx, sample in enumerate(SAMPLE_RESPONSES, 1):
        try:
            model = SupportResponse(**sample)
            lines.append(f"\n[Sample {idx}: Type '{model.query_type}'] -> VALIDATION PASSED")
            lines.append(f"  Content         : {model.content[:75]}...")
            lines.append(f"  Citations       : {model.citations}")
            lines.append(f"  Escalation Flag : {model.escalation_flag}")
            lines.append(f"  Confidence Score: {model.confidence_score}")
            lines.append(f"  JSON Serialization: {model.model_dump_json()[:90]}...")
        except ValidationError as e:
            lines.append(f"\n[Sample {idx}] -> FAILED: {e}")

    lines.extend([
        "",
        "--- TESTING INVALID SCHEMA REJECTION (NEGATIVE TEST) ---",
    ])
    invalid_sample = {
        "query_type": "invalid_type",  # Illegal query_type
        "content": "Sample content",
        "confidence_score": 1.5,  # Exceeds max 1.0
    }
    try:
        SupportResponse(**invalid_sample)
        lines.append("Negative Test Failed: Invalid model was unexpectedly accepted.")
    except ValidationError as e:
        lines.append("Negative Test Passed: Pydantic correctly rejected invalid fields:")
        for err in e.errors():
            lines.append(f"  - Field '{err['loc'][0]}': {err['msg']}")

    lines.append("=" * 70)
    output = "\n".join(lines)
    print(output)
    with open("transcripts/t9_schema_validation.txt", "w", encoding="utf-8") as fh:
        fh.write(output + "\n")
    return output


if __name__ == "__main__":
    run_t9_schema_validation()
