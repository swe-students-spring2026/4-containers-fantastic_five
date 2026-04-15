from __future__ import annotations

import os
import uuid
from datetime import datetime
from pathlib import Path

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    session as flask_session,
    url_for,
)

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
        MONGO_URI=os.environ.get("MONGO_URI", "mongodb://mongodb:27017/appdb"),
    )

    if test_config:
        flask_app.config.update(test_config)

    storage = SessionStorage(
        flask_app.config["SESSION_STORAGE_PATH"],
        mongo_uri=flask_app.config["MONGO_URI"],
    )
    transcriber = AudioTranscriber()
    service = MockInterviewService(storage, transcriber)
    flask_app.config["INTERVIEW_SERVICE"] = service
    flask_app.config["SESSION_STORAGE"] = storage

    # ---------- page routes ----------

    @flask_app.get("/")
    def index():
        """Render the landing page."""
        return render_template("index.html", is_valid=is_logged_in())
    
    @flask_app.route("/login", methods=["GET", "POST"])
    def login():
        """Basic login page."""
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "").strip()

            if not email or not password:
                return render_template("login.html", is_valid=False)

            user = storage.get_user_by_email(email)
            if user is None:
                return render_template("login.html", is_valid=False)

            # check password
            if user.get("password") != password:
                return render_template("login.html", is_valid=False)

            flask_session["user_id"] = user["userId"]
            flask_session["email"] = user["email"]

            return redirect(url_for("dashboard"))

        return render_template("login.html", is_valid=is_logged_in())
    
    @flask_app.route("/signup", methods=["GET", "POST"])
    def signup():
        """Basic signup page."""
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "").strip()
            confirm_password = request.form.get("confirm_password", "").strip()

            if not email or not password:
                return render_template("signup.html", is_valid=False)

            if password != confirm_password:
                return render_template("signup.html", is_valid=False)

            if storage.user_exists(email):
                # if they already exist, just send them to login
                return redirect(url_for("login"))

            user_id = str(uuid.uuid4())
            storage.create_user(user_id=user_id, email=email, password=password)

            flask_session["user_id"] = user_id
            flask_session["email"] = email

            return redirect(url_for("dashboard"))

        return render_template("signup.html", is_valid=is_logged_in())

    @flask_app.get("/logout")
    def logout():
        """Log user out and return to home."""
        flask_session.clear()
        return redirect(url_for("index"))

    @flask_app.get("/dashboard")
    def dashboard():
        """Show all sessions for the current user."""
        login_redirect = require_login()
        if login_redirect:
            return login_redirect

        user_sessions = storage.get_user_sessions(current_user_id())

        # display-friendly fields
        sessions = []
        for raw_session in user_sessions:
            decorated = decorate_session(raw_session)

            # dashboard templates often want a short id field
            decorated["_session_id"] = decorated.get("sessionId", "")
            sessions.append(decorated)

        # pass both names in case your template still uses "runs"
        return render_template(
            "dashboard.html",
            is_valid=True,
            sessions=sessions,
            runs=sessions,
        )

    # ---------- interview routes ----------
    
    @flask_app.post("/api/sessions")
    def create_interview_session():
        """Create a mock interview session with questions."""
        session_data = flask_app.config["INTERVIEW_SERVICE"].create_session()
        return jsonify(session_data), 201

    @flask_app.get("/api/sessions/<session_id>")
    def get_interview_session(session_id: str):
        """Fetch one interview session payload."""
        try:
            session_data = flask_app.config["SESSION_STORAGE"].get_session(session_id)
        except FileNotFoundError:
            return jsonify({"error": "Session not found."}), 404

        return jsonify(session_data)

    @flask_app.post("/api/interview/upload")
    def upload_audio():
        """Store one interview recording and its transcript."""
        session_id = request.form.get("sessionId", "").strip()
        question_id = request.form.get("questionId", "").strip() or "full_interview"
        audio = request.files.get("audio")

        if not session_id or audio is None:
            return jsonify({"error": "sessionId and audio are required."}), 400

        try:
            response_record = flask_app.config["INTERVIEW_SERVICE"].store_audio_response(
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
    app.run(host="0.0.0.0", port=5000, debug=True)