"""Zero-PII Structured Audit Logging Utility.

Track: Recruitment & HR (Naukri.com)
Part 3 - Task T12: Structured JSON-Lines Audit Logging
Invariants:
  - Exactly one JSON-Lines record per request in logs/audit_trail.jsonl.
  - Raw phone numbers NEVER touch disk: text is sanitized via PIIMaskingEngine prior to writing.
"""

import os
import sys
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from crew.guardrails import PIIMaskingEngine

LOGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs"))
AUDIT_LOG_FILE = os.path.join(LOGS_DIR, "audit_trail.jsonl")


class AuditLogger:
    """Manages append-only zero-PII audit logging."""

    def __init__(self, log_path: str = AUDIT_LOG_FILE):
        self.log_path = log_path
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def log_event(
        self,
        route: str,
        user_query: str,
        latency_ms: float,
        tokens_estimated: int,
        status_code: int,
        guardrail_status: Dict[str, Any],
        cache_hit: bool,
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Sanitizes prompt, formats record, and writes single JSONL entry."""
        masked_query, _ = PIIMaskingEngine.mask_phone_numbers(user_query)

        tid = trace_id or str(uuid.uuid4())
        record = {
            "trace_id": tid,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "route": route,
            "session_id": session_id or "anonymous",
            "masked_query": masked_query,
            "tokens_estimated": tokens_estimated,
            "guardrail_status": guardrail_status,
            "cache_hit": cache_hit,
            "latency_ms": round(latency_ms, 3),
            "status_code": status_code,
            "metadata": extra_metadata or {},
        }

        with open(self.log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")

        return record


# Global singleton instance
audit_logger = AuditLogger()
