"""Unit tests for memory.py (Task T8)."""

import pytest
from crew.memory import ConversationalSessionPipeline, clear_session_store


def test_multi_turn_anaphora_resolution():
    clear_session_store()
    pipeline = ConversationalSessionPipeline()
    session_id = "test-session-anaphora"

    # Turn 1: Lookup APP-00012
    a1 = pipeline.ask("Check status for candidate APP-00012", session_id=session_id)
    assert "APP-00012" in a1 or "Screening" in a1

    # Turn 2: Refer to candidate with pronoun 'their'
    a2 = pipeline.ask("What was their expected salary and are they flagged?", session_id=session_id)
    assert "APP-00012" in a2
    assert "expected salary" in a2.lower() or "₹" in a2


def test_session_isolation():
    clear_session_store()
    pipeline = ConversationalSessionPipeline()

    # Session 1 mentions candidate APP-00012
    pipeline.ask("Check status for candidate APP-00012", session_id="session-1")

    # Session 2 has no mention of any candidate
    a_fresh = pipeline.ask("What was their expected salary?", session_id="session-2")
    # Must refuse or ask for record ID because session 2 is isolated
    assert "could not identify which candidate" in a_fresh or "specify the application record" in a_fresh
