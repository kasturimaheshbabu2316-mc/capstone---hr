"""CrewAI Multi-Agent Team Definitions & Orchestration.

Track: Recruitment & HR (Naukri.com)
Part 2 - Task T7: CrewAI Multi-Agent Team Kickoff
Agents:
  - RetrievalAgent: Authorized for rag_lookup only
  - LookupAgent: Authorized for check_job_application_status only
  - ResponseComposer: Zero tools (Least Autonomy)
"""

import os
import sys
from typing import Dict, List, Optional
from pydantic import BaseModel

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Invariant 2: Explicit telemetry suppression
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"

from crewai import Agent, Crew, Process, Task
from llm.mock_llm import MockLLM
from crew.tools import check_job_application_status_tool, rag_lookup_tool
from crew.schemas import SupportResponse


def create_recruitment_crew(query: str, mock_llm: Optional[MockLLM] = None) -> Crew:
    """Instantiates the 3-agent CrewAI multi-agent team with Least Autonomy tool bindings."""
    llm = mock_llm or MockLLM()

    # Agent 1: Retrieval Agent (Librarian) - RAG tool only
    retrieval_agent = Agent(
        role="Policy Knowledge Retrieval Specialist",
        goal="Retrieve authoritative, grounded recruitment policy excerpts from the knowledge base for recruiter inquiries.",
        backstory="Experienced Naukri HR policy librarian specializing in statutory compliance, buyout rules, and internal mobility guidelines.",
        tools=[rag_lookup_tool],
        llm=llm,
        verbose=False,
        max_iter=3,
        allow_delegation=False,
    )

    # Agent 2: Lookup Agent (ATS Specialist) - Status tool only
    lookup_agent = Agent(
        role="Application Status Specialist",
        goal="Query candidate job application lifecycles, salary benchmarks, and calculate empirical escalation scores.",
        backstory="Naukri enterprise candidate tracking system administrator with real-time access to applicant status databases.",
        tools=[check_job_application_status_tool],
        llm=llm,
        verbose=False,
        max_iter=3,
        allow_delegation=False,
    )

    # Agent 3: Response Composer (HR Communicator) - Zero tools (Least Autonomy)
    response_composer = Agent(
        role="HR Communications Synthesizer",
        goal="Synthesize technical status metrics and policy findings into clear, empathetic, and compliant employer-support responses.",
        backstory="Lead Naukri employer-relations specialist dedicated to transparent recruiter communications and verified accuracy.",
        tools=[],  # Invariant 5: Zero tools
        llm=llm,
        verbose=False,
        max_iter=3,
        allow_delegation=False,
    )

    is_status_query = "APP-" in query.upper()

    if is_status_query:
        # Task for Lookup Agent
        task1 = Task(
            description=f"Look up the applicant tracking details and calculate the escalation score for query: '{query}'.",
            expected_output="Detailed status, salary, and escalation score metrics.",
            agent=lookup_agent,
        )
        task2 = Task(
            description="Format the application status findings into a concise, professional employer support response.",
            expected_output="Final synthesized response with application details, escalation status, and HR recommendations.",
            agent=response_composer,
        )
        crew = Crew(
            agents=[lookup_agent, response_composer],
            tasks=[task1, task2],
            process=Process.sequential,
            verbose=False,
        )
    else:
        # Task for Retrieval Agent
        task1 = Task(
            description=f"Query the recruitment policy knowledge base for authoritative rules regarding: '{query}'.",
            expected_output="Authoritative policy excerpts with citation of the relevant parent document.",
            agent=retrieval_agent,
        )
        task2 = Task(
            description="Synthesize the retrieved policy excerpts into an authoritative, empathetic employer response.",
            expected_output="Final policy consultation answer strictly grounded in the knowledge base.",
            agent=response_composer,
        )
        crew = Crew(
            agents=[retrieval_agent, response_composer],
            tasks=[task1, task2],
            process=Process.sequential,
            verbose=False,
        )

    return crew


def run_crew_kickoff_demos() -> str:
    """Executes .kickoff() for both a policy query (RAG tool) and a status query (Lookup tool)."""
    mock_llm = MockLLM()

    lines = [
        "=" * 70,
        "CREWAI MULTI-AGENT TEAM ORCHESTRATION (.kickoff() DEMOS - TASK T7)",
        "=" * 70,
        "Agents in System Architecture:",
        "  1. RetrievalAgent   (Tools: [rag_lookup])",
        "  2. LookupAgent      (Tools: [check_job_application_status])",
        "  3. ResponseComposer (Tools: [] - Least Autonomy Principle)",
        "Process: Sequential (.kickoff())",
        "",
        "--- RUN 1: POLICY CONSULTATION QUERY (INVOKING RAG TOOL) ---",
    ]

    policy_query = "What is the mandatory notice period and policy on notice buyout?"
    policy_crew = create_recruitment_crew(policy_query, mock_llm)
    lines.append(f"Input Query: '{policy_query}'")
    lines.append("Executing policy_crew.kickoff()...")
    policy_result = policy_crew.kickoff()
    lines.append(f"Kickoff Result Output:\n{policy_result.raw if hasattr(policy_result, 'raw') else str(policy_result)}")

    lines.extend([
        "",
        "=" * 70,
        "--- RUN 2: APPLICANT STATUS QUERY (INVOKING STATUS LOOKUP TOOL) ---",
    ])
    status_query = "Please check the application status and escalation risk for candidate APP-00020."
    status_crew = create_recruitment_crew(status_query, mock_llm)
    lines.append(f"Input Query: '{status_query}'")
    lines.append("Executing status_crew.kickoff()...")
    status_result = status_crew.kickoff()
    lines.append(f"Kickoff Result Output:\n{status_result.raw if hasattr(status_result, 'raw') else str(status_result)}")

    lines.append("=" * 70)
    output = "\n".join(lines)
    print(output)
    with open("transcripts/t7_crew_kickoff_transcripts.txt", "w", encoding="utf-8") as fh:
        fh.write(output + "\n")
    return output


if __name__ == "__main__":
    run_crew_kickoff_demos()
