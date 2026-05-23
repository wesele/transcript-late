import numpy as np
from config import config
from ._segment_base import SegmentSTTEngine
from .base import STTEngine


class WhisperLocalEngine(SegmentSTTEngine):
    def __init__(self, on_hypothesis=None, on_recognition=None, on_error=None):
        super().__init__(on_hypothesis, on_recognition, on_error)
        self.local_whisper_model = None

    def _start_listening(self):
        if self.on_hypothesis:
            self.on_hypothesis(f"Loading local Whisper '{config.whisper_local_size}' model (first run may download)...")
        try:
            import whisper as openai_whisper
            self.local_whisper_model = openai_whisper.load_model(config.whisper_local_size, device="cpu")
        except Exception as load_err:
            if self.on_error:
                self.on_error(f"Failed to load local Whisper model: {load_err}")
            return
        super()._start_listening()

    def transcribe(self, audio_data) -> str:
        raw_data = audio_data.get_raw_data(convert_rate=16000, convert_width=2)
        audio_np = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0

        source_is_english = config.source_lang.lower().strip() in ["english", "en"]
        target_is_english = config.target_lang.lower().strip() in ["english", "en"]

        if not source_is_english and target_is_english:
            result = self.local_whisper_model.transcribe(
                audio_np, fp16=False, task="translate",
            )
        else:
            whisper_lang = STTEngine.map_language(config.source_lang, "whisper")
            result = self.local_whisper_model.transcribe(
                audio_np, fp16=False, task="transcribe", language=whisper_lang,
            )

        return result.get("text", "").strip()
