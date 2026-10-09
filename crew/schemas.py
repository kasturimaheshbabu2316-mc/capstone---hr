"""Pydantic v2 Contract Schemas for CrewAI Responses, Tools, and Autogen Verdicts.

Track: Recruitment & HR (Naukri.com)
Part 2 - Task T9: Structured Response Format Validation
Part 4 - Task T14: Autogen Structured Verdict Schema
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class StatusToolInput(BaseModel):
    """Pydantic input schema for check_job_application_status tool."""
    record_id: str = Field(..., pattern=r"^APP-\d{5}$", description="Unique application record ID (e.g. APP-00012)")


class RAGToolInput(BaseModel):
    """Pydantic input schema for rag_lookup tool."""
    query: str = Field(..., min_length=2, max_length=1000, description="Recruitment policy query to retrieve from knowledge base")


class StatusToolResponse(BaseModel):
    """Pydantic output schema for check_job_application_status."""
    record_id: str
    status: str
    expected_salary_inr: int
    days_since_created: int
    flagged_priority_review: bool
    escalation_score: float = Field(..., ge=0.0, le=1.0)
    escalation_triggered: bool
    reasoning: str


class SupportResponse(BaseModel):
    """Pydantic output format for CrewAI response composition."""
    query_type: Literal["policy", "status", "out_of_scope"]
    content: str
    citations: List[str] = Field(default_factory=list)
    escalation_flag: bool = False
    confidence_score: float = Field(..., ge=0.0, le=1.0)

    @field_validator("confidence_score")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        return round(float(v), 4)


class Verdict(BaseModel):
    """Pydantic schema for Autogen secondary peer review."""
    approved: bool
    revised: bool
    final_answer: str
    reason: str
