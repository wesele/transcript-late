from config import config
from ._segment_base import SegmentSTTEngine
from .base import STTEngine


class GoogleSTTEngine(SegmentSTTEngine):
    def transcribe(self, audio_data) -> str:
        lang_code = STTEngine.map_language(config.source_lang, "google")
        return self.recognizer.recognize_google(audio_data, language=lang_code)
