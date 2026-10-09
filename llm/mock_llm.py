"""Deterministic Mock LLM Implementation for Naukri.com Domain Support Agent.

Track: Recruitment & HR (Naukri.com)
Part 2 - Task T7 & Runtime Invariants
Subclasses crewai.llms.base_llm.BaseLLM.
Zero external API keys, zero outbound network calls, zero external telemetry.
Resolves:
  - Pitfall A: Parse model's own generated tokens, ignore ReAct template 'Observation: the result of the action'
  - Pitfall B: Tool selection based on declared Pydantic argument schema (record_id vs query)
"""

import os
import sys
import re
import json
from typing import Any, Dict, List, Optional, Type, Union
from pydantic import BaseModel, Field

# Invariant 2: Explicit telemetry suppression before imports
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"

from crewai.llms.base_llm import BaseLLM
from dataset import get_application_by_id, compute_escalation_score, ESCALATION_THRESHOLD_80TH
from crew.schemas import StatusToolResponse, SupportResponse, Verdict


class MockLLM(BaseLLM):
    """Deterministic, 100% offline Mock LLM extending CrewAI BaseLLM."""

    model: str = Field(default="mock-llm-deterministic")
    temperature: float = Field(default=0.0)

    def __init__(self, model: str = "mock-llm-deterministic", **kwargs: Any):
        super().__init__(model=model, **kwargs)

    def supports_stop_words(self) -> bool:
        return True

    def get_context_window_size(self) -> int:
        return 8192

    def _extract_prompt_text(self, messages: Union[str, List[Any]]) -> str:
        """Flattens messages input into a single string for parsing."""
        if isinstance(messages, str):
            return messages
        if isinstance(messages, list):
            parts = []
            for m in messages:
                if isinstance(m, str):
                    parts.append(m)
                elif hasattr(m, "content"):
                    parts.append(str(m.content))
                elif isinstance(m, dict):
                    parts.append(str(m.get("content", "")))
                else:
                    parts.append(str(m))
            return "\n".join(parts)
        return str(messages)

    def _detect_real_observation(self, prompt: str) -> Optional[str]:
        """Resolves Pitfall A:
        Detects if a genuine tool observation has been returned in the conversation,
        strictly ignoring the ReAct prompt template literal 'Observation: the result of the action'.
        """
        # Look for 'Observation:' followed by actual data (not the template literal)
        match = re.search(r"Observation:\s*(?!the result of the action\b)(.+?)(?=\n\s*(?:Thought|Action|Final Answer|$))", prompt, re.DOTALL | re.IGNORECASE)
        if match:
            obs = match.group(1).strip()
            if obs and obs != "the result of the action":
                return obs
        return None

    def _select_tool_by_schema(self, tools: List[Any], query_text: str) -> Optional[str]:
        """Resolves Pitfall B:
        Dispatches tool calls by matching against declared Pydantic argument schemas,
        NEVER by tool name substrings (e.g. 'lookup').
        """
        if not tools:
            return None

        # Check if query contains an application record ID pattern APP-XXXXX
        has_app_id = bool(re.search(r"APP-\d{5}", query_text, re.IGNORECASE))

        for t in tools:
            # Check declared args_schema
            schema = getattr(t, "args_schema", None)
            tool_name = getattr(t, "name", str(t))

            if schema and hasattr(schema, "model_fields"):
                fields = schema.model_fields.keys()
                # Status tool expects record_id
                if "record_id" in fields and has_app_id:
                    return tool_name
                # RAG tool expects query
                if "query" in fields and not has_app_id:
                    return tool_name

        # Fallback to first available tool if schema matching was indeterminate
        return getattr(tools[0], "name", str(tools[0])) if tools else None

    def call(
        self,
        messages: Union[str, List[Any]],
        tools: Optional[List[Any]] = None,
        callbacks: Optional[List[Any]] = None,
        available_functions: Optional[Dict[str, Any]] = None,
        from_task: Optional[Any] = None,
        from_agent: Optional[Any] = None,
        response_model: Optional[Type[BaseModel]] = None,
        **kwargs: Any,
    ) -> Union[str, Any]:
        """Core deterministic completion dispatcher."""
        prompt = self._extract_prompt_text(messages)
        real_observation = self._detect_real_observation(prompt)

        # Detect candidate ID in prompt
        id_match = re.search(r"APP-\d{5}", prompt, re.IGNORECASE)
        record_id = id_match.group(0).upper() if id_match else None

        # Determine agent role if available
        agent_role = getattr(from_agent, "role", "") if from_agent else ""

        # Case 1: An actual observation is present -> emit Final Answer
        if real_observation:
            if "status" in real_observation.lower() or record_id:
                # Response for status lookup
                # Try parsing observation dict/json
                obs_data = {}
                try:
                    obs_data = json.loads(real_observation.replace("'", '"'))
                except Exception:
                    pass

                status = obs_data.get("status", "Screening")
                salary = obs_data.get("expected_salary_inr", 1500000)
                score = obs_data.get("escalation_score", 0.35)
                esc_flag = obs_data.get("escalation_triggered", False)
                reasoning = obs_data.get("reasoning", "Standard evaluation in progress.")

                ans = (
                    f"Application {record_id or 'record'} is currently in '{status}' status "
                    f"with expected salary ₹{salary:,}. Escalation risk score is {score:.4f} "
                    f"(Escalation Triggered: {esc_flag}). {reasoning}"
                )
                return (
                    f"Thought: I have evaluated the candidate application details.\n"
                    f"Final Answer: {ans}"
                )
            else:
                # Response for RAG lookup
                return (
                    f"Thought: I have retrieved the authoritative policy guidelines from the knowledge base.\n"
                    f"Final Answer: According to Naukri.com recruitment policy: {real_observation[:250]}..."
                )

        # Case 2: Tools are provided and no observation yet -> emit Action
        if tools:
            selected_tool = self._select_tool_by_schema(tools, prompt)
            if selected_tool == "check_job_application_status" or (record_id and "check" in str(selected_tool)):
                target_id = record_id or "APP-00001"
                action_input = json.dumps({"record_id": target_id})
                return (
                    f"Thought: I need to check the status and escalation score for candidate {target_id}.\n"
                    f"Action: check_job_application_status\n"
                    f"Action Input: {action_input}\n"
                )
            else:
                # RAG lookup action
                # Extract clean user question from prompt
                q_match = re.search(r"(?:Query|Question|User):?\s*(.+?)(?:\n|$)", prompt, re.IGNORECASE)
                query_val = q_match.group(1).strip() if q_match else "recruitment policy"
                action_input = json.dumps({"query": query_val})
                return (
                    f"Thought: I need to look up policy guidelines from the knowledge base.\n"
                    f"Action: rag_lookup\n"
                    f"Action Input: {action_input}\n"
                )

        # Case 3: No tools provided (Response Composer or direct query)
        if record_id:
            rec = get_application_by_id(record_id)
            if rec:
                status = rec["status"]
                category = rec["category"]
                salary = rec["expected_salary_inr"]
                score = compute_escalation_score(rec["flagged_priority_review"], rec["days_since_created"])
                esc_flag = score >= ESCALATION_THRESHOLD_80TH
                ans = (
                    f"Candidate application {record_id} for role '{category}' is currently in '{status}' status "
                    f"with an expected salary of ₹{salary:,}. Escalation score is {score:.4f} "
                    f"(Escalation Triggered: {esc_flag})."
                )
            else:
                ans = f"Application record {record_id} does not exist in the candidate tracking system."
        elif any(k in prompt.lower() for k in ["notice", "buyout"]):
            ans = (
                "Confirmed full-time employees are subject to a mandatory sixty-day notice period upon submitting formal resignation. "
                "Notice period buyout requires prior written approval from the department head and HR business partner."
            )
        elif any(k in prompt.lower() for k in ["probation"]):
            ans = (
                "New hires undergo a mandatory six-month probationary period from their joining date. "
                "Mid-probation review occurs at ninety days with final confirmation assessment at five months."
            )
        elif any(k in prompt.lower() for k in ["remote", "wfh", "hybrid"]):
            ans = (
                "Employees are eligible for a hybrid work schedule allowing up to two remote working days per week "
                "following confirmation of probation. 100% remote requires VP approval."
            )
        elif any(k in prompt.lower() for k in ["referral"]):
            ans = (
                "Employees are eligible for referral bonuses ranging from ₹25,000 to ₹75,000 INR when a recommended candidate "
                "completes ninety days of continuous employment."
            )
        else:
            ans = (
                "Naukri.com recruitment policies require adherence to structured interview stages, verified credentials, "
                "and formal compensation band approvals across all talent acquisition processes."
            )

        if "Final Answer:" not in ans and "Thought:" not in ans:
            return (
                f"Thought: I will synthesize an authoritative and grounded HR response.\n"
                f"Final Answer: {ans}"
            )
        return ans
