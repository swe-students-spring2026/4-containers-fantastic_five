"""Filesystem-backed interview session storage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SessionStorage:
    """Stores interview sessions as JSON plus per-question transcript files."""

    def __init__(self, base_path: str | Path) -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def create_session(
        self, session_id: str, questions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Create directories and the initial session payload."""
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
        self._write_session(session_id, payload)
        return payload

    def get_session(self, session_id: str) -> dict[str, Any]:
        """Load a saved session from disk."""
        session_file = self._session_file(session_id)
        with session_file.open("r", encoding="utf-8") as handle:
            return json.load(handle)

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
        self._write_session(session_id, payload)
        return response_record

    def audio_path(self, session_id: str, filename: str) -> Path:
        """Return the destination path for an uploaded audio file."""
        return self._session_dir(session_id) / "audio" / filename

    def _session_dir(self, session_id: str) -> Path:
        return self.base_path / session_id

    def _session_file(self, session_id: str) -> Path:
        return self._session_dir(session_id) / "session.json"

    def _write_session(self, session_id: str, payload: dict[str, Any]) -> None:
        """Write the canonical session JSON file."""
        session_file = self._session_file(session_id)
        session_file.parent.mkdir(parents=True, exist_ok=True)
        with session_file.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
