Minimal Flask app for the mock interview workflow.

Key routes:
- GET / : bare HTML/JS interview page
- POST /api/sessions : create a session and return 2 random questions
- POST /api/interview/upload : upload one audio answer for transcription
- GET /api/sessions/<session_id> : inspect saved session data

Notes:
- Browser recording uses the MediaRecorder API and typically uploads .webm audio.
- Local transcription uses faster-whisper when installed and available.
- If faster-whisper or ffmpeg is missing, the app still stores the audio and returns a clear "unavailable" transcript status.
