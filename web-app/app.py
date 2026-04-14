"""Minimal Flask app for the mock interview workflow."""

from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, render_template, request

from interview_service import MockInterviewService
from storage import SessionStorage
from transcriber import AudioTranscriber


def create_app(test_config: dict | None = None) -> Flask:
    """Application factory used by the dev server and tests."""

    flask_app = Flask(__name__)
    data_dir = Path(flask_app.root_path) / "data" / "sessions"
    flask_app.config.update(
        SECRET_KEY="development-key",
        SESSION_STORAGE_PATH=data_dir,
    )

    if test_config:
        flask_app.config.update(test_config)

    storage = SessionStorage(flask_app.config["SESSION_STORAGE_PATH"])
    transcriber = AudioTranscriber()
    service = MockInterviewService(storage, transcriber)
    flask_app.config["INTERVIEW_SERVICE"] = service
    flask_app.config["SESSION_STORAGE"] = storage

    @flask_app.get("/")
    def index():
        """Render the bare interview page."""
        return render_template("index.html")

    @flask_app.post("/api/sessions")
    def create_session():
        """Create a new interview session with two random questions."""
        session = flask_app.config["INTERVIEW_SERVICE"].create_session()
        return jsonify(session), 201

    @flask_app.get("/api/sessions/<session_id>")
    def get_session(session_id: str):
        """Fetch the persisted session payload."""
        try:
            session = flask_app.config["SESSION_STORAGE"].get_session(session_id)
        except FileNotFoundError:
            return jsonify({"error": "Session not found."}), 404
        return jsonify(session)

    @flask_app.post("/api/interview/upload")
    def upload_audio():
        """Store one combined interview recording and its transcript."""
        session_id = request.form.get("sessionId", "").strip()
        question_id = request.form.get("questionId", "").strip() or "full_interview"
        audio = request.files.get("audio")

        if not session_id or audio is None:
            return (
                jsonify(
                    {
                        "error": "sessionId and audio are required.",
                    }
                ),
                400,
            )

        try:
            response_record = flask_app.config[
                "INTERVIEW_SERVICE"
            ].store_audio_response(
                session_id=session_id,
                question_id=question_id,
                uploaded_file=audio,
            )
        except FileNotFoundError:
            return jsonify({"error": "Session not found."}), 404
        return jsonify(response_record), 201

    return flask_app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
