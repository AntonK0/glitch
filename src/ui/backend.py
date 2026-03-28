import os
import subprocess
import sys
import tempfile
import threading
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd
from dotenv import load_dotenv
from PySide6.QtCore import Property, QObject, Signal, Slot

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPTS = PROJECT_ROOT / "scripts"

SAMPLE_RATE = 16_000
CHANNELS = 1


class Backend(QObject):
    agentReadyChanged = Signal()
    isRecordingChanged = Signal()
    currentModeChanged = Signal()
    lastOutputChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._agentReady = False
        self._isRecording = False
        self._currentMode = "suggest"
        self._lastOutput = "> Awaiting input\n> Ready for composition assistance"
        self._audio_frames: list[np.ndarray] = []
        self._recording_stream: sd.InputStream | None = None
        self._recording_type: str = ""

        threading.Thread(target=self._check_ready, daemon=True).start()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _check_ready(self):
        ext = ".bat" if os.name == "nt" else ".sh"
        scripts = [f"run_voice_suggest{ext}", f"run_voice_demo{ext}", f"run_hum{ext}"]
        missing = [
            s
            for s in scripts
            if not (SCRIPTS / s).exists()
        ]
        self._agentReady = len(missing) == 0
        self.agentReadyChanged.emit()
        if missing:
            self._append(f"> Warning: scripts not found: {', '.join(missing)}")
        else:
            self._append("> Agent systems online")

    def _append(self, line: str):
        print(line, flush=True)  # Reroute to terminal
        self._lastOutput = self._lastOutput + "\n" + line
        self.lastOutputChanged.emit()

    # ── Qt Properties ─────────────────────────────────────────────────────────

    @Property(bool, notify=agentReadyChanged)
    def agentReady(self):
        return self._agentReady

    @Property(bool, notify=isRecordingChanged)
    def isRecording(self):
        return self._isRecording

    @Property(str, notify=currentModeChanged)
    def currentMode(self):
        return self._currentMode

    @Property(str, notify=lastOutputChanged)
    def lastOutput(self):
        return self._lastOutput

    # ── QML Slots ─────────────────────────────────────────────────────────────

    @Slot()
    def startVoicePrompt(self):
        if self._isRecording:
            return
        self._recording_type = "voice"
        self._start_recording()

    @Slot()
    def startHumming(self):
        if self._isRecording:
            return
        self._recording_type = "humming"
        self._start_recording()

    @Slot()
    def stopRecording(self):
        if not self._isRecording:
            return
        recording_type = self._recording_type
        frames = list(self._audio_frames)
        self._stop_recording()
        self._append(f"> Audio data size: {sum(f.nbytes for f in frames)} bytes")
        threading.Thread(
            target=self._process_audio,
            args=(recording_type, frames),
            daemon=True,
        ).start()

    @Slot(str)
    def setMode(self, mode: str):
        if mode in ("suggest", "demo") and mode != self._currentMode:
            self._currentMode = mode
            self.currentModeChanged.emit()
            self._append(f"> Mode: {mode.upper()}")

    # ── Recording ─────────────────────────────────────────────────────────────

    def _start_recording(self):
        self._audio_frames = []
        self._isRecording = True
        self.isRecordingChanged.emit()
        self._append("> Recording… tap again to stop")

        def _cb(indata, frames, time_info, status):
            self._audio_frames.append(indata.copy())

        self._recording_stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            callback=_cb,
        )
        self._recording_stream.start()

    def _stop_recording(self):
        if self._recording_stream:
            self._recording_stream.stop()
            self._recording_stream.close()
            self._recording_stream = None
        self._isRecording = False
        self.isRecordingChanged.emit()
        self._append("> Recording stopped — processing…")

    def _save_wav(self, frames: list[np.ndarray], path: str):
        data = np.concatenate(frames, axis=0)
        # Check if the audio is almost silent (useful for debugging)
        max_amp = np.abs(data).max()
        if max_amp < 100: # Very low threshold for 16-bit PCM
            print(f"--- Warning: Recording is almost silent (Max amplitude: {max_amp}) ---", flush=True)
            self._append("> Warning: Recorded audio is very quiet or silent. Please check your microphone.")
        else:
            print(f"--- Recording max amplitude: {max_amp} ---", flush=True)
            
        with wave.open(path, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(data.tobytes())

    # ── Audio dispatch → scripts ──────────────────────────────────────────────

    def _process_audio(self, recording_type: str, frames: list[np.ndarray]):
        if not frames:
            self._append("> No audio captured.")
            return

        tmp_path = os.path.join(tempfile.gettempdir(), f"muse_{recording_type}.wav")
        self._save_wav(frames, tmp_path)

        ext = ".bat" if os.name == "nt" else ".sh"
        if recording_type == "voice":
            script = (
                f"run_voice_suggest{ext}"
                if self._currentMode == "suggest"
                else f"run_voice_demo{ext}"
            )
        else:
            script = f"run_hum{ext}"

        self._run_script([str(SCRIPTS / script), tmp_path])

    def _run_script(self, cmd: list[str]):
        env = os.environ.copy()
        env.setdefault("PYTHON_314", sys.executable)
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
                cwd=str(PROJECT_ROOT),
                shell=(os.name == "nt"),
            )
            for line in proc.stdout:
                stripped = line.rstrip()
                if stripped:
                    self._append(stripped)
            proc.wait()
            if proc.returncode != 0:
                self._append(f"> Script exited with code {proc.returncode}")
        except Exception as exc:
            self._append(f"> Error launching script: {exc}")
