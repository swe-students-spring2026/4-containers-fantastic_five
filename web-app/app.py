"""Minimal Flask app for the mock interview workflow."""

from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, render_template, request

from interview_service import MockInterviewService
from storage import SessionStorage
from transcriber import AudioTranscriber


def create_app(test_config: dict | None = None) -> Flask:
    """Application factory used by the dev server and tests."""

    app = Flask(__name__)
    data_dir = Path(app.root_path) / "data" / "sessions"
    app.config.update(
        SECRET_KEY="development-key",
        SESSION_STORAGE_PATH=data_dir,
    )

    if test_config:
        app.config.update(test_config)

    storage = SessionStorage(app.config["SESSION_STORAGE_PATH"])
    transcriber = AudioTranscriber()
    service = MockInterviewService(storage, transcriber)
    app.config["INTERVIEW_SERVICE"] = service
    app.config["SESSION_STORAGE"] = storage

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/api/sessions")
    def create_session():
        session = app.config["INTERVIEW_SERVICE"].create_session()
        return jsonify(session), 201

    @app.get("/api/sessions/<session_id>")
    def get_session(session_id: str):
        try:
            session = app.config["SESSION_STORAGE"].get_session(session_id)
        except FileNotFoundError:
            return jsonify({"error": "Session not found."}), 404
        return jsonify(session)

    @app.post("/api/interview/upload")
    def upload_audio():
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
            response_record = app.config["INTERVIEW_SERVICE"].store_audio_response(
                session_id=session_id,
                question_id=question_id,
                uploaded_file=audio,
            )
        except FileNotFoundError:
            return jsonify({"error": "Session not found."}), 404
        return jsonify(response_record), 201

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
