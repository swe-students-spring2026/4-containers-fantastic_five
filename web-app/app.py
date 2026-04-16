from __future__ import annotations

import os,asyncio
import sys
import base64
from io import BytesIO
import uuid
from datetime import datetime
from pathlib import Path
import parser
from pypdf import PdfReader
from random import sample

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
from questions import QUESTION_BANK
from storage import SessionStorage
from transcriber import AudioTranscriber

ML_CLIENT_DIR = Path(__file__).resolve().parents[1] / "machine-learning-client"
if str(ML_CLIENT_DIR) not in sys.path:
    sys.path.insert(0, str(ML_CLIENT_DIR))

from main import CMRun


def extract_pdf_text(pdf_bytes: bytes) -> str:
    #if the uploaded file is emply, return error
    if not pdf_bytes:
        return "error: input pdf file"
    #conver the pdf into a file object so the pdf reader can read it
    reader = PdfReader(BytesIO(pdf_bytes))
    #go through each page and extract the text, then join all the text into one string
    pages_text = [(page.extract_text() or "").strip() for page in reader.pages]
    return "\n\n".join(text for text in pages_text if text).strip()
interview_output = "" 

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
    # ---------- small helpers ----------

    def is_logged_in() -> bool:
        """Simple auth check based on Flask session."""
        return bool(flask_session.get("user_id"))

    def require_login():
        """Redirect to login page if user is not logged in."""
        if not is_logged_in():
            return redirect(url_for("login"))
        return None

    def current_user_id() -> str:
        """Return current user id from Flask session."""
        return flask_session.get("user_id", "")

    def decorate_session(raw_session: dict) -> dict:
        """
        Add a few display fields so the templates do not break.
        storage.py does not fully manage created_at / status yet,
        so we fill in defaults here.
        """
        session_copy = dict(raw_session)

        if "created_at" not in session_copy:
            session_copy["created_at"] = "Unknown"

        if "status" not in session_copy:
            # if score exists, treat it as complete; otherwise pending
            if session_copy.get("applicant_score") is not None:
                session_copy["status"] = "COMPLETE"
            else:
                session_copy["status"] = "PENDING"

        return session_copy

    def save_session_document(session_payload: dict) -> None:
        """
        Small helper to write the full session back to Mongo.
        This uses the storage layer's Mongo collection directly so we can
        preserve custom fields like created_at and status.
        """
        storage._sessions_collection().replace_one(  # pylint: disable=protected-access
            {"_id": session_payload["sessionId"]},
            storage._to_document(session_payload, "sessionId"),  # pylint: disable=protected-access
            upsert=True,
        )

    def read_uploaded_text(uploaded_file) -> tuple[str, str, str]:
        """
        Best-effort file reader.
        Keeps things simple for now. Works best with txt files.
        PDF/DOCX bytes are still stored, even if text extraction is weak.
        """
        if uploaded_file is None or not uploaded_file.filename:
            return "", "", ""

        raw_bytes = uploaded_file.read()
        file_name = uploaded_file.filename

        # basic text decode for now
        essay_text = raw_bytes.decode("utf-8", errors="ignore").strip()

        # keep raw bytes in a string-safe format
        essay_bytes_string = raw_bytes.decode("latin-1", errors="ignore")

        return essay_text, file_name, essay_bytes_string

    # ---------- page routes ----------

    @flask_app.get("/")
    def index():
        """landing page"""
        return render_template("index.html", is_valid=is_logged_in())
    
    @flask_app.route("/login", methods=["GET", "POST"])
    def login():
        """ login page."""
        if request.method == "POST":
            email = request.form.get("email", "").lower()
            password = request.form.get("password", "")
            #ensure that both are inputed
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
            #getdata from submitted form
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "").strip()
            confirm_password = request.form.get("confirm_password", "").strip()
            #if the inputs are invalid just go back to the screen
            if not email or not password:
                return render_template("signup.html", is_valid=False)
            #check if the 2 passwords are the same
            if password != confirm_password:
                return render_template("signup.html", is_valid=False)
            if storage.user_exists(email):
                #if they already exist, just send them to login
                return redirect(url_for("login"))
            user_id = str(uuid.uuid4())
            storage.create_user(user_id=user_id, email=email, password=password)
            flask_session["user_id"] = user_id
            flask_session["email"] = email
            return redirect(url_for("dashboard"))
        #if the request is GET
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

        #display-friendly fields
        sessions = []
        for raw_session in user_sessions:
            decorated = decorate_session(raw_session)

            # dashboard templates often want a short id field
            decorated["_session_id"] = decorated.get("sessionId", "")
            sessions.append(decorated)
        #pass both names in case your template still uses "runs"
        return render_template("dashboard.html", is_valid=True,sessions=sessions,runs=sessions,)
    
    
    @flask_app.route("/runs/new", methods=["GET", "POST"])
    def new_session():
        """
        New session page.
        Right now this mostly renders the form page.
        If you later decide to POST here, this route is ready for it.
        """
        login_redirect = require_login()
        if login_redirect:
            return login_redirect

        if request.method == "POST":
            uploaded_file = request.files.get("user_essay")
            intended_university = request.form.get("intended_university", "").strip()
            sat_score_raw = request.form.get("sat_score", "").strip()
            gpa_raw = request.form.get("gpa", "").strip()
            notes = request.form.get("notes", "").strip()
            essay_file_name =uploaded_file.filename if uploaded_file and uploaded_file.filename else "Not provided"
            essay_pdf_bytes = uploaded_file.read()
            usser_essay = extract_pdf_text(essay_pdf_bytes or b"")
            essay_pdf_b64 = base64.b64encode(essay_pdf_bytes).decode("utf-8") if essay_pdf_bytes else ""

            sat_score = int(sat_score_raw) if sat_score_raw.isdigit() else 0
            try:
                gpa = float(gpa_raw) if gpa_raw else 0.0
            except ValueError:
                gpa = 0.0

            session_id = str(uuid.uuid4())

            session_payload = storage.create_session(session_id,current_user_id(),intended_university,usser_essay,essay_file_name,sat_score,gpa,notes,essay_pdf_b64,
            )

            # Save session with PENDING status; analysis runs after the interview
            session_payload["created_at"] = datetime.utcnow().isoformat()
            session_payload["status"] = "PENDING"
            save_session_document(session_payload)

            return redirect(url_for("interview", session_id=session_id))

        return render_template("newSession.html", is_valid=True)

    @flask_app.get("/interview")
    def interview():
        """Mock interview page."""
        login_redirect = require_login()
        if login_redirect:
            return login_redirect

        session_id = request.args.get("session_id", "")
        return render_template("interview.html", is_valid=True, session_id=session_id)

    @flask_app.post("/runs/<session_id>/analyze")
    def analyze_session(session_id: str):
        """Run the ML analysis on a saved session and redirect to its detail page."""
        login_redirect = require_login()
        if login_redirect:
            return login_redirect

        try:
            raw_session = storage.get_session(session_id)
        except FileNotFoundError:
            return redirect(url_for("dashboard"))

        if raw_session.get("userId") != current_user_id():
            return redirect(url_for("dashboard"))

        essay_pdf_b64 = raw_session.get("essay_pdf_bytes", "")
        try:
            essay_pdf_bytes = (
                base64.b64decode(essay_pdf_b64) if essay_pdf_b64 else b""
            )
        except (ValueError, TypeError):
            essay_pdf_bytes = b""

        output = asyncio.run(
            CMRun(
                user_essay=raw_session.get("user_essay", ""),
                essay_file_name=raw_session.get("essay_file_name", ""),
                essay_pdf_bytes=essay_pdf_bytes,
                gpa=raw_session.get("gpa", 0.0),
                notes=raw_session.get("notes", ""),
                user_interview_response=raw_session.get("user_interview_response", interview_output),
                intended_university=raw_session.get("intended_university", ""),
                sat_score=raw_session.get("sat_score", 0),
            )
        )

        output_result = (
            output.get("result")
            if isinstance(output, dict)
            else getattr(output, "result", None)
        )

        if output_result:
            parsed = parser.parse_agent_output(output_result)
            updated_session = storage.save_analysis_result(
                session_id=session_id,
                applicant_score=parsed["applicant_score"],
                strength=parsed["strength"],
                missing_elements=parsed["missing_elements"],
                suggested_edits=parsed["suggested_edits"],
                ai_insights=parsed["ai_insights"],
            )
            updated_session["status"] = "COMPLETE"
            updated_session["created_at"] = updated_session.get(
                "created_at", raw_session.get("created_at", "")
            )
            save_session_document(updated_session)
        else:
            # Even if parsing fails, mark as complete because analysis finished.
            raw_session["status"] = "COMPLETE"
            raw_session["created_at"] = raw_session.get("created_at", datetime.utcnow().isoformat())
            save_session_document(raw_session)

        return redirect(url_for("session_detail", session_id=session_id))

    @flask_app.get("/runs/<session_id>")
    def session_detail(session_id: str):
        """Detail page for one saved analysis session."""
        login_redirect = require_login()
        if login_redirect:
            return login_redirect

        try:
            raw_session = storage.get_session(session_id)
        except FileNotFoundError:
            return redirect(url_for("dashboard"))

        # basic ownership check
        if raw_session.get("userId") != current_user_id():
            return redirect(url_for("dashboard"))

        session_data = decorate_session(raw_session)

        return render_template(
            "sessionDetail.html",
            is_valid=True,
            session=session_data,
        )
    # ---------- interview routes ----------

    @flask_app.post("/api/sessions")
    def create_interview_session():
        """Create a mock interview session with questions."""
        login_redirect = require_login()
        if login_redirect:
            return jsonify({"error": "Not logged in."}), 401

        questions = sample(QUESTION_BANK, 2)
        session_id = uuid.uuid4().hex
        session_data = storage.create_session(
            session_id=session_id,
            user_id=current_user_id(),
            intended_university="",
            user_essay="",
            essay_file_name="",
            sat_score=0,
            gpa=0.0,
            notes="",
            essay_pdf_bytes="",
            questions=questions,
        )
        session_data["created_at"] = datetime.utcnow().isoformat()
        session_data["status"] = "PENDING"
        save_session_document(session_data)
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
        global interview_output

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
            session_data = flask_app.config["SESSION_STORAGE"].get_session(session_id)
        except FileNotFoundError:
            return jsonify({"error": "Session not found."}), 404

        question_lines = [
            f"Question {index}: {question['text']}"
            for index, question in enumerate(
                session_data.get("interview", {}).get("questions", []),
                start=1,
            )
            if question.get("text")
        ]
        interview_output = "\n".join(
            question_lines + ["", "Transcript:", response_record["transcript"]]
        ).strip()

        return jsonify(response_record), 201
    
   
    return flask_app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
