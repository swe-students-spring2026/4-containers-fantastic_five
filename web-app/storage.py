"""Mongo-backed user authentication and analysis session storage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from pymongo import MongoClient  # pylint: disable=import-error


class SessionStorage:
    """Stores users and analysis sessions in MongoDB + local file storage."""

    def __init__(
        self,
        base_path: str | Path,
        mongo_uri: str | None = None,
    ) -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.mongo_uri = mongo_uri or "mongodb://mongodb:27017/appdb"
        self.client = MongoClient(self.mongo_uri)
        self.database_name = self._database_name_from_uri(self.mongo_uri)

    def _users_collection(self):
        """MongoUser: Email and password only."""
        return self.client[self.database_name]["users"]

    def _sessions_collection(self):
        """MongoSession: All analysis data per session."""
        return self.client[self.database_name]["sessions"]

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def create_session(
        self,
        session_id: str,
        user_id: str,
        intended_university: str,
        user_essay: str,
        essay_file_name: str,
        sat_score: int,
        gpa: float,
        notes: str = "",
        essay_pdf_bytes: str = "",
        questions: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Create a new analysis session with all input fields."""
        session_dir = self._session_dir(session_id)
        (session_dir / "audio").mkdir(parents=True, exist_ok=True)
        (session_dir / "transcripts").mkdir(parents=True, exist_ok=True)

        payload = {
            "sessionId": session_id,
            "userId": user_id,
            "user_essay": user_essay,
            "intended_university": intended_university,
            "user_interview_response": "",  # filled in later during interview
            "essay_file_name": essay_file_name,
            "notes": notes,
            "sat_score": sat_score,
            "gpa": gpa,
            "essay_pdf_bytes": essay_pdf_bytes,
            # Parsed LLM output (filled after ML analysis)
            "applicant_score": None,
            "strength": [],
            "missing_elements": [],
            "suggested_edits": [],
            "ai_insights": "",
            # Interview metadata
            "interview": {
                "questions": questions or [],
                "responses": [],
            },
        }
        self._sessions_collection().replace_one(
            {"_id": session_id}, self._to_document(payload, "sessionId"), upsert=True
        )
        self._write_session(session_id, payload)
        return payload

    def get_session(self, session_id: str) -> dict[str, Any]:
        """Load a saved session from MongoDB."""
        document = self._sessions_collection().find_one({"_id": session_id})
        if document is None:
            raise FileNotFoundError(session_id)
        document.pop("_id", None)
        return document

    def get_user_sessions(self, user_id: str) -> list[dict[str, Any]]:
        """Get all analysis sessions for a user."""
        documents = list(self._sessions_collection().find({"userId": user_id}))
        for doc in documents:
            doc.pop("_id", None)
        return documents

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def save_response(
        self,
        session_id: str,
        question_id: str,
        audio_filename: str,
        transcript: str,
        transcript_status: str,
    ) -> dict[str, Any]:
        """Persist one interview response and transcript."""
        payload = self.get_session(session_id)
        response_record = {
            "questionId": question_id,
            "audioPath": str(self._session_dir(session_id) / "audio" / audio_filename),
            "transcriptPath": str(
                self._session_dir(session_id) / "transcripts" / f"{question_id}.txt"
            ),
            "transcriptStatus": transcript_status,
            "transcript": transcript,
        }

        responses = payload["interview"]["responses"]
        responses = [
            item for item in responses if item["questionId"] != question_id
        ] + [response_record]
        payload["interview"]["responses"] = responses

        transcript_file = (
            self._session_dir(session_id) / "transcripts" / f"{question_id}.txt"
        )
        transcript_file.write_text(transcript, encoding="utf-8")
        self._sessions_collection().replace_one(
            {"_id": session_id}, self._to_document(payload, "sessionId")
        )
        self._write_session(session_id, payload)
        return response_record

    def save_analysis_result(
        self,
        session_id: str,
        applicant_score: int | None,
        strength: list[str],
        missing_elements: list[str],
        suggested_edits: list[str],
        ai_insights: str,
    ) -> dict[str, Any]:
        """Save parsed LLM analysis output back to the session."""
        payload = self.get_session(session_id)
        payload["applicant_score"] = applicant_score
        payload["strength"] = strength
        payload["missing_elements"] = missing_elements
        payload["suggested_edits"] = suggested_edits
        payload["ai_insights"] = ai_insights
        self._sessions_collection().replace_one(
            {"_id": session_id}, self._to_document(payload, "sessionId")
        )
        self._write_session(session_id, payload)
        return payload

    def update_interview_response(self, session_id: str) -> str:
        """Concatenate all interview responses into user_interview_response field."""
        payload = self.get_session(session_id)
        full_response = " ".join(
            [r["transcript"] for r in payload["interview"]["responses"]]
        )
        payload["user_interview_response"] = full_response
        self._sessions_collection().replace_one(
            {"_id": session_id}, self._to_document(payload, "sessionId")
        )
        self._write_session(session_id, payload)
        return full_response

    def audio_path(self, session_id: str, filename: str) -> Path:
        """Return the destination path for an uploaded audio file."""
        return self._session_dir(session_id) / "audio" / filename

    # ===== MongoUser Methods =====

    def create_user(self, user_id: str, email: str, password: str) -> dict[str, Any]:
        """Create a new user record (email and password only)."""
        payload = {
            "userId": user_id,
            "email": email,
            "password": password,  # TODO: hash password in production
        }
        self._users_collection().replace_one(
            {"_id": user_id}, self._to_document(payload, "userId"), upsert=True
        )
        return payload

    def get_user(self, user_id: str) -> dict[str, Any]:
        """Retrieve a user by user_id."""
        document = self._users_collection().find_one({"_id": user_id})
        if document is None:
            raise FileNotFoundError(f"User {user_id} not found")
        document.pop("_id", None)
        return document

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """Find a user by email (for login)."""
        document = self._users_collection().find_one({"email": email})
        if document is not None:
            document.pop("_id", None)
        return document

    def user_exists(self, email: str) -> bool:
        """Check if a user with given email exists."""
        return self._users_collection().find_one({"email": email}) is not None

    # ===== Helper Methods =====

    def _session_dir(self, session_id: str) -> Path:
        return self.base_path / session_id

    def _session_file(self, session_id: str) -> Path:
        return self._session_dir(session_id) / "session.json"

    @staticmethod
    def _database_name_from_uri(mongo_uri: str) -> str:
        parsed_uri = urlparse(mongo_uri)
        database_name = parsed_uri.path.lstrip("/")
        return database_name or "appdb"

    @staticmethod
    def _to_document(payload: dict[str, Any], id_key: str) -> dict[str, Any]:
        document = dict(payload)
        document["_id"] = payload[id_key]
        return document

    def _write_session(self, session_id: str, payload: dict[str, Any]) -> None:
        """Write the canonical session JSON file."""
        session_file = self._session_file(session_id)
        session_file.parent.mkdir(parents=True, exist_ok=True)
        with session_file.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
