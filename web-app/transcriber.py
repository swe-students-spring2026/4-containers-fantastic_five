"""Audio transcription wrapper with a graceful fallback."""

from __future__ import annotations

from pathlib import Path


# pylint: disable=too-few-public-methods
class AudioTranscriber:
    """Uses faster-whisper when available, otherwise returns a placeholder."""

    def __init__(self, model_name: str = "base") -> None:
        self.model_name = model_name
        self._model = None

    def transcribe(self, audio_path: str | Path) -> tuple[str, str]:
        """Transcribe audio, or return a clear fallback message."""
        path = Path(audio_path)  # turn whatever came in into a real file path
        try:
            model = self._get_model()
        except (ImportError, OSError) as exc:
            message = (  # if Whisper is not installed locally, return a readable fallback instead of crashing
                "Transcription unavailable. Install faster-whisper and ffmpeg to "
                f"enable local transcription. Details: {exc}"
            )
            return message, "unavailable"

        segments, _ = model.transcribe(str(path))  # Whisper gives back chunks, not one finished string
        text = " ".join(segment.text.strip() for segment in segments).strip()  # stitch all the chunks together
        if not text:
            text = "No speech detected in the uploaded audio."
        return text, "completed"

    def _get_model(self):
        """Lazily load the Whisper model so startup stays lightweight."""
        if self._model is None:
            from faster_whisper import (  # pylint: disable=import-error,import-outside-toplevel
                WhisperModel,
            )

            self._model = WhisperModel(self.model_name)  # load once so we do not reinitialize the model every call
        return self._model
