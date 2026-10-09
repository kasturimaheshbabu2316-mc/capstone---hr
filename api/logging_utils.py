"""API logging utils adapter re-exporting from app.logging_utils."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.logging_utils import AuditLogger, audit_logger, AUDIT_LOG_FILE, LOGS_DIR

__all__ = ["AuditLogger", "audit_logger", "AUDIT_LOG_FILE", "LOGS_DIR"]
