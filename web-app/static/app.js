const startSessionButton = document.getElementById("start-session");
const sessionStatus = document.getElementById("session-status");
const questionPanel = document.getElementById("question-panel");
const questionList = document.getElementById("question-list");
const recordPanel = document.getElementById("record-panel");
const recordButton = document.getElementById("record-button");
const stopButton = document.getElementById("stop-button");
const recordingStatus = document.getElementById("recording-status");
const timerElement = document.getElementById("timer");
const transcriptPanel = document.getElementById("transcript-panel");
const responsesContainer = document.getElementById("responses");

let activeSession = null;
let mediaRecorder = null;
let mediaStream = null;
let recordedChunks = [];
let recordingStartedAt = null;
let timerInterval = null;

startSessionButton.addEventListener("click", async () => {
  sessionStatus.textContent = "Creating session...";
  const response = await fetch("/api/sessions", { method: "POST" });
  activeSession = await response.json();
  renderSession(activeSession);
  sessionStatus.textContent = "Interview ready.";
});

recordButton.addEventListener("click", async () => {
  if (!activeSession) {
    return;
  }

  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch (error) {
    recordingStatus.textContent = `Microphone access failed: ${error.message}`;
    return;
  }

  recordedChunks = [];
  const mimeType = MediaRecorder.isTypeSupported("audio/webm")
    ? "audio/webm"
    : "";
  mediaRecorder = new MediaRecorder(mediaStream, mimeType ? { mimeType } : undefined);

  mediaRecorder.addEventListener("dataavailable", (event) => {
    if (event.data.size > 0) {
      recordedChunks.push(event.data);
    }
  });

  mediaRecorder.addEventListener("stop", async () => {
    const blob = new Blob(recordedChunks, { type: mediaRecorder.mimeType || "audio/webm" });
    await uploadRecording(blob);
    cleanupRecorder();
  });

  mediaRecorder.start();
  recordButton.disabled = true;
  stopButton.disabled = false;
  recordingStatus.textContent = "Recording in progress...";
  recordingStartedAt = Date.now();
  startTimer();

  window.setTimeout(() => {
    if (mediaRecorder && mediaRecorder.state === "recording") {
      stopRecording();
    }
  }, 5 * 60 * 1000);
});

stopButton.addEventListener("click", () => {
  stopRecording();
});

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    mediaRecorder.stop();
    recordingStatus.textContent = "Uploading audio...";
    stopButton.disabled = true;
    stopTimer();
  }
}

function renderSession(session) {
  questionPanel.hidden = false;
  recordPanel.hidden = false;
  transcriptPanel.hidden = false;

  questionList.innerHTML = "";
  responsesContainer.innerHTML = "";

  session.interview.questions.forEach((question) => {
    const item = document.createElement("li");
    item.textContent = question.text;
    questionList.appendChild(item);
  });

  recordButton.disabled = false;
}

async function uploadRecording(blob) {
  const formData = new FormData();
  formData.append("sessionId", activeSession.sessionId);
  formData.append("audio", blob, "full_interview.webm");

  const response = await fetch("/api/interview/upload", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorPayload = await response.json();
    recordingStatus.textContent = errorPayload.error || "Upload failed.";
    recordButton.disabled = false;
    return;
  }

  const payload = await response.json();
  recordingStatus.textContent = `Transcript status: ${payload.transcriptStatus}`;
  await refreshSession();
  recordButton.disabled = false;
}

async function refreshSession() {
  const response = await fetch(`/api/sessions/${activeSession.sessionId}`);
  activeSession = await response.json();
  renderResponses(activeSession);
}

function renderResponses(session) {
  responsesContainer.innerHTML = "";
  session.interview.responses.forEach((response) => {
    const wrapper = document.createElement("article");
    wrapper.className = "response-card";

    const heading = document.createElement("h3");
    heading.textContent = "Combined response for both questions";
    wrapper.appendChild(heading);

    const status = document.createElement("p");
    status.textContent = `Transcript status: ${response.transcriptStatus}`;
    wrapper.appendChild(status);

    const transcript = document.createElement("pre");
    transcript.textContent = response.transcript;
    wrapper.appendChild(transcript);

    responsesContainer.appendChild(wrapper);
  });
}

function startTimer() {
  stopTimer();
  timerInterval = window.setInterval(() => {
    const elapsedSeconds = Math.floor((Date.now() - recordingStartedAt) / 1000);
    const minutes = String(Math.floor(elapsedSeconds / 60)).padStart(2, "0");
    const seconds = String(elapsedSeconds % 60).padStart(2, "0");
    timerElement.textContent = `${minutes}:${seconds}`;
  }, 250);
}

function stopTimer() {
  if (timerInterval) {
    window.clearInterval(timerInterval);
    timerInterval = null;
  }
}

function cleanupRecorder() {
  if (mediaStream) {
    mediaStream.getTracks().forEach((track) => track.stop());
    mediaStream = null;
  }
  mediaRecorder = null;
}
