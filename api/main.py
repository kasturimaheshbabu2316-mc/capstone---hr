"""API package adapter re-exporting from app package for backward compatibility."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import (
    app,
    AskRequest,
    AskResponse,
    AddDocumentRequest,
    AddDocumentResponse,
    health_probe,
    ask_endpoint,
    add_document_endpoint,
    websocket_chat,
)

__all__ = [
    "app",
    "AskRequest",
    "AskResponse",
    "AddDocumentRequest",
    "AddDocumentResponse",
    "health_probe",
    "ask_endpoint",
    "add_document_endpoint",
    "websocket_chat",
]
