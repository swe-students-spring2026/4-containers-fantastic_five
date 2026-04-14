"""Interview session orchestration."""

from __future__ import annotations

from pathlib import Path
from random import sample
from typing import Any
from uuid import uuid4

from questions import QUESTION_BANK
from storage import SessionStorage
from transcriber import AudioTranscriber


class MockInterviewService:
    """Generates questions and records transcribed interview answers."""

    def __init__(self, storage: SessionStorage, transcriber: AudioTranscriber) -> None:
        self.storage = storage
        self.transcriber = transcriber

    def create_session(self, question_count: int = 2) -> dict[str, Any]:
        """Create a new session seeded with randomly chosen questions."""
        questions = sample(QUESTION_BANK, question_count)
        session_id = uuid4().hex
        session = self.storage.create_session(session_id, questions)
        return session

    def store_audio_response(
        self,
        session_id: str,
        question_id: str,
        uploaded_file,
    ) -> dict[str, Any]:
        """Save one uploaded audio response and attach its transcript."""
        extension = self._detect_extension(
            uploaded_file.mimetype, uploaded_file.filename
        )
        filename = f"{question_id}{extension}"
        destination = self.storage.audio_path(session_id, filename)
        destination.parent.mkdir(parents=True, exist_ok=True)
        uploaded_file.save(destination)
        transcript, transcript_status = self.transcriber.transcribe(destination)
        return self.storage.save_response(
            session_id=session_id,
            question_id=question_id,
            audio_filename=filename,
            transcript=transcript,
            transcript_status=transcript_status,
        )

    @staticmethod
    def _detect_extension(mimetype: str | None, filename: str | None) -> str:
        """Infer a stable file extension for the uploaded audio blob."""
        if filename and "." in filename:
            return Path(filename).suffix
        if mimetype == "audio/webm":
            return ".webm"
        if mimetype == "audio/ogg":
            return ".ogg"
        if mimetype == "audio/mpeg":
            return ".mp3"
        if mimetype == "audio/wav":
            return ".wav"
        return ".bin"
