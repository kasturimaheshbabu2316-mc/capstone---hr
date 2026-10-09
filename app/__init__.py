"""App package for Naukri.com Domain Support Agent."""
from app.main import app
from app.logging_utils import audit_logger

__all__ = ["app", "audit_logger"]
