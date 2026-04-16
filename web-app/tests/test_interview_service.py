"""Tests for interview_service.py."""

# pylint: disable=protected-access

import sys
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from interview_service import (  # pylint: disable=wrong-import-position,import-error
    MockInterviewService,
)


def test_detect_extension_from_filename():
    """Filename suffix should win when present."""
    assert MockInterviewService._detect_extension("audio/webm", "answer.mp3") == ".mp3"


def test_detect_extension_from_mimetype():
    """Known mimetypes should map to stable file extensions."""
    assert MockInterviewService._detect_extension("audio/webm", None) == ".webm"
    assert MockInterviewService._detect_extension("audio/ogg", None) == ".ogg"
    assert MockInterviewService._detect_extension("audio/mpeg", None) == ".mp3"
    assert MockInterviewService._detect_extension("audio/wav", None) == ".wav"
    assert MockInterviewService._detect_extension("unknown/type", None) == ".bin"


def test_create_session_uses_storage():
    """Service should delegate session creation to storage."""
    fake_storage = Mock()
    fake_transcriber = Mock()
    fake_storage.create_session.return_value = {"sessionId": "abc"}

    service = MockInterviewService(fake_storage, fake_transcriber)
    result = service.create_session(question_count=2)

    assert result == {"sessionId": "abc"}
    fake_storage.create_session.assert_called_once()


def test_store_audio_response_saves_audio_and_transcript(tmp_path):
    """Service should save audio and persist transcript metadata."""
    fake_storage = Mock()
    fake_transcriber = Mock()
    fake_transcriber.transcribe.return_value = ("hello world", "completed")

    destination = tmp_path / "session1" / "audio" / "q1.webm"
    fake_storage.audio_path.return_value = destination
    fake_storage.save_response.return_value = {"ok": True}

    uploaded_file = Mock()
    uploaded_file.mimetype = "audio/webm"
    uploaded_file.filename = "answer.webm"

    service = MockInterviewService(fake_storage, fake_transcriber)
    result = service.store_audio_response("session1", "q1", uploaded_file)

    uploaded_file.save.assert_called_once_with(destination)
    fake_transcriber.transcribe.assert_called_once_with(destination)
    fake_storage.save_response.assert_called_once()
    assert result == {"ok": True}
