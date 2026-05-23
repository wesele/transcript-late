import requests
from config import config
from ._segment_base import SegmentSTTEngine
from .base import STTEngine


class WhisperAPIEngine(SegmentSTTEngine):
    def transcribe(self, audio_data) -> str:
        wav_bytes = audio_data.get_wav_data(convert_rate=16000, convert_width=2)

        api_key = config.whisper_key if config.whisper_key else config.api_key
        base_url = config.whisper_url if config.whisper_url else config.base_url
        model_name = config.whisper_model if config.whisper_model else "whisper-1"

        if not api_key:
            raise ValueError("API Key is missing. Provide it via --whisper-key or --key.")

        headers = {"Authorization": f"Bearer {api_key}"}
        files = {"file": ("audio.wav", wav_bytes, "audio/wav")}
        data = {"model": model_name}

        whisper_lang = STTEngine.map_language(config.source_lang, "whisper")
        if whisper_lang:
            data["language"] = whisper_lang

        base = base_url.rstrip("/")
        url = f"{base}/audio/transcriptions"

        response = requests.post(url, headers=headers, files=files, data=data, timeout=15.0)
        response.raise_for_status()
        return response.json().get("text", "")
