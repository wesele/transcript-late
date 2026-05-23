import threading
import json
import pyaudio
import vosk
from config import config
from .base import STTEngine


class VoskSTTEngine(STTEngine):
    def __init__(self, on_hypothesis=None, on_recognition=None, on_error=None):
        super().__init__(on_hypothesis, on_recognition, on_error)
        self.sample_rate = 16000
        self.chunk_size = 4000
        self.thread = None

    def start(self):
        self.is_listening = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_listening = False

    def _run_loop(self):
        vosk.SetLogLevel(-1)

        model_name = STTEngine.map_language(config.source_lang, "vosk", config.vosk_model_size)

        if self.on_hypothesis:
            self.on_hypothesis(f"Loading local Vosk {config.vosk_model_size} model ({model_name})...")

        try:
            model = vosk.Model(model_name=model_name)
            recognizer = vosk.KaldiRecognizer(model, self.sample_rate)
        except Exception as e:
            if self.on_error:
                self.on_error(f"Failed to load local Vosk model: {e}")
            if self.on_hypothesis:
                self.on_hypothesis("")
            return

        if self.on_hypothesis:
            self.on_hypothesis("Model loaded. Initializing PyAudio stream...")

        p = pyaudio.PyAudio()
        try:
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            stream.start_stream()
        except Exception as e:
            if self.on_error:
                self.on_error(f"Failed to open PyAudio input stream: {e}")
            p.terminate()
            if self.on_hypothesis:
                self.on_hypothesis("")
            return

        if self.on_hypothesis:
            self.on_hypothesis("")

        try:
            while self.is_listening:
                data = stream.read(2000, exception_on_overflow=False)
                if len(data) == 0:
                    continue
                if recognizer.AcceptWaveform(data):
                    res = json.loads(recognizer.Result())
                    text = res.get("text", "").strip()
                    if text and self.on_recognition:
                        self.on_recognition(text)
                else:
                    res = json.loads(recognizer.PartialResult())
                    partial = res.get("partial", "").strip()
                    if self.on_hypothesis:
                        self.on_hypothesis(partial)
        except Exception as e:
            if self.on_error:
                self.on_error(f"Vosk engine runtime error: {e}")
        finally:
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass
            p.terminate()
