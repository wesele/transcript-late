from config import config
from .google_stt import GoogleSTTEngine
from .vosk_stt import VoskSTTEngine
from .whisper_api import WhisperAPIEngine
from .whisper_local import WhisperLocalEngine
from .nvidia_riva import NvidiaRivaEngine
from .parakeet_local import NvidiaLocalEngine


def create_engine(on_hypothesis=None, on_recognition=None, on_error=None):
    if config.stt_engine == "google":
        return GoogleSTTEngine(on_hypothesis, on_recognition, on_error)
    elif config.stt_engine == "vosk":
        return VoskSTTEngine(on_hypothesis, on_recognition, on_error)
    elif config.stt_engine == "whisper-api":
        return WhisperAPIEngine(on_hypothesis, on_recognition, on_error)
    elif config.stt_engine == "whisper-local":
        return WhisperLocalEngine(on_hypothesis, on_recognition, on_error)
    elif config.stt_engine == "nvidia":
        return NvidiaRivaEngine(on_hypothesis, on_recognition, on_error)
    elif config.stt_engine == "nvidia-local":
        return NvidiaLocalEngine(on_hypothesis, on_recognition, on_error)
    raise ValueError(f"Unknown STT engine: {config.stt_engine}")


SpeechRecognitionEngine = create_engine
