"""Basic tests for the mock interview app."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest

from app import create_app


class StubTranscriber:
    """Deterministic transcriber for tests."""

    def transcribe(self, _audio_path):
        return "sample transcript", "completed"


@pytest.fixture()
def app(tmp_path: Path):
    flask_app = create_app(
        {
            "TESTING": True,
            "SESSION_STORAGE_PATH": tmp_path / "sessions",
        }
    )
    flask_app.config["INTERVIEW_SERVICE"].transcriber = StubTranscriber()
    yield flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


def test_index_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Mock Interview" in response.data


def test_create_session_returns_two_questions(client):
    response = client.post("/api/sessions")
    payload = response.get_json()

    assert response.status_code == 201
    assert "sessionId" in payload
    assert len(payload["interview"]["questions"]) == 2


def test_upload_audio_saves_transcript(client):
    session_response = client.post("/api/sessions")
    session = session_response.get_json()

    response = client.post(
        "/api/interview/upload",
        data={
            "sessionId": session["sessionId"],
            "audio": (BytesIO(b"fake-audio"), "full_interview.webm"),
        },
        content_type="multipart/form-data",
    )

    payload = response.get_json()
    assert response.status_code == 201
    assert payload["transcript"] == "sample transcript"
    assert payload["transcriptStatus"] == "completed"


def test_get_session_returns_saved_response(client):
    session_response = client.post("/api/sessions")
    session = session_response.get_json()

    client.post(
        "/api/interview/upload",
        data={
            "sessionId": session["sessionId"],
            "audio": (BytesIO(b"fake-audio"), "full_interview.webm"),
        },
        content_type="multipart/form-data",
    )

    response = client.get(f"/api/sessions/{session['sessionId']}")
    payload = response.get_json()

    assert response.status_code == 200
    assert len(payload["interview"]["responses"]) == 1
    assert payload["interview"]["responses"][0]["questionId"] == "full_interview"


def test_get_missing_session_returns_404(client):
    response = client.get("/api/sessions/does-not-exist")
    payload = response.get_json()

    assert response.status_code == 404
    assert payload["error"] == "Session not found."
