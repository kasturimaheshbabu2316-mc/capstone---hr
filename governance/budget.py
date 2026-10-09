"""Runtime Per-Request Token Budget Cap Validator.

Track: Recruitment & HR (Naukri.com)
Part 4 - Task T15: Runtime Budget Ceiling
Enforces hard limit of 250 prompt tokens. Excess tokens raise BudgetExceededError (HTTP 429).
"""

import math
from typing import Tuple


class BudgetExceededError(Exception):
    """Raised when a request exceeds the governance token budget cap."""
    pass


class TokenBudgetValidator:
    """Pre-execution gateway filter measuring estimated prompt tokens against ceiling."""

    BUDGET_CEILING_TOKENS: int = 250

    @classmethod
    def estimate_tokens(cls, query: str) -> int:
        """Estimates prompt tokens using industry heuristic: E_tokens = ceil(len(chars) / 4)."""
        clean_text = query.strip()
        return max(1, math.ceil(len(clean_text) / 4))

    @classmethod
    def validate_budget(cls, query: str) -> Tuple[int, int]:
        """Validates that query does not exceed the 250 token ceiling.
        
        Returns: (estimated_tokens, ceiling)
        Raises: BudgetExceededError if estimated_tokens > 250
        """
        estimated = cls.estimate_tokens(query)
        if estimated > cls.BUDGET_CEILING_TOKENS:
            raise BudgetExceededError(
                f"Request rejected: Query exceeds governance budget cap of {cls.BUDGET_CEILING_TOKENS} tokens "
                f"(Estimated: {estimated} tokens for {len(query)} characters)."
            )
        return estimated, cls.BUDGET_CEILING_TOKENS
