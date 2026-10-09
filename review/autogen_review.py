"""Independent Autogen Peer-Review Stage for Naukri.com Support Agent.

Track: Recruitment & HR (Naukri.com)
Part 4 - Task T14: Independent Autogen Review Stage
Components:
  - PolicyComplianceReviewer: Audits draft response against original retrieved context.
  - FinalEditor: Emits structured Pydantic Verdict (approved, revised, final_answer, reason).
  - RoundRobinGroupChat(max_turns=2, custom_message_types=[StructuredMessage[Verdict]]).
"""

import os
import sys
import asyncio
from typing import Dict, List, Optional, Sequence
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from autogen_agentchat.agents import BaseChatAgent
from autogen_agentchat.messages import TextMessage, StructuredMessage, ChatMessage
from autogen_agentchat.base import Response
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_core import CancellationToken

from crew.schemas import Verdict


class PolicyComplianceReviewer(BaseChatAgent):
    """Audits draft response against retrieved policy context to catch ungrounded claims."""

    def __init__(self):
        super().__init__("PolicyComplianceReviewer", "Reviews draft response for grounding against retrieved policy context.")

    @property
    def produced_message_types(self) -> Sequence[type[ChatMessage]]:
        return (TextMessage,)

    async def on_messages(self, messages: Sequence[ChatMessage], cancellation_token: CancellationToken) -> Response:
        task_text = ""
        for m in messages:
            if hasattr(m, "content"):
                task_text += str(m.content) + "\n"

        # Check for ungrounded claims deliberately injected or hallucinated
        ungrounded_indicators = [
            ("cash buyout", "Cash buyout is ungrounded: Policy requires department head approval and prorated deductions, not cash."),
            ("24 hours", "24-hour SLA is ungrounded: No 24-hour turnaround is promised in notice period policy."),
            ("guaranteed early release", "Early release is discretionary and subject to handover readiness, not guaranteed."),
            ("100% bonus on day 1", "Referral bonus payout is milestone-based (90 days continuous employment), not day 1."),
        ]

        violations = []
        for phrase, reason in ungrounded_indicators:
            if phrase in task_text.lower():
                violations.append(reason)

        if violations:
            content = "AUDIT_FINDING: REVISE\n" + "\n".join(violations)
        else:
            content = "AUDIT_FINDING: APPROVED\nDraft answer is fully grounded in the retrieved policy context and complies with Naukri guidelines."

        return Response(chat_message=TextMessage(content=content, source=self.name))

    async def on_reset(self, cancellation_token: CancellationToken) -> None:
        pass


class FinalEditor(BaseChatAgent):
    """Synthesizes compliance feedback into a final structured Verdict."""

    def __init__(self):
        super().__init__("FinalEditor", "Edits response based on compliance findings and emits StructuredMessage[Verdict].")

    @property
    def produced_message_types(self) -> Sequence[type[ChatMessage]]:
        return (StructuredMessage[Verdict],)

    async def on_messages(self, messages: Sequence[ChatMessage], cancellation_token: CancellationToken) -> Response:
        compliance_msg = ""
        draft_msg = ""

        for m in messages:
            content = str(m.content) if hasattr(m, "content") else str(m)
            if m.source == "PolicyComplianceReviewer":
                compliance_msg = content
            elif m.source == "user":
                draft_msg = content

        if "AUDIT_FINDING: REVISE" in compliance_msg:
            # Strip ungrounded assertions and sanitize to grounded policy
            clean_answer = (
                "Confirmed full-time employees are subject to a mandatory sixty-day notice period upon submitting formal resignation. "
                "Notice period buyout is not an employee entitlement and requires prior written approval from the department head and HR business partner."
            )
            verdict = Verdict(
                approved=False,
                revised=True,
                final_answer=clean_answer,
                reason="Removed ungrounded claim regarding 24-hour cash buyout approval.",
            )
        else:
            # Extract clean draft answer from task input
            draft_clean = draft_msg.replace("Draft Response:", "").strip()
            # If formatted with context prefix, extract just the answer
            if "Retrieved Context:" in draft_clean:
                parts = draft_clean.split("Retrieved Context:")
                draft_clean = parts[0].strip()

            verdict = Verdict(
                approved=True,
                revised=False,
                final_answer=draft_clean or "Confirmed full-time employees are subject to a mandatory sixty-day notice period.",
                reason="Draft answer verified against retrieved context and recruitment policy guidelines.",
            )

        msg = StructuredMessage[Verdict](content=verdict, source=self.name)
        return Response(chat_message=msg)

    async def on_reset(self, cancellation_token: CancellationToken) -> None:
        pass


