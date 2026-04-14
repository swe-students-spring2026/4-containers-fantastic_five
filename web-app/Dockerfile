FROM python:3.12-slim

WORKDIR /app

#install ffmpeg (needed for faster-whisper)
RUN apt-get update && apt-get install -y ffmpeg

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]