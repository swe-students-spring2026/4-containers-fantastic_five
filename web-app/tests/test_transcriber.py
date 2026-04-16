"""Tests for transcriber.py."""

# pylint: disable=too-few-public-methods

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transcriber import AudioTranscriber  # pylint: disable=wrong-import-position,import-error


class _Segment:
    """Fake whisper segment."""

    def __init__(self, text):
        """Store fake segment text."""
        self.text = text


class _Model:
    """Fake whisper model."""

    def __init__(self, segments):
        """Store fake segment output."""
        self._segments = segments

    def transcribe(self, _path):
        """Return deterministic fake segments."""
        return self._segments, None


def test_transcribe_returns_fallback_when_model_unavailable(tmp_path):
    """Transcriber should return unavailable if model setup fails."""
    path = tmp_path / "audio.webm"
    path.write_bytes(b"fake")

    transcriber = AudioTranscriber()

    with patch.object(transcriber, "_get_model", side_effect=ImportError("missing")):
        text, status = transcriber.transcribe(path)

    assert status == "unavailable"
    assert "Transcription unavailable" in text


def test_transcribe_returns_completed_text(tmp_path):
    """Transcriber should join returned segment text when transcription works."""
    path = tmp_path / "audio.webm"
    path.write_bytes(b"fake")

    transcriber = AudioTranscriber()

    with patch.object(
        transcriber,
        "_get_model",
        return_value=_Model([_Segment("hello"), _Segment("world")]),
    ):
        text, status = transcriber.transcribe(path)

    assert status == "completed"
    assert text == "hello world"


def test_transcribe_returns_no_speech_message(tmp_path):
    """Transcriber should return the no-speech message when segments are blank."""
    path = tmp_path / "audio.webm"
    path.write_bytes(b"fake")

    transcriber = AudioTranscriber()

    with patch.object(
        transcriber,
        "_get_model",
        return_value=_Model([_Segment(""), _Segment("   ")]),
    ):
        text, status = transcriber.transcribe(path)

    assert status == "completed"
    assert text == "No speech detected in the uploaded audio."