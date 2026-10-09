"""Unit tests for FastAPI endpoints and WebSocket (Task T11 & T12)."""

import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_ask_policy_endpoint(client):
    payload = {"query": "What is the policy for notice period and buyout?"}
    res = client.post("/ask", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
    assert data["source_type"] == "kb_policy"
    assert "trace_id" in data


def test_ask_status_endpoint(client):
    payload = {"query": "Check status for applicant APP-00001."}
    res = client.post("/ask", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["source_type"] == "applicant_status"
    assert "APP-00001" in data["answer"]


def test_add_document_endpoint(client):
    payload = {
        "filename": "14_welfare_benefits.md",
        "content": (
            "# Welfare Benefits Policy\n\n"
            "Employees are eligible for medical insurance coverage up to five lakhs INR per year. "
            "Claims are processed by the third-party administrator within fifteen days."
        ),
    }
    res = client.post("/add-document", json=payload)
    assert res.status_code == 200
    assert res.json()["filename"] == "14_welfare_benefits.md"


def test_websocket_chat_and_disconnect(client):
    # Connect and chat
    with client.websocket_connect("/ws/chat") as ws:
        ws.send_text("What is the remote work policy?")
        reply = ws.receive_json()
        assert "answer" in reply
        assert "trace_id" in reply

    # Mid-stream disconnect: closing socket cleanly without server crash
    with client.websocket_connect("/ws/chat") as ws_disc:
        ws_disc.close(code=1000)

    # Server remains healthy
    health = client.get("/health")
    assert health.status_code == 200
