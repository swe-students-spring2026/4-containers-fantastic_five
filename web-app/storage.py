"""Mongo-backed interview session storage with per-question transcript files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from pymongo import MongoClient


class SessionStorage:
    """Stores interview sessions in MongoDB plus per-question transcript files."""

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

    def _collection(self):
        return self.client[self.database_name]["sessions"]

    def create_session(
        self, session_id: str, questions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Create directories and persist the initial session payload."""
        session_dir = self._session_dir(session_id)
        (session_dir / "audio").mkdir(parents=True, exist_ok=True)
        (session_dir / "transcripts").mkdir(parents=True, exist_ok=True)
        payload = {
            "sessionId": session_id,
            "interview": {
                "questions": questions,
                "responses": [],
            },
        }
        self._collection().replace_one(
            {"_id": session_id}, self._to_document(payload), upsert=True
        )
        self._write_session(session_id, payload)
        return payload

    def get_session(self, session_id: str) -> dict[str, Any]:
        """Load a saved session from MongoDB."""
        document = self._collection().find_one({"_id": session_id})
        if document is None:
            raise FileNotFoundError(session_id)
        document.pop("_id", None)
        return document

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def save_response(
        self,
        session_id: str,
        question_id: str,
        audio_filename: str,
        transcript: str,
        transcript_status: str,
    ) -> dict[str, Any]:
        """Persist one response record plus its plain-text transcript file."""
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
        self._collection().replace_one({"_id": session_id}, self._to_document(payload))
        self._write_session(session_id, payload)
        return response_record

    def audio_path(self, session_id: str, filename: str) -> Path:
        """Return the destination path for an uploaded audio file."""
        return self._session_dir(session_id) / "audio" / filename

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
    def _to_document(payload: dict[str, Any]) -> dict[str, Any]:
        document = dict(payload)
        document["_id"] = payload["sessionId"]
        return document

    def _write_session(self, session_id: str, payload: dict[str, Any]) -> None:
        """Write the canonical session JSON file."""
        session_file = self._session_file(session_id)
        session_file.parent.mkdir(parents=True, exist_ok=True)
        with session_file.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
