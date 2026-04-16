"""Basic route tests for app.py."""

# pylint: disable=redefined-outer-name

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # pylint: disable=wrong-import-position,import-error


@pytest.fixture()
def app(tmp_path):
    """Create a Flask app with mocked storage and interview service."""
    fake_storage = Mock()
    fake_service = Mock()

    config = {
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "SESSION_STORAGE_PATH": tmp_path / "sessions",
        "MONGO_URI": "mongodb://localhost:27017/testdb",
    }

    with (
        patch("app.SessionStorage", return_value=fake_storage),
        patch("app.AudioTranscriber"),
        patch("app.MockInterviewService", return_value=fake_service),
    ):
        flask_app = create_app(config)
        flask_app.config["SESSION_STORAGE"] = fake_storage
        flask_app.config["INTERVIEW_SERVICE"] = fake_service
        flask_app.fake_storage = fake_storage
        flask_app.fake_service = fake_service
        yield flask_app


@pytest.fixture()
def client(app):
    """Return Flask test client."""
    return app.test_client()


def _log_in_session(client):
    """Mark the session as logged in for protected routes."""
    with client.session_transaction() as session:
        session["user_id"] = "user-123"
        session["email"] = "test@example.com"


def test_index_page_loads(client):
    """Index page should render."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Get Ready for Your College Application!" in response.data


def test_login_page_loads(client):
    """Login page should render."""
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Log In" in response.data


def test_signup_page_loads(client):
    """Signup page should render."""
    response = client.get("/signup")
    assert response.status_code == 200
    assert b"Create your account" in response.data


def test_logout_redirects(client):
    """Logout should redirect back to index."""
    response = client.get("/logout", follow_redirects=False)
    assert response.status_code in (302, 308)


def test_api_sessions_requires_login(client):
    """Interview session creation should reject anonymous users."""
    response = client.post("/api/sessions")
    assert response.status_code == 401
    assert response.get_json()["error"] == "Not logged in."


def test_api_sessions_creates_session_when_logged_in(client, app):
    """Logged-in users should be able to create interview sessions."""
    _log_in_session(client)

    app.fake_storage.create_session.return_value = {
        "sessionId": "abc123",
        "interview": {
            "questions": [{"id": "q1", "text": "Question?"}],
            "responses": [],
        },
    }

    response = client.post("/api/sessions")
    assert response.status_code == 201
    payload = response.get_json()
    assert payload["sessionId"] == "abc123"


def test_get_interview_session_returns_404_when_missing(client, app):
    """Missing sessions should return 404."""
    app.fake_storage.get_session.side_effect = FileNotFoundError("missing")

    response = client.get("/api/sessions/missing")
    assert response.status_code == 404
    assert response.get_json()["error"] == "Session not found."


def test_upload_audio_requires_session_and_audio(client):
    """Upload route should validate required form fields."""
    response = client.post("/api/interview/upload", data={})
    assert response.status_code == 400
    assert response.get_json()["error"] == "sessionId and audio are required."
