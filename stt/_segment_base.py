import threading
import speech_recognition as sr
from config import config
from .base import STTEngine


class SegmentSTTEngine(STTEngine):
    def __init__(self, on_hypothesis=None, on_recognition=None, on_error=None):
        super().__init__(on_hypothesis, on_recognition, on_error)
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.stop_listening_fn = None

        if config.sensitivity >= 5:
            ratio = 1.5 - (config.sensitivity - 5) * 0.09
        else:
            ratio = 1.5 + (5 - config.sensitivity) * 0.625

        self.recognizer.dynamic_energy_ratio = ratio
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.15
        self.recognizer.energy_threshold = 100 if config.sensitivity >= 5 else 300
        self.recognizer.pause_threshold = 0.8
        self.recognizer.non_speaking_duration = 0.4

    def start(self):
        self.is_listening = True
        threading.Thread(target=self._start_listening, daemon=True).start()

    def stop(self):
        self.is_listening = False
        if self.stop_listening_fn:
            self.stop_listening_fn(wait_for_stop=False)

    def _start_listening(self):
        try:
            if self.on_hypothesis:
                self.on_hypothesis("Calibrating microphone...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.8)
            if self.on_hypothesis:
                self.on_hypothesis("")
            self.stop_listening_fn = self.recognizer.listen_in_background(
                self.microphone,
                self._on_audio_segment,
                phrase_time_limit=15
            )
        except Exception as e:
            if self.on_error:
                self.on_error(f"Failed to start audio capture: {e}")

    def _on_audio_segment(self, recognizer, audio_data):
        if not self.is_listening:
            return
        threading.Thread(target=self._process_segment, args=(audio_data,), daemon=True).start()

    def _process_segment(self, audio_data):
        try:
            if self.on_hypothesis:
                self.on_hypothesis("Processing audio segment...")
            text = self.transcribe(audio_data)
            if text and text.strip():
                if self.on_recognition:
                    self.on_recognition(text)
            else:
                if self.on_hypothesis:
                    self.on_hypothesis("")
        except sr.UnknownValueError:
            if self.on_hypothesis:
                self.on_hypothesis("")
        except sr.RequestError as e:
            if self.on_error:
                self.on_error(f"STT request failed: {e}")
        except Exception as e:
            if self.on_error:
                self.on_error(f"STT error: {e}")

    def transcribe(self, audio_data) -> str:
        raise NotImplementedError
