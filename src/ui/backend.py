import asyncio
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
from google import genai
from google.genai import types as gt
from PySide6.QtCore import Property, QObject, Signal, Slot

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPTS = PROJECT_ROOT / "scripts"

SAMPLE_RATE = 16_000
CHANNELS = 1

# Gemini Live API config for voice transcription
LIVE_MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"
LIVE_CONFIG = {
    "response_modalities": ["AUDIO"],
    "input_audio_transcription": {},
}

# Size of audio chunks sent to the Live API (100ms of 16-bit mono @ 16kHz)
CHUNK_SAMPLES = SAMPLE_RATE // 10  # 1600 samples = 100ms


class Backend(QObject):
    agentReadyChanged = Signal()
    isRecordingChanged = Signal()
    currentModeChanged = Signal()
    lastOutputChanged = Signal()
    transcriptionTextChanged = Signal()
    isPlayingAccompanimentChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._agentReady = False
        self._isRecording = False
        self._currentMode = "suggest"
        self._lastOutput = "> Awaiting input\n> Ready for composition assistance"
        self._transcriptionText = ""
        self._audio_frames: list[np.ndarray] = []
        self._recording_stream: sd.InputStream | None = None
        self._recording_type: str = ""
        self._isPlayingAccompaniment = False
        self._playback_stream: sd.OutputStream | None = None

        # Gemini Live session state
        self._live_loop: asyncio.AbstractEventLoop | None = None
        self._live_stop_event: threading.Event = threading.Event()
        self._audio_queue: asyncio.Queue | None = None

        self._genai_client = genai.Client(
            api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        )

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

    def _set_transcription(self, text: str):
        self._transcriptionText = text
        self.transcriptionTextChanged.emit()

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

    @Property(str, notify=transcriptionTextChanged)
    def transcriptionText(self):
        return self._transcriptionText

    @Property(bool, notify=isPlayingAccompanimentChanged)
    def isPlayingAccompaniment(self):
        return self._isPlayingAccompaniment

    # ── QML Slots ─────────────────────────────────────────────────────────────

    @Slot()
    def startVoicePrompt(self):
        if self._isRecording:
            return
        self._recording_type = "voice"
        self._start_voice_live_session()

    @Slot()
    def startAccompaniment(self):
        if self._isRecording:
            return
        self._recording_type = "accompaniment"
        self._start_voice_live_session()

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
        if self._recording_type == "voice":
            self._stop_voice_live_session()
        else:
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

    @Slot()
    def playAccompaniment(self):
        if self._isPlayingAccompaniment:
            self._stop_accompaniment_playback()
            return
        wav_path = str(PROJECT_ROOT / "accompaniment.wav")
        if not os.path.exists(wav_path):
            self._append("> No accompaniment file found. Generate one first.")
            return
        threading.Thread(
            target=self._play_accompaniment_thread,
            args=(wav_path,),
            daemon=True,
        ).start()

    def _play_accompaniment_thread(self, wav_path: str):
        try:
            with wave.open(wav_path, "rb") as wf:
                sr = wf.getframerate()
                ch = wf.getnchannels()
                frames = wf.readframes(wf.getnframes())
            audio = np.frombuffer(frames, dtype=np.int16)
            if ch > 1:
                audio = audio.reshape(-1, ch)

            self._isPlayingAccompaniment = True
            self.isPlayingAccompanimentChanged.emit()
            self._append("> Playing accompaniment…")

            sd.play(audio, samplerate=sr)
            sd.wait()
        except Exception as exc:
            self._append(f"> Playback error: {exc}")
        finally:
            self._isPlayingAccompaniment = False
            self.isPlayingAccompanimentChanged.emit()

    def _stop_accompaniment_playback(self):
        sd.stop()
        self._isPlayingAccompaniment = False
        self.isPlayingAccompanimentChanged.emit()
        self._append("> Playback stopped.")

    # ── Gemini Live Streaming (Voice Prompt) ──────────────────────────────────

    def _start_voice_live_session(self):
        """Open a Gemini Live session and stream microphone audio for transcription."""
        self._isRecording = True
        self.isRecordingChanged.emit()
        self._set_transcription("")
        self._append("> 🎙 Live transcription active — speak now…")

        self._live_stop_event.clear()

        # Start the asyncio event loop in a background thread
        threading.Thread(target=self._run_live_loop, daemon=True).start()

    def _run_live_loop(self):
        """Background thread: run the asyncio event loop for the Live session."""
        loop = asyncio.new_event_loop()
        self._live_loop = loop
        try:
            loop.run_until_complete(self._live_session_coro())
        except Exception as exc:
            self._append(f"> Live session error: {exc}")
        finally:
            loop.close()
            self._live_loop = None

    async def _live_session_coro(self):
        """Core coroutine: connect to Gemini Live, stream audio, receive transcription."""
        self._audio_queue = asyncio.Queue()
        accumulated_text = ""

        async with self._genai_client.aio.live.connect(
            model=LIVE_MODEL, config=LIVE_CONFIG
        ) as session:

            # ── Microphone → queue ─────────────────────────────────
            def _audio_callback(indata, frames, time_info, status):
                if not self._live_stop_event.is_set():
                    # Put raw PCM bytes into the asyncio queue (thread-safe)
                    pcm_bytes = indata.copy().tobytes()
                    try:
                        self._audio_queue.put_nowait(pcm_bytes)
                    except asyncio.QueueFull:
                        pass  # Drop frames if queue is full (unlikely)

            stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype="int16",
                blocksize=CHUNK_SAMPLES,
                callback=_audio_callback,
            )
            stream.start()

            # ── Sender task: queue → Gemini Live ───────────────────
            async def sender():
                try:
                    while not self._live_stop_event.is_set():
                        try:
                            pcm_bytes = await asyncio.wait_for(
                                self._audio_queue.get(), timeout=0.2
                            )
                            await session.send_realtime_input(
                                audio=gt.Blob(
                                    data=pcm_bytes,
                                    mime_type=f"audio/pcm;rate={SAMPLE_RATE}",
                                )
                            )
                        except asyncio.TimeoutError:
                            continue
                except Exception as exc:
                    if not self._live_stop_event.is_set():
                        self._append(f"> Sender error: {exc}")
                finally:
                    # Signal end of audio stream
                    try:
                        await session.send_realtime_input(audio_stream_end=True)
                    except Exception:
                        pass

            # ── Receiver task: Gemini Live → transcription ─────────
            async def receiver():
                nonlocal accumulated_text
                try:
                    async for msg in session.receive():
                        # Check for input transcription events
                        if (
                            msg.server_content
                            and msg.server_content.input_transcription
                            and msg.server_content.input_transcription.text
                        ):
                            chunk = msg.server_content.input_transcription.text
                            accumulated_text += chunk
                            self._set_transcription(accumulated_text.strip())

                        # Also capture direct text responses (fallback / model response)
                        if msg.text is not None:
                            # The model's text response after VAD detects end-of-speech
                            # This is effectively the transcription in TEXT mode
                            if not accumulated_text:
                                accumulated_text = msg.text
                                self._set_transcription(accumulated_text.strip())

                        # If turn is complete and we're stopping, break
                        if (
                            msg.server_content
                            and msg.server_content.turn_complete
                            and self._live_stop_event.is_set()
                        ):
                            break
                except Exception as exc:
                    if not self._live_stop_event.is_set():
                        self._append(f"> Receiver error: {exc}")

            # Run sender and receiver concurrently
            sender_task = asyncio.create_task(sender())
            receiver_task = asyncio.create_task(receiver())

            # Wait for stop signal
            while not self._live_stop_event.is_set():
                await asyncio.sleep(0.1)

            # Give a moment for final transcription to arrive
            await asyncio.sleep(1.0)

            # Cancel sender, let receiver drain
            sender_task.cancel()
            try:
                await sender_task
            except asyncio.CancelledError:
                pass

            # Give receiver a moment then cancel
            receiver_task.cancel()
            try:
                await receiver_task
            except asyncio.CancelledError:
                pass

            # Clean up microphone
            stream.stop()
            stream.close()

        # Session is now closed — launch the voice pipeline with transcribed text
        final_text = accumulated_text.strip()
        if final_text:
            self._append(f"> You said: {final_text}")
            self._run_voice_pipeline(final_text)
        else:
            self._append("> No speech detected.")

    def _stop_voice_live_session(self):
        """Signal the Live session to stop and update UI state."""
        self._live_stop_event.set()
        self._isRecording = False
        self.isRecordingChanged.emit()
        self._append("> Recording stopped — finalizing transcription…")

    def _run_voice_pipeline(self, transcribed_text: str):
        """Route to composer or accompaniment agent based on recording type."""
        if self._recording_type == "accompaniment":
            self._append("> Running accompaniment agent…")
            cmd = [
                sys.executable,
                str(PROJECT_ROOT / "src" / "agents" / "accompany_agent.py"),
                transcribed_text,
            ]
        else:
            self._append("> Running composer agent…")
            cmd = [sys.executable, str(PROJECT_ROOT / "src" / "agents" / "composer_agent.py"), transcribed_text]
        self._run_script(cmd)

    # ── Legacy Recording (Humming only) ───────────────────────────────────────

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

    # ── Audio dispatch → scripts (humming only now) ───────────────────────────

    def _process_audio(self, recording_type: str, frames: list[np.ndarray]):
        if not frames:
            self._append("> No audio captured.")
            return

        tmp_path = os.path.join(tempfile.gettempdir(), f"muse_{recording_type}.wav")
        self._save_wav(frames, tmp_path)

        ext = ".bat" if os.name == "nt" else ".sh"
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
