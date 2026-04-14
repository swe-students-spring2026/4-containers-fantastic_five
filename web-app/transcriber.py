"""Audio transcription wrapper with a graceful fallback."""

from __future__ import annotations

from pathlib import Path


class AudioTranscriber:
    """Uses faster-whisper when available, otherwise returns a placeholder."""

    def __init__(self, model_name: str = "base") -> None:
        self.model_name = model_name
        self._model = None

    def transcribe(self, audio_path: str | Path) -> tuple[str, str]:
        path = Path(audio_path)
        try:
            model = self._get_model()
        except (ImportError, OSError) as exc:
            message = (
                "Transcription unavailable. Install faster-whisper and ffmpeg to "
                f"enable local transcription. Details: {exc}"
            )
            return message, "unavailable"

        segments, _ = model.transcribe(str(path))
        text = " ".join(segment.text.strip() for segment in segments).strip()
        if not text:
            text = "No speech detected in the uploaded audio."
        return text, "completed"

    def _get_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel  # pylint: disable=import-error

            self._model = WhisperModel(self.model_name)
        return self._model
