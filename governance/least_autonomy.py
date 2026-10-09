"""Application-Layer Least Autonomy Enforcement.

Track: Recruitment & HR (Naukri.com)
Part 4 - Task T15: Least Autonomy Principle
Enforces role-based tool access control. Unauthorized tool execution raises SecurityGovernanceError.
"""

from typing import Dict, Set


class SecurityGovernanceError(Exception):
    """Raised when an agent attempts an unauthorized tool execution or illegal wiring."""
    pass


class ToolAccessController:
    """Enforces strict role-based tool authorizations.
    
    Authorization Matrix:
      - RetrievalAgent   : authorized for 'rag_lookup' only
      - LookupAgent      : authorized for 'check_job_application_status' only
      - ResponseComposer : zero tools authorized (analytical synthesis only)
    """

    ROLE_TOOL_WHITELIST: Dict[str, Set[str]] = {
        "Policy Knowledge Retrieval Specialist": {"rag_lookup"},
        "Application Status Specialist": {"check_job_application_status"},
        "HR Communications Synthesizer": set(),  # Least Autonomy: No tools
    }

    @classmethod
    def validate_tool_access(cls, agent_role: str, tool_name: str) -> None:
        """Validates if agent role is authorized to execute tool_name.
        Raises SecurityGovernanceError if unauthorized.
        """
        allowed = cls.ROLE_TOOL_WHITELIST.get(agent_role, set())
        if tool_name not in allowed:
            raise SecurityGovernanceError(
                f"Security Governance Violation: Agent with role '{agent_role}' "
                f"is NOT authorized to invoke tool '{tool_name}'. "
                f"Permitted tools: {list(allowed) if allowed else 'NONE (Least Autonomy)'}."
            )