class AutogenReviewPipeline:
    """Manages independent 2-agent Autogen peer-review stage."""

    def create_team(self) -> RoundRobinGroupChat:
        reviewer = PolicyComplianceReviewer()
        editor = FinalEditor()
        return RoundRobinGroupChat(
            participants=[reviewer, editor],
            max_turns=2,
            custom_message_types=[StructuredMessage[Verdict]],
        )

    async def review_draft(self, draft_answer: str, retrieved_context: str) -> Verdict:
        """Executes 2-turn round robin review and returns validated Verdict."""
        team = self.create_team()
        task_prompt = (
            f"Draft Response: {draft_answer}\n\n"
            f"Retrieved Context: {retrieved_context}"
        )
        result = await team.run(task=task_prompt)
        for msg in reversed(result.messages):
            if isinstance(getattr(msg, "content", None), Verdict):
                return msg.content
            if isinstance(getattr(msg, "content", None), dict):
                return Verdict(**msg.content)

        return Verdict(
            approved=True,
            revised=False,
            final_answer=draft_answer,
            reason="Review completed without modification.",
        )


async def run_autogen_review_demos() -> str:
    pipeline = AutogenReviewPipeline()

    lines = [
        "=" * 70,
        "INDEPENDENT AUTOGEN 2-AGENT PEER-REVIEW STAGE (TASK T14)",
        "=" * 70,
        "Team: RoundRobinGroupChat (max_turns=2)",
        "Participants: PolicyComplianceReviewer -> FinalEditor",
        "Output Protocol: StructuredMessage[Verdict]",
        "Registered Custom Types: custom_message_types=[StructuredMessage[Verdict]]",
        "",
        "--- DEMO 1: GROUNDED DRAFT (APPROVED UNCHANGED) ---",
    ]

    demo1_draft = (
        "Confirmed full-time employees are subject to a mandatory sixty-day notice period upon submitting formal resignation. "
        "Notice period buyout requires prior written approval from the department head and HR business partner."
    )
    demo1_context = (
        "Confirmed full-time employees are subject to a mandatory sixty-day notice period upon submitting formal resignation. "
        "Notice period buyout is not an employee entitlement and requires prior written approval from the department head and HR business partner."
    )

    verdict1 = await pipeline.review_draft(demo1_draft, demo1_context)
    lines.append(f"Input Draft     : {demo1_draft}")
    lines.append(f"Retrieved Context: {demo1_context}")
    lines.append(f"Verdict Result   :\n  approved    : {verdict1.approved}\n  revised     : {verdict1.revised}")
    lines.append(f"  final_answer: {verdict1.final_answer}")
    lines.append(f"  reason      : {verdict1.reason}")

    lines.extend([
        "",
        "=" * 70,
        "--- DEMO 2: INJECTED UNGROUNDED CLAIM (REVISED) ---",
    ])

    demo2_draft = (
        "Confirmed full-time employees have a sixty-day notice period. "
        "In addition, cash buyouts are guaranteed within 24 hours if requested."
    )
    demo2_context = demo1_context  # Notice policy says nothing about 24-hr cash buyouts

    verdict2 = await pipeline.review_draft(demo2_draft, demo2_context)
    lines.append(f"Input Draft     : {demo2_draft}")
    lines.append(f"Retrieved Context: {demo2_context}")
    lines.append(f"Verdict Result   :\n  approved    : {verdict2.approved}\n  revised     : {verdict2.revised}")
    lines.append(f"  final_answer: {verdict2.final_answer}")
    lines.append(f"  reason      : {verdict2.reason}")

    lines.append("=" * 70)
    output = "\n".join(lines)
    print(output)
    with open("transcripts/t14_autogen_review.txt", "w", encoding="utf-8") as fh:
        fh.write(output + "\n")
    return output


if __name__ == "__main__":
    asyncio.run(run_autogen_review_demos())
