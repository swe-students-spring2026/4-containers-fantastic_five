"""Basic tests for the mock interview app."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # pylint: disable=wrong-import-position,import-error


# pylint: disable=too-few-public-methods,redefined-outer-name
class StubTranscriber:
    """Deterministic transcriber for tests."""

    def transcribe(self, _audio_path):
        """Return a fixed transcript for test uploads."""
        return "sample transcript", "completed"


@pytest.fixture()
def flask_app(tmp_path: Path):
    """Create a test Flask app with isolated session storage."""
    flask_app = create_app(
        {
            "TESTING": True,
            "SESSION_STORAGE_PATH": tmp_path / "sessions",
        }
    )
    flask_app.config["INTERVIEW_SERVICE"].transcriber = StubTranscriber()
    yield flask_app


@pytest.fixture()
def test_client(flask_app):
    """Create a Flask test client."""
    return flask_app.test_client()


def test_index_page_loads(test_client):
    """Index route should render the interview page."""
    response = test_client.get("/")
    assert response.status_code == 200
    assert b"Mock Interview" in response.data


def test_create_session_returns_two_questions(test_client):
    """Creating a session should return exactly two questions."""
    response = test_client.post("/api/sessions")
    payload = response.get_json()

    assert response.status_code == 201
    assert "sessionId" in payload
    assert len(payload["interview"]["questions"]) == 2


def test_upload_audio_saves_transcript(test_client):
    """Uploading audio should persist the stub transcript."""
    session_response = test_client.post("/api/sessions")
    session = session_response.get_json()

    response = test_client.post(
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


def test_get_session_returns_saved_response(test_client):
    """Saved interview responses should be returned in the session payload."""
    session_response = test_client.post("/api/sessions")
    session = session_response.get_json()

    test_client.post(
        "/api/interview/upload",
        data={
            "sessionId": session["sessionId"],
            "audio": (BytesIO(b"fake-audio"), "full_interview.webm"),
        },
        content_type="multipart/form-data",
    )

    response = test_client.get(f"/api/sessions/{session['sessionId']}")
    payload = response.get_json()

    assert response.status_code == 200
    assert len(payload["interview"]["responses"]) == 1
    assert payload["interview"]["responses"][0]["questionId"] == "full_interview"


def test_get_missing_session_returns_404(test_client):
    """Missing sessions should return a 404 payload."""
    response = test_client.get("/api/sessions/does-not-exist")
    payload = response.get_json()

    assert response.status_code == 404
    assert payload["error"] == "Session not found."
