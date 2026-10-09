"""Unit tests for Autogen review stage (Task T14)."""

import pytest
import asyncio
from review.autogen_review import AutogenReviewPipeline
from crew.schemas import Verdict


def test_autogen_review_approved():
    pipeline = AutogenReviewPipeline()
    draft = "Confirmed full-time employees are subject to a mandatory sixty-day notice period."
    context = draft

    verdict = asyncio.run(pipeline.review_draft(draft, context))
    assert isinstance(verdict, Verdict)
    assert verdict.approved is True
    assert verdict.revised is False


def test_autogen_review_revised_hallucination():
    pipeline = AutogenReviewPipeline()
    draft = "Notice period is 60 days. In addition, cash buyout within 24 hours is guaranteed."
    context = "Confirmed full-time employees are subject to a mandatory sixty-day notice period."

    verdict = asyncio.run(pipeline.review_draft(draft, context))
    assert isinstance(verdict, Verdict)
    assert verdict.approved is False
    assert verdict.revised is True
    assert "cash buyout" not in verdict.final_answer.lower()
    assert "24 hours" not in verdict.final_answer.lower()
